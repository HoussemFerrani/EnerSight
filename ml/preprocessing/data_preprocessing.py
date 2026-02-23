"""
Data Preprocessing Utilities
Functions for cleaning, transforming, and preparing energy data
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional

def load_energy_data(file_path: str) -> pd.DataFrame:
    """Load energy consumption dataset"""
    df = pd.read_csv(file_path)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    return df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean dataset by handling missing values and outliers"""
    df_clean = df.copy()
    
    # Handle missing values
    numeric_columns = df_clean.select_dtypes(include=[np.number]).columns
    df_clean[numeric_columns] = df_clean[numeric_columns].fillna(df_clean[numeric_columns].median())
    
    # Remove duplicate timestamps
    df_clean = df_clean.drop_duplicates(subset=['Timestamp'], keep='first')
    
    # Sort by timestamp
    df_clean = df_clean.sort_values('Timestamp').reset_index(drop=True)
    
    return df_clean

def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add time-based features for better predictions"""
    df = df.copy()
    
    df['Hour'] = df['Timestamp'].dt.hour
    df['DayOfWeek_Num'] = df['Timestamp'].dt.dayofweek
    df['Month'] = df['Timestamp'].dt.month
    df['DayOfMonth'] = df['Timestamp'].dt.day
    df['IsWeekend'] = df['DayOfWeek_Num'].isin([5, 6]).astype(int)
    
    # Time of day categories
    df['TimeOfDay'] = pd.cut(
        df['Hour'],
        bins=[0, 6, 12, 18, 24],
        labels=['Night', 'Morning', 'Afternoon', 'Evening'],
        include_lowest=True
    )
    
    return df

def add_lag_features(df: pd.DataFrame, columns: list, lags: list = [1, 2, 3, 24]) -> pd.DataFrame:
    """Add lagged features for time-series analysis"""
    df = df.copy()
    
    for col in columns:
        for lag in lags:
            df[f'{col}_lag_{lag}'] = df[col].shift(lag)
    
    # Remove rows with NaN due to lagging
    df = df.dropna()
    
    return df

def add_rolling_features(df: pd.DataFrame, columns: list, windows: list = [3, 6, 24]) -> pd.DataFrame:
    """Add rolling mean features"""
    df = df.copy()
    
    for col in columns:
        for window in windows:
            df[f'{col}_rolling_mean_{window}'] = df[col].rolling(window=window).mean()
            df[f'{col}_rolling_std_{window}'] = df[col].rolling(window=window).std()
    
    # Remove rows with NaN
    df = df.dropna()
    
    return df

def encode_categorical_features(df: pd.DataFrame) -> pd.DataFrame:
    """Encode categorical features"""
    df = df.copy()
    
    # Binary encoding for On/Off features
    df['HVACUsage_On'] = (df['HVACUsage'] == 'On').astype(int)
    df['LightingUsage_On'] = (df['LightingUsage'] == 'On').astype(int)
    df['Holiday_Yes'] = (df['Holiday'] == 'Yes').astype(int)
    
    # One-hot encoding for DayOfWeek
    df = pd.get_dummies(df, columns=['DayOfWeek'], prefix='Day')
    
    return df

def detect_outliers_iqr(df: pd.DataFrame, column: str, threshold: float = 1.5) -> pd.Series:
    """Detect outliers using IQR method"""
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    
    lower_bound = Q1 - threshold * IQR
    upper_bound = Q3 + threshold * IQR
    
    is_outlier = (df[column] < lower_bound) | (df[column] > upper_bound)
    
    return is_outlier

def normalize_data(df: pd.DataFrame, columns: list, method: str = 'minmax') -> tuple:
    """
    Normalize numerical columns
    
    Args:
        df: Input dataframe
        columns: Columns to normalize
        method: 'minmax' or 'standard'
    
    Returns:
        Normalized dataframe and scaler object
    """
    from sklearn.preprocessing import MinMaxScaler, StandardScaler
    
    df_normalized = df.copy()
    
    if method == 'minmax':
        scaler = MinMaxScaler()
    else:
        scaler = StandardScaler()
    
    df_normalized[columns] = scaler.fit_transform(df[columns])
    
    return df_normalized, scaler

def save_processed_data(df: pd.DataFrame, output_path: str):
    """Save processed data to CSV"""
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Processed data saved to {output_path}")

def get_data_summary(df: pd.DataFrame) -> dict:
    """Get summary statistics of the dataset"""
    summary = {
        'total_records': len(df),
        'date_range': {
            'start': df['Timestamp'].min(),
            'end': df['Timestamp'].max()
        },
        'energy_stats': {
            'mean': df['EnergyConsumption'].mean(),
            'median': df['EnergyConsumption'].median(),
            'min': df['EnergyConsumption'].min(),
            'max': df['EnergyConsumption'].max(),
            'std': df['EnergyConsumption'].std()
        },
        'missing_values': df.isnull().sum().to_dict()
    }
    
    return summary
