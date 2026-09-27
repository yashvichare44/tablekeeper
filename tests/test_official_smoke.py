"""Smoke the official stage-1 contract without Docker."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "stage-1"
sys.path.insert(0, str(ROOT))

from application import Application  # noqa: E402
from validation import APIError  # noqa: E402


FIXTURE = {
    "users": [
        {
            "id": "u_owner",
            "email": "ada@example.com",
            "display_name": "Ada",
            "password": "password1",
        }
    ],
    "restaurants": [
        {
            "id": "r1",
            "name": "Harbor",
            "timezone": "America/Los_Angeles",
            "slot_minutes": 30,
            "reservation_duration_minutes": 90,
            "cancellation_cutoff_minutes": 0,
            "opening_hours": [{"weekday": "mon", "opens": "17:00", "closes": "22:00"}],
            "tables": [
                {"id": "t1", "label": "Oak", "capacity": 2},
                {"id": "t2", "label": "Pine", "capacity": 4},
            ],
        }
    ],
    "reservations": [],
}


def test_health_reset_overlap():
    app = Application()
    status, body = app.handle("GET", "/health", {}, {})
    assert status == 200 and body["status"] == "ok"

    status, body = app.handle("POST", "/_test/reset", {}, FIXTURE)
    assert status == 204 and body is None

    status, session = app.handle(
        "POST",
        "/auth/login",
        {},
        {"email": "ada@example.com", "password": "password1"},
    )
    assert status == 200
    headers = {"Authorization": f"Bearer {session['token']}", "Idempotency-Key": "k1"}

    booking = {
        "restaurant_id": "r1",
        "table_id": "t1",
        "party_size": 2,
        "starts_at_local": "2026-09-28T17:00",
    }
    status, first = app.handle("POST", "/reservations", headers, booking)
    assert status == 201
    status, replay = app.handle("POST", "/reservations", headers, booking)
    assert status == 200 and replay["reference"] == first["reference"]

    headers2 = {"Authorization": f"Bearer {session['token']}", "Idempotency-Key": "k2"}
    try:
        app.handle("POST", "/reservations", headers2, booking)
        raise AssertionError("overlap must fail")
    except APIError as error:
        assert error.status == 409
        assert error.code == "table_unavailable"
