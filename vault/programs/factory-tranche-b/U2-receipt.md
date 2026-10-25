# U2 receipt — W3 review debt in gsd_mission.py

## Findings
- MEDIUM-1 REPRODUCED. Old code: after a held pass the record has 2 samples, not 3 (`V-W3C-PERSIST-NON-LAUNCH` red: `epoch=1 samples=2`). Samples were set only on the in-memory rec and persisted via `launch_worker`.
- LOW-1 REPRODUCED. Old code: two identical held passes wrote 2 rows (`V-W3C-HELD-ONE-ROW` red: `rows=2`).
- LOW-3 REPRODUCED by reading: the old check only called the mutant judge function.

## Changes (tools/gsd_mission.py, tools/test_w3_marginal_gain.py)
- New `_persist_gain()`: one locked write of `gain_samples` + `gain_hold` straight after the sample is taken, no seq bump / ledger row. Every later path (continue, readmit, capsule rotation, launch) reloads from disk, so all keep them.
- `relay_held` for the gain hold is appended only when `gain_hold` (head+note identity of the window; spend excluded since it rises every pass) differs from the stored one. Cleared when not held.
- `V-W3C-MUTATION-RED` now runs `supervise` with the head-blind mutant (held, no launch), restores, and a real run relays.
- Limit: the persistence test drives the hold path (non-launch_worker); continue/readmit/rotation are covered by construction (they reload from disk), not by a separate drive.

## Red on old code (gsd_mission.py reverted, new test)
FAIL V-W3C-PERSIST-NON-LAUNCH epoch=1 samples=2
FAIL V-W3C-HELD-ONE-ROW rows=2
W3C_PASS=9/11

## Green
W3C_PASS=11/11 (exit 0); W3A_PASS=5/5 (exit 0); W3B_PASS=6/6 (exit 0)

COMMITS: d278c5b7
