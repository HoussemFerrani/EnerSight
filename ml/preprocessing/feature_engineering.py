"""
Feature Engineering for Energy Consumption Prediction
Advanced feature creation and selection
"""

import pandas as pd
import numpy as np
from sklearn.feature_selection import SelectKBest, f_regression, mutual_info_regression

def create_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create interaction features between existing features"""
    df = df.copy()
    
    # Temperature-related interactions
    df['Temp_x_HVAC'] = df['Temperature'] * df['HVACUsage_On']
    df['Temp_x_Occupancy'] = df['Temperature'] * df['Occupancy']
    
    # Occupancy-related interactions
    df['Occupancy_x_HVAC'] = df['Occupancy'] * df['HVACUsage_On']
    df['Occupancy_x_Lighting'] = df['Occupancy'] * df['LightingUsage_On']
    df['Occupancy_x_SquareFt'] = df['Occupancy'] * df['SquareFootage']
    
    # Energy efficiency indicators
    df['Energy_per_Occupant'] = df['EnergyConsumption'] / (df['Occupancy'] + 1)  # +1 to avoid division by zero
    df['Energy_per_SquareFt'] = df['EnergyConsumption'] / df['SquareFootage']
    
    # HVAC and Lighting both on
    df['HVAC_and_Lighting_On'] = df['HVACUsage_On'] * df['LightingUsage_On']
    
    # Renewable energy contribution
    df['Renewable_Percentage'] = (df['RenewableEnergy'] / (df['EnergyConsumption'] + 0.1)) * 100
    
    return df

def create_weather_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create weather-related comfort and efficiency features"""
    df = df.copy()
    
    # Temperature comfort zones
    df['Temp_Comfortable'] = ((df['Temperature'] >= 20) & (df['Temperature'] <= 26)).astype(int)
    df['Temp_Hot'] = (df['Temperature'] > 26).astype(int)
    df['Temp_Cold'] = (df['Temperature'] < 20).astype(int)
    
    # Humidity comfort zones
    df['Humidity_Comfortable'] = ((df['Humidity'] >= 30) & (df['Humidity'] <= 60)).astype(int)
    df['Humidity_High'] = (df['Humidity'] > 60).astype(int)
    
    # Heat index approximation (simplified)
    df['Heat_Index'] = df['Temperature'] + (0.5 * df['Humidity'] / 100)
    
    return df

def create_occupancy_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create occupancy-related features"""
    df = df.copy()
    
    # Occupancy levels
    df['Occupancy_Low'] = (df['Occupancy'] <= 2).astype(int)
    df['Occupancy_Medium'] = ((df['Occupancy'] > 2) & (df['Occupancy'] <= 6)).astype(int)
    df['Occupancy_High'] = (df['Occupancy'] > 6).astype(int)
    
    # Empty building
    df['Building_Empty'] = (df['Occupancy'] == 0).astype(int)
    
    return df

def create_temporal_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Create features capturing temporal patterns"""
    df = df.copy()
    
    # Peak hours (typically 8AM-6PM)
    df['Peak_Hours'] = ((df['Hour'] >= 8) & (df['Hour'] <= 18)).astype(int)
    
    # Off-peak hours
    df['Off_Peak_Hours'] = ((df['Hour'] < 6) | (df['Hour'] > 22)).astype(int)
    
    # Business hours on weekdays
    df['Business_Hours'] = (df['Peak_Hours'] & ~df['IsWeekend']).astype(int)
    
    # Cyclic encoding for hour (preserves cyclical nature)
    df['Hour_Sin'] = np.sin(2 * np.pi * df['Hour'] / 24)
    df['Hour_Cos'] = np.cos(2 * np.pi * df['Hour'] / 24)
    
    # Cyclic encoding for day of week
    df['DayOfWeek_Sin'] = np.sin(2 * np.pi * df['DayOfWeek_Num'] / 7)
    df['DayOfWeek_Cos'] = np.cos(2 * np.pi * df['DayOfWeek_Num'] / 7)
    
    # Cyclic encoding for month
    df['Month_Sin'] = np.sin(2 * np.pi * df['Month'] / 12)
    df['Month_Cos'] = np.cos(2 * np.pi * df['Month'] / 12)
    
    return df

def select_best_features(X: pd.DataFrame, y: pd.Series, k: int = 20, method: str = 'f_regression'):
    """
    Select k best features using statistical tests
    
    Args:
        X: Feature dataframe
        y: Target variable
        k: Number of features to select
        method: 'f_regression' or 'mutual_info'
    
    Returns:
        Selected features dataframe and feature names
    """
    if method == 'f_regression':
        selector = SelectKBest(score_func=f_regression, k=k)
    else:
        selector = SelectKBest(score_func=mutual_info_regression, k=k)
    
    X_selected = selector.fit_transform(X, y)
    
    # Get selected feature names
    selected_features = X.columns[selector.get_support()].tolist()
    
    print(f"Selected {k} best features:")
    for i, feature in enumerate(selected_features, 1):
        print(f"{i}. {feature}")
    
    return pd.DataFrame(X_selected, columns=selected_features), selected_features

def get_feature_importance(model, feature_names: list, top_n: int = 15):
    """Get feature importance from trained model"""
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        
        feature_importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importances
        }).sort_values('importance', ascending=False)
        
        print(f"\nTop {top_n} Most Important Features:")
        print(feature_importance_df.head(top_n))
        
        return feature_importance_df
    else:
        print("Model does not have feature_importances_ attribute")
        return None
