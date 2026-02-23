# QUICK START - Option 2 Live Data
# Run this script to see live data in your dashboard

Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host "   STARTING LIVE DATA DEMO - Option 2                 " -ForegroundColor Cyan
Write-Host "========================================================`n" -ForegroundColor Cyan

Write-Host "WHAT THIS DOES:" -ForegroundColor Yellow
Write-Host "   1. Starts your backend server with WebSocket support" -ForegroundColor White
Write-Host "   2. Backend generates fake energy data every 5 seconds" -ForegroundColor White
Write-Host "   3. Sends it through WebSocket to your browser" -ForegroundColor White
Write-Host "   4. Dashboard displays live updating numbers`n" -ForegroundColor White

Write-Host "WHY YOU NEED THIS:" -ForegroundColor Yellow
Write-Host "   Without backend = No live data (WebSocket server not running)" -ForegroundColor White
Write-Host "   With backend = Dashboard gets real-time updates automatically`n" -ForegroundColor White

Write-Host "========================================================`n" -ForegroundColor Gray

# STEP 1: Start Backend
Write-Host "STEP 1: Starting Backend with Live Data Simulator..." -ForegroundColor Green
Write-Host "        (This provides the WebSocket at ws://localhost:8000)`n" -ForegroundColor Gray

$backendCmd = "cd '$PWD'; Write-Host ''; Write-Host 'BACKEND SERVER - LIVE DATA WEBSOCKET' -ForegroundColor Green; Write-Host ''; Write-Host 'Generating live energy data every 5 seconds...' -ForegroundColor Yellow; Write-Host 'WebSocket: ws://localhost:8000/api/v1/ws/energy/live' -ForegroundColor Cyan; Write-Host ''; .\venv\Scripts\python -m uvicorn backend.main:app --reload --port 8000"

$backendWindow = Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -PassThru -WindowStyle Normal

Write-Host "   Waiting 60 seconds for backend to start (ML models are loading)..." -ForegroundColor Yellow
Write-Host "      This is normal - TensorFlow takes time to initialize`n" -ForegroundColor Gray

# Progress bar simulation
for ($i = 0; $i -le 60; $i++) {
    $percent = [math]::Round(($i / 60) * 100)
    Write-Progress -Activity "Backend Starting..." -Status "$percent% Complete" -PercentComplete $percent
    Start-Sleep -Seconds 1
}
Write-Progress -Activity "Backend Starting..." -Completed

# STEP 2: Test Backend
Write-Host "`nSTEP 2: Testing if backend is responding..." -ForegroundColor Green
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 10
    Write-Host "   Backend is READY!" -ForegroundColor Green
    Write-Host "   Status: $($health.status)" -ForegroundColor White
} catch {
    Write-Host "   Backend needs more time. Check the backend window." -ForegroundColor Yellow
    Write-Host "      Look for: 'Application startup complete'" -ForegroundColor Gray
}

# STEP 3: Check Frontend
Write-Host "`nSTEP 3: Checking Frontend..." -ForegroundColor Green
$frontendPort = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue

if ($frontendPort) {
    Write-Host "   Frontend is already running on port 3000" -ForegroundColor Green
} else {
    Write-Host "   Starting Frontend..." -ForegroundColor Yellow
    
    $frontendCmd = "cd '$PWD\frontend'; Write-Host ''; Write-Host 'FRONTEND DEV SERVER' -ForegroundColor Blue; Write-Host ''; npm run dev"
    $frontendWindow = Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd -PassThru -WindowStyle Normal
    
    Write-Host "   Waiting 15 seconds for frontend to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
}

Write-Host "`n========================================================" -ForegroundColor Green
Write-Host "                    ALL READY!                          " -ForegroundColor Green
Write-Host "========================================================`n" -ForegroundColor Green

Write-Host "OPEN YOUR DASHBOARD:" -ForegroundColor Cyan
Write-Host "   http://localhost:3000`n" -ForegroundColor White

Write-Host "WHAT YOU SHOULD SEE:" -ForegroundColor Yellow
Write-Host "   1. A pulsing green 'Live' badge at the top" -ForegroundColor White
Write-Host "   2. A purple gradient card showing real-time data:" -ForegroundColor White
Write-Host "      - Current Power (updates every 5 seconds)" -ForegroundColor Gray
Write-Host "      - Voltage (fluctuates realistically)" -ForegroundColor Gray
Write-Host "      - Temperature (changes over time)" -ForegroundColor Gray
Write-Host "      - Real-time Cost calculation" -ForegroundColor Gray
Write-Host "   3. Timestamp updating to show 'Last updated: XX:XX:XX'`n" -ForegroundColor White

Write-Host "OPEN BROWSER CONSOLE (F12) TO SEE:" -ForegroundColor Yellow
Write-Host "   - 'Live data connected' - WebSocket connected" -ForegroundColor White
Write-Host "   - 'Received:' - Every 5 seconds with new data" -ForegroundColor White
Write-Host "   - Live data object showing all values`n" -ForegroundColor White

Write-Host "TO STOP:" -ForegroundColor Yellow
Write-Host "   Just close the backend and frontend terminal windows`n" -ForegroundColor White

Write-Host "========================================================`n" -ForegroundColor Gray

Write-Host "Opening dashboard in your browser..." -ForegroundColor Cyan
Start-Sleep -Seconds 2
Start-Process "http://localhost:3000"

Write-Host "Enjoy watching the live data stream!`n" -ForegroundColor Green

