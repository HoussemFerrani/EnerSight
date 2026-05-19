"""
Async repository for the ml_prediction_log table.

Provides:
- record(): log one prediction
- backfill_missing(): find rows without actual_value, look up the matching
  energy_readings row within a ± tolerance window, fill in actual/error
- recent_drift(): rolling MAPE over the last N hours of backfilled rows
- recent_log(): paginated view of the latest predictions (for debugging)
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.logging import get_logger
from backend.models.energy import EnergyReading
from backend.models.prediction_log import PredictionLog

logger = get_logger(__name__)

# How close in time an energy_readings row must be to count as the "actual"
# for a given prediction. 5 minutes is generous — hourly data lands cleanly,
# 5-minute data lands within one bucket.
MATCH_TOLERANCE = timedelta(minutes=5)


class PredictionLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record(
        self,
        *,
        prediction_type: str,
        model_name: str,
        predicted_value: float,
        target_at: datetime,
        features: Optional[Dict[str, Any]] = None,
        model_version: Optional[str] = None,
    ) -> int:
        """Persist one prediction. Returns the new row id."""
        row = PredictionLog(
            target_at=target_at,
            prediction_type=prediction_type,
            model_name=model_name,
            model_version=model_version,
            features=features,
            predicted_value=float(predicted_value),
        )
        self.session.add(row)
        await self.session.flush()
        return int(row.id)

    async def record_many(self, rows: List[Dict[str, Any]]) -> int:
        """Batch insert — used by /forecast which produces N rows per call."""
        objs = [
            PredictionLog(
                target_at=r["target_at"],
                prediction_type=r["prediction_type"],
                model_name=r["model_name"],
                model_version=r.get("model_version"),
                features=r.get("features"),
                predicted_value=float(r["predicted_value"]),
            )
            for r in rows
        ]
        self.session.add_all(objs)
        await self.session.flush()
        return len(objs)

    async def backfill_missing(self, limit: int = 500) -> Dict[str, int]:
        """
        For up to `limit` rows that have no actual_value yet, find the nearest
        energy_readings entry within ±MATCH_TOLERANCE of target_at and fill in
        actual/error/abs_pct_error.

        Returns a small summary dict the API can hand back.
        """
        # Pull candidate predictions that don't have an actual yet and whose
        # target_at is in the past (otherwise the truth can't possibly exist).
        now = datetime.now(timezone.utc)
        stmt = (
            select(PredictionLog)
            .where(PredictionLog.actual_value.is_(None))
            .where(PredictionLog.target_at <= now)
            .order_by(PredictionLog.target_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        candidates = result.scalars().all()

        filled = 0
        skipped = 0
        for pred in candidates:
            low = pred.target_at - MATCH_TOLERANCE
            high = pred.target_at + MATCH_TOLERANCE
            reading_stmt = (
                select(EnergyReading.consumption, EnergyReading.recorded_at)
                .where(and_(EnergyReading.recorded_at >= low, EnergyReading.recorded_at <= high))
                .order_by(
                    func.abs(
                        func.extract("epoch", EnergyReading.recorded_at - pred.target_at)
                    ).asc()
                )
                .limit(1)
            )
            reading = (await self.session.execute(reading_stmt)).first()
            if not reading:
                skipped += 1
                continue

            actual = float(reading.consumption)
            error = actual - float(pred.predicted_value)
            apct = (abs(error) / abs(actual) * 100.0) if abs(actual) > 1e-6 else None

            await self.session.execute(
                update(PredictionLog)
                .where(PredictionLog.id == pred.id)
                .values(
                    actual_value=actual,
                    error=error,
                    abs_pct_error=apct,
                    backfilled_at=datetime.now(timezone.utc),
                )
            )
            filled += 1

        return {
            "scanned": len(candidates),
            "filled": filled,
            "skipped_no_match": skipped,
        }

    async def recent_drift(self, hours: int = 168, bucket: str = "hour") -> List[Dict[str, Any]]:
        """
        Bucketed MAPE over backfilled predictions. Returns a list of
        {bucket_at, n, mape, mean_error} ordered chronologically. Empty buckets
        are omitted — let the client decide how to fill gaps.
        """
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        bucket_col = func.date_trunc(bucket, PredictionLog.target_at).label("bucket_at")
        stmt = (
            select(
                bucket_col,
                func.count(PredictionLog.id).label("n"),
                func.avg(PredictionLog.abs_pct_error).label("mape"),
                func.avg(PredictionLog.error).label("mean_error"),
            )
            .where(PredictionLog.actual_value.isnot(None))
            .where(PredictionLog.target_at >= since)
            .group_by(bucket_col)
            .order_by(bucket_col.asc())
        )
        result = await self.session.execute(stmt)
        return [
            {
                "bucket_at": row.bucket_at.isoformat() if row.bucket_at else None,
                "n": int(row.n),
                "mape": float(row.mape) if row.mape is not None else None,
                "mean_error": float(row.mean_error) if row.mean_error is not None else None,
            }
            for row in result.all()
        ]

    async def recent_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        stmt = (
            select(PredictionLog)
            .order_by(PredictionLog.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [r.to_dict() for r in result.scalars().all()]

    async def summary(self) -> Dict[str, Any]:
        """Top-level numbers for the dashboard card."""
        total_stmt = select(func.count(PredictionLog.id))
        backfilled_stmt = select(func.count(PredictionLog.id)).where(
            PredictionLog.actual_value.isnot(None)
        )
        mape_stmt = select(func.avg(PredictionLog.abs_pct_error)).where(
            PredictionLog.actual_value.isnot(None)
        )

        total = int((await self.session.execute(total_stmt)).scalar() or 0)
        backfilled = int((await self.session.execute(backfilled_stmt)).scalar() or 0)
        mape = (await self.session.execute(mape_stmt)).scalar()

        return {
            "total_predictions": total,
            "backfilled": backfilled,
            "pending_backfill": total - backfilled,
            "live_mape": float(mape) if mape is not None else None,
            "live_accuracy_pct": (max(0.0, 100.0 - float(mape)) if mape is not None else None),
        }
