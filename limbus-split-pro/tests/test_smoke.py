"""Smoke tests: honestidad del pipeline y config privada. No requieren pesos."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient
from app.main import app
from app.config import settings


def test_bind_is_local_only():
    assert settings.host == "127.0.0.1"


def test_health_and_models_endpoints():
    client = TestClient(app)
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["private"] is True
    r = client.get("/api/models")
    assert r.status_code == 200
    statuses = {m["id"]: m["status"] for m in r.json()["models"]}
    # Honestidad: lead/backing declarado NOT_FOUND_VERIFIED en el manifiesto
    assert any("NOT_FOUND" in s or "EXPERIMENTAL" in s or "VERIFIED" in s
               for s in statuses.values())


def test_vocals_split_refuses_to_simulate():
    from app.engine import vocals_split
    import pytest
    with pytest.raises(RuntimeError):
        vocals_split.split_lead_backing(Path("x.wav"), Path("out"))
