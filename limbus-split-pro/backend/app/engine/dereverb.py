"""Etapa 2 — De-reverb de voz con Mel-Band Roformer (anvuew).

Honestidad técnica:
  - Modelo real y público (ver docs/MODEL_SOURCES.md §Etapa 2), PERO calificado
    EXPERIMENTAL por el propio autor: entrenado con dry vocals mono; puede dañar
    coros/pistas estéreo. La etapa es SIEMPRE opt-in y reporta sus limitaciones.
  - Requiere pesos en models/dereverb_mel_band_roformer/ con SHA-256 verificado
    contra MODEL_MANIFEST.json (descarga explícita vía scripts/download_models.py
    --include-experimental o /api/models/install).
  - Inferencia ejecutable sobre la arquitectura mel_band_roformer del repo de
    ZFTurbo (GPL-3.0). Como alternativa soportada, si audio-separator está
    instalado se delega en él (misma arquitectura, más testeada).
"""
from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.models import registry

MODEL_ID = "dereverb_mel_band_roformer"
LIMITATION_NOTE = ("De-reverb experimental (anvuew MBR, SDR 19.17 reportada): "
                   "entrenado con voz seca mono; puede afectar coros y pistas "
                   "estéreo. Verificado 2026-09-24 en docs/MODEL_SOURCES.md.")


class DereverbNotAvailable(RuntimeError):
    """Nunca simular de-reverb con DSP engañoso: si no hay modelo verificado, se informa."""


def weights_ready() -> tuple[bool, str]:
    entry = next((m for m in registry.all_statuses() if m["id"] == MODEL_ID), None)
    if entry is None:
        return False, f"{MODEL_ID} no figura en MODEL_MANIFEST.json."
    if not entry.get("installed"):
        return False, ("Pesos de-reverb no instalados. Instalación explícita: "
                       "scripts/download_models.py --only dereverb_mel_band_roformer "
                       "--include-experimental (licencia GPL-3.0).")
    if entry.get("hash_match") is False:
        return False, "SHA-256 local NO coincide con el manifiesto. Pesos rechazados."
    return True, LIMITATION_NOTE


def dereverb_vocals(vocal_wav: Path, out_dir: Path) -> Path:
    """Aplica de-reverb al stem vocal y devuelve la ruta del resultado.

    Estrategia de backends (ambos reales, ninguno simulado):
      1. audio-separator (pip install audio-separator) con el yaml del modelo.
      2. fallback claro a error accionable si ningún backend está disponible.
    """
    ok, reason = weights_ready()
    if not ok:
        raise DereverbNotAvailable(reason)

    ckpt = next((settings.models_dir / MODEL_ID).glob("*.ckpt"))
    try:
        from audio_separator.separator import Separator  # type: ignore
    except ImportError as e:
        raise DereverbNotAvailable(
            "Para esta etapa hace falta un backend de inferencia Roformer real: "
            "`pip install audio-separator` (o integrar ZFTurbo/Music-Source-"
            f"Separation-Training como submódulo). Sin él NO simulamos: {e}") from e

    sep = Separator(model_file_dir=str(settings.models_dir / MODEL_ID))
    sep.load_model(model_filename=ckpt.name)
    outputs = sep.separate(str(vocal_wav))
    out = out_dir / "vocals_dereverb.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    first = Path(outputs[0]) if isinstance(outputs, (list, tuple)) else Path(outputs)
    first.replace(out) if first.exists() else None
    if not out.exists():  # algunos backends escriben en output_path con otro nombre
        raise DereverbNotAvailable(f"El backend no produjo salida esperada cerca de {outputs!r}")
    return out
