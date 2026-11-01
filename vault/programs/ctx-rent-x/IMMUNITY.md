# Error -> Immunity entries (ctx-rent-x)

## WAITING-IS-NOT-MODEL-ACTIVITY (recorded 2026-10-31, from the laptop coordinator's successor instruction)
Evidence: mission m-f92eb3ef9ccc HALTED after 3 empty reconcile epochs (8, 9, 10). Each epoch paid model calls only to re-discover
that the remaining phases (4, 5, 7-live, 8-live) waited on the laptop; STATE.md rows "Worker epoch 8", "9", "10" say "No GEX44-runnable
unit; no spend" while still costing an epoch each. This is the defect Phase 6 measures in the estate (waiting = 1.32% of processed on this
host), reproduced inside this very mission.
Immunity (proposal, NOT yet a UKDL rule): a worker whose reconcile finds no runnable unit writes ONE OWNER NOTE line and stops in the
same epoch; an epoch that only reconciles is not scheduled. Candidate home: UKDL Process Rule + a mission-runner check
(`gsd_mission` refuses a new epoch when the previous N epochs recorded "no runnable unit" and no remote branch moved).
Status: UKDL Process Rule WRITTEN 2026-10-31 (`PR-NO-RUNNABLE-UNIT-STOPS-THE-EPOCH-001` in vault/knowledge_base/ukdl-universal.md). Runner check in `gsd_mission` NOT built (owner tool, outside this mission's scope); stays a named proposal. Epochs 5-6 of this mission are additional evidence (Owner D2).
