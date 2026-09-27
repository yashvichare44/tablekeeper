# Room task — stage 1

Implement `stage-1/` as a standalone JSON API that satisfies the official tablekeeper stage-1 contract.

- No browser UI. Stdlib only. `PORT` bind, unprivileged user, IANA zoneinfo in the image.
- Starts empty. `POST /_test/reset` loads users, restaurants, tables and optional confirmed reservations (204).
- Public: `GET /health`, `GET /restaurants`, restaurant detail, `GET /availability`.
- Auth: `POST /auth/signup`, `POST /auth/login` with salted scrypt and non-expiring bearer tokens.
- Authenticated: create/list/get/patch/cancel reservations and `POST /reservation-moves`. Create routes require `Idempotency-Key`.
- One lock. Half-open UTC overlap. Atomic moves have no intermediate occupancy.
- `GET /_test/export` and `POST /_test/import` (track tablekeeper, format_version 1). Invalid import must not mutate state.

Planner assigns. Implementer ships a revision. Reviewer re-runs occupancy and reset/import cases. Do not edit later-stage folders.
