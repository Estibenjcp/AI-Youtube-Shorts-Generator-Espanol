import os
import json
import functools
import re as _re_mod
import unicodedata as _ud
from dotenv import load_dotenv

load_dotenv()

from modules.categories import TOPIC_CATEGORIES_ES, TOPIC_CATEGORIES_EN, TOPIC_CATEGORIES
from modules.personas import (DEFAULT_PERSONA, DEFAULT_TONO, DEFAULT_OBJETIVO,
                              get_persona, get_tono, get_objetivo,
                              build_voice_block)


def _get_secret(key: str, default: str = "") -> str:
    """Lee una clave de st.secrets (Streamlit Cloud) o de os.environ."""
    val = os.getenv(key, "")
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default


@functools.lru_cache(maxsize=1)
def _get_client():
    """Inicializa el cliente de IA una sola vez (singleton por proceso).

    Cacheado con lru_cache: antes se re-instanciaba en cada _generate (~25/run),
    re-leyendo secrets y reimportando el SDK. Si cambias las API keys/secrets,
    reinicia la app para que tome los nuevos valores.
    """
    provider  = _get_secret("AI_PROVIDER", "gemini").lower()
    api_key   = _get_secret("AI_API_KEY", "")
    model     = _get_secret("AI_MODEL", "")

    # Sin timeout, una llamada que se cuelga (red inestable, proveedor caido)
    # bloquea el hilo del pipeline para siempre: no imprime error, no llega a
    # archivar el video ya renderizado, y el worker se queda "vivo" sin avisar
    # ni exito ni fallo. Encontrado en el primer render end-to-end en el
    # servidor: el video quedaba listo en disco pero brain.generate_copy()
    # (llamada sin proteger, justo despues de guardar el video) se quedaba
    # colgada y nunca se llegaba a archivarlo ni a decir DONE/ERROR.
    if provider == "openrouter":
        from openai import OpenAI
        client        = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key, timeout=45.0)
        default_model = "google/gemini-flash-1.5"
    else:
        from google import genai
        from google.genai import types
        client        = genai.Client(api_key=api_key,
                                     http_options=types.HttpOptions(timeout=45_000))
        default_model = "gemini-2.0-flash-exp"

    return client, provider, model or default_model


# Modos de contenido educativo que pasan por generate_script(): en ellos se exige
# evidencia verificable y un paso accionable, con un flujo narrativo distinto al
# de los modos de misterio/viral.
# Nota: "ciencia_facil" NO va aqui — tiene su propia funcion
# (generate_ciencia_facil_script), donde esas reglas estan aplicadas por separado.
EDUCATIONAL_MODES = {
    "mentalidad",            # productividad, habitos, disciplina
    "psicologia_positiva",   # desarrollo personal, inteligencia emocional
}


# ── Parser del modo Guion ────────────────────────────────────────────────────
# Permite pegar un guion ya escrito con cabecera estructurada, por ejemplo:
#
#   Titulo: El secreto para estudiar sin distraerte
#   Categoria: Psicologia conductual y Productividad
#   Visual/Interfaz sugerida: Escritorio desordenado con celular -> escritorio limpio
#   Guion: "¿Sientes que te falta disciplina?
#   . Tu atencion ira al estimulo mas facil
#   . Pon el telefono en otra habitacion"
#
# Sin cabecera, el texto entero se trata como guion (comportamiento anterior).

_FF_LABELS = {
    "titulo":    ("titulo", "title"),
    "categoria": ("categoria", "category", "nicho", "niche"),
    "visual":    ("visual/interfaz sugerida", "visual interfaz sugerida", "visual sugerida",
                  "interfaz sugerida", "visual", "suggested visual", "visuals"),
    "guion":     ("guion", "script", "texto", "text"),
}

_FF_BULLET_RE = _re_mod.compile(r"^\s*(?:[.\-•·*–—>]+|\d+[.)])\s+")


def _ff_normalize(s: str) -> str:
    """Minusculas sin acentos ni espacios sobrantes, para comparar etiquetas.

    Colapsa el espaciado interno y el que rodea a las barras, porque una
    cabecera escrita "Visual / Interfaz sugerida" debe reconocerse igual que
    "Visual/Interfaz sugerida". Sin esto la linea entera se cuela en el guion
    y acaba narrada como si fuera texto hablado.
    """
    s = _ud.normalize("NFD", (s or "").strip().lower())
    s = "".join(c for c in s if _ud.category(c) != "Mn")
    s = _re_mod.sub(r"\s*/\s*", "/", s)   # "visual / interfaz" -> "visual/interfaz"
    s = _re_mod.sub(r"\s+", " ", s)
    return s.strip()


def _ff_strip_bullet(line: str) -> str:
    """Quita la vinieta inicial ('.', '-', '*', '1.', etc.) de una linea."""
    return _FF_BULLET_RE.sub("", line).strip()


# ── Modo LITERAL (guion escrito por un agente externo) ───────────────────────
# El agente de guiones (Documento Maestro) ya entrega el texto narrado final,
# las busquedas de B-roll y el copy. Aqui NO se llama a ningun modelo: el
# sistema de video solo parte el texto en escenas, asigna los clips de Pexels
# y renderiza. Sin persona, sin tono, sin objetivo, sin expansion.
#
# Etiquetas del formato del agente que se descartan si vienen pegadas en el
# mismo texto: [HOOK VISUAL/VERBAL], [CUERPO NARRADO], [CTA], [SUGERENCIAS
# B-ROLL], [METADATOS]. Las dos ultimas secciones no se narran.
_LIT_LABEL_RE = _re_mod.compile(
    r"^\s*(?:\d+\.\s*)?\**\[?\s*(HOOK[^\]:]*|CUERPO[^\]:]*|CTA[^\]:]*|SUGERENCIAS[^\]:]*|B-?ROLL[^\]:]*|METADATOS[^\]:]*)\s*\]?\**\s*:?\s*\**",
    _re_mod.IGNORECASE)
_LIT_SKIP_SECTIONS = ("sugerencias", "b-roll", "broll", "metadatos")

# Busquedas genericas del nicho (habitos / disciplina), en ingles, para cuando
# el agente no manda B-roll o manda menos terminos que escenas. Sin planos
# quemados (cama, ventana, meditacion).
LITERAL_FALLBACK_VISUALS = [
    "person writing planner desk", "alarm clock morning table", "running shoes doorway",
    "messy desk smartphone", "gears mechanism close up", "fork in the road path",
    "kitchen counter healthy food", "dumbbells home floor", "hand flipping light switch",
    "city commute walking fast", "stacking coins table", "calendar marking days",
    "person tying shoelaces", "laptop closing lid", "water glass filling",
]


# Palabras con enie -> sinonimo pronunciable. El agente ya tiene la regla de no
# usarlas; esto es la red de seguridad para que el TTS nunca reciba una enie
# (ni el apanio "anio", que tambien suena raro). Frases primero, luego palabras
# completas (con \b) para no tocar otras palabras.
_ENIE_SINONIMOS = [
    (r"(?:por|en) las? mañanas?", "temprano"),
    (r"cada mañana", "cada dia al despertar"),
    (r"mañanas", "amaneceres"),
    (r"mañana", "el dia siguiente"),
    (r"años", "temporadas"), (r"año", "temporada"),
    (r"niños", "chicos"), (r"niñas", "chicas"), (r"niño", "chico"), (r"niña", "chica"),
    (r"pequeños", "minimos"), (r"pequeñas", "minimas"), (r"pequeño", "minimo"), (r"pequeña", "minima"),
    (r"señales", "alertas"), (r"señal", "alerta"),
    (r"diseñados", "planeados"), (r"diseñadas", "planeadas"), (r"diseñado", "planeado"), (r"diseñada", "planeada"),
    (r"diseñar", "planear"), (r"diseñas", "planeas"), (r"diseña", "planea"), (r"diseños", "planes"), (r"diseño", "plan"),
    (r"enseñanzas", "lecciones"), (r"enseñanza", "leccion"),
    (r"enseñar", "mostrar"), (r"enseñan", "muestran"), (r"enseñas", "muestras"), (r"enseña", "muestra"),
    (r"sueños", "metas"), (r"sueño", "descanso"),
    (r"compañeros", "colegas"), (r"compañeras", "colegas"), (r"compañero", "colega"), (r"compañera", "colega"),
    (r"engañar", "mentir"), (r"engañan", "mienten"), (r"engañas", "mientes"), (r"engaña", "miente"),
    (r"engaños", "mentiras"), (r"engaño", "mentira"),
    (r"dañar", "perjudicar"), (r"dañan", "perjudican"), (r"dañas", "perjudicas"), (r"daña", "perjudica"),
    (r"dañados", "perjudicados"), (r"dañado", "perjudicado"), (r"daños", "perjuicios"), (r"daño", "perjuicio"),
    (r"extraños", "raros"), (r"extrañas", "raras"), (r"extraño", "raro"), (r"extraña", "rara"),
    (r"añadir", "agregar"), (r"añaden", "agregan"), (r"añades", "agregas"), (r"añade", "agrega"),
    (r"baño", "ducha"), (r"empeño", "esfuerzo"), (r"campaña", "iniciativa"), (r"español", "castellano"),
    (r"cariño", "afecto"), (r"montañas", "cerros"), (r"montaña", "cerro"), (r"contraseña", "clave"),
    (r"puño", "mano cerrada"), (r"tamaño", "medida"), (r"señor", "caballero"), (r"señora", "dama"),
    (r"acompañar", "seguir"), (r"acompaña", "sigue"), (r"acompañan", "siguen"),
]
_ENIE_SINONIMOS_RE = [(_re_mod.compile(r"\b" + pat + r"\b", _re_mod.IGNORECASE), rep)
                      for pat, rep in _ENIE_SINONIMOS]


def _sin_enie(text: str) -> str:
    """Reemplaza palabras con enie por sinonimos (respetando la mayuscula
    inicial) y, como ultimo recurso, la enie suelta por 'ni'."""
    def _sub(rep):
        def _f(m):
            w = m.group(0)
            return rep[0].upper() + rep[1:] if w[0].isupper() else rep
        return _f
    for rx, rep in _ENIE_SINONIMOS_RE:
        text = rx.sub(_sub(rep), text)
    return text.replace("ñ", "ni").replace("Ñ", "Ni")


def _lit_clean_narration(raw_text: str) -> str:
    """Devuelve solo el texto que se narra, sin etiquetas del agente ni
    secciones de B-roll/metadatos. Acepta tambien la cabecera Titulo:/Guion:."""
    parsed = parse_freeform_input(raw_text)
    body = parsed["guion"] if parsed["has_structure"] else (raw_text or "")
    out, skipping = [], False
    for line in body.splitlines():
        m = _LIT_LABEL_RE.match(line)
        if m:
            label = m.group(1).lower()
            skipping = any(k in label for k in _LIT_SKIP_SECTIONS)
            rest = line[m.end():].strip()
            if not skipping and rest:
                out.append(rest)
            continue
        if skipping:
            continue
        if line.strip():
            out.append(_ff_strip_bullet(line))
    text = " ".join(out)
    text = _re_mod.sub(r"\s+", " ", text).strip()
    text = text.strip('"“”«»').strip()
    # El TTS pronuncia mal la enie y las vocales acentuadas; misma convencion
    # que el resto del proyecto (anio, senior, habito). El agente ya evita esas
    # letras; esto es la red de seguridad para el texto narrado.
    text = _sin_enie(text)
    text = _ud.normalize("NFD", text)
    return "".join(c for c in text if _ud.category(c) != "Mn")


def _lit_split_sentences(text: str) -> list:
    parts = [t.strip() for t in _re_mod.split(r"(?<=[.!?…])\s+", text) if t.strip()]
    return parts or ([text.strip()] if text.strip() else [])


def normalize_broll(broll) -> list:
    """Lista limpia de busquedas Pexels a partir de una lista o de texto con
    una busqueda por linea/punto y coma. Quita vinietas, comillas y numeracion."""
    if not broll:
        return []
    if isinstance(broll, str):
        items = _re_mod.split(r"[\n;]+", broll)
    else:
        items = list(broll)
    out = []
    for it in items:
        t = _ff_strip_bullet(str(it or "")).strip().strip('"“”«»').strip("'").strip()
        t = _re_mod.sub(r"^\(?\d+\)?[.)-]?\s*", "", t)          # "1) ..." / "2. ..."
        t = _re_mod.sub(r"^[\[\(]?(?:escena|scene)\s*\d+[\]\):.-]*\s*", "", t, flags=_re_mod.I)
        t = t.strip().strip('"“”«»').strip()
        if t and any(c.isalpha() for c in t):
            out.append(t[:60])
    return out[:40]


def build_literal_script(raw_text: str, broll=None, lang: str = "es",
                         secs_per_scene: float = 3.2, wps: float = 2.3) -> list:
    """Parte un guion narrado FINAL en escenas sin tocar una sola palabra.

    - Escenas de ~secs_per_scene segundos (~7 palabras): se agrupan oraciones
      completas; una oracion muy larga se parte por comas/puntos y coma.
      Cada escena muestra dos clips (A/B), asi que el plano cambia cada
      ~1,6 s: ritmo de short, no de documental.
    - visual_1/visual_2: B-roll del agente repartido a lo largo de las escenas
      en orden (si trae menos terminos que escenas, cada termino cubre un
      tramo; si no trae ninguno, LITERAL_FALLBACK_VISUALS).
    - Sin ninguna llamada a IA.
    """
    text = _lit_clean_narration(raw_text)
    if not text:
        return []
    target = max(5, int(secs_per_scene * wps))       # ~7 palabras por escena
    hard   = target + 4                              # tope duro: ~11 palabras

    _CONJ = {"y", "pero", "porque", "que", "cuando", "si", "para", "con", "sin",
             "o", "aunque", "mientras", "donde", "como", "hasta", "sino"}

    def _split_words(piece: str) -> list:
        """Trozo sin comas mas largo que `hard`: cortar cada ~target palabras,
        preferiblemente justo antes de una conjuncion (queda natural al oido)."""
        words = piece.split()
        out, start = [], 0
        while len(words) - start > hard:
            cut = start + target
            for j in range(min(start + hard, len(words) - 1), start + max(3, target // 2), -1):
                if words[j].lower().strip('"“”«»') in _CONJ:
                    cut = j
                    break
            out.append(" ".join(words[start:cut])); start = cut
        out.append(" ".join(words[start:]))
        return out

    units = []
    for sent in _lit_split_sentences(text):
        if len(sent.split()) <= hard:
            units.append(sent)
            continue
        # Oracion larguisima: partir por comas / punto y coma conservando el
        # signo; si un trozo sigue siendo largo (sin comas), partir por palabras.
        chunk, buf = [], []
        for piece in _re_mod.split(r"(?<=[,;:])\s+", sent):
            if len(piece.split()) > hard:
                if buf:
                    chunk.append(" ".join(buf)); buf = []
                chunk.extend(_split_words(piece))
                continue
            buf.append(piece)
            if sum(len(x.split()) for x in buf) >= target:
                chunk.append(" ".join(buf)); buf = []
        if buf:
            chunk.append(" ".join(buf))
        units.extend(chunk)

    scenes_text, cur = [], []
    for u in units:
        cur_words = sum(len(x.split()) for x in cur)
        if cur and cur_words + len(u.split()) > hard:
            scenes_text.append(" ".join(cur)); cur = []
        cur.append(u)
        if sum(len(x.split()) for x in cur) >= target:
            scenes_text.append(" ".join(cur)); cur = []
    if cur:
        # Un resto muy corto se pega a la escena anterior para no dejar un
        # clip de 1 segundo al final.
        if scenes_text and sum(len(x.split()) for x in cur) < target // 2:
            scenes_text[-1] += " " + " ".join(cur)
        else:
            scenes_text.append(" ".join(cur))

    n = len(scenes_text)
    visuals = normalize_broll(broll)
    scenes = []
    for i, t in enumerate(scenes_text):
        if visuals and len(visuals) >= n:
            a = visuals[i]
            b = visuals[(i + 1) % len(visuals)]
        elif visuals:
            k = (i * len(visuals)) // n                 # tramo proporcional
            a = visuals[k]
            b = visuals[(k + 1) % len(visuals)]
        else:
            a = LITERAL_FALLBACK_VISUALS[i % len(LITERAL_FALLBACK_VISUALS)]
            b = LITERAL_FALLBACK_VISUALS[(i + 1) % len(LITERAL_FALLBACK_VISUALS)]
        scenes.append({"id": i + 1, "text": t, "visual_1": a, "visual_2": b, "mood": "calm"})

    dur = sum(len(t.split()) for t in scenes_text) / wps
    src_label = ("B-roll del agente" if visuals else "visuales genericos del nicho") if lang == "es" else \
                ("agent B-roll" if visuals else "generic niche visuals")
    print(f"📜 Modo literal: {n} escenas, ~{dur:.0f}s, {src_label} ({len(visuals)} terminos). Sin IA.")
    return scenes


def parse_freeform_input(raw_text: str) -> dict:
    """Separa la cabecera estructurada del cuerpo del guion.

    Devuelve: {titulo, categoria, visual, guion, beats, has_structure}
    - beats: lista de frases del guion (una por vinieta o linea), sin vinietas.
    - has_structure: True si se reconocio al menos una etiqueta de cabecera.
    """
    out = {"titulo": "", "categoria": "", "visual": "", "guion": "",
           "beats": [], "has_structure": False}
    if not raw_text or not raw_text.strip():
        return out

    lines = raw_text.splitlines()
    guion_lines: list[str] = []
    in_guion = False

    for line in lines:
        matched_field = None
        if ":" in line and not in_guion:
            head, _, tail = line.partition(":")
            head_norm = _ff_normalize(head)
            for field, aliases in _FF_LABELS.items():
                if head_norm in aliases:
                    matched_field = field
                    break
            if matched_field:
                out["has_structure"] = True
                value = tail.strip()
                if matched_field == "guion":
                    in_guion = True           # el resto del texto es el guion
                    if value:
                        guion_lines.append(value)
                else:
                    out[matched_field] = value
                continue

        # Una vez dentro del guion (o si no hay cabecera) acumulamos todo.
        if in_guion or not out["has_structure"]:
            guion_lines.append(line)
        elif line.strip():
            # Texto suelto tras la cabecera pero antes de "Guion:" — es guion igualmente.
            guion_lines.append(line)

    body = "\n".join(guion_lines).strip()
    # Quitar comillas envolventes que suelen acompaniar al guion pegado
    if len(body) >= 2 and body[0] in '"“«' and body[-1] in '"”»':
        body = body[1:-1].strip()
    body = body.strip().strip('"“”«»').strip()

    out["guion"] = body
    # Un beat solo cuenta si contiene texto real: descarta restos de puntuacion
    # como el '.' o '."' que suelen quedar al final de un guion pegado.
    _line_beats = [b for b in (_ff_strip_bullet(l) for l in body.splitlines())
                   if any(c.isalnum() for c in b)]

    # Si el autor escribio el guion como un parrafo corrido (sin vinietas ni
    # saltos de linea, comun cuando se pega desde AppFlowy), partir solo por
    # lineas deja 1-2 beats aunque el texto tenga varias ideas. Eso limita el
    # numero de escenas a ~2 sin importar la duracion objetivo (ver
    # _generate_authored_script: n <= n_ideas*2), asi que el video sale con
    # clips larguisimos y poco dinamicos. Partiendo por oraciones se preserva
    # el mismo contenido, solo con mas granularidad para calcular escenas.
    if len(_line_beats) >= 3:
        out["beats"] = _line_beats
    else:
        _sentence_beats = [s.strip() for s in _re_mod.split(r'(?<=[.!?])\s+', body)
                           if len(s.strip()) > 3]
        out["beats"] = _sentence_beats if len(_sentence_beats) > len(_line_beats) else _line_beats
    return out


# ── Sustitucion de la letra ñ por sinonimos ─────────────────────────────────
# Los motores de voz pronuncian mal la ñ, y convertirla en "n" es peor todavia:
# "año" pasaria a "ano", que es otra palabra. La solucion es cambiar la palabra
# entera por un sinonimo.
#
# Este diccionario es la red DETERMINISTA: se aplica sin depender de ninguna
# llamada a la API. Cubre las palabras con ñ mas frecuentes en contenido de
# psicologia y productividad, conservando genero y numero. Lo que no aparezca
# aqui se consulta al modelo, y solo si eso tambien falla queda la conversion
# ñ→n de audio.py como ultimo recurso.
# REGLA DE ESTE DICCIONARIO: el sinonimo debe ser UNA palabra, sin articulo, y
# del MISMO genero y numero que la original. Si no, el articulo que la precede
# deja de concordar ("el diseño" -> "el estructura") o se duplica ("por la
# mañana" -> "por la el dia siguiente"). Todo lo que necesite reescribir la
# frase se deja fuera a proposito: eso lo resuelve el modelo en el paso 2.
_SIN_ENIE = {
    # tiempo  (masculinos, para que concuerden con "el/un/este")
    "año": "periodo", "años": "periodos",
    # disenio y estructura — el termino clave del nicho
    "diseña": "organiza", "diseñas": "organizas", "diseñan": "organizan",
    "diseñar": "organizar", "diseñe": "organice",
    "diseñado": "organizado", "diseñada": "organizada",
    "diseñados": "organizados", "diseñadas": "organizadas",
    "diseño": "esquema", "diseños": "esquemas",          # ambos masculinos
    "diseñador": "organizador", "diseñadora": "organizadora",
    # senializacion  (femeninos)
    "señal": "pista", "señales": "pistas",
    "señala": "indica", "señalan": "indican", "señalar": "indicar",
    "señalado": "indicado", "señalada": "indicada",
    # tamanio
    "pequeño": "minimo", "pequeña": "minima",
    "pequeños": "minimos", "pequeñas": "minimas",
    # personas
    "compañero": "colega", "compañera": "colega",        # colega vale para ambos
    "compañeros": "colegas", "compañeras": "colegas",
    "niño": "chico", "niña": "chica", "niños": "chicos", "niñas": "chicas",
    "dueño": "propietario", "dueña": "propietaria",
    "dueños": "propietarios", "dueñas": "propietarias",
    # ensenianza
    "enseña": "explica", "enseñas": "explicas", "enseñan": "explican",
    "enseñar": "explicar", "enseñado": "explicado",
    "enseñanza": "leccion", "enseñanzas": "lecciones",   # ambos femeninos
    # conducta y emociones  (mismo genero que el original)
    "sueño": "descanso", "sueños": "objetivos",
    "soñar": "imaginar", "sueña": "imagina",
    "extraño": "raro", "extraña": "rara",
    "extraños": "raros", "extrañas": "raras",
    "daño": "perjuicio", "daños": "perjuicios",
    "engaño": "truco", "engaños": "trucos",              # ambos masculinos
    "cariño": "afecto", "empeño": "esfuerzo",
    "desempeño": "rendimiento",
    "añade": "suma", "añaden": "suman", "añadir": "sumar",
    "añadido": "sumado", "añadida": "sumada",
    "montaña": "colina", "montañas": "colinas",          # ambos femeninos
    "peldaño": "escalon", "peldaños": "escalones",
    "bañar": "lavar", "baña": "lava",
}


def _sustituir_enie(texto: str) -> tuple:
    """Cambia por sinonimo las palabras con ñ que estan en el diccionario.

    Devuelve (texto_nuevo, pendientes) donde `pendientes` son las palabras con
    ñ que el diccionario no cubre y hay que resolver de otra forma.
    Respeta la mayuscula inicial de la palabra original.
    """
    if not texto or ("ñ" not in texto and "Ñ" not in texto):
        return texto, []

    def _reemplazo(m):
        palabra = m.group(0)
        nuevo = _SIN_ENIE.get(palabra.lower())
        if not nuevo:
            return palabra
        return nuevo.capitalize() if palabra[0].isupper() else nuevo

    nuevo_texto = _re_mod.sub(r"[\wáéíóúÁÉÍÓÚüÜñÑ]*[ñÑ][\wáéíóúÁÉÍÓÚüÜñÑ]*",
                             _reemplazo, texto)
    pendientes = _re_mod.findall(r"[\wáéíóúÁÉÍÓÚüÜñÑ]*[ñÑ][\wáéíóúÁÉÍÓÚüÜñÑ]*",
                                 nuevo_texto)
    return nuevo_texto, sorted(set(pendientes))


def _ff_missing_key_terms(beats: list, scenes: list) -> list:
    """Comprueba que los terminos distintivos del autor sobrevivieron a la re-voz.

    Al permitir reescritura libre ya no se puede comparar palabra por palabra, asi
    que vigilamos las palabras largas y especificas (arquitectura, conductual,
    dopamina...). Si alguna desaparece, es senial de que se perdio una idea.
    Devuelve la lista de terminos ausentes (vacia si todo esta cubierto).
    """
    def _norm(s: str) -> str:
        s = _ud.normalize("NFD", (s or "").lower())
        return "".join(c for c in s if _ud.category(c) != "Mn")

    salida = _norm(" ".join((s.get("text") or "") for s in scenes if isinstance(s, dict)))
    if not salida:
        return []

    _ignorar = {"cualquier", "cualquiera", "entonces", "tambien", "despues",
                "mientras", "siempre", "probablemente", "realmente"}
    terminos, vistos = [], set()
    for b in beats:
        for w in _norm(b).split():
            w = w.strip(".,;:¿?¡!()\"'-")
            if len(w) >= 9 and w not in _ignorar and w not in vistos:
                vistos.add(w)
                terminos.append(w)
    return [t for t in terminos if t not in salida]


class ContentBrain:

    def _generate(self, prompt: str) -> str:
        client, provider, model = _get_client()
        if provider == "openrouter":
            # Sin max_tokens, OpenRouter pide el tope del modelo (65536 en varios)
            # como reserva de credito antes de generar nada. Ningun texto de este
            # pipeline (guion, copy, titulos) necesita ni de lejos esa cantidad,
            # y un saldo bajo hace fallar la llamada con 402 aunque el prompt en
            # si sea corto. Encontrado en un render real: fallaba por faltar
            # ~343 tokens de saldo para reservar 65536 completos.
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=8192,
            )
            return response.choices[0].message.content
        else:
            response = client.models.generate_content(model=model, contents=prompt)
            return response.text

    def get_trending_topic(self, manual_topic: str = "", lang: str = "es",
                           category_hint: str = "", mode: str = "auto",
                           exclude_books: list = None,
                           used_topics: list = None) -> str:
        if manual_topic.strip():
            label = "Tema" if lang == "es" else "Topic"
            print(f"🎯 {label}: {manual_topic.strip()}")
            return manual_topic.strip()

        _excl_block_es = _excl_block_en = ""  # no token cost — dedup done locally after generation

        import random as _random
        from modules.categories import (VIRAL_CATEGORIES, TESTIMONIO_CATEGORIES,
                                          BOOK_CATEGORIES, BOOK_CATEGORIES_EN,
                                          MISTERIO_BIBLICO_CATEGORIES, MISTERIO_BIBLICO_CATEGORIES_EN,
                                          TRUE_CRIME_CATEGORIES, TRUE_CRIME_CATEGORIES_EN,
                                          PSICOLOGIA_OSCURA_CATEGORIES, PSICOLOGIA_OSCURA_CATEGORIES_EN,
                                          CONSPIRACION_CATEGORIES, CONSPIRACION_CATEGORIES_EN,
                                          CIENCIA_MISTERIO_CATEGORIES, CIENCIA_MISTERIO_CATEGORIES_EN,
                                          FINANZAS_CATEGORIES, FINANZAS_CATEGORIES_EN,
                                          MENTALIDAD_CATEGORIES, MENTALIDAD_CATEGORIES_EN,
                                          HISTORIA_EPICA_CATEGORIES, HISTORIA_EPICA_CATEGORIES_EN,
                                          PSICOLOGIA_POSITIVA_CATEGORIES, PSICOLOGIA_POSITIVA_CATEGORIES_EN,
                                          MENTE_MASCULINA_CATEGORIES, MENTE_MASCULINA_CATEGORIES_EN,
                                          MUJER_CONSCIENTE_CATEGORIES, MUJER_CONSCIENTE_CATEGORIES_EN,
                                          INDIGNACION_CATEGORIES, INDIGNACION_CATEGORIES_EN,
                                          CIENCIA_FACIL_CATEGORIES, CIENCIA_FACIL_CATEGORIES_EN)

        # Pick category from the right pool depending on mode
        if category_hint.strip():
            category = category_hint.strip()
        elif mode == "viral":
            category = _random.choice(VIRAL_CATEGORIES)
        elif mode == "testimonio":
            category = _random.choice(TESTIMONIO_CATEGORIES)
        elif mode == "misterio_biblico":
            cats = MISTERIO_BIBLICO_CATEGORIES if lang == "es" else MISTERIO_BIBLICO_CATEGORIES_EN
            category = _random.choice(cats)
        elif mode == "libro":
            category = _random.choice(BOOK_CATEGORIES if lang == "es" else BOOK_CATEGORIES_EN)
        elif mode == "true_crime":
            category = _random.choice(TRUE_CRIME_CATEGORIES if lang == "es" else TRUE_CRIME_CATEGORIES_EN)
        elif mode == "psicologia_oscura":
            category = _random.choice(PSICOLOGIA_OSCURA_CATEGORIES if lang == "es" else PSICOLOGIA_OSCURA_CATEGORIES_EN)
        elif mode == "conspiracion":
            category = _random.choice(CONSPIRACION_CATEGORIES if lang == "es" else CONSPIRACION_CATEGORIES_EN)
        elif mode == "ciencia_misterio":
            category = _random.choice(CIENCIA_MISTERIO_CATEGORIES if lang == "es" else CIENCIA_MISTERIO_CATEGORIES_EN)
        elif mode == "finanzas":
            category = _random.choice(FINANZAS_CATEGORIES if lang == "es" else FINANZAS_CATEGORIES_EN)
        elif mode == "mentalidad":
            category = _random.choice(MENTALIDAD_CATEGORIES if lang == "es" else MENTALIDAD_CATEGORIES_EN)
        elif mode == "historia_epica":
            category = _random.choice(HISTORIA_EPICA_CATEGORIES if lang == "es" else HISTORIA_EPICA_CATEGORIES_EN)
        elif mode == "psicologia_positiva":
            category = _random.choice(PSICOLOGIA_POSITIVA_CATEGORIES if lang == "es" else PSICOLOGIA_POSITIVA_CATEGORIES_EN)
        elif mode == "mente_masculina":
            category = _random.choice(MENTE_MASCULINA_CATEGORIES if lang == "es" else MENTE_MASCULINA_CATEGORIES_EN)
        elif mode == "mujer_consciente":
            category = _random.choice(MUJER_CONSCIENTE_CATEGORIES if lang == "es" else MUJER_CONSCIENTE_CATEGORIES_EN)
        elif mode == "indignacion":
            category = _random.choice(INDIGNACION_CATEGORIES if lang == "es" else INDIGNACION_CATEGORIES_EN)
        elif mode == "ciencia_facil":
            category = _random.choice(CIENCIA_FACIL_CATEGORIES if lang == "es" else CIENCIA_FACIL_CATEGORIES_EN)
        else:
            categories = TOPIC_CATEGORIES.get(lang, TOPIC_CATEGORIES_ES)
            category   = _random.choice(categories)

        import time as _time
        # Seed compuesto: nanosegundos + aleatorio → prácticamente único cada llamada
        seed = (int(_time.time_ns()) % 999983) ^ int(_random.random() * 999979)

        # Bloque de advertencia anti-alucinación — incluido en TODOS los modos
        _real_warning_es = (
            f"⚠️ REGLA CRÍTICA: El tema DEBE ser un evento real y verificable que pueda encontrarse "
            f"en Wikipedia, libros de historia o noticias documentadas. "
            f"ABSOLUTAMENTE PROHIBIDO inventar operaciones, fechas, nombres o conspiraciones que no existan. "
            f"Si no estás 100% seguro de que ocurrió → NO lo sugieras. "
            f"Prefiere temas menos conocidos pero 100% reales antes que temas inventados que suenan impactantes.\n"
        )
        _real_warning_en = (
            f"⚠️ CRITICAL RULE: The topic MUST be a real, verifiable event that can be found "
            f"in Wikipedia, history books, or documented news. "
            f"ABSOLUTELY FORBIDDEN to invent operations, dates, names, or conspiracies that don't exist. "
            f"If you are not 100% certain it happened → DO NOT suggest it. "
            f"Prefer lesser-known but 100% real topics over invented ones that sound shocking.\n"
        )

        # Use mode-specific prompt so the topic matches the content style
        if mode == "viral":
            prompt = (
                f"Dame 1 tema oscuro, impactante y REAL para un YouTube Short viral "
                f"en la categoría: {category}. "
                f"Debe ser un hecho histórico documentado: catástrofe real, near miss registrado, "
                f"mortandad histórica comprobada, o experimento gubernamental que realmente existió. "
                f"Semilla: {seed}. "
                f"{_real_warning_es}"
                f"{_excl_block_es}"
                f"Responde ÚNICAMENTE con el nombre del tema, nada más. En español."
            ) if lang == "es" else (
                f"Give me 1 dark, shocking and REAL topic for a viral YouTube Short "
                f"in the category: {category}. "
                f"Must be a documented historical event: real catastrophe, recorded near miss, "
                f"verified mass death, or government experiment that actually existed. "
                f"Seed: {seed}. "
                f"{_real_warning_en}"
                f"{_excl_block_en}"
                f"Return ONLY the topic name, nothing else."
            )
        elif mode == "testimonio":
            prompt = (
                f"Dame 1 tema de horror o misterio DOCUMENTADO para un Short cinematográfico "
                f"en la categoría: {category}. "
                f"Debe basarse en hechos reales: una secta que realmente existió, un ritual documentado, "
                f"un caso policial real, un fenómeno registrado por autoridades o investigadores. "
                f"Semilla: {seed}. "
                f"{_real_warning_es}"
                f"{_excl_block_es}"
                f"Responde ÚNICAMENTE con el nombre del tema, nada más. En español."
            ) if lang == "es" else (
                f"Give me 1 documented horror or mystery topic for a cinematic Short "
                f"in the category: {category}. "
                f"Must be based on real facts: a cult that actually existed, a documented ritual, "
                f"a real criminal case, a phenomenon recorded by authorities or investigators. "
                f"Seed: {seed}. "
                f"{_real_warning_en}"
                f"{_excl_block_en}"
                f"Return ONLY the topic name, nothing else."
            )
        elif mode == "misterio_biblico":
            prompt = (
                f"Dame 1 tema de misterio, secreto oscuro o hecho poco conocido de la Biblia "
                f"en la categoria: {category}. "
                f"Debe estar documentado en textos sagrados, manuscritos historicos, arqueologia biblica o investigacion academica. "
                f"Ejemplos: angeles caidos del Libro de Enoc, los Nefilim del Genesis, la desaparicion del Arca de la Alianza, "
                f"la destruccion de Sodoma y Gomorra, el simbolismo del 666, profecias del Apocalipsis sin explicar. "
                f"Semilla: {seed}. "
                f"{_real_warning_es}"
                f"{_excl_block_es}"
                f"Responde UNICAMENTE con el nombre del tema, nada mas. En espanol."
            ) if lang == "es" else (
                f"Give me 1 mystery, dark secret, or little-known biblical fact "
                f"in the category: {category}. "
                f"Must be documented in sacred texts, historical manuscripts, biblical archaeology, or academic research. "
                f"Examples: fallen angels from the Book of Enoch, the Nephilim in Genesis, the disappearance of the Ark of the Covenant, "
                f"destruction of Sodom and Gomorrah, symbolism of 666, unexplained Apocalypse prophecies. "
                f"Seed: {seed}. "
                f"{_real_warning_en}"
                f"{_excl_block_en}"
                f"Return ONLY the topic name, nothing else."
            )
        elif mode == "libro":
            # Lista negra de libros ya usados en esta sesión
            _excl = exclude_books or []
            _excl_es = (
                (f"- ESTRICTAMENTE PROHIBIDO elegir cualquiera de estos libros ya vistos: {', '.join(_excl)}.\n")
                if _excl else ""
            )
            _excl_en = (
                (f"- STRICTLY FORBIDDEN to choose any of these already-seen books: {', '.join(_excl)}.\n")
                if _excl else ""
            )
            prompt = (
                f"Eres un curador literario experto. Necesito el título de UN libro real de la categoría: {category}.\n"
                f"Semilla de aleatoriedad: {seed} — este número cambia en cada llamada, úsalo para explorar el catálogo en orden diferente.\n"
                f"REGLAS ESTRICTAS:\n"
                f"- PROHIBIDO: 'Hábitos Atómicos', 'El Poder del Ahora', 'Padre Rico Padre Pobre', 'El Monje que Vendió su Ferrari', 'Piense y Hágase Rico'.\n"
                f"{_excl_es}"
                f"- Elige un libro real, valioso pero NO el más obvio de la categoría.\n"
                f"- Rota entre: clásicos del siglo XX, libros modernos (2010-2024), autores latinoamericanos, europeos, asiáticos.\n"
                f"- Formato exacto: 'Título del Libro — Autor'\n"
                f"- Responde ÚNICAMENTE con el título y autor. Nada más."
            ) if lang == "es" else (
                f"You are an expert literary curator. Give me the title of ONE real book from the category: {category}.\n"
                f"Randomness seed: {seed} — this number changes each call, use it to explore the catalog in a different order.\n"
                f"STRICT RULES:\n"
                f"- FORBIDDEN: 'Atomic Habits', 'The Power of Now', 'Rich Dad Poor Dad', 'The 7 Habits of Highly Effective People', 'Think and Grow Rich'.\n"
                f"{_excl_en}"
                f"- Choose a real, valuable book that is NOT the most obvious one in the category.\n"
                f"- Rotate between: 20th-century classics, modern books (2010-2024), authors from different continents.\n"
                f"- Exact format: 'Book Title — Author'\n"
                f"- Return ONLY the title and author. Nothing else."
            )
        elif mode == "biblia":
            _excl = exclude_books or []
            _excl_es = (f"- PROHIBIDO repetir estos pasajes/temas ya vistos: {', '.join(_excl)}.\n") if _excl else ""
            _excl_en = (f"- FORBIDDEN to repeat these already-seen passages/themes: {', '.join(_excl)}.\n") if _excl else ""
            prompt = (
                f"Eres un experto en contenido bíblico y espiritual. Sugiere UN pasaje bíblico o tema espiritual de la categoría: {category}.\n"
                f"Semilla: {seed} — úsala para variar entre versículos, parábolas, temas y libros bíblicos.\n"
                f"REGLAS:\n"
                f"{_excl_es}"
                f"- Puede ser: un versículo específico (ej. 'Juan 3:16'), una parábola, un tema bíblico (ej. 'La fe que mueve montañas').\n"
                f"- Formato: 'Tema o versículo — referencia bíblica (si aplica)'\n"
                f"- Responde ÚNICAMENTE con el tema/versículo. Nada más."
            ) if lang == "es" else (
                f"You are an expert in biblical and spiritual content. Suggest ONE Bible passage or spiritual theme from the category: {category}.\n"
                f"Seed: {seed} — use it to vary between verses, parables, themes, and biblical books.\n"
                f"RULES:\n"
                f"{_excl_en}"
                f"- It can be: a specific verse (e.g. 'John 3:16'), a parable, a biblical theme (e.g. 'Faith that moves mountains').\n"
                f"- Format: 'Theme or verse — biblical reference (if applicable)'\n"
                f"- Return ONLY the theme/verse. Nothing else."
            )
        elif mode == "ciencia_facil":
            prompt = (
                f"Eres un divulgador científico para gente común. Dame 1 fenómeno, dato o experimento REAL "
                f"de la categoría: {category}. "
                f"Debe ser algo sorprendente que le pase a cualquier persona en su vida diaria "
                f"o que pueda explicarse con una analogía cotidiana. "
                f"PROHIBIDO: temas demasiado técnicos, jerga científica en el título, contenido académico aburrido. "
                f"EJEMPLOS del estilo correcto: 'Por qué el cielo es azul y no violeta si la luz violeta es mas energetica', "
                f"'El efecto Mpemba: por que el agua caliente se congela antes que la fria', "
                f"'Por que sientes el estomago en la garganta cuando bajas rapido en un elevador'. "
                f"Semilla: {seed}. "
                f"{_excl_block_es}"
                f"Responde ÚNICAMENTE con el nombre del tema, nada más. En español."
            ) if lang == "es" else (
                f"You are a science communicator for everyday people. Give me 1 REAL phenomenon, fact or experiment "
                f"from the category: {category}. "
                f"It must be something surprising that happens to anyone in daily life "
                f"or that can be explained with a relatable everyday analogy. "
                f"FORBIDDEN: overly technical topics, jargon in the title, boring academic content. "
                f"CORRECT STYLE EXAMPLES: 'Why the sky is blue and not violet if violet light has more energy', "
                f"'The Mpemba effect: why hot water freezes faster than cold water', "
                f"'Why you feel your stomach drop when an elevator goes down fast'. "
                f"Seed: {seed}. "
                f"{_excl_block_en}"
                f"Return ONLY the topic name, nothing else."
            )
        else:
            prompt = (
                f"Dame 1 tema específico y fascinante para un Short Documental "
                f"en la categoría: {category}. "
                f"Debe ser un dato real y verificable, o un evento histórico poco conocido pero documentado. "
                f"Semilla de unicidad: {seed}. "
                f"{_real_warning_es}"
                f"{_excl_block_es}"
                f"Responde ÚNICAMENTE con el nombre del tema, nada más. En español."
            ) if lang == "es" else (
                f"Give me 1 specific and fascinating topic for a Short Documentary "
                f"in the category of: {category}. "
                f"Must be a real, verifiable fact or a little-known but documented historical event. "
                f"Seed for uniqueness: {seed}. "
                f"{_real_warning_en}"
                f"{_excl_block_en}"
                f"Return ONLY the topic name, nothing else."
            )

        topic = self._generate(prompt).strip()
        print(f"🎯 Auto Topic [{category}]: {topic}")
        return topic

    def _verify_topic_is_real(self, topic: str, lang: str = "es") -> bool:
        """Ask the LLM to fact-check its own topic suggestion.
        Returns True if real/documented, False if invented/uncertain.
        Costs ~1 small LLM call but prevents publishing fabricated history."""
        if lang == "es":
            prompt = (
                f"Actúa como un verificador de hechos estricto.\n"
                f"Tema propuesto: \"{topic}\"\n\n"
                f"Pregunta: ¿Este evento/hecho REALMENTE OCURRIÓ y está documentado en "
                f"Wikipedia, enciclopedias históricas, archivos oficiales o libros de historia reconocidos?\n\n"
                f"CRITERIO: Si el evento mezcla personas reales con acciones que NO están documentadas "
                f"(ej. 'Hitler ordenó X' pero esa orden específica no existe en ningún archivo), "
                f"o si incluye fechas/operaciones inventadas → es INVENTADO.\n\n"
                f"Responde ÚNICAMENTE con una de estas dos palabras:\n"
                f"REAL → si está documentado y verificable\n"
                f"INVENTADO → si es falso, incierto, o mezcla hechos reales con detalles fabricados"
            )
        else:
            prompt = (
                f"Act as a strict fact-checker.\n"
                f"Proposed topic: \"{topic}\"\n\n"
                f"Question: Did this event/fact REALLY HAPPEN and is it documented in "
                f"Wikipedia, historical encyclopedias, official archives, or recognized history books?\n\n"
                f"CRITERION: If the event mixes real people with actions that are NOT documented "
                f"(e.g. 'Hitler ordered X' but that specific order exists in no archive), "
                f"or if it includes invented dates/operations → it is INVENTED.\n\n"
                f"Answer ONLY with one of these two words:\n"
                f"REAL → if documented and verifiable\n"
                f"INVENTED → if false, uncertain, or mixes real facts with fabricated details"
            )
        result = self._generate(prompt).strip().upper()
        is_real = "REAL" in result and "INVENTADO" not in result and "INVENTED" not in result
        if not is_real:
            print(f"   ⚠️ Fact-check FAILED for: '{topic}' → result: {result}")
        return is_real

    def get_topic_suggestions(self, category: str, n: int = 6, lang: str = "es",
                               used_topics: list = None) -> list:
        label = "Generando sugerencias para" if lang == "es" else "Generating suggestions for"
        print(f"💡 {label}: {category}...")
        _excl_block_es = _excl_block_en = ""  # dedup done locally after generation, no tokens

        if lang == "es":
            prompt = f"""Eres un investigador experto en contenido viral para YouTube Shorts. Tu especialidad es encontrar HECHOS REALES que la gente no conoce.

Categoría: "{category}"

TAREA: Dame exactamente {n} temas REALES de la categoría indicada. Deben provenir de:
- Noticias reales documentadas (pueden ser recientes o históricas)
- Leyendas o mitos populares que circulan en internet y la cultura popular
- Teorías de conspiración conocidas que la gente discute actualmente
- Fábulas o historias tradicionales con trasfondo real o histórico
- Misterios no resueltos reconocidos por la ciencia o la historia
- Experimentos, eventos o descubrimientos científicos reales poco conocidos

REGLAS ABSOLUTAS:
- PROHIBIDO inventar eventos, personas o datos que no existan.
- PROHIBIDO mezclar hechos reales con detalles ficticios o inventados.
- PROHIBIDO crear títulos que combinen personas históricas reales con acciones que NO están documentadas en ningún archivo o enciclopedia (ej. "Hitler planeó X" si esa operación específica no existe en registros históricos).
- Antes de sugerir cada tema, pregúntate: ¿Puedo encontrar esto en Wikipedia o en un libro de historia reconocido? Si la respuesta es NO → no lo incluyas.
- Cada tema debe ser algo que realmente ocurrió, que realmente se dice, o que realmente existe como leyenda o teoría en la cultura popular.
- Longitud: máximo 12 palabras por tema.
- Estilo: titular directo, que genere curiosidad real.
- Idioma: español neutro latino. Evita palabras con la letra ñ — usa alternativas naturales (ej: "anio" en vez de "año", "senor" en vez de "señor", "Espana" en vez de "España").

FUENTES VÁLIDAS de donde debes extraer (usa tu conocimiento entrenado):
- Historia documentada mundial
- Teorías de conspiración populares (Área 51, Illuminati, reptilianos, etc.)
- Leyendas urbanas conocidas (La Llorona, El Chupacabras, etc.)
- Misterios históricos reales (El Triángulo de las Bermudas, El Arca Perdida, etc.)
- Noticias científicas o sociales reales de los últimos años
- Fábulas con origen histórico verificable
{_excl_block_es}
FORMATO DE SALIDA (JSON estricto, sin markdown):
["tema 1", "tema 2", "tema 3", "tema 4", "tema 5", "tema 6"]"""
        else:
            prompt = f"""You are an expert researcher in viral YouTube Shorts content. Your specialty is finding REAL FACTS that most people don't know about.

Category: "{category}"

TASK: Give me exactly {n} REAL topics from the given category. They must come from:
- Real documented news events (recent or historical)
- Popular legends or myths circulating on the internet and in popular culture
- Known conspiracy theories that people actively discuss
- Fables or traditional stories with a real or historical background
- Unsolved mysteries acknowledged by science or history
- Real lesser-known scientific experiments, events, or discoveries

ABSOLUTE RULES:
- FORBIDDEN: inventing events, people, or data that do not exist.
- FORBIDDEN: mixing real facts with fictional details or invented actions.
- FORBIDDEN: creating titles that combine real historical figures with actions that are NOT documented in any archive or encyclopedia (e.g. "Hitler planned X" if that specific operation doesn't exist in historical records).
- Before suggesting each topic ask yourself: Can this be found in Wikipedia or a recognized history book? If NO → do not include it.
- Each topic must be something that actually happened, is actually said, or actually exists as a legend or theory in popular culture.
- Length: maximum 12 words per topic.
- Style: direct headline that creates genuine curiosity.

VALID SOURCES to draw from (use your trained knowledge):
- Documented world history
- Popular conspiracy theories (Area 51, Illuminati, reptilians, flat earth, etc.)
- Known urban legends (Bigfoot, Loch Ness, Bermuda Triangle, etc.)
- Real historical mysteries (Lost Ark, Atlantis, Stonehenge, etc.)
- Real scientific or social news from recent years
- Fables with verifiable historical origins
{_excl_block_en}
OUTPUT FORMAT (strict JSON, no markdown):
["topic 1", "topic 2", "topic 3", "topic 4", "topic 5", "topic 6"]"""

        raw = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()
        try:
            suggestions = json.loads(clean)
            if isinstance(suggestions, list) and len(suggestions) > 0:
                suggestions = [s.strip() for s in suggestions if isinstance(s, str)]
            else:
                raise ValueError
        except Exception:
            lines = [
                l.strip().strip('"').strip("'").strip('-').strip()
                for l in clean.splitlines() if l.strip()
            ]
            suggestions = [l for l in lines if len(l) > 10]

        # ── Local dedup — filter out topics too similar to already-used ones (zero tokens) ──
        try:
            from modules.topic_history import is_duplicate as _is_dup
            suggestions = [s for s in suggestions if not _is_dup(s, lang=lang)]
        except Exception:
            pass

        return suggestions[:n] or [f"Viral topic about {category}"]

    @staticmethod
    def _sanitize(text: str) -> str:
        """Remove special Unicode characters that break TTS or JSON parsing."""
        replacements = {
            "\u2014": "-", "\u2013": "-",   # em-dash, en-dash
            "\u2018": "'", "\u2019": "'",   # curly single quotes
            "\u201c": '"', "\u201d": '"',   # curly double quotes
            "\u2026": "...",                # ellipsis character
            "\u00ab": '"', "\u00bb": '"',   # guillemets
            "\u2022": "-",                  # bullet
        }
        for char, rep in replacements.items():
            text = text.replace(char, rep)
        return text

    def _parse_scenes(self, raw: str, num_scenes: int, label: str,
                      default_mood: str,
                      fallback_visual_1: str = "dramatic cinematic footage",
                      fallback_visual_2: str = "historical documentary",
                      success_label: str = None) -> list:
        """Mecánica común de parseo para los generate_*_script de patrón estándar.

        Limpia las vallas ```json, parsea el array, normaliza id/text/mood,
        recorta a num_scenes y, si el JSON falla, cae a un fallback por frases.
        Los modos con lógica especial (visual_3 atmosférico, speaker de podcast,
        etc.) NO usan este helper y conservan su parseo propio.
        """
        import re as _re
        clean = raw.replace('```json', '').replace('```', '').strip()
        try:
            scenes = json.loads(clean)
            for i, s in enumerate(scenes):
                s['id']   = i + 1
                s['text'] = self._sanitize(s.get('text', ''))
                s.setdefault('mood', default_mood)
            if len(scenes) > num_scenes:
                print(f"⚠️ AI returned {len(scenes)} {label} scenes, trimming to {num_scenes}.")
                scenes = scenes[:num_scenes]
            elif len(scenes) < num_scenes:
                print(f"⚠️ AI returned only {len(scenes)} {label} scenes (requested {num_scenes}).")
            print(f"✅ {len(scenes)} {success_label or label} scenes ready")
            return scenes
        except Exception:
            sentences = [s.strip() for s in _re.split(r'(?<=[.!?])\s+', clean) if len(s.strip()) > 8][:num_scenes]
            return [
                {"id": i + 1, "text": self._sanitize(s),
                 "visual_1": fallback_visual_1, "visual_2": fallback_visual_2,
                 "mood": default_mood}
                for i, s in enumerate(sentences)
            ]

    def get_topic_and_description(self, manual_topic: str = "", category: str = "",
                                   mode: str = "auto", lang: str = "es",
                                   exclude_books: list = None) -> dict:
        """Resuelve el tema final y genera una descripción breve de 1-2 oraciones.
        Retorna {"topic": str, "description": str}"""
        # Step 1: resolve topic (uses existing logic with category/mode fallback)
        topic = self.get_trending_topic(manual_topic, lang=lang,
                                        category_hint=category, mode=mode,
                                        exclude_books=exclude_books or [])

        # Quality checks — only when topic was auto-generated (no manual input)
        if not manual_topic.strip():
            try:
                from modules.topic_history import is_duplicate as _is_dup
            except Exception:
                _is_dup = None

            for _retry in range(4):
                _dup = _is_dup(topic, lang=lang) if _is_dup else False
                _fake = not self._verify_topic_is_real(topic, lang=lang)
                if not _dup and not _fake:
                    break
                reason = "duplicado" if _dup else "inventado/no verificado"
                print(f"   ♻️ Topic {reason}, regenerando ({_retry+1}/4): '{topic}'")
                topic = self.get_trending_topic("", lang=lang,
                                                category_hint=category, mode=mode,
                                                exclude_books=exclude_books or [])

        # Step 2: generate a 1-2 sentence teaser about the video
        _tone_hint = {
            "viral":      ("oscuro, impactante, histórico" if lang == "es" else "dark, shocking, historical"),
            "testimonio": ("misterioso, perturbador, cinematográfico" if lang == "es" else "mysterious, disturbing, cinematic"),
            "libro":      ("inspirador, revelador, educativo" if lang == "es" else "inspiring, revealing, educational"),
            "biblia":     ("espiritual, esperanzador, edificante" if lang == "es" else "spiritual, hopeful, uplifting"),
            "auto":       ("viral, curioso, impactante" if lang == "es" else "viral, curious, shocking"),
            "category":   ("viral, curioso, impactante" if lang == "es" else "viral, curious, shocking"),
        }.get(mode, ("interesante, impactante" if lang == "es" else "interesting, impactful"))

        if lang == "es":
            prompt = (
                f"Tema del video: \"{topic}\"\n\n"
                f"Escribe exactamente 2 oraciones cortas (maximo 35 palabras en total) que describan:\n"
                f"1. El hecho o dato central que revelara el video.\n"
                f"2. Por que es impactante o fascinante para el espectador.\n\n"
                f"Tono: {_tone_hint}.\n"
                f"PROHIBIDO: preguntas retorica, emojis, spoilers completos, caracteres especiales.\n"
                f"Responde SOLO las 2 oraciones, sin introduccion ni explicacion."
            )
        else:
            prompt = (
                f"Video topic: \"{topic}\"\n\n"
                f"Write exactly 2 short sentences (maximum 35 words total) describing:\n"
                f"1. The central fact or revelation the video will uncover.\n"
                f"2. Why it's shocking or fascinating for the viewer.\n\n"
                f"Tone: {_tone_hint}.\n"
                f"FORBIDDEN: rhetorical questions, emojis, complete spoilers, special characters.\n"
                f"Respond ONLY with the 2 sentences, no intro or explanation."
            )

        description = self._sanitize(self._generate(prompt).strip())
        print(f"🎯 Topic resolved: {topic}")
        print(f"📝 Description: {description}")
        return {"topic": topic, "description": description}

    def recommend_voice(self, topic: str, category: str, mode: str, lang: str,
                        tts_engine: str, voice_options: list) -> str:
        """Picks the most suitable voice label from voice_options for the given topic/mode."""
        if not voice_options:
            return ""
        mood_es = {
            "testimonio": "voz masculina profunda, misteriosa, que genere suspenso",
            "libro":      "voz cálida, clara e inspiradora",
            "biblia":     "voz cálida, tranquila y espiritual",
            "viral":      "voz enérgica e impactante",
            "novela":     "voz dramática y expresiva",
            "podcast":    "voz natural y conversacional",
        }.get(mode, "voz clara y atractiva")
        mood_en = {
            "testimonio": "deep, mysterious, suspenseful male voice",
            "libro":      "warm, clear, inspiring voice",
            "biblia":     "warm, calm, spiritual voice",
            "viral":      "energetic, impactful voice",
            "novela":     "dramatic, expressive voice",
            "podcast":    "natural, conversational voice",
        }.get(mode, "clear, engaging voice")
        opts_text = "\n".join(f"- {v}" for v in voice_options[:25])
        if lang == "es":
            prompt = (
                f"Eres un director de casting de voz para videos de redes sociales.\n"
                f"Contexto del video:\n"
                f"- Tema: {topic}\n"
                f"- Categoría: {category}\n"
                f"- Modo: {mode}\n"
                f"- Personalidad ideal: {mood_es}\n\n"
                f"Elige UNA voz de esta lista que mejor encaje:\n{opts_text}\n\n"
                f"Responde ÚNICAMENTE con el nombre EXACTO de la voz tal como aparece en la lista. Nada más."
            )
        else:
            prompt = (
                f"You are a voice casting director for social media videos.\n"
                f"Video context:\n"
                f"- Topic: {topic}\n"
                f"- Category: {category}\n"
                f"- Mode: {mode}\n"
                f"- Ideal personality: {mood_en}\n\n"
                f"Choose ONE voice from this list that fits best:\n{opts_text}\n\n"
                f"Respond ONLY with the EXACT voice name as it appears in the list. Nothing else."
            )
        raw = self._generate(prompt).strip()
        for opt in voice_options:
            if raw == opt:
                return opt
        for opt in voice_options:
            if raw[:30] in opt or opt[:30] in raw:
                return opt
        return voice_options[0]

    def get_hook_options(self, topic: str, category: str, mode: str = "auto", lang: str = "es", n: int = 3) -> list:
        """Genera N opciones de gancho viral para un tema dado.
        Si topic está vacío, usa la categoría como contexto principal."""

        # Construir el contexto de forma robusta — nunca dejar vacío
        topic   = (topic   or "").strip()
        category = (category or "").strip()

        if topic and category:
            ctx = f"{topic} (categoría: {category})" if lang == "es" else f"{topic} (category: {category})"
        elif topic:
            ctx = topic
        elif category:
            ctx = category
        else:
            ctx = "contenido viral misterioso" if lang == "es" else "viral mystery content"

        # Tipos de hook por modo
        if mode == "testimonio":
            types_es = (
                "- TIPO A: cifra impactante + hecho perturbador ('17 personas desaparecieron la misma noche. Nadie explica como.')\n"
                "- TIPO B: revelacion del testigo ('Lo que este ex-miembro revelo sobre [X] cambio todo.')\n"
                "- TIPO C: secreto oculto ('Nadie habla de lo que paso realmente en [X].')\n"
            )
            types_en = (
                "- TYPE A: shocking number + disturbing fact ('17 people vanished the same night. No one explains how.')\n"
                "- TYPE B: witness reveal ('What this ex-member revealed about [X] changed everything.')\n"
                "- TYPE C: hidden secret ('Nobody talks about what really happened at [X].')\n"
            )
            tone_es = "oscuro y perturbador, estilo testimonio real de horror"
            tone_en = "dark and disturbing, real horror testimony style"
        elif mode == "libro":
            types_es = (
                "- TIPO A: verdad incomoda del libro ('La mayoria trabaja mas duro pero gana menos. Este libro explica por que.')\n"
                "- TIPO B: creencia que el libro destruye ('Todo lo que te ensenaron sobre [X] esta equivocado, segun este libro.')\n"
                "- TIPO C: dato que el libro revela ('Lo que nadie te cuenta sobre [X] esta en este libro.')\n"
            )
            types_en = (
                "- TYPE A: uncomfortable truth from the book ('Most people work harder but earn less. This book explains why.')\n"
                "- TYPE B: belief the book destroys ('Everything you were taught about [X] is wrong, according to this book.')\n"
                "- TYPE C: what the book reveals ('What nobody tells you about [X] is in this book.')\n"
            )
            tone_es = "inspirador e intrigante, que motive a leer el libro"
            tone_en = "inspiring and intriguing, motivating to read the book"
        elif mode == "biblia":
            types_es = (
                "- TIPO A: promesa poderosa ('Dios prometio que nunca te abandonaria. Y hay un versiculo que lo prueba.')\n"
                "- TIPO B: verdad que transforma ('La mayoria no conoce este versiculo. Pero cambia todo.')\n"
                "- TIPO C: pregunta espiritual ('¿Que hace Dios cuando sientes que ya no puedes mas?')\n"
            )
            types_en = (
                "- TYPE A: powerful promise ('God promised He would never leave you. And there is a verse that proves it.')\n"
                "- TYPE B: transforming truth ('Most people don't know this verse. But it changes everything.')\n"
                "- TYPE C: spiritual question ('What does God do when you feel like you can't go on?')\n"
            )
            tone_es = "espiritual, esperanzador y edificante, que toque el corazon"
            tone_en = "spiritual, hopeful and uplifting, touching the heart"
        elif mode in ("true_crime", "psicologia_oscura", "conspiracion"):
            types_es = (
                "- TIPO A (Revelacion oscura): hecho perturbador real ('Lo que encontraron en esa casa no debia existir.')\n"
                "- TIPO B (Dato shockeante): cifra + contexto impactante ('17 victimas. Un solo culpable. Y nadie lo busco.')\n"
                "- TIPO C (Secreto oculto): 'Nadie habla de lo que paso realmente con [X].'\n"
            )
            types_en = (
                "- TYPE A (Dark reveal): real disturbing fact ('What they found in that house should not have existed.')\n"
                "- TYPE B (Shocking stat): number + impactful context ('17 victims. One perpetrator. And nobody looked.')\n"
                "- TYPE C (Hidden secret): 'Nobody talks about what really happened with [X].'\n"
            )
            tone_es = "oscuro e investigativo, estilo documental criminal adictivo"
            tone_en = "dark and investigative, addictive criminal documentary style"
        elif mode == "ciencia_misterio":
            types_es = (
                "- TIPO A (Dato cientifico asombroso): hecho verificable que rompe creencias ('La fisica cuantica prueba que el tiempo no existe como crees.')\n"
                "- TIPO B (Pregunta sin respuesta): '¿Por que los cientificos no pueden explicar [X]?'\n"
                "- TIPO C (Descubrimiento oculto): 'Este experimento estuvo clasificado durante 40 anos.'\n"
            )
            types_en = (
                "- TYPE A (Amazing scientific fact): verifiable fact that breaks beliefs ('Quantum physics proves time does not exist as you think.')\n"
                "- TYPE B (Unanswered question): 'Why can scientists not explain [X]?'\n"
                "- TYPE C (Hidden discovery): 'This experiment was classified for 40 years.'\n"
            )
            tone_es = "cientifico y misterioso, mezcla de rigor y asombro"
            tone_en = "scientific and mysterious, blend of rigor and awe"
        elif mode == "mentalidad":
            types_es = (
                "- TIPO A (Dato conductual): cifra real + causa contraintuitiva ('El 92% abandona su meta antes de febrero. La causa no es falta de voluntad.')\n"
                "- TIPO B (Mito destruido): creencia popular que la investigacion desmonta ('Los habitos NO se forman en 21 dias. Ese numero salio de leer mal un estudio.')\n"
                "- TIPO C (Mecanismo oculto): explica el porque real detras de la conducta ('Tu cerebro no procrastina por pereza. Esta evitando una emocion concreta.')\n"
                "- TIPO D (Accion minima): promesa de algo aplicable hoy en segundos ('30 segundos de accion rompen el ciclo. Asi funciona.')\n"
            )
            types_en = (
                "- TYPE A (Behavioral fact): real stat + counterintuitive cause ('92% quit their goal before February. The cause is not willpower.')\n"
                "- TYPE B (Myth destroyed): popular belief research dismantles ('Habits do NOT form in 21 days. That number came from misreading a study.')\n"
                "- TYPE C (Hidden mechanism): explain the real why behind the behavior ('Your brain does not procrastinate out of laziness. It is avoiding a specific emotion.')\n"
                "- TYPE D (Minimum action): promise something applicable today in seconds ('30 seconds of action breaks the loop. Here is how.')\n"
            )
            tone_es = "practico y revelador, estilo conferencia TED: rigor sin sermon, cero frases de superacion vacias"
            tone_en = "practical and revealing, TED talk style: rigor without preaching, zero empty self-help lines"
        elif mode in ("finanzas", "historia_epica"):
            types_es = (
                "- TIPO A (Verdad incomoda): dato que desafia la mentalidad comun ('El 95% trabaja mas duro pero sigue siendo pobre. Esta es la razon.')\n"
                "- TIPO B (Secreto de exito): 'Lo que los ricos hacen diferente y nunca te contaron.'\n"
                "- TIPO C (Hecho epico): evento real impactante que inspira o sacude ('En 1920 este hombre perdio todo. 10 anos despues controlaba el mundo.')\n"
            )
            types_en = (
                "- TYPE A (Uncomfortable truth): fact challenging common mindset ('95% work harder but stay poor. Here is the reason.')\n"
                "- TYPE B (Success secret): 'What the rich do differently and never told you.'\n"
                "- TYPE C (Epic fact): impactful real event that inspires or shocks ('In 1920 this man lost everything. 10 years later he controlled the world.')\n"
            )
            tone_es = "inspirador e impactante, estilo conferencia TED + historia epica"
            tone_en = "inspiring and impactful, TED talk + epic history style"
        elif mode in ("psicologia_positiva", "mente_masculina", "mujer_consciente"):
            types_es = (
                "- TIPO A (Verdad emocional): frase que toca el corazon ('Nadie te enseno que puedes amarte sin explicaciones.')\n"
                "- TIPO B (Pregunta reflexiva): '¿Y si todo lo que crees sobre [X] te esta limitando?'\n"
                "- TIPO C (Promesa de transformacion): 'Esto cambio todo para miles de personas que sintieron lo mismo que tu.'\n"
            )
            types_en = (
                "- TYPE A (Emotional truth): phrase that touches the heart ('Nobody taught you that you can love yourself without explanations.')\n"
                "- TYPE B (Reflective question): 'What if everything you believe about [X] is limiting you?'\n"
                "- TYPE C (Transformation promise): 'This changed everything for thousands who felt exactly like you.'\n"
            )
            tone_es = "emocional y sanador, estilo psicologia moderna con calidez"
            tone_en = "emotional and healing, modern psychology style with warmth"
        elif mode == "indignacion":
            types_es = (
                "- TIPO A (Red flag laboral): oferta o situacion absurda real ('Empresa pide 5 anos de experiencia para un trabajo de practicas. Sueldo: 600 euros.')\n"
                "- TIPO B (Sarcasmo laboral): 'El jefe que lleva 3 anos diciendote que ya viene tu aumento.'\n"
                "- TIPO C (Indignacion pura): dato injusto que enciende al espectador ('El CEO gano 400 veces mas que sus empleados. Y los despidio igual.')\n"
            )
            types_en = (
                "- TYPE A (Work red flag): real absurd offer or situation ('Company asks for 5 years experience for an internship. Salary: 600 euros.')\n"
                "- TYPE B (Work sarcasm): 'The boss who has been saying your raise is coming for 3 years.'\n"
                "- TYPE C (Pure outrage): unfair fact that fires up the viewer ('The CEO earned 400 times more than his employees. And still laid them off.')\n"
            )
            tone_es = "indignado y sarcastico, estilo humor negro laboral que viraliza"
            tone_en = "outraged and sarcastic, dark work humor style that goes viral"
        elif mode == "ciencia_facil":
            types_es = (
                "- TIPO A (Dato sorprendente cotidiano): hecho cientifico real que pasa en la vida diaria ('Tu cerebro no puede distinguir entre recuerdo real e imaginado. Lo comprobaron en 1974.')\n"
                "- TIPO B (Pregunta que no te esperabas): pregunta simple con respuesta sorprendente ('¿Por que los cubos de hielo del supermercado tienen un agujero en el centro?')\n"
                "- TIPO C (Creencia popular destruida): algo que creías que era de una forma y no lo es ('Todo el mundo piensa que tragarse chicle es peligroso. La ciencia dice lo contrario.')\n"
            )
            types_en = (
                "- TYPE A (Surprising daily fact): real science fact that happens in everyday life ('Your brain cannot tell the difference between a real memory and an imagined one. Proven in 1974.')\n"
                "- TYPE B (Question you didn't expect): simple question with surprising answer ('Why do supermarket ice cubes have a hole in the middle?')\n"
                "- TYPE C (Popular belief destroyed): something you thought worked one way and it doesn't ('Everyone thinks swallowing gum is dangerous. Science says the opposite.')\n"
            )
            tone_es = "curioso y cercano, como un amigo listo que te explica algo alucinante sin tecnicismos"
            tone_en = "curious and relatable, like a smart friend explaining something mind-blowing without jargon"
        else:  # auto, category, viral
            types_es = (
                "- TIPO A (Numero shockeante): cifra + consecuencia brutal ('40.000 personas murieron en 48 horas. Nadie lo investigo.')\n"
                "- TIPO B (Controversia): 'Todo lo que sabes sobre [X] esta completamente equivocado.'\n"
                "- TIPO C (Curiosidad): 'Nadie habla de lo que paso realmente con [X].'\n"
            )
            types_en = (
                "- TYPE A (Shocking number): stat + brutal consequence ('40,000 people died in 48 hours. Nobody investigated.')\n"
                "- TYPE B (Controversy): 'Everything you know about [X] is completely wrong.'\n"
                "- TYPE C (Curiosity): 'Nobody is talking about what really happened with [X].'\n"
            )
            tone_es = "viral e impactante, estilo MrBeast + Dark History"
            tone_en = "viral and impactful, MrBeast + Dark History style"

        if lang == "es":
            prompt = f"""Eres experto en ganchos virales para YouTube Shorts. El espectador decide si sigue viendo en 1.7 segundos.

Contexto del video: "{ctx}"
Tono requerido: {tone_es}

TAREA: Genera exactamente {n} hooks distintos para la Escena 1. Cada uno de un tipo diferente:
{types_es}
REGLAS ABSOLUTAS:
- Maximo 12 palabras por hook
- Sin emojis, sin caracteres especiales, sin comillas rizadas
- Concreto y especifico al contexto — PROHIBIDO ser generico
- Cada hook debe crear curiosidad INMEDIATA e IRRESISTIBLE
- PROHIBIDO responder con explicaciones, solo el JSON

FORMATO (JSON estricto, sin markdown, sin texto extra):
["hook A aqui", "hook B aqui", "hook C aqui"]"""
        else:
            prompt = f"""You are an expert in viral hooks for YouTube Shorts. The viewer decides in 1.7 seconds.

Video context: "{ctx}"
Required tone: {tone_en}

TASK: Generate exactly {n} distinct hooks for Scene 1. Each a different type:
{types_en}
ABSOLUTE RULES:
- Maximum 12 words per hook
- No emojis, no special characters, no curly quotes
- Concrete and specific to the context — GENERIC hooks are FORBIDDEN
- Each hook must create IMMEDIATE and IRRESISTIBLE curiosity
- FORBIDDEN to respond with explanations, only the JSON

FORMAT (strict JSON, no markdown, no extra text):
["hook A here", "hook B here", "hook C here"]"""

        raw   = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()
        # Strip any leading text before the JSON array
        bracket = clean.find('[')
        if bracket > 0:
            clean = clean[bracket:]
        try:
            hooks = json.loads(clean)
            if isinstance(hooks, list):
                result = [self._sanitize(h.strip()) for h in hooks if isinstance(h, str) and len(h.strip()) > 5]
                if result:
                    return result[:n]
        except Exception:
            pass
        # Fallback: extract quoted strings
        import re as _re
        quoted = _re.findall(r'"([^"]{10,})"', raw)
        if quoted:
            return [self._sanitize(q) for q in quoted[:n]]
        lines = [l.strip().strip('"').strip("'").strip('-').strip() for l in raw.splitlines() if len(l.strip()) > 10]
        return [self._sanitize(l) for l in lines if len(l) > 10][:n] or [ctx[:60]]

    def generate_viral_script(self, topic: str, category: str, lang: str = "es", chosen_hook: str = "", num_scenes: int = 9, max_words_per_scene: int = 999) -> list:
        """Genera un guion viral ultra-retención (45-60 seg) con estructura MrBeast/Dark History.
        Single-call: produce JSON scenes directly — no second AI call, no text modification."""
        import re as _re
        label = "Generando guion viral" if lang == "es" else "Generating viral script"
        print(f"🔥 {label}: {topic}...")

        if lang == "es":
            prompt = f"""Eres el mejor guionista de YouTube Shorts especializado en hechos historicos impactantes, near misses, catastrofes evitadas, mortandades misteriosas y misterios sin resolver.

Tu objetivo es crear Shorts que generen maxima retencion y shares (estilo MrBeast + The Why Files + Dark History).

REGLAS OBLIGATORIAS:
- Duracion total: ~{num_scenes * 5} segundos (maximo {num_scenes * 17} palabras en total sumando todos los campos "text").
- MAXIMO {max_words_per_scene} palabras por escena en el campo "text" — es critico para sincronizar con el clip de video.
- EXACTAMENTE {num_scenes} escenas — ni una mas, ni una menos.
- Estructura EXACTA en el orden de las escenas:
  Escena 1: HOOK VIRAL (CRITICO - maximo 12 palabras, el espectador decide en 1.7 seg):
    Elige OBLIGATORIAMENTE uno de estos 4 tipos:
    TIPO A-NUMERO: "[CIFRA] [personas/dias/años] [consecuencia brutal]." Ej: "40.000 personas murieron en 48 horas. Nadie lo investigo."
    TIPO B-CONTROVERSIA: "Todo lo que sabes sobre [ELEMENTO ESPECIFICO DEL TEMA] esta completamente equivocado."
    TIPO C-CURIOSIDAD: "Nadie esta hablando de lo que paso realmente con [ELEMENTO DEL TEMA]."
    TIPO D-PREGUNTA TRAMPA: "¿Que harias si descubrieras que [AFIRMACION IMPACTANTE Y ESPECIFICA]?"
    El hook debe ser IMPOSIBLE de ignorar.
  Escenas 2-{max(3, num_scenes - 3)}: CONTEXTO + DESARROLLO - Situacion historica, detalles brutales, datos desconocidos.
  Escena {num_scenes - 1}: TWIST FINAL - Revelacion impactante, ironia o "lo que paso despues".
  Escena {num_scenes}: CTA - "Comenta QUE MAS si queres la parte 2. Sigueme para mas historia oscura."
- Lenguaje dramatico, conversacional y adictivo. Usa MAYUSCULAS para enfasis.
- PROHIBIDO: emojis, caracteres especiales Unicode (guiones largos, comillas rizadas, puntos suspensivos especiales), la letra ñ (usa alternativas: "anio" por "año", "senor" por "señor").
- USA SOLO: letras, numeros, comas, puntos, signos de exclamacion, signos de interrogacion y apostrofes simples.
- En espanol neutro latino. Nunca digas "hoy te voy a contar" ni "vamos a hablar de".

Tema: {topic}
Categoria: {category}{f'{chr(10)}HOOK PRE-SELECCIONADO (OBLIGATORIO usar este texto EXACTO en Escena 1): "{chosen_hook}"' if chosen_hook else ""}

FORMATO DE SALIDA: JSON estricto, sin markdown, sin texto fuera del JSON:
[
  {{"id":1,"text":"texto de la escena aqui","visual_1":"english pexels term","visual_2":"english pexels term","mood":"dramatic"}},
  {{"id":2,"text":"texto de la escena aqui","visual_1":"english pexels term","visual_2":"english pexels term","mood":"dramatic"}}
]

REGLAS DEL JSON:
- EXACTAMENTE {num_scenes} entradas — no mas, no menos.
- "text": el texto narrado de esa escena. Sin emojis. Sin caracteres especiales.
- "visual_1" y "visual_2": terminos de busqueda en INGLES para Pexels (2-4 palabras), que coincidan con el contenido.
- "mood": siempre "dramatic"."""
        else:
            prompt = f"""You are the best YouTube Shorts scriptwriter specialized in shocking historical facts, near misses, avoided catastrophes, mysterious deaths and unsolved mysteries.

Your goal: maximum retention and shares (MrBeast + The Why Files + Dark History style).

MANDATORY RULES:
- LANGUAGE: ENGLISH ONLY. Every single word must be in English. No Spanish words whatsoever.
- Total duration: ~{num_scenes * 5} seconds (maximum {num_scenes * 17} words total across all "text" fields).
- MAXIMUM {max_words_per_scene} words per scene in the "text" field — critical for video clip sync.
- EXACTLY {num_scenes} scenes — no more, no fewer.
- EXACT scene structure:
  Scene 1: VIRAL HOOK (CRITICAL - max 12 words, viewer decides in 1.7 sec):
    MANDATORY — pick ONE of these 4 hook types:
    TYPE A-NUMBER: "[SHOCKING NUMBER] [people/days/years] [brutal consequence]." E.g.: "40,000 people died in 48 hours. Nobody investigated."
    TYPE B-CONTROVERSY: "Everything you know about [SPECIFIC TOPIC ELEMENT] is completely wrong."
    TYPE C-CURIOSITY: "Nobody is talking about what really happened with [SPECIFIC ELEMENT]."
    TYPE D-TRAP QUESTION: "What would you do if you found out that [SHOCKING SPECIFIC STATEMENT]?"
    The hook must be IMPOSSIBLE to scroll past.
  Scenes 2-{max(3, num_scenes - 3)}: QUICK CONTEXT + DEVELOPMENT - Historical situation, brutal details, unknown facts.
  Scene {num_scenes - 1}: FINAL TWIST - Shocking revelation, irony or "what happened after".
  Scene {num_scenes}: CTA - "Comment WHAT ELSE if you want part 2. Follow for more dark history."
- Dramatic, conversational and addictive language. Use CAPS for emphasis.
- FORBIDDEN: emojis, special Unicode characters (em-dashes, curly quotes, special ellipsis).
- USE ONLY: letters, numbers, commas, periods, exclamation marks, question marks, plain apostrophes.
- Never say "today I'm going to tell you" or "we're going to talk about".

Topic: {topic}
Category: {category}{f'{chr(10)}PRE-SELECTED HOOK (MANDATORY — use this EXACT text in Scene 1): "{chosen_hook}"' if chosen_hook else ""}

OUTPUT FORMAT: Strict JSON, no markdown, no text outside the JSON:
[
  {{"id":1,"text":"scene text here","visual_1":"pexels search term","visual_2":"pexels search term","mood":"dramatic"}},
  {{"id":2,"text":"scene text here","visual_1":"pexels search term","visual_2":"pexels search term","mood":"dramatic"}}
]

JSON RULES:
- EXACTLY {num_scenes} entries — no more, no fewer.
- "text": narrated text for that scene. No emojis. No special characters.
- "visual_1" and "visual_2": English Pexels search terms (2-4 words) matching the content.
- "mood": always "dramatic"."""

        raw = self._generate(prompt)
        return self._parse_scenes(raw, num_scenes, label="viral", default_mood="dramatic")

    def generate_testimonio_script(self, topic: str, category: str, lang: str = "es", chosen_hook: str = "", num_scenes: int = 9, max_words_per_scene: int = 999) -> list:
        """Guion estilo testimonio misterioso — narración lenta, cinematográfica, terror.
        Single-call: produce JSON scenes directly — no second AI call, no text modification."""
        import re as _re
        import random as _random
        print(f"👁️ Generando testimonio: {topic}...")

        ATMOSPHERIC_FALLBACKS = [
            "dark forest night fog", "candle ritual dark room",
            "haunted abandoned church", "mysterious silhouette shadow",
            "foggy cemetery night", "stormy dark night lightning",
            "eerie fog forest", "candlelit room dark",
        ]

        if lang == "es":
            prompt = f"""Eres un experto en crear historias de terror y misterio en formato YouTube/TikTok Shorts, estilo Archimosfera.

Debes contar la historia como si fuera un testimonio real de una persona (ex satanica, testigo, sacerdote, victima, etc.).

Estructura exacta (~{num_scenes * 5} segundos / EXACTAMENTE {num_scenes} escenas / MAXIMO {max_words_per_scene} palabras por escena):
  Escena 1 - HOOK PERTURBADOR (maximo 12 palabras, el espectador decide en 1.7 seg):
    OBLIGATORIO — uno de estos tipos:
    TIPO A: "[CIFRA] personas/casos [hecho perturbador]." Ej: "17 miembros de una secta murieron la misma noche. Nadie explica como."
    TIPO B: "Lo que [testigo/ex-miembro] revelo sobre [ELEMENTO ESPECIFICO] cambio todo."
    TIPO C: "Nadie habla de lo que paso realmente en [LUGAR/EVENTO ESPECIFICO DEL TEMA]."
    TIPO D: "¿Que harias si descubrieras que [HECHO PERTURBADOR CONCRETO]?"
  Escenas 2-{max(3, num_scenes - 3)} - TESTIGO + DESARROLLO: Presentacion del testimoniante y detalles escalofriantes.
  Escena {num_scenes - 1} - CLIMAX: La parte mas fuerte y perturbadora.
  Escena {num_scenes} - CIERRE: Consecuencia + CTA ("Vos crees en esto? Comenta SI o NO").

Reglas de estilo:
- Lenguaje conversacional, misterioso y dramatico.
- Frases como: "me conto que...", "revelo que...", "nadie se atreve a decir...", "lo mas aterrador fue...".
- PROHIBIDO: emojis, caracteres especiales Unicode (guiones largos, comillas rizadas, puntos suspensivos especiales), la letra ñ (usa alternativas: "anio" por "año", "senor" por "señor").
- USA SOLO: letras, numeros, comas, puntos, signos de exclamacion, signos de interrogacion y apostrofes simples.
- En espanol neutro latino.

Tema: {topic}
Categoria: {category}{f'{chr(10)}HOOK PRE-SELECCIONADO (OBLIGATORIO usar este texto EXACTO en Escena 1): "{chosen_hook}"' if chosen_hook else ""}

FORMATO DE SALIDA: JSON estricto, sin markdown, sin texto fuera del JSON:
[
  {{"id":1,"text":"texto de la escena","visual_1":"dark forest night","visual_2":"candle ritual","visual_3":"mysterious shadow","mood":"horror"}},
  {{"id":2,"text":"texto de la escena","visual_1":"foggy cemetery","visual_2":"abandoned church","visual_3":"eerie fog","mood":"horror"}}
]

REGLAS DEL JSON:
- EXACTAMENTE {num_scenes} entradas — no mas, no menos.
- "text": el texto narrado de esa escena. Sin emojis. Sin caracteres especiales.
- "visual_1", "visual_2", "visual_3": terminos en INGLES para Pexels (2-4 palabras). Deben ser oscuros, atmosfericos: dark forest, candles, fog, shadow, cemetery, abandoned, storm, etc.
- "mood": siempre "horror"."""
        else:
            prompt = f"""You are an expert at creating horror and mystery stories in YouTube/TikTok Shorts format, Archimosfera style.

Tell the story as if it were a real testimony from a real person (ex-satanist, witness, priest, victim, etc.).

Exact structure (~{num_scenes * 5} seconds / EXACTLY {num_scenes} scenes / MAX {max_words_per_scene} words per scene):
  Scene 1 - DISTURBING HOOK (max 12 words, viewer decides in 1.7 sec):
    MANDATORY — one of these types:
    TYPE A: "[NUMBER] people/cases [disturbing fact]." E.g.: "17 cult members died the same night. Nobody explains how."
    TYPE B: "What [witness/ex-member/priest] revealed about [SPECIFIC ELEMENT] changed everything."
    TYPE C: "Nobody is talking about what really happened at [SPECIFIC PLACE/EVENT]."
    TYPE D: "What would you do if you found out that [DISTURBING CONCRETE FACT]?"
  Scenes 2-{max(3, num_scenes - 3)} - WITNESS + DEVELOPMENT: Introduce testimony person and chilling details gradually.
  Scene {num_scenes - 1} - CLIMAX: The strongest and most disturbing part.
  Scene {num_scenes} - CLOSING: Consequence + CTA ("Do you believe this? Comment YES or NO").

Style rules:
- LANGUAGE: ENGLISH ONLY. No Spanish words.
- Conversational, mysterious and dramatic language.
- Use phrases like: "she told me that...", "revealed that...", "nobody dares to say...", "the scariest part was...".
- FORBIDDEN: emojis, special Unicode characters (em-dashes, curly quotes, special ellipsis).
- USE ONLY: letters, numbers, commas, periods, exclamation marks, question marks, plain apostrophes.

Topic: {topic}
Category: {category}

OUTPUT FORMAT: Strict JSON, no markdown, no text outside the JSON:
[
  {{"id":1,"text":"scene text here","visual_1":"dark forest night","visual_2":"candle ritual","visual_3":"mysterious shadow","mood":"horror"}},
  {{"id":2,"text":"scene text here","visual_1":"foggy cemetery","visual_2":"abandoned church","visual_3":"eerie fog","mood":"horror"}}
]

JSON RULES:
- EXACTLY {num_scenes} entries — no more, no fewer.
- "text": narrated text for that scene. No emojis. No special characters.
- "visual_1", "visual_2", "visual_3": English Pexels search terms (2-4 words). Must be dark and atmospheric: dark forest, candles, fog, shadow, cemetery, abandoned, storm, etc.
- "mood": always "horror"."""

        raw   = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()

        try:
            scenes = json.loads(clean)
            for i, s in enumerate(scenes):
                s['id']   = i + 1
                s['text'] = self._sanitize(s.get('text', ''))
                s.setdefault('mood', 'horror')
                if not s.get('visual_3'):
                    s['visual_3'] = _random.choice(ATMOSPHERIC_FALLBACKS)
            if len(scenes) > num_scenes:
                print(f"⚠️ AI returned {len(scenes)} testimonio scenes, trimming to {num_scenes}.")
                scenes = scenes[:num_scenes]
            elif len(scenes) < num_scenes:
                print(f"⚠️ AI returned only {len(scenes)} testimonio scenes (requested {num_scenes}).")
            print(f"✅ {len(scenes)} testimonio scenes ready")
            return scenes
        except Exception:
            sentences = [s.strip() for s in _re.split(r'(?<=[.!?])\s+', clean) if len(s.strip()) > 8][:num_scenes]
            return [
                {
                    "id": i+1, "text": self._sanitize(s),
                    "visual_1": _random.choice(ATMOSPHERIC_FALLBACKS),
                    "visual_2": _random.choice(ATMOSPHERIC_FALLBACKS),
                    "visual_3": _random.choice(ATMOSPHERIC_FALLBACKS),
                    "mood": "horror"
                }
                for i, s in enumerate(sentences)
            ]

    def generate_misterio_biblico_script(self, topic: str, category: str, lang: str = "es", chosen_hook: str = "", num_scenes: int = 9, max_words_per_scene: int = 999) -> list:
        """Guion de misterio biblico — secretos oscuros y poco conocidos de la Biblia, estilo documental cinematografico.
        Single-call: produce JSON scenes directly — no second AI call, no text modification."""
        import re as _re
        import random as _random
        print(f"📖 Generando misterio biblico: {topic}...")

        BIBLICAL_FALLBACKS = [
            "ancient stone tablets scrolls", "dark cathedral candles ancient",
            "mysterious light temple ruins", "old manuscript parchment dark",
            "desert ancient ruins night", "stormy sky lightning cross",
            "ancient bible open dark", "mysterious fog ancient city",
        ]

        if lang == "es":
            prompt = f"""Eres un narrador experto en revelar los secretos, misterios y hechos oscuros que esconde la Biblia, estilo documental cinematografico y canal de YouTube viral.

Tu objetivo: exponer este misterio biblico de forma que el espectador sienta que acaba de descubrir algo que nunca le ensenaron.

Estructura exacta (~{num_scenes * 5} segundos / EXACTAMENTE {num_scenes} escenas / MAXIMO {max_words_per_scene} palabras por escena):
  Escena 1 - HOOK OSCURO (maximo 12 palabras, el espectador decide en 1.7 seg):
    OBLIGATORIO — uno de estos tipos:
    TIPO A: "La Biblia oculto esto durante miles de anos. Muy pocos lo saben."
    TIPO B: "Lo que nadie te conto sobre [ELEMENTO ESPECIFICO DEL TEMA]."
    TIPO C: "Nadie habla del pasaje mas perturbador de toda la Biblia."
    TIPO D: "¿Que harias si descubrieras que [HECHO BIBLICO OSCURO Y CONCRETO]?"
  Escenas 2-{max(3, num_scenes - 3)} - REVELACION BIBLICA: El misterio, su contexto en las Escrituras y los detalles que la mayoria desconoce.
  Escena {num_scenes - 1} - REVELACION FINAL: El hecho mas impactante y perturbador del tema.
  Escena {num_scenes} - CIERRE + CTA: Una reflexion que impacte + "¿Lo sabias? Comenta SI o NO y sigueme para mas misterios biblicos".

Reglas de estilo:
- Lenguaje misterioso, dramatico y revelador.
- Frases como: "la Biblia revela que...", "este versiculo dice literalmente...", "los historiadores descubrieron que...", "lo que pocos saben es que...".
- Tono: oscuro y fascinante, como si estuvieras desvelando un secreto milenario.
- PROHIBIDO: emojis, caracteres especiales Unicode (guiones largos, comillas rizadas, puntos suspensivos especiales), la letra n con tilde (usa alternativas: "anio" por "ano", "senor" por "senor").
- USA SOLO: letras, numeros, comas, puntos, signos de exclamacion, signos de interrogacion y apostrofes simples.
- En espanol neutro latino.

Tema: {topic}
Categoria: {category}{f'{chr(10)}HOOK PRE-SELECCIONADO (OBLIGATORIO usar este texto EXACTO en Escena 1): "{chosen_hook}"' if chosen_hook else ""}

FORMATO DE SALIDA: JSON estricto, sin markdown, sin texto fuera del JSON:
[
  {{"id":1,"text":"texto de la escena","visual_1":"ancient scrolls dark","visual_2":"mysterious temple ruins","visual_3":"stormy sky lightning","mood":"mysterious"}},
  {{"id":2,"text":"texto de la escena","visual_1":"old bible candlelight","visual_2":"desert ruins ancient","visual_3":"dark cathedral light","mood":"mysterious"}}
]

REGLAS DEL JSON:
- EXACTAMENTE {num_scenes} entradas — no mas, no menos.
- "text": el texto narrado de esa escena. Sin emojis. Sin caracteres especiales.
- "visual_1", "visual_2", "visual_3": terminos en INGLES para Pexels (2-4 palabras). Deben ser oscuros y biblicos: ancient scrolls, stone tablets, temple ruins, desert night, dark cathedral, mysterious light, old parchment, religious symbols, stormy sky.
- "mood": siempre "mysterious"."""
        else:
            prompt = f"""You are a narrator expert at revealing the secrets, mysteries, and dark facts hidden in the Bible, cinematic documentary style and viral YouTube channel.

Your goal: expose this biblical mystery so the viewer feels they just discovered something they were never taught.

Exact structure (~{num_scenes * 5} seconds / EXACTLY {num_scenes} scenes / MAX {max_words_per_scene} words per scene):
  Scene 1 - DARK HOOK (max 12 words, viewer decides in 1.7 sec):
    MANDATORY — one of these types:
    TYPE A: "The Bible hid this for thousands of years. Very few know."
    TYPE B: "What nobody told you about [SPECIFIC ELEMENT OF THE TOPIC]."
    TYPE C: "Nobody talks about the most disturbing passage in the entire Bible."
    TYPE D: "What would you do if you discovered that [DARK BIBLICAL CONCRETE FACT]?"
  Scenes 2-{max(3, num_scenes - 3)} - BIBLICAL REVELATION: The mystery, its context in Scripture, and the details most people don't know.
  Scene {num_scenes - 1} - FINAL REVELATION: The most impactful and disturbing fact of the topic.
  Scene {num_scenes} - CLOSE + CTA: An impactful reflection + "Did you know this? Comment YES or NO and follow for more biblical mysteries".

Style rules:
- Mysterious, dramatic and revealing language.
- LANGUAGE: ENGLISH ONLY.
- Phrases like: "the Bible reveals that...", "this verse literally says...", "historians discovered that...", "what few people know is...".
- Tone: dark and fascinating, as if unveiling a millennial secret.
- FORBIDDEN: emojis, special Unicode characters (em-dashes, curly quotes, special ellipsis).
- USE ONLY: letters, numbers, commas, periods, exclamation marks, question marks, plain apostrophes.

Topic: {topic}
Category: {category}

OUTPUT FORMAT: Strict JSON, no markdown, no text outside the JSON:
[
  {{"id":1,"text":"scene text here","visual_1":"ancient scrolls dark","visual_2":"mysterious temple ruins","visual_3":"stormy sky lightning","mood":"mysterious"}},
  {{"id":2,"text":"scene text here","visual_1":"old bible candlelight","visual_2":"desert ruins ancient","visual_3":"dark cathedral light","mood":"mysterious"}}
]

JSON RULES:
- EXACTLY {num_scenes} entries — no more, no fewer.
- "text": narrated text for that scene. No emojis. No special characters.
- "visual_1", "visual_2", "visual_3": English Pexels search terms (2-4 words). Must be dark and biblical: ancient scrolls, stone tablets, temple ruins, desert night, dark cathedral, mysterious light, old parchment, religious symbols, stormy sky.
- "mood": always "mysterious"."""

        raw   = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()

        try:
            scenes = json.loads(clean)
            for i, s in enumerate(scenes):
                s['id']   = i + 1
                s['text'] = self._sanitize(s.get('text', ''))
                s.setdefault('mood', 'mysterious')
                if not s.get('visual_3'):
                    s['visual_3'] = _random.choice(BIBLICAL_FALLBACKS)
            if len(scenes) > num_scenes:
                print(f"⚠️ AI returned {len(scenes)} misterio_biblico scenes, trimming to {num_scenes}.")
                scenes = scenes[:num_scenes]
            elif len(scenes) < num_scenes:
                print(f"⚠️ AI returned only {len(scenes)} misterio_biblico scenes (requested {num_scenes}).")
            print(f"✅ {len(scenes)} misterio biblico scenes ready")
            return scenes
        except Exception:
            sentences = [s.strip() for s in _re.split(r'(?<=[.!?])\s+', clean) if len(s.strip()) > 8][:num_scenes]
            return [
                {
                    "id": i+1, "text": self._sanitize(s),
                    "visual_1": _random.choice(BIBLICAL_FALLBACKS),
                    "visual_2": _random.choice(BIBLICAL_FALLBACKS),
                    "visual_3": _random.choice(BIBLICAL_FALLBACKS),
                    "mood": "mysterious"
                }
                for i, s in enumerate(sentences)
            ]

    def generate_book_summary_script(self, book: str, category: str, lang: str = "es", chosen_hook: str = "", num_scenes: int = 9, max_words_per_scene: int = 999) -> list:
        """Resumen de libro de 60 seg — enseña, aplica y motiva a leer.
        Single-call: produce JSON scenes directly — no second AI call, no text modification."""
        import re as _re
        label = "Generando resumen del libro" if lang == "es" else "Generating book summary"
        print(f"📚 {label}: {book}...")

        if lang == "es":
            prompt = f"""Eres un narrador conversacional que habla directamente al oido del espectador. Tu voz sera leida por un sistema de texto a voz, por eso CADA FRASE debe sonar natural al ser pronunciada en voz alta.

Estructura (EXACTAMENTE {num_scenes} escenas / {num_scenes * 15}-{num_scenes * 18} palabras en total / MAXIMO {max_words_per_scene} palabras por escena):
  Escena 1 - GANCHO: Una verdad incomoda o dato sorprendente que el libro revela. Directo, sin rodeos.
  Escena 2 - EL LIBRO: Presenta el titulo y autor de forma natural, como si lo recomendaras a un amigo.
  Escenas 3-{max(4, num_scenes - 3)} - IDEAS + GIRO: La premisa principal y la idea mas inesperada del libro.
  Escena {num_scenes - 1} - EN TU VIDA: Como aplicar esto manana mismo, con un ejemplo concreto.
  Escena {num_scenes} - CIERRE + CTA: Una frase que quede resonando y llamada a la accion.

REGLAS CRITICAS PARA SONAR HUMANO:
- Cada escena: maximo 15 palabras. Frases cortas. Una idea por escena.
- Usa comas donde harias una pausa al hablar.
- Usa "..." solo para pausas dramaticas intencionales (maximo 2 veces en todo el guion).
- Habla en 2da persona: "tu", "te", "tu vida".
- Tono: como si le hablaras a un amigo inteligente, no como un libro de texto.
- Varía el ritmo: alterna frases muy cortas con frases medianas.
- PROHIBIDO: emojis, palabras rebuscadas, frases subordinadas largas, lenguaje de vendedor, la letra ñ.
- PROHIBIDO: caracteres especiales Unicode. Solo letras, numeros, comas, puntos, signos de exclamacion, signos de interrogacion.

Libro: {book}
Categoria: {category}{f'{chr(10)}HOOK PRE-SELECCIONADO (OBLIGATORIO usar este texto EXACTO en Escena 1): "{chosen_hook}"' if chosen_hook else ""}

FORMATO DE SALIDA: JSON estricto, sin markdown, sin texto fuera del JSON:
[
  {{"id":1,"text":"texto corto y natural aqui","visual_1":"person reading book","visual_2":"open notebook writing","mood":"inspiring"}},
  {{"id":2,"text":"texto corto y natural aqui","visual_1":"city skyline sunrise","visual_2":"person thinking window","mood":"inspiring"}}
]

REGLAS DEL JSON:
- "text": el texto narrado. Maximo 15 palabras por escena. Sin caracteres especiales.
- "visual_1" y "visual_2": terminos en INGLES para Pexels (2-4 palabras). Inspiradores: personas leyendo, escribiendo, pensando, naturaleza, ciudad, exito. EVITAR visuals oscuros.
- "mood": siempre "inspiring"."""
        else:
            prompt = f"""You are a conversational narrator speaking directly into the viewer's ear. Your voice will be read by a text-to-speech system, so EVERY SENTENCE must sound natural when spoken out loud.

Structure (EXACTLY {num_scenes} scenes / {num_scenes * 15}-{num_scenes * 18} words total / MAX {max_words_per_scene} words per scene):
  Scene 1 - HOOK: An uncomfortable truth or surprising fact the book reveals. Direct, no fluff.
  Scene 2 - THE BOOK: Introduce the title and author naturally, like recommending it to a friend.
  Scenes 3-{max(4, num_scenes - 3)} - CORE IDEAS + TWIST: Main premise and most unexpected idea of the book.
  Scene {num_scenes - 1} - IN YOUR LIFE: How to apply this tomorrow, with a concrete example.
  Scene {num_scenes} - CLOSE + CTA: A line that keeps echoing and a simple call to action.

CRITICAL RULES FOR SOUNDING HUMAN:
- Each scene: maximum 15 words. Short sentences. One idea per scene.
- Use commas where you would pause when speaking.
- Use "..." only for intentional dramatic pauses (maximum 2 times in the whole script).
- Speak in 2nd person: "you", "your", "your life".
- Tone: like talking to a smart friend, not writing a textbook.
- Vary the rhythm: alternate very short sentences with medium ones.
- FORBIDDEN: emojis, complex vocabulary, long subordinate clauses, salesy language.
- FORBIDDEN: special Unicode characters. Only letters, numbers, commas, periods, exclamation marks, question marks.
- LANGUAGE: ENGLISH ONLY. No Spanish words.

Book: {book}
Category: {category}

OUTPUT FORMAT: Strict JSON, no markdown, no text outside the JSON:
[
  {{"id":1,"text":"short natural text here","visual_1":"person reading book","visual_2":"open notebook writing","mood":"inspiring"}},
  {{"id":2,"text":"short natural text here","visual_1":"city skyline sunrise","visual_2":"person thinking window","mood":"inspiring"}}
]

JSON RULES:
- "text": narrated text. Maximum 15 words per scene. No special characters.
- "visual_1" and "visual_2": English Pexels search terms (2-4 words). Inspiring: people reading, writing, thinking, nature, city, success. AVOID dark visuals.
- "mood": always "inspiring"."""

        raw = self._generate(prompt)
        return self._parse_scenes(raw, num_scenes, label="book", default_mood="inspiring",
                                  fallback_visual_1="person reading book",
                                  fallback_visual_2="open notebook inspiring",
                                  success_label="book summary")

    def generate_bible_script(self, verse: str, category: str, lang: str = "es", chosen_hook: str = "", num_scenes: int = 9, max_words_per_scene: int = 999) -> list:
        """Reflexión bíblica de 60 seg centrada en UN versículo como fuente de toda la narración."""
        import re as _re
        print(f"✝️ Generando reflexión bíblica: {verse}...")

        if lang == "es":
            prompt = f"""Eres un narrador espiritual que habla directamente al corazon del espectador. Tu voz sera leida por texto a voz, cada frase debe sonar natural al pronunciarse.

VERSÍCULO FUENTE: "{verse}"
Este versículo es el UNICO fundamento de todo el guion. Todo gira en torno a el.

Estructura (EXACTAMENTE {num_scenes} escenas / {num_scenes * 15}-{num_scenes * 18} palabras en total / MAXIMO {max_words_per_scene} palabras por escena):
  Escena 1 - GANCHO: Una pregunta o verdad poderosa que conecta con la vida del espectador. Directo al corazon.
  Escena 2 - EL VERSICULO: Cita el texto EXACTO del versiculo y su referencia biblica. Claro y solemne.
  Escenas 3-{max(4, num_scenes - 3)} - REFLEXION + GIRO: Que significa este versiculo, la idea mas profunda e inesperada que encierra.
  Escena {num_scenes - 1} - EN TU VIDA: Como aplicar este versiculo hoy mismo, con un ejemplo concreto y practico.
  Escena {num_scenes} - CIERRE + CTA: Una frase que quede resonando y llamada a la accion (guardar, compartir, reflexionar).

REGLAS CRITICAS:
- Cada escena: maximo 15 palabras. Frases cortas. Una idea por escena.
- Usa comas donde harias una pausa al hablar.
- Habla en 2da persona: "tu", "te", "tu vida".
- Tono: espiritual, esperanzador, como un pastor que le habla a un amigo.
- PROHIBIDO: emojis, palabras rebuscadas, lenguaje religioso forzado o fanático, la letra ñ.
- PROHIBIDO: caracteres especiales Unicode. Solo letras, numeros, comas, puntos, signos de exclamacion, signos de interrogacion.
- NO inventes versiculos. Usa solo el versiculo fuente indicado.
{f'HOOK PRE-SELECCIONADO (OBLIGATORIO usar este texto EXACTO en Escena 1): "{chosen_hook}"' if chosen_hook else ""}

Categoria: {category}

FORMATO DE SALIDA: JSON estricto, sin markdown, sin texto fuera del JSON:
[
  {{"id":1,"text":"texto corto y natural aqui","visual_1":"person praying sunrise","visual_2":"open bible candle light","mood":"inspiring"}},
  {{"id":2,"text":"texto corto y natural aqui","visual_1":"peaceful nature light","visual_2":"person meditating calm","mood":"inspiring"}}
]

REGLAS DEL JSON:
- "text": el texto narrado. Maximo 15 palabras. Sin caracteres especiales.
- "visual_1" y "visual_2": terminos en INGLES para Pexels (2-4 palabras). Espirituales y luminosos: persona orando, biblia abierta, naturaleza tranquila, luz solar, familia unida, esperanza. EVITAR visuals oscuros.
- "mood": siempre "inspiring"."""
        else:
            prompt = f"""You are a spiritual narrator speaking directly into the viewer's heart. Your voice will be read by text-to-speech, every sentence must sound natural when spoken.

SOURCE VERSE: "{verse}"
This verse is the ONLY foundation of the entire script. Everything revolves around it.

Structure (EXACTLY {num_scenes} scenes / {num_scenes * 15}-{num_scenes * 18} words total / MAX {max_words_per_scene} words per scene):
  Scene 1 - HOOK: A powerful question or truth that connects with the viewer's life. Straight to the heart.
  Scene 2 - THE VERSE: Quote the EXACT text of the verse and its biblical reference. Clear and solemn.
  Scenes 3-{max(4, num_scenes - 3)} - REFLECTION + TWIST: What this verse means, the deepest and most unexpected idea it holds.
  Scene {num_scenes - 1} - IN YOUR LIFE: How to apply this verse today, with a concrete practical example.
  Scene {num_scenes} - CLOSE + CTA: A line that keeps echoing and a call to action (save, share, reflect).

CRITICAL RULES:
- Each scene: maximum 15 words. Short sentences. One idea per scene.
- Use commas where you would pause when speaking.
- Speak in 2nd person: "you", "your", "your life".
- Tone: spiritual, hopeful, like a pastor talking to a friend.
- FORBIDDEN: emojis, complex vocabulary, forced or fanatical religious language.
- FORBIDDEN: special Unicode characters. Only letters, numbers, commas, periods, exclamation marks, question marks.
- Do NOT invent verses. Use only the source verse provided.
- LANGUAGE: ENGLISH ONLY.
{f'PRE-SELECTED HOOK (MANDATORY use this EXACT text in Scene 1): "{chosen_hook}"' if chosen_hook else ""}

Category: {category}

OUTPUT FORMAT: Strict JSON, no markdown, no text outside the JSON:
[
  {{"id":1,"text":"short natural text here","visual_1":"person praying sunrise","visual_2":"open bible candle light","mood":"inspiring"}},
  {{"id":2,"text":"short natural text here","visual_1":"peaceful nature light","visual_2":"person meditating calm","mood":"inspiring"}}
]

JSON RULES:
- "text": narrated text. Maximum 15 words. No special characters.
- "visual_1" and "visual_2": English Pexels search terms (2-4 words). Spiritual and luminous: person praying, open bible, peaceful nature, sunlight, united family, hope. AVOID dark visuals.
- "mood": always "inspiring"."""

        raw   = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()

        try:
            scenes = json.loads(clean)
            for i, s in enumerate(scenes):
                s['id']   = i + 1
                s['text'] = self._sanitize(s.get('text', ''))
                s.setdefault('mood', 'inspiring')
            if len(scenes) > num_scenes:
                scenes = scenes[:num_scenes]
            print(f"✅ {len(scenes)} bible scenes ready")
            return scenes
        except Exception:
            sentences = [s.strip() for s in _re.split(r'(?<=[.!?])\s+', clean) if len(s.strip()) > 8][:num_scenes]
            return [
                {"id": i+1, "text": self._sanitize(s), "visual_1": "person praying sunrise", "visual_2": "open bible light", "mood": "inspiring"}
                for i, s in enumerate(sentences)
            ]

    def generate_job_offer_script(self, offer_text: str, lang: str = "es") -> list:
        """Convierte una oferta de empleo en un guion de video promocional.
        Preserva TODA la información original — solo la presenta de forma atractiva."""
        import re as _re
        label = "Convirtiendo oferta de empleo en guion" if lang == "es" else "Converting job offer to script"
        print(f"💼 {label}...")

        if lang == "es":
            prompt = f"""Eres el director creativo de anuncios de empleo más energicos y virales de TikTok y YouTube Shorts.

OFERTA DE EMPLEO (texto original del cliente):
---
{offer_text}
---

TAREA: Crea exactamente 6 escenas — video de 30 SEGUNDOS EXACTOS — estilo anuncio de TV de alto impacto.

REGLAS ABSOLUTAS:
- PROHIBIDO inventar, exagerar o añadir información que NO esté en el texto original.
- Presenta la información de forma EXPLOSIVA y ENERGICA, pero 100% fiel al original.
- Si el salario está en la oferta, DEBES mencionarlo — es el gancho mas poderoso.
- Tono: directo, urgente, habla en 2da persona ("tu", "tu carrera", "si buscas").
- Cada escena: MAXIMO 10 PALABRAS. Frases cortas, poderosas, sin relleno.
- PROHIBIDO: emojis, caracteres especiales Unicode, palabras en ingles (excepto nombre de empresa), la letra ñ.
- TODO el mood debe ser "energetic" — rapido, dinamico, sin pausa.

ESTRUCTURA (6 escenas exactas — ~5 seg cada una):
  Escena 1 — GANCHO EXPLOSIVO: El beneficio mas impactante. Impresiona en 3 segundos.
  Escena 2 — EMPRESA + PUESTO: Quien contrata y que rol. Ultra corto.
  Escena 3 — REQUISITO CLAVE: El mas importante, presentado como "si tienes X, es para ti".
  Escena 4 — BENEFICIO ESTRELLA: Salario, modalidad, crecimiento — lo mas atractivo.
  Escena 5 — URGENCIA: Por que aplicar YA. Plazas limitadas, oportunidad unica, etc.
  Escena 6 — CTA DIRECTO: Aplica ya. Link en descripcion. Accion inmediata.

FORMATO DE SALIDA (JSON estricto, sin markdown, exactamente 6 elementos):
[
  {{"id":1,"text":"texto aqui maximo 10 palabras","visual_1":"energetic job interview success","visual_2":"modern office team celebrating","mood":"energetic"}},
  {{"id":2,"text":"texto aqui","visual_1":"company brand building","visual_2":"professional team working","mood":"energetic"}}
]

REGLAS DEL JSON:
- "text": MAXIMO 10 PALABRAS por escena. Frases de impacto. Sin puntos finales innecesarios.
- "visual_1" y "visual_2": terminos EN INGLES para Pexels (2-4 palabras). Dinamicos: success celebration, career growth, job interview, modern workspace, team achievement, business success.
- "mood": SIEMPRE "energetic" en todas las escenas."""
        else:
            prompt = f"""You are the creative director of the most energetic and viral job ad videos on TikTok and YouTube Shorts.

JOB OFFER (original client text):
---
{offer_text}
---

TASK: Create exactly 6 scenes — a 30-SECOND video — high-impact TV ad style.

ABSOLUTE RULES:
- FORBIDDEN to invent, exaggerate or add information NOT in the original text.
- Present information in an EXPLOSIVE, ENERGETIC way — 100% faithful to the original.
- If salary is in the offer, you MUST mention it — it's the most powerful hook.
- Tone: direct, urgent, speak in 2nd person ("you", "your career", "if you're looking").
- Each scene: MAXIMUM 10 WORDS. Short, powerful phrases. Zero filler.
- FORBIDDEN: emojis, special Unicode characters. ENGLISH ONLY.
- ALL moods must be "energetic" — fast, dynamic, no pauses.

STRUCTURE (exactly 6 scenes — ~5 sec each):
  Scene 1 — EXPLOSIVE HOOK: The most impactful benefit. Wow in 3 seconds.
  Scene 2 — COMPANY + ROLE: Who's hiring and what role. Ultra short.
  Scene 3 — KEY REQUIREMENT: The most important one, framed as "if you have X, this is for you".
  Scene 4 — STAR BENEFIT: Salary, work model, growth — the most attractive detail.
  Scene 5 — URGENCY: Why apply NOW. Limited spots, unique opportunity, etc.
  Scene 6 — DIRECT CTA: Apply now. Link in description. Immediate action.

OUTPUT FORMAT (strict JSON, no markdown, exactly 6 items):
[
  {{"id":1,"text":"max 10 words here","visual_1":"energetic job interview success","visual_2":"modern office team celebrating","mood":"energetic"}},
  {{"id":2,"text":"text here","visual_1":"company brand building","visual_2":"professional team working","mood":"energetic"}}
]

JSON RULES:
- "text": MAXIMUM 10 WORDS per scene. Impact phrases. No unnecessary punctuation.
- "visual_1" and "visual_2": English Pexels search terms (2-4 words). Dynamic: success celebration, career growth, job interview, modern workspace, team achievement, business success.
- "mood": ALWAYS "energetic" for ALL scenes."""

        raw   = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()

        try:
            scenes = json.loads(clean)
            for i, s in enumerate(scenes):
                s['id']   = i + 1
                s['text'] = self._sanitize(s.get('text', ''))
                s['mood'] = 'energetic'   # siempre energético para empleo
            print(f"✅ {len(scenes)} job offer scenes ready (~30s)")
            return scenes
        except Exception:
            sentences = [s.strip() for s in _re.split(r'(?<=[.!?])\s+', clean) if len(s.strip()) > 8][:6]
            return [
                {"id": i+1, "text": self._sanitize(s), "visual_1": "job interview success", "visual_2": "career growth celebration", "mood": "energetic"}
                for i, s in enumerate(sentences)
            ]

    def generate_freeform_script(self, raw_text: str, lang: str = "es",
                                 target_secs: float = 0,
                                 tono_key: str = None,
                                 objetivo_key: str = None) -> list:
        """Convierte texto libre en un guion de YouTube Shorts.

        Dos caminos:
        - Guion autorado (cabecera Titulo/Categoria/Visual o lista de vinietas):
          se respeta palabra por palabra, un beat = una escena. Solo se suaviza
          para que suene natural al narrarlo.
        - Texto suelto (noticia, chisme, reflexion): se adapta a formato viral
          como hasta ahora.
        """
        import re as _re
        parsed = parse_freeform_input(raw_text)
        _beats = parsed["beats"]
        # Guion ya escrito por el usuario: cabecera explicita, o >=3 vinietas.
        _authored = parsed["has_structure"] or len(_beats) >= 3

        if _authored:
            return self._generate_authored_script(parsed, lang=lang,
                                                  target_secs=target_secs,
                                                  tono_key=tono_key,
                                                  objetivo_key=objetivo_key)

        label = "Adaptando texto libre a guion viral" if lang == "es" else "Adapting freeform text to viral script"
        print(f"✍️ {label}...")

        if lang == "es":
            prompt = f"""Eres un experto creador de contenido viral para YouTube Shorts en español latino.

TEXTO DEL USUARIO:
---
{raw_text[:4000]}
---

TAREA:
1. Detecta el TONO del texto (noticia, chisme/entretenimiento, reflexion personal, dato curioso, opinion, humor, otro).
2. Adapta ese contenido para YouTube Shorts — dinamico, rapido, viral — SIN inventar informacion nueva.
3. Preserva todos los hechos, nombres y datos clave del texto original.
4. Adapta el estilo de narracion al tono detectado:
   - Noticia: voz de reportero, datos precisos, urgencia ("Segun reportes...", "Esto acaba de ocurrir...")
   - Chisme/entretenimiento: conversacional, emocionante, ganchos ("Y lo que nadie sabe es...", "Pero aqui lo interesante...")
   - Reflexion/opinion: cercana, emotiva, pausada ("Piensalo asi...", "Esto me hizo pensar...")
   - Dato curioso: asombro, impacto, revelacion ("Lo que pocos saben es...", "Resulta que...")
   - Humor: ligero, ganchos, ritmo rapido
5. Genera entre 7 y 10 escenas cortas y dinamicas.
6. La primera escena SIEMPRE debe ser el GANCHO mas poderoso del texto.
7. PROHIBIDO: emojis, caracteres Unicode especiales, inventar informacion, la letra ñ.
8. Maximo 20 palabras por escena.

FORMATO JSON (sin markdown):
[
  {{"id":1,"text":"texto narrado aqui","visual_1":"english pexels search","visual_2":"alternative english search","mood":"exciting|dramatic|calm|mysterious|informative|fun"}},
  ...
]

Reglas del JSON:
- "text": espanol latino neutro, maximo 20 palabras, sin simbolos especiales.
- "visual_1" y "visual_2": terminos de busqueda EN INGLES para Pexels (2-4 palabras).
- "mood": segun el tono de cada escena.

Responde SOLO el JSON, sin explicaciones."""
        else:
            prompt = f"""You are an expert viral content creator for YouTube Shorts.

USER TEXT:
---
{raw_text[:4000]}
---

TASK:
1. Detect the TONE of the text (news, gossip/entertainment, personal reflection, fun fact, opinion, humor, other).
2. Adapt the content for YouTube Shorts — dynamic, fast, viral — WITHOUT inventing new information.
3. Preserve all facts, names and key data from the original text.
4. Adapt narration style to the detected tone:
   - News: reporter voice, precise data, urgency ("According to reports...", "This just happened...")
   - Gossip/entertainment: conversational, exciting, hooks ("And what nobody knows is...", "But here's the interesting part...")
   - Reflection/opinion: close, emotional, paced ("Think about it this way...", "This made me realize...")
   - Fun fact: amazement, impact, revelation ("What few people know is...", "It turns out that...")
   - Humor: light, hooks, fast pace
5. Generate between 7 and 10 short dynamic scenes.
6. The first scene MUST always be the most powerful HOOK from the text.
7. FORBIDDEN: emojis, special Unicode characters, inventing information.
8. Maximum 20 words per scene.

JSON FORMAT (no markdown):
[
  {{"id":1,"text":"narrated text here","visual_1":"english pexels search","visual_2":"alternative english search","mood":"exciting|dramatic|calm|mysterious|informative|fun"}},
  ...
]

Rules:
- "text": English, maximum 20 words, no special characters.
- "visual_1" and "visual_2": English Pexels search terms (2-4 words).
- "mood": matching the tone of each scene.

Respond ONLY with the JSON, no explanations."""

        raw   = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()

        try:
            scenes = json.loads(clean)
            for i, s in enumerate(scenes):
                s['id']   = i + 1
                s['text'] = self._sanitize(s.get('text', ''))
                s.setdefault('mood', 'informative')
            print(f"✅ {len(scenes)} freeform scenes ready")
            return scenes
        except Exception:
            sentences = [s.strip() for s in _re.split(r'(?<=[.!?])\s+', clean) if len(s.strip()) > 8][:10]
            return [
                {"id": i+1, "text": self._sanitize(s), "visual_1": "people talking news", "visual_2": "interesting facts world", "mood": "informative"}
                for i, s in enumerate(sentences)
            ]

    def _repair_enie(self, scenes: list, lang: str = "es") -> list:
        """Segunda pasada: sustituye las palabras con ñ que se colaron.

        El prompt principal ya pide cero ñ, pero el modelo a veces recae en
        palabras muy naturales ("diseñar"). Aqui se le pide solo el reemplazo de
        esas palabras concretas, lo que es mucho mas fiable que reintentar el
        guion entero. Si la reparacion falla, se devuelven las escenas intactas:
        audio.py convertira la ñ en n como ultima red.
        """
        # PASO 1 — diccionario determinista. No depende de la API, asi que
        # resuelve la mayoria de los casos aunque el modelo falle.
        _cambiadas = []
        for s in scenes:
            antes = s.get("text", "")
            despues, _ = _sustituir_enie(antes)
            if despues != antes:
                s["text"] = despues
                _cambiadas.append(s.get("id", "?"))
        if _cambiadas:
            print(f"   🔤 Sinonimos aplicados por diccionario en escena(s): "
                  f"{', '.join(str(i) for i in _cambiadas)}")

        # PASO 2 — lo que el diccionario no cubre se consulta al modelo.
        palabras = sorted({w for s in scenes
                           for w in _re_mod.findall(r"[\w'\-]*[ñÑ][\w'\-]*", s.get("text", ""))})
        if not palabras:
            print("   ✅ Guion sin ninguna ñ (resuelto con el diccionario)")
            return scenes

        print(f"   🔤 Reparando {len(palabras)} palabra(s) con ñ: {', '.join(palabras)}")
        prompt = f"""Cada palabra de esta lista contiene la letra ñ y hay que sustituirla
porque el motor de voz la pronuncia mal.

PALABRAS: {', '.join(palabras)}

Para cada una, da un sinonimo en espanol latino que:
- NO contenga la letra ñ.
- Mantenga la MISMA forma gramatical (mismo tiempo verbal, mismo genero y numero).
- Encaje en un guion sobre psicologia del comportamiento.
- NO sea una deformacion ortografica de la original (nada de "disenia" o "anio").

Responde SOLO un objeto JSON {{"palabra_original": "sustituto"}}, sin markdown."""

        try:
            raw   = self._generate(prompt)
            clean = raw.replace('```json', '').replace('```', '').strip()
            mapa  = json.loads(clean)
            if not isinstance(mapa, dict):
                raise ValueError("no es un objeto")
        except Exception as e:
            print(f"   ⚠️ No se pudo reparar la ñ ({e}). audio.py la convertira en n.")
            return scenes

        for s in scenes:
            texto = s.get("text", "")
            for orig, nuevo in mapa.items():
                if isinstance(nuevo, str) and nuevo and "ñ" not in nuevo and "Ñ" not in nuevo:
                    texto = texto.replace(orig, nuevo)
            s["text"] = texto

        _quedan = [w for s in scenes
                   for w in _re_mod.findall(r"[\w'\-]*[ñÑ][\w'\-]*", s.get("text", ""))]
        if _quedan:
            print(f"   ⚠️ Aun quedan palabras con ñ: {', '.join(sorted(set(_quedan)))}")
        else:
            print("   ✅ Guion sin ninguna ñ")
        return scenes

    def _generate_authored_script(self, parsed: dict, lang: str = "es",
                                  persona_key: str = None,
                                  target_secs: float = 0,
                                  tono_key: str = None,
                                  objetivo_key: str = None) -> list:
        """Reescribe un guion del usuario con la voz de una persona narradora.

        El autor aporta el CONTENIDO (sus ideas y sus terminos); la persona aporta
        la VOZ (tono, ritmo, estructura). El modelo puede reescribir cada frase de
        cero y reordenar las ideas, pero no puede perder ninguna ni inventar datos.

        persona_key: clave en modules/personas.py. None usa DEFAULT_PERSONA.
        """
        beats     = parsed["beats"]
        titulo    = parsed["titulo"]
        categoria = parsed["categoria"]
        visual    = parsed["visual"]
        n_ideas   = len(beats)

        # ── Duracion objetivo ────────────────────────────────────────────────
        # Convencion del proyecto (ver pipeline.py): el TTS locuta ~2.3 pal/seg.
        # Con una duracion objetivo repartimos el guion en mas escenas que ideas
        # si hace falta, para que ninguna escena se alargue sobre un solo visual.
        _WPS = 2.3
        # Contenido corto vertical corta cada 3-5s para sentirse dinamico; 5.5s
        # y un tope de *2 dejaban escenas larguisimas (2 escenas para 60s)
        # cuando el autor escribe pocas ideas — ver parse_freeform_input, que
        # ahora al menos parte por oraciones si no hay vinietas.
        _SECS_POR_ESCENA_IDEAL = 4.5
        if target_secs and target_secs > 0:
            total_palabras = int(target_secs * _WPS)
            n = max(n_ideas, min(n_ideas * 3,
                                 max(1, round(target_secs / _SECS_POR_ESCENA_IDEAL))))
            wpsc = max(8, total_palabras // n)
            # Estructura de retencion (gancho -> contexto -> mecanismo ->
            # reencuadre -> cierre), como % del guion. El mecanismo es el
            # bloque mas grande a proposito: es la parte que hace que la
            # gente se quede, no el consejo final.
            _w_gancho    = max(6,  int(total_palabras * 0.06))
            _w_contexto  = max(10, int(total_palabras * 0.15))
            _w_mecanismo = max(15, int(total_palabras * 0.38))
            _w_reencuadre= max(10, int(total_palabras * 0.21))
            _w_cierre    = max(8,  int(total_palabras * 0.20))
            _dur_block = f"""
### DURACION OBJETIVO — {target_secs:.0f} SEGUNDOS (obligatorio):
- El guion completo debe rondar las {total_palabras} palabras. Es el dato que
  determina la duracion final del video, asi que acercate a esa cifra.
- Repartelas en {n} escenas de unas {wpsc} palabras cada una.
- Tienes {n_ideas} ideas del autor para {n} escenas: DIVIDE las ideas en varias
  escenas y desarrolla mejor cada mecanismo (el porque detras del comportamiento,
  como se siente, que pasa si no se cambia).
- Desarrollar NO es rellenar: prohibido repetir lo mismo con otras palabras,
  prohibido anadir frases de adorno. Si no tienes con que llenar {total_palabras}
  palabras de contenido real, entrega menos y mejor.

### ARCO OBLIGATORIO (en este orden, aunque el autor haya escrito las ideas en
### otro orden — REORDENA para que encajen aqui):
1. GANCHO (~{_w_gancho} palabras): identificacion inmediata o dato que golpea.
   La primera frase del video. Nada de contexto todavia.
2. CONTEXTO (~{_w_contexto} palabras): explica que esta pasando de forma simple,
   sin todavia explicar el mecanismo.
3. MECANISMO (~{_w_mecanismo} palabras): la parte mas valiosa. Como funciona
   REALMENTE el cerebro o el habito detras de lo que describio el autor. Aqui
   va la mayoria de las ideas del autor desarrolladas a fondo.
4. REENCUADRE (~{_w_reencuadre} palabras): cambia como el espectador ve el
   problema — de "me falta disciplina/voluntad" a "asi funciona mi sistema".
   Tiene que haber un giro de perspectiva explicito, no solo un resumen.
5. CIERRE + CTA (~{_w_cierre} palabras): instruccion concreta de que hacer
   ahora (ver bloque de cierre mas abajo).
"""
        else:
            n    = n_ideas
            wpsc = 22
            _dur_block = ""

        # La persona solo aplica si su idioma coincide con el del guion.
        _pkey    = DEFAULT_PERSONA if persona_key is None else persona_key
        _persona = get_persona(_pkey)
        if _persona and _persona.get("lang") != lang:
            _persona = None

        # El tono decide a que apunta el guion y si mantiene el registro calmado
        # de la persona o lo sustituye por el suyo.
        _tono = get_tono(tono_key or DEFAULT_TONO)
        _persona_block = build_voice_block(_persona, _tono)

        # El objetivo dice PARA QUE sirve el video en el embudo. Se anade
        # despues de la voz y del tono, y su bloque va DESPUES del CTA de la
        # persona a proposito: en conversion sus instrucciones de cierre deben
        # poder mandar sobre el "nunca suenes a vendedora" generico, que existe
        # para que no invente productos, no para prohibir el CTA del autor.
        _objetivo = get_objetivo(objetivo_key or DEFAULT_OBJETIVO)
        _obj_block = _objetivo["spec"]

        _cta_block = (_persona.get("cta", "") if _persona else
                      "### CIERRE:\n"
                      "- Si el autor trae un cierre o llamada a la accion, respetalo.\n"
                      "- Si no, no inventes productos ni enlaces.\n")

        print(f"✍️ Guion autorado: {n_ideas} ideas → {n} escenas"
              + (f" · ~{target_secs:.0f}s" if target_secs else "")
              + (f" · voz: {_persona['label']}" if _persona else " · voz neutra")
              + f" · tono: {_tono['label']}"
              + (" (rompe registro)" if _tono.get("rompe_voz") else "")
              + f" · objetivo: {_objetivo['label']}"
              + (f" · {titulo}" if titulo else ""))

        # Aviso si la duracion pedida se aleja de lo recomendado para el objetivo:
        # un video de captacion de 90s o uno de confianza de 15s desaprovechan
        # su funcion en el embudo. Es un aviso, no se corrige nada.
        if target_secs:
            _smin, _smax = _objetivo["secs_min"], _objetivo["secs_max"]
            if not (_smin <= target_secs <= _smax):
                print(f"   ⚠️ {target_secs:.0f}s para un video de "
                      f"{_objetivo['label']}: lo recomendado son {_smin}-{_smax}s")

        beats_block = "\n".join(f"{i}. {b}" for i, b in enumerate(beats, 1))
        _ctx_es, _ctx_en = "", ""
        if titulo:
            _ctx_es += f"TITULO: {titulo}\n"
            _ctx_en += f"TITLE: {titulo}\n"
        if categoria:
            _ctx_es += f"CATEGORIA / NICHO: {categoria}\n"
            _ctx_en += f"CATEGORY / NICHE: {categoria}\n"
        if visual:
            _ctx_es += f"DIRECCION VISUAL DEL AUTOR: {visual}\n"
            _ctx_en += f"AUTHOR VISUAL DIRECTION: {visual}\n"

        _visual_rule_es = (
            f"- La DIRECCION VISUAL DEL AUTOR manda: derivala en terminos de Pexels y repartela\n"
            f"  a lo largo de las escenas siguiendo su progresion (si describe un antes y un despues,\n"
            f"  las primeras escenas muestran el 'antes' y las ultimas el 'despues')."
            if visual else
            "- Elige visuales literales y cotidianos que el espectador reconozca al instante."
        ) + """
- PROHIBIDO en la escena 1 (el gancho debe tener movimiento o contraste fuerte
  desde el primer frame): persona en cama, luz de ventana, manos quietas con
  el telefono, meditacion. Son los planos mas usados del nicho y no detienen
  el scroll.
- Para conceptos abstractos (piloto automatico, costo mental, decision
  consciente, habito) usa una metafora visual concreta en vez de un plano
  literal de "persona pensando": caminos/carreteras, interruptores o
  engranajes, baterias o energia, una accion repetida, o el contraste entre
  caos y orden.
- Evita stock demasiado bonito, aspiracional o sin tension (gente sonriendo
  en camara lenta, oficinas perfectas): no comunica el mecanismo que se esta
  explicando."""
        _visual_rule_en = (
            f"- The AUTHOR VISUAL DIRECTION rules: translate it into Pexels terms and spread it\n"
            f"  across the scenes following its progression (if it describes a before and an after,\n"
            f"  early scenes show the 'before' and final scenes the 'after')."
            if visual else
            "- Choose literal, everyday visuals the viewer recognizes instantly."
        ) + """
- FORBIDDEN in scene 1 (the hook needs motion or strong contrast from frame
  one): person in bed, window light, still hands holding a phone, meditation.
  These are the niche's most overused shots and do not stop the scroll.
- For abstract concepts (autopilot, mental cost, conscious decision, habit)
  use a concrete visual metaphor instead of a literal "person thinking"
  shot: roads/paths, switches or gears, batteries or energy, a repeated
  action, or a chaos-vs-order contrast.
- Avoid overly pretty, aspirational, tension-free stock (people smiling in
  slow motion, perfect offices): it does not communicate the mechanism being
  explained."""

        if lang == "es":
            prompt = f"""Vas a reescribir un guion para un Short vertical en espanol latino.
El autor ya definio QUE decir. Tu decides COMO se dice, adoptando la voz de abajo.

{_persona_block}
{_ctx_es}
IDEAS DEL AUTOR (cada linea es una idea que debe aparecer en el guion final):
{beats_block}

### TU TAREA:
Reescribe estas ideas como un guion hablado de {n} escenas con la voz descrita arriba.
Tienes libertad total de redaccion: cada frase puede quedar completamente distinta
a como la escribio el autor, si asi suena mas como esa voz.
{_dur_block}

### PUEDES:
- Reescribir cada frase de cero con tus propias palabras.
- REORDENAR las ideas para que el arco funcione (el gancho mas potente primero,
  aunque el autor lo hubiera puesto en medio).
- Anadir conectores y giros de sentido ("Por eso...", "Eso significa que...").
- Anadir UNA analogia cotidiana propia si aclara el mecanismo.
- Partir una idea larga en dos escenas o unir dos ideas cortas en una,
  siempre que al final aparezcan TODAS.

### NO PUEDES:
- Perder ninguna idea del autor. Las {n_ideas} lineas de arriba deben estar todas
  representadas en el guion final.
- Cambiar los terminos tecnicos que uso el autor: si escribio "arquitectura
  conductual", el guion dice "arquitectura conductual", no "organizar tu espacio".
- Inventar cifras, porcentajes, anios, estudios, universidades ni nombres de
  investigadores. Si necesitas respaldo y no lo tienes, dilo en cualitativo
  ("la evidencia apunta a que...") o no lo digas.
- Contradecir al autor ni suavizar su conclusion.
- Usar lenguaje motivacional generico: "tu puedes", "cree en ti", "se la mejor
  version de ti misma", "todo esta en tu mente". Suena a coach y baja la
  retencion. Explica el MECANISMO, no arengues.
- Dar solo un consejo sin explicar antes por que ocurre el comportamiento: el
  "que hacer" viene siempre despues del "por que pasa".

{_cta_block}
{_obj_block}
### FORMATO:
- Espanol latino neutro.
- CERO PALABRAS CON LA LETRA ñ. El motor de voz la pronuncia mal, asi que ninguna
  palabra del guion puede llevarla. Se resuelve eligiendo OTRA palabra:
    * "disenia / diseñar / diseñado"  ->  "organizar", "acomodar", "preparar",
                                          "montar", "ajustar", "crear"
    * "mañana"    ->  "el dia siguiente"       * "pequeño"  ->  "minimo", "breve"
    * "acompaña"  ->  "va contigo"             * "señal"    ->  "aviso", "indicio"
    * "año"       ->  "temporada", "doce meses"* "dueño"    ->  "propietario"
    * "enseña"    ->  "explica", "muestra"     * "extraño"  ->  "raro", "ajeno"
  NUNCA deformes la ortografia: "disenha", "disenia" y "anio" se leen tal como
  estan escritos y suenan aun peor. Si una frase te obliga a usar una ñ,
  REESCRIBE LA FRASE COMPLETA con otra construccion. Siempre hay una salida.
- Manten los acentos y los signos de apertura ¿ y ¡.
- PROHIBIDO: emojis, caracteres Unicode especiales, comillas dentro del texto.
- Maximo {wpsc} palabras por escena. Una sola idea por escena.
{_visual_rule_es}
- visual_1 y visual_2 en INGLES, 2-4 palabras, concretos y filmables.

FORMATO JSON (sin markdown, exactamente {n} entradas):
[
  {{"id":1,"text":"texto narrado","visual_1":"english pexels search","visual_2":"another english search","mood":"informative|calm|exciting|dramatic|mysterious|fun"}}
]

Responde SOLO el JSON."""
        else:
            prompt = f"""You are a script editor for YouTube Shorts.
The author ALREADY WROTE their script. Your job is NOT to rewrite it: it is to prepare it for voiceover.

{_ctx_en}
AUTHOR SCRIPT (each numbered line is one scene, in this exact order):
{beats_block}

### GOLDEN RULE — FIDELITY:
- Produce EXACTLY {n} scenes, one per numbered line, in the SAME order.
- Keep the author's message, technical terms and examples.
  If the author says "behavioral architecture", say "behavioral architecture" — do not simplify it.
- FORBIDDEN to add ideas, facts, figures, hooks or advice the author did not write.
- FORBIDDEN to drop the author's ideas or merge two lines into one scene.

### WHAT YOU MAY CHANGE (so it sounds natural read aloud):
- Reorder words within a sentence so it flows when spoken.
- Add brief spoken connectors between scenes so it does not sound like a list:
  "and this matters", "that is why", "so", "look", "the result".
- Turn written phrasing into spoken phrasing (natural contractions, rhythm).
- Trim filler if a line is long, WITHOUT losing any of the author's ideas.

### TONE:
- Second person, warm, like someone who knows the topic explaining it to you.
- Affirmative and calm. No advertising shout, no motivational-coach voice.
- No sensationalism: the content is already valuable, it does not need selling.

### FORMAT:
- FORBIDDEN: emojis, special Unicode characters, quotes inside the text.
- Maximum 22 words per scene.
{_visual_rule_en}
- visual_1 and visual_2 in ENGLISH, 2-4 words, concrete and filmable.

JSON FORMAT (no markdown, exactly {n} entries):
[
  {{"id":1,"text":"narrated text","visual_1":"english pexels search","visual_2":"another english search","mood":"informative|calm|exciting|dramatic|mysterious|fun"}}
]

Respond ONLY with the JSON."""

        raw   = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()

        try:
            scenes = json.loads(clean)
            if not isinstance(scenes, list):
                raise ValueError("la respuesta no es una lista")
        except Exception:
            scenes = []

        # Nos quedamos solo con escenas utilizables
        scenes = [s for s in scenes if isinstance(s, dict) and (s.get("text") or "").strip()]

        # Red de seguridad. Al permitir reordenacion ya NO se puede rellenar la
        # escena i con el beat i: eso mezclaria el orden nuevo con el viejo y
        # rompería la narrativa. Solo hay dos salidas honestas: usar lo que
        # devolvio el modelo, o caer al guion original completo.
        if len(scenes) < 3:
            print("⚠️ El modelo no devolvio un guion utilizable — se narran las "
                  "ideas del autor tal cual, sin re-voz.")
            scenes = [{"text": b} for b in beats]
        elif len(scenes) != n:
            print(f"ℹ️ El modelo entrego {len(scenes)} escenas, se pidieron {n} "
                  f"(el autor puso {n_ideas} ideas).")

        for i, s in enumerate(scenes):
            s['id']   = i + 1
            s['text'] = self._sanitize((s.get('text') or '').strip())
            s.setdefault('mood', 'informative')
            s.setdefault('visual_1', 'person thinking indoors')
            s.setdefault('visual_2', 'focused person close up')

        # Segunda pasada para eliminar cualquier ñ que se haya colado
        if lang == "es":
            scenes = self._repair_enie(scenes, lang=lang)

        # Verificar que ninguna idea del autor se quedo fuera de la re-voz
        _faltan = _ff_missing_key_terms(beats, scenes)
        if _faltan:
            print(f"⚠️ Terminos del autor ausentes del guion final: {', '.join(_faltan[:6])}"
                  + (" ..." if len(_faltan) > 6 else ""))
        else:
            print("✅ Todos los terminos clave del autor estan presentes")

        # Piso de duracion minima. El bloque de arriba permite explicitamente
        # "si no tienes con que llenar {total_palabras} palabras, entrega menos":
        # eso es correcto para no rellenar con paja, pero puede dejar el video
        # por debajo del minimo de negocio. En vez de rechazar el render, se le
        # pide al modelo 1-2 escenas MAS que profundicen (mecanismo o ejemplo)
        # sin tocar lo que ya escribio el autor.
        # El piso depende del OBJETIVO (personas.OBJETIVOS[*]["min_secs"]): un
        # video de Atencion de 20s es correcto y no debe estirarse a 38s; uno
        # de Confianza si. Nunca se estira por encima de lo que pidio el autor.
        _MIN_SECS = float(_objetivo.get("min_secs", 38))
        if target_secs and target_secs > 0:
            _MIN_SECS = min(_MIN_SECS, float(target_secs))
        if target_secs and target_secs > 0:
            _dur_actual = sum(len((s.get('text') or '').split()) for s in scenes) / _WPS
            if _dur_actual < _MIN_SECS:
                scenes = self._expand_short_script(scenes, lang=lang,
                                                   persona_block=_persona_block,
                                                   min_secs=_MIN_SECS, wps=_WPS)

        print(f"✅ {len(scenes)} escenas listas")
        return scenes

    def _expand_short_script(self, scenes: list, lang: str = "es",
                             persona_block: str = "", min_secs: float = 35,
                             wps: float = 2.3) -> list:
        """Anade 1-2 escenas cuando el guion autorado quedo mas corto que el
        minimo de duracion, sin tocar ninguna escena existente.

        Se insertan antes de la ULTIMA escena, no al final: por convencion de
        este pipeline la ultima escena suele ser el cierre/CTA (ver
        _generate_authored_script), y el desarrollo nuevo debe ir antes de esa
        conclusion, no despues.
        """
        _dur_actual = sum(len((s.get('text') or '').split()) for s in scenes) / wps
        _faltan_palabras = max(1, int((min_secs - _dur_actual) * wps))
        _resumen = "\n".join(f"{i}. {s.get('text', '')}" for i, s in enumerate(scenes, 1))

        label = "Guion corto, pidiendo 1-2 escenas mas" if lang == "es" else "Script too short, requesting 1-2 more scenes"
        print(f"⏱️ {label} (~{_dur_actual:.0f}s de {min_secs:.0f}s minimo)...")

        if lang == "es":
            prompt = f"""Este guion para un Short quedo mas corto de lo necesario.

{persona_block}
GUION ACTUAL (no lo toques, ya esta cerrado):
{_resumen}

TAREA:
Anade 1 o 2 escenas NUEVAS que vayan DESPUES de la ultima idea de desarrollo,
profundizando el mecanismo (el porque real de lo que ya se conto) o sumando un
ejemplo cotidiano concreto que lo ilustre. Necesitas sumar unas {_faltan_palabras}
palabras en total. Si el guion de arriba termina con un cierre o llamada a la
accion, tus escenas nuevas van ANTES de ese cierre, no despues.

NO PUEDES:
- Repetir lo que ya dice el guion con otras palabras.
- Inventar cifras, estudios ni nombres.
- Escribir el cierre de nuevo ni cambiar su idea.

FORMATO:
- Espanol latino neutro, cero letra ñ, maximo 22 palabras por escena.
- visual_1 y visual_2 en ingles, 2-4 palabras.

Responde SOLO un JSON con la(s) escena(s) nueva(s):
[{{"text":"...","visual_1":"...","visual_2":"...","mood":"informative|calm|exciting|dramatic|mysterious|fun"}}]"""
        else:
            prompt = f"""This Short script came out shorter than needed.

CURRENT SCRIPT (do not touch, it is already final):
{_resumen}

TASK:
Add 1 or 2 NEW scenes that go AFTER the last development idea, going deeper
into the mechanism (the real why behind what was already said) or adding a
concrete everyday example that illustrates it. Add about {_faltan_palabras}
words total. If the script above ends with a closing line or call to action,
your new scenes go BEFORE that closing, not after.

YOU MAY NOT:
- Repeat what the script already says in other words.
- Invent figures, studies or names.
- Rewrite the closing line or change its point.

FORMAT:
- Maximum 22 words per scene.
- visual_1 and visual_2 in English, 2-4 words.

Respond ONLY with a JSON array of the new scene(s):
[{{"text":"...","visual_1":"...","visual_2":"...","mood":"informative|calm|exciting|dramatic|mysterious|fun"}}]"""

        try:
            raw   = self._generate(prompt)
            clean = raw.replace('```json', '').replace('```', '').strip()
            nuevas = json.loads(clean)
            if not isinstance(nuevas, list) or not nuevas:
                raise ValueError("respuesta vacia o no es lista")
        except Exception as e:
            print(f"   ⚠️ No se pudo expandir el guion corto ({e}); se deja tal cual.")
            return scenes

        added = []
        for s in nuevas[:2]:
            if not isinstance(s, dict) or not (s.get('text') or '').strip():
                continue
            added.append({
                'text': self._sanitize(s.get('text', '').strip()),
                'visual_1': s.get('visual_1', 'person thinking indoors'),
                'visual_2': s.get('visual_2', 'focused person close up'),
                'mood': s.get('mood', 'informative'),
            })

        if not added:
            print("   ⚠️ El modelo no devolvio escenas nuevas utilizables; se deja el guion tal cual.")
            return scenes

        # Insertar antes del cierre (ultima escena) si hay al menos 2 escenas;
        # si el guion original es solo 1 escena no hay cierre que respetar.
        if len(scenes) >= 2:
            scenes = scenes[:-1] + added + scenes[-1:]
        else:
            scenes = scenes + added
        for i, s in enumerate(scenes):
            s['id'] = i + 1

        if lang == "es":
            scenes = self._repair_enie(scenes, lang=lang)

        _dur_nueva = sum(len((s.get('text') or '').split()) for s in scenes) / wps
        print(f"   ✅ Guion expandido: +{len(added)} escena(s), ~{_dur_nueva:.0f}s")
        return scenes

    def generate_script(self, topic: str, num_scenes: int = 9, lang: str = "es",
                        chosen_hook: str = "", mode: str = "auto") -> list:
        label = "Escribiendo guion" if lang == "es" else "Writing script"
        print(f"📝 {label}: {topic} ({num_scenes} scenes)...")

        # Modos educativos: el espectador debe salir sabiendo QUE hacer, no solo motivado.
        # Cambia el flujo narrativo y anade reglas de evidencia + accion concreta.
        if mode in EDUCATIONAL_MODES:
            flow_es = ("Gancho -> Contexto (a quien le pasa) -> Mecanismo (el porque real) -> "
                       "Evidencia (estudio, cifra o experimento concreto) -> "
                       "Aplicacion (paso accionable hoy) -> Cierre que reencuadra")
            flow_en = ("Hook -> Context (who this happens to) -> Mechanism (the real why) -> "
                       "Evidence (concrete study, stat or experiment) -> "
                       "Application (actionable step today) -> Reframing outro")
            extra_es = (
                "\n### 1b. REGLAS EDUCATIVAS (OBLIGATORIAS en este modo):\n"
                "- **Evidencia real:** al menos UNA escena debe citar algo verificable (estudio, universidad, cifra, anio o nombre del experimento). Si no estas seguro del dato exacto, describe el hallazgo sin inventar cifras ni atribuciones falsas.\n"
                "- **Paso accionable:** al menos UNA escena debe dar una accion concreta que el espectador pueda hacer hoy, en una frase, sin ambiguedad (no vale 'se disciplinado' ni 'cambia tu mentalidad').\n"
                "- **Mecanismo antes que consejo:** explica POR QUE ocurre antes de decir que hacer.\n"
                "- **Prohibido:** frases de superacion vacias, sermones, promesas irreales, lenguaje de coach.\n"
                "- **Carga cognitiva:** una sola idea por escena. Si una escena necesita dos frases largas, simplifica.\n"
            )
            extra_en = (
                "\n### 1b. EDUCATIONAL RULES (MANDATORY in this mode):\n"
                "- **Real evidence:** at least ONE scene must cite something verifiable (study, university, stat, year or experiment name). If unsure of the exact figure, describe the finding without inventing numbers or false attributions.\n"
                "- **Actionable step:** at least ONE scene must give a concrete action the viewer can take today, in one sentence, unambiguous (not 'be disciplined' or 'change your mindset').\n"
                "- **Mechanism before advice:** explain WHY it happens before saying what to do.\n"
                "- **Forbidden:** empty self-help lines, preaching, unrealistic promises, coach-speak.\n"
                "- **Cognitive load:** one single idea per scene. If a scene needs two long sentences, simplify.\n"
            )
        else:
            flow_es  = "Gancho -> Contexto -> Mecanismo -> Giro inesperado -> Cierre memorable"
            flow_en  = "Hook -> Context -> Mechanism -> Twist -> Memorable Outro"
            extra_es = ""
            extra_en = ""

        if lang == "es":
            prompt = f"""Eres el guionista principal de un canal viral de YouTube Shorts en español latino llamado "Mentes Curiosas".

Tema: {topic}

### OBJETIVO:
Crear un guion donde cada oración tenga un "Cambio Visual" para mantener la retención alta.
Necesitamos DOS videos de stock diferentes por cada escena.

### 1. REQUISITOS DEL GUION (La narración):
- **Idioma:** ESPAÑOL LATINO neutro. Sin regionalismos. Sin palabras en inglés. Evita palabras con la letra ñ — usa alternativas naturales (ej: "anio" por "año", "senor" por "señor", "Espana" por "España").
- **Emojis:** PROHIBIDO usar emojis. Solo texto puro narrado. PROHIBIDO usar la letra ñ — usa alternativas (ej: "anio" por "año", "senor" por "señor").
- **Perspectiva:** Estrictamente **3ª Persona** ("Los científicos descubrieron...", "El océano esconde...").
- **Tono:** Cautivador, rápido, lógico. Sin relleno. Cada oración debe generar curiosidad.
- **Estructura:** Exactamente {num_scenes} escenas en total.
- **Flujo:** {flow_es}.
- **HOOK CRITICO (Escena 1, maximo 12 palabras):** OBLIGATORIO uno de: (A) Numero shockeante + consecuencia brutal, (B) "Todo lo que sabes sobre X esta mal", (C) "Nadie habla de lo que paso con X", (D) Pregunta trampa imposible de ignorar.{f' HOOK PRE-SELECCIONADO (usar EXACTO): "{chosen_hook}"' if chosen_hook else ""}
{extra_es}
### 2. REQUISITOS VISUALES (Doble visual por escena):
- Para CADA escena, proporciona DOS términos de búsqueda distintos:
  - **visual_1:** Corresponde al *inicio* de la oración.
  - **visual_2:** Corresponde al *final* de la oración o proporciona contexto/reacción.
- **CRÍTICO:** Los términos visual_1 y visual_2 deben estar en INGLÉS (para búsqueda en Pexels).

### FORMATO DE SALIDA (JSON estricto, exactamente {num_scenes} entradas):
[
    {{
        "id": 1,
        "text": "En 1995, catorce lobos fueron liberados en el Parque Yellowstone, y cambiaron el curso de los ríos.",
        "visual_1": "wolves running snow aerial",
        "visual_2": "river flowing forest drone",
        "mood": "intriguing"
    }}
]"""
        else:
            prompt = f"""You are the lead scriptwriter for a high-retention "Edutainment" YouTube Shorts channel.

Topic: {topic}

### GOAL:
Create a script where every sentence has a "Visual Switch" to keep retention high.
We need TWO different stock videos for every single scene.

### 1. SCRIPT REQUIREMENTS (The Voiceover):
- **Language:** ENGLISH ONLY. Every single word must be in English. No Spanish words whatsoever.
- **Emojis:** NO emojis. Pure narration text only.
- **Perspective:** Strictly **3rd Person** ("Scientists found...", "The ocean hides...").
- **Tone:** Engaging, fast-paced, logical. No fluff. Every sentence must build curiosity.
- **Structure:** Exactly {num_scenes} scenes total.
- **Flow:** {flow_en}.
- **CRITICAL HOOK (Scene 1, max 12 words):** MANDATORY one of: (A) Shocking number + brutal consequence, (B) "Everything you know about X is wrong", (C) "Nobody is talking about what happened with X", (D) Impossible-to-ignore trap question.{f' PRE-SELECTED HOOK (use EXACT text): "{chosen_hook}"' if chosen_hook else ""}
{extra_en}
### 2. VISUAL REQUIREMENTS (Dual Visuals):
- For EVERY scene, provide TWO distinct search terms:
  - **visual_1:** Matches the *start* of the sentence.
  - **visual_2:** Matches the *end* of the sentence or provides reaction/context.
- **Strictly Literal:** If the text is "The economy crashed," search "stock market crash red chart".

### OUTPUT FORMAT (Strict JSON, exactly {num_scenes} entries):
[
    {{
        "id": 1,
        "text": "In 1995, fourteen wolves were released into Yellowstone Park, and they changed the rivers.",
        "visual_1": "wolves running snow aerial",
        "visual_2": "river flowing forest drone",
        "mood": "intriguing"
    }}
]"""

        raw = self._generate(prompt)
        clean_text = raw.replace('```json', '').replace('```', '').strip()

        try:
            scenes = json.loads(clean_text)
            if len(scenes) > num_scenes:
                print(f"⚠️ AI returned {len(scenes)} scenes, trimming to {num_scenes}.")
                scenes = scenes[:num_scenes]
            elif len(scenes) < num_scenes:
                print(f"⚠️ AI returned only {len(scenes)} scenes (requested {num_scenes}).")
            for i, scene in enumerate(scenes):
                scene['id']   = i + 1
                scene['text'] = self._sanitize(scene.get('text', ''))
            return scenes
        except json.JSONDecodeError:
            print("❌ Error parsing JSON. Raw output:")
            print(clean_text)
            return None

    def generate_meme_laboral_script(self, category: str = "", lang: str = "es",
                                      num_memes: int = 7) -> list:
        """Genera una secuencia de memes laborales virales para Shorts/TikTok."""
        print(f"😂 Meme Laboral script: {category or 'general'} ({num_memes} memes)...")

        if lang == "es":
            prompt = f"""Eres el creador de contenido laboral mas viral de TikTok en espanol.
Tu especialidad: memes de trabajo que hacen que la gente comparta porque "me representa al 100%".

Categoria laboral: {category or "Indignacion Laboral general"}

FORMATOS VIRALES — mezcla los mas adecuados para la categoria (no repitas el mismo dos veces seguidas):

F1 POV — empieza con "POV:" y crea escena en 1 frase. Golpe directo.
   Ej: "POV: Tu jefe dice que no hay presupuesto desde su coche de empresa nuevo"

F2 EXPECTATIVA vs REALIDAD — 2 lineas: lo que prometen / lo que es en realidad.
   Ej: "La oferta: ambiente dinamico y equipo unido. La realidad: 3 personas haciendo el trabajo de 9"

F3 NADIE / JEFE — setup vacio + accion del jefe fuera de lugar.
   Ej: "Nadie absolutamente nadie. Mi jefe a las 5:58pm del viernes:"

F4 YO CUANDO — reaccion a situacion laboral universal.
   Ej: "Yo cuando me entero que el companero nuevo gana el doble haciendo la mitad"

F5 ANTES / DESPUES — contraste entre expectativa inicial y realidad tras meses.
   Ej: "Yo el dia 1 lleno de ilusion vs yo 8 meses despues con el ojo twitchando"

F6 OFERTA PARODIA — oferta de empleo con requisitos absurdos + sueldo ridiculo.
   Ej: "Se busca: 15 anios experiencia, MBA, 4 idiomas, disponibilidad 24/7. Sueldo: 'acorde al mercado'"

F7 FRASE SOLA RELATABLE — 1 frase directa sin setup. El 90% la guarda o la envia.
   Ej: "La empresa no puede subir tu sueldo pero si contratar al jefe de tu jefe"

F8 COMPARACION DE 3 — lo que prometen / lo que das / lo que te pagan.
   Ej: "Prometen: flexibilidad. Tu das: 60 horas semanales. Te pagan: el minimo legal"

F9 ESE MOMENTO CUANDO — nostalgia dolorosa + humor negro.
   Ej: "Ese momento cuando tu evaluacion dice 'Desempeno Excepcional' y el aumento es 0%"

REGLAS ABSOLUTAS:
- Cada meme funciona SOLO, sin contexto previo del siguiente
- Maximo 25 palabras de texto por meme — brevedad brutal
- PROHIBIDO: palabras con la letra n con tilde (usa "anio" no "ano", "senor" no "senor"), emojis en el texto
- El humor: NEGRO pero RELATABLE — que duela Y haga reir al mismo tiempo
- Variedad: mezcla formatos, no pongas dos POV seguidos
- Visuals en INGLES, 3-5 palabras, imagenes de stock reales y reconocibles

FORMATO DE SALIDA (JSON estricto, exactamente {num_memes} entradas, sin markdown):
[
  {{
    "id": 1,
    "meme_formato": "POV",
    "text": "POV: Tu jefe dice que no hay dinero para subir sueldos desde su BMW nuevo",
    "visual_1": "luxury car office parking lot",
    "visual_2": "employee frustrated desk low salary",
    "mood": "sarcastic"
  }}
]"""
        else:
            prompt = f"""You are the most viral workplace content creator on TikTok.
Your specialty: work memes people share because "this is literally me".

Work category: {category or "General Work Outrage"}

VIRAL FORMATS — mix the most fitting for the category (never repeat the same format twice in a row):

F1 POV — starts with "POV:" and sets the scene in 1 line.
   Ex: "POV: Your boss says there is no budget for raises from his new company car"

F2 EXPECTATION vs REALITY — 2 lines: what they promise / what it actually is.
   Ex: "Job posting: dynamic team and growth. Reality: 3 people doing the work of 9"

F3 NOBODY / BOSS — empty setup + boss doing something out of place.
   Ex: "Nobody. Nobody at all. My boss at 5:58pm on Friday:"

F4 ME WHEN — reaction to a universal work situation.
   Ex: "Me when I find out the new hire makes double doing half the work"

F5 BEFORE / AFTER — contrast between initial excitement and months-later reality.
   Ex: "Me on day 1 full of hope vs me 8 months later with a permanent eye twitch"

F6 PARODY JOB LISTING — absurd requirements + ridiculous salary.
   Ex: "Wanted: 15 years experience, MBA, 4 languages, 24/7 availability. Salary: competitive"

F7 SOLO RELATABLE LINE — 1 direct punch line, no setup. 90% save or forward it.
   Ex: "The company cannot afford your raise but just hired your boss a new boss"

F8 TRIPLE COMPARISON — what they promise / what you give / what they pay.
   Ex: "They promise: flexibility. You give: 60 hours a week. They pay: legal minimum"

F9 THAT EXACT MOMENT — painful collective nostalgia + dark humor.
   Ex: "That exact moment when your review says Exceptional Performance and the raise is 0 percent"

ABSOLUTE RULES:
- Each meme works ALONE, zero prior context needed
- Maximum 25 words of text per meme — brutal brevity
- FORBIDDEN: emojis in text, long explanations
- Humor: DARK but RELATABLE — it should sting AND make you laugh
- Variety: mix formats, never two POVs back to back
- Visuals in ENGLISH, 3-5 words, real recognizable stock imagery

OUTPUT FORMAT (strict JSON, exactly {num_memes} entries, no markdown):
[
  {{
    "id": 1,
    "meme_formato": "POV",
    "text": "POV: Your boss says there is no money for raises from his brand new BMW",
    "visual_1": "luxury car office parking lot",
    "visual_2": "employee frustrated desk low salary",
    "mood": "sarcastic"
  }}
]"""

        raw = self._generate(prompt)
        clean_text = raw.replace('```json', '').replace('```', '').strip()
        try:
            memes = json.loads(clean_text)
            if len(memes) > num_memes:
                memes = memes[:num_memes]
            for i, meme in enumerate(memes):
                meme['id']   = i + 1
                meme['text'] = self._sanitize(meme.get('text', ''))
            return memes
        except json.JSONDecodeError:
            print("❌ Error parsing meme JSON. Raw output:")
            print(clean_text)
            return None

    def generate_ciencia_facil_script(self, topic: str, category: str = "", lang: str = "es",
                                      chosen_hook: str = "", num_scenes: int = 9,
                                      max_words_per_scene: int = 999) -> list:
        """Guion edutainment: ciencia cotidiana sin tecnicismos, tono de amigo listo."""
        print(f"🔬 Ciencia Fácil script: {topic} ({num_scenes} scenes)...")

        if lang == "es":
            prompt = f"""Eres el guionista de un canal de TikTok/YouTube Shorts llamado "Ciencia para Todos".
Tu misión: explicar ciencia real de forma cercana, sorprendente y SIN JERGA TÉCNICA.
Hablas como un amigo curioso que acaba de descubrir algo alucinante y quiere contártelo.

Tema: {topic}
Categoría: {category or "Ciencia cotidiana"}

### REGLAS DE ESCRITURA (CRÍTICAS):
- **Tono:** Conversacional y cercano. Como si le explicaras a tu mejor amigo en una cafetería.
- **Sin tecnicismos solos:** Si DEBES usar un término técnico, INMEDIATAMENTE lo explicas con una analogía cotidiana entre paréntesis o con "es decir..." / "o sea...".
- **Perspectiva:** Mezcla de 2ª persona ("tu cuerpo hace X") y 3ª persona ("los científicos descubrieron..."). Involucra al espectador.
- **Estructura:** Exactamente {num_scenes} escenas.
- **Flujo:** Gancho sorprendente → Pregunta que todos se hacen → Explicación simple con analogía → Dato que lo hace más increíble → Cierre con "dato bonus" o "aplícalo en tu vida".
- **HOOK CRÍTICO (Escena 1, máximo 12 palabras):** Debe ser una pregunta trampa, un dato cotidiano sorprendente, o una creencia popular que el video destruirá.{f' HOOK PRE-SELECCIONADO (usar EXACTO): "{chosen_hook}"' if chosen_hook else ""}
- **Máximo {max_words_per_scene} palabras por escena.**
- **PROHIBIDO:** emojis, fórmulas químicas o físicas sin explicar, palabras con ñ (usa "anio", "senor", "Espana"), anglicismos innecesarios.
- **RIGOR (crítico):** no inventes cifras, porcentajes, anios ni atribuciones. Si no estás seguro del número exacto, describe el hallazgo en términos cualitativos ("la mayoría", "buena parte de") en lugar de fabricar una cifra falsa. Nunca atribuyas un estudio a una universidad o investigador si no lo tienes claro.
- **UNA IDEA POR ESCENA:** si una escena necesita dos explicaciones distintas, divídela o simplifica.
- **APLICABLE:** al menos UNA escena debe dar algo concreto que el espectador pueda observar o hacer hoy, en una frase (no vale un consejo genérico).

### REQUISITOS VISUALES (Pexels):
- **visual_1:** Imagen cotidiana que el espectador reconoce inmediatamente (no laboratorios vacíos).
- **visual_2:** Visualización del fenómeno o analogía usada en la escena.
- Ambos en INGLÉS, 3-5 palabras, específicos y visuales.

### FORMATO DE SALIDA (JSON estricto, exactamente {num_scenes} entradas):
[
    {{
        "id": 1,
        "text": "Tu cerebro lleva toda tu vida confiando en tus recuerdos. Pero hay un problema: aproximadamente el 40% de ellos son falsos.",
        "visual_1": "person thinking daydream close-up",
        "visual_2": "brain memory neurons colorful",
        "mood": "intriguing"
    }}
]"""
        else:
            prompt = f"""You are the scriptwriter for a TikTok/YouTube Shorts channel called "Science for Everyone".
Your mission: explain real science in a relatable, surprising way — ZERO JARGON.
You talk like a smart curious friend who just discovered something mind-blowing and can't wait to share it.

Topic: {topic}
Category: {category or "Everyday science"}

### WRITING RULES (CRITICAL):
- **Tone:** Conversational and warm. Like explaining to your best friend at a coffee shop.
- **No jargon alone:** If you MUST use a technical term, IMMEDIATELY explain it with an everyday analogy in parentheses or with "meaning..." / "basically...".
- **Perspective:** Mix of 2nd person ("your body does X") and 3rd person ("scientists discovered..."). Involve the viewer.
- **Structure:** Exactly {num_scenes} scenes.
- **Flow:** Surprising hook → Question everyone asks → Simple explanation with analogy → Fact that makes it more incredible → Closing "bonus fact" or "apply it in your life".
- **CRITICAL HOOK (Scene 1, max 12 words):** Must be a trap question, a surprising everyday fact, or a popular belief the video will destroy.{f' PRE-SELECTED HOOK (use EXACT text): "{chosen_hook}"' if chosen_hook else ""}
- **Maximum {max_words_per_scene} words per scene.**
- **FORBIDDEN:** emojis, unexplained chemical/physics formulas, unnecessary jargon.
- **RIGOR (critical):** do not invent figures, percentages, years or attributions. If unsure of the exact number, describe the finding qualitatively ("most", "a large share of") instead of fabricating a false stat. Never attribute a study to a university or researcher unless you are certain.
- **ONE IDEA PER SCENE:** if a scene needs two separate explanations, split it or simplify.
- **APPLICABLE:** at least ONE scene must give something concrete the viewer can observe or do today, in one sentence (a generic tip does not count).

### VISUAL REQUIREMENTS (Pexels):
- **visual_1:** Everyday image the viewer immediately recognizes (not empty labs).
- **visual_2:** Visualization of the phenomenon or analogy used in the scene.
- Both in ENGLISH, 3-5 words, specific and visual.

### OUTPUT FORMAT (Strict JSON, exactly {num_scenes} entries):
[
    {{
        "id": 1,
        "text": "Your brain has spent your whole life trusting your memories. But there's a problem: roughly 40% of them are false.",
        "visual_1": "person thinking daydream close-up",
        "visual_2": "brain memory neurons colorful",
        "mood": "intriguing"
    }}
]"""

        raw = self._generate(prompt)
        clean_text = raw.replace('```json', '').replace('```', '').strip()
        try:
            scenes = json.loads(clean_text)
            if len(scenes) > num_scenes:
                scenes = scenes[:num_scenes]
            for i, scene in enumerate(scenes):
                scene['id']   = i + 1
                scene['text'] = self._sanitize(scene.get('text', ''))
            return scenes
        except json.JSONDecodeError:
            print("❌ Error parsing JSON (ciencia_facil). Raw output:")
            print(clean_text)
            return None

    def generate_podcast_script(self, topic: str, host_name: str = "Host",
                                guest_name: str = "Invitado", lang: str = "es",
                                num_exchanges: int = 6, max_words_per_scene: int = 999) -> list:
        """Genera un diálogo estilo podcast entre dos personas para YouTube Shorts."""
        import re as _re
        print(f"🎙️ Generando diálogo podcast: {topic}...")

        if lang == "es":
            prompt = f"""Eres el guionista de un canal de podcast viral para YouTube Shorts en español latino.

Genera un diálogo natural y fluido entre dos personas:
- Host: {host_name} — hace preguntas, presenta el tema, conduce la conversación
- Invitado: {guest_name} — responde con datos fascinantes, revela información impactante

Tema: {topic}

ESTRUCTURA (EXACTAMENTE {num_exchanges} intercambios / MAXIMO {max_words_per_scene} palabras por turno):
- Turno 1 (Host): Hook viral — pregunta o dato impactante que engancha en 1.7 segundos
- Turnos 2-{num_exchanges - 1}: Diálogo natural alternado con revelaciones progresivas
- Turno {num_exchanges} (Host o Guest): Conclusión + CTA ("Comenta qué opinas y síguenos")

REGLAS:
- Lenguaje conversacional, como si hablaran de verdad, no como narración
- Frases cortas y directas — máximo {max_words_per_scene} palabras por turno
- Datos reales y verificables
- PROHIBIDO: emojis, caracteres Unicode especiales, la letra ñ
- Solo letras, números, comas, puntos, signos de exclamación e interrogación

FORMATO JSON estricto, sin markdown:
[
  {{"id":1,"speaker":"host","text":"¿Sabías que...?","visual_1":"podcast studio microphone","visual_2":"two people talking","mood":"informative"}},
  {{"id":2,"speaker":"guest","text":"Sí, y lo más increíble es...","visual_1":"person explaining animated","visual_2":"podcast closeup face","mood":"informative"}}
]

REGLAS DEL JSON:
- "speaker": "host" o "guest" (alternando, empezar con host)
- "text": el diálogo de ese turno. MAX {max_words_per_scene} palabras. Sin caracteres especiales.
- "visual_1" y "visual_2": términos EN INGLÉS para Pexels (2-4 palabras). Podcast: studio, microphone, conversation, talking, discussion.
- "mood": "informative", "fun", "exciting" o "professional"
- EXACTAMENTE {num_exchanges} entradas"""
        else:
            prompt = f"""You are the scriptwriter of a viral podcast channel for YouTube Shorts.

Generate a natural and fluid dialogue between two people:
- Host: {host_name} — asks questions, introduces the topic, leads the conversation
- Guest: {guest_name} — responds with fascinating data, reveals impactful information

Topic: {topic}

STRUCTURE (EXACTLY {num_exchanges} exchanges / MAX {max_words_per_scene} words per turn):
- Turn 1 (Host): Viral hook — impactful question or fact that hooks in 1.7 seconds
- Turns 2-{num_exchanges - 1}: Natural alternating dialogue with progressive revelations
- Turn {num_exchanges} (Host or Guest): Conclusion + CTA ("Comment what you think and follow us")

RULES:
- Conversational language, as if they are really talking, not narrating
- Short and direct phrases — maximum {max_words_per_scene} words per turn
- Real and verifiable data
- FORBIDDEN: emojis, special Unicode characters
- Only letters, numbers, commas, periods, exclamation and question marks

Strict JSON format, no markdown:
[
  {{"id":1,"speaker":"host","text":"Did you know that...?","visual_1":"podcast studio microphone","visual_2":"two people talking","mood":"informative"}},
  {{"id":2,"speaker":"guest","text":"Yes, and the most incredible thing is...","visual_1":"person explaining animated","visual_2":"podcast closeup face","mood":"informative"}}
]

JSON RULES:
- "speaker": "host" or "guest" (alternating, start with host)
- "text": the dialogue for that turn. MAX {max_words_per_scene} words. No special characters.
- "visual_1" and "visual_2": English Pexels search terms (2-4 words). Podcast: studio, microphone, conversation, talking, discussion.
- "mood": "informative", "fun", "exciting" or "professional"
- EXACTLY {num_exchanges} entries"""

        raw   = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()

        try:
            scenes = json.loads(clean)
            for i, s in enumerate(scenes):
                s['id']   = i + 1
                s['text'] = self._sanitize(s.get('text', ''))
                s.setdefault('mood', 'informative')
                s.setdefault('speaker', 'host' if i % 2 == 0 else 'guest')
            if len(scenes) > num_exchanges:
                print(f"⚠️ AI returned {len(scenes)} podcast scenes, trimming to {num_exchanges}.")
                scenes = scenes[:num_exchanges]
            elif len(scenes) < num_exchanges:
                print(f"⚠️ AI returned only {len(scenes)} podcast scenes (requested {num_exchanges}).")
            print(f"✅ {len(scenes)} podcast scenes ready")
            return scenes
        except Exception:
            sentences = [s.strip() for s in _re.split(r'(?<=[.!?])\s+', clean) if len(s.strip()) > 8][:num_exchanges]
            return [
                {
                    "id": i + 1,
                    "text": self._sanitize(s),
                    "speaker": "host" if i % 2 == 0 else "guest",
                    "visual_1": "podcast studio microphone",
                    "visual_2": "two people talking",
                    "mood": "informative",
                }
                for i, s in enumerate(sentences)
            ]

    def generate_quote_card_prompts(
        self,
        quote: str = "",
        category: str = "",
        lang: str = "es",
    ) -> dict:
        """
        Genera prompts de imagen para una frase célebre o viral en 3 formatos:
        9:16 (Reels/Stories), 1:1 (Instagram post), 16:9 (YouTube/LinkedIn).

        Si no se provee frase, la IA elige una viral/célebre de la categoría dada.
        Retorna dict con keys: quote_used, prompt_9_16, prompt_1_1, prompt_16_9
        """
        print(f"💬 Generando prompts de frase viral [{category or 'auto'}]...")

        # ── Step 1: resolve quote ─────────────────────────────────────────────
        if not quote.strip() and category.strip():
            if lang == "es":
                _qprompt = (
                    f"Dame UNA frase célebre, viral o motivacional de la categoría: {category}.\n"
                    f"Debe ser impactante, compartible y no demasiado larga (máximo 20 palabras).\n"
                    f"Puede ser de un personaje famoso o una frase anónima que haya viralizado.\n"
                    f"Responde SOLO con la frase y el autor si lo hay (formato: 'Frase.' — Autor). Nada más."
                )
            else:
                _qprompt = (
                    f"Give me ONE famous, viral or motivational quote from the category: {category}.\n"
                    f"Must be impactful, shareable, not too long (max 20 words).\n"
                    f"Can be from a famous person or an anonymous viral phrase.\n"
                    f"Respond ONLY with the quote and author if known (format: 'Quote.' — Author). Nothing else."
                )
            quote = self._sanitize(self._generate(_qprompt).strip())
        elif not quote.strip():
            if lang == "es":
                _qprompt = (
                    f"Dame UNA frase célebre o viral de cualquier categoría que esté generando "
                    f"mucha interacción en redes sociales actualmente. "
                    f"Máximo 20 palabras. Formato: 'Frase.' — Autor (o 'Anónimo'). Solo la frase."
                )
            else:
                _qprompt = (
                    f"Give me ONE famous or viral quote from any category that's generating "
                    f"high social media engagement right now. "
                    f"Max 20 words. Format: 'Quote.' — Author (or 'Anonymous'). Just the quote."
                )
            quote = self._sanitize(self._generate(_qprompt).strip())

        print(f"💬 Frase: {quote[:80]}")

        # ── Step 2: common context for all 3 formats ──────────────────────────
        _ctx = f"Quote / frase: \"{quote}\"\nCategory / categoría: {category or 'general'}"

        _style_ref = (
            "Visual style rules:\n"
            "- Cinematic, dramatic, high-contrast\n"
            "- The quote text MUST appear as an overlay on the image (specify exact text)\n"
            "- Background: rich, atmospheric, relevant to the quote's theme\n"
            "- Lighting: dramatic volumetric light (god rays, rim light, or neon glow)\n"
            "- Color palette: deep moody tones OR vibrant energetic tones — match the quote's emotion\n"
            "- Photorealistic or painterly — NO flat design, NO plain backgrounds\n"
            "- PROHIBIDO: bordes blancos, fondos lisos, diseño minimalista sin textura\n"
            "- The quote text overlay must be bold, legible, high contrast, in the quote's original language\n"
            "- Do NOT add any text beyond the quote and optional author credit\n"
        )

        # ── Step 3: generate 3 format prompts in one LLM call ─────────────────
        if lang == "es":
            _main_prompt = f"""Eres un experto en diseño de contenido viral para redes sociales y un maestro generando prompts para IA de imagen (Midjourney, DALL-E, Flux, Ideogram).

{_ctx}

TAREA: Genera EXACTAMENTE 3 prompts de imagen — uno por formato — para una "quote card" (tarjeta con frase) de alto impacto visual que genere interacción masiva en redes sociales.

{_style_ref}

INSTRUCCIONES POR FORMATO:

**FORMATO 9:16 (Reels / Stories / TikTok — VERTICAL)**
- Composición vertical dominante
- La frase ocupa el centro o la mitad inferior
- Fondo: escena atmosférica vertical que no compite con el texto
- Estilo: dramático, editorial, para capturar scroll en 0.5 segundos

**FORMATO 1:1 (Instagram Post / Facebook — CUADRADO)**
- Composición equilibrada y centrada
- La frase puede estar arriba, centro o abajo con margen igual en todos lados
- Fondo: equilibrado, no muy ocupado en los bordes
- Estilo: limpio pero poderoso, optimizado para engagement de post

**FORMATO 16:9 (YouTube / LinkedIn / Twitter — HORIZONTAL)**
- La frase en el tercio izquierdo o centrada
- Background dramático en el tercio derecho o detrás
- Espacio visual izquierdo para texto, lado derecho con escena
- Estilo: thumbnail cinematográfico, click-worthy

FORMATO DE SALIDA (JSON estricto, sin markdown):
{{
  "quote_used": "la frase exacta que usarás",
  "prompt_9_16": "prompt completo en inglés listo para pegar en Midjourney/DALL-E — incluye la frase como texto overlay especificado, composición vertical, iluminación, estilo",
  "prompt_1_1":  "prompt completo en inglés — composición cuadrada, misma frase como texto overlay",
  "prompt_16_9": "prompt completo en inglés — composición horizontal 16:9, misma frase como texto overlay",
  "copy_tiktok": "1-2 líneas gancho + salto de línea + hashtags TikTok: SIEMPRE incluir #fyp #viral al inicio + 2 hashtags de nicho específicos. MAXIMO 4 hashtags en total. En español.",
  "copy_instagram": "2-3 líneas reflexivas que inviten a guardar o compartir + doble salto de línea + EXACTAMENTE 4 hashtags: 1 amplio (1M+ posts) + 1 mediano (100K-1M) + 2 de nicho específico (<100K). MAXIMO 4 hashtags. En español.",
  "copy_facebook": "2-3 líneas conversacionales que generen comentarios (pregunta al final) + MAXIMO 3 hashtags del nicho. Facebook penaliza el exceso de hashtags — menos es más. En español.",
  "copy_twitter": "1 frase directa e impactante + MAXIMO 2 hashtags trending. Máximo 280 caracteres total. En español."
}}

REGLAS CRÍTICAS:
- Los prompts van en INGLÉS (para compatibilidad con los modelos de imagen)
- El texto de la frase que aparece en la imagen va en el IDIOMA ORIGINAL de la frase
- Cada prompt debe tener mínimo 80 palabras y máximo 200 palabras
- Cada prompt debe especificar: sujeto/escena, composición, iluminación, estilo, texto overlay, ratio
- NO repitas el mismo background en los 3 formatos — adapta el encuadre
- Los copies van en español neutro, directos y optimizados para máxima viralidad en cada plataforma
- Los hashtags deben ser REALES y específicos del nicho — PROHIBIDO hashtags genéricos vacíos"""
        else:
            _main_prompt = f"""You are an expert in viral social media content design and a master at generating prompts for AI image generation (Midjourney, DALL-E, Flux, Ideogram).

{_ctx}

TASK: Generate EXACTLY 3 image prompts — one per format — for a high-impact "quote card" that drives massive engagement on social media.

{_style_ref}

FORMAT INSTRUCTIONS:

**FORMAT 9:16 (Reels / Stories / TikTok — VERTICAL)**
- Vertical dominant composition
- Quote occupies center or lower half
- Background: atmospheric vertical scene that doesn't compete with text
- Style: dramatic, editorial, designed to stop scrolling in 0.5 seconds

**FORMAT 1:1 (Instagram Post / Facebook — SQUARE)**
- Balanced, centered composition
- Quote can be top, center or bottom with equal margins on all sides
- Background: balanced, not too busy at edges
- Style: clean but powerful, optimized for post engagement

**FORMAT 16:9 (YouTube / LinkedIn / Twitter — HORIZONTAL)**
- Quote in left third or centered
- Dramatic background in right third or behind
- Left visual space for text, right side with scene
- Style: cinematic thumbnail, click-worthy

OUTPUT FORMAT (strict JSON, no markdown):
{{
  "quote_used": "the exact quote you're using",
  "prompt_9_16": "complete English prompt ready to paste in Midjourney/DALL-E — includes the quote as specified text overlay, vertical composition, lighting, style",
  "prompt_1_1":  "complete English prompt — square composition, same quote as text overlay",
  "prompt_16_9": "complete English prompt — horizontal 16:9 composition, same quote as text overlay",
  "copy_tiktok": "1-2 hook lines + line break + TikTok hashtags: ALWAYS start with #fyp #viral + 2 niche-specific hashtags. MAXIMUM 4 hashtags total. In English.",
  "copy_instagram": "2-3 reflective lines inviting saves or shares + double line break + EXACTLY 4 hashtags: 1 broad (1M+ posts) + 1 medium (100K-1M) + 2 niche-specific (<100K). MAXIMUM 4 hashtags. In English.",
  "copy_facebook": "2-3 conversational lines that spark comments (end with a question) + MAXIMUM 3 niche hashtags. Facebook penalizes hashtag overload — less is more. In English.",
  "copy_twitter": "1 direct impactful sentence + MAXIMUM 2 trending hashtags. Max 280 characters total. In English."
}}

CRITICAL RULES:
- Prompts in ENGLISH (for AI image model compatibility)
- The quote text that appears in the image stays in its original language
- Each prompt: minimum 80 words, maximum 200 words
- Each prompt must specify: subject/scene, composition, lighting, style, text overlay, ratio
- Do NOT reuse the same background for all 3 formats — adapt the framing
- Copies must be punchy and optimized for maximum virality on each platform
- Hashtags must be REAL and niche-specific — FORBIDDEN generic empty hashtags"""

        raw   = self._generate(_main_prompt)
        clean = raw.replace("```json", "").replace("```", "").strip()
        bracket = clean.find("{")
        if bracket > 0:
            clean = clean[bracket:]
        try:
            import json as _j
            result = _j.loads(clean)
            return {
                "quote_used":     result.get("quote_used", quote),
                "prompt_9_16":    self._sanitize(result.get("prompt_9_16", "")),
                "prompt_1_1":     self._sanitize(result.get("prompt_1_1", "")),
                "prompt_16_9":    self._sanitize(result.get("prompt_16_9", "")),
                "copy_tiktok":    self._sanitize(result.get("copy_tiktok", "")),
                "copy_instagram": self._sanitize(result.get("copy_instagram", "")),
                "copy_facebook":  self._sanitize(result.get("copy_facebook", "")),
                "copy_twitter":   self._sanitize(result.get("copy_twitter", "")),
            }
        except Exception:
            return {
                "quote_used":     quote,
                "prompt_9_16":    clean[:800],
                "prompt_1_1":     "",
                "prompt_16_9":    "",
                "copy_tiktok":    "",
                "copy_instagram": "",
                "copy_facebook":  "",
                "copy_twitter":   "",
            }

    def generate_thumbnail_prompt(self, topic: str, script: list, lang: str = "es",
                                   mode: str = "auto", offer_text: str = "") -> str:
        print("🖼️ Generating thumbnail prompt...")
        hook = script[0]['text'] if script else ""

        # ── MODO EMPLEO: prompt especializado de reclutamiento ─────────────────
        if mode == "empleo":
            # Extraer datos clave del guion para no inventar nada
            script_lines = " | ".join(s.get("text", "") for s in script[:6])
            source_ctx   = offer_text.strip()[:1200] if offer_text.strip() else script_lines

            prompt = f"""You are an expert in visual marketing, performance ads and viral recruitment thumbnail design.

JOB OFFER SOURCE (use ONLY this — do NOT invent anything):
---
{source_ctx}
---

EXTRACTED SCRIPT SCENES (reference for copy):
{script_lines}

YOUR TASK: Generate ONE complete image prompt (ready for DALL-E / Midjourney) for a job offer thumbnail.

MANDATORY RULES:
1. RECRUITMENT FOCUS — transmit opportunity, growth and money. Positive and energetic.
2. 70% positive visual dominance. If using contrast (duality), positive side must dominate.
3. COPY INSIDE THE IMAGE (extract ONLY from the offer, no invention):
   - Top title: what the job is (e.g. "REPARTIDOR", "VENDEDOR", "DISEÑADOR")
   - Main headline: the economic or emotional main benefit
   - Secondary badge: specific earning or key advantage (salary if mentioned)
   - Call to action: "EMPIEZA HOY" or "APLICA YA"
4. VISUAL STYLE:
   - Viral thumbnail, cinematic, optimistic and energetic
   - Dramatic but positive lighting: golden glow, neon energy, bright highlights
   - Progress elements: money, apps, metrics, action, celebration, success
   - Vertical composition 9:16, centered, mobile-optimized
   - Photorealistic, 8K, maximum detail
5. ADAPT to job type detected:
   - Delivery/field: outdoor energy, vehicle, city, motion blur
   - Office/remote: modern workspace, laptop, skyline, professional glow
   - Sales: handshake, money rain, targets hit, celebration
   - Technical: tools, precision, expertise glow
6. TEXT ON IMAGE: ALL IN SPANISH (Spanish-speaking audience)
7. PROMPT LANGUAGE: English (for AI image generation compatibility)

OUTPUT FORMAT — return exactly this structure, no markdown, no explanations:

[ONE LINE: brief creative concept]
---
[FULL PROMPT ready for DALL-E/Midjourney, in English, with Spanish overlay texts specified]
"""
            return self._generate(prompt).strip()

        # ── RESTO DE MODOS: prompt cinematográfico estándar ──────────────────
        if lang == "es":
            word_lang_instruction = (
                "- El prompt de imagen va en INGLÉS (para compatibilidad con Midjourney/DALL-E).\n"
                "- EXCEPCIÓN IMPORTANTE: Las palabras del título, badge y headline superpuestos en la imagen "
                "DEBEN estar en ESPAÑOL. Ejemplo: en vez de 'ETERNITY' usa 'ETERNIDAD', "
                "en vez de 'LOST REALM' usa 'REINO PERDIDO', en vez de 'MYTH' usa 'MITO'.\n"
                "- El subtítulo contextual final también debe ir en ESPAÑOL."
            )
        else:
            word_lang_instruction = (
                "- Every single word in the entire prompt — including title, badge, headline, and subtitle — "
                "MUST be in ENGLISH. Absolutely no other language."
            )

        prompt = f"""
You are an expert AI image prompt engineer specializing in viral YouTube Shorts thumbnails.

Video topic: "{topic}"
Opening line: "{hook}"

### YOUR TASK:
Write an image generation prompt following EXACTLY this style reference structure.
Adapt every element to match the video topic — do NOT copy the jellyfish example.

### STYLE REFERENCE (adapt — do not copy):
"Viral thumbnail style, cinematic documentary, dramatic high contrast photo, dual nature.
A massive [SUBJECT] is split vertically. Left side: [POSITIVE/ALIVE/BEGINNING aspect],
luminous glow. Right side: [NEGATIVE/DARK/END aspect], dark and decaying counterpart.
The central vertical axis is sharp. Exaggerated visual duality. Iconic [SUBJECT] centered.
Background is [FITTING DARK ENVIRONMENT], with a dramatic volumetric light beam piercing
from the top right, creating hard shadows and bright highlights on the [SUBJECT].
Swirling particles (dust, embers, glowing debris) around the central figure.
Breaking news/historic discovery aesthetic. Maximum detail, photorealistic, 8k,
vertical composition (9:16). Centralized composition, all key elements within the
central 1:1 safe area. Top area is clear of text.
Title overlaid in the upper center, one dominant word: '[WORD]' with a rugged,
glowing stone texture. Below it, a short secondary badge: '[SHORT_LABEL]' like a label.
Main headline below that, a large powerful word: '[WORD_2]' with a bright crystalline texture.
Finally, a short contextual subtitle relevant to the topic."

### LANGUAGE RULES:
{word_lang_instruction}
- Title and Headline must be single dramatic words in ALL CAPS.
- Badge and subtitle must be short punchy phrases.

### OTHER RULES:
- Keep the same structural format and length as the reference.
- Replace every placeholder with elements specific to "{topic}".
- Return ONLY the final prompt text. No explanations. No JSON. No markdown.
"""
        return self._generate(prompt).strip()

    def generate_copy(self, topic: str, script: list, lang: str = "es", mode: str = "auto") -> dict:
        label = "Generando copy para redes sociales" if lang == "es" else "Generating social media copy"
        print(f"✍️ {label}...")
        hook = script[0]['text'] if script else ""
        last = script[-1]['text'] if script else ""

        # Hashtag pools para TikTok: #fyp + #viral fijos + 3 del nicho = 5 exactos
        # Para Facebook/YouTube se usan solo los 3 del nicho (sin fyp/viral)
        _ht = {
            "viral":      ("#HistoriaOscura #HechosImpactantes #DarkHistory",
                           "#DarkHistory #MysteryFacts #DidYouKnow"),
            "testimonio": ("#Misterio #TerrorReal #HistoriaOculta",
                           "#Mystery #Horror #TrueStory"),
            "libro":      ("#ResumenDeLibro #Lectura #DesarrolloPersonal",
                           "#BookSummary #SelfImprovement #LearnSomethingNew"),
            "empleo":     ("#OfertaDeEmpleo #BuscandoEmpleo #OportunidadLaboral",
                           "#JobOffer #NowHiring #JobOpportunity"),
            "guion":      ("#NoticiasVirales #LoCurioso #SabiaQue",
                           "#ViralNews #DidYouKnow #InterestingFacts"),
        }
        _niche_es, _niche_en = _ht.get(mode, ("#HechosCuriosos #CienciaYMisterio #DatosImpactantes",
                                               "#DidYouKnow #MindBlowing #FunFacts"))
        # TikTok: siempre #fyp #viral + 3 del nicho (total 5)
        hashtags_tiktok_es = f"#fyp #viral {_niche_es}"
        hashtags_tiktok_en = f"#fyp #viral {_niche_en}"
        # Facebook / YouTube: solo los 3 del nicho
        hashtags_es = _niche_es
        hashtags_en = _niche_en
        # Facebook: nicho + geo-targeting fijo para posicionar en México y
        # público latino de Estados Unidos (la audiencia que Vinkly Nicaragua
        # busca alcanzar con estos reels).
        _region_tags = "#Mexico #LatinosEnUSA #Hispanos"
        hashtags_fb_es = f"{_niche_es} {_region_tags}"
        hashtags_fb_en = f"{_niche_en} {_region_tags}"

        if lang == "es":
            prompt = f"""
Eres un estratega experto en redes sociales especializado en contenido viral en español para YouTube Shorts, TikTok y Facebook Reels en el mercado latinoamericano.

Tema del video: "{topic}"
Línea de apertura: "{hook}"
Línea de cierre: "{last}"

### TAREA:
Genera copy optimizado para cada plataforma en español latino.

### 1. TÍTULO YOUTUBE SHORTS:
- Longitud: estrictamente 40–70 caracteres incluyendo espacios y emojis.
- Formato: usa UNO de estos ganchos: Pregunta ("¿Sabías que...?"), Número ("3 datos..."), Intriga ("El secreto detrás de...").
- Coloca la palabra clave más importante en las primeras 6 palabras.
- Termina exactamente con: #Shorts
- Máximo 1 emoji relevante. SIN mayúsculas completas.

### 2. DESCRIPCIÓN DE YOUTUBE (2–3 oraciones):
- Amplía el tema con palabras clave en español. Incluye CTA. Termina con 3 hashtags (#Shorts + 2 específicos).

### 3. CAPTION DE TIKTOK:
- LÍNEA 1: gancho con la PALABRA CLAVE PRINCIPAL del tema (dato impactante o afirmación sorprendente).
- LÍNEA 2: 1 oración conversacional que amplía la curiosidad.
- LÍNEA 3: CTA — pregunta directa que invite a comentar (ej: "¿Lo sabías? Comenta abajo 👇").
- HASHTAGS: Usa EXACTAMENTE estos (ya optimizados para el nicho): {hashtags_tiktok_es}

### 4. CAPTION DE FACEBOOK REELS:
- LÍNEA 1: UNA sola oración — afirmación o dato impactante con la palabra clave principal del tema (sin preguntas, sin CTA, sin línea de contexto aparte). Todo el gancho va en esa única oración.
- LÍNEA 2: los hashtags, todos en una sola línea. Usa EXACTAMENTE estos (ya incluyen nicho + geo-targeting para México y la audiencia latina de Estados Unidos): {hashtags_fb_es}

### SALIDA (JSON estricto, sin markdown). Usa \\n para saltos de línea:
{{
  "youtube_title": "...",
  "youtube_description": "...",
  "tiktok_caption": "línea gancho\\n\\nlínea contexto\\n\\nCTA\\n\\n#tag1 #tag2 #tag3",
  "facebook_caption": "una sola oración con el gancho\\n\\n#tag1 #tag2 #tag3 #Mexico #LatinosEnUSA #Hispanos"
}}
"""
        else:
            prompt = f"""
You are an expert social media strategist specializing in viral short-form video content in English.

Video topic: "{topic}"
Opening line: "{hook}"
Closing line: "{last}"

### TASK:
Generate platform-optimized copy for YouTube Shorts, TikTok, and Facebook Reels.

### 1. YOUTUBE SHORTS TITLE:
- Length: strictly 40–70 characters including spaces and emojis.
- Format: use ONE of these hooks: Question ("Did you know...?"), Number ("3 facts about..."), Intrigue ("The secret behind...").
- Place the most important keyword in the FIRST 6 words.
- End with exactly: #Shorts
- 1 relevant emoji maximum. NO all-caps spam words.

### 2. YOUTUBE DESCRIPTION (2–3 sentences):
- Expand on the topic with relevant keywords. Include a CTA. End with 3 hashtags (#Shorts + 2 topic-specific).

### 3. TIKTOK CAPTION:
- LINE 1: hook containing the PRIMARY KEYWORD (shocking fact or surprising statement).
- LINE 2: 1 short conversational sentence expanding curiosity.
- LINE 3: CTA — direct question inviting engagement (e.g. "Did you know this? Comment below 👇").
- HASHTAGS: Use EXACTLY these (already optimized for the niche): {hashtags_tiktok_en}

### 4. FACEBOOK REELS CAPTION:
- LINE 1: ONE single sentence — the strongest hook, a shocking statement with the main keyword (no questions, no CTA, no separate context line). The entire hook lives in that one sentence.
- LINE 2: the hashtags, all on one line. Use EXACTLY these (already include niche + geo-targeting for Mexico and the US Latino audience): {hashtags_fb_en}

### OUTPUT (strict JSON, no markdown). Use \\n for line breaks:
{{
  "youtube_title": "...",
  "youtube_description": "...",
  "tiktok_caption": "hook line\\n\\ncontext line\\n\\nCTA\\n\\n#tag1 #tag2 #tag3",
  "facebook_caption": "one single hook sentence\\n\\n#tag1 #tag2 #tag3 #Mexico #LatinosEnUSA #Hispanos"
}}
"""

        raw   = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()
        try:
            import json as _j
            data = _j.loads(clean)
            return {
                "youtube_title":       data.get("youtube_title", ""),
                "youtube_description": data.get("youtube_description", ""),
                "tiktok_caption":      data.get("tiktok_caption", ""),
                "facebook_caption":    data.get("facebook_caption", ""),
            }
        except Exception:
            print("⚠️ Could not parse copy JSON — returning raw.")
            return {
                "youtube_title": topic,
                "youtube_description": clean,
                "tiktok_caption": clean,
                "facebook_caption": clean,
            }

    # ------------------------------------------------------------------
    # HOOK CARD
    # ------------------------------------------------------------------

    def generate_hook_text(self, topic: str, script: list, lang: str = "es", mode: str = "auto") -> str:
        """Generate a short, punchy hook card text (max ~50 chars) for the video opener.

        The hook must create instant curiosity / FOMO so the viewer doesn't swipe away.
        Returns a plain string — no quotes, no punctuation at the end.
        Falls back to first sentence of first scene on any error.
        """
        first_line = script[0].get("text", "") if script else ""
        fallback   = first_line.split(".")[0].strip()[:50]

        if lang == "es":
            prompt = f"""Eres experto en crear ganchos virales para YouTube Shorts y TikTok en español latino.

TEMA DEL VIDEO: "{topic}"
PRIMERA LÍNEA DEL GUION: "{first_line[:120]}"
MODO: {mode}

TAREA: Escribe UN SOLO texto de enganche (hook card) que aparecerá en grande al inicio del video.

REGLAS ESTRICTAS:
- Máximo 45 caracteres (se mostrará en pantalla en letra grande)
- Debe generar curiosidad o miedo a perderse algo (FOMO)
- Sin signos de interrogación al final (usa puntos suspensivos si es pregunta)
- Sin comillas, sin emojis
- Solo el texto, nada más
- Ejemplos del tono correcto:
  "Lo que nadie se atrevió a decir"
  "Esto cambió todo para siempre"
  "El secreto que ocultaron por años"
  "Lo descubrieron y lo silenciaron"
  "Nunca te contaron esto"

RESPONDE SOLO CON EL TEXTO DEL HOOK, SIN EXPLICACIONES:"""
        else:
            prompt = f"""You are an expert at creating viral hooks for YouTube Shorts and TikTok.

VIDEO TOPIC: "{topic}"
FIRST SCRIPT LINE: "{first_line[:120]}"
MODE: {mode}

TASK: Write ONE hook card text that will appear large at the start of the video.

STRICT RULES:
- Maximum 45 characters (it will be displayed in large text on screen)
- Must create curiosity or FOMO
- No question marks at the end (use ellipsis if it's a question)
- No quotes, no emojis
- Only the text, nothing else
- Examples of the right tone:
  "What they never told you"
  "This changed everything forever"
  "The secret hidden for years"
  "They found out and silenced it"

RESPOND WITH ONLY THE HOOK TEXT, NO EXPLANATIONS:"""

        try:
            raw = self._generate(prompt).strip()
            # Strip surrounding quotes if the LLM added them
            raw = raw.strip('"\'').strip()
            return raw[:50] if raw else fallback
        except Exception as e:
            print(f"⚠️ Hook card generation failed: {e}")
            return fallback

    # ------------------------------------------------------------------
    # MININOVELA METHODS
    # ------------------------------------------------------------------

    def generate_miniseries_bible(self, theme: str, lang: str = "es") -> dict:
        """Generate the creative bible (story foundation) for a mini-series."""
        if lang == "es":
            prompt = f"""Eres el director creativo de una mini serie viral para YouTube Shorts en español latino.

TEMA DEL USUARIO: "{theme}"

TAREA: Crea la biblia creativa completa para una mini historia de 8 escenas (~60-90 segundos).

REGLAS:
- El tema del usuario es el punto de partida. Desarrolla una historia original pero fiel al tema.
- 2-3 personajes máximo (más es confuso en 60 segundos).
- Escenario concreto y específico (no vago).
- Descripción física de personajes OPTIMIZADA para prompts de video IA (en inglés, detallada).
- Arco narrativo completo: setup → conflicto → clímax → resolución.
- Tono que maximice retención: drama, emoción fuerte, suspenso natural.
- Idioma de la narración: español latino neutro. Evita palabras con ñ — usa alternativas naturales.
- Las descripciones físicas de personajes DEBEN estar en INGLÉS (para los prompts de video IA).

FORMATO DE SALIDA (JSON estricto, sin markdown):
{{
  "title": "título impactante en español",
  "genre": "thriller | drama | romance | comedia | suspenso | horror",
  "setting": "descripción concreta del lugar y época (ej: mansión colonial, Santo Domingo, noche de tormenta, 2024)",
  "setting_visual": "english visual description of the setting for AI video prompts",
  "characters": [
    {{
      "name": "Nombre del personaje",
      "role": "protagonist | antagonist | supporting",
      "age": 35,
      "physical": "detailed english description for AI video: Hispanic female, 35 years old, long dark curly hair, red dress, intense brown eyes, elegant posture",
      "personality": "descripción breve en español de su personalidad y motivación"
    }}
  ],
  "arc": {{
    "setup": "situación inicial en 1-2 oraciones",
    "conflict": "el conflicto principal en 1-2 oraciones",
    "climax": "el momento de máxima tensión en 1-2 oraciones",
    "resolution": "cómo termina en 1-2 oraciones"
  }},
  "narrator_style": "tercera persona omnisciente, tono dramático y urgente"
}}"""
        else:
            prompt = f"""You are the creative director of a viral mini-series for YouTube Shorts.

USER THEME: "{theme}"

TASK: Create the complete creative bible for an 8-scene mini-story (~60-90 seconds).

RULES:
- The user's theme is the starting point. Develop an original story faithful to the theme.
- Maximum 2-3 characters (more is confusing in 60 seconds).
- Concrete and specific setting (not vague).
- Character physical descriptions OPTIMIZED for AI video prompts (in English, detailed).
- Complete narrative arc: setup → conflict → climax → resolution.
- Tone that maximizes retention: drama, natural suspense, strong emotion.
- Narration language: English.
- Character physical descriptions MUST be in ENGLISH (for AI video prompts).

OUTPUT FORMAT (strict JSON, no markdown):
{{
  "title": "impactful title in English",
  "genre": "thriller | drama | romance | comedy | suspense | horror",
  "setting": "concrete description of place and era (e.g., colonial mansion, New York, stormy night, 2024)",
  "setting_visual": "english visual description of the setting for AI video prompts",
  "characters": [
    {{
      "name": "Character Name",
      "role": "protagonist | antagonist | supporting",
      "age": 35,
      "physical": "detailed english description for AI video: Hispanic female, 35 years old, long dark curly hair, red dress, intense brown eyes, elegant posture",
      "personality": "brief description of their personality and motivation"
    }}
  ],
  "arc": {{
    "setup": "initial situation in 1-2 sentences",
    "conflict": "the main conflict in 1-2 sentences",
    "climax": "the moment of maximum tension in 1-2 sentences",
    "resolution": "how it ends in 1-2 sentences"
  }},
  "narrator_style": "third person omniscient, dramatic and urgent tone"
}}"""

        raw = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()
        try:
            import json as _j
            result = _j.loads(clean)
        except Exception:
            result = {
                "title": theme,
                "genre": "drama",
                "setting": "",
                "setting_visual": "",
                "characters": [],
                "arc": {
                    "setup": "",
                    "conflict": "",
                    "climax": "",
                    "resolution": "",
                },
                "narrator_style": "tercera persona omnisciente, tono dramático y urgente",
            }

        print(f"🎬 [Mininovela] Biblia creativa generada: {result.get('title', 'Sin título')}")
        return result

    def generate_miniseries_script(self, bible: dict, lang: str = "es", num_scenes: int = 8) -> list:
        """Generate the scene-by-scene script for the mini-series using its bible."""
        title = bible.get("title", "")
        genre = bible.get("genre", "")
        setting = bible.get("setting", "")
        setting_visual = bible.get("setting_visual", setting)
        arc = bible.get("arc", {})

        char_list = "\n".join(
            f"- {c['name']} ({c['role']}): {c['physical']} | Personalidad: {c['personality']}"
            for c in bible.get("characters", [])
        )

        if lang == "es":
            prompt = f"""Eres el guionista de la mini serie "{title}" ({genre}).

BIBLIA DE LA HISTORIA:
Escenario: {setting}
Descripción visual del escenario: {setting_visual}

PERSONAJES:
{char_list}

ARCO NARRATIVO:
- Setup: {arc.get('setup', '')}
- Conflicto: {arc.get('conflict', '')}
- Clímax: {arc.get('climax', '')}
- Resolución: {arc.get('resolution', '')}

TAREA: Escribe exactamente {num_scenes} escenas para YouTube Shorts.

REGLAS DE NARRACIÓN:
- Idioma: español latino neutro, 3ra persona. Evita palabras con ñ — usa alternativas naturales.
- Cada "text" es la NARRACIÓN en voz en off (lo que dice el narrador). Máximo 15 palabras.
- Sin diálogos en el "text" — solo narración descriptiva y dramática.
- Cada escena: una sola idea poderosa. Sin relleno.
- Flujo: Escena 1 (gancho explosivo) → Escenas 2-3 (setup y personajes) → Escenas 4-6 (conflicto escalando) → Escena 7 (clímax) → Escena 8 (resolución o desenlace impactante).

REGLAS DE VIDEO (MUY IMPORTANTE para IA):
- "visual_1": término de búsqueda EN INGLÉS (Pexels fallback), 3-4 palabras.
- "visual_2": segundo término EN INGLÉS, 3-4 palabras.
- "video_prompt": prompt COMPLETO en INGLÉS para generación de video IA.
  FORMATO del video_prompt: "[Acción visual]. [Personajes presentes con descripción física completa si hay]. [Escenario visual]. [Atmósfera/iluminación]. Cinematic, 9:16 vertical, no text overlays."
  CRÍTICO: Si hay personajes en la escena, SIEMPRE incluye su descripción física completa del personaje de la biblia.
- "characters_in_scene": array con nombres de personajes presentes (puede ser vacío []).
- "mood": energetic | dramatic | mysterious | calm | inspiring | professional | exciting

ESTRUCTURA OBLIGATORIA:
- Escena 1 — GANCHO: La imagen o situación más impactante de la historia. Hook visual puro.
- Escenas 2-3 — INTRODUCCIÓN: Presenta el escenario y los personajes clave.
- Escenas 4-6 — DESARROLLO Y CONFLICTO: La situación escala, tensión crece.
- Escena 7 — CLÍMAX: El momento de máxima tensión.
- Escena 8 — RESOLUCIÓN / GANCHO FINAL: Cierre impactante o pregunta que enganche.

FORMATO DE SALIDA (JSON estricto, sin markdown, exactamente {num_scenes} elementos):
[
  {{
    "id": 1,
    "text": "narración aquí, máximo 15 palabras",
    "visual_1": "english pexels search term",
    "visual_2": "english pexels search term 2",
    "video_prompt": "Complete english AI video generation prompt with character descriptions if present. Setting description. Atmosphere. Cinematic, 9:16 vertical, no text.",
    "characters_in_scene": ["Nombre1"],
    "mood": "dramatic"
  }}
]"""
        else:
            prompt = f"""You are the screenwriter for the mini-series "{title}" ({genre}).

STORY BIBLE:
Setting: {setting}
Visual setting description: {setting_visual}

CHARACTERS:
{char_list}

NARRATIVE ARC:
- Setup: {arc.get('setup', '')}
- Conflict: {arc.get('conflict', '')}
- Climax: {arc.get('climax', '')}
- Resolution: {arc.get('resolution', '')}

TASK: Write exactly {num_scenes} scenes for YouTube Shorts.

NARRATION RULES:
- Language: English, third person.
- Each "text" is the VOICE-OVER NARRATION (what the narrator says). Maximum 15 words.
- No dialogue in "text" — only descriptive and dramatic narration.
- Each scene: one powerful idea. No filler.
- Flow: Scene 1 (explosive hook) → Scenes 2-3 (setup and characters) → Scenes 4-6 (escalating conflict) → Scene 7 (climax) → Scene 8 (resolution or powerful ending).

VIDEO RULES (VERY IMPORTANT for AI):
- "visual_1": English search term (Pexels fallback), 3-4 words.
- "visual_2": second English term, 3-4 words.
- "video_prompt": COMPLETE English prompt for AI video generation.
  FORMAT: "[Visual action]. [Characters present with full physical description if any]. [Visual setting]. [Atmosphere/lighting]. Cinematic, 9:16 vertical, no text overlays."
  CRITICAL: If characters are in the scene, ALWAYS include their full physical description from the bible.
- "characters_in_scene": array with names of characters present (can be empty []).
- "mood": energetic | dramatic | mysterious | calm | inspiring | professional | exciting

MANDATORY STRUCTURE:
- Scene 1 — HOOK: The most impactful image or situation of the story. Pure visual hook.
- Scenes 2-3 — INTRODUCTION: Introduce the setting and key characters.
- Scenes 4-6 — DEVELOPMENT & CONFLICT: The situation escalates, tension grows.
- Scene 7 — CLIMAX: The moment of maximum tension.
- Scene 8 — RESOLUTION / FINAL HOOK: Impactful close or engaging question.

OUTPUT FORMAT (strict JSON, no markdown, exactly {num_scenes} elements):
[
  {{
    "id": 1,
    "text": "narration here, maximum 15 words",
    "visual_1": "english pexels search term",
    "visual_2": "english pexels search term 2",
    "video_prompt": "Complete english AI video generation prompt with character descriptions if present. Setting description. Atmosphere. Cinematic, 9:16 vertical, no text.",
    "characters_in_scene": ["Character1"],
    "mood": "dramatic"
  }}
]"""

        raw = self._generate(prompt)
        clean = raw.replace('```json', '').replace('```', '').strip()
        try:
            import json as _j
            scenes = _j.loads(clean)
            if not isinstance(scenes, list):
                raise ValueError("Response is not a JSON array")
        except Exception:
            # Fallback: build minimal scenes from the arc
            arc_texts = [
                arc.get("setup", ""),
                arc.get("conflict", ""),
                arc.get("climax", ""),
                arc.get("resolution", ""),
            ]
            scenes = []
            for i in range(num_scenes):
                arc_text = arc_texts[min(i, len(arc_texts) - 1)] if arc_texts else ""
                scenes.append({
                    "id": i + 1,
                    "text": arc_text if arc_text else f"Scene {i + 1}",
                    "visual_1": "cinematic drama",
                    "visual_2": "dramatic scene",
                    "video_prompt": f"{setting_visual}. Cinematic, 9:16 vertical, no text.",
                    "characters_in_scene": [],
                    "mood": "dramatic",
                })

        # Sanitize text, fill missing fields, cap at num_scenes
        default_mood = "dramatic"
        sanitized = []
        for scene in scenes[:num_scenes]:
            if not isinstance(scene, dict):
                continue
            scene["text"] = self._sanitize(scene.get("text", ""))
            scene.setdefault("id", len(sanitized) + 1)
            scene.setdefault("visual_1", "cinematic drama")
            scene.setdefault("visual_2", "dramatic scene")
            scene.setdefault("video_prompt", f"{setting_visual}. Cinematic, 9:16 vertical, no text.")
            scene.setdefault("characters_in_scene", [])
            scene.setdefault("mood", default_mood)
            sanitized.append(scene)

        print(f"✅ [Mininovela] {len(sanitized)} escenas generadas para \"{title}\"")
        return sanitized


if __name__ == "__main__":
    brain = ContentBrain()
    topic = brain.get_trending_topic(lang="es")
    script = brain.generate_script(topic, lang="es")
    with open("script.json", "w", encoding="utf-8") as f:
        json.dump(script, f, indent=4, ensure_ascii=False)
        print("✅ Script saved to script.json")
