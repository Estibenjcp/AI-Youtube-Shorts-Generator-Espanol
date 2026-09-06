# Desplegar AutoShorts AI en tu servidor Ubuntu con Portainer

Dos contenedores desde una sola imagen:

| Contenedor | Para que sirve |
|---|---|
| `autoshorts-app` | La interfaz de siempre, en `http://TU_SERVIDOR:8501`. Para trabajar a mano, probar voces y dejar listo el preset. |
| `autoshorts-worker` | El generador automatico. Duerme hasta la hora fijada, hace la tanda del dia y vuelve a dormir. |

---

## 1. Preparar las carpetas en el servidor

```bash
sudo mkdir -p /srv/autoshorts/salida
```

Ahi caeran los `.mp4` terminados, cada uno con un `.json` al lado que trae el
titulo, la descripcion y los hashtags que genero el pipeline.

## 2. Crear el stack en Portainer

**Stacks → Add stack → Repository**, apuntando a tu repo de GitHub
(`AI-Youtube-Shorts-Generator-Espanol`, rama `Main`), fichero
`docker-compose.yml`.

Asi cada vez que subas cambios basta con darle a **Update the stack** y se
reconstruye con el codigo nuevo.

## 3. Variables de entorno del stack

En la misma pantalla, seccion **Environment variables**:

| Variable | Que es | Obligatoria |
|---|---|---|
| `AI_API_KEY` | Clave de Gemini u OpenRouter (escribe los guiones) | Si |
| `AI_PROVIDER` | `gemini` u `openrouter` | Si |
| `AI_MODEL` | Modelo de IA | No |
| `PEXELS_API_KEY` | Banco de video | Si |
| `FISH_API_KEY` | Fish Audio (la voz) | Si |
| `FISH_VOICE_ID` | Id de la voz. Locutor K: `3f45a7fd7a614655a61eb7027b955783` | Si |
| `APP_PASSWORD` | Contrasena de la interfaz | Si |
| `TZ` | `America/Bogota` | No |
| `SALIDA_DIR` | `/srv/autoshorts/salida` | No |
| `WORKER_HORA` | Hora de la tanda, `HH:MM` | No (06:00) |
| `WORKER_VIDEOS_TANDA` | Cuantos videos por tanda | No (3) |
| `TELEGRAM_BOT_TOKEN` | Para el aviso al terminar | No |
| `TELEGRAM_CHAT_ID` | Tu chat de Telegram | No |

**Ninguna clave va dentro de la imagen ni del preset.** Todas se inyectan aqui.

`APP_PASSWORD`: pon una de verdad. La que hay en el `.streamlit/secrets.toml`
local es `demo` y no sirve para algo accesible desde la red.

## 4. Dejar el preset y los temas

El worker necesita dos ficheros en el volumen `datos`. Con el stack ya
levantado:

```bash
docker cp preset.ejemplo.json autoshorts-worker:/datos/preset.json
docker cp temas.ejemplo.txt   autoshorts-worker:/datos/temas.txt
```

- **`preset.json`** — la configuracion del video: modo, voz, numero de escenas,
  duracion, efectos. Son las mismas claves que usa la interfaz, asi que el video
  automatico sale identico al que harias a mano. Si no existe, el worker se
  niega a arrancar en vez de inventarse ajustes.
- **`temas.txt`** — un tema por linea. Las lineas con `#` son notas y se ignoran.
  Un tema que ya se uso no se repite; uno que fallo se reintenta manana.

### Como convierte un tema en video

El preset viene en modo **Guion**, que es el que usas tu. Ese modo no acepta un
tema suelto: espera un guion escrito. Asi que el worker lo hace en dos pasos.

1. **Borrador.** Con el tema de la lista escribe un esqueleto en tu formato
   (`Titulo:` / `Categoria:` / vinietas), una vinieta por escena.
2. **Voz.** Ese borrador entra en el modo Guion por el camino *autorado*, que es
   el que respeta las ideas una a una y les pone encima la voz de Andrea, el
   tono Conductual y el objetivo Confianza.

La division es a proposito: el paso 1 decide **que** se dice, el paso 2 decide
**como suena**. Si el borrador sale mal formado, el worker lo tira y no gasta
render.

El numero de vinietas se calcula igual que lo hace la app, con tope de 12, para
que la lista de temas no acabe generando 15 escenas y se coma la memoria.

## 5. Probar antes de esperar a mañana

```bash
docker exec -it autoshorts-worker python worker.py --uno "Por que te cuesta empezar"
```

Genera un solo video y lo deja en `/srv/autoshorts/salida`. Para una tanda
completa ya mismo:

```bash
docker exec -it autoshorts-worker python worker.py --ahora
```

Y para ver que esta haciendo:

```bash
docker logs -f autoshorts-worker
```

---

## Memoria: por que hay topes

Tu servidor tiene 8 GB y ya va al 61%, o sea unos 3 GB libres. El stack reparte:
1,5 GB para la interfaz y 2 GB para el worker. Ese tope existe para que un
render pesado **no se lleve por delante los otros servicios de la maquina**.

El worker nunca hace dos videos a la vez: los encadena uno tras otro.

Si un video con muchas escenas muere sin explicacion, es el tope. Dos salidas:
bajar el numero de escenas en el preset (9 es lo seguro), o aplicar el arreglo
de trocear la union de clips en `composer.py`.

## Ventaja que igual no esperabas

Tu red local bloquea `videos.pexels.com` — por eso ningun render completo te ha
funcionado. Tu servidor casi seguro no tiene ese bloqueo. Compruebalo:

```bash
docker exec -it autoshorts-worker python -c "import requests; print(requests.head('https://videos.pexels.com', timeout=10).status_code)"
```

Si responde un numero, ya puedes generar videos completos.
