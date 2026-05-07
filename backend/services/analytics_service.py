"""
Enhanced analytics service for advanced data processing
"""
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import pandas as pd
from influxdb_client import InfluxDBClient

from backend.database.influxdb_client import influx_db
from backend.schemas.analytics import (
    AggregatedData,
    AnalyticsSummary,
    ComparisonResult,
    CostCalculation,
    AggregationPeriod
)


class AnalyticsService:
    """Service for enhanced analytics operations"""
    
    def __init__(self):
        self.query_api = influx_db.query_api
        self.bucket = "energy_data"
    
    def get_data_range(
        self,
        start_date: datetime,
        end_date: datetime,
        aggregation: Optional[str] = None
    ) -> List[dict]:
        """Get energy data for a specific date range with optional aggregation"""
        
        if aggregation:
            window_size = self._get_window_size(aggregation)
            query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: {start_date.isoformat()}Z, stop: {end_date.isoformat()}Z)
              |> filter(fn: (r) => r["_measurement"] == "energy_consumption")
              |> filter(fn: (r) => r["_field"] == "value")
              |> aggregateWindow(every: {window_size}, fn: sum, createEmpty: false)
            '''
        else:
            query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: {start_date.isoformat()}Z, stop: {end_date.isoformat()}Z)
              |> filter(fn: (r) => r["_measurement"] == "energy_consumption")
              |> filter(fn: (r) => r["_field"] == "value")
            '''
        
        tables = self.query_api.query(query)
        
        data = []
        for table in tables:
            for record in table.records:
                data.append({
                    "timestamp": record.get_time().isoformat(),
                    "value": float(record.get_value()),
                    "unit": "kWh"
                })
        
        return data
    
    def get_aggregated_data(
        self,
        start_date: datetime,
        end_date: datetime,
        period: AggregationPeriod
    ) -> List[AggregatedData]:
        """Get aggregated energy data by period"""
        
        window_size = self._get_window_size(period.value)
        
        query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: {start_date.isoformat()}Z, stop: {end_date.isoformat()}Z)
          |> filter(fn: (r) => r["_measurement"] == "energy_consumption")
          |> filter(fn: (r) => r["_field"] == "value")
          |> aggregateWindow(every: {window_size}, fn: mean, createEmpty: false)
        '''
        
        tables = self.query_api.query(query)
        
        # Group data by periods
        results = []
        for table in tables:
            for record in table.records:
                period_time = record.get_time()
                value = float(record.get_value())
                
                # Calculate period boundaries
                period_start, period_end = self._get_period_boundaries(period_time, period)
                
                results.append(AggregatedData(
                    period_start=period_start,
                    period_end=period_end,
                    total=value,
                    average=value,
                    min=value,
                    max=value,
                    count=1
                ))
        
        return results
    
    def calculate_cost(
        self,
        start_date: datetime,
        end_date: datetime,
        cost_per_kwh: float = 0.12
    ) -> CostCalculation:
        """Calculate energy cost for a period"""
        
        query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: {start_date.isoformat()}Z, stop: {end_date.isoformat()}Z)
          |> filter(fn: (r) => r["_measurement"] == "energy_consumption")
          |> filter(fn: (r) => r["_field"] == "value")
          |> sum()
        '''
        
        tables = self.query_api.query(query)
        
        total_kwh = 0.0
        for table in tables:
            for record in table.records:
                total_kwh += float(record.get_value())
        
        total_cost = total_kwh * cost_per_kwh
        
        return CostCalculation(
            period_start=start_date,
            period_end=end_date,
            total_kwh=total_kwh,
            cost_per_kwh=cost_per_kwh,
            total_cost=total_cost,
            currency="USD"
        )
    
    def get_summary(
        self,
        start_date: datetime,
        end_date: datetime,
        cost_per_kwh: Optional[float] = None
    ) -> AnalyticsSummary:
        """Get comprehensive analytics summary"""
        
        # Get all data points
        data = self.get_data_range(start_date, end_date)
        
        if not data:
            return AnalyticsSummary(
                total_consumption=0.0,
                average_daily=0.0,
                peak_consumption=0.0,
                peak_timestamp=start_date,
                lowest_consumption=0.0,
                lowest_timestamp=start_date,
                period_start=start_date,
                period_end=end_date,
                data_points=0
            )
        
        # Calculate statistics
        values = [d["value"] for d in data]
        total = sum(values)
        days = (end_date - start_date).days or 1
        avg_daily = total / days
        
        # Find peak and lowest
        peak_idx = values.index(max(values))
        lowest_idx = values.index(min(values))
        
        peak_timestamp = datetime.fromisoformat(data[peak_idx]["timestamp"].replace("Z", "+00:00"))
        lowest_timestamp = datetime.fromisoformat(data[lowest_idx]["timestamp"].replace("Z", "+00:00"))
        
        # Calculate cost if requested
        total_cost = None
        if cost_per_kwh:
            total_cost = total * cost_per_kwh
        
        return AnalyticsSummary(
            total_consumption=total,
            average_daily=avg_daily,
            peak_consumption=max(values),
            peak_timestamp=peak_timestamp,
            lowest_consumption=min(values),
            lowest_timestamp=lowest_timestamp,
            total_cost=total_cost,
            period_start=start_date,
            period_end=end_date,
            data_points=len(data)
        )
    
    def compare_periods(
        self,
        current_start: datetime,
        current_end: datetime,
        comparison_type: str = "previous_period"
    ) -> ComparisonResult:
        """Compare current period with another period"""
        
        # Calculate comparison period dates
        period_duration = current_end - current_start
        
        if comparison_type == "previous_period":
            comp_start = current_start - period_duration
            comp_end = current_start
        elif comparison_type == "same_period_last_month":
            comp_start = current_start - timedelta(days=30)
            comp_end = current_end - timedelta(days=30)
        elif comparison_type == "same_period_last_year":
            comp_start = current_start - timedelta(days=365)
            comp_end = current_end - timedelta(days=365)
        else:
            raise ValueError(f"Invalid comparison type: {comparison_type}")
        
        # Get data for both periods
        current_data = self.get_data_range(current_start, current_end)
        comparison_data = self.get_data_range(comp_start, comp_end)
        
        # Calculate aggregates
        current_total = sum(d["value"] for d in current_data)
        current_avg = current_total / len(current_data) if current_data else 0
        
        comp_total = sum(d["value"] for d in comparison_data)
        comp_avg = comp_total / len(comparison_data) if comparison_data else 0
        
        # Calculate difference and percentage
        difference = current_total - comp_total
        percentage_change = (difference / comp_total * 100) if comp_total > 0 else 0
        
        current_agg = AggregatedData(
            period_start=current_start,
            period_end=current_end,
            total=current_total,
            average=current_avg,
            min=min((d["value"] for d in current_data), default=0),
            max=max((d["value"] for d in current_data), default=0),
            count=len(current_data)
        )
        
        comparison_agg = AggregatedData(
            period_start=comp_start,
            period_end=comp_end,
            total=comp_total,
            average=comp_avg,
            min=min((d["value"] for d in comparison_data), default=0),
            max=max((d["value"] for d in comparison_data), default=0),
            count=len(comparison_data)
        )
        
        return ComparisonResult(
            current_period=current_agg,
            comparison_period=comparison_agg,
            difference=difference,
            percentage_change=percentage_change,
            comparison_type=comparison_type
        )
    
    def export_to_csv(
        self,
        start_date: datetime,
        end_date: datetime,
        aggregation: Optional[str] = None
    ) -> str:
        """Export data to CSV format"""
        
        data = self.get_data_range(start_date, end_date, aggregation)
        
        if not data:
            return "timestamp,value,unit\n"
        
        # Convert to CSV
        csv_lines = ["timestamp,value,unit"]
        for row in data:
            csv_lines.append(f"{row['timestamp']},{row['value']},{row['unit']}")
        
        return "\n".join(csv_lines)
    
    def _get_window_size(self, period: str) -> str:
        """Get InfluxDB window size for aggregation period"""
        mapping = {
            "hour": "1h",
            "day": "1d",
            "week": "7d",
            "month": "30d",
            "year": "365d"
        }
        return mapping.get(period, "1h")
    
    def _get_period_boundaries(
        self,
        timestamp: datetime,
        period: AggregationPeriod
    ) -> Tuple[datetime, datetime]:
        """Get start and end boundaries for a period"""
        
        if period == AggregationPeriod.HOUR:
            start = timestamp.replace(minute=0, second=0, microsecond=0)
            end = start + timedelta(hours=1)
        elif period == AggregationPeriod.DAY:
            start = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif period == AggregationPeriod.WEEK:
            start = timestamp - timedelta(days=timestamp.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
        elif period == AggregationPeriod.MONTH:
            start = timestamp.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1)
            else:
                end = start.replace(month=start.month + 1)
        else:  # YEAR
            start = timestamp.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start.replace(year=start.year + 1)
        
        return start, end


# Singleton instance
analytics_service = AnalyticsService()
