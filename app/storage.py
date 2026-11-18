import json
import sqlite3
from pathlib import Path
from .config import DATABASE_PATH

def _connect():
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with _connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            payload TEXT NOT NULL,
            received_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS devices (
            device_id TEXT PRIMARY KEY,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_payload TEXT
        )""")

def save_telemetry(device_id: str, payload: dict):
    encoded = json.dumps(payload, ensure_ascii=False)
    with _connect() as db:
        db.execute("INSERT INTO telemetry(device_id,payload) VALUES(?,?)", (device_id, encoded))
        db.execute("""INSERT INTO devices(device_id,last_seen,last_payload)
            VALUES(?,CURRENT_TIMESTAMP,?)
            ON CONFLICT(device_id) DO UPDATE SET
            last_seen=CURRENT_TIMESTAMP,last_payload=excluded.last_payload""",
            (device_id, encoded))

def list_devices():
    with _connect() as db:
        return [dict(r) for r in db.execute("SELECT * FROM devices ORDER BY device_id")]

def recent_telemetry(limit=100):
    with _connect() as db:
        rows = db.execute(
            "SELECT device_id,payload,received_at FROM telemetry ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["payload"] = json.loads(item["payload"])
        result.append(item)
    return result
