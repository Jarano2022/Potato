#!/bin/bash
# Script de arranque profesional para Potato

# Obtener la ruta absoluta del directorio del script
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_DIR"

# Activar el entorno virtual si existe
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Exportar PYTHONPATH para que Python encuentre los módulos en src/
export PYTHONPATH=$PYTHONPATH:$PROJECT_DIR

# Ejecutar el punto de entrada principal
python3 src/main.py
