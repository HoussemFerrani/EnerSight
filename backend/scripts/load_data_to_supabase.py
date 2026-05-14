"""
Load the sample Energy_consumption.csv into Supabase Postgres.

Replaces the previous InfluxDB loader. Reads the CSV at data/raw/Energy_consumption.csv
and inserts it into public.energy_readings. Run from the project root:

    python -m backend.scripts.load_data_to_supabase
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, delete, text
from sqlalchemy.orm import sessionmaker

# Make `backend` importable when running this file directly.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.config import get_settings  # noqa: E402
from backend.models.energy import EnergyReading  # noqa: E402

settings = get_settings()

CSV_FILE = PROJECT_ROOT / "data" / "raw" / "Energy_consumption.csv"

DAY_MAP = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}


def _row_to_reading(idx: int, row: pd.Series) -> dict:
    day_val = row.get("DayOfWeek", 0)
    if isinstance(day_val, str):
        day_val = DAY_MAP.get(day_val.lower(), 0)
    return {
        "recorded_at": row["Timestamp"].to_pydatetime() if hasattr(row["Timestamp"], "to_pydatetime") else row["Timestamp"],
        "device_id": f"device_{idx % 10}",
        "location": "default",
        "consumption": float(row.get("EnergyConsumption", 0) or 0),
        "temperature": float(row.get("Temperature", 0) or 0),
        "humidity": float(row.get("Humidity", 0) or 0),
        "square_footage": float(row.get("SquareFootage", 1000) or 1000),
        "occupancy": int(row.get("Occupancy", 0) or 0),
        "hvac_usage": row.get("HVACUsage") == "On",
        "lighting_usage": row.get("LightingUsage") == "On",
        "renewable_energy": float(row.get("RenewableEnergy", 0) or 0),
        "day_of_week": int(day_val),
        "holiday": row.get("Holiday") == "Yes",
    }


def main() -> None:
    if not settings.database_url:
        print("DATABASE_URL is not set. Add it to .env first.")
        sys.exit(1)
    if not CSV_FILE.exists():
        print(f"CSV not found at {CSV_FILE}")
        print("Drop your Energy_consumption.csv into data/raw/ and rerun.")
        sys.exit(1)

    print(f"Reading {CSV_FILE}")
    df = pd.read_csv(CSV_FILE)
    print(f"Loaded {len(df)} rows. Columns: {', '.join(df.columns)}")

    # Normalize timestamps. If a Timestamp column exists, shift the series so it
    # ends "now" — matches the original loader's behavior and keeps recency.
    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        shift = datetime.utcnow() - df["Timestamp"].max()
        df["Timestamp"] = df["Timestamp"] + shift
    else:
        start = datetime.utcnow() - timedelta(hours=len(df))
        df["Timestamp"] = [start + timedelta(hours=i) for i in range(len(df))]
    print(f"Time range: {df['Timestamp'].min()} -> {df['Timestamp'].max()}")

    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        print("Truncating public.energy_readings...")
        session.execute(text("truncate table public.energy_readings restart identity cascade"))
        session.commit()

        records = [_row_to_reading(i, row) for i, row in df.iterrows()]
        # Chunked insert keeps memory and parameter count sane.
        chunk_size = 500
        total = 0
        for i in range(0, len(records), chunk_size):
            chunk = records[i:i + chunk_size]
            session.bulk_insert_mappings(EnergyReading, chunk)
            session.commit()
            total += len(chunk)
            print(f"Inserted {total}/{len(records)}")

        count = session.execute(text("select count(*) from public.energy_readings")).scalar()
        print(f"Done. energy_readings now has {count} rows.")


if __name__ == "__main__":
    main()
