# Docker Build Issue on Windows - Workaround Guide

## Problem Summary

You're experiencing `exec format error` when building Docker images on Windows Docker Desktop. This is a known issue with Docker Desktop on WSL2 and certain Python base images.

```
ERROR: process "/bin/sh -c apt-get update..." did not complete successfully: exit code: 255
exec /bin/sh: exec format error
```

## Why This Happens

- Docker Desktop on Windows with WSL2 has kernel compatibility issues with certain base images
- The fix attempted (line ending conversion, cache clearing, image switching) didn't resolve the core issue
- This affects python:3.11-slim and similar Debian-based images

---

## ✅ SOLUTION 1: Run Backend Locally (Recommended - Fastest)

This bypasses Docker entirely for the backend while keeping databases in Docker.

### Step 1: Start Only Databases in Docker

```powershell
cd C:\Users\hp\Desktop\EnerSight

# Start just postgres and influxdb
docker-compose up -d postgres influxdb

# Wait for health checks
Start-Sleep -Seconds 10
docker-compose ps
```

### Step 2: Setup Backend Locally

```powershell
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Set environment variables
$env:INFLUXDB_URL="http://localhost:8086"
$env:INFLUXDB_TOKEN="my-super-secret-auth-token"
$env:INFLUXDB_ORG="enersight"
$env:INFLUXDB_BUCKET="energy_data"
$env:POSTGRES_HOST="localhost"
$env:POSTGRES_USER="enersight_user"
$env:POSTGRES_PASSWORD="enersight_pass_123"
$env:POSTGRES_DB="enersight"
$env:POSTGRES_PORT="5432"
$env:LOG_LEVEL="INFO"

# Start backend
cd backend
python -m uvicorn main:app --reload --port 8000
```

### Step 3: Setup Frontend Locally

```powershell
# New terminal
cd C:\Users\hp\Desktop\EnerSight\frontend
npm install
npm run dev
```

### Access the Platform

```
Frontend:    http://localhost:5173  (Vite dev server)
Backend API: http://localhost:8000
API Docs:    http://localhost:8000/docs
InfluxDB:    http://localhost:8086
Postgres:    localhost:5432
```

---

## ✅ SOLUTION 2: Create Simpler Docker Dockerfile

If you still want full Docker deployment, create a workaround Dockerfile that avoids the exec format issue:

### backend/Dockerfile (Workaround Version)

```dockerfile
# Use Alpine Linux instead - it has better Windows Docker support
FROM python:3.11-alpine as builder

WORKDIR /app
RUN apk add --no-cache gcc musl-dev g++ linux-headers

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production
FROM python:3.11-alpine

WORKDIR /app
RUN apk add --no-cache curl

COPY --from=builder /root/.local /root/.local
COPY backend/ ./backend/
COPY ml/ ./ml/
COPY data/ ./data/

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app:$PYTHONPATH

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Then rebuild:
```powershell
docker-compose build --no-cache backend
docker-compose up -d
```

---

## ✅ SOLUTION 3: Check Docker Desktop Settings

Sometimes the issue is resolvable by adjusting Docker Desktop configuration:

### Windows → Docker Settings

1. **Settings → General**
   - Uncheck "Use WSL 2 based engine"
   - Switch to Hyper-V (requires checking in Windows Features)

2. **OR Settings → Resources**
   - Increase CPUs to max
   - Increase Memory to 8GB+
   - Increase Disk image size to 100GB

3. **Restart Docker Desktop and retry build**

### Enable Windows Features for Hyper-V

```powershell
# Run as Administrator
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
```

Then restart and switch Docker to Hyper-V mode.

---

## ✅ SOLUTION 4: Use Pre-Built Images

Skip building entirely - use pre-backed images from Docker Hub:

```yaml
services:
  backend:
    image: your-username/enersight-backend:latest  # Pre-built image
    ports:
      - "8000:8000"
    # ... rest of config
```

---

## Quick Decision Flow

```
Do you want to:

1. START CODING NOW? → Use Solution 1 (local backend + Docker for DBs)
2. need full Docker stack? → Try Solution 2 (Alpine Dockerfile)
3. Have time to configure? → Try Solution 3 (Hyper-V switch)
4. Just want it working? → Use Solution 4 (pre-built images)
```

---

## Testing Your Choice

### After Solution 1 (Recommended):

```powershell
# Test backend
curl http://localhost:8000/health

# Test front end
curl http://localhost:5173

# Check InfluxDB
curl http://localhost:8086/health

# Load sample data
docker-compose exec postgres psql -U enersight_user -d enersight -c "SELECT version();"
```

---

## Reverting Back to Full Docker

Once you switch to local backend, you can later switch back to full Docker by:

1. Building the alternative Dockerfile (Solution 2 or 4)
2. Running full compose: `docker-compose up -d --build`
3. Stopping local services: `Ctrl+C` in terminals

---

## Remember

- **Solution 1** is fastest for development
- **Solution 2** is best if Docker absolutely needed
- **Solution 3** requires more system configuration
- **Solution 4** depends on having pre-built images available

Pick one and let me know if you hit any issues!
