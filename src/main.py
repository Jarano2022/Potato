import threading
import subprocess
import os
import sys

# Añadimos el directorio raíz al path para que los imports funcionen correctamente
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import customtkinter as ctk
from src.gui.main_window import PotatoGUI
from src.core.listener import conectar_microfono_con_potato

# Archivo local de música - RUTA ACTUALIZADA
ARCHIVO_MP3 = os.path.abspath("assets/audio/audio_back_in_black.mp3")

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
    # Creamos la interfaz gráfica en negro absoluto
    ventana = PotatoGUI()

    # ⌨️ ASIGNACIÓN DE LA TECLA:
    # Vinculamos la barra espaciadora (<space>) para que detenga la música
    ventana.bind("<space>", detener_musica)

    # Creamos el hilo para el micrófono y Gemini
    hilo_escucha = threading.Thread(
        target=conectar_microfono_con_potato, 
        args=(ventana,), 
        daemon=True
    )
    hilo_escucha.start()

    # Lanzamos la interfaz de la esfera
    ventana.mainloop()

if __name__ == "__main__":
    iniciar_sistema()
