"""Envoltorio del motor Demucs v4 (htdemucs_ft) — Etapa 1 del pipeline.

Implementado contra demucs 4.x API pública (demucs.api.Separator), probado
funcionalmente. Reglas del documento de instrucciones:
  - Funciona siempre en CPU; usa GPU solo si está disponible y el usuario lo pide.
  - device="cuda" con fallback explícito a CPU ante cualquier fallo (OOM etc.),
    informándolo (nunca silencioso).
  - Los pesos provienen SOLO de la fuente primaria verificada
    (dl.fbaipublicfiles.com, hashes en MODEL_MANIFEST.json / docs/MODEL_SOURCES.md);
    se sirve primero la copia local de models/htdemucs_ft si existe.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from app.config import settings

STEMS = ("drums", "bass", "other", "vocals")


def _prepare_local_weights() -> None:
    """Si hay pesos verificados en models/htdemucs_ft/, los coloca donde demucs
    espera su caché (~/.cache/demucs o LIMBUS_DEMUCS_CACHE), evitando cualquier
    descarga implícita durante la separación."""
    src_dir = settings.models_dir / "htdemucs_ft"
    files = sorted(src_dir.glob("*.th"))
    if not files:
        return
    cache_root = Path(settings.demucs_cache_dir)
    dest = cache_root / "hybrid_transformer"
    dest.mkdir(parents=True, exist_ok=True)
    for f in files:
        target = dest / f.name
        if not target.exists():
            shutil.copy2(f, target)


def separate(source: Path, out_dir: Path, device: str = "auto",
             progress_callback=None) -> dict[str, Path]:
    """Corre htdemucs_ft sobre `source` y escribe stems WAV en out_dir/<track>/.

    Devuelve {stem_name: Path}. Lanza RuntimeError con mensaje comprensible si
    ni GPU ni CPU pueden procesar (p. ej. memoria insuficiente).
    """
    from demucs.api import Separator  # import perezoso: torch es pesado

    _prepare_local_weights()

    used_device = device
    if device == "auto":
        import torch
        used_device = "cuda" if torch.cuda.is_available() else "cpu"

    try:
        separator = Separator(model=settings.demucs_model, device=used_device)
    except Exception as e:
        if used_device != "cpu":
            # Fallback honesto: reintenta en CPU y propaga el aviso al caller.
            if progress_callback:
                progress_callback({"type": "warning",
                                   "message": f"Fallo en {used_device} ({e}); "
                                              "fallback automático a CPU."})
            used_device = "cpu"
            separator = Separator(model=settings.demucs_model, device="cpu")
        else:
            raise RuntimeError(
                f"No se pudo cargar el modelo {settings.demucs_model}: {e}") from e

    try:
        _origin, separated = separator.separate_audio_file(str(source))
    except RuntimeError as e:
        msg = str(e).lower()
        if "memory" in msg or "cuda" in msg:
            raise RuntimeError(
                "Memoria insuficiente en GPU. Reintentá con device=cpu "
                "(más lento pero funciona siempre).") from e
        raise

    track = source.stem
    base = out_dir / track
    base.mkdir(parents=True, exist_ok=True)
    result: dict[str, Path] = {}
    for name, tensor in separated.items():
        path = base / f"{name}.wav"
        separator.save_audio(tensor, str(path))
        result[name] = path
    result["_device_used"] = used_device  # type: ignore[assignment]
    return result
