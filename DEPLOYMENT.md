# EnerSight Deployment Guide

Complete guide for deploying EnerSight in production, staging, and development environments.

---

## Table of Contents

1. [Quick Start (Docker)](#quick-start-docker)
2. [Environment Configuration](#environment-configuration)
3. [Production Deployment](#production-deployment)
4. [Development Setup](#development-setup)
5. [Manual Deployment](#manual-deployment)
6. [Security Checklist](#security-checklist)
7. [Troubleshooting](#troubleshooting)
8. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Quick Start (Docker)

### Prerequisites

- Docker Desktop 20.10+ or Docker Engine + Docker Compose
- 4GB RAM minimum (8GB recommended)
- 10GB disk space

### One-Command Deployment

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd EnerSight

# 2. Configure environment (first time only)
cp .env.production .env
# Edit .env with your actual credentials

# 3. Start all services
docker-compose up -d

# 4. Load initial data
docker-compose exec backend python backend/scripts/load_data_to_influxdb.py

# 5. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/api/docs
# InfluxDB UI: http://localhost:8086
```

### Stop Services

```bash
docker-compose down
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f influxdb
```

---

## Environment Configuration

### Available Environments

1. **Development** (`.env.development`)
   - Debug mode enabled
   - Verbose logging
   - Local ports (3000, 8000, 8086)

2. **Staging** (`.env.staging`)
   - Production-like settings
   - Testing environment
   - Separate database

3. **Production** (`.env.production`)
   - Optimized for performance
   - Security hardened
   - Monitoring enabled

### Critical Configuration

#### 1. InfluxDB Token Setup

**First Time Setup:**

```bash
# Start only InfluxDB first
docker-compose up -d influxdb

# Wait 30 seconds for initialization
sleep 30

# Open InfluxDB UI
open http://localhost:8086

# Complete setup wizard:
# - Username: admin
# - Password: enersight2026 (or your choice)
# - Organization: enersight
# - Bucket: energy_data
# - Copy the generated token

# Update .env file with your token
INFLUXDB_TOKEN=<your-token-here>

# Restart all services
docker-compose up -d
```

#### 2. Security Keys

**Generate Strong Keys:**

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT_SECRET
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Update `.env`:
```env
SECRET_KEY=<generated-key-1>
JWT_SECRET=<generated-key-2>
```

#### 3. CORS Origins

Update for your domain:

```env
# Development
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# Production
CORS_ORIGINS=["https://yourdomain.com","https://app.yourdomain.com"]
```

---

## Production Deployment

### Option 1: Docker Compose (Recommended)

```bash
# 1. Prepare production environment
cp .env.production .env

# 2. Update all sensitive values in .env
nano .env

# 3. Build and start services
docker-compose -f docker-compose.yml up -d --build

# 4. Check health
curl http://localhost:8000/health

# 5. Load initial data
docker-compose exec backend python backend/scripts/load_data_to_influxdb.py
```

### Option 2: Cloud Deployment (AWS, Azure, GCP)

#### AWS ECS/Fargate

```yaml
# task-definition.json
{
  "family": "enersight",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-registry/enersight-backend:latest",
      "portMappings": [{"containerPort": 8000}]
    }
  ]
}
```

#### Kubernetes

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: enersight-backend
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: backend
        image: your-registry/enersight-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
```

### Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/enersight
server {
    listen 80;
    server_name yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Development Setup

### Local Development (Without Docker)

```bash
# 1. Backend Setup
cd EnerSight
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Start InfluxDB (Docker)
docker run -d -p 8086:8086 \
  -v influxdb-data:/var/lib/influxdb2 \
  --name influxdb \
  influxdb:latest

# 3. Configure environment
cp .env.development backend/.env
# Update INFLUXDB_TOKEN

# 4. Start backend
cd backend
uvicorn main:app --reload --port 8000

# 5. Frontend Setup (new terminal)
cd frontend
npm install
npm run dev

# 6. Load sample data
python backend/scripts/load_data_to_influxdb.py
```

### Hot Reload Development

```bash
# Backend with auto-reload
uvicorn backend.main:app --reload --port 8000

# Frontend with Vite HMR
cd frontend && npm run dev
```

---

## Manual Deployment

### Build Docker Images

```bash
# Backend
docker build -t enersight-backend:latest -f backend/Dockerfile .

# Frontend
docker build -t enersight-frontend:latest -f frontend/Dockerfile .

# Tag for registry
docker tag enersight-backend:latest your-registry/enersight-backend:latest
docker tag enersight-frontend:latest your-registry/enersight-frontend:latest

# Push to registry
docker push your-registry/enersight-backend:latest
docker push your-registry/enersight-frontend:latest
```

### System Service (systemd)

```ini
# /etc/systemd/system/enersight-backend.service
[Unit]
Description=EnerSight Backend API
After=network.target influxdb.service

[Service]
Type=simple
User=enersight
WorkingDirectory=/opt/enersight
Environment="PATH=/opt/enersight/venv/bin"
ExecStart=/opt/enersight/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable enersight-backend
sudo systemctl start enersight-backend
sudo systemctl status enersight-backend
```

---

## Security Checklist

### Pre-Deployment

- [ ] Change all default passwords
- [ ] Generate strong SECRET_KEY and JWT_SECRET
- [ ] Update CORS origins to production domains
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Enable rate limiting
- [ ] Configure logging and monitoring
- [ ] Review and update security headers
- [ ] Disable DEBUG mode
- [ ] Set proper file permissions

### InfluxDB Security

```bash
# Create read-only token for applications
influx auth create \
  --org enersight \
  --read-bucket energy_data \
  --description "Read-only API token"

# Rotate admin token quarterly
influx auth create --all-access
# Update .env with new token
# Delete old token
```

### Network Security

```bash
# Firewall rules (ufw)
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw deny 8000   # Block direct backend access
sudo ufw deny 8086   # Block direct InfluxDB access
sudo ufw enable
```

---

## Troubleshooting

### Common Issues

#### 1. Backend Can't Connect to InfluxDB

```bash
# Check InfluxDB is running
docker ps | grep influxdb

# Check backend logs
docker-compose logs backend

# Verify token
docker-compose exec backend env | grep INFLUXDB_TOKEN

# Test connection
curl http://localhost:8086/health
```

#### 2. Frontend Shows CORS Error

```bash
# Check backend CORS settings
docker-compose exec backend env | grep CORS

# Update .env
CORS_ORIGINS=["http://localhost:3000"]

# Restart backend
docker-compose restart backend
```

#### 3. No Data in Dashboard

```bash
# Load sample data
docker-compose exec backend python backend/scripts/load_data_to_influxdb.py

# Query InfluxDB directly
docker-compose exec influxdb influx query \
  'from(bucket:"energy_data") |> range(start: -7d) |> limit(n:5)'

# Check API
curl http://localhost:8000/api/v1/energy/readings?limit=5
```

#### 4. Container Won't Start

```bash
# Check logs
docker-compose logs <service-name>

# Rebuild image
docker-compose build --no-cache <service-name>

# Remove and recreate
docker-compose down
docker-compose up -d --force-recreate
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health | jq

# InfluxDB health
curl http://localhost:8086/health

# Frontend health
curl http://localhost:3000/health

# Check all container health
docker-compose ps
```

---

## Monitoring & Maintenance

### Logs

```bash
# Real-time logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100 backend

# Export logs
docker-compose logs > logs_$(date +%Y%m%d).txt
```

### Backups

#### InfluxDB Backup

```bash
# Full backup
docker-compose exec influxdb influx backup /tmp/backup
docker cp enersight-influxdb:/tmp/backup ./influxdb-backup-$(date +%Y%m%d)

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/influxdb"
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec influxdb influx backup /tmp/backup
docker cp enersight-influxdb:/tmp/backup $BACKUP_DIR/backup_$DATE
# Upload to S3 or backup service
```

#### Database Restore

```bash
# Restore from backup
docker cp ./influxdb-backup-20260216 enersight-influxdb:/tmp/restore
docker-compose exec influxdb influx restore /tmp/restore
```

### Performance Monitoring

```bash
# Container resource usage
docker stats

# Backend API metrics
curl http://localhost:8000/metrics

# Database size
docker exec enersight-influxdb du -sh /var/lib/influxdb2
```

### Updates

```bash
# Update application
git pull origin main
docker-compose build
docker-compose up -d

# Update Docker images
docker-compose pull
docker-compose up -d
```

---

## Advanced Configuration

### Scaling

```yaml
# docker-compose.override.yml
services:
  backend:
    deploy:
      replicas: 3
    environment:
      - WORKERS=4
```

### Load Balancing

```bash
# Nginx upstream
upstream backend_servers {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

### SSL/TLS Setup

```bash
# Get Let's Encrypt certificate
certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
certbot renew --dry-run
```

---

## Support & Resources

- **Documentation**: `/docs/README.md`
- **API Reference**: `http://localhost:8000/api/docs`
- **Issues**: GitHub Issues
- **Architecture**: `/docs/ARCHITECTURE.md`

---

**Last Updated**: February 16, 2026
**Version**: 1.0.0
