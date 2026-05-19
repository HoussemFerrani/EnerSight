"""
Regression Model for Energy Consumption Prediction
Using Scikit-learn for baseline predictions
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import os
from typing import Union

# Lag windows in hours. 1 = previous hour, 24 = same hour yesterday,
# 168 = same hour last week — captures the dominant cycles in hourly energy data.
LAG_HOURS = [1, 24, 168]
ROLLING_WINDOWS = [24]  # daily rolling mean to smooth short-term noise

class EnergyRegressionModel:
    """Regression model for energy consumption prediction"""

    def __init__(self, model_type='random_forest', include_lag_features: bool = False):
        """
        Initialize regression model

        Args:
            model_type: 'linear', 'random_forest', or 'gradient_boost'
            include_lag_features: When True, prepare_features adds lag/rolling
                features over EnergyConsumption. Requires a Timestamp column and
                drops rows with insufficient history.
        """
        self.model_type = model_type
        self.include_lag_features = include_lag_features
        self.model: LinearRegression | RandomForestRegressor | GradientBoostingRegressor = None
        self.feature_columns = None

        if model_type == 'linear':
            self.model = LinearRegression()
        elif model_type == 'random_forest':
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        elif model_type == 'gradient_boost':
            self.model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        else:
            raise ValueError(f"Invalid model_type: {model_type}. Must be 'linear', 'random_forest', or 'gradient_boost'")

    def prepare_features(self, df: pd.DataFrame):
        """Prepare features from dataframe. Returns (X, y) tuple."""
        feature_cols = ['Temperature', 'Humidity', 'SquareFootage', 'Occupancy',
                       'RenewableEnergy']

        df['HVACUsage_On'] = (df['HVACUsage'] == 'On').astype(int)
        df['LightingUsage_On'] = (df['LightingUsage'] == 'On').astype(int)
        df['Holiday_Yes'] = (df['Holiday'] == 'Yes').astype(int)

        if 'Timestamp' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            df['Hour'] = df['Timestamp'].dt.hour
            df['DayOfWeek_Num'] = df['Timestamp'].dt.dayofweek
            df['Month'] = df['Timestamp'].dt.month

        feature_cols.extend(['HVACUsage_On', 'LightingUsage_On', 'Holiday_Yes',
                            'Hour', 'DayOfWeek_Num', 'Month'])

        if self.include_lag_features:
            if 'Timestamp' not in df.columns:
                raise ValueError("Lag features require a 'Timestamp' column")
            df = df.sort_values('Timestamp').reset_index(drop=True)
            for lag in LAG_HOURS:
                col = f'EnergyConsumption_lag_{lag}'
                df[col] = df['EnergyConsumption'].shift(lag)
                feature_cols.append(col)
            for window in ROLLING_WINDOWS:
                col = f'EnergyConsumption_rolling_{window}'
                # Shift by 1 before rolling so the window only sees past values —
                # otherwise the current row leaks into its own predictor.
                df[col] = df['EnergyConsumption'].shift(1).rolling(window=window).mean()
                feature_cols.append(col)
            df = df.dropna(subset=feature_cols).reset_index(drop=True)

        self.feature_columns = feature_cols
        X = df[feature_cols]
        y = df['EnergyConsumption']
        return X, y

    def train(self, X_train, y_train):
        """Train the model"""
        self.model.fit(X_train, y_train)

    def predict(self, X):
        """Make predictions"""
        return self.model.predict(X)

    def evaluate(self, X_test, y_test):
        """Evaluate model performance"""
        predictions = self.predict(X_test)

        # MAPE — skip rows where actual is ~0 to avoid divide-by-zero blow-ups.
        actual = np.asarray(y_test, dtype=np.float64)
        pred = np.asarray(predictions, dtype=np.float64)
        mask = np.abs(actual) > 1e-6
        mape = float(np.mean(np.abs((actual[mask] - pred[mask]) / actual[mask])) * 100) if mask.any() else float('nan')

        metrics = {
            'mse': mean_squared_error(y_test, predictions),
            'rmse': np.sqrt(mean_squared_error(y_test, predictions)),
            'mae': mean_absolute_error(y_test, predictions),
            'r2': r2_score(y_test, predictions),
            'mape': mape,
            'accuracy_pct': max(0.0, 100.0 - mape),  # clamp at 0 so a bad model doesn't show negative
        }

        return metrics, predictions

    def save_model(self, filepath):
        """Save trained model"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump({
            'model': self.model,
            'feature_columns': self.feature_columns,
            'model_type': self.model_type,
            'include_lag_features': self.include_lag_features,
        }, filepath)
        print(f"Model saved to {filepath}")

    def load_model(self, filepath):
        """Load trained model"""
        data = joblib.load(filepath)
        self.model = data['model']
        self.feature_columns = data['feature_columns']
        self.model_type = data['model_type']
        self.include_lag_features = data.get('include_lag_features', False)
        print(f"Model loaded from {filepath}")

def train_regression_model(data_path: str, model_type='random_forest',
                           include_lag_features: bool = False,
                           output_filename: str | None = None):
    """
    Train regression model pipeline

    Args:
        data_path: Path to CSV dataset
        model_type: Type of regression model to use
        include_lag_features: If True, train with lag/rolling features and use
            a time-based train/test split (no shuffle) to avoid leakage.
        output_filename: Override the saved model filename (without directory).
    """
    df = pd.read_csv(data_path)

    model = EnergyRegressionModel(model_type=model_type, include_lag_features=include_lag_features)
    X, y = model.prepare_features(df)

    # Time-aware split for lagged models — random shuffle would leak future
    # information through the lag columns.
    shuffle = not include_lag_features
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=shuffle
    )

    variant = "with lags" if include_lag_features else "baseline"
    print(f"Training {model_type} ({variant})...")
    model.train(X_train, y_train)

    metrics, predictions = model.evaluate(X_test, y_test)

    print(f"\nModel Performance ({model_type}, {variant}):")
    print(f"RMSE: {metrics['rmse']:.2f}")
    print(f"MAE: {metrics['mae']:.2f}")
    print(f"R²: {metrics['r2']:.4f}")

    if output_filename is None:
        suffix = "_lagged" if include_lag_features else ""
        output_filename = f"regression_{model_type}{suffix}.joblib"
    model_path = f"ml/models/trained/{output_filename}"
    model.save_model(model_path)

    return model, metrics

if __name__ == "__main__":
    data_path = "data/raw/Energy_consumption.csv"
    model, metrics = train_regression_model(data_path, model_type='random_forest')
