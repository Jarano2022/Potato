import speech_recognition as sr
from ia import enviar_mensaje_a_jarvis # Importamos tu chat continuo
from voz import hablar      # Importamos tu función de voz con mpv

def conectar_microfono_con_jarvis(ventana):
    """Bucle en segundo plano que conecta el micrófono con tu IA y tu voz"""
    reconocedor = sr.Recognizer()
    
    with sr.Microphone() as origen:
        ventana.cambiar_estado("⚙️ CALIBRANDO AUDIO...")
        reconocedor.adjust_for_ambient_noise(origen, duration=1)
        
        while True:
            ventana.cambiar_estado("🎙️ ESCUCHANDO...")
            
            try:
                # 1. Captura el audio del micrófono
                audio = reconocedor.listen(origen, timeout=None, phrase_time_limit=5)
                ventana.cambiar_estado("🧠 PROCESANDO...")
                
                # 2. Traduce el audio a texto
                texto_usuario = reconocedor.recognize_google(audio, language="es-ES")
                print(f"Usuario: {texto_usuario}")
                
                # 3. Envía el texto a tu sesión de Gemini en ia.py
                respuesta_texto = enviar_mensaje_a_jarvis(texto_usuario)
                print(f"Jarvis: {respuesta_texto}")
                
                # 4. Cambia el estado visual y habla usando tu voz.py
                ventana.cambiar_estado("🔊 RESPONDIENDO...")
                hablar(respuesta_texto)
                
            except sr.UnknownValueError:
                # Si detecta ruido pero no palabras, continúa el bucle
                pass
            except Exception as e:
                print(f"Error en el ciclo de Jarvis: {e}")