"""
InfluxDB Connection and Operations
Time-series database for energy consumption data
"""

from influxdb_client.client.influxdb_client import InfluxDBClient
from influxdb_client.client.write.point import Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
import os

class InfluxDBConnection:
    """InfluxDB connection manager"""
    
    def __init__(self):
        self.url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
        self.token = os.getenv("INFLUXDB_TOKEN", "your-token")
        self.org = os.getenv("INFLUXDB_ORG", "enersight")
        self.bucket = os.getenv("INFLUXDB_BUCKET", "energy_data")
        self.client = None
        
    def connect(self):
        """Establish connection to InfluxDB"""
        try:
            self.client = InfluxDBClient(
                url=self.url,
                token=self.token,
                org=self.org
            )
            return True
        except Exception as e:
            print(f"InfluxDB connection failed: {e}")
            return False
    
    def write_energy_data(self, data: dict):
        """Write energy consumption data point"""
        if not self.client:
            if not self.connect():
                raise ConnectionError("Failed to connect to InfluxDB")
        
        assert self.client is not None
        write_api = self.client.write_api(write_options=SYNCHRONOUS)
        
        point = Point("energy_consumption") \
            .tag("location", data.get("location", "default")) \
            .field("consumption", float(data["consumption"])) \
            .field("temperature", float(data.get("temperature", 0))) \
            .field("humidity", float(data.get("humidity", 0))) \
            .field("occupancy", int(data.get("occupancy", 0))) \
            .time(data.get("timestamp", datetime.utcnow()))
        
        write_api.write(bucket=self.bucket, record=point)
    
    def query_data(self, start_time: str, end_time: str):
        """Query energy data within time range"""
        if not self.client:
            if not self.connect():
                raise ConnectionError("Failed to connect to InfluxDB")
        
        assert self.client is not None
        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: {start_time}, stop: {end_time})
            |> filter(fn: (r) => r._measurement == "energy_consumption")
        '''
        
        query_api = self.client.query_api()
        return query_api.query(query=query)
    
    def close(self):
        """Close InfluxDB connection"""
        if self.client:
            self.client.close()

# Singleton instance
influx_db = InfluxDBConnection()
