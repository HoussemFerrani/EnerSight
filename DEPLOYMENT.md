# Deployment Guide

EnerSight runs natively — no Docker. The database is Supabase (managed Postgres + Auth). This guide covers local dev, then cloud deployment.

## Contents
1. [Local Development](#local-development)
2. [Supabase Setup](#supabase-setup)
3. [Backend on Render](#backend-on-render)
4. [Frontend on Vercel](#frontend-on-vercel)
5. [Environment Variables](#environment-variables)
6. [Database Migrations](#database-migrations)
7. [Troubleshooting](#troubleshooting)

---

## Local Development

### Prerequisites
- Python 3.11
- Node.js 20+
- A Supabase project

### Steps
1. Copy `.env.development` to `.env` and fill in the Supabase values (see [Environment Variables](#environment-variables)).
2. Create a `frontend/.env.local` with `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
3. Install dependencies:
   ```powershell
   python -m venv venv
   .\venv\Scripts\python.exe -m pip install -r requirements.txt
   npm --prefix frontend install
   ```
4. Load sample data (CSV at `data/raw/Energy_consumption.csv`):
   ```powershell
   .\venv\Scripts\python.exe -m backend.scripts.load_data_to_supabase
   ```
5. Start everything:
   ```powershell
   .\start.ps1
   ```

Backend at http://localhost:8000, frontend at http://localhost:3000.

---

## Supabase Setup

1. Create a project at https://supabase.com/dashboard.
2. Apply the initial schema. The MCP-applied migration creates:
   - `public.profiles` (mirrors `auth.users` via UUID FK, auto-populated by a trigger)
   - `public.user_preferences`
   - `public.energy_readings` (time-series, indexed on `recorded_at`)
   - `public.alerts`, `public.anomalies`, `public.predictions`
3. Enable Row-Level Security on each table. Policies allow each user to read/update their own profile, preferences, and alerts; reads on `energy_readings` and `anomalies` are open to authenticated users; writes use the service role (bypasses RLS).
4. From **Settings → API**, capture:
   - Project URL
   - `anon` / publishable key (frontend)
   - `service_role` secret key (backend)
5. From **Settings → Database → Connection string**, choose **Transaction pooler** and copy the URI. Replace `[YOUR-PASSWORD]` with your DB password. URL-encode any special characters (`@` → `%40`, `?` → `%3F`, etc.).

### Authentication

Modern Supabase projects sign JWTs with **ES256**. The backend fetches the public key from `<SUPABASE_URL>/auth/v1/.well-known/jwks.json` and caches it in memory. No JWT secret is needed in production.

To create a test user, use **Authentication → Add user** in the dashboard. The `handle_new_user` trigger auto-creates a `public.profiles` row.

---

## Backend on Render

[render.yaml](render.yaml) defines the backend service. Render uses the **native Python runtime** — no Docker image is built.

### Deploy
1. Push your repo to GitHub.
2. In Render, click **New → Blueprint** and point it at the repo.
3. Render picks up `render.yaml` and provisions `enersight-backend` (a web service).
4. In the service's Environment tab, paste:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `DATABASE_URL` (the Supabase pooler URI)
   - `CORS_ORIGINS` (set to your frontend domain)
5. Deploy. Render builds with `pip install -r requirements.txt` and starts uvicorn.

Health checks run against `/health`.

### Notes
- Pick a region close to your Supabase region. The project is in `eu-central-1` (Frankfurt); Render's matching region is `frankfurt`.
- `SECRET_KEY` is auto-generated.
- TensorFlow makes the image large — Render's free tier runs out of RAM. Use `starter` plan or higher.

---

## Frontend on Vercel

Vercel is the native target for Next.js — zero-config deploy.

1. Push your repo to GitHub.
2. In Vercel, **New Project → Import** the repo.
3. Set the **root directory** to `frontend/`.
4. Vercel auto-detects Next.js (16, App Router) and uses `npm run build` → `.next/`.
5. Under **Environment Variables**, add:
   - `NEXT_PUBLIC_API_URL` → your Render backend URL + `/api/v1`
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
6. Deploy.

Netlify and Cloudflare Pages also support Next.js (via their respective Next adapters), but Vercel is the smoothest path.

---

## Environment Variables

### Backend (`.env`)

| Variable | Example | Purpose |
|---|---|---|
| `ENVIRONMENT` | `production` | Affects logging, docs visibility |
| `SUPABASE_URL` | `https://xxx.supabase.co` | Project URL |
| `SUPABASE_ANON_KEY` | `sb_publishable_...` | Frontend-safe key |
| `SUPABASE_SERVICE_ROLE_KEY` | `eyJ...` | Server-only admin key |
| `DATABASE_URL` | `postgresql://postgres.<ref>:<pw>@aws-1-eu-central-1.pooler.supabase.com:6543/postgres` | Supabase pooler URI |
| `SECRET_KEY` | random ≥32 chars | App-level secret |
| `CORS_ORIGINS` | comma-separated origins | Allowed browser origins |
| `LOG_LEVEL` | `INFO` | Logger threshold |

### Frontend (`frontend/.env.local`)

| Variable | Example |
|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://xxx.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `sb_publishable_...` |

---

## Database Migrations

Schema changes happen via the Supabase MCP `apply_migration` tool (or the Supabase CLI / SQL editor). Migrations are stored on the Supabase side; the repo doesn't ship raw SQL files.

To inspect or evolve the schema:
```sql
-- via Supabase SQL editor or the MCP execute_sql tool
select table_name from information_schema.tables where table_schema = 'public';
```

After any DDL change, run the Supabase **advisors** check (security + performance) and resolve warnings.

---

## Troubleshooting

### "Tenant or user not found"
The Supabase pooler couldn't match your `postgres.<project_ref>` user. The pooler hostname is region-specific — for newer projects in eu-central-1 it's `aws-1-eu-central-1.pooler.supabase.com`, not `aws-0`. Copy the exact connection string from the Supabase dashboard.

### "FATAL: password authentication failed for user 'postgres'"
- Wrong DB password — reset it in **Settings → Database**.
- URL-encoded password decoded incorrectly — check that special characters are correctly percent-encoded.
- Pooler credential cache may be stale for ~30 seconds after a reset.

### "Invalid or expired token" (401)
- Backend wasn't fetching the right JWKS. Confirm `SUPABASE_URL` is set and `<url>/auth/v1/.well-known/jwks.json` returns keys.
- The token was signed with HS256 but the backend expects ES256 (or vice versa). See [backend/utils/auth.py](backend/utils/auth.py) — it auto-detects from the JWT header.

### "ML model error: <model> not loaded"
Train them locally and re-deploy with the `joblib`/`keras` files:
```powershell
.\venv\Scripts\python.exe -c "from ml.models.regression_model import train_regression_model; train_regression_model('data/raw/Energy_consumption.csv', 'random_forest')"
.\venv\Scripts\python.exe -c "from ml.models.anomaly_detector import train_anomaly_detector; train_anomaly_detector('data/raw/Energy_consumption.csv')"
```

### Frontend shows a white screen
Browser console almost always tells you. Common culprits:
- Missing `NEXT_PUBLIC_SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_ANON_KEY` in `frontend/.env.local`
- Backend not running (network errors on every request)
- Stale Next.js build cache — delete `frontend/.next/` and restart `npm run dev`, then hard-refresh with Ctrl+Shift+R

### "Session expired" on Alerts/Analytics
The old `enersight_auth_token` localStorage key is gone. All client-side calls to the FastAPI backend must use the shared axios instance in [frontend/src/lib/api/backend.ts](frontend/src/lib/api/backend.ts), which pulls the Supabase access token from `@supabase/ssr` and attaches it as `Authorization: Bearer …` automatically.
