"""
Prediction log — one row per model prediction served by /predict or /forecast.
Filled in lazily by the backfill job once the ground-truth reading arrives.

This table is the source of truth for "live" model accuracy / drift monitoring,
distinct from the static training-time metrics in ml/models/trained/metrics.json.
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB

from backend.database.postgres import Base


class PredictionLog(Base):
    __tablename__ = "ml_prediction_log"

    id = Column(Integer, primary_key=True, index=True)

    # When the prediction was served.
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

    # The wall-clock time the prediction is *about*. For /predict, this is
    # roughly "now". For /forecast step h, this is created_at + h hours.
    target_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # Which endpoint / model produced this row — 'predict' or 'forecast'.
    prediction_type = Column(String(16), nullable=False)
    model_name = Column(String(64), nullable=False)

    # Derived from the trained model file's mtime — lets us slice live drift
    # by which retrained model produced each prediction.
    model_version = Column(String(64), nullable=True, index=True)

    # JSON snapshot of the input features (whatever the endpoint received).
    # Kept for post-hoc debugging — no schema enforced.
    features = Column(JSONB)

    predicted_value = Column(Float, nullable=False)

    # Filled in by backfill once an energy_readings row exists for target_at.
    actual_value = Column(Float, nullable=True)
    error = Column(Float, nullable=True)             # actual - predicted
    abs_pct_error = Column(Float, nullable=True)     # |error|/|actual| * 100
    backfilled_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "target_at": self.target_at.isoformat() if self.target_at else None,
            "prediction_type": self.prediction_type,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "features": self.features,
            "predicted_value": self.predicted_value,
            "actual_value": self.actual_value,
            "error": self.error,
            "abs_pct_error": self.abs_pct_error,
            "backfilled_at": self.backfilled_at.isoformat() if self.backfilled_at else None,
        }
