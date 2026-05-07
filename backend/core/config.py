"""
Application Configuration Management
Using Pydantic Settings for type-safe configuration with validation
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    Follows 12-Factor App methodology for configuration management.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host address")
    api_port: int = Field(default=8000, ge=1, le=65535, description="API port")
    api_version: str = Field(default="v1", description="API version prefix")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Application Metadata
    app_name: str = Field(default="EnerSight", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: str = Field(default="development", description="Environment name")
    
    # Security
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        min_length=32,
        description="Secret key for signing tokens"
    )
    jwt_secret: str = Field(
        default="dev-jwt-secret-change-in-production",
        min_length=32,
        description="JWT signing secret"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, ge=1, description="Access token expiry")
    
    # CORS Configuration
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:3001,http://localhost:5173",
        description="Comma-separated CORS origins"
    )
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    # Database - InfluxDB
    influxdb_url: str = Field(default="http://localhost:8086", description="InfluxDB URL")
    influxdb_token: str = Field(default="", description="InfluxDB authentication token")
    influxdb_org: str = Field(default="enersight", description="InfluxDB organization")
    influxdb_bucket: str = Field(default="energy_data", description="InfluxDB bucket")
    influxdb_timeout: int = Field(default=10000, ge=1000, description="InfluxDB timeout (ms)")
    
    # Database - PostgreSQL
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, ge=1, le=65535, description="PostgreSQL port")
    postgres_db: str = Field(default="enersight", description="PostgreSQL database name")
    postgres_user: str = Field(default="enersight_user", description="PostgreSQL user")
    postgres_password: str = Field(default="", description="PostgreSQL password")
    
    @property
    def postgres_url(self) -> str:
        """Construct PostgreSQL connection URL"""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    # MQTT Configuration
    mqtt_broker: str = Field(default="localhost", description="MQTT broker address")
    mqtt_port: int = Field(default=1883, ge=1, le=65535, description="MQTT port")
    mqtt_topic: str = Field(default="enersight/sensors/#", description="MQTT topic pattern")
    mqtt_username: Optional[str] = Field(default=None, description="MQTT username")
    mqtt_password: Optional[str] = Field(default=None, description="MQTT password")
    mqtt_qos: int = Field(default=1, ge=0, le=2, description="MQTT QoS level")
    mqtt_keepalive: int = Field(default=60, ge=10, description="MQTT keepalive interval")
    
    # Machine Learning Configuration
    ml_models_path: Path = Field(default=Path("ml/models/trained"), description="ML models directory")
    model_regression: str = Field(
        default="regression_random_forest.joblib",
        description="Regression model filename"
    )
    model_lstm: str = Field(
        default="lstm_energy_forecast.keras",
        description="LSTM model filename"
    )
    model_anomaly: str = Field(
        default="anomaly_detector.joblib",
        description="Anomaly detection model filename"
    )
    ml_prediction_batch_size: int = Field(default=32, ge=1, description="Batch size for predictions")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Path = Field(default=Path("logs/enersight.log"), description="Log file path")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    log_rotation: str = Field(default="1 day", description="Log rotation interval")
    log_retention: str = Field(default="30 days", description="Log retention period")
    
    # Performance & Monitoring
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    enable_profiling: bool = Field(default=False, description="Enable profiling")
    max_workers: int = Field(default=4, ge=1, description="Max worker threads")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests: int = Field(default=100, ge=1, description="Max requests per window")
    rate_limit_window: int = Field(default=60, ge=1, description="Rate limit window (seconds)")
    
    # Caching
    cache_enabled: bool = Field(default=True, description="Enable caching")
    cache_ttl: int = Field(default=300, ge=0, description="Cache TTL in seconds")
    redis_url: Optional[str] = Field(default=None, description="Redis URL for caching")
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment name"""
        allowed = {"development", "staging", "production", "testing"}
        if v.lower() not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v.lower()
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v.upper()
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses LRU cache to ensure singleton pattern.
    """
    return Settings()


# Convenience export
settings = get_settings()
