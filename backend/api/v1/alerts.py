"""
Alert API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime, timedelta

from backend.database.postgres import get_db
from backend.models.alert import Alert, AlertStatus, AlertSeverity, AlertType
from backend.models.user import User
from backend.schemas.alert import (
    AlertCreate,
    AlertUpdate,
    AlertResponse,
    AlertSummary,
    AlertStatusEnum
)
from backend.api.dependencies.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    status: Optional[AlertStatusEnum] = None,
    severity: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get alerts for current user with optional filters"""
    query = db.query(Alert).filter(Alert.user_id == int(current_user.id))
    
    if status:
        query = query.filter(Alert.status == status.value)
    
    if severity:
        query = query.filter(Alert.severity == severity)
    
    # Order by most recent first
    query = query.order_by(desc(Alert.created_at))
    
    alerts = query.offset(offset).limit(limit).all()
    
    return [AlertResponse.model_validate(alert) for alert in alerts]


@router.get("/summary", response_model=AlertSummary)
async def get_alert_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get alert summary statistics for current user"""
    user_id = int(current_user.id)
    
    # Total alerts
    total_alerts = db.query(func.count(Alert.id)).filter(Alert.user_id == user_id).scalar()
    
    # Pending alerts
    pending_alerts = db.query(func.count(Alert.id)).filter(
        Alert.user_id == user_id,
        Alert.status == AlertStatus.PENDING
    ).scalar()
    
    # Critical alerts
    critical_alerts = db.query(func.count(Alert.id)).filter(
        Alert.user_id == user_id,
        Alert.severity == AlertSeverity.CRITICAL,
        Alert.status.in_([AlertStatus.PENDING, AlertStatus.SENT])
    ).scalar()
    
    # Unacknowledged alerts
    unacknowledged_alerts = db.query(func.count(Alert.id)).filter(
        Alert.user_id == user_id,
        Alert.acknowledged_at.is_(None),
        Alert.status != AlertStatus.RESOLVED
    ).scalar()
    
    # Alerts today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    alerts_today = db.query(func.count(Alert.id)).filter(
        Alert.user_id == user_id,
        Alert.created_at >= today_start
    ).scalar()
    
    return AlertSummary(
        total_alerts=total_alerts or 0,
        pending_alerts=pending_alerts or 0,
        critical_alerts=critical_alerts or 0,
        unacknowledged_alerts=unacknowledged_alerts or 0,
        alerts_today=alerts_today or 0
    )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific alert by ID"""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == int(current_user.id)
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return AlertResponse.model_validate(alert)


@router.post("/", response_model=AlertResponse, status_code=201)
async def create_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new alert (admin or system use)"""
    # Verify user is creating alert for themselves or is admin
    if int(current_user.id) != alert_data.user_id and str(current_user.role) != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to create alerts for other users")
    
    alert = Alert(
        user_id=alert_data.user_id,
        alert_type=alert_data.alert_type.value,
        severity=alert_data.severity.value,
        title=alert_data.title,
        message=alert_data.message,
        current_value=alert_data.current_value,
        threshold_value=alert_data.threshold_value,
        status=AlertStatus.PENDING
    )
    
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    return AlertResponse.model_validate(alert)


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    alert_update: AlertUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update alert status (acknowledge/resolve)"""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == int(current_user.id)
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Update fields
    if alert_update.status:
        alert.status = alert_update.status.value
        
        # Auto-set timestamps based on status
        if alert_update.status == AlertStatusEnum.ACKNOWLEDGED and not alert.acknowledged_at:
            alert.acknowledged_at = datetime.utcnow()
        elif alert_update.status == AlertStatusEnum.RESOLVED and not alert.resolved_at:
            alert.resolved_at = datetime.utcnow()
    
    if alert_update.acknowledged_at:
        alert.acknowledged_at = alert_update.acknowledged_at
    
    if alert_update.resolved_at:
        alert.resolved_at = alert_update.resolved_at
    
    db.commit()
    db.refresh(alert)
    
    return AlertResponse.model_validate(alert)


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Acknowledge an alert"""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == int(current_user.id)
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = AlertStatus.ACKNOWLEDGED
    alert.acknowledged_at = datetime.utcnow()
    
    db.commit()
    db.refresh(alert)
    
    return AlertResponse.model_validate(alert)


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resolve an alert"""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == int(current_user.id)
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = AlertStatus.RESOLVED
    alert.resolved_at = datetime.utcnow()
    
    if not alert.acknowledged_at:
        alert.acknowledged_at = datetime.utcnow()
    
    db.commit()
    db.refresh(alert)
    
    return AlertResponse.model_validate(alert)


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an alert"""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == int(current_user.id)
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    db.delete(alert)
    db.commit()
    
    return None
