"""Tablekeeper stage 1 — reservations that cannot overlap on the same table."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.db import get_conn, init_db, utc_now, write_txn

STATIC = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Tablekeeper", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class BookingIn(BaseModel):
    table_id: int
    guest_name: str = Field(min_length=1, max_length=80)
    party_size: int = Field(ge=1, le=20)
    starts_at: str
    timezone: str = "UTC"
    duration_minutes: int = Field(default=90, ge=30, le=240)


def _parse_start(value: str, tz_name: str) -> datetime:
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(400, f"unknown timezone: {tz_name}") from exc
    raw = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if raw.tzinfo is None:
        raw = raw.replace(tzinfo=tz)
    return raw.astimezone(timezone.utc)


def _overlaps(conn, table_id: int, start: datetime, end: datetime, ignore_id: str | None = None):
    rows = conn.execute(
        """
        SELECT id FROM reservations
        WHERE table_id = ?
          AND starts_at < ?
          AND ends_at > ?
          AND (? IS NULL OR id != ?)
        """,
        (table_id, end.isoformat(), start.isoformat(), ignore_id, ignore_id),
    ).fetchall()
    return [row["id"] for row in rows]


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "tablekeeper", "stage": 1}


@app.get("/api/tables")
def list_tables() -> dict:
    rows = get_conn().execute("SELECT id, name, capacity, zone FROM tables ORDER BY id").fetchall()
    return {"tables": [dict(row) for row in rows]}


@app.get("/api/reservations")
def list_reservations() -> dict:
    rows = get_conn().execute(
        """
        SELECT r.id, r.table_id, t.name AS table_name, r.guest_name, r.party_size,
               r.starts_at, r.ends_at, r.timezone, r.created_at
        FROM reservations r
        JOIN tables t ON t.id = r.table_id
        ORDER BY r.starts_at
        """
    ).fetchall()
    return {"reservations": [dict(row) for row in rows]}


@app.get("/api/availability")
def availability(starts_at: str, timezone: str = "UTC", party_size: int = 2, duration_minutes: int = 90) -> dict:
    start = _parse_start(starts_at, timezone)
    end = start + timedelta(minutes=duration_minutes)
    conn = get_conn()
    tables = conn.execute("SELECT id, name, capacity, zone FROM tables ORDER BY id").fetchall()
    open_tables = []
    for table in tables:
        if table["capacity"] < party_size:
            continue
        if _overlaps(conn, table["id"], start, end):
            continue
        open_tables.append(dict(table))
    return {
        "starts_at": start.isoformat(),
        "ends_at": end.isoformat(),
        "tables": open_tables,
    }


@app.post("/api/reservations", status_code=201)
def create_reservation(body: BookingIn) -> dict:
    start = _parse_start(body.starts_at, body.timezone)
    end = start + timedelta(minutes=body.duration_minutes)
    if end <= start:
        raise HTTPException(400, "end must be after start")

    with write_txn() as conn:
        table = conn.execute(
            "SELECT id, name, capacity FROM tables WHERE id = ?",
            (body.table_id,),
        ).fetchone()
        if table is None:
            raise HTTPException(404, "table not found")
        if table["capacity"] < body.party_size:
            raise HTTPException(409, "party does not fit this table")
        conflicts = _overlaps(conn, body.table_id, start, end)
        if conflicts:
            raise HTTPException(409, "table already booked for that window")
        booking_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO reservations
            (id, table_id, guest_name, party_size, starts_at, ends_at, timezone, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                booking_id,
                body.table_id,
                body.guest_name.strip(),
                body.party_size,
                start.isoformat(),
                end.isoformat(),
                body.timezone,
                utc_now(),
            ),
        )
    return {
        "id": booking_id,
        "table_id": body.table_id,
        "table_name": table["name"],
        "guest_name": body.guest_name.strip(),
        "party_size": body.party_size,
        "starts_at": start.isoformat(),
        "ends_at": end.isoformat(),
        "timezone": body.timezone,
    }


@app.delete("/api/reservations/{booking_id}")
def cancel_reservation(booking_id: str) -> dict:
    with write_txn() as conn:
        row = conn.execute("DELETE FROM reservations WHERE id = ? RETURNING id", (booking_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "reservation not found")
    return {"deleted": booking_id}
