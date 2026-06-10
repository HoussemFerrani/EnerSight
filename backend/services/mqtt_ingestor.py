"""
MQTT ingestion service.

Subscribes to the sensor topic and persists every message into
`public.energy_readings` — the missing consumer half of the MQTT pipeline
(scripts/mqtt_simulator.py is the publisher half).

Expected JSON payload (the simulator's format):
{
    "timestamp": "...", "temperature": 24.0, "humidity": 50.0,
    "occupancy": 3, "square_footage": 1500.0, "hvac_status": "On",
    "lighting_status": "Off", "renewable_energy": 5.0,
    "energy_consumption": 75.0, "holiday": "No"
}

Controlled via env:
  MQTT_ENABLED  - "true" (default) to run
  MQTT_BROKER   - broker host (default localhost)
  MQTT_PORT     - broker port (default 1883)
  MQTT_USERNAME / MQTT_PASSWORD - optional credentials
  MQTT_TOPIC    - topic to subscribe to (default enersight/sensors/energy)

If no broker is reachable the service retries every 60s without crashing the
app. When feeding data via MQTT, set SIMULATOR_ENABLED=false so the built-in
replay simulator doesn't double-count consumption.
"""
import asyncio
import json
import os
from datetime import datetime

from backend.core.logging import get_logger
from backend.database.postgres import SessionLocal
from backend.models.energy import EnergyReading

logger = get_logger(__name__)

RETRY_SECONDS = 60


def _to_bool(value, on_words=("on", "yes", "true", "1")) -> bool:
    return str(value).strip().lower() in on_words


class MqttIngestorService:
    """Consumes sensor messages from MQTT and writes them to the database."""

    def __init__(self):
        self.enabled = os.getenv("MQTT_ENABLED", "true").lower() in ("true", "1", "yes")
        self.broker = os.getenv("MQTT_BROKER", "localhost")
        self.port = int(os.getenv("MQTT_PORT", "1883"))
        self.username = os.getenv("MQTT_USERNAME", "")
        self.password = os.getenv("MQTT_PASSWORD", "")
        self.topic = os.getenv("MQTT_TOPIC", "enersight/sensors/energy")
        self.is_running = False
        self._client = None
        self._messages_ingested = 0
        self._warned_unreachable = False

    # ----- paho callbacks (run on the paho network thread) -----

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(self.topic)
            self._warned_unreachable = False
            logger.info(f"MQTT connected to {self.broker}:{self.port}, subscribed to '{self.topic}'")
        else:
            logger.warning(f"MQTT connection refused by broker (rc={rc})")

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0 and self.is_running:
            logger.warning("MQTT connection lost; paho will auto-reconnect")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            reading = self._payload_to_reading(payload)
        except Exception as e:
            logger.error(f"Dropped malformed MQTT message on '{msg.topic}': {e}")
            return

        db = SessionLocal()
        try:
            db.add(reading)
            db.commit()
            self._messages_ingested += 1
            logger.debug(
                f"Ingested MQTT reading #{self._messages_ingested}: "
                f"{reading.consumption:.2f} kWh from {reading.device_id}"
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to persist MQTT reading: {e}")
        finally:
            db.close()

    @staticmethod
    def _payload_to_reading(payload: dict) -> EnergyReading:
        # Stamp arrival time server-side: publisher timestamps are local-time
        # and unreliable for the rolling-window queries used by alerts.
        now = datetime.utcnow()
        return EnergyReading(
            recorded_at=now,
            device_id=str(payload.get("device_id", "mqtt_sensor")),
            location=str(payload.get("location", "default")),
            consumption=float(payload["energy_consumption"]),
            temperature=float(payload.get("temperature") or 0.0),
            humidity=float(payload.get("humidity") or 0.0),
            square_footage=float(payload.get("square_footage") or 0.0),
            occupancy=int(payload.get("occupancy") or 0),
            hvac_usage=_to_bool(payload.get("hvac_status", "Off")),
            lighting_usage=_to_bool(payload.get("lighting_status", "Off")),
            renewable_energy=float(payload.get("renewable_energy") or 0.0),
            day_of_week=now.weekday(),
            holiday=_to_bool(payload.get("holiday", "No")),
        )

    # ----- lifecycle -----

    def _connect_once(self) -> bool:
        """Blocking connect attempt; runs in a worker thread."""
        import paho.mqtt.client as mqtt

        client = mqtt.Client(client_id="enersight_backend_ingestor")
        if self.username:
            client.username_pw_set(self.username, self.password or None)
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message
        try:
            client.connect(self.broker, self.port, keepalive=60)
        except Exception as e:
            client.loop_stop()
            if not self._warned_unreachable:
                logger.warning(
                    f"MQTT broker unreachable at {self.broker}:{self.port} ({e}). "
                    f"Retrying every {RETRY_SECONDS}s - install/start a broker "
                    "(e.g. mosquitto) or set MQTT_ENABLED=false to silence this."
                )
                self._warned_unreachable = True
            else:
                logger.debug(f"MQTT broker still unreachable: {e}")
            return False
        client.loop_start()  # paho network loop on its own thread; auto-reconnects
        self._client = client
        return True

    async def start(self):
        if not self.enabled:
            logger.info("MQTT ingestor disabled (MQTT_ENABLED=false)")
            return
        self.is_running = True
        logger.info(f"MQTT ingestor starting (broker {self.broker}:{self.port}, topic '{self.topic}')")
        while self.is_running and self._client is None:
            connected = await asyncio.to_thread(self._connect_once)
            if connected:
                return
            await asyncio.sleep(RETRY_SECONDS)

    def stop(self):
        self.is_running = False
        if self._client is not None:
            try:
                self._client.loop_stop()
                self._client.disconnect()
            except Exception:
                pass
            self._client = None
        logger.info("MQTT ingestor stopped")


mqtt_ingestor = MqttIngestorService()
