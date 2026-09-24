"""Mixer: la mezcla ocurre en el navegador (Web Audio API).

Este endpoint solo exporta la mezcla final recibida del frontend a WAV,
para que el backend nunca invente una mezcla que el usuario no escuchó.
"""
import base64

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings

router = APIRouter(tags=["mixer"])


class ExportRequest(BaseModel):
    job_id: str
    mix_wav_b64: str  # WAV renderizado por el mezclador del navegador


@router.post("/export")
def export_mix(req: ExportRequest):
    try:
        data = base64.b64decode(req.mix_wav_b64)
    except Exception:
        raise HTTPException(400, "Base64 inválido")
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise HTTPException(400, "El payload no es un WAV válido")
    out = settings.output_dir / req.job_id / "final_mix.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    return {"path": str(out.relative_to(settings.output_dir)), "bytes": len(data)}
