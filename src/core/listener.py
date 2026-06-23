import os
from dotenv import load_dotenv
import speech_recognition as sr
from .brain import enviar_mensaje_a_potato
from src.utils.voice import hablar

# Cargar variables de entorno del archivo .env
load_dotenv()

def conectar_microfono_con_potato(ventana=None):
    """Bucle en segundo plano que conecta el micrófono con tu IA y tu voz"""
    reconocedor = sr.Recognizer()
    
    # Configurar el umbral de silencio para permitir pausas más largas al hablar
    pause_threshold = float(os.getenv("PAUSE_THRESHOLD", "2.0"))
    reconocedor.pause_threshold = pause_threshold
    
    # Configurar el límite de duración máxima de frase (None para sin límite)
    phrase_time_limit_env = os.getenv("PHRASE_TIME_LIMIT", "None")
    if phrase_time_limit_env.strip().lower() == "none" or phrase_time_limit_env.strip() == "":
        phrase_time_limit = None
    else:
        phrase_time_limit = float(phrase_time_limit_env)
    
    with sr.Microphone() as origen:
        if ventana:
            ventana.cambiar_estado("⚙️ CALIBRANDO AUDIO...")
        reconocedor.adjust_for_ambient_noise(origen, duration=1)
        
        while True:
            if ventana:
                ventana.cambiar_estado("🎙️ ESCUCHANDO...")
            
            try:
                # 1. Captura el audio del micrófono con la configuración ajustada
                audio = reconocedor.listen(origen, timeout=None, phrase_time_limit=phrase_time_limit)
                if ventana:
                    ventana.cambiar_estado("🧠 PROCESANDO...")
                
                # 2. Traduce el audio a texto
                texto_usuario = reconocedor.recognize_google(audio, language="es-ES")
                print(f"Usuario: {texto_usuario}")
                
                # 3. Envía el texto a tu sesión de Gemini en brain.py
                respuesta_texto = enviar_mensaje_a_potato(texto_usuario, ventana=ventana)
                print(f"Potato: {respuesta_texto}")
                
                # 4. Cambia el estado visual y habla usando voice.py
                if ventana:
                    ventana.cambiar_estado("🔊 RESPONDIENDO...")
                hablar(respuesta_texto, ventana=ventana)
                
            except sr.UnknownValueError:
                # Si detecta ruido pero no palabras, continúa el bucle
                pass
            except Exception as e:
                import traceback
                print(f"Error en el ciclo de Potato: {e}")
                traceback.print_exc()
