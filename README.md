# Dark Factory — tablekeeper

BAND software factory for the WeAreDevelopers x BAND Dark Factory hackathon, **tablekeeper** track.

What you submit is the factory, the room run, and the result.

## Factory

Three seats, generic mandates, Band room handoffs:

- [FACTORY.md](FACTORY.md)
- [mandates/planner.md](mandates/planner.md)
- [mandates/implementer.md](mandates/implementer.md)
- [mandates/reviewer.md](mandates/reviewer.md)

## Stage 1 result

`stage-1/` is a reservation service. A table cannot be double-booked under a concurrent race.

```bash
cd stage-1
python3 -m pip install -r requirements.txt
PYTHONPATH=. python3 -m pytest tests/test_concurrency.py
docker compose up --build
```

Then open http://localhost:8080

## Run the seats

```bash
cp agent_config.example.yaml agent_config.yaml   # then paste three Band keys
# .env already needs LLM_BASE_URL / LLM_MODEL / WORKSPACE_ROOT

.venv/bin/python -m seats.planner_agent
.venv/bin/python -m seats.implementer_agent
.venv/bin/python -m seats.reviewer_agent
```

Paste [tasks/stage-1-tablekeeper.md](tasks/stage-1-tablekeeper.md) into the Band room as the only human message.
