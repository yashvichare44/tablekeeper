# Factory

A three-seat BAND factory. The only human input on a scored run is the task pasted into the room.

## Seats

| Seat | Mandate | Job |
|---|---|---|
| Planner | `mandates/planner.md` | Split the official spec, assign work, reconcile evidence |
| Implementer | `mandates/implementer.md` | Write the stage folder, commit, return a revision |
| Reviewer | `mandates/reviewer.md` | Re-run checks independently and BLOCK or ACCEPT |

Mandates are generic. Tablekeeper endpoints, fixtures and error codes belong in the room task.

## How a stage is frozen

1. Planner publishes the gate for that folder.
2. Implementer copies the previous accepted tree (or starts empty for stage 1) and widens only the new folder.
3. Reviewer runs the official isolated suite for that stage plus independent occupancy cases.
4. On BLOCK, Implementer repairs; original failures stay in the room.
5. On ACCEPT, the folder is frozen. Later stages do not edit it.

## Product design (load-bearing)

- One process, one lock, in-memory store. No replica sharing.
- Half-open UTC intervals. Local slot grids. First-fold IANA times.
- `Idempotency-Key` receipts for create and atomic move. Failed attempts do not consume the key.
- `GET /_test/export` / `POST /_test/import` for portable state. Invalid snapshots leave live state intact.
- Stage 2 adds declared pairs. Stage 3 adds dated policies and series. Stage 4 adds bounded closure planning (`planning_limit` above six tables / four pairs / six bookings).

## Stand-up

1. Three distinct Band remote agents in `agent_config.yaml`.
2. `.env` with `LLM_BASE_URL`, `LLM_MODEL`, `WORKSPACE_ROOT`.
3. Start the three seat processes. Add them to one Band Desktop room.
4. Paste one official-stage task. Do not steer.
5. Export the room after the run. A video without the room is a disqualification.

## Costs

Fill from the BAND Desktop room after each accepted stage:

| Stage | Wall time | Official cases | Notes |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
