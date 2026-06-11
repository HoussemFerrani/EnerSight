# EnerSight — Code Presentation Guide

A map of the project for presenting to a jury. You don't need to explain code
line by line — you need to know **what lives where**, **how data flows**, and
**why it's organized this way**. This document gives you exactly that.

---

## 1. The 30-second pitch

> "EnerSight is an AI-powered energy monitoring platform. Sensor readings flow
> into a Postgres time-series database; a FastAPI backend serves them, runs
> machine-learning models on them, and sends email alerts; a Next.js dashboard
> visualizes everything in real time. The architecture is a clean three-tier
> separation: **frontend** (presentation), **backend** (API + business logic),
> and **ml** (model training lab)."

---

## 2. The folder map (what to say about each folder)

Open the project tree and walk it top-down. One sentence per folder is enough.

### `backend/` — the FastAPI server (the heart)

Built with **clean architecture**: each layer has one job, and layers only
talk to the layer below them.

| Folder | One-liner for the jury |
|---|---|
| `api/` | "The HTTP layer — REST routes and a WebSocket. It only parses requests and calls services; no business logic here." |
| `schemas/` | "Pydantic models that validate every request and response — the API contract." |
| `services/` | "The business logic. Alert monitoring, email notifications, analytics computations, the MQTT ingestor, and the data simulator all live here as services." |
| `repositories/` | "The data-access layer — services never write SQL directly, they go through repositories." |
| `models/` | "SQLAlchemy ORM models — one class per database table (readings, alerts, profiles, preferences)." |
| `database/` | "Connection management for Supabase Postgres." |
| `core/` | "Cross-cutting concerns: configuration from `.env`, the dependency-injection container, structured logging, global error handlers." |
| `ml/` | "The **serving** side of ML — loads the trained model artifacts and wraps them with a uniform `predict()` interface." |
| `migrations/` | "SQL migrations that define the database schema." |
| `main.py` | "The entry point — builds the FastAPI app, registers routes, and starts the background services on startup." |

**Key sentence:** *"A request enters through `api/`, is validated by
`schemas/`, processed by `services/`, which reads data through
`repositories/` mapped by `models/`. Each layer is independently testable."*

### `frontend/` — the Next.js dashboard

| Folder | One-liner |
|---|---|
| `src/app/` | "File-based routing — every folder is a page: dashboard, analytics, alerts, anomalies, predictions, realtime, reports." |
| `src/components/` | "Reusable UI components (shadcn/ui + Tailwind)." |
| `src/lib/` | "The Supabase auth client and `backendFetch` — a helper that attaches the user's JWT to every API call." |

**Key sentence:** *"Pages are React Server Components that fetch from the
backend on the server with the user's token; interactive pieces (charts,
forms, buttons) are small client components."*

### `ml/` — the training lab (separate from serving!)

This separation is a strong point — emphasize it.

| Folder | One-liner |
|---|---|
| `preprocessing/` | "Data cleaning and feature engineering." |
| `models/` | "The model classes: Random Forest regression, LSTM, Isolation Forest anomaly detector." |
| `training/` | "Training pipelines — run these to retrain and save artifacts." |
| `evaluation/` | "K-fold cross-validation and metrics generation — produces `metrics.json`." |
| `models/trained/` | "The saved artifacts (`.joblib`, `.keras`) that the backend loads at runtime." |

**Key sentence:** *"`ml/` is where models are **trained**; `backend/ml/` is
where they are **served**. Training happens offline, the backend only ever
loads the saved artifacts — so a heavy retraining job can never slow down the
API."*

### The rest

- `data/` — "The source dataset (1,000 hourly readings: consumption, temperature, humidity, occupancy, HVAC, lighting, renewables)."
- `scripts/` — "The IoT sensor simulator that publishes readings over MQTT."
- `tests/` — "Pytest suite: unit tests for services, integration tests for the API."
- `docs/` — "Setup, deployment, and architecture-decision records (`legacy/` keeps historical docs)."
- `.env*` — "12-factor configuration: all secrets and tuning knobs live in environment variables, never in code."

---

## 3. The three data-flow stories (memorize these)

When the jury asks "how does it work?", pick the relevant story.

### Story 1 — A sensor reading arrives

```
sensor (simulator) → MQTT broker → backend mqtt_ingestor → energy_readings table
                                        (or: built-in reading simulator writes directly)
```

1. `scripts/mqtt_simulator.py` publishes a JSON reading to an MQTT topic.
2. `backend/services/mqtt_ingestor.py` is subscribed; it validates the payload
   and inserts a row into Postgres.
3. (When no broker is available, `backend/services/reading_simulator.py`
   replays the dataset directly into the database — same result.)

### Story 2 — An alert email is born

```
alert_monitor (every 60s) → checks rolling window → creates Alert row → email_service → Gmail SMTP → inbox
```

1. `backend/services/alert_monitor.py` wakes every 60 seconds.
2. **Threshold path:** sums the last 10 minutes of consumption and compares
   with the user's threshold from `user_preferences`.
3. **Anomaly path:** runs the Isolation Forest over the same window.
4. Alerts are **edge-triggered**: an email fires when a problem *starts*, stays
   silent while it persists, and re-arms when it clears — so every email means
   a new event, never spam.
5. `email_service.py` sends a styled HTML email via SMTP; the alert row is
   marked `sent` and appears on the dashboard.

### Story 3 — A prediction

```
form on /predictions → POST /api/v1/predictions/predict → energy_service → Random Forest wrapper → result
```

1. The user enters conditions (temperature, occupancy, HVAC…).
2. The route validates input via a Pydantic schema and calls the service.
3. The service feeds the features to the **Random Forest** model
   (scikit-learn, ~94% accuracy on the held-out test set) loaded once at
   startup by the model registry in `backend/core/dependencies.py`.
4. Every prediction is also logged to `ml_prediction_log` for **drift
   monitoring** — later, when the real reading arrives, the error is
   backfilled and charted on the dashboard.

---

## 4. Suggested presentation flow (10–15 min)

1. **Pitch** (30s) — the paragraph from section 1.
2. **Live demo first** (3–4 min) — dashboard with live data, analytics charts,
   click "Send test email" on the alerts page, show the email arriving, run a
   prediction. *Demos before code: the jury now knows what the code is for.*
3. **Architecture slide / folder tree** (3 min) — walk the three top-level
   folders with the key sentences from section 2. Stress: three-tier
   separation, clean architecture layers, training/serving split.
4. **One deep-dive** (3 min) — pick ONE story from section 3 (the alert email
   is the most impressive: timer → SQL window → ML → SMTP → inbox) and follow
   it through the actual files on screen.
5. **Engineering quality** (2 min) — show `/api/docs` (auto-generated OpenAPI),
   `tests/`, `metrics.json` (honest model evaluation), and the `.env.example`
   (12-factor config).

---

## 5. Questions the jury may ask (and short answers)

- **"Why FastAPI?"** — Async-native (the background services and WebSocket run
  in the same event loop), automatic OpenAPI docs, and Pydantic validation
  built in.
- **"Why two ML folders?"** — Training (`ml/`) and serving (`backend/ml/`) are
  different concerns: training is offline and heavy, serving must be fast and
  stable. The boundary is the saved artifact files.
- **"Why Random Forest for prediction?"** — Comparable accuracy to the LSTM on
  this dataset (~94%), but simpler, faster at inference, and explainable.
- **"Why is anomaly detection an Isolation Forest?"** — Unsupervised: it needs
  no labeled anomalies, it learns what 'normal' looks like and flags outliers.
- **"How do you avoid alert spam?"** — Edge-triggered alerting: notify on
  state *change* (normal → breach), not on state. Plus a small anti-flapping
  cooldown.
- **"Where does authentication happen?"** — Supabase Auth issues JWTs; the
  Next.js server attaches them to API calls; FastAPI verifies them via
  Supabase's JWKS on every protected route. Row Level Security protects the
  tables themselves.
- **"Is it tested?"** — Unit tests on services and models, integration tests
  on the API (`tests/`), plus live verification of the alert pipeline.
- **"How would it scale?"** — The time-series table is partitioned monthly with
  pg_partman; the backend is stateless (deployable on Render); heavy ML stays
  offline.

---

## 6. Extended talk track (detailed narration)

When you want to talk longer about any part, use these expanded narrations.
Numbers in here are real — they come from the actual project.

### 6.1 What happens when the backend starts

"When I run the server, `main.py` does five things in order. First it loads
configuration from `.env` — database URL, SMTP credentials, alert tuning,
simulator settings — following the 12-factor principle that config lives in
the environment, not in code. Second it configures structured logging. Third
it initializes the database connections — we keep two: a synchronous pool for
background services and an async pool for request handling. Fourth it
registers the ML models in a registry with lazy loading — a model is only
loaded into memory the first time something needs it. Finally it launches
three background tasks that live alongside the API: the alert monitor, the
data simulator, and the MQTT ingestor. All of this is in one `lifespan`
function, so startup and shutdown are symmetric — every task started is
cleanly stopped."

### 6.2 The request lifecycle (clean architecture in action)

"Take `GET /api/v1/alerts` as an example. The request first passes through
middleware — CORS, security headers, gzip. Then FastAPI's dependency
injection kicks in: `get_current_user` extracts the Bearer token, verifies
the JWT signature against Supabase's public keys, and loads the user's
profile — if that fails, the request dies here with a 401 and the route never
runs. The route handler in `api/v1/alerts.py` is then just a few lines: query
alerts for this user, validate each row through a Pydantic response schema,
return. The route knows nothing about SQL; the ORM model knows nothing about
HTTP. That separation means I can unit-test business logic without a running
server, and change the database without touching the API layer."

### 6.3 The database design

"Everything lives in Supabase Postgres. The main tables: `energy_readings` —
the time series, one row per sensor reading with consumption, temperature,
humidity, occupancy, HVAC and lighting state, and renewable generation.
`profiles` and `user_preferences` — application data keyed to Supabase Auth
users; preferences hold the alert threshold and notification opt-in.
`alerts` — every alert with type, severity, status lifecycle
(pending → sent → acknowledged → resolved), and email tracking.
`ml_prediction_log` — every prediction the API makes, stored for drift
monitoring. The readings table is partitioned **monthly with pg_partman**:
Postgres automatically creates next month's partition and can drop old ones —
so queries on recent data stay fast no matter how much history accumulates.
Authentication tables are owned by Supabase Auth; we never store passwords."

### 6.4 The alert pipeline (the best deep-dive)

"The alert monitor is a background service that wakes every 60 seconds — all
intervals are environment-tunable. Each cycle does two checks. The threshold
check sums consumption over a rolling 10-minute window and compares it to the
user's threshold from their preferences. The anomaly check runs the Isolation
Forest over the same window's readings. The clever part is that alerting is
**edge-triggered**, like an interrupt: we keep in-memory state of whether the
condition was already active. An email fires only on the transition from
normal to abnormal; while the problem persists we stay silent; when it clears,
the trigger re-arms. So every email means *a new event*. A small anti-flapping
cooldown prevents bursts when consumption oscillates exactly at the threshold.
When an alert fires we insert the row, fetch the user's email from Supabase
Auth, and send a styled HTML email over SMTP — then mark the alert as sent.
The dashboard also has a test-email button calling a dedicated endpoint, so
the notification pipeline can be demonstrated on demand."

### 6.5 The ML story (training side)

"The dataset is 1,000 hourly readings with ten features. The `ml/` folder is
a complete lab: preprocessing handles cleaning, scaling, and encoding
(HVAC/lighting become binary features, timestamps become hour-of-day and
day-of-week). We trained several candidates: Random Forest and Gradient
Boosting regressors in baseline and lagged variants, and a multivariate LSTM.
Evaluation used a held-out test set plus k-fold cross-validation, and all
metrics are regenerated into `metrics.json` — Random Forest reaches about 94%
accuracy (MAPE ~5.8%). One honest finding worth mentioning: this dataset has
almost zero autocorrelation, so true *forecasting* is impossible — the models
are *estimators*: they answer 'given these conditions, what consumption do we
expect?' Recognizing that limitation is itself a result. The anomaly detector
is an Isolation Forest — unsupervised, so it needs no labeled anomalies —
combined with business rules into a hybrid that reaches F1 ≈ 0.79 with 100%
recall on pseudo-labeled data."

### 6.6 The ML story (serving side + drift)

"Trained models are saved as artifacts — `.joblib` for scikit-learn, `.keras`
for the neural network. The backend never trains anything: `backend/ml/`
contains loaders and thin wrappers giving every model the same `predict()`
interface, loaded lazily through the registry. Every live prediction is also
logged with its input features and a target timestamp. Later, when the real
reading for that timestamp arrives, a backfill job fills in the actual value
and computes the error — that gives us **live drift monitoring**: the
dashboard charts how model accuracy evolves on real data, not just on the
test set. If the live error started growing, that's the signal to retrain."

### 6.7 The frontend rendering model

"The frontend is Next.js with the App Router. Pages are React Server
Components: when you open /analytics, the server reads the Supabase session
cookie, calls the backend API with the user's token, and renders HTML with
the data already in it — the browser never holds API secrets and there's no
loading-spinner waterfall. Only the interactive islands are client
components: the charts (Recharts), forms, and action buttons. Mutations go
through server actions — small server-side functions the buttons call, which
then revalidate the page. The UI kit is shadcn/ui on Tailwind, and the
analytics page composes eight charts from one `/analytics/breakdown` endpoint
that computes all aggregations in SQL — hourly and weekday profiles,
temperature correlation, equipment impact, occupancy, renewables, and a
consumption histogram."

### 6.8 The IoT ingestion story

"Real deployments would have hardware sensors; here a simulator plays that
role, and the pipeline is the same one real sensors would use. The simulator
publishes JSON readings over **MQTT** — the standard IoT pub/sub protocol.
The backend runs an MQTT ingestor subscribed to the sensor topic: every
message is validated defensively (a malformed payload is logged and dropped,
never crashes the service) and persisted. The ingestor is broker-tolerant —
if no broker is running it retries quietly every minute. For development
there's also a built-in replay simulator that writes one dataset row per
minute directly to the database, timestamped now — that's what keeps the
dashboard alive and gives the alert monitor fresh data."

### 6.9 Security

"Three layers. Authentication: Supabase Auth issues short-lived JWTs; the
backend verifies signatures against Supabase's public JWKS keys on every
protected route — we never see or store passwords. Authorization: queries are
scoped to the authenticated user's id, and Postgres Row Level Security
enforces ownership at the database level — even a bug in the API couldn't
leak another user's rows. Transport/config: CORS allowlist, security headers
middleware, secrets only in `.env` which is gitignored, with `.env.example`
as the documented template."

---

## 7. One-line answers for "what is X?" (cheat sheet)

| Term | Answer |
|---|---|
| FastAPI | Python web framework serving our REST API |
| Pydantic | Validates every request/response shape |
| SQLAlchemy | Maps Python classes to Postgres tables |
| Supabase | Hosted Postgres + authentication service |
| MQTT | Lightweight pub/sub protocol used by IoT sensors |
| Isolation Forest | Unsupervised anomaly-detection algorithm (scikit-learn) |
| Random Forest | Ensemble regression model used for predictions (scikit-learn) |
| LSTM | Recurrent neural network (TensorFlow) — trained as an alternative estimator |
| Next.js App Router | File-based routing; pages render on the server |
| Recharts | React charting library behind all the graphs |
| pg_partman | Postgres extension that auto-partitions the readings table by month |
