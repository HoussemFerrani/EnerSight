"""
Energy Data Repository
Concrete implementation for energy consumption data access
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from influxdb_client.client.write.point import Point
from influxdb_client.client.write_api_async import WriteApiAsync

from backend.repositories.base import TimeSeriesRepository
from backend.core.logging import get_logger
from backend.core.exceptions import DatabaseQueryError

logger = get_logger(__name__)


class EnergyDataRepository(TimeSeriesRepository):
    """
    Repository for energy consumption time-series data
    Implements data access layer for InfluxDB
    """
    
    def __init__(self, influxdb_client: InfluxDBClientAsync, bucket: str, org: str):
        """
        Initialize energy data repository
        
        Args:
            influxdb_client: InfluxDB async client
            bucket: InfluxDB bucket for energy data
            org: InfluxDB organization
        """
        super().__init__(influxdb_client, bucket, org)
        self.measurement_name = "energy_consumption"
    
    async def write_measurement(
        self,
        measurement: str,
        tags: dict,
        fields: dict,
        timestamp: datetime
    ) -> None:
        """
        Write energy measurement to InfluxDB
        
        Args:
            measurement: Measurement name (default: "energy_consumption")
            tags: Tags (e.g., {"device_id": "sensor_1", "location": "lab"})
            fields: Fields (e.g., {"temperature": 22.5, "consumption": 1250.3})
            timestamp: Measurement timestamp
        """
        try:
            write_api: WriteApiAsync = self.client.write_api()
            
            point = Point(measurement) \
                .time(timestamp)
            
            # Add tags
            for tag_key, tag_value in tags.items():
                point = point.tag(tag_key, tag_value)
            
            # Add fields
            for field_key, field_value in fields.items():
                point = point.field(field_key, field_value)
            
            await write_api.write(bucket=self.bucket, org=self.org, record=point)
            
            logger.debug(f"Wrote measurement: {measurement} at {timestamp}")
        
        except Exception as e:
            logger.error(f"Failed to write measurement: {e}")
            raise DatabaseQueryError(f"Failed to write to InfluxDB: {str(e)}")
    
    async def write_batch(self, data_points: List[Dict[str, Any]]) -> None:
        """
        Write multiple energy measurements in batch
        
        Args:
            data_points: List of data points, each containing:
                - tags: Dict of tags
                - fields: Dict of fields
                - timestamp: Datetime
        """
        try:
            write_api: WriteApiAsync = self.client.write_api()
            
            points = []
            for data in data_points:
                point = Point(self.measurement_name) \
                    .time(data["timestamp"])
                
                for tag_key, tag_value in data.get("tags", {}).items():
                    point = point.tag(tag_key, tag_value)
                
                for field_key, field_value in data.get("fields", {}).items():
                    point = point.field(field_key, field_value)
                
                points.append(point)
            
            await write_api.write(bucket=self.bucket, org=self.org, record=points)
            
            logger.info(f"Wrote {len(points)} measurements in batch")
        
        except Exception as e:
            logger.error(f"Failed to write batch: {e}")
            raise DatabaseQueryError(f"Failed to write batch to InfluxDB: {str(e)}")
    
    async def query_range(
        self,
        measurement: str,
        start: datetime,
        stop: datetime,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[dict]:
        """
        Query energy data within time range
        
        Args:
            measurement: Measurement name
            start: Start timestamp
            stop: Stop timestamp
            filters: Optional tag filters (e.g., {"device_id": "sensor_1"})
        
        Returns:
            List of data points with timestamp and field values
        """
        try:
            query_api = self.client.query_api()
            
            # Build Flux query
            flux_query = f'''
                from(bucket: "{self.bucket}")
                    |> range(start: {start.isoformat()}Z, stop: {stop.isoformat()}Z)
                    |> filter(fn: (r) => r["_measurement"] == "{measurement}")
            '''
            
            # Add tag filters
            if filters:
                for tag_key, tag_value in filters.items():
                    flux_query += f'\n    |> filter(fn: (r) => r["{tag_key}"] == "{tag_value}")'
            
            # Execute query
            tables = await query_api.query(flux_query, org=self.org)
            
            # Parse results
            results = []
            for table in tables:
                for record in table.records:
                    results.append({
                        "time": record.get_time(),
                        "field": record.get_field(),
                        "value": record.get_value(),
                        **{k: v for k, v in record.values.items() if k not in ["_time", "_field", "_value"]}
                    })
            
            logger.debug(f"Query returned {len(results)} records")
            return results
        
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise DatabaseQueryError(f"Failed to query InfluxDB: {str(e)}")
    
    async def aggregate(
        self,
        measurement: str,
        start: datetime,
        stop: datetime,
        aggregation: str = "mean",
        window: str = "1h"
    ) -> List[dict]:
        """
        Aggregate energy data over time windows
        
        Args:
            measurement: Measurement name
            start: Start timestamp
            stop: Stop timestamp
            aggregation: Aggregation function (mean, sum, max, min, median)
            window: Time window (e.g., "1h", "1d", "5m")
        
        Returns:
            List of aggregated data points
        """
        try:
            query_api = self.client.query_api()
            
            # Map aggregation to Flux function
            agg_functions = {
                "mean": "mean",
                "sum": "sum",
                "max": "max",
                "min": "min",
                "median": "median",
                "count": "count",
            }
            
            agg_func = agg_functions.get(aggregation, "mean")
            
            # Build Flux query with aggregation
            flux_query = f'''
                from(bucket: "{self.bucket}")
                    |> range(start: {start.isoformat()}Z, stop: {stop.isoformat()}Z)
                    |> filter(fn: (r) => r["_measurement"] == "{measurement}")
                    |> aggregateWindow(every: {window}, fn: {agg_func}, createEmpty: false)
                    |> yield(name: "{aggregation}")
            '''
            
            # Execute query
            tables = await query_api.query(flux_query, org=self.org)
            
            # Parse results
            results = []
            for table in tables:
                for record in table.records:
                    results.append({
                        "time": record.get_time(),
                        "field": record.get_field(),
                        "value": record.get_value(),
                        "aggregation": aggregation,
                        "window": window,
                    })
            
            logger.debug(f"Aggregation returned {len(results)} windows")
            return results
        
        except Exception as e:
            logger.error(f"Aggregation failed: {e}")
            raise DatabaseQueryError(f"Failed to aggregate data: {str(e)}")
    
    async def get_latest(self, measurement: str, limit: int = 10) -> List[dict]:
        """
        Get latest N measurements
        
        Args:
            measurement: Measurement name
            limit: Number of latest records to return
        
        Returns:
            List of latest data points
        """
        try:
            query_api = self.client.query_api()
            
            flux_query = f'''
                from(bucket: "{self.bucket}")
                    |> range(start: -7d)
                    |> filter(fn: (r) => r["_measurement"] == "{measurement}")
                    |> sort(columns: ["_time"], desc: true)
                    |> limit(n: {limit})
            '''
            
            tables = await query_api.query(flux_query, org=self.org)
            
            results = []
            for table in tables:
                for record in table.records:
                    results.append({
                        "time": record.get_time(),
                        "field": record.get_field(),
                        "value": record.get_value(),
                    })
            
            return results
        
        except Exception as e:
            logger.error(f"Failed to get latest measurements: {e}")
            raise DatabaseQueryError(f"Failed to get latest data: {str(e)}")
