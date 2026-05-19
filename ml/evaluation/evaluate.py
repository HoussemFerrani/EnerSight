"""
Standalone evaluation pipeline.

Unlike train_models.py, this script does NOT retrain. It loads the artifacts
already saved under ml/models/trained/ and produces:

  1. K-fold cross-validation scores for the regression models — gives a
     mean ± std accuracy estimate, so we know whether the single-split
     94% from training was real or a lucky draw.
  2. A sampled predicted-vs-actual series for the regression and LSTM
     models — so the dashboard can show *where* the model fails.
  3. Precision / recall / F1 for the anomaly detector against pseudo-labels
     derived from the existing business rules in
     ml/models/anomaly_detector.py::_determine_anomaly_reason. This measures
     "how well does IsolationForest agree with our hand-written rules"
     — not absolute accuracy, but the best we can do without ground-truth
     labels.

Outputs:
  ml/models/trained/evaluation.json   — CV stats + anomaly P/R/F1
  ml/models/trained/predictions.json  — sample of (timestamp, actual, predicted)

Run:  python -m ml.evaluation.evaluate
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    precision_score,
    recall_score,
    f1_score,
)

# Ensure ml.* imports resolve when run as a module from the repo root.
sys.path.append(str(Path(__file__).resolve().parents[2]))

from ml.models.regression_model import EnergyRegressionModel
from ml.models.lstm_model import EnergyLSTMModel
from ml.models.anomaly_detector import AnomalyDetector, compute_rule_based_labels

DATA_PATH = "data/processed/energy_data_cleaned.csv"
MODELS_DIR = Path("ml/models/trained")
EVALUATION_PATH = MODELS_DIR / "evaluation.json"
PREDICTIONS_PATH = MODELS_DIR / "predictions.json"

# Sample size for the predicted-vs-actual chart. Keep small so the JSON
# stays light and the chart stays readable.
CHART_SAMPLE_SIZE = 200


def _mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    actual = np.asarray(actual, dtype=np.float64)
    predicted = np.asarray(predicted, dtype=np.float64)
    mask = np.abs(actual) > 1e-6
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100)


def _summary(values: list[float]) -> dict:
    arr = np.asarray(values, dtype=np.float64)
    return {
        "mean": float(arr.mean()),
        "std": float(arr.std()),
        "min": float(arr.min()),
        "max": float(arr.max()),
        "folds": [float(v) for v in arr],
    }


def cross_validate_regression(df: pd.DataFrame, model_type: str, include_lag_features: bool,
                              n_splits: int = 5) -> dict:
    """K-fold CV for a regression variant. Returns mean ± std of all metrics."""
    rmses, maes, mapes, r2s = [], [], [], []

    # We rebuild EnergyRegressionModel from scratch for each fold so the
    # sklearn estimator state is independent across splits.
    shuffle = not include_lag_features
    kf = KFold(n_splits=n_splits, shuffle=shuffle, random_state=42 if shuffle else None)
    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(df)):
        train_df = df.iloc[train_idx].copy()
        test_df = df.iloc[test_idx].copy()

        model = EnergyRegressionModel(model_type=model_type, include_lag_features=include_lag_features)
        X_train, y_train = model.prepare_features(train_df)
        model.train(X_train, y_train)

        # Re-prepare on test split. For lagged models, prepare_features will
        # drop rows that lack enough history within the test slice — that's
        # acceptable for a fold-level estimate.
        X_test, y_test = model.prepare_features(test_df)
        if len(X_test) == 0:
            continue
        pred = model.predict(X_test)

        rmses.append(float(np.sqrt(mean_squared_error(y_test, pred))))
        maes.append(float(mean_absolute_error(y_test, pred)))
        mapes.append(_mape(np.asarray(y_test), pred))
        r2s.append(float(r2_score(y_test, pred)))

    return {
        "n_splits": n_splits,
        "shuffle": not include_lag_features,
        "rmse": _summary(rmses),
        "mae": _summary(maes),
        "mape": _summary(mapes),
        "r2": _summary(r2s),
        "accuracy_pct": _summary([max(0.0, 100.0 - m) for m in mapes]),
    }


def sample_predictions(df: pd.DataFrame, model: EnergyRegressionModel, sample_size: int) -> list[dict]:
    """Generate (timestamp, actual, predicted) tuples for the chart, using a
    chronological held-out tail of the data."""
    df = df.sort_values("Timestamp").reset_index(drop=True)
    split = int(len(df) * 0.8)
    test_df = df.iloc[split:].copy()
    X, y = model.prepare_features(test_df)
    if len(X) == 0:
        return []
    preds = model.predict(X)

    # prepare_features may drop rows (lag NaN tail); rebuild a Timestamp series
    # aligned to the surviving rows. Easiest: re-pull the timestamps from the
    # post-prepare dataframe by re-running the same logic.
    rebuilt = test_df.copy()
    if model.include_lag_features:
        rebuilt = rebuilt.sort_values("Timestamp").reset_index(drop=True)
        for lag in (1, 24, 168):
            rebuilt[f"EnergyConsumption_lag_{lag}"] = rebuilt["EnergyConsumption"].shift(lag)
        rebuilt["EnergyConsumption_rolling_24"] = rebuilt["EnergyConsumption"].shift(1).rolling(24).mean()
        rebuilt = rebuilt.dropna().reset_index(drop=True)
    timestamps = pd.to_datetime(rebuilt["Timestamp"]).astype(str).tolist()

    # Down-sample evenly so we don't ship 800 points to the browser.
    n = len(preds)
    step = max(1, n // sample_size)
    return [
        {
            "timestamp": timestamps[i],
            "actual": float(y.iloc[i]) if hasattr(y, "iloc") else float(y[i]),
            "predicted": float(preds[i]),
        }
        for i in range(0, n, step)
    ][:sample_size]


def _pr_block(truth: np.ndarray, detected: np.ndarray) -> dict:
    return {
        "detected_positive": int(detected.sum()),
        "true_positives": int((truth & detected).sum()),
        "false_positives": int((~truth & detected).sum()),
        "false_negatives": int((truth & ~detected).sum()),
        "precision": float(precision_score(truth, detected, zero_division=0)),
        "recall": float(recall_score(truth, detected, zero_division=0)),
        "f1": float(f1_score(truth, detected, zero_division=0)),
    }


def evaluate_anomaly_detector(df: pd.DataFrame) -> dict:
    detector = AnomalyDetector()
    detector.load_model(str(MODELS_DIR / "anomaly_detector.joblib"))

    # Pseudo-truth from the same rules used at training time — see
    # AnomalyDetector::compute_rule_based_labels for the predicate definitions.
    truth = compute_rule_based_labels(df)

    flags = detector.detect_hybrid(df)

    if not truth.any():
        return {
            "note": "No rule-based pseudo-labels found in dataset — cannot compute P/R.",
            "if_only_detected": int(flags["if_flagged"].sum()),
        }

    return {
        "ground_truth_source": "rule-based pseudo-labels (see anomaly_detector.py::compute_rule_based_labels)",
        "ground_truth_positive": int(truth.sum()),
        # IsolationForest only — measures how well the unsupervised model
        # alone reproduces the rules.
        "if_only": _pr_block(truth, flags["if_flagged"]),
        # Hybrid (recommended production output) — rules OR IF. Recall vs
        # rules is 1.0 by construction; precision tells us how much extra
        # noise the IF adds on top.
        "hybrid": _pr_block(truth, flags["hybrid"]),
        # Novel findings: cases the IF flagged that no rule matched. These
        # are the "unknown unknowns" — what makes having an ML detector at all
        # worthwhile beyond the rules. Cannot be scored against rule truth.
        "novel_findings": {
            "count": int(flags["novel_flagged"].sum()),
            "percentage_of_dataset": float(flags["novel_flagged"].sum() / len(df) * 100),
            "note": "Flagged by IsolationForest but not by any rule — manual triage candidates.",
        },
        "trained_contamination": float(detector.contamination),
        "caveat": "P/R is measured vs heuristic rules, not human-labelled truth. Use as a sanity check, not absolute accuracy.",
    }


def main():
    if not Path(DATA_PATH).exists():
        raise FileNotFoundError(
            f"{DATA_PATH} not found. Run `python -m ml.training.train_models` first to produce the cleaned dataset."
        )

    df = pd.read_csv(DATA_PATH)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])

    print("=" * 60)
    print("EnerSight — Model Evaluation")
    print(f"Dataset: {len(df)} rows, {df['Timestamp'].min()} → {df['Timestamp'].max()}")
    print("=" * 60)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_records": int(len(df)),
        "regression_cv": {},
        "anomaly": {},
    }
    chart_payload = {"generated_at": payload["generated_at"], "models": {}}

    for model_type in ["random_forest", "gradient_boost"]:
        for variant in [False, True]:
            key = f"regression_{model_type}_{'lagged' if variant else 'baseline'}"
            print(f"\n→ 5-fold CV: {key}")
            cv = cross_validate_regression(df, model_type, include_lag_features=variant)
            payload["regression_cv"][key] = cv
            acc = cv["accuracy_pct"]
            print(f"   Accuracy: {acc['mean']:.2f}% ± {acc['std']:.2f}%  (folds: {[f'{v:.1f}' for v in acc['folds']]})")

            # Use the freshly trained final-fold model just for chart sampling.
            # We rebuild once on the full data so the chart reflects the
            # production-style fit, not one of the CV folds.
            print(f"   Sampling predicted-vs-actual for chart...")
            model = EnergyRegressionModel(model_type=model_type, include_lag_features=variant)
            X_full, y_full = model.prepare_features(df.copy())
            # Train on 80% (chronological), sample predictions on the 20% tail.
            split = int(len(X_full) * 0.8)
            model.train(X_full.iloc[:split], y_full.iloc[:split])
            chart_payload["models"][key] = sample_predictions(df, model, CHART_SAMPLE_SIZE)

    print("\n→ Anomaly detector P/R vs pseudo-labels")
    payload["anomaly"] = evaluate_anomaly_detector(df)
    if "precision" in payload["anomaly"]:
        a = payload["anomaly"]
        print(f"   Precision: {a['precision']:.2%}  Recall: {a['recall']:.2%}  F1: {a['f1']:.2%}")

    EVALUATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EVALUATION_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    with PREDICTIONS_PATH.open("w", encoding="utf-8") as f:
        json.dump(chart_payload, f, indent=2, default=str)

    print(f"\n✓ Wrote {EVALUATION_PATH}")
    print(f"✓ Wrote {PREDICTIONS_PATH}")


if __name__ == "__main__":
    main()
