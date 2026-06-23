#!/bin/bash

# Obtener la ruta del directorio del script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=== Arrancando Servidor HTML Independiente ==="

# Ejecutar el servidor usando el entorno virtual con exec
exec venv/bin/python main.py
