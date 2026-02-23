# SUPER SIMPLE - Just start the dashboard (no backend needed!)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Starting Dashboard (Demo Mode)      " -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "This will:" -ForegroundColor Yellow
Write-Host "  - Start the frontend on port 3000" -ForegroundColor White
Write-Host "  - Show LIVE data (browser-generated)" -ForegroundColor White
Write-Host "  - Update every 5 seconds automatically" -ForegroundColor White
Write-Host "  - Open your browser`n" -ForegroundColor White

Write-Host "No backend needed!`n" -ForegroundColor Green

# Check if frontend is already running
$frontendRunning = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue

if ($frontendRunning) {
    Write-Host "Frontend already running!" -ForegroundColor Green
    Write-Host "Opening browser...`n" -ForegroundColor Cyan
    Start-Process "http://localhost:3000"
} else {
    Write-Host "Starting frontend..." -ForegroundColor Yellow
    
    # Start in current terminal
    Set-Location frontend
    Write-Host "`nFrontend starting on port 3000..." -ForegroundColor Cyan
    Write-Host "Browser will open automatically`n" -ForegroundColor Gray
    Write-Host "========================================`n" -ForegroundColor Green
    
    # Wait a bit then open browser
    Start-Job -ScriptBlock {
        Start-Sleep -Seconds 10
        Start-Process "http://localhost:3000"
    } | Out-Null
    
    # Start the dev server
    npm run dev
}
