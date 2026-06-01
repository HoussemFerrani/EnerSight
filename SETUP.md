# EnerSight — Local Setup

Step-by-step to run EnerSight locally on Windows (PowerShell). For a feature
tour see [README.md](README.md); for production deployment see
[DEPLOYMENT.md](DEPLOYMENT.md).

## Prerequisites

- **Python 3.11**
- **Node.js 20+**
- A **Supabase** project — https://supabase.com/dashboard

## 1. Get the code

```powershell
git clone <your-repo-url> EnerSight
cd EnerSight
```

The trained ML models (`ml/models/trained/*.joblib`, `*.keras`) and the demo
dataset (`data/raw/Energy_consumption.csv`) are committed, so the app runs
without retraining.

## 2. Supabase

1. Create a Supabase project.
2. Apply the database schema — run the migrations documented in
   [DEPLOYMENT.md](DEPLOYMENT.md) in the Supabase SQL editor (tables: profiles,
   alerts, partitioned `energy_readings`, anomalies, `ml_prediction_log`, plus
   the RLS policies and pg_cron jobs).
3. From **Project Settings → API**, copy the Project URL, the `anon` /
   publishable key, and the `service_role` key.
4. From **Project Settings → Database → Connection string (Transaction pooler,
   port 6543)**, copy the URI and URL-encode the password.

## 3. Backend

```powershell
# Virtual environment + dependencies
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt

# Environment file
Copy-Item .env.development .env
# Edit .env and fill in (do NOT commit real secrets — .env is gitignored):
#   SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY,
#   SUPABASE_JWT_SECRET, DATABASE_URL
```

## 4. Frontend

```powershell
npm --prefix frontend install

# frontend/.env.local (gitignored). Create it with:
#   NEXT_PUBLIC_SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
#   NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxx
#   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## 5. Load the sample data

```powershell
.\venv\Scripts\python.exe -m backend.scripts.load_data_to_supabase
```

## 6. Create a test user

Supabase Dashboard → **Authentication → Add user** (email + password). The
`handle_new_user` trigger auto-creates the matching `public.profiles` row.

## 7. Run

```powershell
.\start.ps1
```

This opens the backend on http://localhost:8000 (API docs at `/api/docs`) and
the frontend on http://localhost:3000. To run them manually instead:

```powershell
# Terminal 1 — backend
.\venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000

# Terminal 2 — frontend
npm --prefix frontend run dev
```

## 8. Verify

```powershell
# Should report "status":"healthy" and "postgres":"connected"
curl http://localhost:8000/health

# Predict from conditions — try ?model=rf (default) or ?model=lstm
curl -X POST "http://localhost:8000/api/v1/predictions/predict?model=lstm" `
  -H "Content-Type: application/json" `
  -d '{"temperature":24,"humidity":50,"occupancy":5,"hvac_usage":12,"lighting_usage":3,"equipment_usage":8,"renewable_energy":3}'
```

Then open http://localhost:3000, log in with your test user, and the dashboard
should populate.

## Tests

```powershell
.\venv\Scripts\python.exe -m pytest tests/ -v
```

## (Optional) Retrain models & rebuild metrics

The committed artifacts are ready to use; only run these if you change the data
or models.

```powershell
.\venv\Scripts\python.exe -m ml.training.train_models             # RF / GB / univariate LSTM / anomaly
.\venv\Scripts\python.exe -m ml.training.train_lstm_multivariate  # multivariate LSTM estimator
.\venv\Scripts\python.exe -m ml.evaluation.regenerate_metrics     # rebuild metrics.json from saved models (no retrain)
```

## Troubleshooting

- **`/health` shows `postgres` not connected** — check `DATABASE_URL` in `.env`
  (pooler host, port 6543, URL-encoded password).
- **401 / login fails** — confirm `SUPABASE_URL` + keys match the project, and
  that `frontend/.env.local` uses the same project URL.
- **`.env missing` from `start.ps1`** — you skipped step 3; copy
  `.env.development` to `.env`.
- **Rotated your Supabase keys?** Update `.env` (backend) and
  `frontend/.env.local` (frontend) with the new values, then restart.
