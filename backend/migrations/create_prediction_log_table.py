"""
Migration: create the ml_prediction_log table used for live drift monitoring.

Run with:  python -m backend.migrations.create_prediction_log_table

We deliberately avoid importing `backend.database.postgres` here — that pulls
`backend.core.__init__`, which eagerly imports the entire DI graph including
the async services. Instead we build a minimal sync engine straight from the
DATABASE_URL env var, which is exactly what the migration needs.
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("DATABASE_URL is not set. Add it to your .env file.")

# Build a standalone Base for the migration so we don't share state with the
# application's Base (which would trigger the circular import).
MigrationBase = declarative_base()


def _define_table():
    """Mirror the production model on the local Base."""
    from sqlalchemy import Column, DateTime, Float, Integer, String
    from sqlalchemy.dialects.postgresql import JSONB
    from datetime import datetime

    class PredictionLog(MigrationBase):
        __tablename__ = "ml_prediction_log"
        id = Column(Integer, primary_key=True, index=True)
        created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
        target_at = Column(DateTime(timezone=True), nullable=False, index=True)
        prediction_type = Column(String(16), nullable=False)
        model_name = Column(String(64), nullable=False)
        features = Column(JSONB)
        predicted_value = Column(Float, nullable=False)
        actual_value = Column(Float, nullable=True)
        error = Column(Float, nullable=True)
        abs_pct_error = Column(Float, nullable=True)
        backfilled_at = Column(DateTime(timezone=True), nullable=True)

    return PredictionLog


def run_migration():
    table = _define_table()
    print("Creating ml_prediction_log table (if missing)...")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    try:
        MigrationBase.metadata.create_all(bind=engine, tables=[table.__table__])
        print("OK ml_prediction_log table is ready")
    except Exception as e:
        print(f"FAILED: {e}")
        raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    run_migration()
