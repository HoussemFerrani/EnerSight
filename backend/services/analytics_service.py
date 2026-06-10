"""
Analytics service backed by Supabase Postgres.

Replaces the previous InfluxDB/Flux implementation. Reads from
`public.energy_readings` via SQLAlchemy and computes aggregates with
`date_trunc` / `avg` / `sum`.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy import func

from backend.database.postgres import SessionLocal
from backend.models.energy import EnergyReading
from backend.schemas.analytics import (
    AggregatedData,
    AggregationPeriod,
    AnalyticsSummary,
    ComparisonResult,
    CostCalculation,
)


_PERIOD_TO_TRUNC = {
    "hour": "hour",
    "day": "day",
    "week": "week",
    "month": "month",
    "year": "year",
}


class AnalyticsService:
    """Reads aggregates from `energy_readings` in Postgres."""

    def get_data_range(
        self,
        start_date: datetime,
        end_date: datetime,
        aggregation: Optional[str] = None,
    ) -> List[dict]:
        """Return individual or bucketed energy points between two dates."""
        with SessionLocal() as session:
            if aggregation:
                trunc = _PERIOD_TO_TRUNC.get(aggregation, "hour")
                bucket = func.date_trunc(trunc, EnergyReading.recorded_at).label("bucket")
                rows = (
                    session.query(bucket, func.sum(EnergyReading.consumption).label("value"))
                    .filter(EnergyReading.recorded_at >= start_date, EnergyReading.recorded_at < end_date)
                    .group_by(bucket)
                    .order_by(bucket.asc())
                    .all()
                )
                return [
                    {"timestamp": r.bucket.isoformat(), "value": float(r.value or 0.0), "unit": "kWh"}
                    for r in rows
                ]

            rows = (
                session.query(EnergyReading.recorded_at, EnergyReading.consumption)
                .filter(EnergyReading.recorded_at >= start_date, EnergyReading.recorded_at < end_date)
                .order_by(EnergyReading.recorded_at.asc())
                .all()
            )
            return [
                {"timestamp": r.recorded_at.isoformat(), "value": float(r.consumption or 0.0), "unit": "kWh"}
                for r in rows
            ]

    def get_aggregated_data(
        self,
        start_date: datetime,
        end_date: datetime,
        period: AggregationPeriod,
    ) -> List[AggregatedData]:
        """Average consumption per bucket with per-bucket min/max/total/count."""
        trunc = _PERIOD_TO_TRUNC.get(period.value, "hour")
        with SessionLocal() as session:
            bucket = func.date_trunc(trunc, EnergyReading.recorded_at).label("bucket")
            rows = (
                session.query(
                    bucket,
                    func.sum(EnergyReading.consumption).label("total"),
                    func.avg(EnergyReading.consumption).label("avg"),
                    func.min(EnergyReading.consumption).label("min"),
                    func.max(EnergyReading.consumption).label("max"),
                    func.count(EnergyReading.id).label("count"),
                )
                .filter(EnergyReading.recorded_at >= start_date, EnergyReading.recorded_at < end_date)
                .group_by(bucket)
                .order_by(bucket.asc())
                .all()
            )

        results = []
        for r in rows:
            period_start, period_end = self._get_period_boundaries(r.bucket, period)
            results.append(
                AggregatedData(
                    period_start=period_start,
                    period_end=period_end,
                    total=float(r.total or 0.0),
                    average=float(r.avg or 0.0),
                    min=float(r.min or 0.0),
                    max=float(r.max or 0.0),
                    count=int(r.count or 0),
                )
            )
        return results

    def calculate_cost(
        self,
        start_date: datetime,
        end_date: datetime,
        cost_per_kwh: float = 0.12,
    ) -> CostCalculation:
        with SessionLocal() as session:
            total_kwh = (
                session.query(func.coalesce(func.sum(EnergyReading.consumption), 0.0))
                .filter(EnergyReading.recorded_at >= start_date, EnergyReading.recorded_at < end_date)
                .scalar()
            ) or 0.0
        total_kwh = float(total_kwh)
        return CostCalculation(
            period_start=start_date,
            period_end=end_date,
            total_kwh=total_kwh,
            cost_per_kwh=cost_per_kwh,
            total_cost=total_kwh * cost_per_kwh,
            currency="USD",
        )

    def get_summary(
        self,
        start_date: datetime,
        end_date: datetime,
        cost_per_kwh: Optional[float] = None,
    ) -> AnalyticsSummary:
        data = self.get_data_range(start_date, end_date)
        if not data:
            return AnalyticsSummary(
                total_consumption=0.0,
                average_daily=0.0,
                peak_consumption=0.0,
                peak_timestamp=start_date,
                lowest_consumption=0.0,
                lowest_timestamp=start_date,
                period_start=start_date,
                period_end=end_date,
                data_points=0,
            )

        values = [d["value"] for d in data]
        total = sum(values)
        days = (end_date - start_date).days or 1
        peak_idx = values.index(max(values))
        lowest_idx = values.index(min(values))
        peak_ts = datetime.fromisoformat(data[peak_idx]["timestamp"])
        lowest_ts = datetime.fromisoformat(data[lowest_idx]["timestamp"])
        return AnalyticsSummary(
            total_consumption=total,
            average_daily=total / days,
            peak_consumption=max(values),
            peak_timestamp=peak_ts,
            lowest_consumption=min(values),
            lowest_timestamp=lowest_ts,
            total_cost=(total * cost_per_kwh) if cost_per_kwh else None,
            period_start=start_date,
            period_end=end_date,
            data_points=len(data),
        )

    def compare_periods(
        self,
        current_start: datetime,
        current_end: datetime,
        comparison_type: str = "previous_period",
    ) -> ComparisonResult:
        period_duration = current_end - current_start
        if comparison_type == "previous_period":
            comp_start, comp_end = current_start - period_duration, current_start
        elif comparison_type == "same_period_last_month":
            comp_start, comp_end = current_start - timedelta(days=30), current_end - timedelta(days=30)
        elif comparison_type == "same_period_last_year":
            comp_start, comp_end = current_start - timedelta(days=365), current_end - timedelta(days=365)
        else:
            raise ValueError(f"Invalid comparison type: {comparison_type}")

        current_data = self.get_data_range(current_start, current_end)
        comparison_data = self.get_data_range(comp_start, comp_end)

        cur_total = sum(d["value"] for d in current_data)
        cur_avg = cur_total / len(current_data) if current_data else 0
        cmp_total = sum(d["value"] for d in comparison_data)
        cmp_avg = cmp_total / len(comparison_data) if comparison_data else 0
        diff = cur_total - cmp_total
        pct = (diff / cmp_total * 100) if cmp_total > 0 else 0

        return ComparisonResult(
            current_period=AggregatedData(
                period_start=current_start,
                period_end=current_end,
                total=cur_total,
                average=cur_avg,
                min=min((d["value"] for d in current_data), default=0),
                max=max((d["value"] for d in current_data), default=0),
                count=len(current_data),
            ),
            comparison_period=AggregatedData(
                period_start=comp_start,
                period_end=comp_end,
                total=cmp_total,
                average=cmp_avg,
                min=min((d["value"] for d in comparison_data), default=0),
                max=max((d["value"] for d in comparison_data), default=0),
                count=len(comparison_data),
            ),
            difference=diff,
            percentage_change=pct,
            comparison_type=comparison_type,
        )

    def get_breakdowns(self, start_date: datetime, end_date: datetime) -> dict:
        """
        Multi-dimensional breakdowns for the analytics dashboard, computed in
        one pass over the period: time-of-day/weekday profiles, weather and
        occupancy correlations, equipment impact, renewables, and the
        consumption distribution.
        """
        in_range = lambda q: q.filter(  # noqa: E731
            EnergyReading.recorded_at >= start_date,
            EnergyReading.recorded_at < end_date,
        )

        with SessionLocal() as session:
            # Average consumption by hour of day (0-23)
            hour = func.extract("hour", EnergyReading.recorded_at).label("hour")
            hourly = in_range(
                session.query(
                    hour,
                    func.avg(EnergyReading.consumption).label("avg"),
                    func.max(EnergyReading.consumption).label("max"),
                    func.count(EnergyReading.id).label("count"),
                )
            ).group_by(hour).order_by(hour.asc()).all()

            # Average consumption by ISO weekday (1=Mon .. 7=Sun)
            dow = func.extract("isodow", EnergyReading.recorded_at).label("dow")
            weekdays = in_range(
                session.query(
                    dow,
                    func.avg(EnergyReading.consumption).label("avg"),
                    func.count(EnergyReading.id).label("count"),
                )
            ).group_by(dow).order_by(dow.asc()).all()

            # Temperature vs consumption sample for the scatter plot
            scatter = in_range(
                session.query(
                    EnergyReading.temperature,
                    EnergyReading.consumption,
                    EnergyReading.hvac_usage,
                )
                .filter(EnergyReading.temperature.isnot(None))
            ).order_by(func.random()).limit(400).all()

            # Equipment / context impact: avg consumption per on/off state
            def _flag_avgs(column):
                rows = in_range(
                    session.query(
                        column,
                        func.avg(EnergyReading.consumption).label("avg"),
                        func.count(EnergyReading.id).label("count"),
                    )
                ).group_by(column).all()
                out = {"on": None, "off": None}
                for r in rows:
                    out["on" if r[0] else "off"] = round(float(r.avg or 0.0), 2)
                return out

            factors = {
                "hvac": _flag_avgs(EnergyReading.hvac_usage),
                "lighting": _flag_avgs(EnergyReading.lighting_usage),
                "holiday": _flag_avgs(EnergyReading.holiday),
            }

            # Average consumption by occupancy level
            occupancy = in_range(
                session.query(
                    EnergyReading.occupancy,
                    func.avg(EnergyReading.consumption).label("avg"),
                    func.count(EnergyReading.id).label("count"),
                )
                .filter(EnergyReading.occupancy.isnot(None))
            ).group_by(EnergyReading.occupancy).order_by(EnergyReading.occupancy.asc()).all()

            # Consumption vs renewable generation over time. Bucket by hour for
            # short ranges, by day otherwise.
            trunc = "hour" if (end_date - start_date) <= timedelta(days=3) else "day"
            bucket = func.date_trunc(trunc, EnergyReading.recorded_at).label("bucket")
            renewables = in_range(
                session.query(
                    bucket,
                    func.sum(EnergyReading.consumption).label("consumption"),
                    func.sum(func.coalesce(EnergyReading.renewable_energy, 0.0)).label("renewable"),
                )
            ).group_by(bucket).order_by(bucket.asc()).all()

            # Histogram of reading values (12 equal-width bins)
            bounds = in_range(
                session.query(
                    func.min(EnergyReading.consumption),
                    func.max(EnergyReading.consumption),
                )
            ).first()
            distribution = []
            if bounds and bounds[0] is not None and bounds[1] is not None and bounds[1] > bounds[0]:
                lo, hi, bins = float(bounds[0]), float(bounds[1]), 12
                bin_expr = func.width_bucket(EnergyReading.consumption, lo, hi, bins).label("bin")
                rows = in_range(
                    session.query(bin_expr, func.count(EnergyReading.id).label("count"))
                ).group_by(bin_expr).order_by(bin_expr.asc()).all()
                counts = {int(r.bin): int(r.count) for r in rows}
                width = (hi - lo) / bins
                distribution = [
                    {
                        "range_start": round(lo + (b - 1) * width, 1),
                        "range_end": round(lo + b * width, 1),
                        # width_bucket puts the max value in bin n+1 — fold it in
                        "count": counts.get(b, 0) + (counts.get(bins + 1, 0) if b == bins else 0),
                    }
                    for b in range(1, bins + 1)
                ]

        return {
            "hourly_profile": [
                {"hour": int(r.hour), "average": round(float(r.avg or 0.0), 2),
                 "max": round(float(r.max or 0.0), 2), "count": int(r.count)}
                for r in hourly
            ],
            "weekday_profile": [
                {"weekday": int(r.dow), "average": round(float(r.avg or 0.0), 2), "count": int(r.count)}
                for r in weekdays
            ],
            "temperature_scatter": [
                {"temperature": round(float(r.temperature), 1),
                 "consumption": round(float(r.consumption), 2),
                 "hvac": bool(r.hvac_usage)}
                for r in scatter
            ],
            "factors": factors,
            "occupancy_profile": [
                {"occupancy": int(r.occupancy), "average": round(float(r.avg or 0.0), 2), "count": int(r.count)}
                for r in occupancy
            ],
            "renewable_timeseries": [
                {"timestamp": r.bucket.isoformat(),
                 "consumption": round(float(r.consumption or 0.0), 2),
                 "renewable": round(float(r.renewable or 0.0), 2)}
                for r in renewables
            ],
            "distribution": distribution,
        }

    def export_to_csv(
        self,
        start_date: datetime,
        end_date: datetime,
        aggregation: Optional[str] = None,
    ) -> str:
        data = self.get_data_range(start_date, end_date, aggregation)
        if not data:
            return "timestamp,value,unit\n"
        lines = ["timestamp,value,unit"] + [f"{r['timestamp']},{r['value']},{r['unit']}" for r in data]
        return "\n".join(lines)

    def _get_period_boundaries(
        self,
        timestamp: datetime,
        period: AggregationPeriod,
    ) -> Tuple[datetime, datetime]:
        if period == AggregationPeriod.HOUR:
            start = timestamp.replace(minute=0, second=0, microsecond=0)
            return start, start + timedelta(hours=1)
        if period == AggregationPeriod.DAY:
            start = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            return start, start + timedelta(days=1)
        if period == AggregationPeriod.WEEK:
            start = (timestamp - timedelta(days=timestamp.weekday())).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            return start, start + timedelta(days=7)
        if period == AggregationPeriod.MONTH:
            start = timestamp.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start.replace(year=start.year + 1, month=1) if start.month == 12 else start.replace(month=start.month + 1)
            return start, end
        start = timestamp.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, start.replace(year=start.year + 1)


analytics_service = AnalyticsService()
