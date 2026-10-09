# Economic incident: ce-lifecycle-v2 phantom overrun (2026-10-09)

Status: RECORDED. Repaired. Companion to the existing doc `vault/plans/ce-lifecycle-v2-incident-coordinator-bind-2026-10-09.md` (in the live repo at f85d5db7; not re-read here).

## Numbers (coordinator dossier, 11:30Z)
- Reality-delta table (earlier read): ce-lifecycle-v2 used 39,630,319 against cap 8,847,012, remaining -30,783,307.
- After repair: used 6,605,944, open 2,136,570, remaining 2,241,068.
- Difference removed: 33,024,375 on the table; the journal entry was a 32.58M settle (32,801,829 per memory feedback_coordinator_set_location_binds_goal), journal seq 91-94.
  The two figures (33.02M table delta vs 32.58M/32.80M settle) are not reconciled: UNKNOWN, the journal was not read.

## Cause class
Retroactive cwd binding of a coordinator. Coordinator 97a3d9cf ran Set-Location into the v2 root. The session guard bound the whole session to goal ce-lifecycle-v2 and booked the session's earlier spend as a settle. Nothing was spent by a v2 worker.
Second occurrence: the reality scan itself was bound to ce-a3b-r the same way and the guard then refused every call (reality-delta plan, status paragraph). This is the same trap class as the earlier ce-lifecycle-v brick (-3,608,719).

## Repair
Commit f85d5db7 "journal seq 91-94 removed (Owner yes), v2 back to 6,605,944 used". The Owner approved removal.

## What L1 now bounds
Lifecycle L1 (3f9b57cc, an ancestor of 91205acb) binds prospectively. It is NOT on branch main (908b5430), so the main checkout is not covered by it. A coordinator that runs Set-Location in a branch without L1 can still be bound retroactively. Whether L1 prevents the retroactive settle itself (not just later calls) is UNKNOWN; its tests were not read.

## Residual risk
- Any pane that changes cwd into a goal root. Rule: absolute paths and `git -C`; never Set-Location into Apps\pp-*.
- Journal removals are manual and need an Owner yes. No automatic detector of a settle larger than the session's own transcript.
- ce-a3b-r is itself over cap (9,383,534 used of 8,600,000; remaining -783,534), so any bind to it halts the session.

## Second line item: R5c strays
R5c (m-447ca8005684) Close ran `arm` twice without `--no-launch`. Two packet-less strays started. Measured cost 866,883. No Owner repair was needed; the cost is real spend, not a mis-booking. Prevention: a Cognitive CI clause that rejects `arm` in a Close step without `--no-launch` (proposed in the final plan, unit P5).

## Cost booked vs spent
- Booked to v2 by the incident: ~32.6M-33.0M (see above).
- Actually spent by the coordinator session in that window: UNKNOWN (transcript and journal not read).
- Booked after repair: 0 of that amount. Real stray cost: 866,883 (R5c) on top.
