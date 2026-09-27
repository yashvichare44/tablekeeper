"""SQLite store. Writes take a lock so overlapping bookings cannot commit."""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from app.config import STAGE

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "tablekeeper.db"
_LOCK = threading.Lock()
_CONN: sqlite3.Connection | None = None


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=8000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def get_conn() -> sqlite3.Connection:
    global _CONN
    if _CONN is None:
        _CONN = _connect()
    return _CONN


def close_db() -> None:
    global _CONN
    if _CONN is not None:
        _CONN.close()
        _CONN = None


def init_db() -> None:
    conn = get_conn()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS restaurants (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            neighborhood TEXT NOT NULL,
            timezone TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tables (
            id INTEGER PRIMARY KEY,
            restaurant_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            zone TEXT NOT NULL,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
        );

        CREATE TABLE IF NOT EXISTS reservations (
            id TEXT PRIMARY KEY,
            table_id INTEGER NOT NULL,
            guest_name TEXT NOT NULL,
            phone TEXT NOT NULL DEFAULT '',
            party_size INTEGER NOT NULL,
            starts_at TEXT NOT NULL,
            ends_at TEXT NOT NULL,
            timezone TEXT NOT NULL,
            idempotency_key TEXT UNIQUE,
            created_at TEXT NOT NULL,
            FOREIGN KEY (table_id) REFERENCES tables(id)
        );

        CREATE TABLE IF NOT EXISTS waitlist (
            id TEXT PRIMARY KEY,
            restaurant_id INTEGER NOT NULL,
            guest_name TEXT NOT NULL,
            phone TEXT NOT NULL DEFAULT '',
            party_size INTEGER NOT NULL,
            starts_at TEXT NOT NULL,
            ends_at TEXT NOT NULL,
            timezone TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id TEXT PRIMARY KEY,
            reservation_id TEXT NOT NULL UNIQUE,
            rating INTEGER NOT NULL,
            comment TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (reservation_id) REFERENCES reservations(id)
        );

        CREATE INDEX IF NOT EXISTS idx_res_table_time
            ON reservations(table_id, starts_at, ends_at);
        """
    )
    if conn.execute("SELECT COUNT(*) AS n FROM restaurants").fetchone()["n"] == 0:
        conn.executemany(
            "INSERT INTO restaurants (id, name, neighborhood, timezone) VALUES (?, ?, ?, ?)",
            [
                (1, "Harbor & Rye", "Embarcadero", "America/Los_Angeles"),
                (2, "Nightjar", "East Village", "America/New_York"),
            ],
        )
        conn.executemany(
            "INSERT INTO tables (id, restaurant_id, name, capacity, zone) VALUES (?, ?, ?, ?, ?)",
            [
                (1, 1, "Oak 2", 2, "Window"),
                (2, 1, "Oak 4", 4, "Window"),
                (3, 1, "Cedar 8", 8, "Private"),
                (4, 2, "Booth A", 2, "Bar"),
                (5, 2, "Booth B", 4, "Garden"),
                (6, 2, "Room", 6, "Private"),
            ],
        )
    _ = STAGE


def reset_db() -> None:
    close_db()
    if DB_PATH.exists():
        DB_PATH.unlink()
    for suffix in ("-wal", "-shm"):
        extra = Path(str(DB_PATH) + suffix)
        if extra.exists():
            extra.unlink()
    init_db()


@contextmanager
def write_txn():
    with _LOCK:
        conn = get_conn()
        conn.execute("BEGIN IMMEDIATE")
        try:
            yield conn
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
