import requests
import os
import subprocess  # <--- IMPORTANTE: Necesitamos esto para reproducir el sonido
from dotenv import load_dotenv

load_dotenv()

SERVER_IP = os.getenv("JARVIS_VOICE_SERVER_IP")
URL_VOZ = f"http://{SERVER_IP}:8000/speak"

def hablar(texto):
    if not texto:
        return

    try:
        payload = {"text": texto}
        # Hacemos la petición activando stream=True para recibir archivos binarios grandes
        response = requests.post(URL_VOZ, json=payload, timeout=30, stream=True)
        
        if response.status_code == 200:
            print(f"[Voz remota]: {texto}")
            
            # 1. Guardamos el archivo de audio físico en la carpeta /tmp de Arch Linux
            ruta_audio = "/tmp/respuesta_jarvis.wav"
            with open(ruta_audio, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            
            # 2. ¡LA CLAVE! Reproducir el archivo usando un reproductor nativo de Arch Linux
            # Usamos 'mpv' porque es el más rápido, silencioso y no ensucia la terminal
            subprocess.run(["mpv", "--really-quiet", ruta_audio])
            
            # Si prefieres usar alsa-utils en vez de mpv, puedes descomentar la línea de abajo:
            # subprocess.run(["aplay", "-q", ruta_audio])
            
        else:
            print(f"[Error Servidor Voz]: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"\n[Error de conexión con servidor de voz]: {e}")
        print("Asegúrate de que el servidor en Ubuntu esté corriendo y la IP sea correcta.")