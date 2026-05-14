"""
Energy data repository backed by Supabase Postgres.

Replaces the previous InfluxDB implementation. The public method signatures
are preserved so callers (services, routes) keep working unchanged. Aggregation
windows are expressed as Postgres `interval`/`date_trunc` rather than Flux.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import DatabaseQueryError
from backend.core.logging import get_logger
from backend.models.energy import EnergyReading

logger = get_logger(__name__)


# Map InfluxDB-style window strings ("1h", "1d", "5m") to a Postgres date_trunc unit.
_WINDOW_TO_TRUNC = {
    "m": "minute",
    "h": "hour",
    "d": "day",
    "w": "week",
}


def _parse_window(window: str) -> str:
    """Return a date_trunc unit name (e.g. 'hour') from an Influx-style window."""
    if not window:
        return "hour"
    unit = window[-1].lower()
    return _WINDOW_TO_TRUNC.get(unit, "hour")


class EnergyDataRepository:
    """
    Repository for energy consumption time-series data on Postgres.

    Field semantics match the InfluxDB measurement "energy_consumption":
    - tags  -> indexed columns (device_id, location)
    - fields -> data columns (consumption, temperature, humidity, ...)
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------
    async def write_measurement(
        self,
        measurement: str,
        tags: dict,
        fields: dict,
        timestamp: datetime,
    ) -> None:
        """Insert a single energy reading."""
        try:
            row = EnergyReading(
                recorded_at=timestamp,
                device_id=tags.get("device_id", "device_0"),
                location=tags.get("location", "default"),
                consumption=float(fields.get("consumption", 0.0)),
                temperature=fields.get("temperature"),
                humidity=fields.get("humidity"),
                square_footage=fields.get("square_footage"),
                occupancy=fields.get("occupancy"),
                hvac_usage=bool(fields["hvac_usage"]) if "hvac_usage" in fields else None,
                lighting_usage=bool(fields["lighting_usage"]) if "lighting_usage" in fields else None,
                renewable_energy=fields.get("renewable_energy"),
                day_of_week=fields.get("day_of_week"),
                holiday=bool(fields["holiday"]) if "holiday" in fields else None,
            )
            self.session.add(row)
            await self.session.flush()
        except Exception as e:
            logger.error(f"Failed to write reading: {e}")
            raise DatabaseQueryError(f"Failed to write energy reading: {e}")

    async def write_batch(self, data_points: List[Dict[str, Any]]) -> None:
        """Bulk-insert energy readings. Each point: {tags, fields, timestamp}."""
        try:
            rows = []
            for p in data_points:
                tags = p.get("tags", {})
                fields = p.get("fields", {})
                rows.append(
                    EnergyReading(
                        recorded_at=p["timestamp"],
                        device_id=tags.get("device_id", "device_0"),
                        location=tags.get("location", "default"),
                        consumption=float(fields.get("consumption", 0.0)),
                        temperature=fields.get("temperature"),
                        humidity=fields.get("humidity"),
                        square_footage=fields.get("square_footage"),
                        occupancy=fields.get("occupancy"),
                        hvac_usage=bool(fields["hvac_usage"]) if "hvac_usage" in fields else None,
                        lighting_usage=bool(fields["lighting_usage"]) if "lighting_usage" in fields else None,
                        renewable_energy=fields.get("renewable_energy"),
                        day_of_week=fields.get("day_of_week"),
                        holiday=bool(fields["holiday"]) if "holiday" in fields else None,
                    )
                )
            self.session.add_all(rows)
            await self.session.flush()
            logger.info(f"Wrote {len(rows)} readings in batch")
        except Exception as e:
            logger.error(f"Failed to write batch: {e}")
            raise DatabaseQueryError(f"Failed to batch-write energy readings: {e}")

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------
    async def query_range(
        self,
        measurement: str,
        start: datetime,
        stop: datetime,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[dict]:
        """Return readings between `start` and `stop` matching optional tag filters."""
        try:
            query = select(EnergyReading).where(
                EnergyReading.recorded_at >= start,
                EnergyReading.recorded_at < stop,
            )
            if filters:
                for key, value in filters.items():
                    if hasattr(EnergyReading, key):
                        query = query.where(getattr(EnergyReading, key) == value)
            query = query.order_by(EnergyReading.recorded_at.asc())
            result = await self.session.execute(query)
            rows = result.scalars().all()
            return [
                {
                    "time": r.recorded_at,
                    "consumption": r.consumption,
                    "temperature": r.temperature,
                    "humidity": r.humidity,
                    "occupancy": r.occupancy,
                    "hvac_usage": r.hvac_usage,
                    "lighting_usage": r.lighting_usage,
                    "renewable_energy": r.renewable_energy,
                    "square_footage": r.square_footage,
                    "day_of_week": r.day_of_week,
                    "holiday": r.holiday,
                    "device_id": r.device_id,
                    "location": r.location,
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise DatabaseQueryError(f"Failed to query energy readings: {e}")

    async def aggregate(
        self,
        measurement: str,
        start: datetime,
        stop: datetime,
        aggregation: str = "mean",
        window: str = "1h",
    ) -> List[dict]:
        """
        Bucket readings by `window` and reduce with `aggregation`.
        Returns one row per bucket with averaged/summed consumption.
        """
        agg_map = {
            "mean": func.avg,
            "avg": func.avg,
            "sum": func.sum,
            "max": func.max,
            "min": func.min,
            "count": func.count,
        }
        agg_func = agg_map.get(aggregation, func.avg)
        trunc_unit = _parse_window(window)

        try:
            bucket = func.date_trunc(trunc_unit, EnergyReading.recorded_at).label("bucket")
            stmt = (
                select(bucket, agg_func(EnergyReading.consumption).label("value"))
                .where(EnergyReading.recorded_at >= start, EnergyReading.recorded_at < stop)
                .group_by(bucket)
                .order_by(bucket.asc())
            )
            result = await self.session.execute(stmt)
            rows = result.all()
            return [
                {
                    "time": row.bucket,
                    "value": float(row.value) if row.value is not None else None,
                    "aggregation": aggregation,
                    "window": window,
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Aggregation failed: {e}")
            raise DatabaseQueryError(f"Failed to aggregate energy readings: {e}")

    async def get_latest(self, measurement: str, limit: int = 10) -> List[dict]:
        """Return the latest `limit` readings, newest first."""
        try:
            stmt = (
                select(EnergyReading)
                .order_by(EnergyReading.recorded_at.desc())
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            return [r.to_dict() for r in result.scalars().all()]
        except Exception as e:
            logger.error(f"Failed to get latest readings: {e}")
            raise DatabaseQueryError(f"Failed to read latest energy readings: {e}")
