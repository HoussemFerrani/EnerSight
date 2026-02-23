"""
Pytest Configuration and Fixtures
Provides reusable test fixtures and configuration
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from backend.main import app
from backend.core.config import Settings
from backend.repositories.energy_repository import EnergyDataRepository
from backend.services.energy_service import EnergyService


# ==================== Configuration Fixtures ====================

@pytest.fixture
def test_settings() -> Settings:
    """
    Test settings configuration
    Overrides production settings for testing
    """
    return Settings(
        environment="testing",
        debug=True,
        log_level="DEBUG",
        postgres_db="enersight_test",
        influxdb_bucket="energy_data_test",
        secret_key="test-secret-key-minimum-32-chars-long",
        jwt_secret="test-jwt-secret-minimum-32-chars-long",
    )


# ==================== Database Fixtures ====================

@pytest_asyncio.fixture
async def async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create async database session for testing
    Uses in-memory SQLite for fast tests
    """
    # Create async engine with SQLite
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    
    # Create session factory
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # Create tables
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    
    # Provide session
    async with session_factory() as session:
        yield session
    
    # Cleanup
    await engine.dispose()


@pytest.fixture
def mock_influxdb_client():
    """
    Mock InfluxDB client for testing
    """
    mock_client = AsyncMock()
    mock_client.write_api.return_value = AsyncMock()
    mock_client.query_api.return_value = AsyncMock()
    return mock_client


@pytest.fixture
def energy_repository(mock_influxdb_client):
    """
    Energy repository with mocked InfluxDB
    """
    return EnergyDataRepository(
        influxdb_client=mock_influxdb_client,
        bucket="test_bucket",
        org="test_org",
    )


# ==================== Service Fixtures ====================

@pytest.fixture
def mock_regression_model():
    """
    Mock regression model for testing
    """
    model = MagicMock()
    model.predict.return_value = 1250.5
    return model


@pytest.fixture
def mock_lstm_model():
    """
    Mock LSTM model for testing
    """
    model = MagicMock()
    model.forecast_future.return_value = [1200.0, 1250.0, 1300.0]
    return model


@pytest.fixture
def mock_anomaly_detector():
    """
    Mock anomaly detector for testing
    """
    detector = MagicMock()
    detector.detect_anomalies.return_value = []
    return detector


@pytest.fixture
def energy_service(
    energy_repository,
    mock_regression_model,
    mock_lstm_model,
    mock_anomaly_detector,
):
    """
    Energy service with all dependencies mocked
    """
    return EnergyService(
        energy_repository=energy_repository,
        regression_model=mock_regression_model,
        lstm_model=mock_lstm_model,
        anomaly_detector=mock_anomaly_detector,
    )


# ==================== API Client Fixtures ====================

@pytest.fixture
def client() -> TestClient:
    """
    FastAPI test client for API testing
    """
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client():
    """
    Async test client for testing async endpoints
    """
    from httpx import AsyncClient
    
    async with AsyncClient(base_url="http://test://") as client:
        yield client


# ==================== Data Fixtures ====================

@pytest.fixture
def sample_energy_reading():
    """
    Sample energy reading data for testing
    """
    return {
        "device_id": "sensor_001",
        "location": "Lab A",
        "temperature": 22.5,
        "humidity": 45.0,
        "occupancy": 5,
        "hvac_usage": 500.0,
        "lighting_usage": 150.0,
        "equipment_usage": 600.0,
        "renewable_energy": 100.0,
        "timestamp": datetime.utcnow(),
    }


@pytest.fixture
def sample_historical_data():
    """
    Sample historical consumption data for testing
    """
    base_consumption = 1200.0
    return [
        base_consumption + (i % 24) * 50  # Simulate daily pattern
        for i in range(168)  # 1 week of hourly data
    ]


@pytest.fixture
def sample_prediction_features():
    """
    Sample features for ML prediction testing
    """
    return {
        "temperature": 23.0,
        "humidity": 50.0,
        "occupancy": 10,
        "hvac_usage": 600.0,
        "lighting_usage": 200.0,
        "equipment_usage": 700.0,
        "renewable_energy": 150.0,
    }


# ==================== Time Fixtures ====================

@pytest.fixture
def time_range():
    """
    Sample time range for testing
    """
    end = datetime.utcnow()
    start = end - timedelta(days=7)
    return {"start": start, "end": end}


# ==================== Pytest Configuration ====================

def pytest_configure(config):
    """
    Pytest configuration hook
    """
    config.addinivalue_line(
        "markers",
        "unit: Unit tests (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers",
        "integration: Integration tests (may require databases)"
    )
    config.addinivalue_line(
        "markers",
        "slow: Slow tests (ML training, large datasets)"
    )
    config.addinivalue_line(
        "markers",
        "api: API endpoint tests"
    )


@pytest.fixture(autouse=True)
def reset_singletons():
    """
    Reset singleton instances between tests
    Prevents state leakage
    """
    from backend.core.config import get_settings
    from backend.core.dependencies import (
        get_database_manager,
        get_service_container,
        get_model_registry,
    )
    
    # Clear LRU caches
    get_settings.cache_clear()
    get_database_manager.cache_clear()
    get_service_container.cache_clear()
    get_model_registry.cache_clear()
    
    yield
    
    # Cleanup after test
    get_settings.cache_clear()
    get_database_manager.cache_clear()
    get_service_container.cache_clear()
    get_model_registry.cache_clear()
