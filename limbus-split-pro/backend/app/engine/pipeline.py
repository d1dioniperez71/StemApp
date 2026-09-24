"""Orquestador del pipeline en cascada (5 etapas) con progreso SSE.

Honestidad técnica: las etapas sin modelo verificado (de-reverb, lead/backing,
otros instrumentos) se omiten y se REPORTAN como no disponibles, nunca se
simulan con DSP engañoso presentado como IA.
"""
import asyncio
import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from app.config import settings

JOBS: dict[str, "SeparationJob"] = {}


@dataclass
class SeparationJob:
    job_id: str
    source_path: Path
    stages_enabled: list[int] = field(default_factory=lambda: [1, 5])
    status: str = "queued"          # queued | running | done | error | partial
    progress: float = 0.0
    stage_label: str = ""
    stems: dict[str, str] = field(default_factory=dict)   # nombre -> ruta relativa
    warnings: list[str] = field(default_factory=list)
    events: asyncio.Queue = field(default_factory=asyncio.Queue)

    def emit(self, **kw):
        self.events.put_nowait(kw)


STAGE_HONESTY = {
    2: "Etapa de-reverb: sin modelo público verificado con calidad profesional. Omitida.",
    3: "Etapa lead/backing vocals: experimental, sin modelo fiable. Omitida.",
    4: "Etapa otros instrumentos: solo disponible para categorías con modelo verificado.",
}


async def run_job(job: SeparationJob):
    """Pipeline: Etapa 1 Demucs htdemucs_ft → (2-4 condicionales) → Etapa 5 BSRNN."""
    job.status = "running"
    job.emit(type="status", status="running")
    out_dir = settings.output_dir / job.job_id
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        if 1 in job.stages_enabled:
            job.stage_label = "Etapa 1/5 — Demucs htdemucs_ft (4 stems)"
            job.emit(type="stage", stage=1, label=job.stage_label)
            await _run_demucs(job, out_dir)
            job.progress = 0.7

        for s in (2, 3, 4):
            if s in job.stages_enabled:
                job.warnings.append(STAGE_HONESTY[s])
                job.emit(type="warning", stage=s, message=STAGE_HONESTY[s])

        if 5 in job.stages_enabled and "bsrnn_vocals" not in ():
            # BSRNN requiere pesos verificados; si no están instalados, avisar.
            from app.models.registry import all_statuses
            bsrnn = next((m for m in all_statuses() if m["id"] == "bsrnn_vocals"), None)
            if bsrnn and bsrnn.get("installed"):
                job.stage_label = "Etapa 5/5 — Refinamiento BSRNN"
                job.emit(type="stage", stage=5, label=job.stage_label)
                await _run_bsrnn(job, out_dir)
            else:
                msg = "Etapa 5 omitida: pesos BSRNN no instalados/verificados."
                job.warnings.append(msg)
                job.emit(type="warning", stage=5, message=msg)

        job.progress = 1.0
        job.status = "done" if not job.warnings else "partial"
        job.emit(type="done", status=job.status, stems=job.stems,
                 warnings=job.warnings)
    except Exception as e:  # noqa: BLE001
        job.status = "error"
        job.emit(type="error", message=str(e))


async def _run_demucs(job: SeparationJob, out_dir: Path):
    """Ejecuta demucs en un hilo aparte (inferencia CPU/GPU bloqueante)."""
    def _sync():
        from demucs.separate import main as demucs_main
        demucs_main([
            "-n", settings.demucs_model,
            "-o", str(out_dir / "demucs"),
            "--two-stems", "vocals",
            str(job.source_path),
        ])
        base = out_dir / "demucs" / settings.demucs_model / job.source_path.stem
        for stem in ("vocals", "no_vocals", "drums", "bass", "other"):
            p = base / f"{stem}.wav"
            if p.exists():
                job.stems[stem] = str(p.relative_to(settings.output_dir))

    loop = asyncio.get_event_loop()
    job.emit(type="progress", value=0.05)
    await loop.run_in_executor(None, _sync)


async def _run_bsrnn(job: SeparationJob, out_dir: Path):
    """Refinamiento vocal con BSRNN. Placeholder hasta validar pesos/licencia.

    Se implementará contra ByteDance/music_source_separation cuando los
    checkpoints estén descargados y verificados por hash en models/.
    """
    raise NotImplementedError("BSRNN engine pendiente de pesos verificados.")


def create_job(source_path: Path, stages: Optional[list[int]] = None) -> SeparationJob:
    job = SeparationJob(job_id=uuid.uuid4().hex[:12], source_path=source_path,
                        stages_enabled=stages or [1, 5])
    JOBS[job.job_id] = job
    asyncio.create_task(run_job(job))
    return job
