"""
Energy Data Schemas
Pydantic models for energy-related data
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List


class EnergyReadingCreate(BaseModel):
    """Schema for creating a new energy reading"""
    device_id: str = Field(..., description="Unique device identifier")
    location: str = Field(..., description="Physical location")
    temperature: float = Field(..., ge=-50, le=60, description="Temperature in Celsius")
    humidity: float = Field(..., ge=0, le=100, description="Humidity percentage")
    occupancy: int = Field(..., ge=0, description="Number of occupants")
    hvac_usage: float = Field(..., ge=0, description="HVAC consumption in kWh")
    lighting_usage: float = Field(..., ge=0, description="Lighting consumption in kWh")
    equipment_usage: float = Field(..., ge=0, description="Equipment consumption in kWh")
    renewable_energy: float = Field(..., ge=0, description="Renewable generation in kWh")
    timestamp: Optional[datetime] = Field(default=None, description="Reading timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "sensor_001",
                "location": "Building A - Floor 2",
                "temperature": 22.5,
                "humidity": 45.0,
                "occupancy": 15,
                "hvac_usage": 12.5,
                "lighting_usage": 3.2,
                "equipment_usage": 8.7,
                "renewable_energy": 5.0,
            }
        }


class EnergyReadingResponse(BaseModel):
    """Response after recording energy reading"""
    success: bool
    device_id: str
    timestamp: str
    total_consumption: float
    net_consumption: float
    is_anomaly: bool


class EnergyReading(BaseModel):
    """Single energy consumption reading"""
    timestamp: datetime
    consumption: float = Field(..., description="Energy consumption in kWh")
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    occupancy: Optional[int] = None
    hvac_status: Optional[str] = None
    lighting_status: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2026-02-13T10:00:00",
                "consumption": 75.5,
                "temperature": 25.3,
                "humidity": 45.2,
                "occupancy": 5,
                "hvac_status": "On",
                "lighting_status": "Off"
            }
        }


class EnergyStatistics(BaseModel):
    """Energy consumption statistics"""
    total_consumption: float = Field(..., description="Total consumption in kWh")
    average_daily: float = Field(..., description="Average daily consumption")
    peak_consumption: float = Field(..., description="Peak consumption")
    minimum_consumption: float = Field(..., description="Minimum consumption")
    days: int = Field(..., description="Number of days analyzed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_consumption": 1245.80,
                "average_daily": 41.53,
                "peak_consumption": 62.30,
                "minimum_consumption": 28.40,
                "days": 30
            }
        }
