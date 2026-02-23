"""
Real-time energy data simulator service.

Generates realistic energy consumption data patterns for live monitoring.
"""

import asyncio
import random
from datetime import datetime, timezone
from typing import Dict, Any
import math


class DataSimulator:
    """Simulates realistic real-time energy consumption data."""
    
    def __init__(self):
        self.base_consumption = 150.0  # Base kWh consumption
        self.is_running = False
        
    def generate_reading(self) -> Dict[str, Any]:
        """Generate a single realistic energy reading."""
        now = datetime.now(timezone.utc)
        hour = now.hour
        
        # Simulate daily pattern: higher during day, lower at night
        time_factor = 1.0 + 0.3 * math.sin((hour - 6) * math.pi / 12)
        
        # Add some randomness
        random_factor = random.uniform(0.85, 1.15)
        
        # Calculate consumption
        consumption = self.base_consumption * time_factor * random_factor
        
        # Occasional spikes (5% chance)
        if random.random() < 0.05:
            consumption *= random.uniform(1.5, 2.0)
        
        # Generate related metrics
        voltage = random.uniform(220, 240)
        current = consumption / voltage if voltage > 0 else 0
        power_factor = random.uniform(0.85, 0.95)
        temperature = random.uniform(18, 28)
        humidity = random.uniform(40, 70)
        
        return {
            "timestamp": now.isoformat(),
            "consumption": round(consumption, 2),
            "voltage": round(voltage, 2),
            "current": round(current, 2),
            "power_factor": round(power_factor, 2),
            "temperature": round(temperature, 1),
            "humidity": round(humidity, 1),
            "cost": round(consumption * 0.12, 2),  # $0.12 per kWh
            "location": "Building A - Floor 1",
            "device_id": "sensor_001"
        }
    
    async def stream_data(self, callback, interval: float = 5.0):
        """
        Continuously generate and stream data.
        
        Args:
            callback: Async function to call with each reading
            interval: Seconds between readings (default: 5)
        """
        self.is_running = True
        
        while self.is_running:
            try:
                reading = self.generate_reading()
                await callback(reading)
                await asyncio.sleep(interval)
            except Exception as e:
                print(f"Error in data simulator: {e}")
                await asyncio.sleep(interval)
    
    def stop(self):
        """Stop the data stream."""
        self.is_running = False


# Singleton instance
_simulator_instance = None


def get_simulator() -> DataSimulator:
    """Get or create the singleton simulator instance."""
    global _simulator_instance
    if _simulator_instance is None:
        _simulator_instance = DataSimulator()
    return _simulator_instance
