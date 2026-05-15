"""
Optimization recommendations service.

Runs a small rules engine over `public.energy_readings` and produces
actionable energy-efficiency recommendations with projected savings.

Each rule:
  - Reads readings in [start, end)
  - Returns 0 or 1 Recommendation (no recommendation when the rule's
    threshold isn't met — silence is meaningful)
  - Projects savings to a monthly horizon so the dashboard can rank
    recommendations by impact regardless of the analysis window
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import case, func

from backend.database.postgres import SessionLocal
from backend.models.energy import EnergyReading
from backend.schemas.optimization import (
    OptimizationReport,
    Recommendation,
    RecommendationCategory,
    RecommendationSeverity,
)


DEFAULT_COST_PER_KWH = 0.12
DEFAULT_WINDOW_DAYS = 30


def _scale_to_month(value_kwh: float, window_days: float) -> float:
    """Project a kWh figure observed over `window_days` to a monthly horizon."""
    if window_days <= 0:
        return 0.0
    return value_kwh * (30.0 / window_days)


def _confidence_from_sample(n: int) -> float:
    """Simple saturating confidence: more samples → more trust, capped at 0.95."""
    if n <= 0:
        return 0.0
    return min(0.95, 0.4 + 0.55 * (1.0 - 1.0 / (1.0 + n / 50.0)))


class OptimizationService:
    """Stateless rules engine. Each rule is a method returning Optional[Recommendation]."""

    def generate_report(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        cost_per_kwh: float = DEFAULT_COST_PER_KWH,
    ) -> OptimizationReport:
        end = end or datetime.utcnow()
        start = start or end - timedelta(days=DEFAULT_WINDOW_DAYS)
        window_days = max((end - start).total_seconds() / 86400.0, 1.0)

        rules = (
            self._rule_hvac_when_empty,
            self._rule_lights_when_empty,
            self._rule_underused_renewable,
            self._rule_weekend_phantom_load,
        )

        recs: List[Recommendation] = []
        with SessionLocal() as session:
            for rule in rules:
                rec = rule(session, start, end, window_days, cost_per_kwh)
                if rec is not None:
                    recs.append(rec)

        # Rank by projected USD savings (desc), then severity.
        sev_rank = {
            RecommendationSeverity.CRITICAL: 0,
            RecommendationSeverity.WARNING: 1,
            RecommendationSeverity.INFO: 2,
        }
        recs.sort(key=lambda r: (-r.estimated_savings_usd, sev_rank[r.severity]))

        return OptimizationReport(
            period_start=start,
            period_end=end,
            cost_per_kwh=cost_per_kwh,
            total_recommendations=len(recs),
            total_estimated_savings_kwh=sum(r.estimated_savings_kwh for r in recs),
            total_estimated_savings_usd=sum(r.estimated_savings_usd for r in recs),
            recommendations=recs,
        )

    # ------------------------------------------------------------------
    # Rule 1: HVAC running while building is empty.
    # ------------------------------------------------------------------
    def _rule_hvac_when_empty(self, session, start, end, window_days, cost_per_kwh):
        row = (
            session.query(
                func.coalesce(func.sum(EnergyReading.consumption), 0.0).label("wasted_kwh"),
                func.count(EnergyReading.id).label("n"),
                func.coalesce(func.sum(
                    case((EnergyReading.hvac_usage.is_(True), 1), else_=0)
                ), 0).label("hvac_total"),
            )
            .filter(
                EnergyReading.recorded_at >= start,
                EnergyReading.recorded_at < end,
                EnergyReading.hvac_usage.is_(True),
                EnergyReading.occupancy == 0,
            )
            .one()
        )
        wasted = float(row.wasted_kwh or 0.0)
        n = int(row.n or 0)
        if wasted <= 0 or n < 5:
            return None

        # How prevalent is this pattern? Use it for severity.
        hvac_total = session.query(func.count(EnergyReading.id)).filter(
            EnergyReading.recorded_at >= start,
            EnergyReading.recorded_at < end,
            EnergyReading.hvac_usage.is_(True),
        ).scalar() or 0
        share = n / hvac_total if hvac_total > 0 else 0.0
        severity = (
            RecommendationSeverity.CRITICAL if share > 0.30
            else RecommendationSeverity.WARNING if share > 0.10
            else RecommendationSeverity.INFO
        )

        monthly_kwh = _scale_to_month(wasted, window_days)
        return Recommendation(
            id="hvac_when_empty",
            title="HVAC is running while the building is empty",
            category=RecommendationCategory.HVAC,
            severity=severity,
            description=(
                f"Detected {n} readings where HVAC was active with zero occupancy, "
                f"consuming {wasted:.1f} kWh over the analysis window "
                f"({share * 100:.1f}% of all HVAC-on readings)."
            ),
            suggestion=(
                "Tie HVAC scheduling to occupancy: set an unoccupied setpoint with a "
                "wider deadband, or wire HVAC to occupancy sensors so it cools/heats "
                "only when the space is in use."
            ),
            estimated_savings_kwh=round(monthly_kwh, 2),
            estimated_savings_usd=round(monthly_kwh * cost_per_kwh, 2),
            confidence=_confidence_from_sample(n),
            supporting_metrics={
                "readings_affected": float(n),
                "wasted_kwh_in_window": round(wasted, 2),
                "share_of_hvac_on_time": round(share, 4),
            },
        )

    # ------------------------------------------------------------------
    # Rule 2: Lights on while building is empty.
    # ------------------------------------------------------------------
    def _rule_lights_when_empty(self, session, start, end, window_days, cost_per_kwh):
        row = (
            session.query(
                func.coalesce(func.sum(EnergyReading.consumption), 0.0).label("wasted_kwh"),
                func.count(EnergyReading.id).label("n"),
            )
            .filter(
                EnergyReading.recorded_at >= start,
                EnergyReading.recorded_at < end,
                EnergyReading.lighting_usage.is_(True),
                EnergyReading.occupancy == 0,
            )
            .one()
        )
        wasted = float(row.wasted_kwh or 0.0)
        n = int(row.n or 0)
        if wasted <= 0 or n < 5:
            return None

        # Lighting is typically a smaller share of total kWh than HVAC; reflect
        # that by attributing only an estimated lighting fraction of the
        # measured consumption to lighting savings.
        LIGHTING_FRACTION = 0.25
        savings = wasted * LIGHTING_FRACTION
        monthly_kwh = _scale_to_month(savings, window_days)

        severity = (
            RecommendationSeverity.WARNING if n > 50
            else RecommendationSeverity.INFO
        )
        return Recommendation(
            id="lights_when_empty",
            title="Lighting is on while the building is empty",
            category=RecommendationCategory.LIGHTING,
            severity=severity,
            description=(
                f"Detected {n} readings where lighting was on with zero occupancy. "
                f"Lighting accounts for an estimated {LIGHTING_FRACTION * 100:.0f}% "
                f"of recorded consumption in this segment ({savings:.1f} kWh)."
            ),
            suggestion=(
                "Install passive-infrared (PIR) motion sensors in low-traffic areas, "
                "and add a default after-hours shutdown schedule for lighting circuits."
            ),
            estimated_savings_kwh=round(monthly_kwh, 2),
            estimated_savings_usd=round(monthly_kwh * cost_per_kwh, 2),
            confidence=_confidence_from_sample(n),
            supporting_metrics={
                "readings_affected": float(n),
                "consumption_in_window": round(wasted, 2),
                "lighting_fraction_assumed": LIGHTING_FRACTION,
            },
        )

    # ------------------------------------------------------------------
    # Rule 3: Renewable generation is underutilised.
    # ------------------------------------------------------------------
    def _rule_underused_renewable(self, session, start, end, window_days, cost_per_kwh):
        # Compare the grid consumption that happens *during* high-renewable
        # readings to the overall median. If renewable is high but grid use is
        # still high, discretionary loads could shift into the renewable window.
        row = (
            session.query(
                func.coalesce(func.sum(EnergyReading.renewable_energy), 0.0).label("total_renew"),
                func.coalesce(func.avg(EnergyReading.consumption), 0.0).label("avg_cons"),
                func.coalesce(func.avg(EnergyReading.renewable_energy), 0.0).label("avg_renew"),
                func.count(EnergyReading.id).label("n"),
            )
            .filter(
                EnergyReading.recorded_at >= start,
                EnergyReading.recorded_at < end,
                EnergyReading.renewable_energy.isnot(None),
            )
            .one()
        )
        n = int(row.n or 0)
        avg_renew = float(row.avg_renew or 0.0)
        if n < 20 or avg_renew <= 0:
            return None

        # Readings where renewable was above average AND consumption was also
        # above average: an opportunity to shift load into the renewable window.
        opp = (
            session.query(
                func.count(EnergyReading.id).label("n"),
                func.coalesce(func.sum(EnergyReading.renewable_energy), 0.0).label("renew_kwh"),
            )
            .filter(
                EnergyReading.recorded_at >= start,
                EnergyReading.recorded_at < end,
                EnergyReading.renewable_energy > row.avg_renew,
                EnergyReading.consumption > row.avg_cons,
            )
            .one()
        )
        opp_n = int(opp.n or 0)
        renew_kwh = float(opp.renew_kwh or 0.0)
        if opp_n < 5 or renew_kwh <= 0:
            return None

        # Conservative assumption: only 30% of renewable above average is
        # actually shiftable load.
        SHIFTABLE_FRACTION = 0.30
        savings = renew_kwh * SHIFTABLE_FRACTION
        monthly_kwh = _scale_to_month(savings, window_days)

        return Recommendation(
            id="underused_renewable",
            title="Renewable generation is underutilised at peak production hours",
            category=RecommendationCategory.RENEWABLE,
            severity=RecommendationSeverity.INFO,
            description=(
                f"Across {opp_n} high-renewable readings, grid consumption stayed "
                f"above the average ({float(row.avg_cons):.2f} kWh). Renewable "
                f"output during these readings totalled {renew_kwh:.1f} kWh."
            ),
            suggestion=(
                "Shift flexible loads (water heating, EV charging, batch processes) "
                "into the highest renewable-production hours to maximise on-site "
                "use of clean energy."
            ),
            estimated_savings_kwh=round(monthly_kwh, 2),
            estimated_savings_usd=round(monthly_kwh * cost_per_kwh, 2),
            confidence=_confidence_from_sample(opp_n),
            supporting_metrics={
                "opportunity_readings": float(opp_n),
                "avg_renewable_kwh": round(avg_renew, 3),
                "avg_consumption_kwh": round(float(row.avg_cons), 3),
                "shiftable_fraction_assumed": SHIFTABLE_FRACTION,
            },
        )

    # ------------------------------------------------------------------
    # Rule 4: Weekend / holiday baseline > weekday baseline (phantom loads).
    # ------------------------------------------------------------------
    def _rule_weekend_phantom_load(self, session, start, end, window_days, cost_per_kwh):
        # day_of_week 5/6 = Saturday/Sunday in the loader's convention.
        weekend_min = session.query(func.min(EnergyReading.consumption)).filter(
            EnergyReading.recorded_at >= start,
            EnergyReading.recorded_at < end,
            EnergyReading.day_of_week.in_([5, 6]),
        ).scalar()
        weekday_min = session.query(func.min(EnergyReading.consumption)).filter(
            EnergyReading.recorded_at >= start,
            EnergyReading.recorded_at < end,
            EnergyReading.day_of_week.in_([0, 1, 2, 3, 4]),
        ).scalar()
        weekend_count = session.query(func.count(EnergyReading.id)).filter(
            EnergyReading.recorded_at >= start,
            EnergyReading.recorded_at < end,
            EnergyReading.day_of_week.in_([5, 6]),
        ).scalar() or 0

        if weekend_min is None or weekday_min is None or weekend_count < 20:
            return None
        weekend_min = float(weekend_min)
        weekday_min = float(weekday_min)
        if weekday_min <= 0 or weekend_min <= weekday_min:
            return None

        # If weekend minimum exceeds weekday minimum, that gap is the phantom
        # load running 24h on weekends.
        gap_per_reading = weekend_min - weekday_min
        # Project to a monthly figure: ~8 weekend days × 24h per month × gap.
        # We use weekend_count as an approximate hours-of-weekend in window.
        gap_total_in_window = gap_per_reading * weekend_count
        monthly_kwh = _scale_to_month(gap_total_in_window, window_days)

        severity = (
            RecommendationSeverity.WARNING if gap_per_reading / weekday_min > 0.20
            else RecommendationSeverity.INFO
        )
        return Recommendation(
            id="weekend_phantom_load",
            title="Weekend baseline consumption suggests always-on equipment",
            category=RecommendationCategory.BASELINE,
            severity=severity,
            description=(
                f"Weekend minimum consumption ({weekend_min:.2f} kWh) is "
                f"{(gap_per_reading / weekday_min) * 100:.1f}% higher than the "
                f"weekday minimum ({weekday_min:.2f} kWh). The gap is consistent "
                f"with always-on devices that don't follow a weekday schedule."
            ),
            suggestion=(
                "Audit equipment that runs unattended on weekends: server racks, "
                "fume hoods, vending machines, idle workstations. Add scheduled "
                "shutdowns or smart power strips."
            ),
            estimated_savings_kwh=round(monthly_kwh, 2),
            estimated_savings_usd=round(monthly_kwh * cost_per_kwh, 2),
            confidence=_confidence_from_sample(weekend_count),
            supporting_metrics={
                "weekend_min_kwh": round(weekend_min, 3),
                "weekday_min_kwh": round(weekday_min, 3),
                "gap_kwh": round(gap_per_reading, 3),
                "weekend_readings": float(weekend_count),
            },
        )


optimization_service = OptimizationService()
