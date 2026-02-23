# SIMPLE START - Just run backend and frontend for live data

Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "  Starting EnerSight Live Data Demo  " -ForegroundColor Green
Write-Host "======================================`n" -ForegroundColor Cyan

# Start Backend
Write-Host "1. Starting Backend Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit -Command cd '$PWD'; Write-Host 'Backend Server (Port 8000)' -ForegroundColor Green; .\venv\Scripts\python -m uvicorn backend.main:app --reload --port 8000"

Start-Sleep -Seconds 3

# Start Frontend (check if already running)
$frontendRunning = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue

if (-not $frontendRunning) {
    Write-Host "2. Starting Frontend Server..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit -Command cd '$PWD\frontend'; Write-Host 'Frontend Server (Port 3000)' -ForegroundColor Blue; npm run dev"
} else {
    Write-Host "2. Frontend already running!" -ForegroundColor Green
}

Write-Host "`n======================================" -ForegroundColor Green
Write-Host "  Servers Starting!                  " -ForegroundColor Green
Write-Host "======================================`n" -ForegroundColor Green

Write-Host "Wait 60 seconds for backend to fully load..." -ForegroundColor Yellow
Write-Host "Then open: http://localhost:3000`n" -ForegroundColor Cyan

Write-Host "Opening browser in 65 seconds..." -ForegroundColor Gray
Start-Sleep -Seconds 65
Start-Process "http://localhost:3000"

Write-Host "Done!`n" -ForegroundColor Green
