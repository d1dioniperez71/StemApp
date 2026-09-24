#!/usr/bin/env bash
# Arranque Linux/macOS — verifica dependencias y fuerza bind 127.0.0.1
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -c "import fastapi, uvicorn" 2>/dev/null || { echo "Faltan dependencias. Ejecuta: pip install -e backend[dev]"; exit 1; }
echo "Limbus Split Pro → http://127.0.0.1:8317 (solo local)"
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8317
