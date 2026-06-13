"""
Anomaly Detection Routes
Endpoints for detecting unusual energy consumption patterns
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List
from datetime import datetime, timedelta, timezone

from backend.api.models.anomalies import AnomalyDetectionResponse
from backend.services.energy_service import EnergyService
from backend.core.dependencies import get_energy_service
from backend.core.exceptions import MLException
from backend.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/detect",
    response_model=AnomalyDetectionResponse,
    summary="Detect Anomalies",
    description="Detect unusual energy consumption patterns using Isolation Forest algorithm"
)
async def detect_anomalies(
    hours: int = Query(24, ge=1, le=720, description="Hours to analyze (max 720 = 30 days)"),
    service: EnergyService = Depends(get_energy_service)
):
    """
    Detect anomalies in recent energy consumption
    
    Uses Isolation Forest algorithm to identify unusual consumption
    patterns that may indicate:
    - Equipment malfunction
    - Inefficient device behavior
    - Unusual usage patterns
    - Potential energy waste
    
    Args:
    - hours: Number of recent hours to analyze
    
    Returns:
    - Number of anomalies detected
    - List of anomaly records with details
    - Period analyzed
    """
    try:
        end = datetime.now(timezone.utc)
        start = end - timedelta(hours=hours)
        
        anomalies = await service.detect_anomalies(start=start, end=end)
        
        return {
            "anomalies_detected": len(anomalies),
            "period_analyzed": f"{hours} hours",
            "anomalies": anomalies,
        }
    
    except MLException as e:
        logger.error(f"ML model error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Failed to detect anomalies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/history",
    summary="Get Anomaly History",
    description="Retrieve historical anomaly detections"
)
async def get_anomaly_history(
    days: int = Query(7, ge=1, le=90, description="Number of days to retrieve"),
    service: EnergyService = Depends(get_energy_service)
):
    """
    Get historical anomaly detections
    
    Returns detected anomalies from the specified time period
    for trend analysis and reporting.
    
    Args:
    - days: Number of days to look back
    
    Returns:
    - Total anomalies count
    - List of historical anomaly records
    """
    try:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        
        anomalies = await service.detect_anomalies(start=start, end=end)
        
        return {
            "total_anomalies": len(anomalies),
            "days_analyzed": days,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "anomalies": anomalies,
        }
    
    except MLException as e:
        logger.error(f"ML model error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Failed to fetch anomaly history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
