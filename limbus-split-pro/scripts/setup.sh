#!/usr/bin/env bash
# ============================================================================
# Limbus Split Pro — setup.sh (Linux/macOS)
# Instalación reproducible en entorno controlado (.venv del proyecto).
#
# Qué hace (secciones 11, 20 y 21 de qwen_stem_instructions.txt):
#   1. Verifica Python 3.10+ (recomendado 3.11/3.12).
#   2. Crea virtualenv .venv dentro del proyecto.
#   3. Instala PyTorch (CPU o CUDA 12.4 según flag) desde la fuente oficial.
#   4. Instala dependencias backend desde pyproject.toml + requirements.lock.
#   5. Verifica/instala FFmpeg (o informa cómo obtenerlo).
#   6. (--with-models) Descarga los modelos del MODEL_MANIFEST.json DESDE LAS
#      FUENTES PRIMARIAS verificadas (ver docs/MODEL_SOURCES.md), calcula y
#      valida SHA-256, y escribe los hashes reales en el manifiesto local.
#   7. Redirige cachés (torch/HF/demucs) a una carpeta controlada del proyecto.
#
# Uso:
#   ./setup.sh                 # solo dependencias (no descarga modelos)
#   ./setup.sh --gpu           # torch con CUDA 12.4
#   ./setup.sh --with-models   # + descarga/verificación explícita de modelos
#   ./setup.sh --experimental-models  # incluye dereverb/BSRNN opt-in
#
# PRIVACIDAD: este script solo contacta pypi.org, download.pytorch.org,
# dl.fbaipublicfiles.com y huggingface.co (lista completa en docs/MODEL_SOURCES.md).
# No envía ningún dato del usuario.
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV="$PROJECT_ROOT/.venv"
CACHE_DIR="$PROJECT_ROOT/.cache"       # cachés controladas dentro del proyecto
MODELS_DIR="$PROJECT_ROOT/models"
MANIFEST="$PROJECT_ROOT/MODEL_MANIFEST.json"
BACKEND="$PROJECT_ROOT/backend"

USE_CUDA=0
WITH_MODELS=0
EXPERIMENTAL=0
for arg in "$@"; do
  case "$arg" in
    --gpu) USE_CUDA=1 ;;
    --with-models) WITH_MODELS=1 ;;
    --experimental-models) WITH_MODELS=1; EXPERIMENTAL=1 ;;
    -h|--help) grep '^#' "$0" | head -30; exit 0 ;;
    *) echo "Flag desconocido: $arg"; exit 1 ;;
  esac
done

log()  { printf '\n\033[1;36m[setup]\033[0m %s\n' "$*"; }
fail() { printf '\n\033[1;31m[ERROR]\033[0m %s\n' "$*" >&2; exit 1; }

# --- 1. Python -------------------------------------------------------------
PY=""
for cand in python3.12 python3.11 python3; do
  if command -v "$cand" >/dev/null 2>&1; then
    ver="$("$cand" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    maj="${ver%%.*}"; min="${ver##*.}"
    if [ "$maj" -eq 3 ] && [ "$min" -ge 10 ] && [ "$min" -lt 13 ]; then PY="$cand"; break; fi
  fi
done
[ -n "$PY" ] || fail "Se requiere Python 3.10–3.12 (recomendado 3.11). Instalá una versión compatible."
log "Python: $PY ($($PY -c 'import sys; print(sys.version.split()[0])'))"

# --- 2. Virtualenv ----------------------------------------------------------
if [ ! -d "$VENV" ]; then
  log "Creando virtualenv en .venv/"
  "$PY" -m venv "$VENV" || fail "No se pudo crear el venv (¿falta python3-venv?)"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
export PIP_DISABLE_PIP_VERSION_CHECK=1
python -m pip install --quiet --upgrade pip

# --- 3. PyTorch (fuente oficial) --------------------------------------------
mkdir -p "$CACHE_DIR"/{torch,huggingface,demucs,ffmpeg} "$MODELS_DIR"
export TORCH_HOME="$CACHE_DIR/torch"
export HF_HOME="$CACHE_DIR/huggingface"

if [ "$USE_CUDA" = "1" ]; then
  log "Instalando PyTorch con CUDA 12.4 (fuente oficial download.pytorch.org)"
  pip install --quiet torch torchaudio --index-url https://download.pytorch.org/whl/cu124
else
  log "Instalando PyTorch CPU (fuente oficial download.pytorch.org)"
  pip install --quiet torch torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# --- 4. Dependencias backend -------------------------------------------------
log "Instalando dependencias del backend (pyproject.toml)"
pip install --quiet -e "$BACKEND"
[ -f "$BACKEND/requirements.lock" ] && pip install --quiet -r "$BACKEND/requirements.lock"

python - <<'EOF'
import torch, demucs, fastapi, soundfile  # noqa: F401
print(f"  torch {torch.__version__} | cuda disponible: {torch.cuda.is_available()}")
print("  demucs/fastapi/soundfile importan correctamente")
EOF

# --- 5. FFmpeg ---------------------------------------------------------------
if command -v ffmpeg >/dev/null 2>&1; then
  log "FFmpeg presente: $(ffmpeg -version | head -1 | cut -d' ' -f3)"
else
  log "AVISO: FFmpeg no encontrado en PATH. Demucs lo necesita para mp3/m4a/ogg."
  log "  Linux: instalá tu paquete de ffmpeg, o descargá el build estático oficial:"
  log "    https://johnvansickle.com/ffmpeg/  (copialo a $CACHE_DIR/ffmpeg/)"
  log "  macOS: brew install ffmpeg"
  log "  Windows: ver scripts/setup.ps1 (gyan.dev / chocolatey)."
fi

# --- 6. Modelos (solo con flag explícito: nunca descarga silenciosa) ---------
if [ "$WITH_MODELS" = "1" ]; then
  log "Descarga EXPLÍCITA de modelos (consentimiento otorgado vía flag)"
  python "$SCRIPT_DIR/download_models.py" $([ "$EXPERIMENTAL" = "1" ] && echo "--include-experimental")
else
  log "Sin descarga de modelos (agregá --with-models para descargarlos ahora,"
  log "o dejá que la app los pida explícitamente desde /api/models/install)."
fi

# --- 7. Resumen ---------------------------------------------------------------
cat <<EOF

============================================================
✔ Setup completo.
  Entorno:        $VENV
  Cachés:         $CACHE_DIR (torch/hf/demucs redirigidas, nada fuera del proyecto)
  Modelos:        $MODELS_DIR + caché interna de demucs (redirigida a .cache/demucs)
  GPU:            ${USE_CUDA:+CUDA solicitada}$( [ "$USE_CUDA" = "0" ] && echo "modo CPU" )
  Fuentes:        docs/MODEL_SOURCES.md (URLs y SHA-256 verificados)
Arrancá con:      ./scripts/start.sh
============================================================
EOF
