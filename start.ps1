# EnerSight - start backend (uvicorn) and frontend (vite) in two new windows.
# Run from the project root. Requires the venv at .\venv and frontend deps installed.

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Starting EnerSight (native)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "ERROR: venv not found. Run:" -ForegroundColor Red
    Write-Host "  python -m venv venv"
    Write-Host "  .\venv\Scripts\python.exe -m pip install -r requirements.txt"
    exit 1
}
if (-not (Test-Path ".\frontend\node_modules")) {
    Write-Host "ERROR: frontend deps not installed. Run:" -ForegroundColor Red
    Write-Host "  npm --prefix frontend install"
    exit 1
}
if (-not (Test-Path ".\.env")) {
    Write-Host "ERROR: .env missing. Copy from .env.development and fill in your secrets." -ForegroundColor Red
    exit 1
}

$projectRoot = (Get-Location).Path

Write-Host "Starting backend (FastAPI) on http://localhost:8000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$projectRoot'; .\venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000 --host 0.0.0.0"
)

Start-Sleep -Seconds 2

Write-Host "Starting frontend (Vite) on http://localhost:3000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$projectRoot'; npm --prefix frontend run dev"
)

Write-Host ""
Write-Host "Both services launched in new terminal windows." -ForegroundColor Green
Write-Host "  Backend:  http://localhost:8000  (docs: /api/docs)"
Write-Host "  Frontend: http://localhost:3000"
Write-Host ""
Write-Host "Close those windows to stop the services." -ForegroundColor Gray
