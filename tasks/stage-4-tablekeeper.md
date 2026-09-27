# Room task — stage 4 (paste this, then stop typing)

Extend `stage-4/` without breaking what already works.

Add:
- a waitlist when a requested window is full
- automatic promotion from the waitlist when a conflicting booking is cancelled
- one review per reservation, a second review is rejected

Re-run every earlier check (overlap, cross-restaurant, race, idempotent retry, reschedule conflict). A regression is a BLOCK.

Complete folder, `docker compose up`, no outbound network.
