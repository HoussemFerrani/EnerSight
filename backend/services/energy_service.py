"""
Energy Service - Business Logic Layer
Implements business rules and orchestrates operations between repositories and ML models

Service Layer Benefits:
- Separation of concerns (business logic vs data access)
- Reusable business operations
- Easier testing with dependency injection
- Transaction management
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from backend.repositories.energy_repository import EnergyDataRepository
from backend.core.logging import get_logger
from backend.core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    DatabaseConnectionError,
    MLException,
    PredictionError,
)

logger = get_logger(__name__)


class EnergyService:
    """
    Service for energy consumption business logic
    Orchestrates data access and ML operations
    """
    
    def __init__(
        self,
        energy_repository: Optional[EnergyDataRepository] = None,
        regression_model: Any = None,
        lstm_model: Any = None,
        anomaly_detector: Any = None,
    ):
        """
        Initialize energy service with dependencies
        
        Args:
            energy_repository: Repository for energy data access (optional)
            regression_model: ML model for regression predictions
            lstm_model: LSTM model for time-series forecasting
            anomaly_detector: Model for anomaly detection
        """
        self.repository = energy_repository
        self.regression_model = regression_model
        self.lstm_model = lstm_model
        self.anomaly_detector = anomaly_detector
    
    async def record_energy_reading(
        self,
        device_id: str,
        location: str,
        temperature: float,
        humidity: float,
        occupancy: int,
        hvac_usage: float,
        lighting_usage: float,
        equipment_usage: float,
        renewable_energy: float,
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Record a new energy consumption reading
        
        Business Rules:
        - Validate input ranges
        - Calculate total consumption
        - Detect anomalies in real-time
        - Store in time-series database
        
        Args:
            device_id: Unique device identifier
            location: Physical location
            temperature: Temperature in Celsius
            humidity: Humidity percentage
            occupancy: Number of occupants
            hvac_usage: HVAC consumption in kWh
            lighting_usage: Lighting consumption in kWh
            equipment_usage: Equipment consumption in kWh
            renewable_energy: Renewable generation in kWh
            timestamp: Reading timestamp (default: now)
        
        Returns:
            Dict with recording status and calculated values
        
        Raises:
            ValidationError: If input validation fails
        """
        # Validate inputs
        self._validate_reading_inputs(
            temperature, humidity, occupancy,
            hvac_usage, lighting_usage, equipment_usage, renewable_energy
        )
        
        # Calculate total consumption
        total_consumption = hvac_usage + lighting_usage + equipment_usage
        net_consumption = total_consumption - renewable_energy
        
        # Use current time if not provided
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Prepare data for storage
        tags = {
            "device_id": device_id,
            "location": location,
        }
        
        fields = {
            "temperature": temperature,
            "humidity": humidity,
            "occupancy": occupancy,
            "hvac_usage": hvac_usage,
            "lighting_usage": lighting_usage,
            "equipment_usage": equipment_usage,
            "renewable_energy": renewable_energy,
            "total_consumption": total_consumption,
            "net_consumption": net_consumption,
        }
        
        # Store in database
        if not self.repository:
            raise DatabaseConnectionError("Postgres", {"reason": "Repository not configured"})
        
        try:
            await self.repository.write_measurement(
                measurement="energy_consumption",
                tags=tags,
                fields=fields,
                timestamp=timestamp,
            )
            
            logger.info(
                f"Recorded energy reading: device={device_id}, "
                f"consumption={total_consumption:.2f} kWh"
            )
            
            # Optional: Real-time anomaly detection
            is_anomaly = False
            if self.anomaly_detector:
                is_anomaly = self._check_anomaly({
                    **fields,
                    "total_consumption": total_consumption,
                })
            
            return {
                "success": True,
                "device_id": device_id,
                "timestamp": timestamp.isoformat(),
                "total_consumption": total_consumption,
                "net_consumption": net_consumption,
                "is_anomaly": is_anomaly,
            }
        
        except Exception as e:
            logger.error(f"Failed to record energy reading: {e}")
            raise
    
    async def get_consumption_history(
        self,
        start: datetime,
        end: datetime,
        device_id: Optional[str] = None,
        aggregation: str = "raw",
        window: str = "1h",
    ) -> List[Dict[str, Any]]:
        """
        Get historical energy consumption data
        
        Args:
            start: Start timestamp
            end: End timestamp
            device_id: Filter by device (optional)
            aggregation: Aggregation type (raw, mean, sum, max, min)
            window: Time window for aggregation (e.g., "1h", "1d")
        
        Returns:
            List of energy consumption records
        """
        if not self.repository:
            raise DatabaseConnectionError("Postgres", {"reason": "Repository not configured"})
        
        filters = {}
        if device_id:
            filters["device_id"] = device_id
        
        if aggregation == "raw":
            # Return raw data points
            data = await self.repository.query_range(
                measurement="energy_consumption",
                start=start,
                stop=end,
                filters=filters,
            )
        else:
            # Return aggregated data
            data = await self.repository.aggregate(
                measurement="energy_consumption",
                start=start,
                stop=end,
                aggregation=aggregation,
                window=window,
            )
        
        logger.info(f"Retrieved {len(data)} consumption records")
        return data
    
    async def predict_consumption(
        self,
        temperature: float,
        humidity: float,
        occupancy: int,
        hvac_usage: float,
        lighting_usage: float,
        equipment_usage: float,
        renewable_energy: float,
    ) -> Dict[str, Any]:
        """
        Predict energy consumption using ML model
        
        Args:
            Features for prediction
        
        Returns:
            Prediction result with confidence
        
        Raises:
            PredictionError: If prediction fails
            MLException: If model not loaded
        """
        if not self.regression_model:
            raise MLException("Regression model not loaded")
        
        try:
            # Prepare features
            features = {
                "Temperature": temperature,
                "Humidity": humidity,
                "Occupancy": occupancy,
                "HVACUsage": hvac_usage,
                "LightingUsage": lighting_usage,
                "EquipmentUsage": equipment_usage,
                "RenewableEnergy": renewable_energy,
            }
            
            # Make prediction
            prediction = self.regression_model.predict(features)
            
            logger.info(f"Predicted consumption: {prediction:.2f} kWh")
            
            return {
                "predicted_consumption": round(prediction, 2),
                "model": "Random Forest",
                "confidence": 0.85,  # TODO: Calculate actual confidence
                "features": features,
            }
        
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise PredictionError(f"Failed to predict consumption: {str(e)}")
    
    async def forecast_consumption(
        self,
        historical_data: List[float],
        forecast_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Forecast future energy consumption using LSTM
        
        Args:
            historical_data: Historical consumption values
            forecast_hours: Number of hours to forecast
        
        Returns:
            Forecast results
        """
        if not self.lstm_model:
            raise MLException("LSTM model not loaded")
        
        try:
            # Generate forecast
            forecast = self.lstm_model.forecast_future(
                historical_data,
                steps_ahead=forecast_hours
            )
            
            logger.info(f"Generated {forecast_hours}h forecast")
            
            return {
                "forecast": [round(val, 2) for val in forecast],
                "forecast_hours": forecast_hours,
                "model": "LSTM",
            }
        
        except Exception as e:
            logger.error(f"Forecasting failed: {e}")
            raise PredictionError(f"Failed to forecast: {str(e)}")
    
    async def detect_anomalies(
        self,
        start: datetime,
        end: datetime,
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in energy consumption
        
        Args:
            start: Start timestamp
            end: End timestamp
        
        Returns:
            List of detected anomalies with details
        """
        if not self.repository:
            raise DatabaseConnectionError("Postgres", {"reason": "Repository not configured"})
        
        if not self.anomaly_detector:
            raise MLException("Anomaly detector not loaded")
        
        # Get historical data
        data = await self.repository.query_range(
            measurement="energy_consumption",
            start=start,
            stop=end,
        )
        
        if not data:
            return []
        
        # Convert to DataFrame for anomaly detection
        import pandas as pd
        df = pd.DataFrame(data)
        
        # Run anomaly detection
        predictions, scores = self.anomaly_detector.detect(df)
        
        # Filter for anomalies only (prediction == -1)
        anomalies = []
        for idx, (pred, score) in enumerate(zip(predictions, scores)):
            if pred == -1:
                record = data[idx]
                
                # Determine severity based on anomaly score
                # Scores are typically in range [-0.5, 0.5], lower = more anomalous
                if score < -0.2:
                    severity = "high"
                elif score < -0.1:
                    severity = "medium"
                else:
                    severity = "low"
                
                anomalies.append({
                    "timestamp": record.get("timestamp", start),
                    "device_id": record.get("device_id", "unknown"),
                    "consumption": record.get("consumption", 0.0),
                    "expected_consumption": record.get("consumption", 0.0) * 0.85,  # Estimate
                    "anomaly_score": float(score),
                    "severity": severity,
                })
        
        logger.info(f"Detected {len(anomalies)} anomalies in {len(data)} records")
        
        return anomalies
    
    async def calculate_statistics(
        self,
        start: datetime,
        end: datetime,
    ) -> Dict[str, Any]:
        """
        Calculate energy consumption statistics
        
        Args:
            start: Start timestamp
            end: End timestamp
        
        Returns:
            Statistical summary
        """
        if not self.repository:
            raise DatabaseConnectionError("Postgres", {"reason": "Repository not configured"})
        
        # Get aggregated data
        daily_data = await self.repository.aggregate(
            measurement="energy_consumption",
            start=start,
            stop=end,
            aggregation="sum",
            window="1d",
        )
        
        if not daily_data:
            return {
                "total_consumption": 0,
                "average_daily": 0,
                "peak_consumption": 0,
                "days": 0,
            }
        
        # Postgres aggregate returns one row per bucket with a "value" column.
        consumptions = [d["value"] for d in daily_data if d.get("value") is not None]
        
        return {
            "total_consumption": round(sum(consumptions), 2),
            "average_daily": round(sum(consumptions) / len(consumptions), 2) if consumptions else 0,
            "peak_consumption": round(max(consumptions), 2) if consumptions else 0,
            "minimum_consumption": round(min(consumptions), 2) if consumptions else 0,
            "days": len(consumptions),
        }
    
    # ==================== Private Helper Methods ====================
    
    def _validate_reading_inputs(
        self,
        temperature: float,
        humidity: float,
        occupancy: int,
        hvac_usage: float,
        lighting_usage: float,
        equipment_usage: float,
        renewable_energy: float,
    ) -> None:
        """Validate energy reading inputs"""
        
        # Temperature validation (-50°C to 60°C)
        if not -50 <= temperature <= 60:
            raise ValidationError(
                f"Temperature {temperature}°C out of valid range (-50 to 60°C)",
                field="temperature"
            )
        
        # Humidity validation (0-100%)
        if not 0 <= humidity <= 100:
            raise ValidationError(
                f"Humidity {humidity}% out of valid range (0-100%)",
                field="humidity"
            )
        
        # Occupancy validation (non-negative)
        if occupancy < 0:
            raise ValidationError(
                f"Occupancy cannot be negative: {occupancy}",
                field="occupancy"
            )
        
        # Energy values validation (non-negative)
        for field_name, value in [
            ("hvac_usage", hvac_usage),
            ("lighting_usage", lighting_usage),
            ("equipment_usage", equipment_usage),
            ("renewable_energy", renewable_energy),
        ]:
            if value < 0:
                raise ValidationError(
                    f"{field_name} cannot be negative: {value}",
                    field=field_name
                )
    
    def _check_anomaly(self, features: Dict[str, float]) -> bool:
        """Check if reading is anomalous"""
        # TODO: Implement real-time anomaly detection
        return False
