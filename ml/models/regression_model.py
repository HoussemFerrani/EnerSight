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

class EnergyRegressionModel:
    """Regression model for energy consumption prediction"""
    
    def __init__(self, model_type='random_forest'):
        """
        Initialize regression model
        
        Args:
            model_type: 'linear', 'random_forest', or 'gradient_boost'
        """
        self.model_type = model_type
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
        """Prepare features from dataframe"""
        # Store feature columns
        feature_cols = ['Temperature', 'Humidity', 'SquareFootage', 'Occupancy', 
                       'RenewableEnergy']
        
        # Add encoded categorical features
        df['HVACUsage_On'] = (df['HVACUsage'] == 'On').astype(int)
        df['LightingUsage_On'] = (df['LightingUsage'] == 'On').astype(int)
        df['Holiday_Yes'] = (df['Holiday'] == 'Yes').astype(int)
        
        # Add time-based features from Timestamp
        if 'Timestamp' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            df['Hour'] = df['Timestamp'].dt.hour
            df['DayOfWeek_Num'] = df['Timestamp'].dt.dayofweek
            df['Month'] = df['Timestamp'].dt.month
        
        feature_cols.extend(['HVACUsage_On', 'LightingUsage_On', 'Holiday_Yes', 
                            'Hour', 'DayOfWeek_Num', 'Month'])
        
        self.feature_columns = feature_cols
        return df[feature_cols]
    
    def train(self, X_train, y_train):
        """Train the model"""
        self.model.fit(X_train, y_train)
    
    def predict(self, X):
        """Make predictions"""
        return self.model.predict(X)
    
    def evaluate(self, X_test, y_test):
        """Evaluate model performance"""
        predictions = self.predict(X_test)
        
        metrics = {
            'mse': mean_squared_error(y_test, predictions),
            'rmse': np.sqrt(mean_squared_error(y_test, predictions)),
            'mae': mean_absolute_error(y_test, predictions),
            'r2': r2_score(y_test, predictions)
        }
        
        return metrics, predictions
    
    def save_model(self, filepath):
        """Save trained model"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump({
            'model': self.model,
            'feature_columns': self.feature_columns,
            'model_type': self.model_type
        }, filepath)
        print(f"Model saved to {filepath}")
    
    def load_model(self, filepath):
        """Load trained model"""
        data = joblib.load(filepath)
        self.model = data['model']
        self.feature_columns = data['feature_columns']
        self.model_type = data['model_type']
        print(f"Model loaded from {filepath}")

def train_regression_model(data_path: str, model_type='random_forest'):
    """
    Train regression model pipeline
    
    Args:
        data_path: Path to CSV dataset
        model_type: Type of regression model to use
    """
    # Load data
    df = pd.read_csv(data_path)
    
    # Initialize model
    model = EnergyRegressionModel(model_type=model_type)
    
    # Prepare features
    X = model.prepare_features(df)
    y = df['EnergyConsumption']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train model
    print(f"Training {model_type} model...")
    model.train(X_train, y_train)
    
    # Evaluate
    metrics, predictions = model.evaluate(X_test, y_test)
    
    print(f"\nModel Performance:")
    print(f"RMSE: {metrics['rmse']:.2f}")
    print(f"MAE: {metrics['mae']:.2f}")
    print(f"R²: {metrics['r2']:.4f}")
    
    # Save model
    model_path = f"ml/models/trained/regression_{model_type}.joblib"
    model.save_model(model_path)
    
    return model, metrics

if __name__ == "__main__":
    # Example usage
    data_path = "data/raw/Energy_consumption.csv"
    model, metrics = train_regression_model(data_path, model_type='random_forest')
