# Servidor de Audio Independiente para Potato (TTS)

Este es un servidor de síntesis de voz (Text-to-Speech) independiente para Potato. Escucha en el puerto `8000` y expone el endpoint `/speak` que espera recibir peticiones POST con texto y responde con el flujo de audio binario.

## Características

- **Voz grave y refinada**: Diseñado para utilizar voces masculinas profundas y profesionales.
- **Soporte de ElevenLabs**: Utiliza el motor premium de ElevenLabs si se configuran las claves API.
- **Soporte de Edge-TTS (Gratuito/Local)**: Utiliza la voz de alta calidad de Microsoft Edge (`es-ES-AlvaroNeural`) de forma gratuita y local, sin necesidad de claves de API.
- **Tolerancia a fallos automática (Fallback)**: Si ElevenLabs se queda sin saldo o falla, el servidor conmuta de manera invisible a Edge-TTS para que Potato nunca pierda la voz.

## Configuración (.env)

El servidor carga automáticamente las variables del archivo `.env` en la raíz del proyecto principal (o de un archivo `.env` local si existe).

Puedes configurar las siguientes variables de entorno:

- `TTS_ENGINE`: El motor predeterminado a usar (`elevenlabs` o `edge-tts`). Si no se define, se detecta automáticamente (usa ElevenLabs si hay API key, si no Edge-TTS).
- `POTATO_ELEVEN_API_KEY`: Tu clave de API de ElevenLabs.
- `POTATO_VOICE_ID`: El ID de la voz a usar en ElevenLabs (por defecto usa "Adam" `pNInz6obpgq5paqqJJAe`, una voz muy grave y sofisticada).
- `EDGE_VOICE`: La voz neural de Edge-TTS a utilizar (por defecto `es-ES-AlvaroNeural`).
- `PORT`: Puerto donde escuchará el servidor (por defecto `8000`).
- `HOST`: Dirección de red donde escuchará el servidor (por defecto `0.0.0.0` para permitir accesos desde otras máquinas en la misma red).

## Instalación y Arranque

1. Instala las dependencias en tu entorno de Python:
   ```bash
   pip install -r requirements.txt
   ```

2. Arranca el servidor ejecutando el script proporcionado:
   ```bash
   ./arrancar_servidor.sh
   ```

El servidor estará listo y escuchando en `http://localhost:8000`.

## Pruebas

Puedes probar el servidor de forma independiente usando `curl`:

```bash
curl -X POST http://localhost:8000/speak \
  -H "Content-Type: application/json" \
  -d '{"text": "Hola, soy Potato. Tu servidor de audio independiente está funcionando perfectamente."}' \
  --output /tmp/test_potato.mp3
```

Luego puedes reproducirlo con `mpv` o cualquier otro reproductor:
```bash
mpv /tmp/test_potato.mp3
```
