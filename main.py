import threading
import subprocess
import os
import customtkinter as ctk
from gui import JarvisGUI
from escucha import conectar_microfono_con_jarvis

# Archivo local de música
ARCHIVO_MP3 = "/home/jofre/Proyectos/jarvis/video-audio/audio_back_in_black.mp3"

# Variable global para controlar el proceso de la música
proceso_musica = None

def reproducir_musica_fondo():
    """Lanza el reproductor mpv e inicializa la variable del proceso"""
    global proceso_musica
    
    if os.path.exists(ARCHIVO_MP3):
        SEGUNDO_INICIO = "3" 
        print(f"🎵 Reproduciendo {ARCHIVO_MP3} desde el segundo {SEGUNDO_INICIO}...")
        try:
            # Usamos Popen en lugar de run para que no se quede bloqueado esperando a que termine la canción
            proceso_musica = subprocess.Popen([
                "mpv", 
                "--no-video", 
                f"--start={SEGUNDO_INICIO}", 
                ARCHIVO_MP3
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"[Error al reproducir música]: {e}")
    else:
        print(f"[Aviso]: No se encontró el archivo {ARCHIVO_MP3}. Continuando sin música.")

def detener_musica(event=None):
    """Detiene el proceso de mpv de forma segura si está corriendo"""
    global proceso_musica
    if proceso_musica is not None and proceso_musica.poll() is None:
        print("🛑 Deteniendo música de fondo...")
        proceso_musica.terminate() # Apaga mpv inmediatamente

def iniciar_sistema():
    # Lanzamos la música local en segundo plano
    #hilo_musica = threading.Thread(target=reproducir_musica_fondo, daemon=True)
    #hilo_musica.start()

    # Creamos la interfaz gráfica en negro absoluto
    ventana = JarvisGUI()

    # ⌨️ ASIGNACIÓN DE LA TECLA:
    # Vinculamos la barra espaciadora (<space>) para que detenga la música
    ventana.bind("<space>", detener_musica)
    # Si prefieres la tecla 'S', descomenta la línea de abajo y comenta la de la barra espaciadora:
    # ventana.bind("<s>", detener_musica)

    # Creamos el hilo para el micrófono y Gemini
    hilo_escucha = threading.Thread(
        target=conectar_microfono_con_jarvis, 
        args=(ventana,), 
        daemon=True
    )
    hilo_escucha.start()

    # Lanzamos la interfaz de la esfera
    ventana.mainloop()

if __name__ == "__main__":
    iniciar_sistema()
