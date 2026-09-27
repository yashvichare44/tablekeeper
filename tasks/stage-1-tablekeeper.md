# Room task — stage 1 (paste this, then stop typing)

Build a restaurant reservation service in `stage-1/`.

Hard rule: the same table must never be held by two reservations whose time windows overlap, including concurrent requests, retries, and bookings created from different time zones.

Ship:
- a service that starts from `stage-1/docker-compose.yml` with no outbound network
- a simple UI to pick a table and book a window
- automated checks that prove a 20-way race for one table/window yields exactly one booking
- keep the folder self-contained and buildable

Planner: split the work and assign the Implementer.
Implementer: write the service and the race check, then @mention Reviewer with evidence.
Reviewer: re-run the checks. BLOCK or ACCEPT. Do not edit product files.
