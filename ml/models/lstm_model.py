"""
LSTM Model for Time-Series Energy Consumption Forecasting
Using TensorFlow/Keras for deep learning predictions
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import os

class EnergyLSTMModel:
    """LSTM model for time-series energy forecasting"""
    
    def __init__(self, sequence_length=24, features=1):
        """
        Initialize LSTM model
        
        Args:
            sequence_length: Number of past timesteps to use for prediction
            features: Number of features per timestep
        """
        self.sequence_length = sequence_length
        self.features = features
        self.model = None
        self.scaler = MinMaxScaler()
    
    def create_sequences(self, data, target):
        """Create sequences for LSTM training"""
        X, y = [], []
        
        for i in range(len(data) - self.sequence_length):
            X.append(data[i:i + self.sequence_length])
            y.append(target[i + self.sequence_length])
        
        return np.array(X), np.array(y)
    
    def build_model(self, units=[50, 50], dropout=0.2):
        """Build LSTM architecture"""
        self.model = Sequential()
        
        # First LSTM layer
        self.model.add(LSTM(
            units=units[0],
            return_sequences=True,
            input_shape=(self.sequence_length, self.features)
        ))
        self.model.add(Dropout(dropout))
        
        # Second LSTM layer
        self.model.add(LSTM(units=units[1], return_sequences=False))
        self.model.add(Dropout(dropout))
        
        # Output layer
        self.model.add(Dense(units=1))
        
        # Compile model
        self.model.compile(
            optimizer='adam',
            loss='mean_squared_error',
            metrics=['mae']
        )
        
        return self.model
    
    def prepare_data(self, df: pd.DataFrame):
        """Prepare data for LSTM training"""
        # Sort by timestamp
        df = df.sort_values('Timestamp')
        
        # Extract target variable
        target = df['EnergyConsumption'].values.reshape(-1, 1).astype(np.float64)
        
        # Scale data
        scaled_data = self.scaler.fit_transform(np.asarray(target))
        
        # Create sequences
        X, y = self.create_sequences(scaled_data, scaled_data)
        
        return X, y
    
    def train(self, X_train, y_train, X_val, y_val, epochs=50, batch_size=32):
        """Train LSTM model"""
        # Ensure model is built before training
        if self.model is None:
            self.build_model()
        
        assert self.model is not None, "Model failed to build"
        
        # Callbacks
        early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
        
        checkpoint_path = "ml/models/trained/lstm_checkpoint.keras"
        os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
        
        checkpoint = ModelCheckpoint(
            checkpoint_path,
            monitor='val_loss',
            save_best_only=True,
            verbose=1
        )
        
        # Train
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stop, checkpoint],
            verbose=1
        )
        
        return history
    
    def predict(self, X):
        """Make predictions"""
        assert self.model is not None, "Model must be built or loaded before making predictions"
        predictions = self.model.predict(X, verbose=0)
        # Inverse transform to get actual values
        return self.scaler.inverse_transform(predictions)
    
    def forecast_future(self, last_sequence, steps=24):
        """Forecast multiple steps into the future"""
        assert self.model is not None, "Model must be built or loaded before making forecasts"
        predictions = []
        current_sequence = last_sequence.copy()
        
        for _ in range(steps):
            # Predict next step
            pred = self.model.predict(current_sequence.reshape(1, self.sequence_length, self.features))
            predictions.append(pred[0, 0])
            
            # Update sequence
            current_sequence = np.append(current_sequence[1:], pred, axis=0)
        
        # Inverse transform
        predictions = np.array(predictions).reshape(-1, 1)
        return self.scaler.inverse_transform(predictions)
    
    def save_model(self, filepath):
        """Save trained model"""
        assert self.model is not None, "Model must be built or loaded before saving"
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.model.save(filepath)
        
        # Save scaler separately
        scaler_path = filepath.replace('.keras', '_scaler.joblib')
        import joblib
        joblib.dump(self.scaler, scaler_path)
        
        print(f"Model saved to {filepath}")
    
    def load_model(self, filepath):
        """Load trained model"""
        self.model = keras.models.load_model(filepath)
        
        # Load scaler
        scaler_path = filepath.replace('.keras', '_scaler.joblib')
        import joblib
        self.scaler = joblib.load(scaler_path)
        
        print(f"Model loaded from {filepath}")

def train_lstm_model(data_path: str, sequence_length=24):
    """
    Train LSTM model pipeline
    
    Args:
        data_path: Path to CSV dataset
        sequence_length: Number of past hours to use for prediction
    """
    # Load data
    df = pd.read_csv(data_path)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'].values)
    
    # Initialize model
    model = EnergyLSTMModel(sequence_length=sequence_length, features=1)
    
    # Prepare data
    X, y = model.prepare_data(df)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False  # Don't shuffle time series!
    )
    
    # Build model
    model.build_model(units=[64, 32], dropout=0.2)
    
    print(f"Training LSTM model with sequence length {sequence_length}...")
    print(f"Training samples: {X_train.shape[0]}, Test samples: {X_test.shape[0]}")
    
    # Train
    history = model.train(X_train, y_train, X_test, y_test, epochs=50, batch_size=32)
    
    # Evaluate
    predictions = model.predict(X_test)
    actual = model.scaler.inverse_transform(y_test)
    
    mse = np.mean((predictions - actual) ** 2)
    rmse = np.sqrt(mse)
    mae = np.mean(np.abs(predictions - actual))
    
    print(f"\nModel Performance:")
    print(f"RMSE: {rmse:.2f}")
    print(f"MAE: {mae:.2f}")
    
    # Save model
    model_path = "ml/models/trained/lstm_energy_forecast.keras"
    model.save_model(model_path)
    
    return model, history

if __name__ == "__main__":
    # Example usage
    data_path = "data/raw/Energy_consumption.csv"
    model, history = train_lstm_model(data_path, sequence_length=24)
