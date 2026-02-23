#!/bin/bash

# EnerSight Quick Start Script
# Automated setup for development environment

set -e  # Exit on error

echo "=========================================="
echo "  EnerSight Quick Start"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}➜${NC} $1"
}

# Check prerequisites
print_info "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker Desktop."
    exit 1
fi
print_success "Docker found"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed."
    exit 1
fi
print_success "Docker Compose found"

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    print_info "Creating .env file from template..."
    cp .env.development .env
    print_success ".env file created"
    print_info "Please edit .env with your InfluxDB token after initial setup"
else
    print_success ".env file exists"
fi

# Start services
print_info "Starting services with Docker Compose..."
docker-compose up -d

# Wait for services to be healthy
print_info "Waiting for services to be ready..."
sleep 10

# Check InfluxDB
print_info "Checking InfluxDB..."
if curl -sf http://localhost:8086/health > /dev/null; then
    print_success "InfluxDB is running"
else
    print_error "InfluxDB is not responding"
    echo "Please check: docker-compose logs influxdb"
fi

# Check Backend
print_info "Checking Backend API..."
if curl -sf http://localhost:8000/health > /dev/null; then
    print_success "Backend is running"
else
    print_error "Backend is not responding"
    echo "Please check: docker-compose logs backend"
fi

# Check Frontend
print_info "Checking Frontend..."
if curl -sf http://localhost:3000 > /dev/null; then
    print_success "Frontend is running"
else
    print_error "Frontend is not responding"
    echo "Please check: docker-compose logs frontend"
fi

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "📱 Access your application:"
echo "   Frontend:  http://localhost:3000"
echo "   API:       http://localhost:8000"
echo "   API Docs:  http://localhost:8000/api/docs"
echo "   InfluxDB:  http://localhost:8086"
echo ""
echo "📝 Next Steps:"
echo "   1. Open http://localhost:8086 to complete InfluxDB setup"
echo "   2. Copy the generated token"
echo "   3. Update .env file: INFLUXDB_TOKEN=<your-token>"
echo "   4. Restart backend: docker-compose restart backend"
echo "   5. Load sample data: docker-compose exec backend python backend/scripts/load_data_to_influxdb.py"
echo ""
echo "🔍 Useful Commands:"
echo "   View logs:    docker-compose logs -f"
echo "   Stop all:     docker-compose down"
echo "   Restart:      docker-compose restart"
echo ""
