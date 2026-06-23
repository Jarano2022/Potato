#!/bin/bash

# Obtener la ruta del directorio del script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=== Arrancando Servidor de Audio Independiente ==="

# Ejecutar el servidor usando el entorno virtual
exec venv/bin/python main.py
