"""Configuración central de Limbus Split Pro (backend).

Reglas del documento de instrucciones:
- El servidor escucha ÚNICAMENTE en 127.0.0.1 (nunca 0.0.0.0).
- No se descargan modelos silenciosamente: la descarga es explícita y gestionada.
"""
from pathlib import Path

from pydantic_settings import BaseSettings

# Raíces del proyecto: limbus-split-pro/
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    host: str = "127.0.0.1"  # por diseño: nunca 0.0.0.0
    port: int = 8317
    upload_dir: Path = PROJECT_ROOT / "uploads"
    output_dir: Path = PROJECT_ROOT / "outputs"
    models_dir: Path = PROJECT_ROOT / "models"
    manifest_path: Path = PROJECT_ROOT / "MODEL_MANIFEST.json"
    max_upload_mb: int = 200
    demucs_model: str = "htdemucs_ft"

    class Config:
        env_prefix = "LIMBUS_"


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.output_dir.mkdir(parents=True, exist_ok=True)
