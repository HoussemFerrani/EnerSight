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
import pandas as pd
from sklearn.model_selection import train_test_split

from ml.models.regression_model import EnergyRegressionModel

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
    """Re-score the saved multivariate LSTM estimator on its hold-out split.

    This is the genuinely-trained LSTM (concurrent estimator, R² ≈ 0.59). The
    old univariate forecaster is intentionally NOT scored here: it collapses to
    the mean on this temporally-random data (R² ≈ -0.05) and its MAPE-based
    "accuracy" was misleading.
    """
    from ml.models.lstm_multivariate import EnergyMultivariateLSTMModel

    model = EnergyMultivariateLSTMModel()
    model.load(
        f"{TRAINED_DIR}/lstm_energy_multivariate.keras",
        f"{TRAINED_DIR}/lstm_multivariate_bundle.joblib",
    )

    df = pd.read_csv(CLEANED_DATA)
    _, X_test, _, y_test = model.prepare_and_split(df, test_size=0.2)
    m = model.evaluate(X_test, y_test)

    return {
        "task": "estimation",
        "algorithm": "Multivariate LSTM",
        "sequence_length": model.sequence_length,
        "rmse": m["rmse"],
        "mae": m["mae"],
        "r2": m["r2"],
        "mape": m["mape"],
        "accuracy_pct": m["accuracy_pct"],
        "note": "Concurrent estimator (conditions->consumption), not a forecaster: the dataset has ~zero autocorrelation so true forecasting is impossible.",
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

    print("Scoring multivariate LSTM estimator on its hold-out split...")
    payload["models"]["lstm_multivariate"] = _lstm_block()

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
