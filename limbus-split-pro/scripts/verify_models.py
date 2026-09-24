#!/usr/bin/env python3
"""Verificación honesta del estado de modelos contra MODEL_MANIFEST.json."""
import sys, json
sys.path.insert(0, "backend")
from app.models.registry import all_statuses
for m in all_statuses():
    flag = "OK" if m["installed"] and m.get("hash_match") is not False else ("INSTALADO(hash pendiente)" if m["installed"] else "NO INSTALADO")
    print(f"[{flag:26s}] {m['id']} (etapa {m['stage']}, licencia: {m['license']})")
