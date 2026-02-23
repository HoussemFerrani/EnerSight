"""
Enhanced analytics schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class AggregationPeriod(str, Enum):
    """Aggregation period options"""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class ComparisonType(str, Enum):
    """Comparison type options"""
    PREVIOUS_PERIOD = "previous_period"
    SAME_PERIOD_LAST_MONTH = "same_period_last_month"
    SAME_PERIOD_LAST_YEAR = "same_period_last_year"


class EnergyDataPoint(BaseModel):
    """Single energy data point"""
    timestamp: datetime
    value: float
    unit: str = "kWh"


class AggregatedData(BaseModel):
    """Aggregated energy data"""
    period_start: datetime
    period_end: datetime
    total: float
    average: float
    min: float
    max: float
    count: int
    unit: str = "kWh"


class CostCalculation(BaseModel):
    """Energy cost calculation result"""
    period_start: datetime
    period_end: datetime
    total_kwh: float
    cost_per_kwh: float
    total_cost: float
    currency: str = "USD"
    breakdown: Optional[dict] = None


class ComparisonResult(BaseModel):
    """Comparison analytics result"""
    current_period: AggregatedData
    comparison_period: AggregatedData
    difference: float
    percentage_change: float
    comparison_type: str


class AnalyticsSummary(BaseModel):
    """Overall analytics summary"""
    total_consumption: float
    average_daily: float
    peak_consumption: float
    peak_timestamp: datetime
    lowest_consumption: float
    lowest_timestamp: datetime
    total_cost: Optional[float] = None
    period_start: datetime
    period_end: datetime
    data_points: int


class ExportRequest(BaseModel):
    """Data export request"""
    start_date: datetime
    end_date: datetime
    format: str = Field(..., pattern="^(csv|excel|json)$")
    aggregation: Optional[AggregationPeriod] = None
    include_cost: bool = False
    cost_per_kwh: Optional[float] = None


class DateRangeRequest(BaseModel):
    """Date range filter request"""
    start_date: datetime
    end_date: datetime
    aggregation: Optional[AggregationPeriod] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "start_date": "2026-02-01T00:00:00Z",
                "end_date": "2026-02-22T23:59:59Z",
                "aggregation": "day"
            }
        }
    }
