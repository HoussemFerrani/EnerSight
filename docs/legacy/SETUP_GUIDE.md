> ⚠️ **OUTDATED** — This guide describes the pre-migration stack (InfluxDB, Vite, Docker). The current stack is **Supabase (Postgres + Auth)**, **Next.js 16 (App Router)**, and a native FastAPI deployment (no Docker). For accurate setup instructions see [README.md](../README.md#quick-start) and [DEPLOYMENT.md](../DEPLOYMENT.md). This file is kept for historical context only.

---

# EnerSight Setup Guide

Complete installation and setup instructions for the EnerSight platform.

## Prerequisites

- **Python**: 3.9 or higher
- **Node.js**: 16.x or higher
- **InfluxDB**: 2.x
- **MQTT Broker**: Mosquitto or similar
- **Git**: For version control

## 📦 Step 1: Clone and Setup Environment

```bash
# Navigate to project directory
cd c:\Users\hp\Desktop\EnerSight

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

## 🗄️ Step 2: Setup InfluxDB

### Install InfluxDB

**Windows:**
Download from: https://portal.influxdata.com/downloads/

**Linux:**
```bash
wget https://dl.influxdata.com/influxdb/releases/influxdb2-2.7.1-amd64.deb
sudo dpkg -i influxdb2-2.7.1-amd64.deb
sudo systemctl start influxdb
```

### Configure InfluxDB

1. Open browser: `http://localhost:8086`
2. Complete setup wizard:
   - Username: `admin`
   - Password: (choose secure password)
   - Organization: `enersight`
   - Bucket: `energy_data`
3. Generate API token: Settings → Tokens → Generate Token
4. Copy token for `.env` file

## 🔌 Step 3: Setup MQTT Broker

**Windows (Mosquitto):**
```bash
# Download from: https://mosquitto.org/download/
# Install and start service
net start mosquitto
```

**Linux:**
```bash
sudo apt-get install mosquitto mosquitto-clients
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

**Test MQTT:**
```bash
# Terminal 1 - Subscribe
mosquitto_sub -h localhost -t test

# Terminal 2 - Publish
mosquitto_pub -h localhost -t test -m "Hello MQTT"
```

## ⚙️ Step 4: Environment Configuration

```bash
# Copy example environment file
copy .env.example .env

# Edit .env with your actual credentials
# Update:
# - INFLUXDB_TOKEN (from Step 2)
# - POSTGRES_PASSWORD
# - SECRET_KEY
```

## 📊 Step 5: Load Dataset

```bash
# Copy your dataset to data folder
copy "c:\Users\hp\Desktop\PFE\Energy_consumption.csv" "data\raw\Energy_consumption.csv"

# Load data into InfluxDB
python scripts\load_data_to_influxdb.py --csv data/raw/Energy_consumption.csv --token YOUR_INFLUX_TOKEN
```

## 🤖 Step 6: Train ML Models

```bash
# Train all models
python ml\training\train_models.py --data data/raw/Energy_consumption.csv

# Train specific model
python ml\training\train_models.py --models regression
python ml\training\train_models.py --models lstm
python ml\training\train_models.py --models anomaly
```

Expected output:
```
Training regression model...
✓ RMSE: 5.23
✓ R²: 0.94
Model saved to ml/models/trained/
```

## 🚀 Step 7: Start Backend

```bash
# Activate virtual environment
venv\Scripts\activate

# Start FastAPI server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Test API: `http://localhost:8000/docs`

## 🎨 Step 8: Start Frontend

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend available at: `http://localhost:3000`

## 🔄 Step 9: Simulate IoT Sensors (Optional)

```bash
# In new terminal
python scripts\mqtt_simulator.py --data data/raw/Energy_consumption.csv --interval 5
```

This simulates real-time sensor data publishing to MQTT every 5 seconds.

## 📈 Step 10: Setup Grafana (Optional)

```bash
# Install Grafana
# Windows: Download from https://grafana.com/grafana/download
# Linux:
sudo apt-get install -y grafana

# Start Grafana
sudo systemctl start grafana-server

# Access: http://localhost:3000
# Default credentials: admin/admin
```

**Configure InfluxDB Data Source:**
1. Settings → Data Sources → Add InfluxDB
2. Query Language: Flux
3. URL: `http://localhost:8086`
4. Organization: `enersight`
5. Token: (your InfluxDB token)
6. Save & Test

## ✅ Verification Checklist

- [ ] InfluxDB running on port 8086
- [ ] MQTT broker running on port 1883
- [ ] Backend API accessible at http://localhost:8000
- [ ] Frontend dashboard at http://localhost:3000
- [ ] ML models trained in `ml/models/trained/`
- [ ] Dataset loaded in `data/raw/`

## 🧪 Testing

```bash
# Test API health
curl http://localhost:8000/health

# Test MQTT
python scripts\mqtt_simulator.py --interval 2

# Run unit tests
pytest tests/
```

## 🐛 Troubleshooting

### InfluxDB Connection Error
```bash
# Check if InfluxDB is running
curl http://localhost:8086/health

# Verify token in .env file
```

### MQTT Connection Failed
```bash
# Check Mosquitto service
net start mosquitto  # Windows
sudo systemctl status mosquitto  # Linux
```

### Frontend API Error
```bash
# Ensure backend is running
# Check CORS settings in backend/main.py
# Verify VITE_API_URL in frontend/.env
```

### Model Training Fails
```bash
# Check dataset path
# Ensure all dependencies installed
pip install -r requirements.txt
```

## 🔐 Security Notes

**For Production:**
1. Change all default passwords
2. Use strong SECRET_KEY
3. Configure CORS properly
4. Use HTTPS
5. Enable authentication
6. Secure database connections

## 📚 Next Steps

1. Customize Grafana dashboards
2. Add user authentication
3. Configure email alerts
4. Deploy to cloud (AWS, Azure, GCP)
5. Setup CI/CD pipeline

## 💡 Useful Commands

```bash
# Backend
uvicorn backend.main:app --reload

# Frontend
cd frontend && npm run dev

# Train models
python ml/training/train_models.py

# Simulate sensors
python scripts/mqtt_simulator.py

# Load data
python scripts/load_data_to_influxdb.py --csv data/raw/Energy_consumption.csv
```

---

For more help, check the documentation in the `docs/` folder or raise an issue on GitHub.
