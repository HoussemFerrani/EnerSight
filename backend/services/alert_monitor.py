"""
Alert monitoring service - checks energy consumption against thresholds
"""
import asyncio
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.database.postgres import SessionLocal
from backend.database.influxdb_client import influx_db
from backend.models.user import User
from backend.models.alert import Alert, AlertType, AlertSeverity, AlertStatus
from backend.services.email_service import email_service


class AlertMonitorService:
    """Service for monitoring energy consumption and triggering alerts"""
    
    def __init__(self):
        self.is_running = False
        self.check_interval = 300  # 5 minutes
    
    async def start(self):
        """Start the alert monitoring service"""
        self.is_running = True
        print("🚨 Alert monitoring service started")
        
        while self.is_running:
            try:
                await self.check_all_users()
            except Exception as e:
                print(f"❌ Error in alert monitoring: {str(e)}")
            
            # Wait before next check
            await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """Stop the alert monitoring service"""
        self.is_running = False
        print("🛑 Alert monitoring service stopped")
    
    async def check_all_users(self):
        """Check energy consumption for all users with alerts enabled"""
        db = SessionLocal()
        
        try:
            # Get all active users with alert notifications enabled
            users = db.query(User).filter(
                User.is_active == True,
                User.preferences.has()  # Has preferences
            ).all()
            
            print(f"🔍 Checking alerts for {len(users)} users...")
            
            for user in users:
                try:
                    # Get user preferences
                    prefs = user.preferences
                    if not prefs:
                        continue
                    
                    # Check if email notifications are enabled
                    email_enabled = bool(prefs.email_notifications)
                    
                    if not email_enabled:
                        continue
                    
                    # Get threshold from preferences
                    threshold = float(prefs.alert_threshold_kwh) if prefs.alert_threshold_kwh else None
                    
                    if not threshold or threshold <= 0:
                        continue
                    
                    # Check consumption against threshold
                    await self.check_user_consumption(db, user, threshold)
                    
                except Exception as e:
                    print(f"❌ Error checking user {user.id}: {str(e)}")
                    continue
        
        finally:
            db.close()
    
    async def check_user_consumption(self, db: Session, user: User, threshold: float):
        """Check energy consumption for a specific user"""
        try:
            # Get recent energy consumption from InfluxDB (last hour)
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            
            # Query InfluxDB for energy data
            query = f'''
            from(bucket: "energy_data")
              |> range(start: {start_time.isoformat()}Z, stop: {end_time.isoformat()}Z)
              |> filter(fn: (r) => r["_measurement"] == "energy_consumption")
              |> filter(fn: (r) => r["_field"] == "value")
              |> sum()
            '''
            
            tables = influx_db.query_api.query(query)
            
            if not tables or len(tables) == 0:
                return
            
            # Get total consumption for the hour
            total_consumption = 0
            for table in tables:
                for record in table.records:
                    total_consumption += float(record.get_value())
            
            # Check if consumption exceeds threshold
            if total_consumption > threshold:
                # Check if we already sent an alert recently (avoid spam)
                recent_alert = db.query(Alert).filter(
                    Alert.user_id == int(user.id),
                    Alert.alert_type == AlertType.THRESHOLD_EXCEEDED,
                    Alert.created_at >= datetime.utcnow() - timedelta(hours=1)
                ).first()
                
                if recent_alert:
                    print(f"⏭️  Skipping alert for user {user.username} (already alerted recently)")
                    return
                
                # Create alert
                alert = Alert(
                    user_id=int(user.id),
                    alert_type=AlertType.THRESHOLD_EXCEEDED,
                    severity=AlertSeverity.WARNING if total_consumption < threshold * 1.5 else AlertSeverity.CRITICAL,
                    status=AlertStatus.PENDING,
                    title="Energy Consumption Alert",
                    message=f"Your energy consumption ({total_consumption:.2f} kWh) has exceeded your threshold ({threshold:.2f} kWh) in the last hour.",
                    current_value=total_consumption,
                    threshold_value=threshold
                )
                
                db.add(alert)
                db.commit()
                db.refresh(alert)
                
                print(f"⚠️  Alert created for user {user.username}: {total_consumption:.2f} kWh > {threshold:.2f} kWh")
                
                # Send email notification
                if user.preferences and bool(user.preferences.email_notifications):
                    email_sent = email_service.send_threshold_alert(
                        to_email=str(user.email),
                        username=str(user.username),
                        current_value=total_consumption,
                        threshold_value=threshold,
                        timestamp=datetime.utcnow()
                    )
                    
                    if email_sent:
                        alert.email_sent = True
                        alert.sent_at = datetime.utcnow()
                        alert.status = AlertStatus.SENT
                        db.commit()
        
        except Exception as e:
            print(f"❌ Error checking consumption for user {user.id}: {str(e)}")
    
    async def check_anomalies(self):
        """Check for anomalies and send alerts - can be extended"""
        # This can be integrated with the anomaly detection system
        # For now, it's a placeholder for future enhancement
        pass


# Singleton instance
alert_monitor = AlertMonitorService()
