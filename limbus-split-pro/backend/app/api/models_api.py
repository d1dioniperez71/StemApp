"""API de gestión explícita de modelos (manifiesto, estado, descarga confirmada)."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models import registry

router = APIRouter(tags=["models"])


class InstallRequest(BaseModel):
    model_id: str
    consent: bool  # el usuario debe confirmar la descarga y su licencia


@router.get("/models")
def list_models():
    return {"models": registry.all_statuses()}


@router.post("/models/install")
def install(req: InstallRequest):
    if not req.consent:
        raise HTTPException(400, "Se requiere consentimiento explícito (consent=true) para descargar modelos.")
    try:
        return registry.install_model(req.model_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
