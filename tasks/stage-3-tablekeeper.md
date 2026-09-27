# Room task — stage 3 (paste this, then stop typing)

Repair failure modes in `stage-3/` without weakening the no-overlap rule.

The service must:
- treat `Idempotency-Key` as a replay: the same key cannot create a second reservation
- reject a reschedule that would overlap another booking on that table
- keep the 20-way race at exactly one winner
- remain a complete containerized service

This stage is about retries and recovery, not new product surface.
