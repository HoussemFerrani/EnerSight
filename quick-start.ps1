# EnerSight Quick Start Script - PowerShell Version
# Automated setup for development environment on Windows

# Colors
function Write-Success { Write-Host "[SUCCESS] $args" -ForegroundColor Green }
function Write-Error { Write-Host "[ERROR] $args" -ForegroundColor Red }
function Write-Info { Write-Host "[INFO] $args" -ForegroundColor Yellow }

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  EnerSight Quick Start" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Info "Checking prerequisites..."

# Check Docker
try {
    $dockerVersion = docker --version
    Write-Success "Docker found: $dockerVersion"
} catch {
    Write-Error "Docker is not installed. Please install Docker Desktop."
    exit 1
}

# Check Docker Compose
try {
    $composeVersion = docker-compose --version
    Write-Success "Docker Compose found: $composeVersion"
} catch {
    Write-Error "Docker Compose is not installed."
    exit 1
}

# Create .env if it doesn't exist
if (-not (Test-Path .env)) {
    Write-Info "Creating .env file from template..."
    Copy-Item .env.development .env
    Write-Success ".env file created"
    Write-Info "Please edit .env with your InfluxDB token after initial setup"
} else {
    Write-Success ".env file exists"
}

# Start services
Write-Info "Starting services with Docker Compose..."
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to start services"
    exit 1
}

# Wait for services to be ready
Write-Info "Waiting for services to be ready..."
Start-Sleep -Seconds 10

# Check InfluxDB
Write-Info "Checking InfluxDB..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8086/health" -UseBasicParsing -ErrorAction Stop
    Write-Success "InfluxDB is running"
} catch {
    Write-Error "InfluxDB is not responding"
    Write-Host "Please check: docker-compose logs influxdb"
}

# Check Backend
Write-Info "Checking Backend API..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -ErrorAction Stop
    Write-Success "Backend is running"
} catch {
    Write-Error "Backend is not responding"
    Write-Host "Please check: docker-compose logs backend"
}

# Check Frontend
Write-Info "Checking Frontend..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -ErrorAction Stop
    Write-Success "Frontend is running"
} catch {
    Write-Error "Frontend is not responding"
    Write-Host "Please check: docker-compose logs frontend"
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📱 Access your application:" -ForegroundColor Green
Write-Host "   Frontend:  http://localhost:3000"
Write-Host "   API:       http://localhost:8000"
Write-Host "   API Docs:  http://localhost:8000/api/docs"
Write-Host "   InfluxDB:  http://localhost:8086"
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Open http://localhost:8086 to complete InfluxDB setup"
Write-Host "   2. Copy the generated token"
Write-Host "   3. Update .env file: INFLUXDB_TOKEN=<your-token>"
Write-Host "   4. Restart backend: docker-compose restart backend"
Write-Host "   5. Load sample data: docker-compose exec backend python backend/scripts/load_data_to_influxdb.py"
Write-Host ""
Write-Host "[USEFUL COMMANDS]" -ForegroundColor Cyan
Write-Host "   View logs:    docker-compose logs -f"
Write-Host "   Stop all:     docker-compose down"
Write-Host "   Restart:      docker-compose restart"
Write-Host ""
