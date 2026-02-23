"""
Data Loader Script
Load CSV data into InfluxDB for historical analysis
"""

import pandas as pd
from influxdb_client.client.influxdb_client import InfluxDBClient
from influxdb_client.client.write.point import Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
import sys
import os

def load_data_to_influxdb(csv_path, url, token, org, bucket):
    """
    Load energy consumption data from CSV to InfluxDB
    
    Args:
        csv_path: Path to CSV file
        url: InfluxDB URL
        token: InfluxDB token
        org: InfluxDB organization
        bucket: InfluxDB bucket name
    """
    print(f"Loading data from {csv_path}...")
    
    # Read CSV
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} records")
    
    # Connect to InfluxDB
    client = InfluxDBClient(url=url, token=token, org=org)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
    # Convert data to InfluxDB points
    points = []
    for record_count, (idx, row) in enumerate(df.iterrows(), 1):
        point = Point("energy_consumption") \
            .tag("location", "building_1") \
            .tag("hvac_status", row['HVACUsage']) \
            .tag("lighting_status", row['LightingUsage']) \
            .tag("holiday", row['Holiday']) \
            .tag("day_of_week", row['DayOfWeek']) \
            .field("consumption", float(row['EnergyConsumption'])) \
            .field("temperature", float(row['Temperature'])) \
            .field("humidity", float(row['Humidity'])) \
            .field("occupancy", int(row['Occupancy'])) \
            .field("square_footage", float(row['SquareFootage'])) \
            .field("renewable_energy", float(row['RenewableEnergy'])) \
            .time(pd.to_datetime(row['Timestamp']))
        
        points.append(point)
        
        # Write in batches of 1000
        if len(points) >= 1000:
            write_api.write(bucket=bucket, record=points)
            print(f"Wrote {record_count} records...")
            points = []
    
    # Write remaining points
    if points:
        write_api.write(bucket=bucket, record=points)
    
    print(f"✓ Successfully loaded {len(df)} records to InfluxDB")
    
    # Close connection
    write_api.close()
    client.close()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Load CSV data to InfluxDB')
    parser.add_argument('--csv', type=str, required=True, help='Path to CSV file')
    parser.add_argument('--url', type=str, default='http://localhost:8086', help='InfluxDB URL')
    parser.add_argument('--token', type=str, required=True, help='InfluxDB token')
    parser.add_argument('--org', type=str, default='enersight', help='InfluxDB organization')
    parser.add_argument('--bucket', type=str, default='energy_data', help='InfluxDB bucket')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv):
        print(f"Error: CSV file not found: {args.csv}")
        sys.exit(1)
    
    load_data_to_influxdb(
        csv_path=args.csv,
        url=args.url,
        token=args.token,
        org=args.org,
        bucket=args.bucket
    )

if __name__ == "__main__":
    main()
