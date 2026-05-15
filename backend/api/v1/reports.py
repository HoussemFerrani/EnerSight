"""
Report endpoints.

Returns generated PDF reports and CSV exports for a given period.
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from backend.api.dependencies.auth import get_current_user
from backend.models.user import User
from backend.services.analytics_service import analytics_service
from backend.services.optimization_service import DEFAULT_COST_PER_KWH
from backend.services.report_service import report_service

router = APIRouter()


@router.get(
    "/period.pdf",
    summary="Generate a PDF period report",
    responses={200: {"content": {"application/pdf": {}}}},
)
async def get_period_report_pdf(
    days: int = Query(30, ge=1, le=365, description="Trailing window length when start is omitted."),
    cost_per_kwh: float = Query(DEFAULT_COST_PER_KWH, gt=0),
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
) -> Response:
    end_dt = end or datetime.utcnow()
    start_dt = start or (end_dt - timedelta(days=days))
    author_name = current_user.full_name or current_user.username or current_user.email

    pdf_bytes = report_service.build_period_report(
        start=start_dt,
        end=end_dt,
        cost_per_kwh=cost_per_kwh,
        author_name=author_name,
    )
    filename = f"enersight-report-{start_dt.date()}_to_{end_dt.date()}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/period.csv",
    summary="Export period data as CSV",
)
async def get_period_report_csv(
    days: int = Query(30, ge=1, le=365),
    aggregation: Optional[str] = Query(None, description="One of hour, day, week, month, year. Omit for raw readings."),
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
) -> Response:
    end_dt = end or datetime.utcnow()
    start_dt = start or (end_dt - timedelta(days=days))

    csv_text = analytics_service.export_to_csv(start_dt, end_dt, aggregation)
    filename = f"enersight-readings-{start_dt.date()}_to_{end_dt.date()}.csv"
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
