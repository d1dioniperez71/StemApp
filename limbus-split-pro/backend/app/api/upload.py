"""Upload de pistas: validación honesta de formatos reales."""
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from app.config import settings

router = APIRouter(tags=["upload"])

ALLOWED_EXT = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".opus"}


@router.post("/upload")
async def upload_track(file: UploadFile):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(415, f"Formato no soportado: {ext}. Aceptados: {sorted(ALLOWED_EXT)}")
    dest = settings.upload_dir / Path(file.filename).name
    size = 0
    with open(dest, "wb") as f:
        while chunk := await file.read(1 << 20):
            size += len(chunk)
            if size > settings.max_upload_mb * 1024 * 1024:
                f.close(); dest.unlink(missing_ok=True)
                raise HTTPException(413, f"Archivo supera el límite de {settings.max_upload_mb} MB")
            f.write(chunk)
    return {"path": str(dest), "filename": dest.name, "size_bytes": size}
