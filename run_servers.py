import subprocess
import time
import sys
import os

def run():
    print("=================================================")
    print("   POTATO DAEMON - INICIANDO SERVIDORES         ")
    print("=================================================")
    
    # Asegurar que el PYTHONPATH incluya la raíz del proyecto
    env = os.environ.copy()
    env["PYTHONPATH"] = env.get("PYTHONPATH", "") + ":" + os.path.abspath(os.path.dirname(__file__))

    print("🚀 1/2 Iniciando Servidor de Audio (FastAPI)...")
    audio_process = subprocess.Popen(
        [sys.executable, "servers/audio_server/main.py"],
        env=env
    )
    
    # Dar tiempo a que el servidor de audio levante y ocupe el puerto
    time.sleep(3)
    
    print("🚀 2/2 Iniciando Servidor HTML (FastAPI)...")
    html_process = subprocess.Popen(
        [sys.executable, "servers/html_server/main.py"],
        env=env
    )
    
    print("=================================================")
    print("   POTATO EN EJECUCIÓN (CONTRL+C PARA DETENER)   ")
    print("=================================================")

    try:
        while True:
            time.sleep(1)
            # Si alguno de los procesos muere, rompemos el ciclo
            if audio_process.poll() is not None:
                print("❌ ERROR: El Servidor de Audio se ha detenido inesperadamente.")
                break
            if html_process.poll() is not None:
                print("❌ ERROR: El Servidor HTML se ha detenido inesperadamente.")
                break
    except KeyboardInterrupt:
        print("\n🛑 Apagando servidores de Potato...")
    finally:
        audio_process.terminate()
        html_process.terminate()
        audio_process.wait()
        html_process.wait()
        print("👋 Servidores apagados correctamente. ¡Hasta luego!")

if __name__ == "__main__":
    run()
