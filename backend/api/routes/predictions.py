"""
Predictions Routes
Endpoints for ML-based energy consumption predictions
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Dict, Any, List

from backend.api.models.predictions import (
    PredictionRequest,
    PredictionResponse,
    ForecastResponse,
)
from backend.services.energy_service import EnergyService
from backend.core.dependencies import get_energy_service
from backend.core.exceptions import PredictionError, MLException
from backend.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict Energy Consumption",
    description="Predict energy consumption using Random Forest regression model"
)
async def predict_consumption(
    data: PredictionRequest,
    service: EnergyService = Depends(get_energy_service)
):
    """
    Predict energy consumption based on input features
    
    Uses trained Random Forest model to predict total consumption
    based on environmental factors and equipment usage patterns.
    
    Returns:
    - Predicted consumption value
    - Model name
    - Confidence score
    - Input features used
    """
    try:
        result = await service.predict_consumption(
            temperature=data.temperature,
            humidity=data.humidity,
            occupancy=data.occupancy,
            hvac_usage=data.hvac_usage,
            lighting_usage=data.lighting_usage,
            equipment_usage=data.equipment_usage,
            renewable_energy=data.renewable_energy,
            for_timestamp=data.for_timestamp,
        )
        return result
    
    except PredictionError as e:
        logger.error(f"Prediction error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except MLException as e:
        logger.error(f"ML model error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error during prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/forecast",
    response_model=ForecastResponse,
    summary="Forecast Energy Consumption",
    description="Generate time-series forecast using LSTM neural network"
)
async def forecast_consumption(
    historical_data: List[float],
    hours: int = Query(24, ge=1, le=168, description="Number of hours to forecast (max 168 = 1 week)"),
    service: EnergyService = Depends(get_energy_service)
):
    """
    Forecast future energy consumption using LSTM model
    
    Requires historical consumption data (at least 24 data points)
    to generate future predictions.
    
    Args:
    - historical_data: List of recent consumption values (kWh)
    - hours: Number of hours ahead to forecast
    
    Returns:
    - Forecasted consumption values
    - Forecast horizon
    - Model information
    """
    try:
        if len(historical_data) < 24:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient historical data. Need at least 24 data points."
            )
        
        result = await service.forecast_consumption(
            historical_data=historical_data,
            forecast_hours=hours,
        )
        return result
    
    except PredictionError as e:
        logger.error(f"Forecast error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except MLException as e:
        logger.error(f"ML model error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=e.message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during forecasting: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
