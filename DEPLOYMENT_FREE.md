# 🆓 FREE Deployment Guide - Render.com

## Total Cost: **$0/month** ✨

---

## 📋 Overview

**What We're Deploying:**
- Backend (FastAPI) → Render Web Service (FREE)
- Frontend (React) → Render Static Site (FREE)
- PostgreSQL → Render PostgreSQL (FREE - 1GB storage)
- Redis → Render Redis (FREE - 25MB)
- InfluxDB → InfluxDB Cloud (FREE - 30 day retention)

**Limitations:**
- ⚠️ Services sleep after 15 min inactivity (30s cold start)
- ⚠️ PostgreSQL data older than 90 days auto-deleted
- ⚠️ 750 hours/month per service (enough for 1-2 services always-on)

---

## 🚀 Step-by-Step Deployment

### 1️⃣ Setup InfluxDB Cloud (External)

InfluxDB doesn't have native Render support, use their free cloud tier:

1. Go to https://cloud2.influxdata.com/signup
2. Create free account
3. Create organization (e.g., "enersight")
4. Create bucket: `energy_data`
5. Generate API token:
   - Go to **Data** → **API Tokens**
   - Click **Generate API Token** → **All Access Token**
   - Copy token (starts with `your-token-here`)
6. Note your details:
   ```
   URL: https://us-east-1-1.aws.cloud2.influxdata.com (or your region)
   Organization: enersight
   Bucket: energy_data
   Token: [your-copied-token]
   ```

---

### 2️⃣ Push Code to GitHub

```bash
cd EnerSight

# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Prepare for Render deployment"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/enersight.git
git branch -M main
git push -u origin main
```

---

### 3️⃣ Deploy on Render

#### **Option A: Using Blueprint (render.yaml) - RECOMMENDED**

1. Go to https://dashboard.render.com/
2. Sign up / Log in with GitHub
3. Click **New** → **Blueprint**
4. Connect your GitHub repository
5. Render will auto-detect `render.yaml`
6. Click **Apply**
7. Wait for all services to deploy (~5-10 minutes)

#### **Option B: Manual Setup**

**a) Create PostgreSQL Database:**
1. Dashboard → **New** → **PostgreSQL**
2. Name: `enersight-postgres`
3. Database: `enersight`
4. User: `enersight_user`
5. Region: Choose closest to you
6. Plan: **Free**
7. Click **Create Database**
8. Copy **Internal Database URL** (starts with `postgresql://`)

**b) Create Redis:**
1. Dashboard → **New** → **Redis**
2. Name: `enersight-redis`
3. Plan: **Free**
4. Click **Create Redis**
5. Note the hostname and port

**c) Deploy Backend:**
1. Dashboard → **New** → **Web Service**
2. Connect GitHub repo
3. Settings:
   - **Name:** `enersight-backend`
   - **Environment:** `Docker`
   - **Dockerfile Path:** `backend/Dockerfile`
   - **Plan:** `Free`
   - **Health Check Path:** `/health`
4. Add Environment Variables:
   ```
   ENVIRONMENT=production
   API_HOST=0.0.0.0
   API_PORT=8000
   
   # PostgreSQL (use Internal Database URL)
   POSTGRES_HOST=[from database]
   POSTGRES_PORT=5432
   POSTGRES_DB=enersight
   POSTGRES_USER=enersight_user
   POSTGRES_PASSWORD=[from database]
   
   # InfluxDB Cloud
   INFLUXDB_URL=[your cloud URL]
   INFLUXDB_TOKEN=[your token]
   INFLUXDB_ORG=enersight
   INFLUXDB_BUCKET=energy_data
   
   # Redis
   REDIS_HOST=[from redis service]
   REDIS_PORT=[from redis service]
   
   # Security (generate random strings)
   SECRET_KEY=[run: openssl rand -hex 32]
   JWT_SECRET_KEY=[run: openssl rand -hex 32]
   
   # CORS (update after frontend deployed)
   CORS_ORIGINS=https://enersight.onrender.com
   
   # Email (optional - use Gmail app password)
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=[Gmail app password]
   EMAIL_FROM=noreply@enersight.com
   
   # Disable features that need local files
   ENABLE_MQTT=False
   ML_MODELS_PATH=/tmp/models
   ```
5. Click **Create Web Service**

**d) Deploy Frontend:**
1. Dashboard → **New** → **Static Site**
2. Connect GitHub repo
3. Settings:
   - **Name:** `enersight-frontend`
   - **Build Command:** `cd frontend && npm ci && npm run build`
   - **Publish Directory:** `frontend/dist`
   - **Plan:** `Free`
4. Add Environment Variable:
   ```
   VITE_API_URL=https://enersight-backend.onrender.com/api/v1
   ```
5. Add Rewrite Rule (for React Router):
   - Source: `/*`
   - Destination: `/index.html`
   - Action: `Rewrite`
6. Click **Create Static Site**

---

### 4️⃣ Update CORS After Deployment

1. Go to backend service settings
2. Update `CORS_ORIGINS` to your frontend URL:
   ```
   CORS_ORIGINS=https://enersight.onrender.com,https://enersight-frontend.onrender.com
   ```
3. Click **Save Changes** (triggers redeploy)

---

### 5️⃣ Initialize Database

Connect to your backend shell:

```bash
# Option 1: Use Render Shell
# Go to backend service → Shell tab → Click "Launch Shell"

# Option 2: Use local connection
# Get connection string from Render dashboard, then:
docker compose run backend python -c "
from backend.database.models import Base
from backend.database.connection import engine
Base.metadata.create_all(bind=engine)
print('Database initialized!')
"
```

Or via Render dashboard:
1. Backend service → **Shell**
2. Run:
   ```bash
   python -c "from backend.database.models import Base; from backend.database.connection import engine; Base.metadata.create_all(bind=engine)"
   ```

---

### 6️⃣ Load Initial Data (Optional)

If you want to seed data:

```bash
# In Render Shell for backend
python backend/scripts/load_data_to_influxdb.py
```

---

## 🌐 Access Your App

After deployment completes (~10 minutes):

- **Frontend:** `https://enersight-frontend.onrender.com`
- **Backend API:** `https://enersight-backend.onrender.com/docs`
- **InfluxDB UI:** `https://cloud2.influxdata.com` (your cloud instance)

**Default Login:**
- Username: `johndoe`
- Password: `SecurePass123!`

---

## ⚙️ Important Settings

### Auto-Deploy on Git Push

1. Go to each service settings
2. Enable **Auto-Deploy**
3. Select branch: `main`
4. Every push to main will trigger redeployment

### Keep Services Awake (Optional)

Free tier services sleep after 15 min. To prevent:

**Option 1: UptimeRobot (Free)**
1. Sign up at https://uptimerobot.com
2. Add monitor:
   - Type: HTTP(s)
   - URL: `https://enersight-backend.onrender.com/health`
   - Interval: 5 minutes
3. This pings your backend every 5 min, keeping it awake

**Option 2: Cron Job (Render Cron - Paid)**
- Requires paid plan

---

## 🔧 Troubleshooting

### Backend Won't Start

**Check Logs:**
```
Dashboard → Backend Service → Logs
```

**Common Issues:**
1. **Database connection failed:**
   - Verify `POSTGRES_HOST` matches internal hostname
   - Check PostgreSQL is running

2. **InfluxDB connection failed:**
   - Verify `INFLUXDB_URL`, `INFLUXDB_TOKEN`, `INFLUXDB_ORG`
   - Check token hasn't expired

3. **Redis connection failed:**
   - Verify `REDIS_HOST` and `REDIS_PORT`
   - Redis must be in same region

### Frontend Shows Blank Page

1. **Check build logs** for errors
2. **Verify API URL:**
   - Must match backend service URL
   - Should end with `/api/v1`
3. **Check CORS:**
   - Backend must allow frontend domain

### Services Keep Sleeping

- Use UptimeRobot (free) to ping every 5 min
- Or upgrade to paid plan ($7/month) for always-on

### Database Connection Refused

- Use **Internal Database URL**, not external
- Format: `postgresql://user:pass@host:5432/db`
- Internal URLs work within Render network (faster, no egress fees)

---

## 💰 Cost Breakdown

| Service | Plan | Cost |
|---------|------|------|
| PostgreSQL | Free (1GB) | $0 |
| Redis | Free (25MB) | $0 |
| Backend | Free (750h) | $0 |
| Frontend | Free | $0 |
| InfluxDB | Cloud Free | $0 |
| **Total** | | **$0/month** ✨ |

**Upgrade Costs (if needed):**
- PostgreSQL: $7/month (10GB, no retention limit)
- Redis: $10/month (1GB)
- Backend: $7/month (always-on, 512MB RAM)
- Total upgraded: ~$24/month

---

## 🎯 Alternative Free Options

### Fly.io
- 3 VMs free (256MB each)
- PostgreSQL addon free (3GB)
- Better for "always-on" apps
- Guide: https://fly.io/docs/languages-and-frameworks/dockerfile/

### Railway
- $5/month free credit
- Better DX than Render
- Credits run out quickly with multiple services
- Guide: https://docs.railway.app/getting-started

### Koyeb
- 1 free service
- Docker support
- Good for single containerized app
- Guide: https://www.koyeb.com/docs/deploy

---

## 📚 Next Steps

1. ✅ Deploy to Render (this guide)
2. 🔒 Setup custom domain (optional)
3. 📧 Configure email alerts (Gmail app password)
4. 📊 Setup UptimeRobot monitoring
5. 🔐 Add SSL certificate (auto with custom domain)
6. 🚀 Share your app!

---

## 🆘 Need Help?

- Render Docs: https://render.com/docs
- InfluxDB Cloud: https://docs.influxdata.com/influxdb/cloud/
- Community: https://community.render.com/

**Common Commands:**

```bash
# View backend logs
render logs -s enersight-backend

# Restart service
render restart -s enersight-backend

# Open dashboard
render open
```

---

**Your app is now live and FREE! 🎉**
