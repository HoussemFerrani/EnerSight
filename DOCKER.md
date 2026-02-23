# 🐳 Docker Deployment Guide

Complete guide for deploying EnerSight using Docker and Docker Compose.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Docker Commands](#docker-commands)
- [Service Details](#service-details)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)
- [Performance Tuning](#performance-tuning)

## Prerequisites

### Required Software
- **Docker**: 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose**: 2.0+ (included with Docker Desktop)
- **Git**: For cloning the repository

### System Requirements
- **CPU**: 2 cores minimum, 4+ recommended
- **RAM**: 4GB minimum, 8GB+ recommended
- **Disk**: 10GB free space minimum
- **OS**: Windows 10/11, macOS 11+, Linux (Ubuntu 20.04+)

### Network Ports
Ensure these ports are available:
- `3000` - Frontend (React application)
- `8000` - Backend API (FastAPI)
- `8086` - InfluxDB UI and API
- `5432` - PostgreSQL database
- `6379` - Redis (optional, production only)

## Quick Start

### 1. Clone and Configure

```bash
# Clone the repository
git clone <your-repo-url>
cd EnerSight

# Copy environment template
cp .env.example .env

# Edit .env with your settings (required!)
# At minimum, update:
#   - SECRET_KEY
#   - JWT_SECRET
#   - INFLUXDB_TOKEN
#   - POSTGRES_PASSWORD
#   - SMTP settings (if using email alerts)
```

### 2. One-Command Start

**Windows:**
```powershell
.\quick-start.ps1
```

**Linux/macOS:**
```bash
chmod +x quick-start.sh
./quick-start.sh
```

### 3. Manual Start

```bash
# Pull images
docker compose pull

# Build custom images
docker compose build

# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **InfluxDB UI**: http://localhost:8086

**Default Login:**
- Username: `johndoe`
- Password: `SecurePass123!`

## Configuration

### Environment Variables

Key environment variables to configure in `.env`:

#### Security (CRITICAL - Must Change for Production!)
```env
SECRET_KEY=generate-using-openssl-rand-hex-32
JWT_SECRET=generate-using-openssl-rand-hex-32
```

Generate secure keys:
```bash
# Linux/macOS
openssl rand -hex 32

# PowerShell
[System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
```

#### Database
```env
# InfluxDB
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=your-influxdb-token-here
INFLUXDB_ORG=enersight
INFLUXDB_BUCKET=energy_data

# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=enersight
POSTGRES_USER=enersight_user
POSTGRES_PASSWORD=secure-password-here
```

#### Email Alerts
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=EnerSight Alerts
```

**For Gmail:**
1. Go to Google Account → Security
2. Enable 2-Factor Authentication
3. Generate App Password
4. Use app password in SMTP_PASSWORD

#### API Configuration
```env
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
ENVIRONMENT=production
CORS_ORIGINS=http://localhost:3000
```

## Docker Commands

### Service Management

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose stop

# Restart all services
docker compose restart

# Start specific service
docker compose start backend

# Stop specific service
docker compose stop frontend

# Restart specific service
docker compose restart influxdb

# Remove all containers
docker compose down

# Remove containers and volumes (WARNING: deletes data!)
docker compose down -v
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend

# Last 100 lines
docker compose logs --tail=100 backend

# Since specific time
docker compose logs --since 2024-01-01T00:00:00 backend
```

### Building and Updating

```bash
# Build all images
docker compose build

# Build specific image
docker compose build backend

# Build without cache
docker compose build --no-cache

# Pull latest base images
docker compose pull

# Rebuild and restart
docker compose up -d --build
```

### Executing Commands

```bash
# Backend container
docker compose exec backend python backend/scripts/load_data_to_influxdb.py

# PostgreSQL operations
docker compose exec postgres psql -U enersight_user -d enersight

# InfluxDB CLI
docker compose exec influxdb influx

# Shell access
docker compose exec backend bash
docker compose exec frontend sh
```

### Health Checks

```bash
# Check service status
docker compose ps

# Individual service health
docker inspect enersight-backend | grep -A 10 Health
docker inspect enersight-influxdb | grep -A 10 Health

# Quick health check
curl http://localhost:8000/health
curl http://localhost:8086/health
```

## Service Details

### Backend (FastAPI)

**Container**: `enersight-backend`
**Port**: `8000`
**Base Image**: `python:3.11-slim`

Features:
- Multi-stage build for smaller image
- Health check endpoint
- Auto-restart on failure
- Volume mounts for logs and models

Configuration:
```yaml
environment:
  - WORKERS=4
  - LOG_LEVEL=INFO
  - TIMEOUT_SECONDS=60
```

### Frontend (React + Nginx)

**Container**: `enersight-frontend`
**Port**: `3000` (mapped to 80 internally)
**Base Images**: `node:18-alpine` (build), `nginx:alpine` (runtime)

Features:
- Two-stage build (build + serve)
- Optimized nginx configuration
- Gzip compression enabled
- Security headers
- React Router support

### PostgreSQL

**Container**: `enersight-postgres`
**Port**: `5432`
**Image**: `postgres:15-alpine`

Features:
- Persistent data volume
- Health checks
- Automatic backups (with backup volume)
- Connection pooling

Default credentials (change in production!):
- Database: `enersight`
- User: `enersight_user`
- Password: Set in `.env`

### InfluxDB

**Container**: `enersight-influxdb`
**Port**: `8086`
**Image**: `influxdb:2.7-alpine`

Features:
- Time-series data storage
- Persistent volumes for data and config
- Auto-initialization
- Built-in UI

Access UI: http://localhost:8086

### Redis (Production Only)

**Container**: `enersight-redis`
**Port**: `6379`
**Image**: `redis:7-alpine`

Features:
- Caching layer
- Data persistence (AOF)
- Password protection
- Memory limits

Only included in `docker-compose.prod.yml`

## Production Deployment

### Using Production Configuration

```bash
# Use production compose file
docker compose -f docker-compose.prod.yml up -d

# Or with environment override
COMPOSE_FILE=docker-compose.prod.yml docker compose up -d
```

### Production Checklist

- [ ] Change all default passwords
- [ ] Generate secure SECRET_KEY and JWT_SECRET
- [ ] Configure SMTP for email alerts
- [ ] Set DEBUG=False
- [ ] Configure proper CORS_ORIGINS
- [ ] Enable SSL/TLS (use nginx-proxy service)
- [ ] Set up automated backups
- [ ] Configure log rotation
- [ ] Set resource limits
- [ ] Enable monitoring (Prometheus/Grafana)
- [ ] Configure firewall rules
- [ ] Set up health check monitoring

### SSL/TLS Configuration

1. **Using Nginx Proxy** (included in prod):

```bash
# Generate SSL certificates
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/private.key \
  -out nginx/ssl/certificate.crt

# Start with proxy profile
docker compose --profile with-proxy -f docker-compose.prod.yml up -d
```

2. **Using Let's Encrypt** (recommended):

```bash
# Use certbot
docker run -it --rm -v $PWD/nginx/ssl:/etc/letsencrypt certbot/certbot certonly --standalone
```

### Resource Limits

Production configuration includes resource limits:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '1.0'
      memory: 1G
```

Adjust based on your server capacity.

### Backups

**Automated Backup Script:**

```bash
#!/bin/bash
# backup.sh - Run daily via cron

DATE=$(date +%Y%m%d_%H%M%S)

# Backup PostgreSQL
docker compose exec -T postgres pg_dump -U enersight_user enersight > backups/postgres/backup_$DATE.sql

# Backup InfluxDB
docker compose exec influxdb influx backup /backups/influxdb_$DATE

# Keep only last 30 days
find backups/ -type f -mtime +30 -delete
```

Add to crontab:
```bash
0 2 * * * /path/to/enersight/backup.sh
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker compose logs <service-name>

# Check service status
docker compose ps

# Restart service
docker compose restart <service-name>

# Force recreate
docker compose up -d --force-recreate <service-name>
```

### Backend Can't Connect to InfluxDB

**Symptom**: Backend logs show connection errors

**Solution**:
```bash
# 1. Check InfluxDB is running
docker compose ps influxdb

# 2. Verify health
curl http://localhost:8086/health

# 3. Check token
docker compose exec influxdb influx auth list

# 4. Restart services in order
docker compose restart influxdb
sleep 10
docker compose restart backend
```

### Frontend Shows Blank Page

**Symptom**: White screen or 404 on frontend

**Solutions**:
```bash
# 1. Check nginx logs
docker compose logs frontend

# 2. Verify build completed
docker compose exec frontend ls -la /usr/share/nginx/html

# 3. Rebuild frontend
docker compose build --no-cache frontend
docker compose up -d frontend

# 4. Check browser console for errors
# Open browser dev tools (F12) and check Console tab
```

### Database Connection Refused

**Symptom**: "Connection refused" on port 5432 or 8086

**Solutions**:
```bash
# 1. Check if port is already in use
netstat -ano | findstr :5432  # Windows
lsof -i :5432                 # Linux/macOS

# 2. Wait for database to be ready
docker compose logs postgres | grep "ready to accept"

# 3. Check health
docker inspect enersight-postgres | grep Health

# 4. Verify .env configuration
cat .env | grep POSTGRES_HOST
```

### Out of Memory

**Symptom**: Services killed or slow performance

**Solution**:
```bash
# Check memory usage
docker stats

# Increase Docker memory limit (Docker Desktop)
# Settings → Resources → Memory → 8GB+

# Add memory limits to services
# Edit docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 1G
```

### Permission Denied on Volumes

**Symptom**: "Permission denied" in logs

**Solution**:
```bash
# Fix permissions
sudo chown -R $USER:$USER logs/ backups/ ml/

# Or run with elevated permissions
sudo docker compose up -d
```

## Performance Tuning

### Backend Optimization

```yaml
environment:
  # Increase workers (CPU cores * 2)
  - WORKERS=8
  
  # Connection pooling
  - MAX_CONNECTIONS=100
  
  # Timeout settings
  - TIMEOUT_SECONDS=120
  - KEEP_ALIVE_TIMEOUT=5
```

### PostgreSQL Tuning

```yaml
environment:
  # Add PostgreSQL optimizations
  - POSTGRES_MAX_CONNECTIONS=200
  - POSTGRES_SHARED_BUFFERS=256MB
  - POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
  - POSTGRES_WORK_MEM=16MB
```

### InfluxDB Optimization

```yaml
environment:
  # Increase cache and parallelism
  - INFLUXD_QUERY_CONCURRENCY=20
  - INFLUXD_QUERY_QUEUE_SIZE=100
  - INFLUXD_STORAGE_CACHE_SNAPSHOT_MEMORY_SIZE=26214400
```

### Nginx Caching

```nginx
# Add to nginx.conf
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m inactive=60m;

location /api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_key "$request_uri";
}
```

## Monitoring

### Health Check Monitoring

```bash
# Create monitoring script
#!/bin/bash
# health-check.sh

SERVICES="backend frontend postgres influxdb"

for service in $SERVICES; do
    HEALTH=$(docker inspect enersight-$service | jq -r '.[0].State.Health.Status')
    if [ "$HEALTH" != "healthy" ]; then
        echo "ALERT: $service is $HEALTH"
        # Send alert (email, Slack, etc.)
    fi
done
```

### Prometheus + Grafana

```yaml
# Add to docker-compose.yml
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    depends_on:
      - prometheus
```

## Useful Scripts

### cleanup.sh - Clean up Docker resources

```bash
#!/bin/bash
# Remove stopped containers
docker compose down

# Remove unused images
docker image prune -f

# Remove unused volumes (WARNING: deletes data!)
# docker volume prune -f

# Remove unused networks
docker network prune -f
```

### update.sh - Update and restart services

```bash
#!/bin/bash
# Pull latest code
git pull

# Update images
docker compose pull

# Rebuild and restart
docker compose up -d --build

# Check status
docker compose ps
```

---

For additional help, see:
- [Main README](README.md)
- [API Documentation](http://localhost:8000/docs)
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
