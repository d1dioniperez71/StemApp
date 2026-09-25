#!/usr/bin/env python3
"""Descarga/verificación explícita de modelos desde las fuentes primarias del
MODEL_MANIFEST.json. Compartido por setup.sh/setup.ps1 y por la API (/models/install).

Reglas (qwen_stem_instructions.txt):
  - Nunca se ejecuta implícitamente: solo vía --with-models en setup o consent=true.
  - Verifica SHA-256 contra el manifiesto; si el manifiesto dice
    PENDIENTE_VERIFICACION_LOCAL, calcula el hash real y lo escribe en el
    manifiesto local para futuras verificaciones.
  - Descarga atómica (.part -> rename) con progreso en consola.
  - Los pesos de demucs además se copian a models/demucs/ para que
    scripts/start.sh los sirva desde la caché controlada del proyecto.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "MODEL_MANIFEST.json"
MODELS_DIR = PROJECT_ROOT / "models"
PLACEHOLDER = "PENDIENTE_VERIFICACION_LOCAL"
EXPERIMENTAL_IDS = {"dereverb_mel_band_roformer", "bsrnn_vocals"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")

    def report(blocks: int, block_size: int, total: int) -> None:
        if total > 0:
            done = min(blocks * block_size, total)
            pct = done * 100 / total
            sys.stdout.write(f"\r    {dest.name}: {pct:5.1f}% "
                             f"({done/1e6:.1f}/{total/1e6:.1f} MB)")
            sys.stdout.flush()

    req = urllib.request.Request(url, headers={"User-Agent": "LimbusSplitPro-setup/0.1"})
    with urllib.request.urlopen(req) as r, tmp.open("wb") as out:
        shutil.copyfileobj(r, out)
    print()
    tmp.replace(dest)


def verify_or_record(model_dir: Path, w: dict) -> bool:
    """Devuelve True si el archivo existe y coincide (o fue registrado)."""
    local = model_dir / w["file"]
    if not local.exists():
        print(f"  ↓ {w['url']}")
        download(w["url"], local)
    actual = sha256_file(local)
    declared = w.get("sha256")
    if declared in (None, PLACEHOLDER):
        w["sha256"] = actual
        w["sha256_verified_on"] = "local-" + str(__import__("datetime").date.today())
        print(f"  ✚ {w['file']}: hash real registrado {actual[:16]}…")
        return True
    if actual == declared:
        print(f"  ✔ {w['file']}: SHA-256 coincide")
        return True
    print(f"  ✘ {w['file']}: SHA-256 NO COINCIDE\n"
          f"      esperado: {declared}\n      obtenido: {actual}")
    local.unlink()  # no dejar artefacto sospechoso
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--include-experimental", action="store_true",
                    help="Incluye modelos EXPERIMENTAL/opt-in (dereverb, BSRNN).")
    ap.add_argument("--only", nargs="*", metavar="MODEL_ID",
                    help="IDs concretos del manifiesto a instalar.")
    args = ap.parse_args()

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    ok_all = True
    changed = False

    for m in manifest["models"]:
        mid = m["id"]
        if args.only and mid not in args.only:
            continue
        if not args.only and not args.include_experimental and mid in EXPERIMENTAL_IDS:
            print(f"— {mid}: omitido (experimental; usá --include-experimental)")
            continue
        weights = m.get("weights") or []
        if not weights:
            print(f"— {mid}: sin pesos descargables ({m['status']})")
            continue
        print(f"◆ {mid} [{m['license']}]")
        model_dir = MODELS_DIR / mid
        before = json.dumps(weights)
        all_ok = all(verify_or_record(model_dir, w) for w in weights)
        changed |= json.dumps(weights) != before
        ok_all &= all_ok

    if changed:
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                                 encoding="utf-8")
        print("\nMODEL_MANIFEST.json actualizado con los hashes reales verificados.")

    # Sincronizar la caché de demucs con models/demucs para arranque offline
    d = MODELS_DIR / "htdemucs_ft"
    if d.exists():
        target = MODELS_DIR / "demucs" / "hybrid_transformer"
        target.mkdir(parents=True, exist_ok=True)
        for f in d.glob("*.th"):
            if not (target / f.name).exists():
                shutil.copy2(f, target / f.name)

    return 0 if ok_all else 2


if __name__ == "__main__":
    raise SystemExit(main())
