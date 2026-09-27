# Stage 1 — Tablekeeper

Restaurant reservations where the same table cannot be held twice for an overlapping window.

```bash
cd stage-1
python3 -m pytest tests/test_concurrency.py
docker compose up --build
```

Open http://localhost:8080. The compose network is `internal: true` so the container has no outbound internet.
