# Room task — stage 4

Copy accepted stage-3 into `stage-4/` and widen only that folder.

Add manager `POST /restaurants/{id}/replans` and apply, plus `POST /series/{id}/amend`. Bounded solver: six tables, four pairs, six considered bookings; larger inputs return `planning_limit` with no mutation. Closures occupy. Original series schedules survive edits.

Reviewer runs the full isolated harness on all four folders. Do not edit frozen earlier folders.
