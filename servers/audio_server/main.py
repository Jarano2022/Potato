import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import requests
import edge_tts

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("audio_server")

# Cargar variables de entorno: primero del directorio superior (proyecto principal) y luego locales
load_dotenv(dotenv_path="../../.env")
load_dotenv(dotenv_path=".env")

app = FastAPI(
    title="Potato Independent Audio Server",
    description="Servidor independiente de TTS (Text-to-Speech) con voces graves y refinadas.",
    version="1.0.0"
)

class SpeakRequest(BaseModel):
    text: str

# Configuración
ELEVEN_API_KEY = os.getenv("POTATO_ELEVEN_API_KEY")
# Si no hay Voice ID, usamos la voz "Adam" (pNInz6obpgq5paqqJJAe) que es muy grave, masculina y refinada
ELEVEN_VOICE_ID = os.getenv("POTATO_VOICE_ID", "pNInz6obpgq5paqqJJAe")
EDGE_VOICE = os.getenv("EDGE_VOICE", "es-ES-AlvaroNeural")  # Voz grave y profesional en español
TTS_ENGINE = os.getenv("TTS_ENGINE", "elevenlabs" if ELEVEN_API_KEY else "edge-tts").lower()

logger.info(f"Configuración cargada:")
logger.info(f" - Motor predeterminado: {TTS_ENGINE}")
logger.info(f" - ElevenLabs Voice ID: {ELEVEN_VOICE_ID}")
logger.info(f" - ElevenLabs API Key presente: {'Sí' if ELEVEN_API_KEY else 'No'}")
logger.info(f" - Edge-TTS Voice: {EDGE_VOICE}")

async def stream_edge_tts(text: str, voice: str):
    """Generador asíncrono para hacer streaming de audio desde Edge-TTS."""
    try:
        communicate = edge_tts.Communicate(text, voice)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]
    except Exception as e:
        logger.error(f"Error en el generador de Edge-TTS: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno en Edge-TTS: {e}")

def stream_elevenlabs(text: str, api_key: str, voice_id: str):
    """Generador síncrono (ejecutado en threadpool por FastAPI) para streaming desde ElevenLabs."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.55,
            "similarity_boost": 0.8,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }
    try:
        # Petición de stream directo a ElevenLabs
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=30)
        
        if response.status_code == 200:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk
        else:
            error_msg = f"ElevenLabs API retornó estado {response.status_code}: {response.text}"
            logger.error(error_msg)
            # Lanzamos una excepción que capturaremos en el endpoint para el fallback
            raise RuntimeError(error_msg)
    except Exception as e:
        logger.error(f"Error en conexión con ElevenLabs: {e}")
        raise e

@app.post("/speak")
async def speak(request: SpeakRequest):
    """
    Endpoint principal para sintetizar texto a voz.
    Si ElevenLabs está configurado y no falla, lo usa. De lo contrario, cae en Edge-TTS.
    """
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="El campo 'text' no puede estar vacío.")

    logger.info(f"Sintetizando texto: '{text[:50]}...'")

    # Intentar ElevenLabs si está seleccionado
    if TTS_ENGINE == "elevenlabs" and ELEVEN_API_KEY:
        try:
            logger.info("Intentando generar audio con ElevenLabs...")
            # Probamos si podemos obtener el primer fragmento de ElevenLabs
            # Para evitar bloquear si falla, usamos un generador síncrono adaptado
            generator = stream_elevenlabs(text, ELEVEN_API_KEY, ELEVEN_VOICE_ID)
            
            # Para verificar si el generador funciona antes de responder con StreamingResponse,
            # extraemos el primer chunk. Si falla, el bloque except atrapará el error y hará fallback.
            first_chunk = next(generator)
            
            # Definimos un generador encadenado que entrega el primer chunk y luego el resto
            def chained_generator():
                yield first_chunk
                for chunk in generator:
                    yield chunk
            
            return StreamingResponse(chained_generator(), media_type="audio/mpeg")
        except Exception as e:
            logger.warning(f"Fallo en ElevenLabs ({e}). Aplicando fallback a Edge-TTS.")
            # Continuamos al fallback de Edge-TTS
    
    # Fallback o uso directo de Edge-TTS
    logger.info(f"Generando audio con Edge-TTS (Voz: {EDGE_VOICE})...")
    return StreamingResponse(stream_edge_tts(text, EDGE_VOICE), media_type="audio/mpeg")

@app.get("/health")
async def health():
    """Endpoint de estado del servidor."""
    return {
        "status": "online",
        "engine": TTS_ENGINE,
        "elevenlabs_configured": bool(ELEVEN_API_KEY),
        "edge_voice": EDGE_VOICE
    }

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("POTATO_AUDIO_PORT", os.getenv("PORT", "8000")))
    uvicorn.run(app, host=host, port=port)
