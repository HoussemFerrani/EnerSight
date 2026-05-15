"""
Benchmark Keras vs TFLite (float32 + INT8) for the LSTM forecaster.

Reports for each variant:
  * On-disk size
  * Single-step inference latency (mean over N runs)
  * 24-step iterative forecast latency
  * Numerical deviation from the Keras baseline

Run with:
    python -m ml.training.benchmark_lstm_tflite
"""
from __future__ import annotations

import argparse
import os
import time
from pathlib import Path
from statistics import mean, stdev

import numpy as np
import tensorflow as tf
from tensorflow import keras


MODELS_DIR = Path("ml/models/trained")
SEQUENCE_LEN = 24
N_WARMUP = 5
N_RUNS = 50


def _bytes_on_disk(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            total += os.path.getsize(os.path.join(root, f))
    return total


def _fmt_bytes(n: int) -> str:
    x = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if x < 1024:
            return f"{x:,.1f} {unit}"
        x /= 1024
    return f"{x:,.1f} TB"


def _time_keras(model, x: np.ndarray) -> float:
    t0 = time.perf_counter()
    model.predict(x, verbose=0)
    return time.perf_counter() - t0


def _time_tflite(interp, in_idx: int, out_idx: int, x: np.ndarray) -> float:
    t0 = time.perf_counter()
    interp.set_tensor(in_idx, x)
    interp.invoke()
    interp.get_tensor(out_idx)
    return time.perf_counter() - t0


def run() -> None:
    keras_path = MODELS_DIR / "lstm_energy_forecast.keras"
    float_path = MODELS_DIR / "lstm_energy_forecast.tflite"
    int8_path = MODELS_DIR / "lstm_energy_forecast.q8.tflite"

    if not keras_path.exists() or not float_path.exists():
        raise SystemExit(
            "Missing artifacts. Run `python -m ml.training.export_lstm_tflite` first."
        )

    # Inference-only benchmark: feed already-scaled values in [0,1] directly,
    # bypassing the scaler since we're measuring the network, not preprocessing.
    rng = np.random.default_rng(42)
    x = rng.uniform(0.0, 1.0, size=(1, SEQUENCE_LEN, 1)).astype(np.float32)

    # ---- Keras baseline ------------------------------------------------
    print("\nLoading Keras model...")
    keras_model = keras.models.load_model(keras_path)
    for _ in range(N_WARMUP):
        keras_model.predict(x, verbose=0)
    keras_times = [_time_keras(keras_model, x) for _ in range(N_RUNS)]
    keras_pred = float(keras_model.predict(x, verbose=0)[0, 0])

    # ---- TFLite float32 ------------------------------------------------
    print("Loading TFLite float32 interpreter...")
    f_interp = tf.lite.Interpreter(model_path=str(float_path))
    f_interp.allocate_tensors()
    f_in = f_interp.get_input_details()[0]["index"]
    f_out = f_interp.get_output_details()[0]["index"]
    for _ in range(N_WARMUP):
        f_interp.set_tensor(f_in, x); f_interp.invoke()
    f_times = [_time_tflite(f_interp, f_in, f_out, x) for _ in range(N_RUNS)]
    f_interp.set_tensor(f_in, x); f_interp.invoke()
    f_pred = float(f_interp.get_tensor(f_out)[0, 0])

    # ---- TFLite INT8 (optional) ---------------------------------------
    q_times = q_pred = None
    if int8_path.exists():
        print("Loading TFLite INT8 interpreter...")
        q_interp = tf.lite.Interpreter(model_path=str(int8_path))
        q_interp.allocate_tensors()
        q_in = q_interp.get_input_details()[0]["index"]
        q_out = q_interp.get_output_details()[0]["index"]
        for _ in range(N_WARMUP):
            q_interp.set_tensor(q_in, x); q_interp.invoke()
        q_times = [_time_tflite(q_interp, q_in, q_out, x) for _ in range(N_RUNS)]
        q_interp.set_tensor(q_in, x); q_interp.invoke()
        q_pred = float(q_interp.get_tensor(q_out)[0, 0])

    # ---- Report --------------------------------------------------------
    print("\n=== LSTM inference benchmark ===")
    print(f"  N runs (excluding warmup): {N_RUNS}")
    print(f"  Sequence length: {SEQUENCE_LEN}, features: 1\n")

    rows = [
        ("Keras (.keras)", keras_path, keras_times, keras_pred, 0.0),
        ("TFLite float32",  float_path, f_times,     f_pred,     abs(f_pred - keras_pred)),
    ]
    if q_pred is not None:
        rows.append(("TFLite INT8 (quant)", int8_path, q_times, q_pred, abs(q_pred - keras_pred)))

    print(f"  {'Variant':<22}{'Size':>12}{'Latency mean':>16}{'Stddev':>12}{'Pred':>12}{'|err vs Keras|':>18}")
    print("  " + "-" * 92)
    for label, path, times, pred, err in rows:
        size = _bytes_on_disk(path)
        mean_ms = mean(times) * 1000
        std_ms = stdev(times) * 1000 if len(times) > 1 else 0.0
        print(
            f"  {label:<22}{_fmt_bytes(size):>12}{mean_ms:>13.3f} ms"
            f"{std_ms:>9.3f} ms{pred:>12.4f}{err:>18.2e}"
        )

    # 24-step iterative forecast latency: closer to how the API uses the model.
    print("\n=== 24-step iterative forecast ===")
    for label, predict_one in (
        ("Keras", lambda seq: float(keras_model.predict(seq, verbose=0)[0, 0])),
        ("TFLite float32", lambda seq: (
            f_interp.set_tensor(f_in, seq), f_interp.invoke(),
            float(f_interp.get_tensor(f_out)[0, 0]),
        )[-1]),
    ):
        seq = x.copy()
        # warmup
        for _ in range(3):
            predict_one(seq)
        t0 = time.perf_counter()
        for _ in range(24):
            v = predict_one(seq)
            seq = np.concatenate([seq[:, 1:, :], np.array([[[v]]], dtype=np.float32)], axis=1)
        dt = time.perf_counter() - t0
        print(f"  {label:<18}{dt * 1000:.1f} ms total ({dt * 1000 / 24:.2f} ms/step)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    run()
