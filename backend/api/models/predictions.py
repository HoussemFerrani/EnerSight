"""
Prediction Schemas
Pydantic models for ML prediction requests and responses
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class PredictionRequest(BaseModel):
    """Request schema for energy consumption prediction"""
    temperature: float = Field(..., ge=-50, le=60, description="Temperature in Celsius")
    humidity: float = Field(..., ge=0, le=100, description="Humidity percentage")
    occupancy: int = Field(..., ge=0, description="Number of occupants")
    hvac_usage: float = Field(..., ge=0, description="HVAC consumption in kWh")
    lighting_usage: float = Field(..., ge=0, description="Lighting consumption in kWh")
    equipment_usage: float = Field(..., ge=0, description="Equipment consumption in kWh")
    renewable_energy: float = Field(..., ge=0, description="Renewable generation in kWh")
    for_timestamp: Optional[datetime] = Field(
        None,
        description=(
            "Wall-clock time the prediction is about (ISO-8601). Defaults to "
            "now. Set this when predicting against historical sensor readings "
            "so the drift backfill can match against the right energy_readings row."
        ),
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "temperature": 22.5,
                "humidity": 45.0,
                "occupancy": 15,
                "hvac_usage": 12.5,
                "lighting_usage": 3.2,
                "equipment_usage": 8.7,
                "renewable_energy": 5.0
            }
        }


class PredictionResponse(BaseModel):
    """Response schema for prediction"""
    predicted_consumption: float = Field(..., description="Predicted consumption in kWh")
    model: str = Field(..., description="Model used for prediction")
    confidence: float = Field(..., ge=0, le=1, description="Prediction confidence")
    features: Dict[str, Any] = Field(..., description="Input features used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "predicted_consumption": 24.35,
                "model": "Random Forest",
                "confidence": 0.85,
                "features": {
                    "Temperature": 22.5,
                    "Humidity": 45.0,
                    "Occupancy": 15
                }
            }
        }


class ForecastResponse(BaseModel):
    """Response schema for time-series forecast"""
    forecast: List[float] = Field(..., description="Forecasted consumption values")
    forecast_hours: int = Field(..., description="Number of hours forecasted")
    model: str = Field(..., description="Model used for forecasting")
    
    class Config:
        json_schema_extra = {
            "example": {
                "forecast": [24.5, 26.3, 28.1, 25.7],
                "forecast_hours": 24,
                "model": "LSTM"
            }
        }
