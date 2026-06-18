import os
from dotenv import load_dotenv  # 📦 Cargamos la librería para leer el .env
from google import genai
from google.genai import types
from agente import ejecutar_comando_sistema  

# 🔄 Carga las variables de entorno del archivo .env al sistema
load_dotenv()

# 🔒 Obtenemos la clave de forma segura desde el entorno
api_key_gemini = os.getenv("JARVIS_GEMINI_API_KEY")

# ⚙️ Inicializamos el cliente pasándole la clave explícitamente
client = genai.Client(api_key=api_key_gemini)

# Creamos la configuración del asistente con su instrucción y su herramienta 🧰
config_jarvis = types.GenerateContentConfig(
    system_instruction=(
        "Eres Jarvis, un asistente virtual avanzado y experto administrador de sistemas Arch Linux. "
        "Tu objetivo es ayudar al usuario a controlar su ordenador, gestionar el sistema y depurar errores. "
        "\n\nDIRECTRICES DE PENSAMIENTO:"
        "\n1. Análisis Proactivo: Antes de ejecutar un comando, piensa en las dependencias o posibles riesgos."
        "\n2. Depuración: Si un comando falla (devuelve ERROR), analiza los detalles de la salida. "
        "Explícale al usuario por qué falló y propón una solución técnica o un comando alternativo."
        "\n3. Transparencia: Informa al usuario sobre lo que vas a hacer de forma técnica pero elegante."
        "\n4. Herramientas: Usa 'ejecutar_comando_sistema' para cualquier acción física o consulta del sistema (ls, df, grep, etc.)."
        "\n\nActúa siempre con la eficiencia y el tono de un ingeniero senior de sistemas."
    ),
    tools=[ejecutar_comando_sistema],
    temperature=0.7,
)

# Creamos la sesión de chat continuo
jarvis_chat = client.chats.create(model="gemini-2.5-flash", config=config_jarvis)

def enviar_mensaje_a_jarvis(texto_usuario: str) -> str:
    """
    Envía el texto a Gemini y gestiona automáticamente si la IA 
    decide invocar la herramienta del sistema.
    """
    # Enviamos el mensaje inicial del usuario
    respuesta = jarvis_chat.send_message(texto_usuario)
    
    # 🧠 Verificamos si Gemini decidió hacer una llamada a la función (Tool Calling)
    if respuesta.function_calls:
        for llamada in respuesta.function_calls:
            # Validamos que sea nuestra función
            if llamada.name == "ejecutar_comando_sistema":
                # Extraemos los argumentos que Gemini calculó
                argumentos = llamada.args
                comando = argumentos.get("comando")
                descripcion = argumentos.get("descripcion")
                
                # Ejecutamos la función de agente.py (que pedirá confirmación por voz)
                resultado_ejecucion = ejecutar_comando_sistema(comando, descripcion)
                
                # Le devolvemos el resultado de la acción a Gemini para que cierre el ciclo
                respuesta_final = jarvis_chat.send_message(resultado_ejecucion)
                return respuesta_final.text
                
    # Si no requería usar herramientas, devolvemos la respuesta de texto normal
    return respuesta.text