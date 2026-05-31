"""
Train the concurrent multivariate LSTM and save its artifacts.

    .\\venv\\Scripts\\python.exe -m ml.training.train_lstm_multivariate

Writes:
  ml/models/trained/lstm_energy_multivariate.keras
  ml/models/trained/lstm_multivariate_bundle.joblib   (scalers + meta)

Prints honest test metrics (R²/RMSE/MAE/MAPE) and a sanity check that the
single-vector inference path (tiled window, used by the API) agrees with the
full-window predictions.
"""

import numpy as np
import pandas as pd

from ml.models.lstm_multivariate import EnergyMultivariateLSTMModel

DATA = "data/processed/energy_data_cleaned.csv"
KERAS_PATH = "ml/models/trained/lstm_energy_multivariate.keras"
BUNDLE_PATH = "ml/models/trained/lstm_multivariate_bundle.joblib"


def main() -> None:
    df = pd.read_csv(DATA)

    # sequence_length=1: the dataset is temporally random (no autocorrelation in
    # consumption OR its drivers), so a multi-step window adds no signal and would
    # make the single-conditions API path out-of-distribution. A length-1 sequence
    # keeps training inputs identical to what /predict feeds, so the reported R²
    # is exactly what the API delivers.
    model = EnergyMultivariateLSTMModel(sequence_length=1)
    X_train, X_test, y_train, y_test = model.prepare_and_split(df, test_size=0.2)
    print(f"Train windows: {len(X_train)}  Test windows: {len(X_test)}  "
          f"Features/step: {len(model.feature_columns)}")

    model.build_model(units=(64, 32), dropout=0.2)
    model.train(X_train, y_train, X_test, y_test, epochs=80, batch_size=32, verbose=0)

    metrics = model.evaluate(X_test, y_test)
    print("\n=== Multivariate LSTM — honest test metrics ===")
    for k, v in metrics.items():
        print(f"  {k:12} {v:.4f}")

    # Sanity: does the API's tiled single-vector path agree with the windowed
    # model on the test rows? (It should, since the data has no autocorrelation.)
    df_eng = pd.read_csv(DATA)
    from ml.models.lstm_multivariate import engineer_features
    df_eng = engineer_features(df_eng)
    n = len(df_eng); split = int(n * 0.8)
    test_rows = df_eng.iloc[split:].to_dict("records")
    windowed = model.target_scaler.inverse_transform(model.model.predict(X_test, verbose=0)).ravel()
    tiled = np.array([model.predict_point(r) for r in test_rows[:len(windowed)]])
    mad = float(np.mean(np.abs(windowed - tiled)))
    print(f"\nTiled-vs-windowed mean abs diff: {mad:.3f} kWh "
          f"({'OK — single-vector path is faithful' if mad < 1.0 else 'WARN — divergent'})")

    model.save(KERAS_PATH, BUNDLE_PATH)
    print(f"\n[OK] Saved {KERAS_PATH} and {BUNDLE_PATH}")


if __name__ == "__main__":
    main()
