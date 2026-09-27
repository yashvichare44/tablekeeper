# Stage 4 — extend without breaking

Keeps every earlier invariant, then adds waitlist promotion and one review per booking.

```bash
PYTHONPATH=. python3 -m pytest tests/test_stage.py
docker compose up --build
```

http://localhost:8084
