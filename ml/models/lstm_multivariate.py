"""
Multivariate (concurrent) LSTM for energy consumption.

Why this model exists
---------------------
The original univariate LSTM (`lstm_model.py`) forecasts future consumption
from past consumption alone. On this dataset that is hopeless: consumption — and
every driver — has ~zero hour-to-hour autocorrelation (verified: Temperature
lag-1 ≈ -0.02, consumption lag-1 ≈ 0.00). A univariate forecaster therefore
collapses to predicting the mean (R² ≈ -0.05, i.e. worse than the mean).

The signal here is *concurrent*, not temporal: consumption is driven by the
conditions at the same timestep (Temperature corr +0.70, Occupancy, HVAC...).
So this model is a **sequence regressor**: it consumes a window of the exogenous
feature vectors that ENDS at the target timestep and predicts that timestep's
consumption. It is a genuine multivariate LSTM and reaches the data's real
ceiling (R² ≈ 0.5, in line with the Random Forest) — an honest number, not the
MAPE-flattered 91.8% the univariate model reported.

It is an *estimator* ("nowcast from current conditions"), not a *forecaster*:
true forecasting is impossible on a temporally-random dataset.
"""

import os

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.models import Sequential

# Same drivers the Random Forest uses, so the two models are comparable.
FEATURE_COLUMNS = [
    "Temperature", "Humidity", "SquareFootage", "Occupancy", "RenewableEnergy",
    "HVACUsage_On", "LightingUsage_On", "Holiday_Yes", "Hour", "DayOfWeek_Num",
]


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive the model's feature columns from a raw/cleaned dataframe."""
    df = df.copy()
    df["HVACUsage_On"] = (df["HVACUsage"] == "On").astype(int)
    df["LightingUsage_On"] = (df["LightingUsage"] == "On").astype(int)
    df["Holiday_Yes"] = (df["Holiday"] == "Yes").astype(int)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df = df.sort_values("Timestamp").reset_index(drop=True)
    df["Hour"] = df["Timestamp"].dt.hour
    df["DayOfWeek_Num"] = df["Timestamp"].dt.dayofweek
    return df


class EnergyMultivariateLSTMModel:
    """Concurrent multivariate LSTM (sequence-of-features -> consumption[t])."""

    def __init__(self, sequence_length: int = 24):
        self.sequence_length = sequence_length
        self.feature_columns = list(FEATURE_COLUMNS)
        self.feature_scaler = StandardScaler()
        self.target_scaler = MinMaxScaler()
        self.model = None

    # ---- data prep -------------------------------------------------------
    def _windows(self, feats_scaled: np.ndarray, target_scaled: np.ndarray):
        """Causal windows ending at (and including) each target row."""
        L = self.sequence_length
        X, y = [], []
        for i in range(L - 1, len(feats_scaled)):
            X.append(feats_scaled[i - L + 1: i + 1])
            y.append(target_scaled[i])
        return np.array(X), np.array(y)

    def prepare_and_split(self, df: pd.DataFrame, test_size: float = 0.2):
        """Engineer, scale (fit on train rows only), window, chronological split."""
        df = engineer_features(df)
        feats = df[self.feature_columns].values.astype(np.float64)
        target = df["EnergyConsumption"].values.reshape(-1, 1).astype(np.float64)

        n = len(df)
        split = int(n * (1 - test_size))
        # Fit scalers on the train rows only — no test leakage.
        self.feature_scaler.fit(feats[:split])
        self.target_scaler.fit(target[:split])
        feats_s = self.feature_scaler.transform(feats)
        target_s = self.target_scaler.transform(target)

        X, y = self._windows(feats_s, target_s)
        # Window k targets row (k + L - 1); it is a train sample iff that row
        # falls in the train range.
        end_rows = np.arange(self.sequence_length - 1, n)
        train_mask = end_rows < split
        return X[train_mask], X[~train_mask], y[train_mask], y[~train_mask]

    # ---- model -----------------------------------------------------------
    def build_model(self, units=(64, 32), dropout=0.2):
        n_features = len(self.feature_columns)
        model = Sequential()
        model.add(LSTM(units[0], return_sequences=True,
                       input_shape=(self.sequence_length, n_features)))
        model.add(Dropout(dropout))
        model.add(LSTM(units[1], return_sequences=False))
        model.add(Dropout(dropout))
        model.add(Dense(1))
        model.compile(optimizer="adam", loss="mean_squared_error", metrics=["mae"])
        self.model = model
        return model

    def train(self, X_train, y_train, X_val, y_val, epochs=80, batch_size=32, verbose=0):
        if self.model is None:
            self.build_model()
        early = EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)
        return self.model.fit(
            X_train, y_train, validation_data=(X_val, y_val),
            epochs=epochs, batch_size=batch_size, callbacks=[early], verbose=verbose,
        )

    def evaluate(self, X_test, y_test) -> dict:
        preds = self.target_scaler.inverse_transform(self.model.predict(X_test, verbose=0)).ravel()
        actual = self.target_scaler.inverse_transform(y_test.reshape(-1, 1)).ravel()
        mask = np.abs(actual) > 1e-6
        mape = float(np.mean(np.abs((actual[mask] - preds[mask]) / actual[mask])) * 100) if mask.any() else float("nan")
        return {
            "rmse": float(np.sqrt(mean_squared_error(actual, preds))),
            "mae": float(mean_absolute_error(actual, preds)),
            "r2": float(r2_score(actual, preds)),
            "mape": mape,
            "accuracy_pct": max(0.0, 100.0 - mape),
        }

    # ---- inference -------------------------------------------------------
    def predict_point(self, feature_row: dict) -> float:
        """Estimate consumption from a single conditions vector.

        The data has no temporal structure, so the window is filled by tiling
        the current conditions across all timesteps — the model keys off the
        (final) concurrent step regardless.
        """
        vec = np.array([[float(feature_row.get(c, 0.0)) for c in self.feature_columns]], dtype=np.float64)
        vec_s = self.feature_scaler.transform(vec)
        window = np.tile(vec_s, (self.sequence_length, 1)).reshape(1, self.sequence_length, len(self.feature_columns))
        pred_s = self.model.predict(window, verbose=0)
        return float(self.target_scaler.inverse_transform(pred_s)[0, 0])

    # ---- persistence -----------------------------------------------------
    def save(self, keras_path: str, bundle_path: str):
        os.makedirs(os.path.dirname(keras_path), exist_ok=True)
        self.model.save(keras_path)
        joblib.dump({
            "feature_scaler": self.feature_scaler,
            "target_scaler": self.target_scaler,
            "feature_columns": self.feature_columns,
            "sequence_length": self.sequence_length,
        }, bundle_path)

    def load(self, keras_path: str, bundle_path: str):
        from tensorflow import keras
        self.model = keras.models.load_model(keras_path)
        bundle = joblib.load(bundle_path)
        self.feature_scaler = bundle["feature_scaler"]
        self.target_scaler = bundle["target_scaler"]
        self.feature_columns = bundle["feature_columns"]
        self.sequence_length = bundle["sequence_length"]
        return self
