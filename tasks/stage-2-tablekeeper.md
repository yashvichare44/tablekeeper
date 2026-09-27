# Room task — stage 2 (paste this, then stop typing)

Extend the service in `stage-2/` into a complete, buildable multi-restaurant reservation app.

Keep the stage-1 hard rule: one table cannot be held twice for an overlapping window, including concurrent requests.

Add:
- more than one restaurant, each with its own tables
- availability filtered by restaurant
- cancel from the API and the UI
- guest phone on a booking
- the same race check, plus a check that two restaurants can book the same clock time

`stage-2/docker-compose.yml` must start with no outbound network.
