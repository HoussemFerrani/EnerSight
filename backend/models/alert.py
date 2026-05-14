"""
Alert models for energy consumption monitoring
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.database.postgres import Base
import enum


class AlertType(str, enum.Enum):
    """Alert type enumeration"""
    THRESHOLD_EXCEEDED = "threshold_exceeded"
    ANOMALY_DETECTED = "anomaly_detected"
    SYSTEM_WARNING = "system_warning"
    COST_ALERT = "cost_alert"


class AlertSeverity(str, enum.Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    """Alert status"""
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class Alert(Base):
    """Alert model for energy consumption notifications"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Alert details
    alert_type = Column(Enum(AlertType), nullable=False)
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.WARNING, nullable=False)
    status = Column(Enum(AlertStatus), default=AlertStatus.PENDING, nullable=False)
    
    # Message details
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Metrics
    current_value = Column(Float)
    threshold_value = Column(Float)
    
    # Notification flags
    email_sent = Column(Boolean, default=False)
    push_sent = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime)
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    
    # Relationship
    user = relationship("Profile", backref="alerts")
    
    def __repr__(self):
        return f"<Alert {self.id} - {self.alert_type} ({self.severity})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "user_id": str(self.user_id) if self.user_id else None,
            "alert_type": self.alert_type.value if self.alert_type else None,
            "severity": self.severity.value if self.severity else None,
            "status": self.status.value if self.status else None,
            "title": self.title,
            "message": self.message,
            "current_value": self.current_value,
            "threshold_value": self.threshold_value,
            "email_sent": self.email_sent,
            "push_sent": self.push_sent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
