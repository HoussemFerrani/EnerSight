"""
Unit Tests for Energy Service
Tests business logic in isolation using mocks
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.energy_service import EnergyService
from backend.core.exceptions import ValidationError, MLException, PredictionError


@pytest.mark.unit
class TestEnergyService:
    """Test suite for EnergyService business logic"""
    
    @pytest.mark.asyncio
    async def test_record_energy_reading_success(
        self,
        energy_service,
        sample_energy_reading,
    ):
        """Test successful energy reading recording"""
        # Arrange
        energy_service.repository.write_measurement = AsyncMock()
        
        # Act
        result = await energy_service.record_energy_reading(
            **sample_energy_reading
        )
        
        # Assert
        assert result["success"] is True
        assert result["device_id"] == sample_energy_reading["device_id"]
        assert "total_consumption" in result
        assert result["total_consumption"] == 1250.0  # 500 + 150 + 600
        assert result["net_consumption"] == 1150.0  # 1250 - 100
        
        # Verify repository was called
        energy_service.repository.write_measurement.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_record_energy_reading_validates_temperature(
        self,
        energy_service,
        sample_energy_reading,
    ):
        """Test temperature validation"""
        # Arrange - Invalid temperature
        sample_energy_reading["temperature"] = 100.0  # Too high
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await energy_service.record_energy_reading(
                **sample_energy_reading
            )
        
        assert "temperature" in str(exc_info.value).lower()
        assert exc_info.value.details["field"] == "temperature"
    
    @pytest.mark.asyncio
    async def test_record_energy_reading_validates_humidity(
        self,
        energy_service,
        sample_energy_reading,
    ):
        """Test humidity validation"""
        # Arrange - Invalid humidity
        sample_energy_reading["humidity"] = 150.0  # Too high
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await energy_service.record_energy_reading(
                **sample_energy_reading
            )
        
        assert "humidity" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_record_energy_reading_validates_negative_values(
        self,
        energy_service,
        sample_energy_reading,
    ):
        """Test that energy values cannot be negative"""
        # Arrange
        sample_energy_reading["hvac_usage"] = -100.0
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await energy_service.record_energy_reading(
                **sample_energy_reading
            )
        
        assert "negative" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_get_consumption_history_raw(
        self,
        energy_service,
        time_range,
    ):
        """Test retrieving raw consumption history"""
        # Arrange
        mock_data = [
            {"time": datetime.utcnow(), "field": "total_consumption", "value": 1200.0},
            {"time": datetime.utcnow(), "field": "total_consumption", "value": 1250.0},
        ]
        energy_service.repository.query_range = AsyncMock(return_value=mock_data)
        
        # Act
        result = await energy_service.get_consumption_history(
            start=time_range["start"],
            end=time_range["end"],
            aggregation="raw",
        )
        
        # Assert
        assert len(result) == 2
        assert result == mock_data
        energy_service.repository.query_range.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_consumption_history_aggregated(
        self,
        energy_service,
        time_range,
    ):
        """Test retrieving aggregated consumption history"""
        # Arrange
        mock_data = [
            {"time": datetime.utcnow(), "value": 1200.0, "aggregation": "mean"},
        ]
        energy_service.repository.aggregate = AsyncMock(return_value=mock_data)
        
        # Act
        result = await energy_service.get_consumption_history(
            start=time_range["start"],
            end=time_range["end"],
            aggregation="mean",
            window="1h",
        )
        
        # Assert
        assert len(result) == 1
        energy_service.repository.aggregate.assert_called_once_with(
            measurement="energy_consumption",
            start=time_range["start"],
            stop=time_range["end"],
            aggregation="mean",
            window="1h",
        )
    
    @pytest.mark.asyncio
    async def test_predict_consumption_success(
        self,
        energy_service,
        sample_prediction_features,
    ):
        """Test successful consumption prediction"""
        # Arrange
        expected_prediction = 1250.5
        energy_service.regression_model.predict.return_value = expected_prediction
        
        # Act
        result = await energy_service.predict_consumption(
            **sample_prediction_features
        )
        
        # Assert
        assert result["predicted_consumption"] == expected_prediction
        assert result["model"] == "Random Forest"
        assert "confidence" in result
        assert "features" in result
        energy_service.regression_model.predict.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_predict_consumption_no_model_loaded(
        self,
        energy_service,
        sample_prediction_features,
    ):
        """Test prediction fails when model not loaded"""
        # Arrange
        energy_service.regression_model = None
        
        # Act & Assert
        with pytest.raises(MLException) as exc_info:
            await energy_service.predict_consumption(
                **sample_prediction_features
            )
        
        assert "not loaded" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_predict_consumption_model_error(
        self,
        energy_service,
        sample_prediction_features,
    ):
        """Test prediction handles model errors gracefully"""
        # Arrange
        energy_service.regression_model.predict.side_effect = Exception("Model error")
        
        # Act & Assert
        with pytest.raises(PredictionError) as exc_info:
            await energy_service.predict_consumption(
                **sample_prediction_features
            )
        
        assert "failed" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_forecast_consumption_success(
        self,
        energy_service,
        sample_historical_data,
    ):
        """Test successful time-series forecasting"""
        # Arrange
        forecast_hours = 24
        expected_forecast = [1200.0, 1250.0, 1300.0]
        energy_service.lstm_model.forecast_future.return_value = expected_forecast
        
        # Act
        result = await energy_service.forecast_consumption(
            historical_data=sample_historical_data,
            forecast_hours=forecast_hours,
        )
        
        # Assert
        assert result["forecast_hours"] == forecast_hours
        assert len(result["forecast"]) == len(expected_forecast)
        assert result["model"] == "LSTM"
        energy_service.lstm_model.forecast_future.assert_called_once_with(
            sample_historical_data,
            steps_ahead=forecast_hours
        )
    
    @pytest.mark.asyncio
    async def test_forecast_consumption_no_model(
        self,
        energy_service,
        sample_historical_data,
    ):
        """Test forecasting fails when LSTM not loaded"""
        # Arrange
        energy_service.lstm_model = None
        
        # Act & Assert
        with pytest.raises(MLException):
            await energy_service.forecast_consumption(
                historical_data=sample_historical_data,
                forecast_hours=24,
            )
    
    @pytest.mark.asyncio
    async def test_calculate_statistics_success(
        self,
        energy_service,
        time_range,
    ):
        """Test statistics calculation"""
        # Arrange
        mock_data = [
            {"field": "total_consumption", "value": 1000.0},
            {"field": "total_consumption", "value": 1200.0},
            {"field": "total_consumption", "value": 1400.0},
        ]
        energy_service.repository.aggregate = AsyncMock(return_value=mock_data)
        
        # Act
        result = await energy_service.calculate_statistics(
            start=time_range["start"],
            end=time_range["end"],
        )
        
        # Assert
        assert result["total_consumption"] == 3600.0  # Sum
        assert result["average_daily"] == 1200.0  # Average
        assert result["peak_consumption"] == 1400.0  # Max
        assert result["minimum_consumption"] == 1000.0  # Min
        assert result["days"] == 3
    
    @pytest.mark.asyncio
    async def test_calculate_statistics_no_data(
        self,
        energy_service,
        time_range,
    ):
        """Test statistics with no data"""
        # Arrange
        energy_service.repository.aggregate = AsyncMock(return_value=[])
        
        # Act
        result = await energy_service.calculate_statistics(
            start=time_range["start"],
            end=time_range["end"],
        )
        
        # Assert - Should return zeros
        assert result["total_consumption"] == 0
        assert result["average_daily"] == 0
        assert result["peak_consumption"] == 0
        assert result["days"] == 0
    
    def test_validate_reading_inputs_valid(self, energy_service):
        """Test input validation with valid data"""
        # Should not raise exception
        energy_service._validate_reading_inputs(
            temperature=22.5,
            humidity=45.0,
            occupancy=5,
            hvac_usage=500.0,
            lighting_usage=150.0,
            equipment_usage=600.0,
            renewable_energy=100.0,
        )
    
    def test_validate_reading_inputs_boundary_values(self, energy_service):
        """Test input validation at boundary values"""
        # Temperature boundaries
        energy_service._validate_reading_inputs(
            temperature=-50.0,  # Min
            humidity=0.0,  # Min
            occupancy=0,
            hvac_usage=0.0,
            lighting_usage=0.0,
            equipment_usage=0.0,
            renewable_energy=0.0,
        )
        
        energy_service._validate_reading_inputs(
            temperature=60.0,  # Max
            humidity=100.0,  # Max
            occupancy=1000,
            hvac_usage=10000.0,
            lighting_usage=5000.0,
            equipment_usage=15000.0,
            renewable_energy=8000.0,
        )


@pytest.mark.unit
class TestEnergyServiceEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.mark.asyncio
    async def test_record_reading_with_zero_values(
        self,
        energy_service,
        sample_energy_reading,
    ):
        """Test recording with all zero energy values"""
        # Arrange
        sample_energy_reading.update({
            "hvac_usage": 0.0,
            "lighting_usage": 0.0,
            "equipment_usage": 0.0,
            "renewable_energy": 0.0,
        })
        energy_service.repository.write_measurement = AsyncMock()
        
        # Act
        result = await energy_service.record_energy_reading(
            **sample_energy_reading
        )
        
        # Assert
        assert result["success"] is True
        assert result["total_consumption"] == 0.0
        assert result["net_consumption"] == 0.0
    
    @pytest.mark.asyncio
    async def test_record_reading_renewable_exceeds_consumption(
        self,
        energy_service,
        sample_energy_reading,
    ):
        """Test when renewable energy exceeds consumption (net negative)"""
        # Arrange
        sample_energy_reading["renewable_energy"] = 2000.0  # Exceeds total
        energy_service.repository.write_measurement = AsyncMock()
        
        # Act
        result = await energy_service.record_energy_reading(
            **sample_energy_reading
        )
        
        # Assert - Net consumption can be negative (exporting energy)
        assert result["success"] is True
        assert result["net_consumption"] < 0
