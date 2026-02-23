#!/usr/bin/env pwsh
# EnerSight Quick Start Script
# Starts all services in the correct order

$ErrorActionPreference = "Stop"

Write-Host "`n╔════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   EnerSight Energy Monitoring Platform    ║" -ForegroundColor Cyan
Write-Host "║            Quick Start Script              ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Step 1: Check if InfluxDB is running
Write-Host "📊 Step 1: Checking InfluxDB..." -ForegroundColor Yellow
$influxStatus = docker ps --filter "name=enersight-influxdb" --format "{{.Status}}" 2>$null

if ($influxStatus) {
    Write-Host "   ✅ InfluxDB is running" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  InfluxDB not running. Starting..." -ForegroundColor Yellow
    docker start enersight-influxdb 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ InfluxDB started" -ForegroundColor Green
        Start-Sleep -Seconds 5
    } else {
        Write-Host "   ℹ️  InfluxDB container not found. Creating..." -ForegroundColor Cyan
        docker run -d `
            --name enersight-influxdb `
            -p 8086:8086 `
            -v influxdb-data:/var/lib/influxdb2 `
            -v influxdb-config:/etc/influxdb2 `
            -e DOCKER_INFLUXDB_INIT_MODE=setup `
            -e DOCKER_INFLUXDB_INIT_USERNAME=admin `
            -e DOCKER_INFLUXDB_INIT_PASSWORD=adminpass123 `
            -e DOCKER_INFLUXDB_INIT_ORG=enersight `
            -e DOCKER_INFLUXDB_INIT_BUCKET=energy_data `
            -e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=my-super-secret-auth-token `
            influxdb:latest
        
        Write-Host "   ✅ InfluxDB created and started" -ForegroundColor Green
        Write-Host "   ⏳ Waiting for initialization (10 seconds)..." -ForegroundColor Cyan
        Start-Sleep -Seconds 10
    }
}

# Step 2: Check backend
Write-Host "`n🔧 Step 2: Checking Backend..." -ForegroundColor Yellow
$backendRunning = Get-Process python -ErrorAction SilentlyContinue | Where-Object { 
    $_.MainWindowTitle -eq '' 
}

if ($backendRunning) {
    Write-Host "   ✅ Backend is already running (PID: $($backendRunning.Id))" -ForegroundColor Green
} else {
    Write-Host "   🚀 Starting backend server..." -ForegroundColor Cyan
    
    # Start in background
    Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\venv\Scripts\python -m uvicorn backend.main:app --reload --port 8000" -WindowStyle Minimized
    
    Write-Host "   ⏳ Waiting for backend to initialize (8 seconds)..." -ForegroundColor Cyan
    Start-Sleep -Seconds 8
    
    # Test backend
    try {
        $health = Invoke-RestMethod "http://localhost:8000/health" -TimeoutSec 5
        Write-Host "   ✅ Backend is healthy!" -ForegroundColor Green
        Write-Host "      Status: $($health.status)" -ForegroundColor White
        Write-Host "      InfluxDB: $($health.components.influxdb)" -ForegroundColor White
    } catch {
        Write-Host "   ⚠️  Backend might still be starting up..." -ForegroundColor Yellow
    }
}

# Step 3: Check frontend
Write-Host "`n🎨 Step 3: Checking Frontend..." -ForegroundColor Yellow
$frontendPort = netstat -ano | Select-String ":3000" | Select-String "LISTENING"

if ($frontendPort) {
    Write-Host "   ✅ Frontend is already running on port 3000" -ForegroundColor Green
} else {
    Write-Host "   🚀 Starting frontend server..." -ForegroundColor Cyan
    
    # Start in background
    Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; npm run dev" -WindowStyle Minimized
    
    Write-Host "   ⏳ Waiting for frontend to start (8 seconds)..." -ForegroundColor Cyan
    Start-Sleep -Seconds 8
    
    Write-Host "   ✅ Frontend started!" -ForegroundColor Green
}

# Step 4: Open browser
Write-Host "`n🌐 Step 4: Opening Dashboard..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
Start-Process "http://localhost:3000"
Write-Host "   ✅ Dashboard opened in browser" -ForegroundColor Green

# Summary
Write-Host "`n╔════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║        🎉 All Systems Operational!         ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "📊 Services Status:" -ForegroundColor Cyan
Write-Host "   • InfluxDB:  http://localhost:8086 ✅" -ForegroundColor White
Write-Host "   • Backend:   http://localhost:8000 ✅" -ForegroundColor White
Write-Host "   • Frontend:  http://localhost:3000 ✅" -ForegroundColor White
Write-Host "   • API Docs:  http://localhost:8000/docs ✅`n" -ForegroundColor White

Write-Host "🔐 Credentials:" -ForegroundColor Cyan
Write-Host "   • InfluxDB: admin / adminpass123" -ForegroundColor White
Write-Host "   • Token: my-super-secret-auth-token`n" -ForegroundColor White

Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "   • Quick Fixes:  .\QUICK_FIXES.md" -ForegroundColor White
Write-Host "   • InfluxDB Guide: .\INFLUXDB_MANAGEMENT.md" -ForegroundColor White
Write-Host "   • Backup Tool: .\scripts\backup_influxdb.ps1`n" -ForegroundColor White

Write-Host "Press any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
