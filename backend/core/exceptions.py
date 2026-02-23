"""
Custom Exception Classes
Domain-specific exceptions for better error handling and debugging
"""

from typing import Any, Optional


class EnerSightException(Exception):
    """Base exception for all EnerSight errors"""

    def __init__(
        self,
        message: str,
        code: str = "ENERSIGHT_ERROR",
        details: Optional[dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


# ==================== API Exceptions ====================

class APIException(EnerSightException):
    """Base exception for API-related errors"""
    pass


class ValidationError(APIException):
    """Data validation failed"""

    def __init__(self, message: str, field: Optional[str] = None, details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={"field": field, **(details or {})}
        )


class AuthenticationError(APIException):
    """Authentication failed"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, code="AUTHENTICATION_ERROR")


class AuthorizationError(APIException):
    """Authorization/permission denied"""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message=message, code="AUTHORIZATION_ERROR")


class ResourceNotFoundError(APIException):
    """Requested resource not found"""

    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} not found",
            code="RESOURCE_NOT_FOUND",
            details={"resource": resource, "identifier": str(identifier)}
        )


class ResourceAlreadyExistsError(APIException):
    """Resource already exists (conflict)"""

    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} already exists",
            code="RESOURCE_ALREADY_EXISTS",
            details={"resource": resource, "identifier": str(identifier)}
        )


class RateLimitExceededError(APIException):
    """Rate limit exceeded"""

    def __init__(self, retry_after: Optional[int] = None):
        super().__init__(
            message="Rate limit exceeded",
            code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after}
        )


# ==================== Database Exceptions ====================

class DatabaseException(EnerSightException):
    """Base exception for database errors"""
    pass


class DatabaseConnectionError(DatabaseException):
    """Database connection failed"""

    def __init__(self, db_type: str, details: Optional[dict] = None):
        super().__init__(
            message=f"Failed to connect to {db_type}",
            code="DB_CONNECTION_ERROR",
            details={"database_type": db_type, **(details or {})}
        )


class DatabaseQueryError(DatabaseException):
    """Database query failed"""

    def __init__(self, message: str, query: Optional[str] = None):
        super().__init__(
            message=message,
            code="DB_QUERY_ERROR",
            details={"query": query}
        )


class DatabaseIntegrityError(DatabaseException):
    """Database integrity constraint violated"""

    def __init__(self, message: str, constraint: Optional[str] = None):
        super().__init__(
            message=message,
            code="DB_INTEGRITY_ERROR",
            details={"constraint": constraint}
        )


# ==================== ML Exceptions ====================

class MLException(EnerSightException):
    """Base exception for ML-related errors"""
    pass


class ModelNotFoundError(MLException):
    """ML model file not found"""

    def __init__(self, model_name: str, path: Optional[str] = None):
        super().__init__(
            message=f"Model '{model_name}' not found",
            code="MODEL_NOT_FOUND",
            details={"model_name": model_name, "path": path}
        )


class ModelLoadError(MLException):
    """Failed to load ML model"""

    def __init__(self, model_name: str, reason: str):
        super().__init__(
            message=f"Failed to load model '{model_name}': {reason}",
            code="MODEL_LOAD_ERROR",
            details={"model_name": model_name, "reason": reason}
        )


class PredictionError(MLException):
    """Prediction failed"""

    def __init__(self, message: str, model_name: Optional[str] = None):
        super().__init__(
            message=message,
            code="PREDICTION_ERROR",
            details={"model_name": model_name}
        )


class ModelTrainingError(MLException):
    """Model training failed"""

    def __init__(self, message: str, model_type: Optional[str] = None):
        super().__init__(
            message=message,
            code="MODEL_TRAINING_ERROR",
            details={"model_type": model_type}
        )


class InvalidFeatureError(MLException):
    """Invalid features provided for prediction"""

    def __init__(self, message: str, missing_features: Optional[list[str]] = None):
        super().__init__(
            message=message,
            code="INVALID_FEATURE_ERROR",
            details={"missing_features": missing_features}
        )


# ==================== IoT/MQTT Exceptions ====================

class IoTException(EnerSightException):
    """Base exception for IoT-related errors"""
    pass


class MQTTConnectionError(IoTException):
    """MQTT broker connection failed"""

    def __init__(self, broker: str, port: int, reason: Optional[str] = None):
        super().__init__(
            message=f"Failed to connect to MQTT broker {broker}:{port}",
            code="MQTT_CONNECTION_ERROR",
            details={"broker": broker, "port": port, "reason": reason}
        )


class MQTTPublishError(IoTException):
    """Failed to publish MQTT message"""

    def __init__(self, topic: str, reason: Optional[str] = None):
        super().__init__(
            message=f"Failed to publish to topic '{topic}'",
            code="MQTT_PUBLISH_ERROR",
            details={"topic": topic, "reason": reason}
        )


class SensorDataError(IoTException):
    """Invalid sensor data received"""

    def __init__(self, message: str, sensor_id: Optional[str] = None):
        super().__init__(
            message=message,
            code="SENSOR_DATA_ERROR",
            details={"sensor_id": sensor_id}
        )


# ==================== Data Processing Exceptions ====================

class DataProcessingException(EnerSightException):
    """Base exception for data processing errors"""
    pass


class DataValidationError(DataProcessingException):
    """Data validation failed"""

    def __init__(self, message: str, data_type: Optional[str] = None):
        super().__init__(
            message=message,
            code="DATA_VALIDATION_ERROR",
            details={"data_type": data_type}
        )


class DataTransformationError(DataProcessingException):
    """Data transformation failed"""

    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(
            message=message,
            code="DATA_TRANSFORMATION_ERROR",
            details={"operation": operation}
        )


# ==================== Configuration Exceptions ====================

class ConfigurationError(EnerSightException):
    """Configuration error"""

    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            details={"config_key": config_key}
        )


class MissingConfigurationError(ConfigurationError):
    """Required configuration missing"""

    def __init__(self, config_key: str):
        super().__init__(
            message=f"Required configuration '{config_key}' is missing",
            config_key=config_key
        )
