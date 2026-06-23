import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from .agent import ejecutar_comando_sistema
import src.core.agent as agent

# 🔄 Carga las variables de entorno del archivo .env al sistema
load_dotenv()

# 🔒 Obtenemos la clave de forma segura desde el entorno
api_key_gemini = os.getenv("POTATO_GEMINI_API_KEY")

# ⚙️ Inicializamos el cliente pasándole la clave explícitamente
client = genai.Client(api_key=api_key_gemini)

# Creamos la configuración del asistente con su instrucción y su herramienta 🧰
config_potato = types.GenerateContentConfig(
    system_instruction=(
        "Eres Potato, un asistente virtual avanzado y experto administrador de sistemas Arch Linux. "
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
potato_chat = client.chats.create(model="gemini-2.5-flash", config=config_potato)

def enviar_mensaje_a_potato(texto_usuario: str, ventana=None) -> str:
    """
    Envía el texto a Gemini y gestiona automáticamente si la IA 
    decide invocar la herramienta del sistema.
    """
    if ventana:
        agent.set_ventana(ventana)

    # Enviamos el mensaje inicial del usuario
    respuesta = potato_chat.send_message(texto_usuario)

    # Si Potato responde algo de texto (sus pensamientos o respuesta), lo mostramos en consola
    if respuesta.text and ventana:
        ventana.log_consola(f"🥔 POTATO: {respuesta.text}")

    # 🧠 Verificamos si Gemini decidió hacer una llamada a la función (Tool Calling)
    if respuesta.function_calls:
        for llamada in respuesta.function_calls:
            # Validamos que sea nuestra función
            if llamada.name == "ejecutar_comando_sistema":
                # Extraemos los argumentos que Gemini calculó
                argumentos = llamada.args
                comando = argumentos.get("comando")
                descripcion = argumentos.get("descripcion")

                # Ejecutamos la función de agent.py (que pedirá confirmación)
                resultado_ejecucion = ejecutar_comando_sistema(comando, descripcion)

                # Le devolvemos el resultado de la acción a Gemini para que cierre el ciclo
                respuesta_final = potato_chat.send_message(resultado_ejecucion)

                if respuesta_final.text and ventana:
                    ventana.log_consola(f"🥔 POTATO: {respuesta_final.text}")

                return respuesta_final.text

    # Si no requería usar herramientas, devolvemos la respuesta de texto normal
    return respuesta.text
