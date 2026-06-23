import subprocess
import logging
import speech_recognition as sr
import threading
import os

# Asegurar que la carpeta de logs existe
os.makedirs("logs", exist_ok=True)

# Configuración de logs
logging.basicConfig(
    filename="logs/potato_actividad.log", 
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

error_logger = logging.getLogger("error_logger")
error_handler = logging.FileHandler("logs/potato_errores.log")
error_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
error_logger.addHandler(error_handler)

# Variable global para acceder a la GUI desde las herramientas de la IA
ventana_global = None

def set_ventana(ventana):
    global ventana_global
    ventana_global = ventana

def escuchar_confirmacion_voz() -> str:
    """
    Activa el micrófono rápidamente para capturar la respuesta del usuario (sí/no).
    """
    reconocedor = sr.Recognizer()
    with sr.Microphone() as origen:
        if ventana_global:
            ventana_global.log_consola("🎤 ESCUCHANDO VOZ...")
        reconocedor.adjust_for_ambient_noise(origen, duration=0.5)
        try:
            audio = reconocedor.listen(origen, timeout=3, phrase_time_limit=3)
            texto = reconocedor.recognize_google(audio, language="es-ES")
            return texto.lower()
        except Exception:
            return ""

def evaluar_y_ejecutar(comando: str, descripcion: str) -> str:
    """
    Ejecuta el comando y devuelve el resultado detallado para que la IA lo analice.
    """
    if ventana_global:
        ventana_global.log_consola(f"\n⚠️ SOLICITUD DE EJECUCIÓN:")
        ventana_global.log_consola(f"📋 Acción: {descripcion}")
        ventana_global.log_consola(f"💻 Comando: {comando}")
        ventana_global.log_consola("🤔 ¿Confirmas la ejecución? (Dí 'sí' o escríbelo en el chat)")
        ventana_global.cambiar_estado("🤔 ESPERANDO CONFIRMACIÓN...")

    # Iniciamos escucha por voz
    respuesta_voz = escuchar_confirmacion_voz()

    confirmado = False
    if "sí" in respuesta_voz or "si" in respuesta_voz or "procede" in respuesta_voz:
        confirmado = True
    elif "no" in respuesta_voz or "cancel" in respuesta_voz:
        confirmado = False
    else:
        # Si la voz no captó nada claro, esperamos al chat
        if ventana_global:
            ventana_global.log_consola("⏳ Esperando respuesta por chat...")
            respuesta_chat = ventana_global.esperar_confirmacion_chat(timeout=20)
            if "sí" in respuesta_chat or "si" in respuesta_chat or "ok" in respuesta_chat or "procede" in respuesta_chat:
                confirmado = True
            elif "no" in respuesta_chat or "cancel" in respuesta_chat:
                confirmado = False
            else:
                return "NO SE RECIBIÓ CONFIRMACIÓN. OPERACIÓN ABORTADA."

    if not confirmado:
        if ventana_global:
            ventana_global.log_consola("❌ ACCIÓN ABORTADA POR EL USUARIO.")
        return "OPERACIÓN CANCELADA POR EL USUARIO."

    try:
        if ventana_global:
            ventana_global.log_consola(f"🚀 Ejecutando: {comando}...")
            ventana_global.cambiar_estado("⚡ EJECUTANDO...")

        logging.info(f"Ejecutando: {comando} ({descripcion})")
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=60)

        output = f"STDOUT: {resultado.stdout}\nSTDERR: {resultado.stderr}"

        if ventana_global:
            if resultado.stdout:
                ventana_global.log_consola(f"✅ SALIDA:\n{resultado.stdout}")
            if resultado.stderr:
                ventana_global.log_consola(f"⚠️ ERROR/AVISO:\n{resultado.stderr}")

        if resultado.returncode == 0:
            logging.info(f"Éxito en '{comando}':\n{output}")
            return f"ÉXITO. Salida del sistema:\n{resultado.stdout}"
        else:
            logging.warning(f"Error (Código {resultado.returncode}) en '{comando}':\n{output}")
            return f"ERROR (Código {resultado.returncode}). Detalles:\n{resultado.stderr if resultado.stderr else resultado.stdout}"

    except Exception as e:
        error_msg = f"FALLO CRÍTICO al ejecutar '{comando}': {str(e)}"
        error_logger.error(error_msg)
        if ventana_global:
            ventana_global.log_consola(f"🔥 {error_msg}")
        return error_msg

def ejecutar_comando_sistema(comando: str, descripcion: str) -> str:
    """
    Ejecuta un comando nativo en el sistema.

    Args:
        comando: El comando exacto de terminal.
        descripcion: Breve explicación de la acción para el usuario.

    Returns:
        La salida real del comando (stdout o stderr).
    """
    return evaluar_y_ejecutar(comando, descripcion)
