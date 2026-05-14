"""
MQTT Client for IoT Device Communication
Handles real-time data ingestion from energy sensors
"""

import paho.mqtt.client as mqtt
import json
import os
from datetime import datetime

class MQTTClient:
    """MQTT client for receiving sensor data"""
    
    def __init__(self):
        self.broker = os.getenv("MQTT_BROKER", "localhost")
        self.port = int(os.getenv("MQTT_PORT", 1883))
        self.topic = os.getenv("MQTT_TOPIC", "enersight/sensors/#")
        self.client = mqtt.Client(client_id="enersight_backend")
        
        # Set callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            print(f"Connected to MQTT Broker: {self.broker}")
            client.subscribe(self.topic)
            print(f"Subscribed to topic: {self.topic}")
        else:
            print(f"Failed to connect, return code {rc}")
    
    def on_message(self, client, userdata, msg):
        """Callback when message is received"""
        try:
            payload = json.loads(msg.payload.decode())
            print(f"Received message on {msg.topic}: {payload}")
            
            # TODO: persist payload to public.energy_readings via the repository
            self.process_sensor_data(payload)
            
        except json.JSONDecodeError as e:
            print(f"Error decoding message: {e}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker"""
        print(f"Disconnected from MQTT Broker with code: {rc}")
    
    def process_sensor_data(self, data: dict):
        """Process incoming sensor data"""
        # Add timestamp if not present
        if "timestamp" not in data:
            data["timestamp"] = datetime.utcnow().isoformat()
        
        # TODO: validate the payload schema
        # TODO: persist to public.energy_readings (Supabase Postgres)
        # TODO: trigger anomaly detection on the new reading
        pass
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(self.broker, self.port, 60)
            return True
        except Exception as e:
            print(f"MQTT connection failed: {e}")
            return False
    
    def start(self):
        """Start MQTT client loop"""
        self.client.loop_start()
    
    def stop(self):
        """Stop MQTT client loop"""
        self.client.loop_stop()
        self.client.disconnect()

# Singleton instance
mqtt_client = MQTTClient()
