# Fuentes primarias de modelos — investigación verificada

Fecha de verificación: **2026-09-24**. Todas las URLs fueron consultadas directamente
y los hashes SHA-256 fueron calculados descargando los archivos completos desde la
fuente primaria (no copiados de terceros).

## Etapa 1 — Demucs v4 `htdemucs_ft` (separación base 4 stems)

- **Repositorio / código:** https://github.com/facebookresearch/demucs (main)
- **Paquete PyPI:** `demucs` 4.0.1 → probado también con 4.1.0
- **Licencia:** CC BY-NC 4.0 (código MIT; pesos no comerciales) — LICENSE del repo
- **Definición del bag (fuente primaria):**
  `demucs/remote/htdemucs_ft.yaml` → modelos `f7e0c4bc, d12395a8, 92cfc3b6, 04573f0d`
- **URL base de pesos:** `https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/`
- **Listado oficial:** `demucs/remote/files.txt` (todos los checkpoints existentes;
  los 4 anteriores figuran activos, sin marca REMOVED)

### SHA-256 verificados por descarga completa (cada ~80.5 MB)

| Checkpoint | URL | SHA-256 |
|---|---|---|
| f7e0c4bc-ba3fe64a.th | dl.fbaipublicfiles.com/demucs/hybrid_transformer/f7e0c4bc-ba3fe64a.th | `ba3fe64ae8ef66ac9a4857222ce48efbdc5eb3ad375cb79dd13debee5aaa4066` |
| d12395a8-e57c48e6.th | …/d12395a8-e57c48e6.th | `e57c48e6b0e38af4f7118d7bd08c49f0a0c0edf7d09143bdd902ea0d237303e6` |
| 92cfc3b6-ef3bcb9c.th | …/92cfc3b6-ef3bcb9c.th | `ef3bcb9c8b40d14ae5d51b6db2587339cc12c6b77c0be151ce6d69002e087bf2` |
| 04573f0d-f3cf25b2.th | …/04573f0d-f3cf25b2.th | `f3cf25b222c4eed7cd49dd8b2c9597d50c18bd154090f7b919cfa5f93cf22c49` |

Nota: la convención de nombres de Meta es `<sig>-<sha256[:8]>.th`; en los 4 casos el
prefijo coincide con los primeros 8 hex-dígitos del SHA-256 real calculado aquí, lo
que corrobora la integridad de la fuente.

## Etapa 2 — De-reverb de voz: Mel-Band Roformer (anvuew)

**Hallazgo que actualiza el manifiesto:** SÍ existe un modelo público entrenado
específicamente para de-reverb de voz musical, con métricas SDR publicadas y uso
activo en la comunidad (ZFTurbo/Music-Source-Separation-Training, UVR). La calidad
"profesional" sigue siendo dependiente del material: se mantiene etiqueta
EXPERIMENTAL hasta validación auditiva local.

- **Checkpoint (HF):** https://huggingface.co/anvuew/dereverb_mel_band_roformer
- **Código de inferencia:** https://github.com/ZFTurbo/Music-Source-Separation-Training
- **Licencia:** GPL-3.0 (declarada en la tarjeta del modelo). Implicancia: binario
  de uso privado OK; si algún día se distribuye, las obligaciones GPL aplican.
- **Base arquitectónica:** fine-tune de KimberleyJSN/melbandroformer (separación
  vocal/instrumental), adaptado a de-reverb.
- **Pesos disponibles (verificados en el árbol del repo HF):**
  - `dereverb_mel_band_roformer_anvuew_sdr_19.1729.ckpt` (SDR 19.17 reportada)
  - `dereverb_mel_band_roformer_less_aggressive_anvuew_sdr_18.8050.ckpt`
  - `dereverb_mel_band_roformer_mono_anvuew_sdr_20.4029.ckpt` (mayor SDR pero
    fuerza mono: puede dañar voces estéreo/overdubbed — elegir según caso)
- **Limitaciones documentadas por el autor (README del modelo):**
  - Entrenado con dry vocals mono → riesgo en coros/pistas estéreo.
  - Los dos primeros checkpoints tienen un bug de alineación reverb/voz en
    entrenamiento (commit 0ca5691 de ZFTurbo/MSS), lo que paradójicamente les da
    cierta capacidad de quitar residuos y armonías no centrales.
- **SHA-256:** `PENDIENTE_VERIFICACION_LOCAL` — el script `setup.sh --with-models`
  lo calcula tras la descarga y lo escribe en MODEL_MANIFEST.json.

## Etapa 3 — Lead vs backing vocals

**Estado: NOT_FOUND_VERIFIED (confirmado en esta investigación).**

Búsquedas realizadas (2026-09-24):
- HuggingFace API `search=backing vocals` → 0 resultados de modelos de separación.
- Repositorios UVR (Anjok07/ultimatevocalremovergui): ofrece "Instrument Only",
  karaoke y 6-stems (Demucs v4 `htdemucs_6s`: incluye *piano/guitar* pero NO
  lead/backing); no publica un modelo lead-vs-backing con documentación ni métricas.
- Literatura académica: no hay checkpoints públicos reproducibles con calidad
  profesional para esta tarea específica sobre música mezclada.

Decisión honesta: la etapa permanece deshabilitada; la UI debe informarlo.
Candidato futuro a evaluar: `zassq/singing-voice-separation` (separación de voz
cantada, contexto distinto; requiere validación antes de prometer nada).

## Etapa 5 — BSRNN (dos fuentes primarias distintas, no confundir)

### 5a. ByteDance/Raveseed BSRNN (speech enhancement, 16 kHz)
- **Paper:** "BSRNN: Band-Split RNN for Advanced Speech Enhancement" (Interspeech 2023)
- **Código:** https://github.com/bytedance/BRSLM
- **Licencia:** Apache-2.0 (LICENSE del repo)
- ⚠️ Es para **habla** a 16 kHz, NO para música a 44.1 kHz. No apto como refinador
  vocal de stems musicales. Descartado para el pipeline musical.

### 5b. crlandsc BSRNN (música, trained on MUSDB18-HQ)
- **Checkpoints (HF):** https://huggingface.co/crlandsc/bsrnn-vocals (+ `-drums`,
  `-bass`, `-other`)
- **Código de referencia:** derivado de https://github.com/bytedance/music_source_separation
  (Apache-2.0)
- **Archivo:** `vocals.ckpt` (~519.8 MB), formato Lightning
- **⚠️ Licencia de los pesos: NO DECLARADA** en la tarjeta del modelo (verificado:
  `cardData` solo tiene tags). El código es Apache-2.0, pero los checkpoints están
  entrenados con MUSDB18-HQ (datos no comerciales). **No integrar por defecto**
  hasta resolver el estatus legal; queda EXPERIMENTAL/opt-in explícito.
- **SHA-256:** a verificar en descarga local (el script lo registra).

## Requisitos de red para setup

El instalador necesita alcanzar:
- `pypi.org` / `files.pythonhosted.org` (dependencias Python)
- `download.pytorch.org` (builds de torch CPU/CUDA)
- `dl.fbaipublicfiles.com` (pesos Demucs)
- `huggingface.co` (pesos de-reverb/BSRNN opcionales)
- ffmpeg: se usa el del sistema si existe; si no, build estático de
  johnvansickle.com (Linux) o gyan.dev/chocolatey (Windows).
