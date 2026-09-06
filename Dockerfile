# AutoShorts AI — una sola imagen que sirve para los dos contenedores del stack:
# la interfaz de Streamlit y el worker que genera videos solo.
#
# Python 3.11 fijo a proposito. En Streamlit Cloud el proyecto acabo corriendo
# sobre Python 3.14 sin pedirlo y eso ya provoco fallos; aqui la version la
# decidimos nosotros.
FROM python:3.11-slim

# ffmpeg          -> composer.py y audio.py llaman al binario, no a una libreria.
# fonts-dejavu    -> OBLIGATORIO. Sin una fuente real instalada, el filtro
#                    drawtext de ffmpeg aborta con "Cannot find a valid font"
#                    y el render muere justo al quemar los subtitulos.
# tzdata          -> para que la hora programada del worker sea la tuya, no UTC.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ffmpeg \
      fonts-dejavu-core \
      tzdata \
      ca-certificates \
 && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Las dependencias van antes que el codigo para que Docker reutilice esta capa
# y un cambio en un .py no obligue a reinstalar todo.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Carpetas de trabajo del pipeline. Se crean por si el volumen arranca vacio.
RUN mkdir -p assets/final assets/temp assets/audio_clips assets/video_clips \
             assets/salida /datos

EXPOSE 8501

# Por defecto la imagen levanta la interfaz. El worker sobreescribe el command
# en docker-compose.yml.
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
