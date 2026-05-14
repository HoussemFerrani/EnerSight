"""
Alert monitoring service.

Polls energy consumption in `public.energy_readings` and creates `public.alerts`
when a user's hourly total exceeds their preference threshold. The user's email
is fetched from `auth.users` since Supabase Auth owns credentials.
"""
import asyncio
from datetime import datetime, timedelta

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from backend.database.postgres import SessionLocal
from backend.models.alert import Alert, AlertSeverity, AlertStatus, AlertType
from backend.models.energy import EnergyReading
from backend.models.user import Profile, UserPreferences
from backend.services.email_service import email_service


class AlertMonitorService:
    """Periodically checks all users for threshold breaches."""

    def __init__(self):
        self.is_running = False
        self.check_interval = 300  # seconds

    async def start(self):
        self.is_running = True
        print("Alert monitoring service started")
        while self.is_running:
            try:
                await self.check_all_users()
            except Exception as e:
                print(f"Error in alert monitoring: {e}")
            await asyncio.sleep(self.check_interval)

    def stop(self):
        self.is_running = False
        print("Alert monitoring service stopped")

    async def check_all_users(self):
        db = SessionLocal()
        try:
            users = (
                db.query(Profile, UserPreferences)
                .join(UserPreferences, UserPreferences.user_id == Profile.id)
                .filter(Profile.is_active.is_(True))
                .filter(UserPreferences.email_notifications.is_(True))
                .all()
            )
            print(f"Checking alerts for {len(users)} users...")
            for user, prefs in users:
                try:
                    threshold = float(prefs.alert_threshold_kwh or 0)
                    if threshold <= 0:
                        continue
                    await self.check_user_consumption(db, user, threshold)
                except Exception as e:
                    print(f"Error checking user {user.id}: {e}")
        finally:
            db.close()

    async def check_user_consumption(self, db: Session, user: Profile, threshold: float):
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)

            total_consumption = (
                db.query(func.coalesce(func.sum(EnergyReading.consumption), 0.0))
                .filter(EnergyReading.recorded_at >= start_time, EnergyReading.recorded_at < end_time)
                .scalar()
            ) or 0.0
            total_consumption = float(total_consumption)

            if total_consumption <= threshold:
                return

            recent_alert = (
                db.query(Alert)
                .filter(
                    Alert.user_id == user.id,
                    Alert.alert_type == AlertType.THRESHOLD_EXCEEDED.value,
                    Alert.created_at >= datetime.utcnow() - timedelta(hours=1),
                )
                .first()
            )
            if recent_alert:
                print(f"Skipping alert for {user.username} (recent alert exists)")
                return

            severity = (
                AlertSeverity.CRITICAL.value
                if total_consumption >= threshold * 1.5
                else AlertSeverity.WARNING.value
            )
            alert = Alert(
                user_id=user.id,
                alert_type=AlertType.THRESHOLD_EXCEEDED.value,
                severity=severity,
                status=AlertStatus.PENDING.value,
                title="Energy Consumption Alert",
                message=(
                    f"Your energy consumption ({total_consumption:.2f} kWh) exceeded your "
                    f"threshold ({threshold:.2f} kWh) in the last hour."
                ),
                current_value=total_consumption,
                threshold_value=threshold,
            )
            db.add(alert)
            db.commit()
            db.refresh(alert)
            print(f"Alert created for {user.username}: {total_consumption:.2f} > {threshold:.2f}")

            # Email lives in auth.users (Supabase) — fetch it via raw SQL.
            email_row = db.execute(
                text("select email from auth.users where id = :uid"),
                {"uid": str(user.id)},
            ).first()
            email = email_row[0] if email_row else None
            if email:
                sent = email_service.send_threshold_alert(
                    to_email=email,
                    username=str(user.username),
                    current_value=total_consumption,
                    threshold_value=threshold,
                    timestamp=datetime.utcnow(),
                )
                if sent:
                    alert.email_sent = True
                    alert.sent_at = datetime.utcnow()
                    alert.status = AlertStatus.SENT.value
                    db.commit()
        except Exception as e:
            print(f"Error checking consumption for user {user.id}: {e}")

    async def check_anomalies(self):
        """Placeholder for anomaly-driven alerts."""
        pass


alert_monitor = AlertMonitorService()
