"""
worker.py — generacion automatica y programada de videos.

Corre dentro del contenedor 'worker' del stack. Cada dia, a la hora fijada en
WORKER_HORA, coge los temas pendientes de la lista, genera un video por cada uno
y avisa por Telegram cuando termina.

DECISION IMPORTANTE — por que hay un preset y no opciones aqui dentro:
Este worker NO inventa ni duplica ninguna configuracion de la interfaz. Lee un
preset JSON con exactamente las mismas claves que usa app.py al llamar a
run_pipeline, y lo unico que cambia en cada vuelta es el tema. Asi el video
automatico sale identico al que verias generando a mano, y cuando cambies algo
en la app basta con actualizar el preset. Si el preset no existe, el worker se
niega a arrancar en vez de adivinar ajustes.

Las credenciales nunca viven en el preset: se inyectan desde el entorno.

Uso:
    python worker.py --daemon     duerme hasta WORKER_HORA y repite cada dia
    python worker.py --ahora      hace una tanda ya mismo y sale (para probar)
    python worker.py --uno "tema" genera un solo video de ese tema y sale
    python worker.py --serve      levanta el endpoint HTTP /generar para n8n

--serve es para cuando el guion no sale de temas.txt sino de otro sitio
(AppFlowy vía n8n): expone POST /generar y deja de correr la tanda diaria
automatica. Los otros tres modos no cambian.
"""

import json
import os
import queue
import re
import shutil
import sys
import threading
import time
import unicodedata
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Sin esto, cualquier emoji en un log() revienta con UnicodeEncodeError en
# consolas cp1252 (Windows) y mata el hilo que lo llama a media ejecucion —
# me paso en pruebas locales: el hilo del render moría en el primer log()
# ANTES de tocar el pipeline, y el candado de concurrencia se soltaba de
# inmediato sin haber generado nada. app.py ya se protege igual arriba de todo.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from modules.brain import ContentBrain
from modules.pipeline import run_pipeline
from modules import topic_history

# ── Configuracion desde el entorno ───────────────────────────────────────────

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
PRESET_FILE = os.getenv("WORKER_PRESET_FILE", "/datos/preset.json")
TEMAS_FILE  = os.getenv("WORKER_TEMAS_FILE",  "/datos/temas.txt")
SALIDA_DIR  = os.getenv("WORKER_SALIDA_DIR",  os.path.join(BASE_DIR, "assets", "salida"))
HORA        = os.getenv("WORKER_HORA", "06:00")
POR_TANDA   = int(os.getenv("WORKER_VIDEOS_TANDA", "3"))

# Donde el pipeline deja SIEMPRE el video, con el mismo nombre cada vez.
# Por eso hay que moverlo tras cada generacion o el siguiente lo pisa.
VIDEO_RECIEN_HECHO = os.path.join(BASE_DIR, "assets", "final", "final_short.mp4")

# Claves que el worker fuerza desde el entorno, pase lo que pase en el preset.
# Evita que una credencial quede escrita en un JSON del servidor.
CREDENCIALES = {
    "fish_api_key": "FISH_API_KEY",
    "fish_model":   "FISH_MODEL",
    "el_api_key":   "ELEVENLABS_API_KEY",
    "gtts_api_key": "GOOGLE_TTS_KEY",
    "ai_video_key": "AI_VIDEO_KEY",
}


def log(msg: str):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


# ── Preset y temas ───────────────────────────────────────────────────────────

def cargar_preset() -> dict:
    """Lee el preset y le inyecta las credenciales del entorno."""
    if not os.path.exists(PRESET_FILE):
        raise SystemExit(
            f"No encuentro el preset en {PRESET_FILE}.\n"
            "Copia preset.ejemplo.json al volumen 'datos' como preset.json y "
            "ajusta el modo y la voz. El worker no arranca sin el a proposito: "
            "prefiero pararme a inventarme ajustes que no has elegido."
        )
    with open(PRESET_FILE, "r", encoding="utf-8") as f:
        preset = json.load(f)

    for clave_params, var_entorno in CREDENCIALES.items():
        valor = os.getenv(var_entorno, "")
        if valor:
            preset[clave_params] = valor

    return preset


def temas_pendientes(limite: int) -> list:
    """Devuelve hasta 'limite' temas de la lista que aun no se hayan usado.

    Se apoya en topic_history.is_duplicate, el mismo control que usa la app, para
    que un tema parecido a otro ya publicado no vuelva a salir.
    """
    if not os.path.exists(TEMAS_FILE):
        log(f"⚠️  No hay lista de temas en {TEMAS_FILE}.")
        return []

    with open(TEMAS_FILE, "r", encoding="utf-8") as f:
        crudos = [ln.strip() for ln in f]

    pendientes = []
    for tema in crudos:
        # Lineas vacias y comentarios con # se ignoran: asi puedes anotar en la lista.
        if not tema or tema.startswith("#"):
            continue
        if topic_history.is_duplicate(tema, lang="es"):
            continue
        pendientes.append(tema)
        if len(pendientes) >= limite:
            break

    return pendientes


# ── Generacion ───────────────────────────────────────────────────────────────

def desarrollar_tema(tema: str, preset: dict) -> str:
    """Convierte un tema suelto en un guion estructurado con el formato del autor.

    POR QUE HACE FALTA ESTE PASO:
    El modo Guion tiene dos caminos dentro de brain.generate_freeform_script.
    Si el texto trae cabecera "Titulo:" o tres o mas vinietas, lo trata como
    GUION DEL AUTOR: lo respeta idea por idea y solo le pone encima la voz de la
    persona, el tono y el objetivo. Si le llega una linea suelta cae en el otro
    camino, cuyo prompt dice literalmente "SIN inventar informacion nueva" — con
    un tema de una sola frase eso da un guion famelico.

    Asi que el worker escribe primero el borrador de ideas y deja que el camino
    autorado le ponga la voz. La division queda limpia: aqui el QUE se dice,
    alli el COMO suena (Andrea, tono conductual, objetivo del embudo).
    """
    # Mismo calculo que hace brain para decidir cuantas escenas salen, para que
    # el numero de vinietas que pido sea el numero de escenas que acabara habiendo
    # y no me lleve una sorpresa. El tope de 12 es la barrera de memoria: 15
    # escenas es lo que reventó el render en la nube.
    n = max(int(preset.get("num_scenes", 9)),
            round(float(preset.get("target_total_secs", 43)) / 5.5))
    n = min(n, 12)

    prompt = f"""Eres guionista de contenido corto sobre psicologia conductual,
habitos y productividad, en espanol latino.

TEMA: {tema}

Escribe el ESQUELETO del video. Solo las ideas: la voz se la pone otro despues.

FORMATO EXACTO, sin nada antes ni despues:

Titulo: <titulo corto y concreto, maximo 60 caracteres>
Categoria: psicologia conductual
Guion:
- <idea 1>
- <idea 2>
(y asi hasta {n})

REGLAS:
- Exactamente {n} vinietas. Ni una mas ni una menos.
- Cada vinieta es UNA idea completa, de 12 a 20 palabras.
- La primera nombra la conducta concreta que el espectador reconoce en si mismo.
- Las del medio explican el MECANISMO de por que ocurre, no dan consejos.
- La ultima aterriza en un cambio pequeno y realista del ENTORNO.
- Prohibido: listas tipo "5 tips", promesas de resultados, plazos inventados,
  frases de cartel motivacional y apelar a la fuerza de voluntad.
- No escribas parrafos. Solo la cabecera y las vinietas."""

    borrador = ContentBrain()._generate(prompt).strip()

    # Red de seguridad: si el modelo devuelve algo sin la estructura esperada,
    # el camino autorado no se activaria y el guion saldria pobre sin avisar.
    _vinietas = borrador.count(chr(10) + "-")
    if "Titulo:" not in borrador or _vinietas < 2:
        raise RuntimeError(
            "el borrador del tema salio sin la estructura esperada "
            "(cabecera 'Titulo:' y vinietas); no lo mando al render")

    log(f"   Borrador: {_vinietas} ideas")
    return borrador


def _ejecutar_pipeline(params: dict) -> tuple:
    """Corre run_pipeline y devuelve (ok, mensaje_error, datos_copy).

    Compartido por las dos formas de generar (tema suelto o guion ya escrito):
    la unica diferencia entre ellas es como se rellena params antes de llegar
    aqui. run_pipeline se ejecuta en un hilo solo para poder ir leyendo su cola
    de mensajes en vivo: asi 'docker logs' muestra el avance en tiempo real en
    vez de escupirlo todo de golpe al final.
    """
    cola = queue.Queue()
    hilo = threading.Thread(target=run_pipeline, args=(cola, params), daemon=True)
    hilo.start()

    ok, error, copy_data = False, "", {}

    while True:
        try:
            msg = cola.get(timeout=1.0)
        except queue.Empty:
            if not hilo.is_alive():
                break          # murio sin decir DONE ni ERROR
            continue

        if msg == "DONE":
            ok = True
            break
        if msg.startswith("ERROR:"):
            error = msg[6:]
            break
        if msg.startswith("COPY:"):
            try:
                copy_data = json.loads(msg[5:])
            except Exception:
                pass
            continue

        log(f"   {msg}")

    hilo.join(timeout=30)

    if not ok and not error:
        error = "el pipeline termino sin avisar (revisa el log de arriba)"

    return ok, error, copy_data


def generar(tema: str, preset: dict) -> tuple:
    """Genera un video a partir de un TEMA suelto (lista temas.txt).

    Cada modo lee el tema de un sitio distinto, y esto no es un detalle: el
    modo Guion NO mira "topic". Lee "guion_raw_text" y, si llega vacio, aborta
    con "No se proporciono texto para el guion libre" antes de hacer nada.
    """
    params = dict(preset)
    if preset.get("mode") == "guion":
        params["guion_raw_text"] = desarrollar_tema(tema, preset)
    else:
        params["topic"] = tema
    return _ejecutar_pipeline(params)


def generar_desde_guion(guion_completo: str, preset: dict, copy: str = "") -> tuple:
    """Genera un video a partir de un GUION YA ESCRITO (AppFlowy via n8n).

    A diferencia de generar(), aqui NO se pasa por desarrollar_tema(): el
    guion ya viene completo con su cabecera 'Titulo:/Categoria:/Guion:', asi
    que entra directo al camino autorado (respeta las ideas del autor). Pasarlo
    por el borrador de IA otra vez seria reescribir lo que la persona ya
    redacto a mano en AppFlowy — justo lo que no queremos.

    Lo mismo aplica al copy: si el autor ya escribio uno en la columna "Copy"
    de AppFlowy, se usa tal cual (via copy_override) en vez del generado por IA.
    """
    params = dict(preset)
    params["guion_raw_text"] = guion_completo
    if copy.strip():
        params["copy_override"] = copy.strip()
    return _ejecutar_pipeline(params)


def _slug(texto: str, largo: int = 60) -> str:
    """Nombre de fichero seguro: sin tildes, sin enies, sin signos raros."""
    limpio = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    limpio = re.sub(r"[^\w\s-]", "", limpio).strip().lower()
    limpio = re.sub(r"[\s_-]+", "-", limpio)
    return limpio[:largo] or "video"


def archivar(tema: str, copy_data: dict) -> str:
    """Mueve el mp4 recien hecho a la carpeta de salida con nombre propio.

    Es obligatorio hacerlo antes del siguiente video: el pipeline siempre escribe
    en assets/final/final_short.mp4 y el segundo pisaria al primero.
    """
    if not os.path.exists(VIDEO_RECIEN_HECHO):
        return ""

    os.makedirs(SALIDA_DIR, exist_ok=True)
    base    = f"{datetime.now():%Y-%m-%d_%H%M}_{_slug(tema)}"
    destino = os.path.join(SALIDA_DIR, base + ".mp4")

    # os.replace/os.rename exigen el MISMO sistema de archivos. VIDEO_RECIEN_HECHO
    # vive en la capa interna del contenedor y SALIDA_DIR es un volumen montado
    # del host — son dispositivos distintos, y os.replace revienta con
    # "OSError: [Errno 18] Invalid cross-device link". shutil.move detecta ese
    # caso y cae solo a copiar + borrar. Encontrado en el primer render
    # end-to-end: el video quedaba listo mas nunca llegaba a la carpeta de
    # salida, sin avisar exito ni fallo (la excepcion escapaba sin log()).
    shutil.move(VIDEO_RECIEN_HECHO, destino)

    # El copy (titulo, descripcion, hashtags) que genera el pipeline se guarda al
    # lado del video: es lo que hara falta para publicarlo, a mano o automatico.
    if copy_data:
        with open(os.path.join(SALIDA_DIR, base + ".json"), "w", encoding="utf-8") as f:
            json.dump({"tema": tema, "copy": copy_data}, f, ensure_ascii=False, indent=2)

    return destino


# ── Aviso ────────────────────────────────────────────────────────────────────

def avisar(texto: str):
    """Manda un mensaje por Telegram. Si no esta configurado, no hace nada."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat  = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat:
        return
    try:
        import requests
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat, "text": texto},
            timeout=15,
        )
    except Exception as e:
        log(f"⚠️  No pude avisar por Telegram: {e}")


# ── Tanda ────────────────────────────────────────────────────────────────────

def hacer_tanda(cuantos: int = None):
    cuantos = cuantos or POR_TANDA
    preset  = cargar_preset()
    temas   = temas_pendientes(cuantos)

    if not temas:
        log("No hay temas pendientes. Anade mas a la lista.")
        avisar("AutoShorts: no quedan temas pendientes en la lista.")
        return

    log(f"Tanda de {len(temas)} video(s). Modo: {preset.get('mode', '?')}")

    hechos, fallidos = [], []

    for i, tema in enumerate(temas, 1):
        log(f"── [{i}/{len(temas)}] {tema}")
        inicio = time.time()

        try:
            ok, error, copy_data = generar(tema, preset)
        except Exception as e:
            ok, error, copy_data = False, str(e), {}

        if ok:
            destino = archivar(tema, copy_data)
            # Solo se marca como usado si de verdad salio. Si fallo, el tema
            # sigue en la cola y se reintenta en la tanda siguiente.
            topic_history.add_topic(tema, mode=preset.get("mode", ""),
                                    lang=preset.get("lang", "es"),
                                    category=preset.get("category", ""))
            hechos.append(os.path.basename(destino) or tema)
            log(f"   ✅ Listo en {time.time() - inicio:.0f}s → {destino}")
        else:
            fallidos.append(f"{tema} — {error}")
            log(f"   ❌ Fallo: {error}")

    resumen = f"AutoShorts — tanda del {datetime.now():%d/%m}\n"
    if hechos:
        resumen += "\nListos:\n" + "\n".join(f"• {h}" for h in hechos)
    if fallidos:
        resumen += "\n\nFallaron:\n" + "\n".join(f"• {f}" for f in fallidos)

    log(resumen.replace("\n", " | "))
    avisar(resumen)


# ── Programador ──────────────────────────────────────────────────────────────

def segundos_hasta_la_hora() -> float:
    """Segundos que faltan para la proxima WORKER_HORA (formato HH:MM)."""
    try:
        h, m = (int(x) for x in HORA.split(":"))
    except Exception:
        log(f"⚠️  WORKER_HORA='{HORA}' no es HH:MM. Uso 06:00.")
        h, m = 6, 0

    ahora    = datetime.now()
    objetivo = ahora.replace(hour=h, minute=m, second=0, microsecond=0)
    if objetivo <= ahora:
        objetivo += timedelta(days=1)
    return (objetivo - ahora).total_seconds()


def daemon():
    log(f"Worker en marcha. Tanda diaria a las {HORA} ({POR_TANDA} video/s).")
    log(f"Preset: {PRESET_FILE} · Temas: {TEMAS_FILE} · Salida: {SALIDA_DIR}")

    while True:
        espera = segundos_hasta_la_hora()
        log(f"Durmiendo {espera / 3600:.1f} h hasta la proxima tanda.")
        time.sleep(espera)
        try:
            hacer_tanda()
        except SystemExit:
            raise
        except Exception as e:
            # Un fallo de una tanda no puede tumbar el worker: manana lo reintenta.
            log(f"❌ La tanda fallo entera: {e}")
            avisar(f"AutoShorts: la tanda de hoy fallo.\n{e}")
        # Margen para no repetir la tanda dentro del mismo minuto.
        time.sleep(90)


# ── Servidor HTTP para n8n ────────────────────────────────────────────────────
#
# Un solo candado global: nunca dos renders a la vez. El servidor solo acepta
# el trabajo y contesta al momento (202); el resultado real (video + copy)
# sigue llegando por el webhook_url que YA manda pipeline.py, el mismo que
# alimenta la aprobacion por Telegram. Este endpoint no reemplaza eso, solo
# resuelve "como entra un guion nuevo", que antes solo podia venir de
# temas.txt o de la interfaz.

_RENDER_LOCK  = threading.Lock()
_HTTP_TOKEN   = os.getenv("WORKER_HTTP_TOKEN", "")
_HTTP_PORT    = int(os.getenv("WORKER_HTTP_PORT", "8600"))


def _generar_en_segundo_plano(titulo: str, categoria: str, guion: str, preset: dict, copy: str = ""):
    guion_completo = f"Titulo: {titulo}\nCategoria: {categoria}\nGuion:\n{guion}"
    try:
        log(f"▶ Generando (HTTP): {titulo}")
        ok, error, copy_data = generar_desde_guion(guion_completo, preset, copy)
        if ok:
            destino = archivar(titulo, copy_data)
            log(f"   ✅ Listo → {destino}")
        else:
            log(f"   ❌ Fallo: {error}")
            avisar(f"AutoShorts: fallo generando \"{titulo}\".\n{error}")
    except Exception as e:
        log(f"   ❌ Excepcion inesperada: {e}")
        avisar(f"AutoShorts: excepcion generando \"{titulo}\".\n{e}")
    finally:
        _RENDER_LOCK.release()


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *a):
        log("HTTP " + (fmt % a))

    def _json(self, status: int, payload: dict):
        cuerpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self):
        if self.path == "/salud":
            self._json(200, {"ocupado": _RENDER_LOCK.locked()})
        else:
            self._json(404, {"error": "ruta desconocida"})

    def do_POST(self):
        if self.path != "/generar":
            self._json(404, {"error": "ruta desconocida"})
            return

        if not _HTTP_TOKEN or self.headers.get("X-Worker-Token", "") != _HTTP_TOKEN:
            self._json(401, {"error": "token invalido"})
            return

        try:
            largo = int(self.headers.get("Content-Length", "0"))
            body  = json.loads(self.rfile.read(largo) or b"{}")
        except Exception:
            self._json(400, {"error": "cuerpo no es JSON valido"})
            return

        titulo    = (body.get("titulo") or "").strip()
        categoria = (body.get("categoria") or "").strip()
        guion     = (body.get("guion") or "").strip()
        copy      = (body.get("copy") or "").strip()
        if not titulo or not guion:
            self._json(400, {"error": "faltan 'titulo' o 'guion'"})
            return

        if not _RENDER_LOCK.acquire(blocking=False):
            # No es un error: n8n debe interpretarlo como "reintenta en la
            # proxima vuelta del schedule", nunca como fallo del item.
            self._json(409, {"error": "ya hay un render en curso"})
            return

        preset = cargar_preset()
        hilo = threading.Thread(
            target=_generar_en_segundo_plano,
            args=(titulo, categoria, guion, preset, copy),
            daemon=True,
        )
        hilo.start()
        self._json(202, {"aceptado": True, "titulo": titulo})


def servir():
    if not _HTTP_TOKEN:
        raise SystemExit(
            "Falta WORKER_HTTP_TOKEN. --serve no arranca sin el a proposito: "
            "sin un token, cualquiera en la red interna podria disparar "
            "renders (y gastar las claves de pago) llamando al endpoint."
        )
    cargar_preset()  # falla rapido si el preset no existe, antes de escuchar
    log(f"Sirviendo en :{_HTTP_PORT} — POST /generar (token requerido), GET /salud")
    ThreadingHTTPServer(("0.0.0.0", _HTTP_PORT), _Handler).serve_forever()


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--daemon" in args:
        daemon()
    elif "--serve" in args:
        servir()
    elif "--ahora" in args:
        hacer_tanda()
    elif "--uno" in args:
        i = args.index("--uno")
        if i + 1 >= len(args):
            raise SystemExit('Falta el tema: python worker.py --uno "mi tema"')
        tema   = args[i + 1]
        preset = cargar_preset()
        ok, error, copy_data = generar(tema, preset)
        if ok:
            try:
                log(f"✅ {archivar(tema, copy_data)}")
            except Exception as e:
                # El video ya esta bien generado en este punto; que archivar()
                # falle no puede desaparecer en silencio como paso la vez
                # anterior (el proceso terminaba sin log ni traceback visible).
                raise SystemExit(f"❌ El video se genero pero no se pudo archivar: {e}")
        else:
            raise SystemExit(f"❌ {error}")
    else:
        print(__doc__)
