"""
Enhanced analytics API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta
from typing import Optional
import io

from backend.services.analytics_service import analytics_service
from backend.schemas.analytics import (
    DateRangeRequest,
    ExportRequest,
    AnalyticsSummary,
    AggregatedData,
    ComparisonResult,
    CostCalculation,
    AggregationPeriod,
    ComparisonType
)
from backend.api.dependencies.auth import get_current_user
from backend.models.user import User

router = APIRouter()


@router.post("/date-range", response_model=list)
async def get_data_by_date_range(
    request: DateRangeRequest,
    current_user: User = Depends(get_current_user)
):
    """Get energy data for a specific date range with optional aggregation"""
    try:
        data = analytics_service.get_data_range(
            start_date=request.start_date,
            end_date=request.end_date,
            aggregation=request.aggregation.value if request.aggregation else None
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    cost_per_kwh: Optional[float] = Query(None, description="Cost per kWh for cost calculation"),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive analytics summary for a period"""
    try:
        summary = analytics_service.get_summary(
            start_date=start_date,
            end_date=end_date,
            cost_per_kwh=cost_per_kwh
        )
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@router.get("/aggregated", response_model=list[AggregatedData])
async def get_aggregated_analytics(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    period: AggregationPeriod = Query(..., description="Aggregation period (hour, day, week, month, year)"),
    current_user: User = Depends(get_current_user)
):
    """Get aggregated energy data by time period"""
    try:
        data = analytics_service.get_aggregated_data(
            start_date=start_date,
            end_date=end_date,
            period=period
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to aggregate data: {str(e)}")


@router.get("/cost", response_model=CostCalculation)
async def calculate_energy_cost(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    cost_per_kwh: float = Query(0.12, description="Cost per kWh (default: $0.12)"),
    current_user: User = Depends(get_current_user)
):
    """Calculate energy cost for a period"""
    try:
        cost = analytics_service.calculate_cost(
            start_date=start_date,
            end_date=end_date,
            cost_per_kwh=cost_per_kwh
        )
        return cost
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate cost: {str(e)}")


@router.get("/compare", response_model=ComparisonResult)
async def compare_periods(
    current_start: datetime = Query(...),
    current_end: datetime = Query(...),
    comparison_type: ComparisonType = Query(ComparisonType.PREVIOUS_PERIOD),
    current_user: User = Depends(get_current_user)
):
    """Compare current period with another period"""
    try:
        comparison = analytics_service.compare_periods(
            current_start=current_start,
            current_end=current_end,
            comparison_type=comparison_type.value
        )
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare periods: {str(e)}")


@router.get("/breakdown")
async def get_breakdowns(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    current_user: User = Depends(get_current_user)
):
    """
    Multi-dimensional breakdowns for the analytics dashboard: hourly/weekday
    profiles, temperature scatter, equipment impact, occupancy, renewables,
    and the consumption distribution.
    """
    try:
        return analytics_service.get_breakdowns(start_date=start_date, end_date=end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute breakdowns: {str(e)}")


@router.get("/export/csv")
async def export_to_csv(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    aggregation: Optional[AggregationPeriod] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Export energy data to CSV file"""
    try:
        csv_data = analytics_service.export_to_csv(
            start_date=start_date,
            end_date=end_date,
            aggregation=aggregation.value if aggregation else None
        )
        
        # Create filename with date range
        filename = f"energy_data_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
        
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export data: {str(e)}")


@router.get("/quick-stats")
async def get_quick_stats(
    current_user: User = Depends(get_current_user)
):
    """Get quick statistics for common time periods"""
    try:
        now = datetime.utcnow()
        
        # Today
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_summary = analytics_service.get_summary(today_start, now)
        
        # This week
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_summary = analytics_service.get_summary(week_start, now)
        
        # This month
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_summary = analytics_service.get_summary(month_start, now)
        
        # Last 24 hours
        day_ago = now - timedelta(hours=24)
        last_24h_summary = analytics_service.get_summary(day_ago, now)
        
        return {
            "today": {
                "total": today_summary.total_consumption,
                "average": today_summary.average_daily,
                "peak": today_summary.peak_consumption
            },
            "this_week": {
                "total": week_summary.total_consumption,
                "average": week_summary.average_daily,
                "peak": week_summary.peak_consumption
            },
            "this_month": {
                "total": month_summary.total_consumption,
                "average": month_summary.average_daily,
                "peak": month_summary.peak_consumption
            },
            "last_24h": {
                "total": last_24h_summary.total_consumption,
                "average": last_24h_summary.average_daily,
                "peak": last_24h_summary.peak_consumption
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get quick stats: {str(e)}")


@router.get("/trends")
async def get_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user)
):
    """Get energy consumption trends over time"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get daily aggregated data
        daily_data = analytics_service.get_aggregated_data(
            start_date=start_date,
            end_date=end_date,
            period=AggregationPeriod.DAY
        )
        
        # Calculate trend
        if len(daily_data) >= 2:
            first_half = daily_data[:len(daily_data)//2]
            second_half = daily_data[len(daily_data)//2:]
            
            first_avg = sum(d.average for d in first_half) / len(first_half)
            second_avg = sum(d.average for d in second_half) / len(second_half)
            
            trend_direction = "increasing" if second_avg > first_avg else "decreasing"
            trend_percentage = ((second_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0
        else:
            trend_direction = "stable"
            trend_percentage = 0.0
        
        return {
            "period_days": days,
            "data_points": len(daily_data),
            "trend_direction": trend_direction,
            "trend_percentage": round(trend_percentage, 2),
            "daily_data": [
                {
                    "date": d.period_start.isoformat(),
                    "total": d.total,
                    "average": d.average
                }
                for d in daily_data
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate trends: {str(e)}")
