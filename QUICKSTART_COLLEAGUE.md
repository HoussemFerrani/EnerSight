# EnerSight — Quick Start (Windows)

A Python (FastAPI) backend + Next.js frontend. The database is hosted on **Supabase
in the cloud**, so there is **nothing to install for the database** — the app just
connects, and you'll see live demo data. The credentials are already filled in for you.

## 1. Install prerequisites (once)

- **Python 3.11** — https://www.python.org/downloads/
  - Important: **3.11**, not 3.12 or newer (a machine-learning dependency has no newer build).
  - During install, tick **"Add python.exe to PATH"**.
- **Node.js 20 or newer** — https://nodejs.org (the LTS download is fine).

Verify in a **new** PowerShell window:

```powershell
py -3.11 --version   # should print Python 3.11.x   (or: python --version)
node --version       # should print v20 or higher
```

## 2. Set up (once, ~5–10 minutes)

Open PowerShell **in this folder** and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

This creates the Python virtual environment and installs all backend + frontend
dependencies. (TensorFlow is large, so the first run takes a few minutes.)

## 3. Run

```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

Two terminal windows open:

- **Backend** → http://localhost:8000 (API docs at http://localhost:8000/api/docs)
- **Frontend** → http://localhost:3000

Close those two windows to stop the app.

## Troubleshooting

- **`running scripts is disabled on this system`** — use the full command above
  (`powershell -ExecutionPolicy Bypass -File .\setup.ps1`); it bypasses the policy
  for just that run.
- **`python` is version 3.12+** — install Python 3.11 alongside it; `setup.ps1`
  automatically prefers `py -3.11`.
- **Frontend won't start** — confirm `node --version` is v20+.
- **Backend port 8000 already in use** — close any other app using it, or stop a
  previous backend window.
