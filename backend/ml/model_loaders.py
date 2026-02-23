"""
Model Loading Utilities
Handles loading of trained ML models into memory
"""

import os
import joblib
from pathlib import Path
from typing import Any

import tensorflow as tf
from tensorflow import keras

from backend.core.logging import get_logger
from backend.ml.model_wrappers import (
    RegressionModelWrapper,
    LSTMModelWrapper,
    AnomalyDetectorWrapper,
)

logger = get_logger(__name__)


def get_models_dir() -> Path:
    """Get the path to trained models directory"""
    # Get project root (3 levels up from this file)
    backend_dir = Path(__file__).parent.parent
    project_root = backend_dir.parent
    models_dir = project_root / "ml" / "models" / "trained"
    
    if not models_dir.exists():
        raise FileNotFoundError(f"Models directory not found: {models_dir}")
    
    return models_dir


def load_regression_model(model_name: str = "random_forest") -> RegressionModelWrapper:
    """
    Load trained regression model
    
    Args:
        model_name: Model type - 'random_forest' or 'gradient_boost'
    
    Returns:
        Wrapped regression model with predict() method
    
    Raises:
        FileNotFoundError: If model file doesn't exist
        ValueError: If model_name is invalid
    """
    models_dir = get_models_dir()
    
    if model_name == "random_forest":
        model_path = models_dir / "regression_random_forest.joblib"
    elif model_name == "gradient_boost":
        model_path = models_dir / "regression_gradient_boost.joblib"
    else:
        raise ValueError(f"Invalid model_name: {model_name}. Must be 'random_forest' or 'gradient_boost'")
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    logger.info(f"Loading regression model from {model_path}")
    model_data = joblib.load(model_path)
    logger.info(f"Regression model loaded successfully: {model_name}")
    
    # Wrap model for consistent API
    return RegressionModelWrapper(model_data)


def load_lstm_model() -> LSTMModelWrapper:
    """
    Load trained LSTM model and its scaler
    
    Returns:
        Wrapped LSTM model with forecast_future() method
    
    Raises:
        FileNotFoundError: If model or scaler file doesn't exist
    """
    models_dir = get_models_dir()
    
    model_path = models_dir / "lstm_energy_forecast.keras"
    scaler_path = models_dir / "lstm_energy_forecast_scaler.joblib"
    
    if not model_path.exists():
        raise FileNotFoundError(f"LSTM model file not found: {model_path}")
    
    if not scaler_path.exists():
        raise FileNotFoundError(f"LSTM scaler file not found: {scaler_path}")
    
    logger.info(f"Loading LSTM model from {model_path}")
    model = keras.models.load_model(model_path)
    
    logger.info(f"Loading LSTM scaler from {scaler_path}")
    scaler = joblib.load(scaler_path)
    
    logger.info("LSTM model and scaler loaded successfully")
    
    model_data = {
        "model": model,
        "scaler": scaler,
    }
    
    # Wrap model for consistent API
    return LSTMModelWrapper(model_data)


def load_anomaly_detector() -> AnomalyDetectorWrapper:
    """
    Load trained anomaly detection model
    
    Returns:
        Wrapped anomaly detector with detect() method
    
    Raises:
        FileNotFoundError: If model file doesn't exist
    """
    models_dir = get_models_dir()
    
    model_path = models_dir / "anomaly_detector.joblib"
    
    if not model_path.exists():
        raise FileNotFoundError(f"Anomaly detector file not found: {model_path}")
    
    logger.info(f"Loading anomaly detector from {model_path}")
    model_data = joblib.load(model_path)
    logger.info("Anomaly detector loaded successfully")
    
    # Wrap model for consistent API
    return AnomalyDetectorWrapper(model_data)


def validate_model_files() -> dict[str, bool]:
    """
    Validate that all required model files exist
    
    Returns:
        Dictionary mapping model names to existence status
    """
    models_dir = get_models_dir()
    
    required_files = {
        "regression_random_forest": models_dir / "regression_random_forest.joblib",
        "regression_gradient_boost": models_dir / "regression_gradient_boost.joblib",
        "lstm_model": models_dir / "lstm_energy_forecast.keras",
        "lstm_scaler": models_dir / "lstm_energy_forecast_scaler.joblib",
        "anomaly_detector": models_dir / "anomaly_detector.joblib",
    }
    
    status = {}
    for name, path in required_files.items():
        exists = path.exists()
        status[name] = exists
        if not exists:
            logger.warning(f"Model file not found: {path}")
    
    return status
