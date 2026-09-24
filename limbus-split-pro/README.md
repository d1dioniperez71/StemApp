# Limbus Split Pro — Local Web Edition

Aplicación web **privada y local** para separar música en stems con IA (Demucs v4 htdemucs_ft + BSRNN), sin nube ni telemetría. El servidor escucha únicamente en `127.0.0.1`.

## Estructura
- `backend/` — FastAPI: upload, pipeline en cascada (5 etapas), gestión explícita de modelos, export.
- `frontend/` — React + Vite + TypeScript: mezclador con Web Audio API.
- `MODEL_MANIFEST.json` — manifiesto de modelos con licencias y hashes SHA-256.
- `scripts/` — arranque y verificación.

## Principios (de qwen_stem_instructions.txt)
1. **Honestidad técnica**: ninguna etapa se simula. De-reverb y lead/backing están marcados como no disponibles hasta encontrar modelos verificados.
2. **Descarga explícita**: ningún modelo se descarga sin confirmación del usuario (`POST /api/models/install` con `consent=true`).
3. **Privacidad**: bind solo a 127.0.0.1; todo el procesamiento es local.
4. **Reproducibilidad**: pyproject.toml con versiones fijadas; hashes SHA-256 por modelo.

## Inicio rápido
```bash
pip install -e backend[dev]
./scripts/start.sh            # backend en http://127.0.0.1:8317
cd frontend && npm install && npm run dev   # UI en http://127.0.0.1:5173
python scripts/verify_models.py
```
