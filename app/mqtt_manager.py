import json
import logging
import threading
import paho.mqtt.client as mqtt
from . import config, storage

log = logging.getLogger("yolouno.local_mqtt")
_client = None
_connected = threading.Event()

def _on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        _connected.set()
        log.info("Connected to local Mosquitto")
        client.subscribe("yolouno/+/telemetry", qos=1)
        client.subscribe("yolouno/+/status", qos=1)
    else:
        _connected.clear()
        log.error("Local MQTT connection failed: %s", reason_code)

def _on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    _connected.clear()
    log.warning("Disconnected from local MQTT: %s", reason_code)

def _on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        parts = msg.topic.split("/")
        if len(parts) != 3:
            return
        device_id, message_type = parts[1], parts[2]
        if message_type == "telemetry" and isinstance(payload, dict):
            storage.save_telemetry(device_id, payload)
        elif message_type == "status":
            log.info("Device %s status: %s", device_id, payload)
    except (UnicodeDecodeError, json.JSONDecodeError):
        log.warning("Invalid JSON on topic %s", msg.topic)

def start():
    global _client
    _client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="yolouno-dashboard-backend"
    )
    _client.on_connect = _on_connect
    _client.on_disconnect = _on_disconnect
    _client.on_message = _on_message
    _client.reconnect_delay_set(min_delay=1, max_delay=30)
    _client.connect_async(config.LOCAL_MQTT_HOST, config.LOCAL_MQTT_PORT, keepalive=60)
    _client.loop_start()

def stop():
    global _client
    if _client:
        _client.loop_stop()
        _client.disconnect()
        _client = None

def is_connected():
    return _connected.is_set()

def publish_command(device_id: str, method: str, params):
    if not _client or not _connected.is_set():
        raise RuntimeError("Dashboard backend is not connected to local Mosquitto")
    payload = {"method": method, "params": params}
    info = _client.publish(
        f"yolouno/{device_id}/command",
        json.dumps(payload),
        qos=1
    )
    if info.rc != mqtt.MQTT_ERR_SUCCESS:
        raise RuntimeError(f"MQTT publish failed: rc={info.rc}")
    return payload
