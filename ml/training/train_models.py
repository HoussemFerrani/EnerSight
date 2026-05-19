"""
Main Training Script
Train all ML models (Regression, LSTM, Anomaly Detection) and persist
evaluation metrics to ml/models/trained/metrics.json so they can be surfaced
in the dashboard.
"""

import sys
import os
import json
from datetime import datetime, timezone
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.models.regression_model import train_regression_model
from ml.models.lstm_model import train_lstm_model
from ml.models.anomaly_detector import train_anomaly_detector
from ml.preprocessing.data_preprocessing import load_energy_data, clean_data, save_processed_data
import argparse

METRICS_PATH = "ml/models/trained/metrics.json"


def _coerce_metric(value):
    """JSON-safe numeric coercion (numpy floats are not JSON-serializable by default)."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def write_metrics(payload: dict):
    """Write metrics.json atomically-ish — overwrite each run with the latest."""
    os.makedirs(os.path.dirname(METRICS_PATH), exist_ok=True)
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"\n✓ Metrics written to {METRICS_PATH}")


def main():
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

    print("\n[1/4] Loading and cleaning data...")
    df = load_energy_data(args.data)
    df_clean = clean_data(df)

    print(f"✓ Loaded {len(df_clean)} records")
    print(f"  Date range: {df_clean['Timestamp'].min()} to {df_clean['Timestamp'].max()}")

    save_processed_data(df_clean, 'data/processed/energy_data_cleaned.csv')

    models_to_train = args.models
    if 'all' in models_to_train:
        models_to_train = ['regression', 'lstm', 'anomaly']

    metrics_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "path": args.data,
            "records": int(len(df_clean)),
            "date_range": {
                "start": str(df_clean['Timestamp'].min()),
                "end": str(df_clean['Timestamp'].max()),
            },
        },
        "models": {},
    }

    if 'regression' in models_to_train:
        print("\n[2/4] Training Regression Models...")
        print("-" * 60)

        for model_type in ['random_forest', 'gradient_boost']:
            # Baseline (no lag features) — powers the /predict endpoint.
            print(f"\nTraining {model_type} (baseline)...")
            _, baseline_metrics = train_regression_model(
                'data/processed/energy_data_cleaned.csv',
                model_type=model_type,
                include_lag_features=False,
            )
            metrics_payload["models"][f"regression_{model_type}_baseline"] = {
                "task": "regression",
                "algorithm": model_type,
                "variant": "baseline",
                "uses_lag_features": False,
                "rmse": _coerce_metric(baseline_metrics["rmse"]),
                "mae": _coerce_metric(baseline_metrics["mae"]),
                "r2": _coerce_metric(baseline_metrics["r2"]),
                "mape": _coerce_metric(baseline_metrics["mape"]),
                "accuracy_pct": _coerce_metric(baseline_metrics["accuracy_pct"]),
            }

            # With lag features — held-out time-based split, benchmark only.
            print(f"\nTraining {model_type} (with lag features)...")
            _, lagged_metrics = train_regression_model(
                'data/processed/energy_data_cleaned.csv',
                model_type=model_type,
                include_lag_features=True,
            )
            metrics_payload["models"][f"regression_{model_type}_lagged"] = {
                "task": "regression",
                "algorithm": model_type,
                "variant": "lagged",
                "uses_lag_features": True,
                "rmse": _coerce_metric(lagged_metrics["rmse"]),
                "mae": _coerce_metric(lagged_metrics["mae"]),
                "r2": _coerce_metric(lagged_metrics["r2"]),
                "mape": _coerce_metric(lagged_metrics["mape"]),
                "accuracy_pct": _coerce_metric(lagged_metrics["accuracy_pct"]),
            }

    if 'lstm' in models_to_train:
        print("\n[3/4] Training LSTM Model...")
        print("-" * 60)
        import numpy as np
        import pandas as pd
        from sklearn.model_selection import train_test_split

        model, history = train_lstm_model(
            'data/processed/energy_data_cleaned.csv',
            sequence_length=24
        )

        # Recompute test metrics on the original scale so MAPE makes sense.
        lstm_df = pd.read_csv('data/processed/energy_data_cleaned.csv')
        lstm_df['Timestamp'] = pd.to_datetime(lstm_df['Timestamp'])
        X_all, y_all = model.prepare_data(lstm_df)
        _, X_test, _, y_test = train_test_split(X_all, y_all, test_size=0.2, shuffle=False)

        preds_scaled = model.model.predict(X_test, verbose=0)
        preds = model.scaler.inverse_transform(preds_scaled).ravel()
        actuals = model.scaler.inverse_transform(y_test.reshape(-1, 1)).ravel()

        rmse_lstm = float(np.sqrt(np.mean((preds - actuals) ** 2)))
        mae_lstm = float(np.mean(np.abs(preds - actuals)))
        mask = np.abs(actuals) > 1e-6
        mape_lstm = float(np.mean(np.abs((actuals[mask] - preds[mask]) / actuals[mask])) * 100) if mask.any() else float('nan')

        metrics_payload["models"]["lstm_forecast"] = {
            "task": "forecast",
            "algorithm": "LSTM",
            "sequence_length": 24,
            "rmse": rmse_lstm,
            "mae": mae_lstm,
            "mape": mape_lstm,
            "accuracy_pct": max(0.0, 100.0 - mape_lstm),
            "epochs_trained": len(history.history.get("val_loss", [])),
        }
        print("✓ LSTM model trained successfully")

    if 'anomaly' in models_to_train:
        print("\n[4/4] Training Anomaly Detector...")
        print("-" * 60)
        detector, anomalies = train_anomaly_detector(
            'data/processed/energy_data_cleaned.csv'
        )
        # Now that we tune contamination against rule-based pseudo-labels AND
        # support a hybrid (rules OR IF) detection path, we can report real
        # numbers. The hybrid block is what the production system should use.
        from ml.models.anomaly_detector import compute_rule_based_labels
        import pandas as pd
        an_df = pd.read_csv('data/processed/energy_data_cleaned.csv')
        flags = detector.detect_hybrid(an_df)
        truth = compute_rule_based_labels(an_df)
        total = int(len(an_df))

        def _f1_block(detected):
            from sklearn.metrics import f1_score as _f1, precision_score as _p, recall_score as _r
            return {
                "precision": float(_p(truth, detected, zero_division=0)),
                "recall": float(_r(truth, detected, zero_division=0)),
                "f1": float(_f1(truth, detected, zero_division=0)),
                "flagged_count": int(detected.sum()),
                "flag_rate": float(detected.sum() / total),
            }

        metrics_payload["models"]["anomaly_detector"] = {
            "task": "anomaly_detection",
            "algorithm": "IsolationForest (+ rules hybrid)",
            "contamination": float(detector.contamination),
            "n_estimators": int(detector.n_estimators),
            "total_records": total,
            "ground_truth_positive": int(truth.sum()),
            "if_only": _f1_block(flags["if_flagged"]),
            "hybrid": _f1_block(flags["hybrid"]),
            "novel_findings": {
                "count": int(flags["novel_flagged"].sum()),
                "flag_rate": float(flags["novel_flagged"].sum() / total),
            },
            "note": "Pseudo-labels from business rules. Hybrid is the production output.",
        }
        print(f"  IF-only F1: {metrics_payload['models']['anomaly_detector']['if_only']['f1']:.3f}")
        print(f"  Hybrid F1:  {metrics_payload['models']['anomaly_detector']['hybrid']['f1']:.3f}")
        print(f"  Novel findings: {metrics_payload['models']['anomaly_detector']['novel_findings']['count']}")
        print("✓ Anomaly detector trained successfully")

    write_metrics(metrics_payload)

    print("\n" + "=" * 60)
    print("✓ All models trained successfully!")
    print("=" * 60)
    print("\nTrained models saved in: ml/models/trained/")
    print(f"Metrics saved in: {METRICS_PATH}")

if __name__ == "__main__":
    main()
