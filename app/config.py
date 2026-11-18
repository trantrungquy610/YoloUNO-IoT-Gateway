import os

GATEWAY_ID = os.getenv("GATEWAY_ID", "yolouno-gateway-01")
LOCAL_MQTT_HOST = os.getenv("LOCAL_MQTT_HOST", "127.0.0.1")
LOCAL_MQTT_PORT = int(os.getenv("LOCAL_MQTT_PORT", "1883"))
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/gateway.db")
