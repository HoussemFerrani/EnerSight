"""
Reading simulator service.

There are no real sensors: this background task replays rows from the
historical dataset into `public.energy_readings` with current timestamps, so
the dashboard stays live and the alert monitor has fresh data to evaluate.
(Distinct from data_simulator.py, which only feeds the WebSocket demo stream
and persists nothing.)

Controlled via env:
  SIMULATOR_ENABLED          - "true" (default) to run
  SIMULATOR_INTERVAL_SECONDS - seconds between readings (default 300)
  SIMULATOR_DATA_PATH        - CSV to replay (default data/raw/Energy_consumption.csv)

At the default 300s interval the rolling 1-hour total is ~12 readings of
~75-85 kWh each (~950 kWh) — set the alert threshold relative to that.
"""
import asyncio
import os
import random
from datetime import datetime
from pathlib import Path

from backend.core.logging import get_logger
from backend.database.postgres import SessionLocal
from backend.models.energy import EnergyReading

logger = get_logger(__name__)


class ReadingSimulatorService:
    """Replays the historical dataset as live sensor readings."""

    def __init__(self):
        self.is_running = False
        self.enabled = os.getenv("SIMULATOR_ENABLED", "true").lower() in ("true", "1", "yes")
        self.interval = int(os.getenv("SIMULATOR_INTERVAL_SECONDS", "300"))
        self.data_path = os.getenv("SIMULATOR_DATA_PATH", "data/raw/Energy_consumption.csv")
        self._rows = None
        self._index = 0

    def _load_dataset(self) -> None:
        path = Path(self.data_path)
        if not path.exists():
            logger.warning(f"Simulator dataset not found at {path}; using random readings")
            self._rows = None
            return
        import pandas as pd
        self._rows = pd.read_csv(path)
        # Start at a random position so restarts don't always replay the same days
        self._index = random.randrange(len(self._rows))
        logger.info(f"Simulator loaded {len(self._rows)} rows from {path}")

    def _next_reading(self) -> EnergyReading:
        now = datetime.utcnow()
        if self._rows is None:
            return EnergyReading(
                recorded_at=now,
                device_id="simulator",
                location="default",
                consumption=round(random.uniform(50, 100), 2),
                temperature=round(random.uniform(18, 32), 2),
                humidity=round(random.uniform(30, 70), 2),
                square_footage=1500.0,
                occupancy=random.randint(0, 10),
                hvac_usage=random.random() < 0.5,
                lighting_usage=random.random() < 0.5,
                renewable_energy=round(random.uniform(0, 30), 2),
                day_of_week=now.weekday(),
                holiday=False,
            )

        row = self._rows.iloc[self._index]
        self._index = (self._index + 1) % len(self._rows)
        return EnergyReading(
            recorded_at=now,
            device_id="simulator",
            location="default",
            consumption=float(row["EnergyConsumption"]),
            temperature=float(row["Temperature"]),
            humidity=float(row["Humidity"]),
            square_footage=float(row["SquareFootage"]),
            occupancy=int(row["Occupancy"]),
            hvac_usage=str(row["HVACUsage"]).strip().lower() == "on",
            lighting_usage=str(row["LightingUsage"]).strip().lower() == "on",
            renewable_energy=float(row["RenewableEnergy"]),
            day_of_week=now.weekday(),
            holiday=str(row["Holiday"]).strip().lower() == "yes",
        )

    def insert_reading(self) -> EnergyReading:
        """Insert one simulated reading. Returns the persisted row."""
        db = SessionLocal()
        try:
            reading = self._next_reading()
            db.add(reading)
            db.commit()
            db.refresh(reading)
            logger.debug(
                f"Simulated reading: {reading.consumption:.2f} kWh at {reading.recorded_at}"
            )
            return reading
        finally:
            db.close()

    async def start(self):
        if not self.enabled:
            logger.info("Reading simulator disabled (SIMULATOR_ENABLED=false)")
            return
        self._load_dataset()
        self.is_running = True
        logger.info(f"Reading simulator started (interval: {self.interval}s)")
        while self.is_running:
            try:
                self.insert_reading()
            except Exception as e:
                logger.error(f"Error inserting simulated reading: {e}")
            await asyncio.sleep(self.interval)

    def stop(self):
        self.is_running = False
        logger.info("Reading simulator stopped")


reading_simulator = ReadingSimulatorService()
