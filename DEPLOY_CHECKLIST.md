# 🚀 Quick Deploy Checklist

## Before Deploying

- [ ] Push code to GitHub
- [ ] Sign up for InfluxDB Cloud (free)
- [ ] Get InfluxDB token and details
- [ ] Sign up for Render.com

## Deploy Steps

### 1. InfluxDB Cloud Setup (5 min)
```
1. https://cloud2.influxdata.com/signup
2. Create org: "enersight"
3. Create bucket: "energy_data"
4. Generate token → Copy it
```

### 2. Push to GitHub (2 min)
```bash
git init
git add .
git commit -m "Deploy to Render"
git remote add origin https://github.com/YOUR_USERNAME/enersight.git
git push -u origin main
```

### 3. Deploy on Render (10 min)
```
1. https://dashboard.render.com/
2. New → Blueprint
3. Select your repo
4. Apply render.yaml
5. Wait for deployment
```

### 4. Set Environment Variables
In Render dashboard, backend service:
```
INFLUXDB_URL=[your cloud URL]
INFLUXDB_TOKEN=[your token]
SMTP_USERNAME=[optional]
SMTP_PASSWORD=[optional]
```

### 5. Update CORS
After frontend deploys, update backend:
```
CORS_ORIGINS=https://your-frontend.onrender.com
```

### 6. Access App
```
Frontend: https://enersight-frontend.onrender.com
Backend: https://enersight-backend.onrender.com/docs

Login: johndoe / SecurePass123!
```

## Keep It Awake (Optional)

Use UptimeRobot (free):
```
1. https://uptimerobot.com
2. Add monitor → Your backend /health endpoint
3. 5 min interval
```

## Cost
**$0/month** 🎉

---

📖 Full guide: [DEPLOYMENT_FREE.md](DEPLOYMENT_FREE.md)
