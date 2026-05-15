"""Pydantic schemas for the optimization recommendations feature."""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class RecommendationCategory(str, Enum):
    HVAC = "hvac"
    LIGHTING = "lighting"
    RENEWABLE = "renewable"
    BASELINE = "baseline"
    SCHEDULING = "scheduling"


class RecommendationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Recommendation(BaseModel):
    id: str = Field(..., description="Stable rule identifier (e.g. 'hvac_when_empty').")
    title: str
    category: RecommendationCategory
    severity: RecommendationSeverity
    description: str = Field(..., description="Human-readable explanation of the finding.")
    suggestion: str = Field(..., description="Concrete action the operator can take.")
    estimated_savings_kwh: float = Field(0.0, description="Projected savings per month, in kWh.")
    estimated_savings_usd: float = Field(0.0, description="Projected savings per month, in USD.")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="0-1 confidence in this finding.")
    supporting_metrics: Dict[str, float] = Field(default_factory=dict)


class OptimizationReport(BaseModel):
    period_start: datetime
    period_end: datetime
    cost_per_kwh: float
    total_recommendations: int
    total_estimated_savings_kwh: float
    total_estimated_savings_usd: float
    recommendations: List[Recommendation]
