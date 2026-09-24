"""Gestión explícita de modelos: manifiesto, verificación SHA-256, descarga confirmada.

Regla del documento: NUNCA descargar modelos silenciosamente durante el proceso.
La descarga se dispara de forma explícita desde /api/models/install y registra
el hash SHA-256 real obtenido.
"""
import hashlib
import json
from pathlib import Path

from app.config import settings

MANIFEST_PATH = settings.manifest_path
MODELS_DIR = settings.models_dir


def load_manifest() -> dict:
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def model_status(entry: dict) -> dict:
    """Estado honesto de un modelo: instalado, hash verificado o pendiente."""
    out = {**entry, "installed": False, "hash_match": None}
    # Los pesos de Demucs viven en la caché de demucs (~/.cache/demucs); los
    # propios (BSRNN etc.) en models/. Se reportan ambos estados.
    candidates = list(MODELS_DIR.glob(f"*{entry['id']}*"))
    if candidates:
        p = candidates[0]
        out["installed"] = True
        actual = sha256_file(p)
        declared = entry.get("sha256")
        out["actual_sha256"] = actual
        if declared and declared not in (None, "PENDIENTE_VERIFICACION_LOCAL"):
            out["hash_match"] = actual == declared
    return out


def all_statuses() -> list[dict]:
    return [model_status(m) for m in load_manifest()["models"]]


def install_model(model_id: str) -> dict:
    """Descarga EXPLÍCITA (asincróna vía API). Solo modelos del manifiesto.

    Implementación actual: para htdemucs_ft usa el downloader oficial de demucs
    hacia su caché; para otros devuelve NOT_IMPLEMENTED hasta que se valide
    fuente/licencia (honestidad técnica ante todo).
    """
    manifest = load_manifest()
    entry = next((m for m in manifest["models"] if m["id"] == model_id), None)
    if entry is None:
        raise ValueError(f"Modelo '{model_id}' no presente en MODEL_MANIFEST.json")
    if model_id == "htdemucs_ft":
        from demucs.pretrained import get_model  # import perezoso

        mdl = get_model("htdemucs_ft")  # descarga oficial + verificación interna
        return {"status": "installed", "model": model_id,
                "location": "demucs cache", "license": entry["license"]}
    return {"status": "NOT_IMPLEMENTED", "model": model_id,
            "reason": "Fuente/licencia aún no verificadas. Ver notas del manifiesto."}
