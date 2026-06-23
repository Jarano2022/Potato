# Usar imagen base oficial de Python
FROM python:3.11-slim

# Evitar que Python escriba archivos .pyc y forzar salida de logs sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema para compilar PyAudio, FFmpeg y Curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    portaudio19-dev \
    python3-dev \
    build-essential \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar Tailscale CLI (opcional por si se quiere autenticar dentro)
RUN curl -fsSL https://tailscale.com/install.sh | sh

# Crear y establecer el directorio de trabajo
WORKDIR /app

# Copiar archivos de requerimientos primero para cachear capas Docker
COPY requirements.txt .
COPY servers/audio_server/requirements.txt ./servers/audio_server/requirements.txt
COPY servers/html_server/requirements.txt ./servers/html_server/requirements.txt

# Instalar dependencias de Python globales dentro del contenedor
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r servers/audio_server/requirements.txt \
    && pip install --no-cache-dir -r servers/html_server/requirements.txt

# Copiar todo el código de la aplicación
COPY . .

# Exponer los puertos por defecto para audio (8000) e interfaz web HTML (8082)
EXPOSE 8000
EXPOSE 8082

# Iniciar la suite de servidores de Potato usando el supervisor supervisado
CMD ["python", "run_servers.py"]
