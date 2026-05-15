"""
Optimization recommendations endpoints.

Exposes the rule-driven recommendations produced by `optimization_service`
to authenticated clients. Mounted under /api/v1/optimizations.
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query

from backend.api.dependencies.auth import get_current_user
from backend.models.user import User
from backend.schemas.optimization import OptimizationReport
from backend.services.optimization_service import (
    DEFAULT_COST_PER_KWH,
    DEFAULT_WINDOW_DAYS,
    optimization_service,
)

router = APIRouter()


@router.get("/", response_model=OptimizationReport, summary="Optimization recommendations")
async def get_optimization_report(
    days: int = Query(
        DEFAULT_WINDOW_DAYS,
        ge=1,
        le=365,
        description="Trailing window of days to analyse (default 30).",
    ),
    cost_per_kwh: float = Query(
        DEFAULT_COST_PER_KWH,
        gt=0,
        description="Local energy price for USD savings projection.",
    ),
    start: Optional[datetime] = Query(
        None,
        description="Explicit start of the analysis window; overrides `days`.",
    ),
    end: Optional[datetime] = Query(
        None,
        description="Explicit end of the analysis window; defaults to now.",
    ),
    current_user: User = Depends(get_current_user),
) -> OptimizationReport:
    end_dt = end or datetime.utcnow()
    start_dt = start or (end_dt - timedelta(days=days))
    return optimization_service.generate_report(
        start=start_dt,
        end=end_dt,
        cost_per_kwh=cost_per_kwh,
    )
