"""
ORM models for energy time-series data (replaces the InfluxDB measurement).
"""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, Integer, SmallInteger, String

from backend.database.postgres import Base


class EnergyReading(Base):
    """One row per sensor reading. Indexed by recorded_at desc."""
    __tablename__ = "energy_readings"

    id = Column(BigInteger, primary_key=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False, index=True)
    device_id = Column(String, nullable=False, default="device_0")
    location = Column(String, nullable=False, default="default")
    consumption = Column(Float, nullable=False)
    temperature = Column(Float)
    humidity = Column(Float)
    square_footage = Column(Float)
    occupancy = Column(Integer)
    hvac_usage = Column(Boolean)
    lighting_usage = Column(Boolean)
    renewable_energy = Column(Float)
    day_of_week = Column(SmallInteger)
    holiday = Column(Boolean)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "device_id": self.device_id,
            "location": self.location,
            "consumption": self.consumption,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "square_footage": self.square_footage,
            "occupancy": self.occupancy,
            "hvac_usage": self.hvac_usage,
            "lighting_usage": self.lighting_usage,
            "renewable_energy": self.renewable_energy,
            "day_of_week": self.day_of_week,
            "holiday": self.holiday,
        }
