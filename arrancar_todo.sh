#!/bin/bash

# Configuración de colores para una interfaz premium en terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # Sin color

# Asegurar que estamos en el directorio del proyecto
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

mostrar_menu() {
    clear
    echo -e "${BLUE}=================================================${NC}"
    echo -e "${BLUE}    POTATO - PANEL DE CONTROL Y ARRANQUE         ${NC}"
    echo -e "${BLUE}=================================================${NC}"
    echo -e " 1) 📦 Instalar todas las dependencias (Venvs)"
    echo -e " 2) 🔊 Iniciar Servidor de Audio (Solo)"
    echo -e " 3) 🎙️ Iniciar Asistente Potato (Solo)"
    echo -e " 4) 🚀 Iniciar TODO junto (Audio + Web + GUI local)"
    echo -e " 5) 🌐 Iniciar Servidores en SEGUNDO PLANO (Audio + Web + Funnel)"
    echo -e " 6) 🛑 Detener Servidores en SEGUNDO PLANO"
    echo -e " 7) ❌ Salir"
    echo -e "${BLUE}=================================================${NC}"
    echo -n "Selecciona una opción [1-7]: "
}

instalar_dependencias() {
    PYTHON_CMD="python3"
    if ! command -v python3 &> /dev/null; then
        PYTHON_CMD="python"
    fi

    echo -e "\n${YELLOW}[+] Creando e instalando entorno virtual para el Proyecto Principal...${NC}"
    if [ ! -d "venv" ]; then
        $PYTHON_CMD -m venv venv
    fi
    venv/bin/pip install -r requirements.txt
    
    echo -e "\n${YELLOW}[+] Creando e instalando entorno virtual para el Servidor de Audio...${NC}"
    if [ ! -d "servers/audio_server/venv" ]; then
        $PYTHON_CMD -m venv servers/audio_server/venv
    fi
    servers/audio_server/venv/bin/pip install -r servers/audio_server/requirements.txt
    
    echo -e "\n${YELLOW}[+] Creando e instalando entorno virtual para el Servidor HTML...${NC}"
    if [ ! -d "servers/html_server/venv" ]; then
        $PYTHON_CMD -m venv servers/html_server/venv
    fi
    servers/html_server/venv/bin/pip install -r servers/html_server/requirements.txt
    
    echo -e "\n${GREEN}[✓] ¡Todas las dependencias han sido instaladas con éxito!${NC}"
    read -p "Presiona Enter para continuar..."
}

iniciar_audio() {
    echo -e "\n${GREEN}[🚀] Iniciando Servidor de Audio...${NC}"
    ./servers/audio_server/arrancar_servidor.sh
}

iniciar_potato() {
    echo -e "\n${GREEN}[🚀] Iniciando Asistente Potato...${NC}"
    if [ -x "venv/bin/python" ]; then
        venv/bin/python main.py
    else
        echo -e "${YELLOW}[!] Entorno virtual del proyecto principal no detectado. Usando python global...${NC}"
        python3 main.py
    fi
}

iniciar_todo() {
    # Cargar variables de entorno del archivo .env
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    fi

    echo -e "\n${GREEN}[🚀] Iniciando Servidor de Audio en segundo plano...${NC}"
    # Guardamos la salida del servidor en un archivo de log para diagnosticar errores
    ./servers/audio_server/arrancar_servidor.sh > servers/audio_server/servidor.log 2>&1 &
    AUDIO_PID=$!
    
    # Nos aseguramos de matar todos los procesos en segundo plano al salir
    trap "kill $AUDIO_PID $HTML_PID $TAILSCALE_PID 2>/dev/null; tailscale serve reset --yes 2>/dev/null" EXIT INT TERM
    
    echo -e "${YELLOW}[*] Esperando 3 segundos a que el servidor de audio se estabilice...${NC}"
    sleep 3
    
    # Comprobar si el proceso del servidor de audio sigue activo
    if ! kill -0 $AUDIO_PID 2>/dev/null; then
        echo -e "${RED}[Error] El servidor de audio falló al arrancar. Detalles del log:${NC}"
        echo -e "${BLUE}-------------------------------------------------${NC}"
        if [ -f "servers/audio_server/servidor.log" ]; then
            cat servers/audio_server/servidor.log
        else
            echo "No se encontró el archivo de log: servers/audio_server/servidor.log"
        fi
        echo -e "${BLUE}-------------------------------------------------${NC}"
        read -p "Presiona Enter para volver..."
        return
    fi
    
    echo -e "\n${GREEN}[🚀] Iniciando Servidor HTML en segundo plano...${NC}"
    ./servers/html_server/arrancar_servidor.sh > servers/html_server/servidor.log 2>&1 &
    HTML_PID=$!
    
    # Actualizar trap con el PID de HTML
    trap "kill $AUDIO_PID $HTML_PID $TAILSCALE_PID 2>/dev/null; tailscale serve reset --yes 2>/dev/null" EXIT INT TERM
    
    sleep 1
    
    # Comprobar si el proceso del servidor HTML sigue activo
    if ! kill -0 $HTML_PID 2>/dev/null; then
        echo -e "${RED}[Error] El servidor HTML falló al arrancar. Detalles del log:${NC}"
        echo -e "${BLUE}-------------------------------------------------${NC}"
        if [ -f "servers/html_server/servidor.log" ]; then
            cat servers/html_server/servidor.log
        else
            echo "No se encontró el archivo de log: servers/html_server/servidor.log"
        fi
        echo -e "${BLUE}-------------------------------------------------${NC}"
        read -p "Presiona Enter para volver..."
        kill $AUDIO_PID 2>/dev/null
        return
    fi

    # Exponer con Tailscale Funnel si está activo en las variables de entorno
    TAILSCALE_PID=""
    if [ "$EXPOSE_TAILSCALE" = "True" ] || [ "$EXPOSE_TAILSCALE" = "true" ]; then
        echo -e "\n${GREEN}[🔒] Exponiendo Servidor HTML públicamente con Tailscale Funnel en puerto $POTATO_HTML_PORT...${NC}"
        tailscale serve reset --yes 2>/dev/null
        tailscale funnel --bg --yes $POTATO_HTML_PORT > servers/html_server/funnel.log 2>&1 &
        TAILSCALE_PID=$!
        # Actualizar trap para incluir Tailscale
        trap "kill $AUDIO_PID $HTML_PID $TAILSCALE_PID 2>/dev/null; tailscale serve reset --yes 2>/dev/null" EXIT INT TERM
    fi
    
    echo -e "\n${GREEN}[🚀] Iniciando Asistente Potato...${NC}"
    if [ -x "venv/bin/python" ]; then
        venv/bin/python src/main.py
    else
        python3 src/main.py
    fi
    
    # Al salir del asistente, detenemos todos los servidores y limpiamos la exposición
    echo -e "\n${YELLOW}[-] Apagando los servidores de Audio, HTML y exposición de Tailscale...${NC}"
    kill $AUDIO_PID $HTML_PID $TAILSCALE_PID 2>/dev/null
    tailscale serve reset --yes 2>/dev/null
    trap - EXIT INT TERM
    read -p "Presiona Enter para continuar..."
}

iniciar_servidores_segundo_plano() {
    # Cargar variables de entorno del archivo .env
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    fi

    # Comprobar si ya están corriendo
    if [ -f "/tmp/potato_audio.pid" ] && kill -0 $(cat /tmp/potato_audio.pid) 2>/dev/null; then
        echo -e "${YELLOW}[!] Los servidores ya se están ejecutando en segundo plano.${NC}"
        read -p "Presiona Enter para volver..."
        return
    fi

    echo -e "\n${GREEN}[🚀] Iniciando Servidor de Audio en segundo plano...${NC}"
    ./servers/audio_server/arrancar_servidor.sh > servers/audio_server/servidor.log 2>&1 &
    AUDIO_PID=$!
    echo $AUDIO_PID > /tmp/potato_audio.pid
    
    echo -e "${YELLOW}[*] Esperando a que se estabilice el audio...${NC}"
    sleep 3
    
    # Comprobar si el proceso del servidor de audio sigue activo
    if ! kill -0 $AUDIO_PID 2>/dev/null; then
        echo -e "${RED}[Error] El servidor de audio falló al arrancar. Detalles del log:${NC}"
        cat servers/audio_server/servidor.log
        rm /tmp/potato_audio.pid
        read -p "Presiona Enter para volver..."
        return
    fi
    
    echo -e "${GREEN}[🚀] Iniciando Servidor HTML en segundo plano...${NC}"
    ./servers/html_server/arrancar_servidor.sh > servers/html_server/servidor.log 2>&1 &
    HTML_PID=$!
    echo $HTML_PID > /tmp/potato_html.pid
    
    sleep 1
    
    # Comprobar si el proceso del servidor HTML sigue activo
    if ! kill -0 $HTML_PID 2>/dev/null; then
        echo -e "${RED}[Error] El servidor HTML falló al arrancar. Detalles del log:${NC}"
        cat servers/html_server/servidor.log
        kill $(cat /tmp/potato_audio.pid) 2>/dev/null
        rm /tmp/potato_audio.pid /tmp/potato_html.pid
        read -p "Presiona Enter para volver..."
        return
    fi

    # Exponer con Tailscale Funnel si está activo
    TAILSCALE_PID=""
    if [ "$EXPOSE_TAILSCALE" = "True" ] || [ "$EXPOSE_TAILSCALE" = "true" ]; then
        echo -e "${GREEN}[🔒] Exponiendo Servidor HTML con Tailscale Funnel en puerto $POTATO_HTML_PORT...${NC}"
        tailscale serve reset --yes 2>/dev/null
        tailscale funnel --bg --yes $POTATO_HTML_PORT > servers/html_server/funnel.log 2>&1 &
        TAILSCALE_PID=$!
        echo $TAILSCALE_PID > /tmp/potato_tailscale.pid
    fi

    echo -e "\n${GREEN}[✓] Servidores iniciados correctamente en segundo plano.${NC}"
    echo -e "Puedes verificar los logs en 'servers/audio_server/servidor.log' y 'servers/html_server/servidor.log'."
    if [ -n "$TAILSCALE_PID" ]; then
        echo -e "Tailscale Funnel está exponiendo el puerto $POTATO_HTML_PORT en segundo plano."
    fi
    read -p "Presiona Enter para continuar..."
}

detener_servidores_segundo_plano() {
    echo -e "\n${YELLOW}[-] Deteniendo servidores en segundo plano...${NC}"
    
    if [ -f "/tmp/potato_audio.pid" ]; then
        kill $(cat /tmp/potato_audio.pid) 2>/dev/null
        rm /tmp/potato_audio.pid
    fi
    
    if [ -f "/tmp/potato_html.pid" ]; then
        kill $(cat /tmp/potato_html.pid) 2>/dev/null
        rm /tmp/potato_html.pid
    fi
    
    if [ -f "/tmp/potato_tailscale.pid" ]; then
        kill $(cat /tmp/potato_tailscale.pid) 2>/dev/null
        rm /tmp/potato_tailscale.pid
    fi
    
    tailscale serve reset --yes 2>/dev/null
    echo -e "${GREEN}[✓] Todos los servidores en segundo plano han sido detenidos.${NC}"
    read -p "Presiona Enter para continuar..."
}

# Bucle principal
while true; do
    mostrar_menu
    read opcion
    case $opcion in
        1) instalar_dependencias ;;
        2) iniciar_audio ;;
        3) iniciar_potato ;;
        4) iniciar_todo ;;
        5) iniciar_servidores_segundo_plano ;;
        6) detener_servidores_segundo_plano ;;
        7) echo -e "\n${BLUE}Hasta luego, señor.${NC}"; exit 0 ;;
        *) echo -e "\n${RED}Opción inválida. Selecciona un número del 1 al 7.${NC}"; sleep 1.5 ;;
    esac
done
