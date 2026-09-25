# ============================================================================
# Limbus Split Pro — setup.ps1 (Windows 10/11, objetivo principal)
# Equivalente a scripts/setup.sh. Uso:
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1
#   .\setup.ps1 -GPU
#   .\setup.ps1 -WithModels                # + descarga explícita de modelos
#   .\setup.ps1 -WithModels -ExperimentalModels
# PRIVACIDAD: solo contacta python.org, pypi.org, download.pytorch.org,
# dl.fbaipublicfiles.com, huggingface.co y (ffmpeg) gyan.dev. Ver docs/MODEL_SOURCES.md.
# ============================================================================
param(
    [switch]$GPU,
    [switch]$WithModels,
    [switch]$ExperimentalModels
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ProjectRoot = Split-Path -Parent $Root
$Venv = Join-Path $ProjectRoot ".venv"
$Cache = Join-Path $ProjectRoot ".cache"
$Backend = Join-Path $ProjectRoot "backend"

function Step($msg) { Write-Host "`n[setup] $msg" -ForegroundColor Cyan }
function Die($msg)  { Write-Host "[ERROR] $msg" -ForegroundColor Red; exit 1 }

# --- 1. Python 3.10–3.12 -----------------------------------------------------
$py = $null
foreach ($c in @("python", "py")) {
    try {
        $v = & $c -c "import sys;print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($v) {
            $maj, $min = $v.Split(".") | ForEach-Object { [int]$_ }
            if ($maj -eq 3 -and $min -ge 10 -and $min -lt 13) { $py = $c; break }
        }
    } catch {}
}
if (-not $py) {
    Die "Instalá Python 3.11 desde https://www.python.org/downloads/ (marcar 'Add to PATH') o usá el embeddable (Opción B del documento, sección 11)."
}
Step "Python OK: $py"

# --- 2. Virtualenv ------------------------------------------------------------
if (-not (Test-Path $Venv)) {
    Step "Creando virtualenv en .venv/"
    & $py -m venv $Venv
}
& (Join-Path $Venv "Scripts\Activate.ps1")
python -m pip install --quiet --upgrade pip

# --- 3. PyTorch (fuente oficial) ----------------------------------------------
New-Item -ItemType Directory -Force -Path (Join-Path $Cache "torch"), `
    (Join-Path $Cache "huggingface"), (Join-Path $Cache "demucs"), `
    (Join-Path $Cache "ffmpeg"), (Join-Path $ProjectRoot "models") | Out-Null
$env:TORCH_HOME = Join-Path $Cache "torch"
$env:HF_HOME = Join-Path $Cache "huggingface"

if ($GPU) {
    Step "Instalando PyTorch CUDA 12.4 (download.pytorch.org)"
    pip install --quiet torch torchaudio --index-url https://download.pytorch.org/whl/cu124
} else {
    Step "Instalando PyTorch CPU (download.pytorch.org)"
    pip install --quiet torch torchaudio --index-url https://download.pytorch.org/whl/cpu
}

# --- 4. Backend ----------------------------------------------------------------
Step "Instalando dependencias del backend"
pip install --quiet -e $Backend
if (Test-Path (Join-Path $Backend "requirements.lock")) {
    pip install --quiet -r (Join-Path $Backend "requirements.lock")
}
python -c "import torch, demucs, fastapi, soundfile; print('  torch', torch.__version__, '| cuda:', torch.cuda.is_available())"

# --- 5. FFmpeg -------------------------------------------------------------------
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Step "FFmpeg no encontrado. Opciones:"
    Write-Host "  a) choco install ffmpeg   (si tenés Chocolatey)"
    Write-Host "  b) Descargá el build compartido de https://www.gyan.dev/ffmpeg/builds/"
    Write-Host "     y copiá ffmpeg.exe a $Cache\ffmpeg\ (start.ps1 lo agrega al PATH)"
} else {
    Step "FFmpeg presente: $((Get-Command ffmpeg).Source)"
}

# --- 6. Modelos (explícito, nunca silencioso) ------------------------------------
if ($WithModels -or $ExperimentalModels) {
    Step "Descarga EXPLÍCITA de modelos con verificación SHA-256"
    $args = @((Join-Path $Root "download_models.py"))
    if ($ExperimentalModels) { $args += "--include-experimental" }
    python @args
    if ($LASTEXITCODE -ne 0) { Die "Verificación de modelos falló." }
} else {
    Step "Sin descarga de modelos (agregá -WithModels; o instalalos desde la UI con consentimiento)"
}

Write-Host "`n============================================================"
Write-Host "Setup completo. Arrancá con: .\scripts\start.ps1"
Write-Host "Fuentes primarias y hashes: docs\MODEL_SOURCES.md"
Write-Host "============================================================"
