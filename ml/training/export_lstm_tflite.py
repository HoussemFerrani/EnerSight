"""
Convert the trained Keras LSTM into a TensorFlow Lite flatbuffer.

This is what bridges the ML model to IoT / edge deployment: the resulting
`.tflite` file is a fraction of the original `.keras` size and runs under
`tf.lite.Interpreter` (or the standalone `tflite_runtime`) on Raspberry Pi,
ESP32-class boards, smartphones, and gateways — none of which can host a
full TensorFlow install.

Two converted artifacts are produced side-by-side:
  * lstm_energy_forecast.tflite           — float32, no quantization
  * lstm_energy_forecast.q8.tflite        — dynamic-range INT8 quantized

The scaler.joblib stays unchanged; the TFLite interpreter consumes scaled
float inputs exactly like the Keras model did.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow import keras


DEFAULT_KERAS_PATH = Path("ml/models/trained/lstm_energy_forecast.keras")
DEFAULT_OUTPUT_DIR = Path("ml/models/trained")


def convert(keras_path: Path, output_dir: Path) -> dict:
    if not keras_path.exists():
        raise FileNotFoundError(f"Trained Keras model not found at {keras_path}")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading Keras model from {keras_path}")
    model = keras.models.load_model(keras_path)

    # Float32 (baseline) conversion --------------------------------------
    print("Converting -> float32 .tflite (no quantization)...")
    float_converter = tf.lite.TFLiteConverter.from_keras_model(model)
    # LSTM ops need SELECT_TF_OPS fallback on some TF versions; allow it so
    # the conversion succeeds across environments.
    float_converter.target_spec.supported_ops = [
        tf.lite.OpsSet.TFLITE_BUILTINS,
        tf.lite.OpsSet.SELECT_TF_OPS,
    ]
    float_tflite = float_converter.convert()
    float_path = output_dir / "lstm_energy_forecast.tflite"
    float_path.write_bytes(float_tflite)
    print(f"  wrote {float_path}  ({_size(float_path)})")

    # Dynamic-range INT8 quantization ------------------------------------
    print("Converting -> INT8 dynamic-range quantized .tflite...")
    q_converter = tf.lite.TFLiteConverter.from_keras_model(model)
    q_converter.optimizations = [tf.lite.Optimize.DEFAULT]
    q_converter.target_spec.supported_ops = [
        tf.lite.OpsSet.TFLITE_BUILTINS,
        tf.lite.OpsSet.SELECT_TF_OPS,
    ]
    try:
        q_tflite = q_converter.convert()
        q_path = output_dir / "lstm_energy_forecast.q8.tflite"
        q_path.write_bytes(q_tflite)
        print(f"  wrote {q_path}  ({_size(q_path)})")
    except Exception as e:  # pragma: no cover — environment-dependent
        print(f"  INT8 quantization failed ({e!r}); skipping the quantized variant.")
        q_path = None

    keras_size_bytes = _bytes_on_disk(keras_path)
    float_size_bytes = float_path.stat().st_size
    q_size_bytes = q_path.stat().st_size if q_path else None

    print("\nSize comparison")
    print(f"  Keras (.keras dir):       {_fmt_bytes(keras_size_bytes)}")
    print(f"  TFLite float32:           {_fmt_bytes(float_size_bytes)}  "
          f"({float_size_bytes / max(keras_size_bytes, 1) * 100:.1f}% of Keras)")
    if q_size_bytes is not None:
        print(f"  TFLite INT8 (dynamic):    {_fmt_bytes(q_size_bytes)}  "
              f"({q_size_bytes / max(keras_size_bytes, 1) * 100:.1f}% of Keras)")

    # Sanity check: float TFLite predictions should closely match Keras.
    _numerical_check(model, float_path)

    return {
        "keras_path": str(keras_path),
        "tflite_float_path": str(float_path),
        "tflite_int8_path": str(q_path) if q_path else None,
        "keras_size_bytes": keras_size_bytes,
        "tflite_float_size_bytes": float_size_bytes,
        "tflite_int8_size_bytes": q_size_bytes,
    }


def _numerical_check(keras_model, tflite_path: Path) -> None:
    print("\nNumerical agreement check (random input, sequence_length=24)...")
    rng = np.random.default_rng(42)
    x = rng.uniform(0.0, 1.0, size=(1, 24, 1)).astype(np.float32)

    keras_pred = float(keras_model.predict(x, verbose=0)[0, 0])

    interp = tf.lite.Interpreter(model_path=str(tflite_path))
    interp.allocate_tensors()
    in_idx = interp.get_input_details()[0]["index"]
    out_idx = interp.get_output_details()[0]["index"]
    interp.set_tensor(in_idx, x)
    interp.invoke()
    tflite_pred = float(interp.get_tensor(out_idx)[0, 0])

    abs_err = abs(keras_pred - tflite_pred)
    print(f"  Keras prediction:   {keras_pred:.6f}")
    print(f"  TFLite prediction:  {tflite_pred:.6f}")
    print(f"  Absolute error:     {abs_err:.2e}")
    if abs_err > 1e-3:
        print("  [!] predictions diverge — investigate before deploying.")
    else:
        print("  [OK] predictions match to within 1e-3.")


def _size(path: Path) -> str:
    return _fmt_bytes(path.stat().st_size)


def _bytes_on_disk(path: Path) -> int:
    """Return total bytes for a file *or* a SavedModel-style directory."""
    if path.is_file():
        return path.stat().st_size
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            total += os.path.getsize(os.path.join(root, f))
    return total


def _fmt_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:,.1f} {unit}"
        n /= 1024
    return f"{n:,.1f} TB"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--keras-path", type=Path, default=DEFAULT_KERAS_PATH,
        help=f"Path to the trained Keras model (default: {DEFAULT_KERAS_PATH})",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
        help=f"Where to write the .tflite files (default: {DEFAULT_OUTPUT_DIR})",
    )
    args = parser.parse_args()
    convert(args.keras_path, args.output_dir)
