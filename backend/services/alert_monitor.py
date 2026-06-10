"""
Alert monitoring service.

Polls energy consumption in `public.energy_readings` and creates `public.alerts`
when the rolling-window total exceeds the user's preference threshold, or when
the Isolation Forest flags anomalous readings. The user's email is fetched from
`auth.users` since Supabase Auth owns credentials.

Alerts are EDGE-TRIGGERED: an alert (and its email) fires the moment a
condition starts, stays silent while the same condition persists, and re-arms
as soon as the condition clears — so every alert means a NEW problem.

Controlled via env:
  ALERT_CHECK_INTERVAL_SECONDS - seconds between checks (default 60)
  ALERT_WINDOW_MINUTES         - rolling consumption window (default 10)
  ALERT_COOLDOWN_MINUTES       - anti-flapping floor between alerts of the
                                 same type (default 5)

The threshold compares against the WINDOW total: with the simulator at 60s
(~78 kWh/reading), a 10-minute window sums to ~780 kWh on average.

Note: `energy_readings` has no user_id — it is a single household's sensor
stream, so consumption totals and anomalies are global by design and compared
against each active user's own preferences.
"""
import asyncio
import os
from datetime import datetime, timedelta

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from backend.core.logging import get_logger
from backend.database.postgres import SessionLocal
from backend.models.alert import Alert, AlertSeverity, AlertStatus, AlertType
from backend.models.energy import EnergyReading
from backend.models.user import Profile, UserPreferences
from backend.services.email_service import email_service

logger = get_logger(__name__)


class AlertMonitorService:
    """Periodically checks for threshold breaches and anomalous readings."""

    def __init__(self):
        self.is_running = False
        self.check_interval = int(os.getenv("ALERT_CHECK_INTERVAL_SECONDS", "60"))
        self.window_minutes = int(os.getenv("ALERT_WINDOW_MINUTES", "10"))
        self.cooldown_minutes = int(os.getenv("ALERT_COOLDOWN_MINUTES", "5"))
        # Edge-trigger state: alert fires the moment a condition STARTS, stays
        # silent while it persists, and re-arms once the condition clears.
        self._breaching: dict = {}  # user_id -> bool (threshold currently exceeded)
        self._anomaly_active = False

    async def start(self):
        self.is_running = True
        logger.info("Alert monitoring service started")
        while self.is_running:
            try:
                await self.check_all_users()
            except Exception as e:
                logger.error(f"Error in threshold monitoring: {e}")
            try:
                await self.check_anomalies()
            except Exception as e:
                logger.error(f"Error in anomaly monitoring: {e}")
            await asyncio.sleep(self.check_interval)

    def stop(self):
        self.is_running = False
        logger.info("Alert monitoring service stopped")

    DEFAULT_THRESHOLD_KWH = 500.0

    def _notifiable_users(self, db: Session):
        """
        Active users who opted into email notifications. Users without a
        user_preferences row are included with defaults (notifications on),
        so a missing prefs row never silently disables alerts.
        """
        return (
            db.query(Profile, UserPreferences)
            .outerjoin(UserPreferences, UserPreferences.user_id == Profile.id)
            .filter(Profile.is_active.is_(True))
            .filter(
                (UserPreferences.email_notifications.is_(True))
                | (UserPreferences.user_id.is_(None))
            )
            .all()
        )

    @staticmethod
    def _get_user_email(db: Session, user_id) -> str | None:
        # Email lives in auth.users (Supabase) — fetch it via raw SQL.
        row = db.execute(
            text("select email from auth.users where id = :uid"),
            {"uid": str(user_id)},
        ).first()
        return row[0] if row else None

    def _has_recent_alert(self, db: Session, user_id, alert_type: str) -> bool:
        """Anti-flapping floor: minimum gap between alerts of the same type."""
        return (
            db.query(Alert)
            .filter(
                Alert.user_id == user_id,
                Alert.alert_type == alert_type,
                Alert.created_at >= datetime.utcnow() - timedelta(minutes=self.cooldown_minutes),
            )
            .first()
            is not None
        )

    async def check_all_users(self):
        db = SessionLocal()
        try:
            users = self._notifiable_users(db)
            logger.debug(f"Checking threshold alerts for {len(users)} users")
            for user, prefs in users:
                try:
                    threshold = (
                        float(prefs.alert_threshold_kwh or 0)
                        if prefs is not None
                        else self.DEFAULT_THRESHOLD_KWH
                    )
                    if threshold <= 0:
                        continue
                    await self.check_user_consumption(db, user, threshold)
                except Exception as e:
                    logger.error(f"Error checking user {user.id}: {e}")
        finally:
            db.close()

    async def check_user_consumption(self, db: Session, user: Profile, threshold: float):
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=self.window_minutes)

            total_consumption = (
                db.query(func.coalesce(func.sum(EnergyReading.consumption), 0.0))
                .filter(EnergyReading.recorded_at >= start_time, EnergyReading.recorded_at < end_time)
                .scalar()
            ) or 0.0
            total_consumption = float(total_consumption)

            breaching = total_consumption > threshold
            was_breaching = self._breaching.get(user.id, False)
            self._breaching[user.id] = breaching

            if not breaching:
                return
            if was_breaching:
                # Ongoing breach already alerted; re-arms when consumption recovers.
                return
            if self._has_recent_alert(db, user.id, AlertType.THRESHOLD_EXCEEDED.value):
                logger.debug(f"Skipping threshold alert for {user.username} (anti-flap cooldown)")
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
                    f"threshold ({threshold:.2f} kWh) in the last {self.window_minutes} minutes."
                ),
                current_value=total_consumption,
                threshold_value=threshold,
            )
            db.add(alert)
            db.commit()
            db.refresh(alert)
            logger.info(
                f"Threshold alert created for {user.username}: "
                f"{total_consumption:.2f} > {threshold:.2f} kWh"
            )

            email = self._get_user_email(db, user.id)
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
            logger.error(f"Error checking consumption for user {user.id}: {e}")

    async def check_anomalies(self):
        """Run the Isolation Forest over the rolling window and email anomaly alerts."""
        try:
            from backend.core.dependencies import get_model_registry
            registry = get_model_registry()
            try:
                detector = registry.get_model("anomaly_detector")
            except ValueError:
                # Registry is populated during app startup; register the loader
                # ourselves so the monitor doesn't depend on startup ordering.
                from backend.ml.model_loaders import load_anomaly_detector
                registry.register_model("anomaly_detector", load_anomaly_detector)
                detector = registry.get_model("anomaly_detector")
        except Exception as e:
            logger.warning(f"Anomaly detector unavailable, skipping anomaly alerts: {e}")
            return

        from backend.services.energy_service import build_anomaly_features

        db = SessionLocal()
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=self.window_minutes)
            readings = (
                db.query(EnergyReading)
                .filter(EnergyReading.recorded_at >= start_time, EnergyReading.recorded_at < end_time)
                .order_by(EnergyReading.recorded_at)
                .all()
            )
            if not readings:
                return

            data = []
            for r in readings:
                row = r.to_dict()
                row["time"] = row.pop("recorded_at")
                data.append(row)

            predictions, scores = detector.detect(build_anomaly_features(data))
            anomalous = [
                (data[i], float(scores[i]))
                for i, pred in enumerate(predictions)
                if pred == -1
            ]

            was_active = self._anomaly_active
            self._anomaly_active = bool(anomalous)

            if not anomalous:
                return
            if was_active:
                # Ongoing anomalous period already alerted; re-arms once clean.
                return

            worst_record, worst_score = min(anomalous, key=lambda item: item[1])
            logger.info(
                f"{len(anomalous)} anomalous readings in the last {self.window_minutes} minutes "
                f"(worst score {worst_score:.3f})"
            )

            # Same severity bands as the /anomalies API.
            if worst_score < -0.2:
                severity = AlertSeverity.CRITICAL.value
            elif worst_score < -0.1:
                severity = AlertSeverity.WARNING.value
            else:
                severity = AlertSeverity.INFO.value

            for user, prefs in self._notifiable_users(db):
                if self._has_recent_alert(db, user.id, AlertType.ANOMALY_DETECTED.value):
                    logger.debug(f"Skipping anomaly alert for {user.username} (anti-flap cooldown)")
                    continue

                alert = Alert(
                    user_id=user.id,
                    alert_type=AlertType.ANOMALY_DETECTED.value,
                    severity=severity,
                    status=AlertStatus.PENDING.value,
                    title="Anomaly Detected in Energy Consumption",
                    message=(
                        f"{len(anomalous)} unusual reading(s) detected in the last "
                        f"{self.window_minutes} minutes. "
                        f"Worst anomaly score: {worst_score:.3f} "
                        f"(consumption {worst_record.get('consumption', 0.0):.2f} kWh)."
                    ),
                    current_value=float(worst_record.get("consumption") or 0.0),
                )
                db.add(alert)
                db.commit()
                db.refresh(alert)
                logger.info(f"Anomaly alert created for {user.username}")

                email = self._get_user_email(db, user.id)
                if email:
                    sent = email_service.send_anomaly_alert(
                        to_email=email,
                        username=str(user.username),
                        anomaly_score=worst_score,
                        timestamp=datetime.utcnow(),
                    )
                    if sent:
                        alert.email_sent = True
                        alert.sent_at = datetime.utcnow()
                        alert.status = AlertStatus.SENT.value
                        db.commit()
        except Exception as e:
            logger.error(f"Error during anomaly monitoring: {e}")
        finally:
            db.close()


alert_monitor = AlertMonitorService()
