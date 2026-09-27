# Stage 3 — repair failures

Idempotent retries and safe reschedule. A replayed key cannot create a second seat.

```bash
PYTHONPATH=. python3 -m pytest tests/test_stage.py
docker compose up --build
```

http://localhost:8083
