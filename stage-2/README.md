# Stage 2 — multi-restaurant service

Search two restaurants, book a table, cancel. Double-booking is still impossible.

```bash
PYTHONPATH=. python3 -m pytest tests/test_stage.py
docker compose up --build
```

http://localhost:8082
