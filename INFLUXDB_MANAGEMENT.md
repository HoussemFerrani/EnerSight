# InfluxDB Management Guide

## 🔐 Preventing Token Expiration Issues

### Current Setup (Safe Mode)
Your InfluxDB is configured with a **permanent admin token** that won't expire:

```
Token: my-super-secret-auth-token
Username: admin
Password: adminpass123
```

This token is set via Docker environment variables and will persist across container restarts.

---

## 📦 Backup Strategy (Avoid Data Loss)

### Why Backup?
- Protects against accidental container deletion
- Allows easy migration to new containers
- Enables disaster recovery

### Quick Backup
```powershell
# Backup InfluxDB data
.\scripts\backup_influxdb.ps1 -Action backup

# Backups are saved to: .\backups\influxdb_backup_YYYY-MM-DD_HH-mm-ss.tar
```

### Quick Restore
```powershell
# Restore from latest backup
.\scripts\backup_influxdb.ps1 -Action restore -BackupPath ".\backups\influxdb_backup_2026-02-16_19-30-00.tar"
```

---

## 🔄 Token Management

### If You Need to Regenerate a Token (Without Losing Data)

**Option 1: Generate New Token via UI (Recommended)**
1. Go to http://localhost:8086
2. Login with: `admin` / `adminpass123`
3. Go to **Data → API Tokens**
4. Click **Generate API Token → All Access Token**
5. Copy the new token
6. Update your `.env` files:
   ```bash
   INFLUXDB_TOKEN=your-new-token-here
   ```
7. Restart backend: `.\venv\Scripts\python -m uvicorn backend.main:app --reload --port 8000`

**Option 2: Use CLI Inside Container**
```powershell
# Create a new token
docker exec enersight-influxdb influx auth create `
  --org enersight `
  --all-access `
  --description "New admin token"

# List all tokens
docker exec enersight-influxdb influx auth list --org enersight
```

---

## 🚨 Emergency: Start Fresh (Without Losing Knowledge)

If InfluxDB is completely broken and you need to reset:

### Step 1: Backup First (If Possible)
```powershell
.\scripts\backup_influxdb.ps1 -Action backup
```

### Step 2: Reset InfluxDB
```powershell
# Stop and remove container + volumes
docker stop enersight-influxdb
docker rm enersight-influxdb
docker volume rm enersight_influxdb-data enersight_influxdb-config

# Start fresh with docker-compose
docker compose up -d influxdb

# Wait 10 seconds for initialization
Start-Sleep -Seconds 10
```

### Step 3: Reload Your Data
```powershell
# Load sample data
cd c:\Users\hp\Desktop\EnerSight
.\venv\Scripts\python backend\scripts\load_data_to_influxdb.py
```

### Step 4: Restore Backup (If You Made One)
```powershell
.\scripts\backup_influxdb.ps1 -Action restore -BackupPath ".\backups\influxdb_backup_latest.tar"
```

---

## 🛡️ Best Practices

### 1. Regular Backups
Set up a scheduled task to backup daily:
```powershell
# Windows Task Scheduler command:
# Run: powershell.exe
# Arguments: -File "C:\Users\hp\Desktop\EnerSight\scripts\backup_influxdb.ps1" -Action backup
```

### 2. Using Docker Volumes (Already Configured)
Your `docker-compose.yml` uses persistent volumes:
```yaml
volumes:
  - influxdb-data:/var/lib/influxdb2      # Stores all data
  - influxdb-config:/etc/influxdb2        # Stores configuration
```

This means:
- ✅ Data persists when container restarts
- ✅ Token settings persist
- ✅ Only lost if you explicitly run `docker volume rm`

### 3. Environment Variables (Already Configured)
The container uses environment variables for initial setup:
```yaml
environment:
  - DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=my-super-secret-auth-token
```

This ensures:
- ✅ Same token every time you recreate the container
- ✅ Predictable authentication
- ✅ Easy to document and share with team

---

## 🔍 Troubleshooting

### Problem: "Unauthorized" or "Token Invalid"

**Solution 1: Check if token is correct**
```powershell
# Test token directly
curl -H "Authorization: Token my-super-secret-auth-token" http://localhost:8086/api/v2/buckets
```

**Solution 2: Verify .env files match**
```powershell
# Check backend .env
Get-Content .\backend\.env | Select-String "INFLUXDB_TOKEN"

# Should show: INFLUXDB_TOKEN=my-super-secret-auth-token
```

**Solution 3: Restart backend to reload env**
```powershell
# Kill old python processes
Get-Process python | Stop-Process -Force

# Start fresh
.\venv\Scripts\python -m uvicorn backend.main:app --reload --port 8000
```

### Problem: "Connection Refused"

**Check if InfluxDB is running:**
```powershell
docker ps | Select-String "influx"
```

**Start if stopped:**
```powershell
docker start enersight-influxdb
```

**Check health:**
```powershell
curl http://localhost:8086/health -UseBasicParsing
```

---

## 📝 Quick Reference Card

| Task | Command |
|------|---------|
| Backup InfluxDB | `.\scripts\backup_influxdb.ps1 -Action backup` |
| Restore InfluxDB | `.\scripts\backup_influxdb.ps1 -Action restore -BackupPath "path"` |
| Check if running | `docker ps \| Select-String influx` |
| View logs | `docker logs enersight-influxdb --tail 50` |
| Restart container | `docker restart enersight-influxdb` |
| Login to UI | http://localhost:8086 (`admin` / `adminpass123`) |
| Test token | `curl -H "Authorization: Token my-super-secret-auth-token" http://localhost:8086/api/v2/buckets` |

---

## 🎓 Why This Setup is Better

### Before (Original Setup)
- ❌ Generated random token via UI
- ❌ Token was user-specific and could expire
- ❌ Hard to share or document
- ❌ Lost when container was recreated
- ❌ No backup strategy

### After (Current Setup)
- ✅ Fixed token in environment variables
- ✅ Persists across container recreations
- ✅ Easy to document and version control
- ✅ Backup/restore scripts available
- ✅ Multiple CORS origins configured (ports 3000, 3001, 5173)
- ✅ Docker volumes preserve data

---

## 🚀 Future Production Considerations

For production deployment, you should:

1. **Use Secrets Management**
   - Store token in Azure Key Vault / AWS Secrets Manager
   - Never commit tokens to Git

2. **Enable TLS/SSL**
   - Use HTTPS for InfluxDB
   - Use proper certificates

3. **Set Up Automated Backups**
   - Daily backups to cloud storage (S3, Azure Blob)
   - Keep 30 days of backups

4. **Monitor Token Usage**
   - Set up alerts for authentication failures
   - Rotate tokens every 90 days

5. **Use Read-Only Tokens for Dashboards**
   - Create separate tokens with limited permissions
   - Admin token only for backend write operations

---

*Last Updated: February 16, 2026*
