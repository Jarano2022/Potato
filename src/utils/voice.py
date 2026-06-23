import requests
import os
import subprocess
import wave
import pyaudio
import numpy as np
from dotenv import load_dotenv

load_dotenv()

SERVER_IP = os.getenv("POTATO_VOICE_SERVER_IP")
POTATO_AUDIO_PORT = os.getenv("POTATO_AUDIO_PORT", "8000")
URL_VOZ = f"http://{SERVER_IP}:{POTATO_AUDIO_PORT}/speak"

def reproducir_y_analizar(archivo_wav, ventana=None):
    """
    Reproduce un archivo WAV usando PyAudio y calcula el volumen
    y frecuencias en tiempo real para actualizar la interfaz.
    """
    if not os.path.exists(archivo_wav):
        return
        
    wf = wave.open(archivo_wav, 'rb')
    p = pyaudio.PyAudio()
    
    # Abrir stream de salida
    stream = p.open(
        format=p.get_format_from_width(wf.getsampwidth()),
        channels=wf.getnchannels(),
        rate=wf.getframerate(),
        output=True
    )
    
    chunk_size = 1024
    data = wf.readframes(chunk_size)
    
    while data:
        # Escribir audio al dispositivo
        stream.write(data)
        
        if ventana:
            try:
                # Analizar datos del fragmento
                if wf.getsampwidth() == 2:
                    audio_data = np.frombuffer(data, dtype=np.int16)
                elif wf.getsampwidth() == 1:
                    audio_data = np.frombuffer(data, dtype=np.int8)
                else:
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    
                if len(audio_data) > 0:
                    # Calcular volumen (RMS)
                    rms = np.sqrt(np.mean(audio_data.astype(np.float32)**2))
                    max_val = 32767.0 if wf.getsampwidth() == 2 else 127.0
                    vol_normalizado = rms / max_val
                    # Hacerlo un poco más sensible y reactivo para la UI
                    vol_normalizado = min(1.0, vol_normalizado * 2.8)
                    
                    # FFT rápido para obtener bandas de frecuencia (graves, medios, agudos)
                    fft_data = np.abs(np.fft.rfft(audio_data))
                    num_freqs = len(fft_data)
                    if num_freqs > 3:
                        bass = float(np.mean(fft_data[:num_freqs//6]))
                        mid = float(np.mean(fft_data[num_freqs//6:num_freqs//2]))
                        treble = float(np.mean(fft_data[num_freqs//2:]))
                    else:
                        bass, mid, treble = 0.0, 0.0, 0.0
                        
                    # Escalar frecuencias para la animación
                    bass_norm = min(1.0, bass / (max_val * 0.1)) if max_val > 0 else 0.0
                    mid_norm = min(1.0, mid / (max_val * 0.05)) if max_val > 0 else 0.0
                    treble_norm = min(1.0, treble / (max_val * 0.02)) if max_val > 0 else 0.0
                    
                    # Enviar a la interfaz
                    ventana.update_audio_metrics(vol_normalizado, (bass_norm, mid_norm, treble_norm))
            except Exception:
                pass
                
        data = wf.readframes(chunk_size)
        
    # Restablecer métricas al finalizar la reproducción
    if ventana:
        ventana.update_audio_metrics(0.0, (0.0, 0.0, 0.0))
        
    stream.stop_stream()
    stream.close()
    p.terminate()

def hablar(texto, ventana=None):
    if not texto:
        return

    try:
        payload = {"text": texto}
        # Hacemos la petición activando stream=True para recibir archivos binarios
        response = requests.post(URL_VOZ, json=payload, timeout=30, stream=True)
        
        if response.status_code == 200:
            print(f"[Voz remota]: {texto}")
            
            # 1. Guardamos el archivo de audio físico temporal en MP3
            ruta_mp3 = "/tmp/respuesta_potato.mp3"
            ruta_wav = "/tmp/respuesta_potato.wav"
            
            with open(ruta_mp3, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            
            # 2. Convertimos el MP3 a WAV con FFMPEG para analizarlo en Python
            subprocess.run([
                "ffmpeg", "-y", "-i", ruta_mp3, 
                "-acodec", "pcm_s16le", "-ar", "22050", 
                ruta_wav
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # 3. Reproducir el archivo y actualizar la GUI
            reproducir_y_analizar(ruta_wav, ventana)
            
        else:
            print(f"[Error Servidor Voz]: {response.status_code} - {response.text}")
            
    except Exception as e:
        import traceback
        print(f"\n[Error de conexión con servidor de voz]: {e}")
        traceback.print_exc()
        print("Asegúrate de que el servidor en Ubuntu esté corriendo y la IP sea correcta.")