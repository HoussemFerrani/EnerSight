"""
Alert schemas for API validation
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class AlertTypeEnum(str, Enum):
    """Alert type enumeration"""
    THRESHOLD_EXCEEDED = "threshold_exceeded"
    ANOMALY_DETECTED = "anomaly_detected"
    SYSTEM_WARNING = "system_warning"
    COST_ALERT = "cost_alert"


class AlertSeverityEnum(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatusEnum(str, Enum):
    """Alert status"""
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AlertCreate(BaseModel):
    """Schema for creating an alert"""
    user_id: int
    alert_type: AlertTypeEnum
    severity: AlertSeverityEnum = AlertSeverityEnum.WARNING
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1)
    current_value: Optional[float] = None
    threshold_value: Optional[float] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": 1,
                "alert_type": "threshold_exceeded",
                "severity": "warning",
                "title": "Energy threshold exceeded",
                "message": "Your energy consumption has exceeded the set threshold of 1000 kWh",
                "current_value": 1250.5,
                "threshold_value": 1000.0
            }
        }
    }


class AlertUpdate(BaseModel):
    """Schema for updating an alert"""
    status: Optional[AlertStatusEnum] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class AlertResponse(BaseModel):
    """Schema for alert response"""
    id: int
    user_id: int
    alert_type: str
    severity: str
    status: str
    title: str
    message: str
    current_value: Optional[float] = None
    threshold_value: Optional[float] = None
    email_sent: bool
    push_sent: bool
    created_at: datetime
    sent_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "user_id": 1,
                "alert_type": "threshold_exceeded",
                "severity": "warning",
                "status": "sent",
                "title": "Energy threshold exceeded",
                "message": "Your energy consumption has exceeded the set threshold",
                "current_value": 1250.5,
                "threshold_value": 1000.0,
                "email_sent": True,
                "push_sent": False,
                "created_at": "2026-02-22T12:00:00",
                "sent_at": "2026-02-22T12:00:05",
                "acknowledged_at": None,
                "resolved_at": None
            }
        }
    }


class AlertSummary(BaseModel):
    """Summary of alerts"""
    total_alerts: int
    pending_alerts: int
    critical_alerts: int
    unacknowledged_alerts: int
    alerts_today: int
