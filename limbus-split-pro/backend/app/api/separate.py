"""Endpoints de separación + progreso SSE."""
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config import settings
from app.engine.pipeline import JOBS, create_job

router = APIRouter(tags=["separate"])


class SeparateRequest(BaseModel):
    path: str
    stages: list[int] = [1, 5]


@router.post("/separate")
def separate(req: SeparateRequest):
    src = Path(req.path)
    if not src.exists() or settings.upload_dir not in src.resolve().parents and src.resolve().parent != settings.upload_dir.resolve():
        raise HTTPException(400, "Ruta de audio no válida (debe ser un archivo subido).")
    job = create_job(src.resolve(), req.stages)
    return {"job_id": job.job_id}


@router.get("/separate/{job_id}/events")
async def events(job_id: str):
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(404, "Job desconocido")

    async def stream():
        while True:
            ev = await job.events.get()
            yield f"data: {ev}\n\n"
            if ev.get("type") in ("done", "error"):
                break

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.get("/stems/{job_id}/{stem}")
def stem_file(job_id: str, stem: str):
    from fastapi.responses import FileResponse
    job = JOBS.get(job_id)
    if job is None or stem not in job.stems:
        raise HTTPException(404, "Stem no disponible")
    return FileResponse(settings.output_dir / job.stems[stem], filename=f"{stem}.wav")
