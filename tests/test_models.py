"""
Unit Tests for ML Models
"""

import pytest
import pandas as pd
import numpy as np
from ml.models.regression_model import EnergyRegressionModel
from ml.models.anomaly_detector import AnomalyDetector

def test_regression_model():
    """Test regression model initialization and basic operations"""
    model = EnergyRegressionModel(model_type='random_forest')
    assert model.model is not None
    assert model.model_type == 'random_forest'

def test_anomaly_detector():
    """Test anomaly detector initialization"""
    detector = AnomalyDetector(contamination=0.05)
    assert detector.contamination == 0.05
    assert detector.model is not None

# Add more tests as needed
