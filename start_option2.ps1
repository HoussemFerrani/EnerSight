# Option 2: Live Data Simulation - Quick Start Guide

Write-Host "`n=====================================================" -ForegroundColor Cyan
Write-Host "   Option 2: Live Data Simulation - Quick Start" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Cyan

Write-Host "`n📋 What's New:" -ForegroundColor Yellow
Write-Host "   ✅ Real-time data simulator (backend/services/data_simulator.py)"
Write-Host "   ✅ WebSocket endpoint (backend/api/v1/websocket.py)"
Write-Host "   ✅ useWebSocket hook (frontend/src/hooks/useWebSocket.js)"
Write-Host "   ✅ Live data dashboard card with pulsing indicator"
Write-Host "   ✅ Updates every 5 seconds automatically"

Write-Host "`n🚀 Starting Services..." -ForegroundColor Cyan

# Check if InfluxDB is running
Write-Host "`n1️⃣ Checking InfluxDB..." -ForegroundColor Yellow
$influx = docker ps --filter "name=enersight-influxdb" --format "{{.Status}}"
if ($influx -match "Up") {
    Write-Host "   ✅ InfluxDB is running" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Starting InfluxDB..." -ForegroundColor Yellow
    docker start enersight-influxdb
    Start-Sleep -Seconds 3
}

# Start Backend in new window
Write-Host "`n2️⃣ Starting Backend (with WebSocket support)..." -ForegroundColor Yellow
Write-Host "   Opening new terminal window..." -ForegroundColor Gray

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$PWD'; Write-Host '`n🚀 Backend Server with WebSocket Support`n' -ForegroundColor Green; .\venv\Scripts\python -m uvicorn backend.main:app --reload --port 8000"
) -WindowStyle Normal

Write-Host "   ⏳ Waiting for backend to initialize (ML models loading)..." -ForegroundColor Gray
Start-Sleep -Seconds 50

# Test backend
Write-Host "`n   Testing backend..." -ForegroundColor Gray
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5
    if ($health.status) {
        Write-Host "   ✅ Backend is UP and running!" -ForegroundColor Green
    }
} catch {
    Write-Host "   ⚠️  Backend still loading (this is normal on first start)" -ForegroundColor Yellow
    Write-Host "   💡 Check the backend terminal window for progress" -ForegroundColor Gray
}

# Start Frontend in new window  
Write-Host "`n3️⃣ Starting Frontend (with live data display)..." -ForegroundColor Yellow
Write-Host "   Opening new terminal window..." -ForegroundColor Gray

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$PWD\frontend'; Write-Host '`n🎨 Frontend Dev Server`n' -ForegroundColor Blue; npm run dev"
) -WindowStyle Normal

Write-Host "   ⏳ Waiting for frontend to start..." -ForegroundColor Gray
Start-Sleep -Seconds 15

Write-Host "`n=====================================================" -ForegroundColor Green
Write-Host "   🎉 Live Data Simulation is Ready!" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green

Write-Host "`n📊 What to Look For:" -ForegroundColor Yellow
Write-Host "   1. Dashboard should show a pulsing '🟢 Live' indicator" -ForegroundColor White
Write-Host "   2. Purple gradient card at the top with real-time data" -ForegroundColor White
Write-Host "   3. Values update every 5 seconds automatically" -ForegroundColor White
Write-Host "   4. Timestamp updates showing latest data received" -ForegroundColor White

Write-Host "`n🌐 Open Dashboard:" -ForegroundColor Cyan
Write-Host "   http://localhost:3000" -ForegroundColor White

Write-Host "`n🔧 WebSocket Endpoint:" -ForegroundColor Cyan
Write-Host "   ws://localhost:8000/api/v1/ws/energy/live" -ForegroundColor White
Write-Host "   Status: http://localhost:8000/api/v1/energy/live/status" -ForegroundColor White

Write-Host "`n💡 Tips:" -ForegroundColor Yellow
Write-Host "   • Open browser console (F12) to see WebSocket messages" -ForegroundColor Gray
Write-Host "   • '📨 Received:' logs show incoming live data" -ForegroundColor Gray
Write-Host "   • '✅ WebSocket connected' confirms successful connection" -ForegroundColor Gray
Write-Host "   • Data simulates realistic patterns (higher during day)" -ForegroundColor Gray
Write-Host "   • Random spikes occur 5% of the time (for anomaly testing)" -ForegroundColor Gray

Write-Host "`n📁 New Files Created:" -ForegroundColor Cyan
Write-Host "   backend/services/data_simulator.py       - Generates realistic data" -ForegroundColor Gray
Write-Host "   backend/api/v1/websocket.py              - WebSocket endpoint" -ForegroundColor Gray
Write-Host "   frontend/src/hooks/useWebSocket.js       - React WebSocket hook" -ForegroundColor Gray
Write-Host "   (Dashboard.jsx updated with live data card)" -ForegroundColor Gray

Write-Host "`n🎬 Opening Dashboard..." -ForegroundColor Cyan
Start-Sleep -Seconds 3
Start-Process "http://localhost:3000"

Write-Host "`n✅ All services started! Check the dashboard for live updates!`n" -ForegroundColor Green
