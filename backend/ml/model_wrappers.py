"""
Model Wrapper Classes for Backend
Provides consistent interface for loaded ML models
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Union

from backend.core.logging import get_logger

logger = get_logger(__name__)


class RegressionModelWrapper:
    """
    Wrapper for loaded regression model
    Provides predict() method that accepts feature dict
    """
    
    def __init__(self, loaded_model_data: Dict[str, Any]):
        """
        Initialize wrapper with loaded model data
        
        Args:
            loaded_model_data: Dictionary containing 'model', 'feature_columns', 'model_type'
        """
        self.model = loaded_model_data['model']
        self.feature_columns = loaded_model_data['feature_columns']
        self.model_type = loaded_model_data['model_type']
        logger.info(f"Initialized {self.model_type} regression model wrapper")
    
    def predict(self, features: Dict[str, float]) -> float:
        """
        Predict energy consumption from features dictionary
        
        Args:
            features: Dictionary with keys:
                - Temperature
                - Humidity
                - Occupancy
                - HVACUsage
                - LightingUsage
                - EquipmentUsage
                - RenewableEnergy
        
        Returns:
            Predicted consumption value
        """
        # Create feature vector in correct order
        feature_values = []
        
        # Base features (from self.feature_columns)
        feature_mapping = {
            'Temperature': features.get('Temperature', 22.0),
            'Humidity': features.get('Humidity', 50.0),
            'SquareFootage': 1000.0,  # Default value
            'Occupancy': features.get('Occupancy', 10),
            'RenewableEnergy': features.get('RenewableEnergy', 0.0),
        }
        
        # Encoded categorical features
        hvac_on = 1 if features.get('HVACUsage', 0.0) > 0 else 0
        lighting_on = 1 if features.get('LightingUsage', 0.0) > 0 else 0
        
        # Build feature array matching training columns
        for col in self.feature_columns:
            if col == 'HVACUsage_On':
                feature_values.append(hvac_on)
            elif col == 'LightingUsage_On':
                feature_values.append(lighting_on)
            elif col in feature_mapping:
                feature_values.append(feature_mapping[col])
            else:
                # Time features or others - use defaults
                feature_values.append(0)
        
        # Convert to numpy array and reshape for prediction
        X = np.array(feature_values).reshape(1, -1)
        
        # Make prediction
        prediction = self.model.predict(X)[0]
        
        logger.debug(f"Predicted consumption: {prediction:.2f} kWh")
        return float(prediction)


class LSTMModelWrapper:
    """
    Wrapper for loaded LSTM model
    Provides forecast_future() method
    """
    
    def __init__(self, loaded_model_data: Dict[str, Any]):
        """
        Initialize wrapper with loaded LSTM model and scaler
        
        Args:
            loaded_model_data: Dictionary containing 'model' and 'scaler'
        """
        self.model = loaded_model_data['model']
        self.scaler = loaded_model_data['scaler']
        self.sequence_length = 24  # Default from training
        logger.info("Initialized LSTM model wrapper")
    
    def forecast_future(
        self, 
        historical_data: Union[List[float], np.ndarray],
        steps_ahead: int = 24
    ) -> List[float]:
        """
        Forecast future energy consumption
        
        Args:
            historical_data: Historical consumption values (at least sequence_length values)
            steps_ahead: Number of future timesteps to predict
        
        Returns:
            List of forecasted values
        """
        # Ensure we have enough historical data
        if len(historical_data) < self.sequence_length:
            raise ValueError(
                f"Need at least {self.sequence_length} historical values, got {len(historical_data)}"
            )
        
        # Take last sequence_length values
        recent_data = np.array(historical_data[-self.sequence_length:])
        
        # Scale the data
        recent_data_scaled = self.scaler.transform(recent_data.reshape(-1, 1))
        
        # Prepare for prediction
        current_sequence = recent_data_scaled[-self.sequence_length:].reshape(1, self.sequence_length, 1)
        
        forecast = []
        
        # Generate forecast iteratively
        for _ in range(steps_ahead):
            # Predict next value
            next_value_scaled = self.model.predict(current_sequence, verbose=0)[0, 0]
            
            # Inverse transform to get actual value
            next_value = self.scaler.inverse_transform([[next_value_scaled]])[0, 0]
            forecast.append(float(next_value))
            
            # Update sequence for next prediction
            next_value_scaled_reshaped = np.array([[[next_value_scaled]]])
            current_sequence = np.concatenate([
                current_sequence[:, 1:, :],
                next_value_scaled_reshaped
            ], axis=1)
        
        logger.debug(f"Generated forecast for {steps_ahead} steps")
        return forecast


class LSTMTFLiteWrapper:
    """
    Drop-in replacement for `LSTMModelWrapper` that runs inference through
    `tf.lite.Interpreter` instead of full Keras.

    Why: the .tflite flatbuffer is ~8x smaller than the .keras directory and
    can run on edge devices (Raspberry Pi, ESP32-class boards, smart-meter
    gateways) under the standalone `tflite_runtime` package — no full
    TensorFlow needed. The dashboard and prediction API don't change; this
    class exposes the same `forecast_future()` signature so swapping is a
    no-op for callers.
    """

    def __init__(self, loaded_model_data: Dict[str, Any]):
        import tensorflow as tf  # local import: TF is a heavy dependency

        tflite_path = loaded_model_data["tflite_path"]
        self.scaler = loaded_model_data["scaler"]
        self.sequence_length = 24  # must match the Keras training config

        # An interpreter is cheap to keep alive; tensor buffers are allocated
        # once and reused across invocations.
        self.interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
        self.interpreter.allocate_tensors()
        self._input_idx = self.interpreter.get_input_details()[0]["index"]
        self._output_idx = self.interpreter.get_output_details()[0]["index"]

        logger.info(f"Initialized LSTM TFLite wrapper from {tflite_path}")

    def _predict_one(self, sequence: np.ndarray) -> float:
        """Run one forward pass through the TFLite interpreter."""
        x = sequence.reshape(1, self.sequence_length, 1).astype(np.float32)
        self.interpreter.set_tensor(self._input_idx, x)
        self.interpreter.invoke()
        return float(self.interpreter.get_tensor(self._output_idx)[0, 0])

    def forecast_future(
        self,
        historical_data: Union[List[float], np.ndarray],
        steps_ahead: int = 24,
    ) -> List[float]:
        """Same contract as `LSTMModelWrapper.forecast_future`."""
        if len(historical_data) < self.sequence_length:
            raise ValueError(
                f"Need at least {self.sequence_length} historical values, "
                f"got {len(historical_data)}"
            )

        recent = np.asarray(historical_data[-self.sequence_length:], dtype=np.float64)
        scaled = self.scaler.transform(recent.reshape(-1, 1))
        current_sequence = scaled[-self.sequence_length:].reshape(self.sequence_length, 1)

        forecast: List[float] = []
        for _ in range(steps_ahead):
            next_scaled = self._predict_one(current_sequence)
            next_value = float(self.scaler.inverse_transform([[next_scaled]])[0, 0])
            forecast.append(next_value)
            current_sequence = np.concatenate(
                [current_sequence[1:], np.array([[next_scaled]], dtype=np.float64)],
                axis=0,
            )

        logger.debug(f"Generated TFLite forecast for {steps_ahead} steps")
        return forecast


class LSTMMultivariateWrapper:
    """
    Wrapper for the concurrent multivariate LSTM (sequence regressor).

    Unlike `LSTMModelWrapper` (which forecasts the future from past consumption
    and is meaningless on this temporally-random dataset), this model estimates
    consumption from the *current* conditions — the same question `/predict`
    answers with Random Forest, so it exposes the same `predict(features)`
    signature and uses identical input conventions for a fair comparison.
    """

    def __init__(self, loaded_model_data: Dict[str, Any]):
        # `model` is an EnergyMultivariateLSTMModel already loaded with weights
        # and scalers.
        self.model = loaded_model_data["model"]
        self.feature_columns = self.model.feature_columns
        logger.info("Initialized multivariate LSTM wrapper")

    def predict(self, features: Dict[str, float]) -> float:
        """Estimate consumption from a conditions dict.

        Accepts the same feature dict as `RegressionModelWrapper.predict` and
        applies the same defaults (SquareFootage=1000, time/holiday features
        absent -> 0) so RF and LSTM are directly comparable on /predict.
        """
        feature_row = {
            "Temperature": features.get("Temperature", 22.0),
            "Humidity": features.get("Humidity", 50.0),
            "SquareFootage": 1000.0,
            "Occupancy": features.get("Occupancy", 10),
            "RenewableEnergy": features.get("RenewableEnergy", 0.0),
            "HVACUsage_On": 1 if features.get("HVACUsage", 0.0) > 0 else 0,
            "LightingUsage_On": 1 if features.get("LightingUsage", 0.0) > 0 else 0,
            "Holiday_Yes": 0,
            "Hour": 0,
            "DayOfWeek_Num": 0,
        }
        prediction = self.model.predict_point(feature_row)
        logger.debug(f"Multivariate LSTM predicted: {prediction:.2f} kWh")
        return float(prediction)


class AnomalyDetectorWrapper:
    """
    Wrapper for loaded anomaly detector
    Provides detect() method
    """
    
    def __init__(self, loaded_model_data: Dict[str, Any]):
        """
        Initialize wrapper with loaded anomaly detector
        
        Args:
            loaded_model_data: Dictionary containing 'model', 'scaler', 'feature_columns'
        """
        self.model = loaded_model_data['model']
        self.scaler = loaded_model_data['scaler']
        self.feature_columns = loaded_model_data['feature_columns']
        self.contamination = loaded_model_data.get('contamination', 0.05)
        logger.info("Initialized anomaly detector wrapper")
    
    def detect(self, data: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        """
        Detect anomalies in data
        
        Args:
            data: DataFrame with energy consumption data
        
        Returns:
            Tuple of (predictions, scores)
            - predictions: 1 for normal, -1 for anomaly
            - scores: Anomaly scores (lower = more anomalous)
        """
        # Prepare features
        X = self._prepare_features(data)
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        # Detect anomalies
        predictions = self.model.predict(X_scaled)
        scores = self.model.score_samples(X_scaled)
        
        anomaly_count = np.sum(predictions == -1)
        logger.debug(f"Detected {anomaly_count} anomalies in {len(data)} records")
        
        return predictions, scores
    
    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for anomaly detection"""
        features = df.copy()
        
        # Encode categorical features if present
        if 'HVACUsage' in features.columns:
            features['HVACUsage_On'] = (features['HVACUsage'] == 'On').astype(int)
        elif 'HVACUsage_On' not in features.columns:
            # If not present, assume default
            features['HVACUsage_On'] = 0
        
        if 'LightingUsage' in features.columns:
            features['LightingUsage_On'] = (features['LightingUsage'] == 'On').astype(int)
        elif 'LightingUsage_On' not in features.columns:
            features['LightingUsage_On'] = 0
        
        # Add time features if Timestamp present
        if 'Timestamp' in features.columns:
            features['Timestamp'] = pd.to_datetime(features['Timestamp'])
            features['Hour'] = features['Timestamp'].dt.hour
        elif 'Hour' not in features.columns:
            features['Hour'] = 12  # Default noon
        
        # Select only the feature columns used during training
        available_cols = [col for col in self.feature_columns if col in features.columns]
        
        # Add missing columns with defaults
        for col in self.feature_columns:
            if col not in features.columns:
                if col == 'Hour':
                    features[col] = 12
                elif col in ['HVACUsage_On', 'LightingUsage_On']:
                    features[col] = 0
                elif col == 'EnergyConsumption':
                    features[col] = 0
                else:
                    features[col] = 0
        
        return features[self.feature_columns]
