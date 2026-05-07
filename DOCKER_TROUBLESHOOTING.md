# Docker Build Troubleshooting Guide

## Quick Diagnosis

Run this to identify issues:

```powershell
# Check Docker status
docker-compose ps

# View detailed logs
docker-compose logs -f

# Check specific service
docker-compose logs -f backend
```

---

## Problem-Specific Solutions

### 🔴 Backend Build Timeout/Fails

**Symptoms:**
- `pip install` hangs
- "Killed" message
- Out of memory errors

**Solutions (in order):**

1. **Clear cache:**
   ```powershell
   docker system prune -a --volumes -f
   docker-compose build --no-cache backend
   ```

2. **Increase Docker resources:**
   - Windows: Docker Desktop → Settings → Resources → increase Memory to 6-8GB
   - Restart Docker Desktop

3. **Optimize Dockerfile build:**
   ```dockerfile
   # Disable pip cache during install
   RUN pip install --no-cache-dir -r requirements.txt
   
   # Combine RUN commands to reduce layers
   RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*
   ```

4. **Check for problematic dependencies:**
   - TensorFlow takes longest
   - Try building backend alone: `docker-compose build backend`

---

### 🔴 Frontend Build Fails

**Symptoms:**
- `npm ci` fails
- `npm run build` errors
- Node module conflicts

**Solutions:**

1. **Clear npm cache:**
   ```powershell
   docker exec enersight-frontend npm cache clean --force
   docker-compose rebuild frontend
   ```

2. **Check Node version compatibility:**
   - Current: Node 18-alpine
   - Try: `node:20-alpine` if needed

3. **Alternative: Add to Dockerfile:**
   ```dockerfile
   RUN npm ci --silent --legacy-peer-deps
   ```

---

### 🔴 Containers Won't Start After Build

**Check logs:**
```powershell
docker-compose logs <service-name>
```

**Common causes & fixes:**

| Issue | Solution |
|-------|----------|
| `connection refused` | Services not healthy yet. Wait 30-60s, check `docker-compose ps` |
| `ModuleNotFoundError` | Rebuild: `docker-compose build --no-cache` |
| `INFLUXDB_TOKEN` not set | Create `.env` file with required variables |
| `port already in use` | Change port: `docker-compose.yml` modify `ports:` section |
| `permission denied` | Windows path issue, use full paths in `volumes:` |

---

### 🔴 CORS / Connection Errors at Runtime

**Problem:** Frontend can't reach backend

**Solution:**
```powershell
# Verify environment
docker-compose exec backend env | grep CORS

# Should show: CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173

# If not set, update docker-compose.yml:
environment:
  - CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173

# Restart
docker-compose restart backend
```

---

### 🔴 InfluxDB/Postgres Connection Fails

**Check connectivity:**
```powershell
# From backend container
docker-compose exec backend curl -v http://influxdb:8086/health
docker-compose exec backend curl -v http://postgres:5432

# Check postgres specifically
docker-compose exec backend python -c "import psycopg2; psycopg2.connect('postgresql://enersight_user:enersight_pass_123@postgres:5432/enersight')"
```

**Troubleshooting:**
- Wait for healthchecks: `docker-compose logs postgres influxdb`
- Increase timeout in docker-compose.yml:
  ```yaml
  healthcheck:
    start_period: 60s  # Increase from default
  ```

---

## Complete Clean Rebuild Process

If all else fails, use this nuclear option:

```powershell
# 1. Stop everything
docker-compose down

# 2. Remove all Docker data
docker system prune -a --volumes -f

# 3. Delete .env if corrupted
Remove-Item .env -ErrorAction SilentlyContinue

# 4. Create fresh .env
@"
ENVIRONMENT=development
INFLUXDB_TOKEN=my-super-secret-auth-token
POSTGRES_PASSWORD=enersight_pass_123
DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=my-super-secret-auth-token
"@ | Out-File -Encoding UTF8 .env

# 5. Rebuild from scratch
docker-compose build --progress=plain

# 6. Start services
docker-compose up -d

# 7. Wait and check
Start-Sleep -Seconds 30
docker-compose ps
```

---

## Performance Optimization Tips

### 1. **Reduce TensorFlow Size**
Replace in `requirements.txt`:
```diff
- tensorflow==2.15.0
+ tensorflow-cpu==2.15.0  # Lighter, faster
```

### 2. **Use BuildKit** (faster builds)
```powershell
$env:DOCKER_BUILDKIT=1
docker-compose build
```

### 3. **Cache Dependencies Properly**
Move dependency copy before source code copy in Dockerfile:
```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ ./backend/  # Changes here won't rebuild dependencies
```

---

## Monitoring During Build

```powershell
# Watch resource usage
docker stats

# Follow logs in real-time
docker-compose logs -f

# Watch for specific error patterns
docker-compose logs | Select-String "ERROR|FAIL|Exception"
```

---

## Prevention

1. **Always check logs first:**
   ```powershell
   docker-compose logs --tail=50 <service>
   ```

2. **Test connectivity in container:**
   ```powershell
   docker-compose exec backend curl http://influxdb:8086/health
   ```

3. **Keep Docker updated:**
   ```powershell
   wsl --update  # For Docker on Windows
   ```

4. **Document environment variables:**
   - Create `.env.example` with all required variables
   - Check `docker-compose.yml` for `environment:` sections

---

## When All Else Fails

1. Check Docker Desktop logs: **Settings → Troubleshoot**
2. Restart Docker Desktop completely
3. Check system disk space: `dir C:\` (need >20GB free)
4. Update Docker: Get latest Docker Desktop
5. Check Windows WSL: `wsl --list --verbose`

