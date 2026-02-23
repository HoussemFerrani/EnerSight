"""
IoT Sensor Simulator
Simulates real-time energy sensor data and publishes via MQTT
"""

import paho.mqtt.client as mqtt
import json
import time
import random
import pandas as pd
from datetime import datetime
import os

class SensorSimulator:
    """Simulate IoT energy sensors"""
    
    def __init__(self, data_source=None, broker="localhost", port=1883):
        self.broker = broker
        self.port = port
        self.client = mqtt.Client(client_id="sensor_simulator")
        self.data_source = data_source
        self.current_index = 0
        
        # Load historical data if provided
        if data_source and os.path.exists(data_source):
            self.historical_data = pd.read_csv(data_source)
            print(f"Loaded {len(self.historical_data)} records from {data_source}")
        else:
            self.historical_data = None
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(self.broker, self.port, 60)
            print(f"Connected to MQTT broker at {self.broker}:{self.port}")
            return True
        except Exception as e:
            print(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def generate_random_reading(self):
        """Generate random sensor reading"""
        return {
            "timestamp": datetime.now().isoformat(),
            "temperature": round(random.uniform(18, 32), 2),
            "humidity": round(random.uniform(30, 70), 2),
            "occupancy": random.randint(0, 10),
            "square_footage": 1500,
            "hvac_status": random.choice(["On", "Off"]),
            "lighting_status": random.choice(["On", "Off"]),
            "renewable_energy": round(random.uniform(0, 30), 2),
            "energy_consumption": round(random.uniform(50, 100), 2)
        }
    
    def get_historical_reading(self):
        """Get reading from historical dataset"""
        if self.historical_data is None:
            return self.generate_random_reading()
        
        if self.current_index >= len(self.historical_data):
            self.current_index = 0  # Loop back to start
        
        row = self.historical_data.iloc[self.current_index]
        self.current_index += 1
        
        return {
            "timestamp": datetime.now().isoformat(),  # Use current time
            "temperature": float(row['Temperature']),
            "humidity": float(row['Humidity']),
            "occupancy": int(row['Occupancy']),
            "square_footage": float(row['SquareFootage']),
            "hvac_status": row['HVACUsage'],
            "lighting_status": row['LightingUsage'],
            "renewable_energy": float(row['RenewableEnergy']),
            "energy_consumption": float(row['EnergyConsumption']),
            "holiday": row['Holiday']
        }
    
    def publish_reading(self, topic="enersight/sensors/energy"):
        """Publish sensor reading to MQTT"""
        reading = self.get_historical_reading() if self.historical_data is not None else self.generate_random_reading()
        
        payload = json.dumps(reading)
        result = self.client.publish(topic, payload)
        
        if result.rc == 0:
            print(f"Published: {reading['energy_consumption']:.2f} kWh at {reading['timestamp']}")
        else:
            print(f"Failed to publish message")
        
        return reading
    
    def simulate_continuous(self, interval=5, topic="enersight/sensors/energy"):
        """Continuously publish sensor data at specified interval (seconds)"""
        print(f"Starting continuous simulation (interval: {interval}s)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.publish_reading(topic)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nSimulation stopped by user")
        finally:
            self.client.disconnect()

def main():
    """Main simulation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='IoT Energy Sensor Simulator')
    parser.add_argument('--broker', type=str, default='localhost', help='MQTT broker address')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--data', type=str, default='data/raw/Energy_consumption.csv', 
                       help='Historical data CSV file')
    parser.add_argument('--interval', type=int, default=5, help='Publishing interval in seconds')
    parser.add_argument('--topic', type=str, default='enersight/sensors/energy', help='MQTT topic')
    
    args = parser.parse_args()
    
    # Initialize simulator
    simulator = SensorSimulator(
        data_source=args.data,
        broker=args.broker,
        port=args.port
    )
    
    # Connect and simulate
    if simulator.connect():
        simulator.simulate_continuous(interval=args.interval, topic=args.topic)

if __name__ == "__main__":
    main()
