# Tablekeeper — Dark Factory

BAND factory + official-contract Tablekeeper service for the [WeAreDevelopers x BAND Dark Factory](https://lablab.ai/ai-hackathons/wearedevelopers-hackathon) hackathon.

The product matches the published tablekeeper harness: empty start, `POST /_test/reset` fixtures, auth, occupancy under one lock, idempotent writes, portable export/import, 2 CPU / 2 GiB, no pip, no outbound runtime.

Earlier public runs that encode this contract: [Figueira](https://github.com/athosfif/tablekeeper-band-dark-factory), [icohangar ShipScore](https://github.com/icohangar-ops/tablekeeper).

## Stages

| Folder | Scope | UI |
|---|---|---|
| [stage-1](stage-1/RUN.md) | JSON API, auth, bookings, atomic moves, portable state | none |
| [stage-2](stage-2/RUN.md) | Combinable table pairs + English browser flows | `/` `/signup` `/login` `/lookup` |
| [stage-3](stage-3/RUN.md) | Dated policies, history, recurring series | same routes |
| [stage-4](stage-4/RUN.md) | Closure replans + atomic series amend | same routes |

```sh
docker build -t tablekeeper-stage4 ./stage-4
docker run --rm --name tablekeeper-stage4 --cpus 2 --memory 2g \
  -e PORT=8080 -p 127.0.0.1:8080:8080 tablekeeper-stage4
```

Readiness: `GET /health` → `{"status":"ok"}`. The process starts empty. Load restaurants through `POST /_test/reset`.

## Factory

Three generic seats (product detail stays in the room task, not the mandates):

- [FACTORY.md](FACTORY.md)
- [mandates/planner.md](mandates/planner.md)
- [mandates/implementer.md](mandates/implementer.md)
- [mandates/reviewer.md](mandates/reviewer.md)

```sh
.venv/bin/python -m seats.planner_agent
.venv/bin/python -m seats.implementer_agent
.venv/bin/python -m seats.reviewer_agent
```

## Official check (when you have the challenge checkout)

```sh
python -m harness run --track tablekeeper --repo /absolute/this/repo \
  --all --mode isolated --out /absolute/evidence
python -m harness check /absolute/this/repo --track tablekeeper
```

The read-only checkout used by accepted runs is `803560d2a678ace1414465c098eb0ab5380ffade`.
