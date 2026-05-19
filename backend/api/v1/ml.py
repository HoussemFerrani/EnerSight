"""
ML Metrics Endpoint
Exposes static training metrics, evaluation results, predicted-vs-actual
samples, and live drift monitoring derived from the ml_prediction_log table.
"""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies.auth import get_current_user
from backend.core.dependencies import get_postgres_session
from backend.core.logging import get_logger
from backend.repositories.prediction_log_repository import PredictionLogRepository

logger = get_logger(__name__)
# Gate every endpoint in this router behind a valid Supabase session. The
# dashboard's backendFetch helper already forwards the access token.
router = APIRouter(dependencies=[Depends(get_current_user)])

# Resolve files relative to the project root (backend/api/v1 -> 3 levels up).
TRAINED_DIR = Path(__file__).resolve().parents[3] / "ml" / "models" / "trained"
METRICS_FILE = TRAINED_DIR / "metrics.json"
EVALUATION_FILE = TRAINED_DIR / "evaluation.json"
PREDICTIONS_FILE = TRAINED_DIR / "predictions.json"


def _read_json(path: Path, not_found_hint: str):
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=not_found_hint,
        )
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Corrupt JSON at {path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{path.name} is malformed — regenerate it.",
        )


@router.get(
    "/metrics",
    summary="Model evaluation metrics",
    description="Returns RMSE/MAE/R²/MAPE for the latest trained models, plus anomaly-detector stats.",
)
async def get_model_metrics():
    return _read_json(
        METRICS_FILE,
        "No metrics file found. Run `python -m ml.training.train_models` to generate one.",
    )


@router.get(
    "/evaluation",
    summary="Cross-validation + anomaly precision/recall",
    description="Deeper evaluation produced by `python -m ml.evaluation.evaluate`.",
)
async def get_evaluation():
    return _read_json(
        EVALUATION_FILE,
        "No evaluation file found. Run `python -m ml.evaluation.evaluate` to generate one.",
    )


@router.get(
    "/predictions",
    summary="Sampled predicted-vs-actual series for charts",
    description="Per-model arrays of (timestamp, actual, predicted) tuples for dashboard visualisation.",
)
async def get_predictions():
    return _read_json(
        PREDICTIONS_FILE,
        "No predictions file found. Run `python -m ml.evaluation.evaluate` to generate one.",
    )


# ==================== Live drift monitoring ====================

@router.get(
    "/drift/summary",
    summary="Live drift summary",
    description="Top-line numbers across all logged predictions: count, backfilled, live MAPE.",
)
async def get_drift_summary(session: AsyncSession = Depends(get_postgres_session)):
    repo = PredictionLogRepository(session)
    return await repo.summary()


@router.get(
    "/drift",
    summary="Live drift over time",
    description="Bucketed MAPE/error over the last N hours of backfilled predictions.",
)
async def get_drift(
    hours: int = Query(168, ge=1, le=24 * 30, description="Lookback window in hours"),
    bucket: str = Query("hour", pattern="^(hour|day)$"),
    session: AsyncSession = Depends(get_postgres_session),
):
    repo = PredictionLogRepository(session)
    series = await repo.recent_drift(hours=hours, bucket=bucket)
    return {"hours": hours, "bucket": bucket, "series": series}


@router.post(
    "/backfill",
    summary="Fill in actual values for past predictions",
    description=(
        "Looks at predictions whose target_at has passed and joins them against "
        "energy_readings within ±5 minutes. Run periodically (cron) to keep drift "
        "metrics current."
    ),
)
async def run_backfill(
    limit: int = Query(500, ge=1, le=10000),
    session: AsyncSession = Depends(get_postgres_session),
):
    repo = PredictionLogRepository(session)
    return await repo.backfill_missing(limit=limit)


@router.get(
    "/log",
    summary="Recent prediction log entries (debugging)",
)
async def get_log(
    limit: int = Query(50, ge=1, le=500),
    session: AsyncSession = Depends(get_postgres_session),
):
    repo = PredictionLogRepository(session)
    rows = await repo.recent_log(limit=limit)
    return {"count": len(rows), "rows": rows}
