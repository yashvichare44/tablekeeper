from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.db import reset_db
from app.main import app


def _client() -> TestClient:
    reset_db()
    return TestClient(app)


def test_health():
    client = _client()
    assert client.get("/health").json()["ok"] is True


def test_second_overlap_is_rejected():
    client = _client()
    start = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(hours=2)
    payload = {
        "table_id": 1,
        "guest_name": "First",
        "party_size": 2,
        "starts_at": start.isoformat(),
        "timezone": "UTC",
        "duration_minutes": 90,
    }
    assert client.post("/api/reservations", json=payload).status_code == 201
    payload["guest_name"] = "Second"
    assert client.post("/api/reservations", json=payload).status_code == 409


def test_concurrent_same_slot_only_one_wins():
    client = _client()
    start = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(hours=4)

    def book(i: int):
        return client.post(
            "/api/reservations",
            json={
                "table_id": 3,
                "guest_name": f"Racer {i}",
                "party_size": 2,
                "starts_at": start.isoformat(),
                "timezone": "UTC",
                "duration_minutes": 90,
            },
        ).status_code

    with ThreadPoolExecutor(max_workers=20) as pool:
        codes = [future.result() for future in as_completed(pool.submit(book, i) for i in range(20))]

    assert codes.count(201) == 1
    assert codes.count(409) == 19
    bookings = client.get("/api/reservations").json()["reservations"]
    assert len([b for b in bookings if b["table_id"] == 3]) == 1
