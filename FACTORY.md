# Factory

A three-seat software factory on BAND. Seats coordinate in a room. The only human input for a scored run is the task pasted into that room.

## Seats

| Seat | Mandate | Tools | Runtime |
|---|---|---|---|
| Planner | `mandates/planner.md` | list/read workspace + BAND room tools | LangGraph + Band SDK |
| Implementer | `mandates/implementer.md` | read/write/run + BAND room tools | LangGraph + Band SDK |
| Reviewer | `mandates/reviewer.md` | read/run + BAND room tools | LangGraph + Band SDK |

Mandates are generic. They do not name a product, an endpoint, or a track. Product detail belongs in the room task.

## Why this shape

Planner sequences. Implementer changes the tree. Reviewer re-runs checks and can BLOCK. Review cannot be skipped: the Implementer is not allowed to declare a stage done.

If Reviewer blocks, Planner assigns a fix. That is the recovery loop.

## Stand-up

1. Copy `agent_config.example.yaml` to `agent_config.yaml` and paste three Band remote-agent keys. Each seat needs its own agent id.
2. Put model settings in `.env` (`LLM_BASE_URL`, `LLM_MODEL`, `WORKSPACE_ROOT`).
3. Install: `python3 -m venv .venv && .venv/bin/pip install -e .`
4. Run three processes:

```bash
.venv/bin/python -m seats.planner_agent
.venv/bin/python -m seats.implementer_agent
.venv/bin/python -m seats.reviewer_agent
```

5. In BAND Desktop / app.band.ai, create a room, add all three seats, paste one stage task, then do not steer.

## Design choices

- One in-flight implementation item at a time so handoffs stay readable in the room.
- Reviewer has no write tool, so it cannot silently patch the tree.
- Model thinking is disabled so tool calls stay parseable.
- Workspace tools stay path-jailed to `WORKSPACE_ROOT`.

## Costs

Record tokens and wall time from the BAND Desktop room after each stage run. Fill this table from the run you submit:

| Stage | Seats used | Wall time | Notes |
|---|---|---|---|
| 1 | Planner, Implementer, Reviewer | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |

## Catching bad work

Reviewer must re-run checks. A missing log is a BLOCK. Implementer may not ACCEPT its own work.

## Result so far

`stage-1/` is a complete, containerized service for the tablekeeper track. Later stages go in `stage-2/` through `stage-4/` the same way: one task in the room, factory produces the folder.

## BAND Desktop export

Export the room that produced each submitted stage and keep it with the repo (or attach it on lablab). A video without that room is a disqualification.
