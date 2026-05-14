# EnerSight - Smart Energy Management and Monitoring Platform

An IoT-style platform for real-time energy monitoring, predictive analytics, and anomaly detection.

![Status](https://img.shields.io/badge/status-active-green)
![Python](https://img.shields.io/badge/python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![React](https://img.shields.io/badge/React-18.2-blue)
![Supabase](https://img.shields.io/badge/Supabase-Postgres-3ECF8E)

## Overview

EnerSight monitors, analyzes, and optimizes building energy consumption using IoT sensor data, machine learning, and real-time analytics. Backed by Supabase (Postgres + Auth) and a FastAPI + React stack.

## Features

- **Real-time monitoring** — live energy consumption tracking
- **ML predictions** — Random Forest, Gradient Boosting, and LSTM
- **Anomaly detection** — Isolation Forest with explanations
- **Interactive dashboards** — Recharts + Chart.js visualizations
- **Authentication** — Supabase Auth (email/password, JWT)
- **Alerts** — threshold breaches surface as per-user alerts

## Tech Stack

**Backend**
- Python 3.11
- FastAPI 0.109
- SQLAlchemy 2.0 (sync + async)
- PyJWT (Supabase ES256 JWT verification via JWKS)
- supabase-py (auth admin)
- scikit-learn / TensorFlow / Keras

**Frontend**
- React 18 + Vite
- @supabase/supabase-js
- Material UI, Recharts, Chart.js, Axios

**Data**
- Supabase Postgres (auth, profiles, alerts, energy time-series, anomalies, predictions)
- Supabase Auth (replaces the previous custom JWT)

## Project Structure

```
EnerSight/
├── backend/                # FastAPI application
│   ├── api/                # REST + WebSocket routes
│   ├── core/               # Config, DI, logging, errors
│   ├── database/           # Supabase Postgres engine
│   ├── models/             # SQLAlchemy ORM models
│   ├── repositories/       # Data access layer
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   ├── scripts/            # Data loader
│   └── utils/              # JWT verification, helpers
├── frontend/               # React + Vite app
│   ├── src/
│   │   ├── components/     # Shared UI
│   │   ├── pages/          # Dashboard, Analytics, Alerts, etc.
│   │   └── services/       # supabaseClient, api, alertService, ...
├── ml/                     # ML models
│   ├── models/             # Regression / LSTM / Anomaly classes
│   └── training/           # Training pipelines
├── data/raw/               # Source CSV(s) (ignored by git)
├── render.yaml             # Render deployment (backend only)
├── start.ps1               # One-shot local launcher (Windows)
└── requirements.txt
```

## Quick Start

### Prerequisites
- Python 3.11
- Node.js 20+
- A Supabase project — get one at https://supabase.com/dashboard

### 1. Set up Supabase
1. Create a project.
2. Open the SQL editor and run the migration from your local Supabase MCP, or apply the schema documented in `DEPLOYMENT.md`.
3. From **Project Settings → API**, copy:
   - Project URL
   - `anon` / publishable key
   - `service_role` key
4. From **Project Settings → Database → Connection string (Transaction pooler, port 6543)**, copy the URI and replace `[YOUR-PASSWORD]` with your database password.

### 2. Configure environment
```powershell
cp .env.development .env
# Edit .env and fill in:
#   SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, DATABASE_URL
# Plus (for the frontend, in frontend/.env.local):
#   VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY
```

### 3. Install dependencies
```powershell
# Backend
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt

# Frontend
npm --prefix frontend install
```

### 4. Load sample data
Drop your CSV at `data/raw/Energy_consumption.csv`, then:
```powershell
.\venv\Scripts\python.exe -m backend.scripts.load_data_to_supabase
```

### 5. Create a test user
Either via Supabase Dashboard → Authentication → Add user, or via the admin API. The `handle_new_user` trigger auto-creates a row in `public.profiles`.

### 6. Run
```powershell
.\start.ps1
```
This launches:
- Backend: http://localhost:8000 (docs at `/api/docs`)
- Frontend: http://localhost:3000

## API Endpoints

### Energy
- `GET /api/v1/energy/statistics` — period statistics
- `GET /api/v1/energy/readings` — raw/aggregated readings
- `POST /api/v1/energy/readings` — submit a reading

### Predictions
- `POST /api/v1/predictions/predict` — single prediction
- `POST /api/v1/predictions/forecast` — forecast horizon

### Anomalies
- `GET /api/v1/anomalies/detect` — run detection
- `GET /api/v1/anomalies/history` — recent results

### Alerts
- `GET /api/v1/alerts/` — list current user's alerts
- `POST /api/v1/alerts/{id}/acknowledge` — acknowledge an alert

### Auth
- `GET /api/v1/auth/me` — current user's profile
- `GET /api/v1/auth/verify` — verify token validity

### System
- `GET /health` — service health
- `GET /api/v1/info` — API capabilities

## Dataset

CSV columns expected by [load_data_to_supabase.py](backend/scripts/load_data_to_supabase.py):
- `Timestamp`, `EnergyConsumption`, `Temperature`, `Humidity`
- `SquareFootage`, `Occupancy`, `HVACUsage`, `LightingUsage`
- `RenewableEnergy`, `DayOfWeek`, `Holiday`

## Authentication

The backend verifies Supabase access tokens using **ES256** asymmetric signatures, fetching the public key from the project's JWKS endpoint (`/auth/v1/.well-known/jwks.json`). The frontend uses `@supabase/supabase-js` for sign-in/sign-out and the shared axios instance in [api.js](frontend/src/services/api.js) attaches the access token automatically.

## ML Models

- **Random Forest Regressor** — primary prediction (`ml/models/regression_model.py`)
- **LSTM** — sequential forecasting (`ml/models/lstm_model.py`)
- **Isolation Forest** — anomaly detection (`ml/models/anomaly_detector.py`)

Trained artifacts live in `ml/models/trained/`. Retrain locally via:
```powershell
.\venv\Scripts\python.exe -c "from ml.models.regression_model import train_regression_model; train_regression_model('data/raw/Energy_consumption.csv', 'random_forest')"
```

## Deployment

The backend deploys to Render via [render.yaml](render.yaml) on the native Python runtime — no Docker. The frontend deploys to Vercel/Netlify/Cloudflare Pages with `npm run build`.

See [DEPLOYMENT.md](DEPLOYMENT.md) for the full guide.

## Development

### Tests
```powershell
.\venv\Scripts\python.exe -m pytest tests/ -v
```

### Linting / type checking
```powershell
.\venv\Scripts\python.exe -m black backend/
.\venv\Scripts\python.exe -m isort backend/
.\venv\Scripts\python.exe -m mypy backend/
```

## License

MIT — see `LICENSE`.
