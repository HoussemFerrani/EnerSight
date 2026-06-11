# EnerSight — Project Overview

EnerSight is a smart energy-management platform that monitors building energy
consumption, predicts it from environmental and usage conditions, detects
anomalies, and recommends concrete efficiency actions. It is built as a
full-stack application backed by Supabase (Postgres + Auth).

For hands-on install/run instructions see [SETUP.md](SETUP.md); for the full
feature reference see [README.md](README.md); for deployment see
[DEPLOYMENT.md](DEPLOYMENT.md).

## The problem it solves

Buildings waste energy in ways that are invisible without analytics: HVAC
running while unoccupied, lighting left on, baseline "phantom" loads at the
weekend, and renewable generation that isn't used when it's available.
EnerSight turns raw sensor readings into three actionable layers:

1. **Visibility** — dashboards and reports over historical consumption.
2. **Prediction** — estimate consumption from conditions (temperature,
   occupancy, HVAC/lighting state, renewable output, …).
3. **Action** — anomaly flags for *unknown* problems and an explainable rules
   engine for *known* inefficiencies, each with projected savings.

## Architecture

```
┌──────────────┐     HTTPS / JWT      ┌──────────────────┐      ┌─────────────┐
│  Next.js 16  │ ───────────────────► │   FastAPI         │ ───► │  Supabase   │
│  (App Router)│  Authorization:      │   (Python 3.11)   │      │  Postgres   │
│  React 19    │  Bearer <token>      │   services/ +     │      │  + Auth     │
│  Recharts    │ ◄─────────────────── │   repositories/   │ ◄─── │  (RLS)      │
└──────────────┘      JSON            └────────┬──────────┘      └─────────────┘
                                               │ loads
                                      ┌────────▼──────────┐
                                      │  ml/models/trained│
                                      │  RF · GB · LSTM ·  │
                                      │  IsolationForest   │
                                      └───────────────────┘
```

- **Frontend** (`frontend/`) — Next.js App Router + React 19 + TypeScript,
  Tailwind 4, Base UI / shadcn-style components, Recharts. Auth via
  `@supabase/ssr`; all data flows through the FastAPI backend (the browser
  never queries the data tables directly).
- **Backend** (`backend/`) — FastAPI with a clean layering: `api/` routes →
  `services/` (business logic) → `repositories/` (data access) over SQLAlchemy.
  Supabase access tokens are verified as ES256 JWTs via the project JWKS.
- **Data** (Supabase Postgres) — auth, profiles, alerts, the partitioned
  `energy_readings` time-series (pg_partman + pg_cron), anomalies, and the
  `ml_prediction_log` used for live drift monitoring.
- **ML** (`ml/`) — model classes, training pipelines, and an evaluation /
  metrics-regeneration step. Trained artifacts are committed under
  `ml/models/trained/` so a fresh clone runs without retraining.

## Machine learning

| Model | Role | Quality |
|---|---|---|
| Random Forest | Default consumption predictor (`/predict`) | R² ≈ 0.54, RMSE ≈ 5.5 kWh |
| Gradient Boosting | Benchmark predictor | similar |
| **Multivariate LSTM** | Concurrent estimator (`/predict?model=lstm`) | **R² ≈ 0.59, RMSE ≈ 5.0 kWh** — strongest |
| Isolation Forest | Anomaly detection (rules + IF hybrid) | hybrid F1 ≈ 0.79 |
| Univariate LSTM | Legacy forecaster + TFLite edge demo | see caveat below |

**Honest note on forecasting.** The sample dataset is *temporally random* —
consumption and its drivers have ~zero hour-to-hour autocorrelation, so
consumption is explained by *concurrent* conditions (Temperature corr +0.70),
not by its own past. True time-series forecasting therefore can't beat a mean
predictor on this data, which is why the LSTM is framed as a **concurrent
multivariate estimator** rather than a forecaster. R² (not the MAPE-based
"accuracy", which is flattered by the tight target) is the honest metric; it is
capped near ~0.55 by how much the measured features explain. See the README's
[forecasting-vs-estimation note](README.md#a-note-on-forecasting-vs-estimation-important).

## Key features

- Real-time and historical energy dashboards (Recharts).
- Consumption prediction with a selectable model (RF or multivariate LSTM).
- Anomaly detection (Isolation Forest) with rule-based explanations.
- Model accuracy, 5-fold cross-validation, and live drift monitoring.
- Optimization recommendations with projected monthly kWh / USD savings.
- Downloadable PDF period reports and CSV exports.
- Supabase Auth (email/password, JWT) with RLS-locked data tables.

## Repository layout

See the **Project Structure** section of [README.md](README.md#project-structure)
for the annotated tree.
