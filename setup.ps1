# EnerSight one-time setup.
# Creates the Python virtual environment and installs backend + frontend dependencies.
# Run from the project root:
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  EnerSight setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# --- 1. Find a compatible Python (3.9-3.11; TensorFlow 2.15 has no 3.12+ wheels) ---
$pyExe = $null
$pyArgs = @()
$prevEAP = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"
foreach ($v in @("3.11", "3.10", "3.9")) {
    & py "-$v" --version *> $null
    if ($LASTEXITCODE -eq 0) { $pyExe = "py"; $pyArgs = @("-$v"); break }
}
if (-not $pyExe) {
    $ver = (& python --version 2>&1 | Out-String).Trim()
    if ($ver -match "Python 3\.(9|10|11)\.") {
        $pyExe = "python"; $pyArgs = @()
    } elseif ($ver -match "Python 3\.") {
        $pyExe = "python"; $pyArgs = @()
        Write-Host "WARNING: found '$ver'. TensorFlow 2.15 only has wheels for Python 3.9-3.11." -ForegroundColor Yellow
        Write-Host "         Install Python 3.11 (https://www.python.org/downloads/) and re-run; setup will pick it up via 'py -3.11'." -ForegroundColor Yellow
    }
}
$ErrorActionPreference = $prevEAP
if (-not $pyExe) {
    Write-Host "ERROR: Python not found. Install Python 3.11 from https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "       and tick 'Add python.exe to PATH' during install, then re-run this script." -ForegroundColor Red
    exit 1
}
Write-Host "Using Python: $pyExe $($pyArgs -join ' ')" -ForegroundColor Gray

# --- 2. Create venv + install backend deps ---
if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment (.\venv) ..." -ForegroundColor Yellow
    & $pyExe @pyArgs -m venv venv
} else {
    Write-Host "Virtual environment already exists - reusing it." -ForegroundColor Gray
}
$venvPy = ".\venv\Scripts\python.exe"
Write-Host "Upgrading pip ..." -ForegroundColor Yellow
& $venvPy -m pip install --upgrade pip
Write-Host "Installing Python dependencies (TensorFlow is large - this can take several minutes) ..." -ForegroundColor Yellow
& $venvPy -m pip install -r requirements.txt

# --- 3. Node.js + frontend deps ---
Write-Host "Checking Node.js ..." -ForegroundColor Yellow
$node = $null
$prevEAP = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"
$node = (& node --version 2>&1 | Out-String).Trim()
$ErrorActionPreference = $prevEAP
if (-not $node -or $node -notmatch "^v\d+") {
    Write-Host "ERROR: Node.js not found. Install Node 20+ from https://nodejs.org and re-run." -ForegroundColor Red
    exit 1
}
$nodeMajor = [int]($node.TrimStart('v').Split('.')[0])
if ($nodeMajor -lt 20) {
    Write-Host "WARNING: Node $node found, but Next.js 16 needs Node 20+. Frontend may fail to start." -ForegroundColor Yellow
} else {
    Write-Host "Node $node" -ForegroundColor Gray
}
Write-Host "Installing frontend dependencies (npm install) ..." -ForegroundColor Yellow
npm --prefix frontend install

# --- 4. Ensure env files exist ---
if (-not (Test-Path ".\.env")) {
    if (Test-Path ".\.env.development") {
        Copy-Item ".\.env.development" ".\.env"
        Write-Host "Created .env from .env.development" -ForegroundColor Gray
    } elseif (Test-Path ".\.env.example") {
        Copy-Item ".\.env.example" ".\.env"
        Write-Host "Created .env from .env.example - FILL IN SECRETS before starting." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Start the app with:" -ForegroundColor Green
Write-Host "    powershell -ExecutionPolicy Bypass -File .\start.ps1" -ForegroundColor White
Write-Host ""
