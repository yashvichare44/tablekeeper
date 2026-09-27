from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.config import STAGE
from app.db import reset_db
from app.main import app


def client() -> TestClient:
    reset_db()
    return TestClient(app)


def _slot(hours=3):
    start = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(hours=hours)
    return {
        "table_id": 1,
        "guest_name": "First",
        "party_size": 2,
        "starts_at": start.isoformat(),
        "timezone": "UTC",
        "duration_minutes": 90,
    }


def test_health_reports_stage():
    assert client().get("/health").json()["stage"] == STAGE


def test_overlap_rejected():
    c = client()
    payload = _slot()
    assert c.post("/api/reservations", json=payload).status_code == 201
    payload["guest_name"] = "Second"
    assert c.post("/api/reservations", json=payload).status_code == 409


def test_two_restaurants_same_clock_ok():
    c = client()
    payload = _slot(5)
    assert c.post("/api/reservations", json=payload).status_code == 201
    payload["table_id"] = 4
    payload["guest_name"] = "NY guest"
    assert c.post("/api/reservations", json=payload).status_code == 201


def test_concurrent_same_slot_one_winner():
    c = client()
    start = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(hours=8)

    def book(i: int):
        return c.post(
            "/api/reservations",
            json={
                "table_id": 2,
                "guest_name": f"Racer {i}",
                "party_size": 2,
                "starts_at": start.isoformat(),
                "timezone": "UTC",
            },
        ).status_code

    with ThreadPoolExecutor(max_workers=20) as pool:
        codes = [f.result() for f in as_completed(pool.submit(book, i) for i in range(20))]
    assert codes.count(201) == 1
    assert codes.count(409) == 19


def test_idempotent_retry_does_not_double_book():
    if STAGE < 3:
        return
    c = client()
    payload = _slot(10)
    headers = {"Idempotency-Key": "retry-1"}
    first = c.post("/api/reservations", json=payload, headers=headers)
    second = c.post("/api/reservations", json=payload, headers=headers)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert second.json().get("replayed") is True
    assert len(c.get("/api/reservations").json()["reservations"]) == 1


def test_reschedule_conflict():
    if STAGE < 3:
        return
    c = client()
    a = _slot(12)
    b = dict(a, guest_name="Other", starts_at=(datetime.fromisoformat(a["starts_at"]) + timedelta(hours=3)).isoformat())
    first = c.post("/api/reservations", json=a).json()
    assert c.post("/api/reservations", json=b).status_code == 201
    moved = c.patch(
        f"/api/reservations/{first['id']}",
        json={"starts_at": b["starts_at"], "timezone": "UTC"},
    )
    assert moved.status_code == 409


def test_waitlist_promotes_on_cancel():
    if STAGE < 4:
        return
    c = client()
    payload = _slot(14)
    assert c.post("/api/reservations", json=payload).status_code == 201
    payload["guest_name"] = "Waiting"
    payload["waitlist_if_full"] = True
    wait = c.post("/api/reservations", json=payload)
    assert wait.status_code == 201
    assert wait.json()["waitlisted"] is True
    held = c.get("/api/reservations").json()["reservations"][0]
    cancel = c.delete(f"/api/reservations/{held['id']}")
    assert cancel.json()["promoted"]
    names = [r["guest_name"] for r in c.get("/api/reservations").json()["reservations"]]
    assert names == ["Waiting"]


def test_review_once():
    if STAGE < 4:
        return
    c = client()
    booked = c.post("/api/reservations", json=_slot(16)).json()
    assert c.post("/api/reviews", json={"reservation_id": booked["id"], "rating": 5, "comment": "Perfect"}).status_code == 201
    assert c.post("/api/reviews", json={"reservation_id": booked["id"], "rating": 4}).status_code == 409
