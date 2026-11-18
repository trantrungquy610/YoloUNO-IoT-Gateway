import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from . import storage, mqtt_manager, config

logging.basicConfig(level=logging.INFO)

class Command(BaseModel):
    method: str
    params: object

@asynccontextmanager
async def lifespan(app: FastAPI):
    storage.init_db()
    mqtt_manager.start()
    yield
    mqtt_manager.stop()

app = FastAPI(title="YoloUNO Local Dashboard", version="0.2.0", lifespan=lifespan)
dashboard_dir = Path(__file__).resolve().parent.parent / "dashboard"
app.mount("/static", StaticFiles(directory=dashboard_dir), name="static")

@app.get("/")
def dashboard():
    return FileResponse(dashboard_dir / "index.html")

@app.get("/api/health")
def health():
    return {
        "gateway": config.GATEWAY_ID,
        "status": "running",
        "localMqttConnected": mqtt_manager.is_connected()
    }

@app.get("/api/devices")
def devices():
    return storage.list_devices()

@app.get("/api/telemetry")
def telemetry(limit: int = 100):
    return storage.recent_telemetry(max(1, min(limit, 500)))

@app.post("/api/devices/{device_id}/command")
def send_command(device_id: str, command: Command):
    try:
        payload = mqtt_manager.publish_command(device_id, command.method, command.params)
        return {"success": True, "deviceId": device_id, "command": payload}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
