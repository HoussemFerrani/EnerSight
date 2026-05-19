"""
Anomaly Detection for Energy Consumption
Detect unusual patterns and inefficient device behavior.

Notes on quality:
- This is an *unsupervised* detector (IsolationForest), so there are no real
  ground-truth labels at training time. To still tune it sensibly, we treat
  the existing business rules in `_determine_anomaly_reason` as pseudo-labels:
  any row matching at least one rule is "anomalous enough" that we'd expect
  the detector to flag it. The shared `compute_rule_based_labels` function
  generates those labels deterministically from the dataframe.
- `tune_contamination` then sweeps a small grid of `contamination` values and
  picks the one that maximises F1 vs those pseudo-labels. The pseudo-labels
  are a proxy, not truth — but they're better than picking 0.05 by hand.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler
import joblib

# Default contamination grid for tuning.
#
# Capped at 0.15 deliberately: this detector is designed to run in HYBRID mode
# (rules OR IsolationForest). The rules already catch rule-matching cases with
# precision=1, so the IF only needs to flag NOVEL surprises. A high
# contamination here would just add false positives on top of the rules.
# F1 vs rule pseudo-labels still drives the pick — we just refuse to tune
# into noise territory.
DEFAULT_CONTAMINATION_GRID = [0.03, 0.05, 0.08, 0.10, 0.12, 0.15]


def compute_rule_based_labels(df: pd.DataFrame) -> np.ndarray:
    """Boolean array — True for rows matching at least one of the business
    rules encoded in `_determine_anomaly_reason`. Used as pseudo-truth for
    tuning and evaluation.

    Keeps the rule definitions in lock-step with the per-row reasoning code
    by mirroring the same predicates."""
    rules = (
        (df["EnergyConsumption"] > 85)
        & (df["HVACUsage"] == "Off")
        & (df["LightingUsage"] == "Off")
    ) | (
        (df["Occupancy"] < 2) & (df["EnergyConsumption"] > 80)
    ) | (
        (df["Holiday"] == "Yes") & (df["EnergyConsumption"] > 85)
    ) | (
        ((df["Temperature"] < 22) | (df["Temperature"] > 28))
        & (df["HVACUsage"] == "On")
        & (df["EnergyConsumption"] < 70)
    )
    return rules.values


class AnomalyDetector:
    """Anomaly detection for energy consumption patterns"""

    def __init__(self, contamination: float = 0.05, n_estimators: int = 200):
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=n_estimators,
        )
        self.scaler = StandardScaler()
        self.feature_columns = None

    def prepare_features(self, df: pd.DataFrame):
        """Prepare the input feature matrix.

        Now includes Holiday, RenewableEnergy, and day-of-week, which the
        previous version was missing despite the business rules referencing
        Holiday directly. Without them the detector couldn't see the same
        information the rules used."""
        features = df.copy()

        features['HVACUsage_On'] = (features['HVACUsage'] == 'On').astype(int)
        features['LightingUsage_On'] = (features['LightingUsage'] == 'On').astype(int)

        feature_cols = [
            'EnergyConsumption', 'Temperature', 'Humidity', 'Occupancy',
            'HVACUsage_On', 'LightingUsage_On',
        ]

        # Holiday — rule-driven feature the previous detector was blind to.
        if 'Holiday' in features.columns:
            features['Holiday_Yes'] = (features['Holiday'] == 'Yes').astype(int)
            feature_cols.append('Holiday_Yes')

        # Renewable generation gives the model context for net consumption.
        if 'RenewableEnergy' in features.columns:
            feature_cols.append('RenewableEnergy')

        if 'Timestamp' in features.columns:
            features['Timestamp'] = pd.to_datetime(features['Timestamp'])
            features['Hour'] = features['Timestamp'].dt.hour
            features['DayOfWeek_Num'] = features['Timestamp'].dt.dayofweek
            feature_cols.extend(['Hour', 'DayOfWeek_Num'])

        self.feature_columns = feature_cols
        return features[feature_cols]

    def train(self, X):
        """Train anomaly detection model"""
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)

    def detect_anomalies(self, X):
        """Returns (predictions, scores). predictions: 1 for normal, -1 for anomaly."""
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        scores = self.model.score_samples(X_scaled)
        return predictions, scores

    def detect_hybrid(self, df: pd.DataFrame):
        """Hybrid: rule-matches OR IsolationForest outliers.

        Returns dict with three boolean arrays the caller can inspect or
        combine:
          - 'rule_flagged': matches at least one business rule (precision=1
            by construction)
          - 'if_flagged':   IsolationForest flagged it
          - 'hybrid':       rule_flagged OR if_flagged (the recommended
            production output — caught by either signal)
        Plus 'novel_flagged' = if_flagged AND NOT rule_flagged, i.e. cases the
        rules missed but the model still found suspicious. This is the
        *complementary value* the ML adds beyond the rules.
        """
        X = self.prepare_features(df.copy())
        if_predictions, scores = self.detect_anomalies(X)
        if_flagged = if_predictions == -1
        rule_flagged = compute_rule_based_labels(df)
        return {
            "rule_flagged": rule_flagged,
            "if_flagged": if_flagged,
            "hybrid": rule_flagged | if_flagged,
            "novel_flagged": if_flagged & ~rule_flagged,
            "scores": scores,
        }

    def find_anomalies_with_context(self, df: pd.DataFrame):
        X = self.prepare_features(df)
        predictions, scores = self.detect_anomalies(X)

        result_df = df.copy()
        result_df['is_anomaly'] = predictions == -1
        result_df['anomaly_score'] = scores

        anomalies = result_df[result_df['is_anomaly']].copy()
        anomalies['reason'] = anomalies.apply(self._determine_anomaly_reason, axis=1)
        return anomalies

    def _determine_anomaly_reason(self, row):
        reasons = []
        if row['EnergyConsumption'] > 85 and row['HVACUsage'] == 'Off' and row['LightingUsage'] == 'Off':
            reasons.append("High consumption without HVAC/Lighting")
        if row['Occupancy'] < 2 and row['EnergyConsumption'] > 80:
            reasons.append("High consumption with low occupancy")
        if row['Holiday'] == 'Yes' and row['EnergyConsumption'] > 85:
            reasons.append("High consumption on holiday")
        if (row['Temperature'] < 22 or row['Temperature'] > 28) and row['HVACUsage'] == 'On':
            if row['EnergyConsumption'] < 70:
                reasons.append("Inefficient HVAC operation")
        return "; ".join(reasons) if reasons else "Statistical outlier"

    def save_model(self, filepath):
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'contamination': self.contamination,
            'n_estimators': self.n_estimators,
        }, filepath)
        print(f"Anomaly detector saved to {filepath}")

    def load_model(self, filepath):
        data = joblib.load(filepath)
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_columns = data['feature_columns']
        self.contamination = data['contamination']
        self.n_estimators = data.get('n_estimators', 100)
        print(f"Anomaly detector loaded from {filepath}")


def tune_contamination(
    df: pd.DataFrame,
    candidates: list[float] = None,
    n_estimators: int = 200,
) -> dict:
    """Grid-search contamination against pseudo-labels from the business rules.
    Returns dict with the best value, the per-candidate F1, and the picked
    detector instance fitted on the full dataset."""
    candidates = candidates or DEFAULT_CONTAMINATION_GRID
    truth = compute_rule_based_labels(df)

    if not truth.any():
        # Without any rule hits we can't tune — fall back to a sane default.
        detector = AnomalyDetector(contamination=0.05, n_estimators=n_estimators)
        X = detector.prepare_features(df)
        detector.train(X)
        return {
            "best_contamination": 0.05,
            "best_f1": None,
            "scores": [],
            "note": "No rule-matching rows in dataset — defaulted to 0.05.",
            "detector": detector,
            "X": X,
        }

    scores = []
    best = None
    for c in candidates:
        detector = AnomalyDetector(contamination=c, n_estimators=n_estimators)
        X = detector.prepare_features(df)
        detector.train(X)
        preds, _ = detector.detect_anomalies(X)
        detected = preds == -1
        f1 = float(f1_score(truth, detected, zero_division=0))
        prec = float(precision_score(truth, detected, zero_division=0))
        rec = float(recall_score(truth, detected, zero_division=0))
        scores.append({"contamination": c, "f1": f1, "precision": prec, "recall": rec})
        if best is None or f1 > best["f1"]:
            best = {
                "contamination": c, "f1": f1, "precision": prec, "recall": rec,
                "detector": detector, "X": X,
            }

    return {
        "best_contamination": best["contamination"],
        "best_f1": best["f1"],
        "best_precision": best["precision"],
        "best_recall": best["recall"],
        "scores": scores,
        "detector": best["detector"],
        "X": best["X"],
    }


def train_anomaly_detector(data_path: str, tune: bool = True):
    """
    Train anomaly detection model.

    Args:
        data_path: Path to CSV dataset
        tune: When True, sweep contamination values and pick the F1-optimal
              one (using rule-based pseudo-labels). When False, train at the
              hardcoded contamination=0.05.
    """
    df = pd.read_csv(data_path)

    if tune:
        print("Tuning contamination against rule-based pseudo-labels...")
        result = tune_contamination(df)
        detector = result["detector"]
        print(f"Best contamination: {result['best_contamination']} (F1={result['best_f1']:.3f}, "
              f"P={result['best_precision']:.3f}, R={result['best_recall']:.3f})")
        print("All candidates:")
        for s in result["scores"]:
            print(f"  c={s['contamination']:.2f}  F1={s['f1']:.3f}  P={s['precision']:.3f}  R={s['recall']:.3f}")
    else:
        detector = AnomalyDetector(contamination=0.05)
        X = detector.prepare_features(df)
        print("Training anomaly detector (no tuning, contamination=0.05)...")
        detector.train(X)

    anomalies = detector.find_anomalies_with_context(df)

    print(f"\nFound {len(anomalies)} anomalies in training data "
          f"({len(anomalies)/len(df)*100:.2f}% of {len(df)} rows)")

    if len(anomalies) > 0:
        print("\nSample anomalies:")
        print(anomalies[['Timestamp', 'EnergyConsumption', 'Occupancy',
                        'HVACUsage', 'LightingUsage', 'reason']].head())

    model_path = "ml/models/trained/anomaly_detector.joblib"
    detector.save_model(model_path)

    return detector, anomalies


if __name__ == "__main__":
    data_path = "data/raw/Energy_consumption.csv"
    detector, anomalies = train_anomaly_detector(data_path)
