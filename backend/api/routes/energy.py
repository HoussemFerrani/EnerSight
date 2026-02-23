"""
Energy Data Routes
Endpoints for energy consumption data retrieval and management
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Optional, List
from datetime import datetime, timedelta

from backend.api.models.energy import (
    EnergyReadingCreate,
    EnergyReadingResponse,
    EnergyStatistics,
)
from backend.services.energy_service import EnergyService
from backend.core.dependencies import get_energy_service
from backend.core.exceptions import ValidationError, ResourceNotFoundError
from backend.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/readings",
    response_model=EnergyReadingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Energy Reading",
    description="Record a new energy consumption reading with device and environmental data"
)
async def record_energy_reading(
    reading: EnergyReadingCreate,
    service: EnergyService = Depends(get_energy_service)
):
    """
    Record a new energy consumption reading
    
    Business Logic:
    - Validates all input parameters
    - Calculates total and net consumption
    - Performs real-time anomaly detection
    - Stores in time-series database
    """
    try:
        result = await service.record_energy_reading(
            device_id=reading.device_id,
            location=reading.location,
            temperature=reading.temperature,
            humidity=reading.humidity,
            occupancy=reading.occupancy,
            hvac_usage=reading.hvac_usage,
            lighting_usage=reading.lighting_usage,
            equipment_usage=reading.equipment_usage,
            renewable_energy=reading.renewable_energy,
            timestamp=reading.timestamp,
        )
        return result
    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to record reading: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/readings",
    summary="Get Historical Readings",
    description="Retrieve historical energy consumption data with optional aggregation"
)
async def get_historical_readings(
    start_date: Optional[str] = Query(None, description="Start date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    aggregation: str = Query("raw", description="Aggregation type: raw, mean, sum, max, min"),
    window: str = Query("1h", description="Time window for aggregation (e.g., 1h, 1d, 1w)"),
    service: EnergyService = Depends(get_energy_service)
):
    """
    Get historical energy consumption data
    
    Query Parameters:
    - start_date: Start timestamp (defaults to 24 hours ago)
    - end_date: End timestamp (defaults to now)
    - device_id: Optional device filter
    - aggregation: Data aggregation method
    - window: Time window for aggregation
    """
    try:
        # Parse dates or use defaults
        if start_date:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            start = datetime.utcnow() - timedelta(hours=24)
        
        if end_date:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end = datetime.utcnow()
        
        data = await service.get_consumption_history(
            start=start,
            end=end,
            device_id=device_id,
            aggregation=aggregation,
            window=window,
        )
        
        return {
            "data": data,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "aggregation": aggregation,
            "count": len(data),
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to fetch historical data: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/statistics",
    response_model=EnergyStatistics,
    summary="Get Energy Statistics",
    description="Calculate aggregated energy consumption statistics for a time period"
)
async def get_energy_statistics(
    period: str = Query("week", description="Period: day, week, month, year"),
    start_date: Optional[str] = Query(None, description="Custom start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Custom end date (ISO format)"),
    service: EnergyService = Depends(get_energy_service)
):
    """
    Get energy consumption statistics
    
    Calculates:
    - Total consumption
    - Average daily consumption
    - Peak consumption
    - Minimum consumption
    """
    try:
        # Determine time range based on period
        end = datetime.utcnow()
        
        if start_date and end_date:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            period_map = {
                "day": timedelta(days=1),
                "week": timedelta(weeks=1),
                "month": timedelta(days=30),
                "year": timedelta(days=365),
            }
            delta = period_map.get(period, timedelta(weeks=1))
            start = end - delta
        
        stats = await service.calculate_statistics(start=start, end=end)
        return stats
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to calculate statistics: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
