"""
Anomaly Detection for Energy Consumption
Detect unusual patterns and inefficient device behavior
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib

class AnomalyDetector:
    """Anomaly detection for energy consumption patterns"""
    
    def __init__(self, contamination=0.05):
        """
        Initialize anomaly detector
        
        Args:
            contamination: Expected proportion of anomalies in dataset
        """
        self.contamination = contamination
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.feature_columns = None
    
    def prepare_features(self, df: pd.DataFrame):
        """Prepare features for anomaly detection"""
        features = df.copy()
        
        # Encode categorical features
        features['HVACUsage_On'] = (features['HVACUsage'] == 'On').astype(int)
        features['LightingUsage_On'] = (features['LightingUsage'] == 'On').astype(int)
        
        # Select relevant features
        feature_cols = ['EnergyConsumption', 'Temperature', 'Humidity', 
                       'Occupancy', 'HVACUsage_On', 'LightingUsage_On']
        
        # Add time-based features
        if 'Timestamp' in features.columns:
            features['Timestamp'] = pd.to_datetime(features['Timestamp'])
            features['Hour'] = features['Timestamp'].dt.hour
            feature_cols.append('Hour')
        
        self.feature_columns = feature_cols
        return features[feature_cols]
    
    def train(self, X):
        """Train anomaly detection model"""
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Fit model
        self.model.fit(X_scaled)
    
    def detect_anomalies(self, X):
        """
        Detect anomalies in data
        
        Returns:
            Array of predictions: 1 for normal, -1 for anomaly
        """
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        
        # Also get anomaly scores
        scores = self.model.score_samples(X_scaled)
        
        return predictions, scores
    
    def find_anomalies_with_context(self, df: pd.DataFrame):
        """
        Find anomalies and provide context
        
        Returns:
            DataFrame with anomalies and their details
        """
        X = self.prepare_features(df)
        predictions, scores = self.detect_anomalies(X)
        
        # Add predictions to dataframe
        result_df = df.copy()
        result_df['is_anomaly'] = predictions == -1
        result_df['anomaly_score'] = scores
        
        # Filter to anomalies only
        anomalies = result_df[result_df['is_anomaly']].copy()
        
        # Add context
        anomalies['reason'] = anomalies.apply(self._determine_anomaly_reason, axis=1)
        
        return anomalies
    
    def _determine_anomaly_reason(self, row):
        """Determine why a data point is considered anomalous"""
        reasons = []
        
        # High consumption with HVAC and Lighting off
        if row['EnergyConsumption'] > 85 and row['HVACUsage'] == 'Off' and row['LightingUsage'] == 'Off':
            reasons.append("High consumption without HVAC/Lighting")
        
        # Low occupancy but high consumption
        if row['Occupancy'] < 2 and row['EnergyConsumption'] > 80:
            reasons.append("High consumption with low occupancy")
        
        # Holiday with high consumption
        if row['Holiday'] == 'Yes' and row['EnergyConsumption'] > 85:
            reasons.append("High consumption on holiday")
        
        # Extreme temperature but normal consumption (inefficiency)
        if (row['Temperature'] < 22 or row['Temperature'] > 28) and row['HVACUsage'] == 'On':
            if row['EnergyConsumption'] < 70:
                reasons.append("Inefficient HVAC operation")
        
        return "; ".join(reasons) if reasons else "Statistical outlier"
    
    def save_model(self, filepath):
        """Save trained model"""
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'contamination': self.contamination
        }, filepath)
        print(f"Anomaly detector saved to {filepath}")
    
    def load_model(self, filepath):
        """Load trained model"""
        data = joblib.load(filepath)
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_columns = data['feature_columns']
        self.contamination = data['contamination']
        print(f"Anomaly detector loaded from {filepath}")

def train_anomaly_detector(data_path: str):
    """
    Train anomaly detection model
    
    Args:
        data_path: Path to CSV dataset
    """
    # Load data
    df = pd.read_csv(data_path)
    
    # Initialize detector
    detector = AnomalyDetector(contamination=0.05)
    
    # Prepare features
    X = detector.prepare_features(df)
    
    # Train
    print("Training anomaly detector...")
    detector.train(X)
    
    # Find anomalies in training data
    anomalies = detector.find_anomalies_with_context(df)
    
    print(f"\nFound {len(anomalies)} anomalies in training data")
    print(f"Percentage of anomalies: {len(anomalies)/len(df)*100:.2f}%")
    
    if len(anomalies) > 0:
        print("\nSample anomalies:")
        print(anomalies[['Timestamp', 'EnergyConsumption', 'Occupancy', 
                        'HVACUsage', 'LightingUsage', 'reason']].head())
    
    # Save model
    model_path = "ml/models/trained/anomaly_detector.joblib"
    detector.save_model(model_path)
    
    return detector, anomalies

if __name__ == "__main__":
    # Example usage
    data_path = "data/raw/Energy_consumption.csv"
    detector, anomalies = train_anomaly_detector(data_path)
