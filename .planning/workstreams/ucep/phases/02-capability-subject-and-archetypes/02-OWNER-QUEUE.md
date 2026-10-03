# Phase 2 Owner queue (UCEP-02)

Status: every item below is open, and none blocks Phase 2 completion. Phase 2 touches no
scheduled task, no hook and no `settings.json`; hosting the producer is an Owner step (R-4).

| id | scope | item | effect until done |
|---|---|---|---|
| O-1 | Owner action | Host the out-of-band producer after merge: run `tools/capability_traits.py --all` (built in plan 02-04) as a second action of the scheduled task `PP-Tower-Capsules`, or as a sibling task that uses the same `tools/hidden_launch.vbs` wrapper. | Every real-session read of the trait cache finds no file, so each trait reads `no-cache` and UNJUDGED. Nothing is ever read as ABSENT. |
| O-2 | Owner action, Phase 6 scope | Optional: a SessionStart detached refresh of the subject repository, using the `hooks/jit_warm.js` pattern. It needs a new file under `hooks/` plus an Owner registration. | None for Phase 2. It only shortens the window in which a freshly cloned repository has no cache. |
| L-1 | Not an Owner action | The liveness exit: the two PLANNED rows `capability_runtime/archetypes` and `capability_runtime/trait_scan` in `vault/liveness/reachability_registry.json` are removed when a live surface imports the modules (Phase 5 `modules/gsd_x/mission/envelope.py`, delivered in Phase 6). | Both units stay declared PLANNED, so neither is a liveness offender. |

The registry rows point here with `Owner queue: .planning/workstreams/ucep/phases/02-capability-subject-and-archetypes/02-OWNER-QUEUE.md`.
