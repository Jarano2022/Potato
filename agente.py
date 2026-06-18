import subprocess
import logging
import speech_recognition as sr

# Configuración de logs
# jarvis_actividad.log guardará el historial de comandos y sus salidas
logging.basicConfig(
    filename="jarvis_actividad.log", 
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# jarvis_errores.log para fallos críticos del script
error_logger = logging.getLogger("error_logger")
error_handler = logging.FileHandler("jarvis_errores.log")
error_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
error_logger.addHandler(error_handler)

def escuchar_confirmacion_voz() -> str:
    """
    Activa el micrófono rápidamente para capturar la respuesta del usuario (sí/no).
    """
    reconocedor = sr.Recognizer()
    with sr.Microphone() as origen:
        print("🎤 Escuchando confirmación (sí/no)...")
        reconocedor.adjust_for_ambient_noise(origen, duration=0.5)
        try:
            audio = reconocedor.listen(origen, timeout=4, phrase_time_limit=3)
            texto = reconocedor.recognize_google(audio, language="es-ES")
            return texto.lower()
        except Exception:
            return ""

def evaluar_y_ejecutar(comando: str, descripcion: str) -> str:
    """
    Ejecuta el comando y devuelve el resultado detallado para que la IA lo analice.
    """
    respuesta_usuario = escuchar_confirmacion_voz()
    
    if "no" in respuesta_usuario or "cancel" in respuesta_usuario:
        print("❌ Acción abortada por el usuario.")
        return "OPERACIÓN CANCELADA POR EL USUARIO."
        
    if "sí" in respuesta_usuario or "si" in respuesta_usuario or "procede" in respuesta_usuario:
        try:
            logging.info(f"Ejecutando: {comando} ({descripcion})")
            resultado = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=30)
            
            output = f"STDOUT: {resultado.stdout}\nSTDERR: {resultado.stderr}"
            
            if resultado.returncode == 0:
                logging.info(f"Éxito en '{comando}':\n{output}")
                return f"ÉXITO. Salida del sistema:\n{resultado.stdout}"
            else:
                logging.warning(f"Error (Código {resultado.returncode}) en '{comando}':\n{output}")
                return f"ERROR (Código {resultado.returncode}). Detalles:\n{resultado.stderr if resultado.stderr else resultado.stdout}"
                
        except Exception as e:
            error_msg = f"FALLO CRÍTICO al ejecutar '{comando}': {str(e)}"
            error_logger.error(error_msg)
            return error_msg

    return "NO SE RECIBIÓ CONFIRMACIÓN. OPERACIÓN ABORTADA."

def ejecutar_comando_sistema(comando: str, descripcion: str) -> str:
    """
    Ejecuta un comando nativo en Arch Linux.
    
    Args:
        comando: El comando exacto de terminal.
        descripcion: Breve explicación de la acción.
                     
    Returns:
        La salida real del comando (stdout o stderr) para que la IA pueda diagnosticar.
    """
    return evaluar_y_ejecutar(comando, descripcion)