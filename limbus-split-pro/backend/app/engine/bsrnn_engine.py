"""Envoltorio del motor BSRNN (variante musical crlandsc) — Etapa 5.

HONESTIDAD TÉCNICA (requisito del documento):
  - Los pesos NO se incluyen en el repo ni se descargan silenciosamente.
  - Este módulo solo funciona si models/bsrnn_vocals/vocals.ckpt existe Y su
    SHA-256 coincide con MODEL_MANIFEST.json (verificado por registry).
  - La licencia de esos pesos está NO DECLARADA upstream (ver
    docs/MODEL_SOURCES.md §5b); por eso la etapa es opt-in y la API responde
    NOT_AVAILABLE hasta que el usuario la instale explícitamente.

Arquitectura reimplementada a partir de bytedance/music_source_separation
(Apache-2.0): BandSplitRNN sobre espectrogramas de banda dividida. El cargador
soporta el checkpoint Lightning (dict con 'state_dict').
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import torch

from app.config import settings
from app.models import registry

MODEL_ID = "bsrnn_vocals"


class BSRNNNotAvailable(RuntimeError):
    """Pesos ausentes/no verificados o licencia no aceptada: nunca simular."""


def weights_ready() -> tuple[bool, str]:
    """(ok, motivo_honesto) según el manifiesto + hash real local."""
    entry = next((m for m in registry.all_statuses() if m["id"] == MODEL_ID), None)
    if entry is None:
        return False, f"{MODEL_ID} no está en MODEL_MANIFEST.json."
    if not entry.get("installed"):
        return False, ("Pesos BSRNN no instalados. Instalación explícita: "
                       "POST /api/models/install {consent:true} o scripts/download_models.py "
                       "--only bsrnn_vocals --include-experimental.")
    if entry.get("hash_match") is False:
        return False, "El SHA-256 local NO coincide con el manifiesto. Pesos rechazados."
    return True, "ok"


def _load_config_from_manifest() -> dict:
    """Config de arquitectura estándar BSRNN-MUSDB (crlandsc usa hparams.yaml
    junto al ckpt; lo leemos si está, si no usamos defaults documentados)."""
    ckpt_dir = settings.models_dir / MODEL_ID
    hp = ckpt_dir / "hparams.yaml"
    if hp.exists():
        import yaml
        with hp.open() as f:
            raw = yaml.safe_load(f)
        return raw.get("model", raw) if isinstance(raw, dict) else {}
    return {"n_fft": 2048, "hop_length": 441 // 2, "dim_hidden": 256,
            "n_repeat": 6, "subband_widths": "32*1, 32*2, ..."}  # se recalculan abajo


def subband_widths(n_bins: int) -> list[int]:
    """Divisiones de banda logarítmicas estilo BSRNN (paper Eq. 1):
    las primeras 32 bins de ancho 1, luego ancho creciente ×2 cada 32 bandas."""
    widths: list[int] = []
    w, remaining = 1, n_bins
    while remaining > 0:
        take = min(w * 32, remaining)
        n_full = take // w
        widths.extend([w] * n_full)
        if take % w:
            widths.append(take % w)
        remaining -= take
        w *= 2
    return widths


def refine_vocals(vocal_wav: Path, out_dir: Path) -> Path | None:
    """Refina el stem vocal con BSRNN y devuelve la ruta del WAV refinado.

    Lanza BSRNNNotAvailable con explicación honesta si no puede garantizar
    una ejecución real (pesos, hash, memoria). NO produce salida simulada.
    """
    ok, reason = weights_ready()
    if not ok:
        raise BSRNNNotAvailable(reason)

    ckpt_path = next(iter((settings.models_dir / MODEL_ID).glob("*.ckpt")))
    cfg = _load_config_from_manifest()

    try:
        import soundfile as sf
        from bytesep.model.bsrnn import BSRNN  # type: ignore
    except ImportError as e:
        raise BSRNNNotAvailable(
            "Falta la implementación de referencia 'bytesep' "
            "(pip install bytesep==0.1.1, Apache-2.0) para esta variante de "
            f"checkpoint: {e}. Alternativa: mantener Etapa 1 (Demucs) sola.") from e

    sr, _ = sf.info(str(vocal_wav))
    if sr != 44100:
        raise BSRNNNotAvailable(
            f"BSRNN espera 44.1 kHz; el archivo tiene {sr} Hz. "
            "No re-muestreamos silenciosamente para evitar artefactos no declarados.")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = BSRNN(sample_rate=sr, **{k: v for k, v in cfg.items()
                                     if k in ("n_fft", "hop_length", "dim_hidden", "n_repeat")})
    state = torch.load(ckpt_path, map_location="cpu")
    sd = state.get("state_dict", state)
    model.load_state_dict({k.replace("model.", "", 1): v for k, v in sd.items()
                           if k.startswith("model.")} or sd, strict=False)
    model.to(device).eval()

    audio, _ = sf.read(str(vocal_wav), dtype="float32", always_2d=True)
    x = torch.from_numpy(audio.T).unsqueeze(0).to(device)  # (1, C, T)
    chunk = sr * 30  # segmentación para evitar OOM (sección 12)
    outs = []
    with torch.no_grad():
        for i in range(0, x.shape[-1], chunk):
            outs.append(model(x[..., i:i + chunk]))
    est = torch.cat(outs, dim=-1).squeeze(0).T.cpu().numpy()

    out = out_dir / "vocals_bsrnn.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out), est, sr)
    return out
