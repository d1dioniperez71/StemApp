"""Etapa 3 — Lead vs backing vocals.

ESTADO OFICIAL: NOT_FOUND_VERIFIED (investigación del 2026-09-24 documentada en
docs/MODEL_SOURCES.md §Etapa 3). No existe un modelo público fiable para esta
tarea sobre música mezclada; por lo tanto este módulo DELIBERADAMENTE no ofrece
ninguna funcionalidad simulada (ni heurísticas de paneo/pitch presentadas como IA).

La API responde 501 con el motivo completo, y la UI lo muestra tal cual.
Cuando aparezca un candidato verificable, se implementará aquí siguiendo el
mismo patrón que dereverb.py (pesos + hash + licencia verificados antes de
ejecutar nada).
"""
from __future__ import annotations

REASON = (
    "Separación lead/backing vocals no disponible: tras buscar en fuentes "
    "primarias (HuggingFace, repositorios UVR, literatura) el 2026-09-24 no se "
    "encontró ningún modelo público con calidad profesional reproducible. "
    "No simulamos esta etapa con heurísticas. Detalle: docs/MODEL_SOURCES.md."
)


def split_lead_backing(*_args, **_kwargs):
    raise NotImplementedError(REASON)
