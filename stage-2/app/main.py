"""Tablekeeper — each stage folder pins STAGE in app.config."""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import STAGE
from app.db import get_conn, init_db, utc_now, write_txn

STATIC = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Tablekeeper", version=f"0.{STAGE}.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class BookingIn(BaseModel):
    table_id: int
    guest_name: str = Field(min_length=1, max_length=80)
    phone: str = ""
    party_size: int = Field(ge=1, le=20)
    starts_at: str
    timezone: str = "UTC"
    duration_minutes: int = Field(default=90, ge=30, le=240)
    waitlist_if_full: bool = False


class RescheduleIn(BaseModel):
    starts_at: str
    timezone: str = "UTC"
    duration_minutes: int = Field(default=90, ge=30, le=240)


class ReviewIn(BaseModel):
    reservation_id: str
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=400)


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


def _row_booking(conn, booking_id: str) -> dict:
    row = conn.execute(
        """
        SELECT r.id, r.table_id, t.name AS table_name, t.restaurant_id,
               rest.name AS restaurant_name, r.guest_name, r.phone, r.party_size,
               r.starts_at, r.ends_at, r.timezone, r.created_at
        FROM reservations r
        JOIN tables t ON t.id = r.table_id
        JOIN restaurants rest ON rest.id = t.restaurant_id
        WHERE r.id = ?
        """,
        (booking_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(404, "reservation not found")
    return dict(row)


def _promote_waitlist(conn, restaurant_id: int, start: datetime, end: datetime) -> str | None:
    if STAGE < 4:
        return None
    waiting = conn.execute(
        """
        SELECT * FROM waitlist
        WHERE restaurant_id = ? AND starts_at < ? AND ends_at > ?
        ORDER BY created_at
        """,
        (restaurant_id, end.isoformat(), start.isoformat()),
    ).fetchall()
    tables = conn.execute(
        "SELECT id, capacity FROM tables WHERE restaurant_id = ?",
        (restaurant_id,),
    ).fetchall()
    for guest in waiting:
        g_start = datetime.fromisoformat(guest["starts_at"])
        g_end = datetime.fromisoformat(guest["ends_at"])
        for table in tables:
            if table["capacity"] < guest["party_size"]:
                continue
            if _overlaps(conn, table["id"], g_start, g_end):
                continue
            booking_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO reservations
                (id, table_id, guest_name, phone, party_size, starts_at, ends_at, timezone, idempotency_key, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
                """,
                (
                    booking_id,
                    table["id"],
                    guest["guest_name"],
                    guest["phone"],
                    guest["party_size"],
                    guest["starts_at"],
                    guest["ends_at"],
                    guest["timezone"],
                    utc_now(),
                ),
            )
            conn.execute("DELETE FROM waitlist WHERE id = ?", (guest["id"],))
            return booking_id
    return None


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "tablekeeper", "stage": STAGE}


@app.get("/api/restaurants")
def list_restaurants() -> dict:
    rows = get_conn().execute(
        "SELECT id, name, neighborhood, timezone FROM restaurants ORDER BY id"
    ).fetchall()
    return {"restaurants": [dict(row) for row in rows]}


@app.get("/api/tables")
def list_tables(restaurant_id: int | None = None) -> dict:
    if restaurant_id is None:
        rows = get_conn().execute(
            "SELECT id, restaurant_id, name, capacity, zone FROM tables ORDER BY id"
        ).fetchall()
    else:
        rows = get_conn().execute(
            "SELECT id, restaurant_id, name, capacity, zone FROM tables WHERE restaurant_id = ? ORDER BY id",
            (restaurant_id,),
        ).fetchall()
    return {"tables": [dict(row) for row in rows]}


@app.get("/api/reservations")
def list_reservations() -> dict:
    rows = get_conn().execute(
        """
        SELECT r.id, r.table_id, t.name AS table_name, t.restaurant_id,
               rest.name AS restaurant_name, r.guest_name, r.phone, r.party_size,
               r.starts_at, r.ends_at, r.timezone, r.created_at
        FROM reservations r
        JOIN tables t ON t.id = r.table_id
        JOIN restaurants rest ON rest.id = t.restaurant_id
        ORDER BY r.starts_at
        """
    ).fetchall()
    return {"reservations": [dict(row) for row in rows]}


@app.get("/api/availability")
def availability(
    starts_at: str,
    timezone: str = "UTC",
    party_size: int = 2,
    duration_minutes: int = 90,
    restaurant_id: int | None = None,
) -> dict:
    start = _parse_start(starts_at, timezone)
    end = start + timedelta(minutes=duration_minutes)
    conn = get_conn()
    if restaurant_id is None:
        tables = conn.execute(
            "SELECT id, restaurant_id, name, capacity, zone FROM tables ORDER BY id"
        ).fetchall()
    else:
        tables = conn.execute(
            "SELECT id, restaurant_id, name, capacity, zone FROM tables WHERE restaurant_id = ? ORDER BY id",
            (restaurant_id,),
        ).fetchall()
    open_tables = []
    for table in tables:
        if table["capacity"] < party_size:
            continue
        if _overlaps(conn, table["id"], start, end):
            continue
        open_tables.append(dict(table))
    return {"starts_at": start.isoformat(), "ends_at": end.isoformat(), "tables": open_tables}


@app.post("/api/reservations", status_code=201)
def create_reservation(
    body: BookingIn,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict:
    start = _parse_start(body.starts_at, body.timezone)
    end = start + timedelta(minutes=body.duration_minutes)
    if end <= start:
        raise HTTPException(400, "end must be after start")
    if STAGE < 3:
        idempotency_key = None

    with write_txn() as conn:
        if idempotency_key:
            existing = conn.execute(
                "SELECT id FROM reservations WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            if existing:
                return {**_row_booking(conn, existing["id"]), "replayed": True}

        table = conn.execute(
            "SELECT id, name, capacity, restaurant_id FROM tables WHERE id = ?",
            (body.table_id,),
        ).fetchone()
        if table is None:
            raise HTTPException(404, "table not found")
        if table["capacity"] < body.party_size:
            raise HTTPException(409, "party does not fit this table")
        conflicts = _overlaps(conn, body.table_id, start, end)
        if conflicts:
            if STAGE >= 4 and body.waitlist_if_full:
                wait_id = str(uuid.uuid4())
                conn.execute(
                    """
                    INSERT INTO waitlist
                    (id, restaurant_id, guest_name, phone, party_size, starts_at, ends_at, timezone, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        wait_id,
                        table["restaurant_id"],
                        body.guest_name.strip(),
                        body.phone.strip(),
                        body.party_size,
                        start.isoformat(),
                        end.isoformat(),
                        body.timezone,
                        utc_now(),
                    ),
                )
                return {
                    "waitlisted": True,
                    "id": wait_id,
                    "restaurant_id": table["restaurant_id"],
                }
            raise HTTPException(409, "table already booked for that window")

        booking_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO reservations
            (id, table_id, guest_name, phone, party_size, starts_at, ends_at, timezone, idempotency_key, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                booking_id,
                body.table_id,
                body.guest_name.strip(),
                body.phone.strip(),
                body.party_size,
                start.isoformat(),
                end.isoformat(),
                body.timezone,
                idempotency_key,
                utc_now(),
            ),
        )
        return _row_booking(conn, booking_id)


@app.patch("/api/reservations/{booking_id}")
def reschedule(booking_id: str, body: RescheduleIn) -> dict:
    if STAGE < 3:
        raise HTTPException(404, "not available in this stage")
    start = _parse_start(body.starts_at, body.timezone)
    end = start + timedelta(minutes=body.duration_minutes)
    with write_txn() as conn:
        current = conn.execute("SELECT table_id FROM reservations WHERE id = ?", (booking_id,)).fetchone()
        if current is None:
            raise HTTPException(404, "reservation not found")
        if _overlaps(conn, current["table_id"], start, end, ignore_id=booking_id):
            raise HTTPException(409, "table already booked for that window")
        conn.execute(
            "UPDATE reservations SET starts_at = ?, ends_at = ?, timezone = ? WHERE id = ?",
            (start.isoformat(), end.isoformat(), body.timezone, booking_id),
        )
        return _row_booking(conn, booking_id)


@app.delete("/api/reservations/{booking_id}")
def cancel_reservation(booking_id: str) -> dict:
    with write_txn() as conn:
        row = conn.execute(
            """
            SELECT r.id, t.restaurant_id, r.starts_at, r.ends_at
            FROM reservations r
            JOIN tables t ON t.id = r.table_id
            WHERE r.id = ?
            """,
            (booking_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(404, "reservation not found")
        conn.execute("DELETE FROM reviews WHERE reservation_id = ?", (booking_id,))
        conn.execute("DELETE FROM reservations WHERE id = ?", (booking_id,))
        promoted = _promote_waitlist(
            conn,
            row["restaurant_id"],
            datetime.fromisoformat(row["starts_at"]),
            datetime.fromisoformat(row["ends_at"]),
        )
    return {"deleted": booking_id, "promoted": promoted}


@app.get("/api/waitlist")
def list_waitlist() -> dict:
    if STAGE < 4:
        raise HTTPException(404, "not available in this stage")
    rows = get_conn().execute("SELECT * FROM waitlist ORDER BY created_at").fetchall()
    return {"waitlist": [dict(row) for row in rows]}


@app.post("/api/reviews", status_code=201)
def create_review(body: ReviewIn) -> dict:
    if STAGE < 4:
        raise HTTPException(404, "not available in this stage")
    with write_txn() as conn:
        exists = conn.execute("SELECT id FROM reservations WHERE id = ?", (body.reservation_id,)).fetchone()
        if exists is None:
            raise HTTPException(404, "reservation not found")
        review_id = str(uuid.uuid4())
        try:
            conn.execute(
                "INSERT INTO reviews (id, reservation_id, rating, comment, created_at) VALUES (?, ?, ?, ?, ?)",
                (review_id, body.reservation_id, body.rating, body.comment.strip(), utc_now()),
            )
        except Exception as exc:
            raise HTTPException(409, "review already exists") from exc
    return {"id": review_id, "reservation_id": body.reservation_id, "rating": body.rating}
