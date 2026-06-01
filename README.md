# EnerSight - Smart Energy Management and Monitoring Platform

An IoT-style platform for real-time energy monitoring, predictive analytics, and anomaly detection.

![Status](https://img.shields.io/badge/status-active-green)
![Python](https://img.shields.io/badge/python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![Next.js](https://img.shields.io/badge/Next.js-16-black)
![React](https://img.shields.io/badge/React-19-blue)
![Supabase](https://img.shields.io/badge/Supabase-Postgres-3ECF8E)

## Overview

EnerSight monitors, analyzes, and optimizes building energy consumption using IoT sensor data, machine learning, and real-time analytics. Backed by Supabase (Postgres + Auth) and a FastAPI + Next.js stack.

## Features

- **Real-time monitoring** — live energy consumption tracking
- **ML predictions** — Random Forest / Gradient Boosting regressors and a multivariate LSTM estimator (pick the model on the predictions page or via `/predict?model=rf|lstm`)
- **Anomaly detection** — Isolation Forest with explanations
- **Model accuracy & drift monitoring** — training-time metrics, k-fold cross-validation, predicted-vs-actual charts, and live drift backfilled in-database via pg_cron (see [Model Accuracy & Drift Monitoring](#model-accuracy--drift-monitoring))
- **Optimization recommendations** — rules engine that suggests concrete actions to reduce waste, with projected monthly savings (see [Optimization Recommendations](#optimization-recommendations))
- **Reports** — downloadable PDF period reports + CSV export of raw readings (see [Reports](#reports))
- **Edge-deployable ML** — the (legacy univariate) LSTM forecaster has a TensorFlow Lite variant (~8× smaller, ~49× faster on CPU), shown as an edge-deployment exercise; see [TensorFlow Lite Inference](#tensorflow-lite-inference)
- **Interactive dashboards** — Recharts visualizations
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
- Next.js 16 (App Router) + React 19 + TypeScript
- @supabase/ssr + @supabase/supabase-js
- Tailwind CSS 4, shadcn/ui, Base UI, lucide-react, sonner
- Recharts, Axios

**Data**
- Supabase Postgres (auth, profiles, alerts, energy time-series, anomalies, predictions)
- Supabase Auth (replaces the previous custom JWT)
- **pg_partman + pg_cron** — declarative monthly partitioning of the energy time-series table, with automated partition creation and retention (see [Time-Series Storage](#time-series-storage))

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
├── frontend/               # Next.js (App Router) app
│   ├── src/
│   │   ├── app/            # Routes: login, (app)/{dashboard,analytics,alerts,...}
│   │   ├── components/     # Shared UI
│   │   └── lib/            # supabase client/server, api/backend.ts, utils
├── ml/                     # ML models
│   ├── models/             # Regression / LSTM / Anomaly classes
│   ├── training/           # Training pipelines (+ TFLite export, benchmark)
│   └── evaluation/         # K-fold CV + anomaly P/R evaluation script
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
#   NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY
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
- `POST /api/v1/predictions/predict` — single prediction from current conditions. Pick the model with `?model=rf` (Random Forest, default) or `?model=lstm` (multivariate LSTM estimator). Optional `for_timestamp` ISO-8601 anchors the prediction for drift backfill.
- `POST /api/v1/predictions/forecast` — legacy time-series forecast horizon (univariate LSTM; see the forecasting caveat under [ML Models](#ml-models))

### ML Monitoring (auth required)
- `GET /api/v1/ml/metrics` — training-time RMSE/MAE/R²/MAPE/Accuracy per model
- `GET /api/v1/ml/evaluation` — 5-fold cross-validation results + anomaly precision/recall/F1
- `GET /api/v1/ml/predictions` — sampled predicted-vs-actual series for the chart
- `GET /api/v1/ml/drift/summary` — live counters (total / backfilled / pending / live accuracy)
- `GET /api/v1/ml/drift?hours=168&bucket=hour` — bucketed MAPE-over-time series
- `POST /api/v1/ml/backfill?limit=500` — fill in `actual_value` for past predictions (also runs automatically every 15 min via `pg_cron`)
- `GET /api/v1/ml/log?limit=50` — recent prediction log entries (debugging)

### Anomalies
- `GET /api/v1/anomalies/detect` — run detection
- `GET /api/v1/anomalies/history` — recent results

### Alerts
- `GET /api/v1/alerts/` — list current user's alerts
- `POST /api/v1/alerts/{id}/acknowledge` — acknowledge an alert

### Optimizations
- `GET /api/v1/optimizations/` — ranked list of actionable energy-efficiency recommendations with projected monthly savings (kWh + USD)

### Reports
- `GET /api/v1/reports/period.pdf` — generated PDF period report (summary, charts, outliers, recommendations)
- `GET /api/v1/reports/period.csv` — raw reading-level CSV export for the period

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

The backend verifies Supabase access tokens using **ES256** asymmetric signatures, fetching the public key from the project's JWKS endpoint (`/auth/v1/.well-known/jwks.json`). The frontend uses `@supabase/ssr` + `@supabase/supabase-js` for sign-in/sign-out and the shared axios instance in [backend.ts](frontend/src/lib/api/backend.ts) attaches the access token automatically.

## TensorFlow Lite Inference

The brief lists **TensorFlow Lite** under the tools section because the project's keyword list explicitly includes *IoT*, *Smart Buildings*, and *Smart Homes*. TFLite is what makes ML deployable to those targets — a stripped-down runtime that runs trained TensorFlow models on Raspberry Pi, ESP32-class gateways, smartphones, and microcontrollers, with **no full TensorFlow install needed**.

> **Scope caveat (read this first).** This section is a *deployment-optimization exercise* applied to the **legacy univariate LSTM forecaster**. On this dataset that forecaster does not beat a mean predictor (the data is temporally random — see [the forecasting-vs-estimation note](#a-note-on-forecasting-vs-estimation-important)), so the value demonstrated here is the **size/latency win of the TFLite runtime**, not forecast accuracy. The genuinely-accurate model is the multivariate LSTM estimator served at `/predict?model=lstm`; converting *it* to TFLite is an identical, trivial follow-up.

### What was added

| File | Role |
|---|---|
| [ml/training/export_lstm_tflite.py](ml/training/export_lstm_tflite.py) | Converts the trained `.keras` LSTM into two `.tflite` artifacts (float32 + INT8 dynamic-range quantized), verifies numerical agreement |
| [ml/training/benchmark_lstm_tflite.py](ml/training/benchmark_lstm_tflite.py) | Benchmarks size, single-step latency, 24-step iterative forecast latency, and prediction error against the Keras baseline |
| `LSTMTFLiteWrapper` in [backend/ml/model_wrappers.py](backend/ml/model_wrappers.py) | Drop-in replacement for `LSTMModelWrapper`; same `forecast_future()` signature, internally uses `tf.lite.Interpreter` |
| `LSTM_USE_TFLITE` env var in [backend/core/config.py](backend/core/config.py) | When `true`, [load_lstm_model](backend/ml/model_loaders.py) returns the TFLite wrapper. Defaults to `false` — existing behavior is unchanged. |

### Regenerating the artifacts

```powershell
.\venv\Scripts\python.exe -m ml.training.export_lstm_tflite
.\venv\Scripts\python.exe -m ml.training.benchmark_lstm_tflite
```

The first command writes `ml/models/trained/lstm_energy_forecast.tflite` and `lstm_energy_forecast.q8.tflite`. The second prints the benchmark table below.

### Benchmark — measured on the dev machine

50 runs (5 warmup discarded), 1×24×1 input tensor:

| Variant | On-disk size | Single-step latency | 24-step forecast | Pred error vs Keras |
|---|---:|---:|---:|---:|
| Keras (`.keras`) | 378.0 KB | 57.3 ms | 1354.6 ms | — (baseline) |
| **TFLite float32** | **132.0 KB** (35% of Keras) | **1.17 ms** (49× faster) | **31.7 ms** (43× faster) | 0.0 (bit-exact) |
| **TFLite INT8** (quant) | **48.2 KB** (12.7% of Keras) | **1.38 ms** (41× faster) | — | 9.84e-04 (~0.18%) |

The huge per-call speedup is because Keras `model.predict()` carries significant Python and graph-execution overhead per invocation; `tf.lite.Interpreter.invoke()` runs the model directly. The same effect makes TFLite a great fit for IoT use, where each device runs many small inferences.

### How to switch the backend to TFLite

Add to your `.env`:

```env
LSTM_USE_TFLITE=true
```

[load_lstm_model](backend/ml/model_loaders.py) reads this flag at startup. When `true` and the `.tflite` artifact exists, it returns `LSTMTFLiteWrapper`; otherwise it falls back to the full-Keras wrapper. The prediction API and forecast UI don't change — same endpoints, same response shape.

### The IoT story

The 48 KB INT8 artifact + `tflite_runtime` (a ~2 MB Python wheel, no TensorFlow) can be dropped onto:
- A Raspberry Pi 4 next to the building's smart meter, running predictions locally
- A smart-meter gateway, where bandwidth back to the cloud is expensive
- A mobile app, for site-engineer dry-runs without internet

In each case the *same* trained model — produced by the same training pipeline — handles inference. That is why TFLite earns its place in the brief.

### Caveats

- The LSTM conversion needs `tf.lite.OpsSet.SELECT_TF_OPS` (the "Flex" delegate) because TFLite's pure builtin op set doesn't cover every Keras LSTM internal. This adds a small runtime dependency on TF op support. Pure-CMSIS-NN microcontroller deployment would require a slightly different model architecture (e.g., a smaller GRU or a CNN forecaster) — out of scope for this project but a clean follow-up.
- INT8 dynamic-range quantization adds <0.2% absolute error on this dataset, which is well within the noise floor of the underlying signal.

## Reports

The brief lists *"Dashboard with charts, reports, and alerts."* Charts live in the analytics pages, alerts in the alerts page — this section covers reports: a single, shareable PDF document plus a raw CSV export.

### What the PDF report contains

Generated server-side by [backend/services/report_service.py](backend/services/report_service.py) using [reportlab](https://www.reportlab.com/) for layout and matplotlib for the embedded charts. Everything is rendered to in-memory PNG bytes and inlined into the PDF — no temp files on disk.

| Section | Source |
|---|---|
| Executive summary (total kWh, est. cost, avg daily, peak) | `analytics_service.get_summary` |
| Period comparison vs previous window of equal length | `analytics_service.compare_periods` |
| Consumption trend chart (daily for ≥ 2-day windows, hourly otherwise) | `analytics_service.get_data_range` + matplotlib |
| Hourly profile (average consumption by hour-of-day) | direct SQL on `energy_readings` + matplotlib |
| Statistical outliers (`|z-score| > 2`, top 10 by magnitude) | direct SQL using `avg` + `stddev_samp` |
| Optimization recommendations table | `optimization_service.generate_report` |

The report is branded (teal accent), paginated with a footer (`Generated YYYY-MM-DD HH:MM UTC · Page N`), and named `enersight-report-<start>_to_<end>.pdf` via `Content-Disposition`. A local sample sits in `logs/sample_report.pdf` after running the smoke test.

### CSV export

`GET /api/v1/reports/period.csv?days=30` (or with explicit `start`/`end` and optional `aggregation=hour|day|week|month|year`) returns the raw reading-level data, suitable for spreadsheet analysis. Backed by the existing `analytics_service.export_to_csv`.

### Frontend

[frontend/src/app/(app)/reports/page.tsx](frontend/src/app/(app)/reports/page.tsx) is a server component listing what's included; the actual download is handled by the client component [download-buttons.tsx](frontend/src/app/(app)/reports/download-buttons.tsx), which:
1. Reads the Supabase access token from the browser client
2. Calls the backend with `Authorization: Bearer <token>`
3. Streams the response as a `Blob`, builds an object URL, and triggers a download with the filename from `Content-Disposition`

Period length is controlled by [period-selector.tsx](frontend/src/app/(app)/reports/period-selector.tsx) (7 / 14 / 30 / 90 / 180 / 365 days), persisted in the URL search params so deep links work.

### Why server-side PDF (and not browser print-to-PDF)?

- **Deterministic output** — the PDF looks the same on any client. Browser print depends on user-installed fonts, zoom, and headless-Chrome flags.
- **No JS runtime needed** — the report can run from a cron job, an email digest, or an API integration with no browser. Browser-print only works in front of a user.
- **Smaller deploy** — `reportlab` is a pure-Python wheel. Headless Chromium adds 200 MB+ to the container.

## Optimization Recommendations

Anomaly detection tells you *something is wrong*. Optimization recommendations tell you *what to do about it*. The `/api/v1/optimizations/` endpoint runs a small, explainable rules engine over recent `energy_readings` and returns a ranked list of concrete actions with projected monthly savings (kWh and USD).

### Architecture

- **Schemas**: [backend/schemas/optimization.py](backend/schemas/optimization.py) defines `Recommendation` and `OptimizationReport`.
- **Service**: [backend/services/optimization_service.py](backend/services/optimization_service.py) holds the rules engine. Each rule is a method on `OptimizationService` that takes a SQLAlchemy session, a `[start, end)` window, and the cost per kWh, and returns `Optional[Recommendation]`. Silence is meaningful — a rule returning `None` means "this pattern wasn't detected, no recommendation needed."
- **API route**: [backend/api/v1/optimizations.py](backend/api/v1/optimizations.py) exposes the report.
- **Frontend**: [frontend/src/app/(app)/optimizations/page.tsx](frontend/src/app/(app)/optimizations/page.tsx) renders each recommendation as a card with severity, category icon, projected monthly savings, supporting metrics, and a concrete suggested action.

### Rules currently implemented

| Rule id | What it detects | Suggested action |
|---|---|---|
| `hvac_when_empty` | HVAC active during readings with `occupancy = 0` | Tie HVAC schedule to occupancy / wider deadband when unoccupied |
| `lights_when_empty` | Lighting active during readings with `occupancy = 0` | Install PIR motion sensors and after-hours shutdown schedules |
| `underused_renewable` | Renewable output above-average while grid consumption stays above-average | Shift flexible loads (water heating, EV charging, batch jobs) into the renewable-production window |
| `weekend_phantom_load` | Weekend minimum consumption exceeds weekday minimum | Audit always-on equipment (servers, fume hoods, vending) and add scheduled shutdowns |

### Recommendation payload

Each recommendation includes:
- `title`, `category` (hvac / lighting / renewable / baseline / scheduling), `severity` (info / warning / critical)
- `description` — what was observed, with the supporting numbers inlined
- `suggestion` — concrete action the operator can take
- `estimated_savings_kwh` and `estimated_savings_usd` — projected to a **monthly** horizon so recommendations from different window sizes can be compared
- `confidence` (0-1) — saturating function of sample size, so a 5-sample finding gets a different weight than a 500-sample one
- `supporting_metrics` — the raw numbers used to derive the recommendation, exposed for transparency

The report is sorted by projected USD savings, so the most impactful action is always at the top.

### Why a rules engine (not an ML model)?

For "suggest optimizations" the rules engine wins on three axes:
1. **Explainability** — each recommendation comes with the exact numbers that triggered it. An ML model would produce a score with no actionable reason.
2. **Cold-start** — works on day one with no training data, which matters because optimization opportunities are most valuable to surface *early*.
3. **Operator trust** — energy engineers can read the rule, agree or disagree, and tune thresholds. ML black boxes are routinely ignored in industrial settings for exactly this reason.

The anomaly detector (Isolation Forest) is still where ML earns its keep — it finds *unknown* unknowns. The rules engine encodes *known* unknowns. The two are complementary.

## Time-Series Storage

The `energy_readings` table is a **declaratively partitioned Postgres table**, managed by [`pg_partman`](https://github.com/pgpartman/pg_partman) and maintained nightly by [`pg_cron`](https://github.com/citusdata/pg_cron). This is the Postgres-native time-series setup used when TimescaleDB is not available on the managed platform (Supabase does not ship TimescaleDB for licensing reasons).

### Design

- **Partition strategy**: `RANGE (recorded_at)`, **monthly** partitions
- **Composite primary key**: `(id, recorded_at)` — Postgres requires the partition key to be part of every unique constraint on a partitioned table
- **Default partition**: catch-all for any row that doesn't match an existing range (acts as a safety net)
- **Indexes propagate to children**: `recorded_at DESC`, `(device_id, recorded_at DESC)`, `(location, recorded_at DESC)` are declared once on the parent and Postgres creates matching local indexes on every partition
- **Row Level Security**: preserved on the parent table; policies apply uniformly across all partitions

### Automation

`pg_partman` is configured to:

| Setting | Value | Effect |
|---|---|---|
| `partition_interval` | `1 month` | one child partition per calendar month |
| `premake` | `6` | always keep 6 future partitions ready |
| `retention` | `12 months` | drop partitions older than 12 months |
| `retention_keep_table` | `false` | retention drops the underlying table outright (fast) |
| `infinite_time_partitions` | `true` | maintenance keeps creating future partitions indefinitely |
| `automatic_maintenance` | `on` | partition creation/drop happens via the maintenance proc |

A `pg_cron` job named `partman-maintenance` runs every night at **02:00 UTC** and calls `partman.run_maintenance_proc()`. This is what creates next month's partition before any data needs it, and drops year-old partitions when they age out.

### Why this matters

- **Partition pruning** — time-bounded queries (the dominant access pattern for the dashboard, analytics, and ML training pipelines) scan only the relevant month's partition instead of the full table. Verified with `EXPLAIN`: a `WHERE recorded_at >= '...' AND recorded_at < '...'` plan touches a single child partition.
- **Bounded index size** — every index is local to one partition, so write performance stays flat as the time-series grows. With a single-table design, indexes grow linearly with row count and INSERTs slow over time.
- **Instant retention drops** — `DROP TABLE` on an old partition is O(1). Deleting old rows from a non-partitioned table would scan and rewrite indexes; partitioned drops don't touch the surviving data at all.
- **Operationally hands-off** — partition creation and pruning are scheduled inside the database itself, with no application-level cron, no external scheduler, and no Docker container to babysit.

### Files involved

- Migration: `partition_energy_readings_by_month` (Supabase migrations)
- Cron job: `partman-maintenance` in `cron.job`
- Configuration row: `partman.part_config` where `parent_table = 'public.energy_readings'`

### Schema trade-off

The previous foreign key `anomalies.reading_id → energy_readings.id` was removed during the migration. Postgres requires FKs into partitioned tables to reference the **full** primary key, which is now composite `(id, recorded_at)`. The reference is now a soft pointer — `anomalies` was empty at migration time so no data was affected, and this is the standard pattern for anomaly/event tables that point at time-series readings. To restore strict integrity in the future, add `recorded_at` to `anomalies` and recreate the FK as composite.

## ML Models

- **Random Forest Regressor** — default consumption predictor (`ml/models/regression_model.py`). R² ≈ 0.54, RMSE ≈ 5.5 kWh.
- **Gradient Boosting Regressor** — benchmark predictor, similar accuracy.
- **Multivariate LSTM** — concurrent consumption *estimator* (`ml/models/lstm_multivariate.py`). R² ≈ 0.59, RMSE ≈ 5.0 kWh — the strongest single model. Selectable via `/predict?model=lstm`.
- **Isolation Forest** — anomaly detection (`ml/models/anomaly_detector.py`), used as a rules+IF hybrid.
- **Univariate LSTM** — legacy time-series forecaster (`ml/models/lstm_model.py`), kept for the `/forecast` endpoint and the TFLite edge-deployment demo. See the honest caveat under [TensorFlow Lite Inference](#tensorflow-lite-inference).

### A note on forecasting vs. estimation (important)

This dataset is **temporally random**: `EnergyConsumption` and every driver have ~zero hour-to-hour autocorrelation (verified — e.g. consumption lag-1 ≈ 0.00, Temperature lag-1 ≈ −0.02). Consumption is driven by *concurrent* conditions (Temperature correlates +0.70), not by its own history.

Consequence: **true forecasting is not learnable here** — the original univariate LSTM collapsed to predicting the mean (R² ≈ −0.05, i.e. worse than the mean), and its old MAPE-based "accuracy" was misleading on such a tight target (a mean-only predictor already scores ~91%). The LSTM is therefore framed as a **concurrent multivariate estimator** (`sequence_length=1`): given the conditions at a timestep, estimate that timestep's consumption. This reaches the data's real ceiling (R² ≈ 0.59) and matches what `/predict?model=lstm` actually returns.

Trained artifacts live in `ml/models/trained/`. Retrain the regression/forecaster/anomaly models + persist metrics via:

```powershell
.\venv\Scripts\python.exe -m ml.training.train_models          # RF / GB / univariate LSTM / anomaly
.\venv\Scripts\python.exe -m ml.training.train_lstm_multivariate   # multivariate LSTM estimator
.\venv\Scripts\python.exe -m ml.evaluation.regenerate_metrics      # rebuild metrics.json from saved models (no retrain)
```

The `regression_random_forest` variant also supports `include_lag_features=True`, which adds lag (1h, 24h, 168h) and 24h rolling-mean features over `EnergyConsumption`. Lagged variants use a time-based train/test split to avoid look-ahead leakage. They are trained side-by-side with the baseline as a benchmark; the `/predict` endpoint always uses the baseline so single-shot calls (which have no history context) don't degrade.

## Model Accuracy & Drift Monitoring

The platform answers three distinct questions about model quality, each with a different mechanism:

| Question | Mechanism | Where it shows |
|---|---|---|
| *How accurate is the model on the test set?* | Training-time metrics: RMSE, MAE, R², MAPE, Accuracy% | "Model accuracy" card on the dashboard, [/api/v1/ml/metrics](#ml-monitoring-auth-required) |
| *Is that accuracy stable, or did we get lucky on one split?* | 5-fold cross-validation with mean ± std per fold | "Cross-validation stability" card, [/api/v1/ml/evaluation](#ml-monitoring-auth-required) |
| *Where does the model fail?* | Sampled predicted-vs-actual series (chronological held-out tail) | "Predicted vs actual" chart |
| *Is the anomaly detector catching the right things?* | Precision / Recall / F1 vs pseudo-labels from the existing business rules | "Anomaly detector quality" card |
| *How is the live model performing in production right now?* | `ml_prediction_log` table + scheduled backfill + bucketed MAPE | "Live drift monitoring" card, [/api/v1/ml/drift](#ml-monitoring-auth-required) |

### Layer 1 — Training-time metrics

[ml/models/trained/metrics.json](ml/models/trained/metrics.json) holds per-model RMSE, MAE, R², MAPE, and Accuracy (= 100% − MAPE). Random Forest and Gradient Boosting are each trained twice — baseline (no lag features) and lagged — so the impact of lag features is visible side-by-side. The LSTM entry is the **multivariate estimator** (`lstm_multivariate`, task `estimation`, R² ≈ 0.59), scored on its hold-out split in kWh so it's comparable to the regressors.

> Generate it with `python -m ml.evaluation.regenerate_metrics`, which **re-scores the already-saved models without retraining** — so the numbers match the artifacts you ship. (`train_models` also writes metrics while training, but running it for a subset overwrites the file; the regenerate script rebuilds the complete set.)

> **Accuracy caveat:** the target is tight (mean 77, std 8 kWh), so "Accuracy = 100 − MAPE" reads high for everything — a mean-only predictor already scores ~91%. **R² is the honest discriminator** (~0.54 RF, ~0.59 multivariate LSTM); it's capped near ~0.55 by the data (Temperature alone explains most of the signal, the rest is noise).

### Layer 2 — Cross-validation & evaluation

`python -m ml.evaluation.evaluate` loads the saved artifacts (no retraining) and produces:

- **5-fold CV** for all regression variants. Reports mean ± std for RMSE/MAE/MAPE/R²/Accuracy. Shuffled folds for baseline, time-ordered folds for lagged (lag features leak under shuffle).
- **Predicted-vs-actual sample** (≤ 200 points) for each regression variant, taken from the chronological 20% tail. Used by the dashboard chart.
- **Anomaly precision/recall/F1** vs **rule-based pseudo-labels** derived from the same business heuristics in `AnomalyDetector._determine_anomaly_reason`. This measures *agreement with the rules*, not absolute accuracy — for that you need a human-labelled dataset. Surfaced honestly in the UI as a caveat.

Outputs land in [ml/models/trained/evaluation.json](ml/models/trained/evaluation.json) and [ml/models/trained/predictions.json](ml/models/trained/predictions.json).

### Layer 3 — Live drift monitoring

Every call to `/api/v1/predictions/predict` and `/api/v1/predictions/forecast` is logged to `public.ml_prediction_log` with:

| Column | Purpose |
|---|---|
| `target_at` | Wall-clock time the prediction is *about*. For `/predict` defaults to `now` (override via the new `for_timestamp` request field). For `/forecast` step `h`, it's `now + h hours`. |
| `model_name`, `model_version` | `model_version` is derived from the trained-model file's mtime (`backend/ml/model_version.py`). Lets you slice drift by retrained model. |
| `features` | JSONB snapshot of the input — kept for post-hoc debugging. |
| `predicted_value` | What the model returned. |
| `actual_value`, `error`, `abs_pct_error`, `backfilled_at` | Filled in by the backfill once a matching `energy_readings` row exists. |

Logging is **non-blocking** — `_safe_log_*` helpers in [backend/services/energy_service.py](backend/services/energy_service.py) swallow log-write failures so a DB hiccup never breaks the user-facing endpoint.

**Backfill** is a Postgres function `public.ml_backfill_predictions(p_limit INT)` that joins pending log rows against `energy_readings` within ±5 minutes of `target_at` and updates `actual_value`/`error`/`abs_pct_error`. Same logic in SQL is 10× faster than going through the HTTP endpoint and avoids round-trip overhead. The function is `SECURITY DEFINER`, `REVOKE`d from `anon`/`authenticated`, granted only to `service_role`.

**Schedule**: a `pg_cron` job `ml_backfill_predictions_every_15m` runs `SELECT public.ml_backfill_predictions(1000)` every 15 minutes — fully in-database, no application cron required. The HTTP endpoint `POST /api/v1/ml/backfill` is kept for manual triggering.

**Dashboard card**: shows total / backfilled / pending counters, the live accuracy %, and a MAPE-over-time line chart with a dashed reference line at the training-time MAPE — when the live line stays above the reference, the model has drifted and needs retraining.

### Migrations involved

- `add_model_version_to_prediction_log` — adds `model_version TEXT` + index to `ml_prediction_log`
- `create_ml_backfill_function_and_cron` — creates the SQL function and pg_cron job (idempotent)
- `enable_rls_on_data_tables` — see the [Security](#security) section below
- Python migration script: [backend/migrations/create_prediction_log_table.py](backend/migrations/create_prediction_log_table.py) creates the table initially

### Re-running the whole pipeline

```powershell
# Layer 1 — train + persist training metrics
.\venv\Scripts\python.exe -m ml.training.train_models

# Layer 2 — run CV + anomaly P/R + predicted-vs-actual sampling
.\venv\Scripts\python.exe -m ml.evaluation.evaluate
```

Layer 3 backfill is automatic. To force a backfill manually:

```bash
curl -X POST "https://<your-backend>/api/v1/ml/backfill?limit=1000" \
     -H "Authorization: Bearer <supabase-access-token>"
```

## Security

All `/api/v1/ml/*` endpoints are gated by `get_current_user` (Supabase Auth ES256 JWT). The dashboard's `backendFetch` helper forwards the access token automatically.

### Row Level Security on data tables

The migration [backend/migrations/enable_rls_on_data_tables.sql](backend/migrations/enable_rls_on_data_tables.sql) enables RLS on `ml_prediction_log` and every `energy_readings` partition with **no permissive policies** — i.e., a complete lockdown to anon and authenticated PostgREST clients. This is safe because:

1. The FastAPI backend connects as the `postgres` user (superuser), which **bypasses RLS**.
2. The frontend never queries these tables directly via `supabase-js` — all data flows through FastAPI.

Result: Supabase's `rls_disabled_in_public` advisory drops from 12× **ERROR** to 0. The replacement `rls_enabled_no_policy` notices are **INFO**-level and expected (no policies = no anon access, which is the goal). If you ever want `supabase-js` to query these tables directly (e.g., realtime subscriptions), uncomment the policy template at the bottom of the migration file.

## Deployment

The backend deploys to Render via [render.yaml](render.yaml) on the native Python runtime — no Docker. The frontend (Next.js) deploys to Vercel with `npm run build`.

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
