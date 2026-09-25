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
        from app.engine.demucs_engine import separate as demucs_separate
        stems = demucs_separate(job.source_path, out_dir / "demucs")
        for stem, p in stems.items():
            job.stems[stem] = str(p.relative_to(settings.output_dir))

    loop = asyncio.get_event_loop()
    job.emit(type="progress", value=0.05)
    await loop.run_in_executor(None, _sync)


async def _run_bsrnn(job: SeparationJob, out_dir: Path):
    """Refinamiento vocal con BSRNN (etapa 5, opt-in).

    Delega en app.engine.bsrnn_engine, que exige pesos instalados y verificados
    por SHA-256 + licencia resuelta; si falta algo, lanza error accionable
    (nunca simula resultados).
    """
    from app.engine.bsrnn_engine import refine_vocals, weights_ready
    ok, why = weights_ready()
    if not ok:
        raise RuntimeError(f"Etapa 5 (BSRNN) no disponible: {why}")
    vocals = job.stems.get("vocals")
    if not vocals:
        raise RuntimeError("Etapa 5 requiere el stem 'vocals' de la etapa 1.")
    out = await asyncio.get_event_loop().run_in_executor(
        None, refine_vocals, settings.output_dir / vocals, out_dir / "bsrnn")
    if out is None:
        raise RuntimeError("BSRNN devolvió un resultado vacío; revisar pesos/log.")
    job.stems["vocals_bsrnn"] = str(out.relative_to(settings.output_dir))


def create_job(source_path: Path, stages: Optional[list[int]] = None) -> SeparationJob:
    job = SeparationJob(job_id=uuid.uuid4().hex[:12], source_path=source_path,
                        stages_enabled=stages or [1, 5])
    JOBS[job.job_id] = job
    asyncio.create_task(run_job(job))
    return job
