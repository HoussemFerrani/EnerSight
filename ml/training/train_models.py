"""
Main Training Script
Train all ML models (Regression, LSTM, Anomaly Detection)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.models.regression_model import train_regression_model
from ml.models.lstm_model import train_lstm_model
from ml.models.anomaly_detector import train_anomaly_detector
from ml.preprocessing.data_preprocessing import load_energy_data, clean_data, save_processed_data
import argparse

def main():
    """Main training pipeline"""
    parser = argparse.ArgumentParser(description='Train EnerSight ML Models')
    parser.add_argument('--data', type=str, default='data/raw/Energy_consumption.csv',
                       help='Path to energy consumption dataset')
    parser.add_argument('--models', type=str, nargs='+', 
                       default=['regression', 'lstm', 'anomaly'],
                       choices=['regression', 'lstm', 'anomaly', 'all'],
                       help='Models to train')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("EnerSight - ML Model Training Pipeline")
    print("=" * 60)
    
    # Load and clean data
    print("\n[1/4] Loading and cleaning data...")
    df = load_energy_data(args.data)
    df_clean = clean_data(df)
    
    print(f"✓ Loaded {len(df_clean)} records")
    print(f"  Date range: {df_clean['Timestamp'].min()} to {df_clean['Timestamp'].max()}")
    
    # Save cleaned data
    save_processed_data(df_clean, 'data/processed/energy_data_cleaned.csv')
    
    models_to_train = args.models
    if 'all' in models_to_train:
        models_to_train = ['regression', 'lstm', 'anomaly']
    
    # Train Regression Models
    if 'regression' in models_to_train:
        print("\n[2/4] Training Regression Models...")
        print("-" * 60)
        
        for model_type in ['random_forest', 'gradient_boost']:
            print(f"\nTraining {model_type}...")
            model, metrics = train_regression_model(
                'data/processed/energy_data_cleaned.csv',
                model_type=model_type
            )
            print(f"✓ {model_type} trained successfully")
    
    # Train LSTM Model
    if 'lstm' in models_to_train:
        print("\n[3/4] Training LSTM Model...")
        print("-" * 60)
        model, history = train_lstm_model(
            'data/processed/energy_data_cleaned.csv',
            sequence_length=24
        )
        print("✓ LSTM model trained successfully")
    
    # Train Anomaly Detector
    if 'anomaly' in models_to_train:
        print("\n[4/4] Training Anomaly Detector...")
        print("-" * 60)
        detector, anomalies = train_anomaly_detector(
            'data/processed/energy_data_cleaned.csv'
        )
        print("✓ Anomaly detector trained successfully")
    
    print("\n" + "=" * 60)
    print("✓ All models trained successfully!")
    print("=" * 60)
    print("\nTrained models saved in: ml/models/trained/")
    print("\nNext steps:")
    print("1. Test models using test_models.py")
    print("2. Deploy models to backend API")
    print("3. Start the FastAPI server")

if __name__ == "__main__":
    main()
