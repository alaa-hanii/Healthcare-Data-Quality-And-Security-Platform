"""
ProcessingLayer/orchestration.py
----------------------------------
Lowest layer of the Orchestration pipeline. Owns the raw event log
(every run of every layer) in a small local SQLite DB so history
survives backend restarts — same role the .dtsx files / PowerBI link
play for their respective layers.
"""

import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "orchestration.db")


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orchestration_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            layer TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT,
            duration_seconds REAL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


init_db()


def insert_event(layer: str, status: str, message: str = "", duration_seconds: float = None) -> dict:
    ts = datetime.utcnow().isoformat()
    conn = _conn()
    cur = conn.execute(
        "INSERT INTO orchestration_events (layer, status, message, duration_seconds, timestamp) "
        "VALUES (?, ?, ?, ?, ?)",
        (layer, status, message, duration_seconds, ts),
    )
    conn.commit()
    event_id = cur.lastrowid
    conn.close()
    return {"id": event_id, "layer": layer, "status": status, "message": message,
            "duration_seconds": duration_seconds, "timestamp": ts}


def get_events(limit: int = 50) -> list:
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM orchestration_events ORDER BY timestamp DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_events_between(start_iso: str, end_iso: str) -> list:
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM orchestration_events WHERE timestamp >= ? AND timestamp < ? ORDER BY timestamp ASC",
        (start_iso, end_iso),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_events() -> list:
    conn = _conn()
    rows = conn.execute("SELECT * FROM orchestration_events ORDER BY timestamp ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]
