"""
Load Energy Data from CSV to InfluxDB
Script to import historical energy consumption data
"""

import pandas as pd
from datetime import datetime, timedelta
from influxdb_client.client.influxdb_client import InfluxDBClient
from influxdb_client.client.write.point import Point
from influxdb_client.client.write_api import SYNCHRONOUS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# InfluxDB configuration
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "enersight")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "energy_data")

# CSV file path - get absolute path relative to script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
CSV_FILE = os.path.join(PROJECT_ROOT, "data", "raw", "Energy_consumption.csv")


def clear_existing_data():
    """Clear all existing data from InfluxDB bucket"""
    if not INFLUXDB_TOKEN:
        print("❌ Error: INFLUXDB_TOKEN environment variable is not set")
        return
    
    print("\n🗑️  Clearing existing data from InfluxDB...")
    
    client = InfluxDBClient(
        url=INFLUXDB_URL,
        token=INFLUXDB_TOKEN,
        org=INFLUXDB_ORG
    )
    
    delete_api = client.delete_api()
    
    try:
        # Delete all data from the measurement
        start = "1970-01-01T00:00:00Z"
        stop = datetime.now().isoformat() + "Z"
        
        delete_api.delete(
            start=start,
            stop=stop,
            predicate='_measurement="energy_consumption"',
            bucket=INFLUXDB_BUCKET,
            org=INFLUXDB_ORG
        )
        
        print("✓ Cleared existing data")
    except Exception as e:
        print(f"⚠️  Could not clear data: {e}")
    finally:
        client.close()


def load_csv_to_influxdb():
    """Load CSV data into InfluxDB"""
    
    print("=" * 60)
    print("Loading Energy Data to InfluxDB")
    print("=" * 60)
    
    # Check if CSV file exists
    if not os.path.exists(CSV_FILE):
        print(f"❌ Error: CSV file not found at {CSV_FILE}")
        return
    
    # Read CSV
    print(f"\n📁 Reading CSV file: {CSV_FILE}")
    df = pd.read_csv(CSV_FILE)
    print(f"✓ Loaded {len(df)} records")
    
    # Display sample data
    print(f"\n📊 Sample data:")
    print(df.head())
    print(f"\n📋 Columns: {', '.join(df.columns)}")
    
    # Convert Timestamp column to datetime
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        # Shift timestamps to current dates (last 1000 hours ending now)
        oldest_timestamp = df['Timestamp'].min()
        current_end_time = datetime.now()
        start_time = current_end_time - timedelta(hours=len(df))
        time_shift = start_time - oldest_timestamp
        df['Timestamp'] = df['Timestamp'] + time_shift
        print(f"✓ Shifted timestamps to current dates: {df['Timestamp'].min()} to {df['Timestamp'].max()}")
    else:
        print("\n⚠️ No Timestamp column found, using sequential timestamps")
        # Create timestamps: one record per hour starting from now
        start_time = datetime.now() - timedelta(hours=len(df))
        df['Timestamp'] = [start_time + timedelta(hours=i) for i in range(len(df))]
    
    # Connect to InfluxDB
    if not INFLUXDB_TOKEN:
        print("❌ Error: INFLUXDB_TOKEN environment variable is not set")
        return
    
    print(f"\n🔌 Connecting to InfluxDB at {INFLUXDB_URL}")
    client = InfluxDBClient(
        url=INFLUXDB_URL,
        token=INFLUXDB_TOKEN,
        org=INFLUXDB_ORG
    )
    
    # Get write API
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
    # Day of week mapping
    day_map = {
        'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
        'Friday': 4, 'Saturday': 5, 'Sunday': 6
    }
    
    # Prepare data points
    print(f"\n📝 Preparing data points...")
    points = []
    
    for idx, (index, row) in enumerate(df.iterrows()):
        # Convert day of week to number
        day_val = row.get('DayOfWeek', 0)
        if isinstance(day_val, str):
            day_val = day_map.get(day_val, 0)
        
        # Create a point for each record
        point = (Point("energy_consumption")
            .time(row['Timestamp'])
            .tag("device_id", f"device_{idx % 10}")
            .field("consumption", float(row.get('EnergyConsumption', 0)))
            .field("temperature", float(row.get('Temperature', 0)))
            .field("humidity", float(row.get('Humidity', 0)))
            .field("square_footage", float(row.get('SquareFootage', 1000)))
            .field("occupancy", int(row.get('Occupancy', 0)))
            .field("hvac_usage", 1 if row.get('HVACUsage') == 'On' else 0)
            .field("lighting_usage", 1 if row.get('LightingUsage') == 'On' else 0)
            .field("renewable_energy", float(row.get('RenewableEnergy', 0)))
            .field("day_of_week", int(day_val))
            .field("holiday", 1 if row.get('Holiday') == 'Yes' else 0))
        
        points.append(point)
    
    print(f"✓ Prepared {len(points)} data points")
    
    # Write to InfluxDB
    print(f"\n💾 Writing to InfluxDB bucket: {INFLUXDB_BUCKET}")
    try:
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=points)
        print(f"✅ Successfully wrote {len(points)} points to InfluxDB!")
    except Exception as e:
        print(f"❌ Error writing to InfluxDB: {e}")
        client.close()
        return
    
    # Verify data was written
    print(f"\n🔍 Verifying data...")
    query_api = client.query_api()
    query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: -365d)
        |> filter(fn: (r) => r._measurement == "energy_consumption")
        |> count()
    '''
    
    try:
        result = query_api.query(query=query, org=INFLUXDB_ORG)
        total_records = 0
        for table in result:
            for record in table.records:
                total_records += record.get_value()
        
        print(f"✓ Verified: {total_records} records in InfluxDB")
    except Exception as e:
        print(f"⚠️  Could not verify (but data was written): {e}")
    
    # Close connection
    client.close()
    
    print(f"\n" + "=" * 60)
    print("✅ Data loading complete!")
    print("=" * 60)
    print(f"\nNext steps:")
    print(f"1. Visit http://localhost:8086 to explore data")
    print(f"2. Test your API endpoints:")
    print(f"   - GET http://127.0.0.1:8000/api/v1/energy/statistics?period=week")
    print(f"   - GET http://127.0.0.1:8000/api/v1/energy/readings")
    print(f"3. Check your frontend Dashboard for real data!")


if __name__ == "__main__":
    clear_existing_data()
    load_csv_to_influxdb()
