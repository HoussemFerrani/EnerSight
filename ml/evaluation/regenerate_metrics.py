"""
Regenerate ml/models/trained/metrics.json from the ALREADY-TRAINED artifacts —
no retraining.

Why this exists
---------------
`ml.training.train_models` computes the per-model training metrics *while it
trains* and overwrites metrics.json each run. Running it with a subset
(e.g. `--models anomaly`) therefore wipes the regression/LSTM entries. This
script rebuilds a complete metrics.json by loading the persisted models and
re-scoring them on the exact same deterministic hold-out split the training
pipeline used, so the dashboard "Model accuracy" card is populated again
without changing any model artifact.

Faithfulness
------------
- Regression: the split is `train_test_split(..., test_size=0.2,
  random_state=42, shuffle=<baseline>)`, identical to
  `regression_model.train_regression_model`. The saved estimator was fit on
  the train half of that very split, so scoring it on the test half reproduces
  the training-time RMSE/MAE/R²/MAPE/accuracy exactly.
- LSTM: mirrors the test-metric block in `train_models` (chronological 20%
  tail, inverse-transformed to kWh) using the saved `.keras` + scaler.
- Anomaly: preserved verbatim from the existing metrics.json (it is produced
  by the real hybrid pipeline and matches the saved detector).

Usage
-----
    .\\venv\\Scripts\\python.exe -m ml.evaluation.regenerate_metrics
"""

import json
import os
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from ml.models.regression_model import EnergyRegressionModel
from ml.models.lstm_model import EnergyLSTMModel

TRAINED_DIR = "ml/models/trained"
METRICS_PATH = f"{TRAINED_DIR}/metrics.json"
CLEANED_DATA = "data/processed/energy_data_cleaned.csv"
RAW_DATA = "data/raw/Energy_consumption.csv"


def _regression_block(model_type: str, include_lag_features: bool) -> dict:
    """Re-score a saved regression estimator on its original hold-out split."""
    suffix = "_lagged" if include_lag_features else ""
    path = f"{TRAINED_DIR}/regression_{model_type}{suffix}.joblib"

    model = EnergyRegressionModel(model_type=model_type,
                                  include_lag_features=include_lag_features)
    df = pd.read_csv(CLEANED_DATA)
    X, y = model.prepare_features(df)

    shuffle = not include_lag_features
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=shuffle
    )

    saved = joblib.load(path)
    model.model = saved["model"]
    model.feature_columns = saved["feature_columns"]
    # Align column order with what the estimator was fitted on.
    X_test = X_test[saved["feature_columns"]]

    metrics, _ = model.evaluate(X_test, y_test)
    return {
        "task": "regression",
        "algorithm": model_type,
        "variant": "lagged" if include_lag_features else "baseline",
        "uses_lag_features": include_lag_features,
        "rmse": float(metrics["rmse"]),
        "mae": float(metrics["mae"]),
        "r2": float(metrics["r2"]),
        "mape": float(metrics["mape"]),
        "accuracy_pct": float(metrics["accuracy_pct"]),
    }


def _lstm_block() -> dict:
    """Re-score the saved LSTM on the chronological 20% tail, in kWh."""
    model = EnergyLSTMModel(sequence_length=24, features=1)
    model.load_model(f"{TRAINED_DIR}/lstm_energy_forecast.keras")

    df = pd.read_csv(CLEANED_DATA)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    # prepare_data re-fits a MinMaxScaler on the same target column — idempotent
    # on identical data, so the scaling matches training.
    X_all, y_all = model.prepare_data(df)
    _, X_test, _, y_test = train_test_split(X_all, y_all, test_size=0.2, shuffle=False)

    preds_scaled = model.model.predict(X_test, verbose=0)
    preds = model.scaler.inverse_transform(preds_scaled).ravel()
    actuals = model.scaler.inverse_transform(y_test.reshape(-1, 1)).ravel()

    rmse = float(np.sqrt(np.mean((preds - actuals) ** 2)))
    mae = float(np.mean(np.abs(preds - actuals)))
    mask = np.abs(actuals) > 1e-6
    mape = float(np.mean(np.abs((actuals[mask] - preds[mask]) / actuals[mask])) * 100) if mask.any() else float("nan")

    return {
        "task": "forecast",
        "algorithm": "LSTM",
        "sequence_length": 24,
        "rmse": rmse,
        "mae": mae,
        "mape": mape,
        "accuracy_pct": max(0.0, 100.0 - mape),
    }


def _preserved_anomaly_block() -> dict | None:
    """Carry the existing anomaly block forward unchanged, if present."""
    if not os.path.exists(METRICS_PATH):
        return None
    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        existing = json.load(f)
    return existing.get("models", {}).get("anomaly_detector")


def main() -> None:
    df_clean = pd.read_csv(CLEANED_DATA)
    df_clean["Timestamp"] = pd.to_datetime(df_clean["Timestamp"])

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "path": RAW_DATA,
            "records": int(len(df_clean)),
            "date_range": {
                "start": str(df_clean["Timestamp"].min()),
                "end": str(df_clean["Timestamp"].max()),
            },
        },
        "models": {},
        "note": "Regenerated from saved artifacts via ml.evaluation.regenerate_metrics (no retraining).",
    }

    print("Scoring regression models on their hold-out splits...")
    for model_type in ["random_forest", "gradient_boost"]:
        payload["models"][f"regression_{model_type}_baseline"] = _regression_block(model_type, False)
        payload["models"][f"regression_{model_type}_lagged"] = _regression_block(model_type, True)

    print("Scoring LSTM on the chronological tail...")
    payload["models"]["lstm_forecast"] = _lstm_block()

    anomaly = _preserved_anomaly_block()
    if anomaly is not None:
        payload["models"]["anomaly_detector"] = anomaly
        print("Preserved existing anomaly_detector block.")
    else:
        print("No existing anomaly block to preserve — run train_models --models anomaly.")

    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)

    print(f"\n[OK] Wrote {len(payload['models'])} model entries to {METRICS_PATH}")
    for name, m in payload["models"].items():
        acc = m.get("accuracy_pct")
        acc_s = f"{acc:.1f}%" if isinstance(acc, (int, float)) else "n/a"
        print(f"  - {name:36} accuracy={acc_s}")


if __name__ == "__main__":
    main()
