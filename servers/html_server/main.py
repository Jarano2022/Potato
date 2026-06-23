import os
import subprocess
import json
import logging
import requests
import io
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("html_server")

# Cargar variables de entorno del proyecto
load_dotenv(dotenv_path="../../.env")
load_dotenv(dotenv_path=".env")

app = FastAPI(
    title="Potato Web Server",
    description="Servidor web para interactuar con Potato desde cualquier lugar vía Tailscale.",
    version="1.0.0"
)

# Cargar API keys
api_key_gemini = os.getenv("POTATO_GEMINI_API_KEY")
if not api_key_gemini:
    logger.warning("No se encontró POTATO_GEMINI_API_KEY en las variables de entorno.")

# Inicializar cliente de Gemini
client = genai.Client(api_key=api_key_gemini)

# Configurar chat continuo
config_potato = types.GenerateContentConfig(
    system_instruction=(
        "Eres Potato, un asistente virtual avanzado y experto administrador de sistemas Arch Linux. "
        "Tu objetivo es ayudar al usuario a controlar su ordenador, gestionar el sistema y depurar errores. "
        "Actúa siempre con la eficiencia y el tono de un ingeniero senior de sistemas."
    ),
    temperature=0.7,
)
potato_chat = client.chats.create(model="gemini-2.5-flash", config=config_potato)

class ChatRequest(BaseModel):
    message: str

def get_tailscale_info():
    """
    Consulta a la cli local de tailscale para obtener el MagicDNS y la IP local
    del nodo en la VPN privada.
    """
    try:
        res = subprocess.run(["tailscale", "status", "--json"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            cert_domains = data.get("CertDomains", [])
            dns_name = cert_domains[0] if cert_domains else "Desconocido"
            
            # Obtener IP propia en la red tailscale
            self_node = data.get("Self", {})
            ips = self_node.get("TailscaleIPs", ["127.0.0.1"])
            
            return {
                "dns_name": dns_name,
                "ips": ips,
                "active": True
            }
    except Exception as e:
        logger.warning(f"No se pudo consultar el estado de Tailscale: {e}")
    return {"dns_name": "No disponible", "ips": ["127.0.0.1"], "active": False}

@app.post("/api/chat")
async def chat(req: ChatRequest):
    msg = req.message.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")
    try:
        response = potato_chat.send_message(msg)
        return {"response": response.text}
    except Exception as e:
        logger.error(f"Error en chat con Gemini: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tts")
async def tts(text: str):
    if not text.strip():
        raise HTTPException(status_code=400, detail="El texto no puede estar vacío.")
    
    # Redirigir al puerto del servidor de audio (audio_server)
    try:
        audio_port = os.getenv("POTATO_AUDIO_PORT", "8000")
        logger.info(f"Solicitando voz sintetizada para: '{text[:30]}...' al puerto {audio_port}")
        
        # Enviar petición al servidor de voz
        res = requests.post(f"http://127.0.0.1:{audio_port}/speak", json={"text": text}, timeout=30)
        if res.status_code == 200:
            return StreamingResponse(io.BytesIO(res.content), media_type="audio/mpeg")
        else:
            logger.error(f"Servidor de audio retornó código {res.status_code}: {res.text}")
            raise HTTPException(status_code=res.status_code, detail="Error al generar audio en el servidor de voz.")
    except Exception as e:
        logger.error(f"Error conectando al servidor de audio local: {e}")
        raise HTTPException(status_code=500, detail=f"No se pudo conectar con el servidor de audio local: {e}")

@app.get("/api/status")
async def status():
    return {
        "status": "online",
        "tailscale": get_tailscale_info()
    }

@app.get("/", response_class=HTMLResponse)
async def serve_home():
    html_content = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Potato Web Terminal</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght=300;400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #000000;
            --terminal-bg: rgba(10, 10, 10, 0.7);
            --accent-color: #ffaa00;
            --text-color: #ffffff;
            --border-color: #333333;
            --shadow-color: rgba(255, 170, 0, 0.3);
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'JetBrains Mono', monospace;
            background-color: var(--bg-color);
            color: var(--text-color);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        /* Efecto de rejilla de fondo */
        body::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                linear-gradient(rgba(20, 20, 20, 0.3) 1px, transparent 1px),
                linear-gradient(90deg, rgba(20, 20, 20, 0.3) 1px, transparent 1px);
            background-size: 20px 20px;
            z-index: -1;
            pointer-events: none;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 30px;
            border-bottom: 1px solid var(--border-color);
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(10px);
            z-index: 10;
        }

        .logo-section h1 {
            font-size: 20px;
            font-weight: 700;
            letter-spacing: 2px;
            color: var(--accent-color);
            text-shadow: 0 0 10px var(--shadow-color);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .status-badge {
            background: rgba(255, 170, 0, 0.1);
            border: 1px solid var(--accent-color);
            color: var(--accent-color);
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 0 8px var(--shadow-color);
        }

        .status-badge .dot {
            width: 8px;
            height: 8px;
            background: var(--accent-color);
            border-radius: 50%;
            animation: pulse 1.5s infinite;
        }

        main {
            flex: 1;
            display: flex;
            position: relative;
            height: calc(100vh - 150px);
        }

        /* Consola de logs lateral */
        .sidebar {
            width: 320px;
            border-right: 1px solid var(--border-color);
            background: rgba(5, 5, 5, 0.85);
            display: flex;
            flex-direction: column;
            padding: 20px;
        }

        @media (max-width: 900px) {
            .sidebar {
                display: none;
            }
        }

        .sidebar-title {
            font-size: 12px;
            color: #888888;
            margin-bottom: 15px;
            letter-spacing: 1px;
        }

        .system-logs {
            flex: 1;
            font-size: 11px;
            line-height: 1.6;
            color: #aaaaaa;
            overflow-y: auto;
            white-space: pre-wrap;
            font-family: monospace;
        }

        /* Centro de la pantalla con la esfera */
        .center-stage {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            position: relative;
            padding: 20px;
        }

        .orb-container {
            width: 300px;
            height: 300px;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .orb {
            width: 140px;
            height: 140px;
            background: radial-gradient(circle, #ffffff 0%, var(--accent-color) 70%, #ff5500 100%);
            border-radius: 50%;
            box-shadow: 0 0 35px var(--shadow-color);
            transition: transform 0.1s ease, box-shadow 0.1s ease, background 0.5s ease;
            z-index: 2;
            cursor: pointer;
        }

        /* Anillos orbitantes alrededor del núcleo */
        .ring {
            position: absolute;
            width: 180px;
            height: 180px;
            border: 2px solid var(--accent-color);
            border-radius: 50%;
            opacity: 0.3;
            animation: ring-pulse 4s infinite linear;
            pointer-events: none;
            transition: border-color 0.5s ease;
        }

        .ring:nth-child(2) {
            width: 220px;
            height: 220px;
            animation-duration: 6s;
            animation-direction: reverse;
            opacity: 0.2;
        }

        .ring:nth-child(3) {
            width: 260px;
            height: 260px;
            animation-duration: 8s;
            opacity: 0.1;
        }

        /* Sección de Chat */
        .chat-section {
            width: 380px;
            border-left: 1px solid var(--border-color);
            background: rgba(5, 5, 5, 0.85);
            display: flex;
            flex-direction: column;
            height: 100%;
        }

        @media (max-width: 768px) {
            main {
                flex-direction: column;
            }
            .chat-section {
                width: 100%;
                border-left: none;
                border-top: 1px solid var(--border-color);
                height: 50%;
            }
            .center-stage {
                height: 50%;
            }
        }

        .chat-feed {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .message {
            max-width: 85%;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 13px;
            line-height: 1.5;
            word-wrap: break-word;
        }

        .message.user {
            align-self: flex-end;
            background: #222222;
            color: #ffffff;
            border: 1px solid #444444;
            border-bottom-right-radius: 0;
        }

        .message.potato {
            align-self: flex-start;
            background: rgba(255, 170, 0, 0.05);
            color: #ffffff;
            border: 1px solid var(--accent-color);
            border-bottom-left-radius: 0;
            box-shadow: 0 0 8px rgba(255, 170, 0, 0.1);
        }

        .message.system {
            align-self: center;
            background: rgba(247, 190, 2, 0.1);
            color: #f7be02;
            border: 1px solid #f7be02;
            font-size: 11px;
            max-width: 95%;
        }

        .input-bar {
            padding: 20px;
            border-top: 1px solid var(--border-color);
            background: rgba(0, 0, 0, 0.9);
            display: flex;
            gap: 10px;
        }

        .input-bar input {
            flex: 1;
            background: #111111;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 12px 15px;
            color: #ffffff;
            font-family: inherit;
            font-size: 14px;
            outline: none;
            transition: border-color 0.3s ease;
        }

        .input-bar input:focus {
            border-color: var(--accent-color);
        }

        .input-bar button {
            background: var(--accent-color);
            color: #000000;
            border: none;
            border-radius: 4px;
            padding: 0 20px;
            font-family: inherit;
            font-weight: bold;
            font-size: 14px;
            cursor: pointer;
            transition: opacity 0.3s ease, box-shadow 0.3s ease, background 0.3s ease;
            box-shadow: 0 0 10px var(--shadow-color);
        }

        .input-bar button:hover {
            opacity: 0.9;
            box-shadow: 0 0 15px var(--accent-color);
        }

        .input-bar #mic-btn {
            padding: 0 15px;
            font-size: 16px;
            transition: background 0.2s ease, transform 0.1s ease;
        }

        /* Animaciones */
        @keyframes pulse {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.2); opacity: 0.5; }
            100% { transform: scale(1); opacity: 1; }
        }

        @keyframes ring-pulse {
            0% { transform: rotate(0deg) scale(1); opacity: 0.3; }
            50% { transform: rotate(180deg) scale(1.1); opacity: 0.15; }
            100% { transform: rotate(360deg) scale(1); opacity: 0.3; }
        }

        /* Barra de desplazamiento */
        ::-webkit-scrollbar {
            width: 6px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(0,0,0,0.1);
        }
        ::-webkit-scrollbar-thumb {
            background: #333333;
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: var(--accent-color);
        }
    </style>
</head>
<body>
    <header>
        <div class="logo-section">
            <h1>🥔 POTATO WEB</h1>
        </div>
        <div id="tailscale-badge" class="status-badge">
            <div class="dot"></div>
            <span>CONECTANDO...</span>
        </div>
    </header>

    <main>
        <div class="sidebar">
            <div class="sidebar-title">TERMINAL DE ACTIVIDAD</div>
            <div id="logs" class="system-logs">>>> SISTEMA WEB INICIALIZADO...
>>> CONECTANDO A POTATO API...</div>
        </div>

        <div class="center-stage">
            <div class="orb-container">
                <div class="ring"></div>
                <div class="ring"></div>
                <div class="ring"></div>
                <div id="gui-orb" class="orb"></div>
            </div>
        </div>

        <div class="chat-section">
            <div id="chat-feed" class="chat-feed">
                <div class="message potato">Hola, soy Potato. ¿En qué puedo ayudarte hoy, señor?</div>
            </div>
            <form id="chat-form" class="input-bar">
                <input id="chat-input" type="text" placeholder="Escribe tu comando o pregunta aquí..." autocomplete="off">
                <button id="mic-btn" type="button">🎙️</button>
                <button type="submit">ENVIAR</button>
            </form>
        </div>
    </main>

    <script>
        const chatForm = document.getElementById('chat-form');
        const chatInput = document.getElementById('chat-input');
        const chatFeed = document.getElementById('chat-feed');
        const guiOrb = document.getElementById('gui-orb');
        const logsDiv = document.getElementById('logs');
        const tailscaleBadge = document.getElementById('tailscale-badge');
        const micBtn = document.getElementById('mic-btn');
        const rings = document.querySelectorAll('.ring');

        let audioCtx = null;
        let analyser = null;
        let sourceNode = null;
        let animationFrameId = null;

        let recognition = null;
        let isListening = false;

        // Cambiar colores y destellos según el estado de la IA
        function updateUIState(state) {
            let color, accent, shadow;
            switch(state) {
                case 'escuchando':
                    color = 'radial-gradient(circle, #ffffff 0%, #00e5ff 70%, #0055ff 100%)';
                    accent = '#00e5ff';
                    shadow = 'rgba(0, 229, 255, 0.4)';
                    break;
                case 'procesando':
                    color = 'radial-gradient(circle, #ffffff 0%, #d500f9 70%, #7c4dff 100%)';
                    accent = '#d500f9';
                    shadow = 'rgba(213, 0, 249, 0.4)';
                    break;
                case 'respondiendo':
                    color = 'radial-gradient(circle, #ffffff 0%, #ffea00 70%, #ff5500 100%)';
                    accent = '#ffea00';
                    shadow = 'rgba(255, 234, 0, 0.4)';
                    break;
                default: // idle / online
                    color = 'radial-gradient(circle, #ffffff 0%, #ffaa00 70%, #ff5500 100%)';
                    accent = '#ffaa00';
                    shadow = 'rgba(255, 170, 0, 0.3)';
            }
            
            guiOrb.style.background = color;
            guiOrb.style.boxShadow = `0 0 35px ${shadow}`;
            document.documentElement.style.setProperty('--accent-color', accent);
            document.documentElement.style.setProperty('--shadow-color', shadow);
        }

        function log(message) {
            logsDiv.textContent += `\n[${new Date().toLocaleTimeString()}] ${message}`;
            logsDiv.scrollTop = logsDiv.scrollHeight;
        }

        // Reconocimiento de voz nativo por el navegador
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'es-ES';

            recognition.onstart = () => {
                isListening = true;
                micBtn.style.background = '#ff0055'; // Color rojo/rosa de grabación
                micBtn.textContent = '🛑';
                updateUIState('escuchando');
                log("Escuchando desde el micrófono del navegador...");
            };

            recognition.onresult = (event) => {
                const text = event.results[0][0].transcript;
                chatInput.value = text;
                log(`Voz transcrita: "${text}"`);
                // Enviar automáticamente el formulario
                chatForm.dispatchEvent(new Event('submit'));
            };

            recognition.onerror = (event) => {
                log(`Error de micrófono en navegador: ${event.error}`);
                stopMicrophone();
            };

            recognition.onend = () => {
                stopMicrophone();
            };
        } else {
            micBtn.style.display = 'none';
            log("Este navegador no soporta SpeechRecognition nativo.");
        }

        function stopMicrophone() {
            isListening = false;
            micBtn.style.background = 'var(--accent-color)';
            micBtn.textContent = '🎙️';
            updateUIState('idle');
        }

        micBtn.addEventListener('click', () => {
            if (!recognition) return;
            if (isListening) {
                recognition.stop();
            } else {
                // Activar o reanudar el contexto de audio al interactuar
                if (audioCtx && audioCtx.state === 'suspended') {
                    audioCtx.resume();
                }
                recognition.start();
            }
        });

        // Permitir iniciar la escucha haciendo clic directo sobre la esfera central (Orb)
        guiOrb.addEventListener('click', () => {
            micBtn.click();
        });

        // Obtener estado de conexión y Tailscale
        async function fetchStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                if (data.tailscale && data.tailscale.active) {
                    const domain = data.tailscale.dns_name.replace(/\.$/, '');
                    tailscaleBadge.querySelector('span').textContent = `TAILSCALE: ${domain}`;
                    log(`Conectado a Tailscale en la dirección: ${domain}`);
                } else {
                    tailscaleBadge.querySelector('span').textContent = 'EXPOSICIÓN LOCAL';
                    tailscaleBadge.style.borderColor = '#f7be02';
                    tailscaleBadge.style.color = '#f7be02';
                    tailscaleBadge.querySelector('.dot').style.background = '#f7be02';
                    log('Exposición local activa. Tailscale no detectado o inactivo.');
                }
                updateUIState('idle');
            } catch (err) {
                log(`Error conectando al estado de Tailscale: ${err}`);
            }
        }

        // Manejar el envío del formulario de chat
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const text = chatInput.value.trim();
            if (!text) return;

            chatInput.value = '';
            appendMessage('user', text);
            log(`Usuario: "${text}"`);
            
            updateUIState('procesando');
            log("Enviando consulta a Gemini...");

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                
                if (res.ok) {
                    const data = await res.json();
                    appendMessage('potato', data.response);
                    log(`Potato: "${data.response}"`);
                    
                    // Generar respuesta sintetizada por voz
                    playTTS(data.response);
                } else {
                    log(`Error en la consulta: ${res.statusText}`);
                    updateUIState('idle');
                }
            } catch (err) {
                log(`Error de red: ${err}`);
                updateUIState('idle');
            }
        });

        function appendMessage(sender, text) {
            const msgDiv = document.createElement('div');
            msgDiv.classList.add('message', sender);
            msgDiv.textContent = text;
            chatFeed.appendChild(msgDiv);
            chatFeed.scrollTop = chatFeed.scrollHeight;
        }

        // Solicitar el audio al servidor web y reproducirlo analizando frecuencia/volumen
        async function playTTS(text) {
            updateUIState('procesando');
            try {
                if (!audioCtx) {
                    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                }
                
                // Si el navegador suspendió el contexto, reanudar en interacción
                if (audioCtx.state === 'suspended') {
                    await audioCtx.resume();
                }

                if (!analyser) {
                    analyser = audioCtx.createAnalyser();
                    analyser.fftSize = 64;
                }

                log("Generando sintetización de voz...");
                const url = `/api/tts?text=${encodeURIComponent(text)}`;
                const audio = new Audio(url);
                
                audio.addEventListener('play', () => {
                    updateUIState('respondiendo');
                    log("Reproduciendo respuesta de voz...");
                    
                    if (sourceNode) {
                        sourceNode.disconnect();
                    }
                    sourceNode = audioCtx.createMediaElementSource(audio);
                    sourceNode.connect(analyser);
                    analyser.connect(audioCtx.destination);
                    
                    analyzeAudio();
                });

                audio.addEventListener('ended', () => {
                    updateUIState('idle');
                    log("Finalizó la reproducción de voz.");
                    if (animationFrameId) {
                        cancelAnimationFrame(animationFrameId);
                    }
                    guiOrb.style.transform = 'scale(1)';
                    rings.forEach(ring => ring.style.transform = 'scale(1)');
                });

                audio.play();
            } catch (err) {
                log(`Error de reproducción de audio: ${err}`);
                updateUIState('idle');
            }
        }

        // Analizar en tiempo real y distorsionar la esfera de la web
        function analyzeAudio() {
            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            
            function draw() {
                animationFrameId = requestAnimationFrame(draw);
                analyser.getByteFrequencyData(dataArray);
                
                let sum = 0;
                for (let i = 0; i < bufferLength; i++) {
                    sum += dataArray[i];
                }
                const avg = sum / bufferLength;
                
                // Escalar esfera central
                const scale = 1.0 + (avg / 255.0) * 0.75;
                guiOrb.style.transform = `scale(${scale})`;
                
                // Sombra dinámica (brillo)
                const shadowSize = 35 + (avg / 255.0) * 100;
                guiOrb.style.boxShadow = `0 0 ${shadowSize}px var(--shadow-color)`;
                
                // Escalar anillos exteriores reactivamente
                rings.forEach((ring, idx) => {
                    const ringScale = 1.0 + (avg / 255.0) * (0.2 + idx * 0.1);
                    ring.style.transform = `scale(${ringScale})`;
                });
            }
            draw();
        }

        // Cargar
        fetchStatus();
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("POTATO_HTML_HOST", "0.0.0.0")
    port = int(os.getenv("POTATO_HTML_PORT", "8082"))
    uvicorn.run(app, host=host, port=port)
