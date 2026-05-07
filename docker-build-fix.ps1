# Docker Build Troubleshooting & Optimization Script
# This script fixes common Docker build issues

Write-Host "🐳 EnerSight Docker Build Helper" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

# Function to run commands
function Execute {
    param([string]$Command, [string]$Description)
    Write-Host "▶ $Description" -ForegroundColor Yellow
    Invoke-Expression $Command
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed: $Description" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Success" -ForegroundColor Green
    Write-Host ""
}

# Check Docker installation
Write-Host "Checking Docker..." -ForegroundColor Cyan
docker --version
docker-compose --version
Write-Host ""

$choice = Read-Host "What would you like to do?
1. Clean build (remove all containers/images)
2. Rebuild with no cache
3. Check service health
4. View detailed logs
5. Troubleshoot specific service
Enter choice (1-5)"

switch($choice) {
    "1" {
        Write-Host "🗑  Performing clean build..." -ForegroundColor Magenta
        Execute "docker-compose down" "Stopping all containers"
        Execute "docker system prune -a --volumes -f" "Cleaning up Docker system"
        Execute "docker-compose up -d --build" "Building and starting services"
        Write-Host "Waiting 30 seconds for services to initialize..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30
        Execute "docker-compose ps" "Checking container status"
    }
    
    "2" {
        Write-Host "🔨 Rebuilding with no cache..." -ForegroundColor Magenta
        Execute "docker-compose build --no-cache --progress=plain" "Building images"
        Execute "docker-compose up -d" "Starting services"
        Write-Host "Waiting 30 seconds for services to initialize..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30
        Execute "docker-compose ps" "Checking container status"
    }
    
    "3" {
        Write-Host "🏥 Checking service health..." -ForegroundColor Magenta
        docker-compose ps
        Write-Host ""
        Write-Host "Testing connections..." -ForegroundColor Yellow
        docker-compose exec backend curl -f http://influxdb:8086/health > $null 2>&1
        if ($LASTEXITCODE -eq 0) { Write-Host "✓ Backend → InfluxDB: OK" -ForegroundColor Green }
        else { Write-Host "✗ Backend → InfluxDB: FAILED" -ForegroundColor Red }
        
        docker-compose exec backend curl -f http://postgres:5432 > $null 2>&1
        if ($LASTEXITCODE -eq 0) { Write-Host "✓ Backend → Postgres: OK" -ForegroundColor Green }
        else { Write-Host "✗ Backend → Postgres: FAILED" -ForegroundColor Red }
    }
    
    "4" {
        $service = Read-Host "Enter service name (postgres/influxdb/backend/frontend/all)"
        if($service -eq "all") {
            docker-compose logs --tail=100
        } else {
            docker-compose logs -f --tail=100 $service
        }
    }
    
    "5" {
        $service = Read-Host "Enter service name (postgres/influxdb/backend/frontend)"
        Write-Host "Logs for $service :" -ForegroundColor Yellow
        docker-compose logs $service
        Write-Host ""
        Write-Host "Container details:" -ForegroundColor Yellow
        docker-compose exec $service env | grep -E "(DB|INFLUX|CORS|PORT)" || Write-Host "No matching env vars"
    }
}

Write-Host "`n📌 Quick Reference:" -ForegroundColor Cyan
Write-Host "  Frontend:    http://localhost:3000"
Write-Host "  Backend API: http://localhost:8000"
Write-Host "  API Docs:    http://localhost:8000/docs"
Write-Host "  InfluxDB UI: http://localhost:8086"
