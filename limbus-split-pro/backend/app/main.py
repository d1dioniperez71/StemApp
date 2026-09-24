"""FastAPI app — Limbus Split Pro (edición local, privada).

Arrancar SOLO con: uvicorn app.main:app --host 127.0.0.1
(host fijado en settings; el bind a 0.0.0.0 está prohibido por diseño.)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import upload, separate, mixer, models_api
from app.config import settings

app = FastAPI(
    title="Limbus Split Pro",
    version="0.1.0",
    description="Separación de stems con IA, 100% local. Sin telemetría.",
)

# CORS: solo orígenes locales del frontend de desarrollo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(separate.router, prefix="/api")
app.include_router(mixer.router, prefix="/api")
app.include_router(models_api.router, prefix="/api")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "bind": f"{settings.host}:{settings.port}",
        "private": settings.host == "127.0.0.1",
    }
