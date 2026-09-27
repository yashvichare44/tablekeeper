# Dark Factory — tablekeeper

BAND software factory for the WeAreDevelopers x BAND Dark Factory hackathon, **tablekeeper** track.

What you submit is the factory, the room run, and the result.

## Factory

Three seats, generic mandates, Band room handoffs:

- [FACTORY.md](FACTORY.md)
- [mandates/planner.md](mandates/planner.md)
- [mandates/implementer.md](mandates/implementer.md)
- [mandates/reviewer.md](mandates/reviewer.md)

## Results (all four stages)

Official lablab stage packets were not public, so these follow the published arc: build the service, repair retries, extend it without regressions.

| Stage | Folder | Check | UI |
|---|---|---|---|
| 1 | `stage-1/` | `PYTHONPATH=. python3 -m pytest tests/test_concurrency.py` | http://localhost:8080 |
| 2 | `stage-2/` | `PYTHONPATH=. python3 -m pytest tests/test_stage.py` | http://localhost:8082 |
| 3 | `stage-3/` | `PYTHONPATH=. python3 -m pytest tests/test_stage.py` | http://localhost:8083 |
| 4 | `stage-4/` | `PYTHONPATH=. python3 -m pytest tests/test_stage.py` | http://localhost:8084 |

```bash
cd stage-4 && docker compose up --build
```

Room tasks: `tasks/stage-1-tablekeeper.md` … `tasks/stage-4-tablekeeper.md`.

## Run the seats

```bash
cp agent_config.example.yaml agent_config.yaml   # then paste three Band keys
# .env already needs LLM_BASE_URL / LLM_MODEL / WORKSPACE_ROOT

.venv/bin/python -m seats.planner_agent
.venv/bin/python -m seats.implementer_agent
.venv/bin/python -m seats.reviewer_agent
```

Paste [tasks/stage-1-tablekeeper.md](tasks/stage-1-tablekeeper.md) into the Band room as the only human message.
