"""
Anomaly Detection Schemas
Pydantic models for anomaly detection requests and responses
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class AnomalyRecord(BaseModel):
    """Single anomaly detection record"""
    timestamp: datetime
    device_id: Optional[str] = None
    consumption: float
    expected_consumption: float
    anomaly_score: float
    severity: str = Field(..., description="low, medium, high")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2026-02-13T10:00:00",
                "device_id": "sensor_001",
                "consumption": 125.5,
                "expected_consumption": 45.2,
                "anomaly_score": 0.95,
                "severity": "high"
            }
        }


class AnomalyDetectionResponse(BaseModel):
    """Response schema for anomaly detection"""
    anomalies_detected: int = Field(..., description="Number of anomalies found")
    period_analyzed: str = Field(..., description="Time period analyzed")
    anomalies: List[AnomalyRecord] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "anomalies_detected": 3,
                "period_analyzed": "24 hours",
                "anomalies": []
            }
        }
