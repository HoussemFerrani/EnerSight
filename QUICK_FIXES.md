# Quick Fixes Reference

## ⚠️ Common Issues & Solutions

### Issue 1: "Failed to load dashboard data" / "InfluxDB not configured"

**Root Cause:** Frontend running on wrong port (not in CORS allow list)

**Quick Fix:**
```powershell
# 1. Check frontend port
netstat -ano | Select-String ":3000"

# 2. If not on 3000, restart it
Get-Process node | Stop-Process -Force
cd frontend
npm run dev

# 3. Frontend should start on http://localhost:3000
```

**Prevention:** CORS now allows ports 3000, 3001, and 5173 ✅

---

### Issue 2: InfluxDB Token Expired / Invalid

**Root Cause:** Tokens can expire or get corrupted

**Quick Fix:**
```powershell
# Option A: Use the fixed permanent token
# Your token: my-super-secret-auth-token
# It's set in docker-compose.yml and won't expire

# Option B: Generate new token via UI
# 1. Go to http://localhost:8086
# 2. Login: admin / adminpass123
# 3. Data → API Tokens → Generate API Token → All Access Token
# 4. Copy token and update .env files:
#    INFLUXDB_TOKEN=your-new-token

# 5. Restart backend
.\venv\Scripts\python -m uvicorn backend.main:app --reload --port 8000
```

**Prevention:** 
- ✅ Fixed token in environment variables
- ✅ Backup script created: `.\scripts\backup_influxdb.ps1`

---

### Issue 3: Need to Recreate InfluxDB Container

**Best Practice (No Data Loss):**
```powershell
# Step 1: Backup first!
.\scripts\backup_influxdb.ps1 -Action backup

# Step 2: Recreate container
docker stop enersight-influxdb
docker rm enersight-influxdb
docker compose up -d influxdb

# Step 3: Data is preserved (Docker volumes)
# Wait 10 seconds, then test:
curl http://localhost:8086/health -UseBasicParsing
```

---

### Issue 4: Backend Can't Connect to InfluxDB

**Checklist:**
```powershell
# 1. Is InfluxDB running?
docker ps | Select-String "influx"

# 2. Is token correct in .env?
Get-Content .\backend\.env | Select-String "INFLUXDB_TOKEN"
# Should be: my-super-secret-auth-token

# 3. Restart backend
Get-Process python | Stop-Process -Force
.\venv\Scripts\python -m uvicorn backend.main:app --reload --port 8000

# 4. Test health
Invoke-RestMethod http://localhost:8000/health
```

---

### Issue 5: Frontend Shows Old/Cached Data

**Quick Fix:**
```powershell
# In your browser:
# Press: Ctrl + Shift + R (hard refresh)
# Or: Ctrl + F5

# If that doesn't work, restart frontend:
Get-Process node | Stop-Process -Force
cd frontend
npm run dev
```

---

## 🚀 Starting Your App (Correct Way)

### Full Start Order:
```powershell
# 1. Start InfluxDB (if using Docker)
docker start enersight-influxdb

# 2. Wait for it to be healthy (5 seconds)
Start-Sleep -Seconds 5

# 3. Start Backend
.\venv\Scripts\python -m uvicorn backend.main:app --reload --port 8000

# 4. Start Frontend (new terminal)
cd frontend
npm run dev

# 5. Open browser
# http://localhost:3000
```

---

## 🔐 Current Credentials

### InfluxDB
```
URL:      http://localhost:8086
Username: admin
Password: adminpass123
Token:    my-super-secret-auth-token
Org:      enersight
Bucket:   energy_data
```

### Application URLs
```
Dashboard:  http://localhost:3000
Backend:    http://localhost:8000
API Docs:   http://localhost:8000/docs
Health:     http://localhost:8000/health
```

---

## 📦 Backup Commands

```powershell
# Create backup
.\scripts\backup_influxdb.ps1 -Action backup

# Restore backup
.\scripts\backup_influxdb.ps1 -Action restore -BackupPath ".\backups\influxdb_backup_2026-02-16_19-30-00.tar"

# List backups
Get-ChildItem .\backups\*.tar | Select-Object Name, Length, LastWriteTime
```

---

## 🎯 What We Fixed Today (Feb 16, 2026)

### Problems Encountered:
1. ❌ Frontend was on port 3001 (CORS blocked)
2. ❌ InfluxDB token expired/invalid
3. ❌ Dashboard showed "not configured" error

### Solutions Implemented:
1. ✅ **CORS Update**: Now allows ports 3000, 3001, 5173
2. ✅ **Fixed Token**: Permanent token in docker-compose.yml
3. ✅ **Backup Script**: `.\scripts\backup_influxdb.ps1`
4. ✅ **Documentation**: INFLUXDB_MANAGEMENT.md
5. ✅ **Fresh Container**: New InfluxDB with correct credentials
6. ✅ **Data Reloaded**: 1,000 records (12,984.91 kWh)
7. ✅ **Frontend Restarted**: Now on correct port 3000

### Current Status:
✅ Backend running on port 8000
✅ Frontend running on port 3000
✅ InfluxDB healthy with persistent token
✅ 1,000+ data points loaded
✅ All API endpoints working
✅ Dashboard showing real data

---

*Keep this file handy for quick troubleshooting!*
