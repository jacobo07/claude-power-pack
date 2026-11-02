# S9 Knowledge Vault incidents: Mission Control + Exactness Bridge

This file is the record for the addendum's 17 Lane A seeds and the Lane B seeds, plus incidents found during S9.

Status values:
- **FIXED** means code and a regression gate exist.
- **SMOKE** means the fix is also proven on the real host by the MC-PR canaries.
- **OPEN** means the incident is named and not repaired.

Code anchors:
- PP Lane A: `98504a8d`.
- t1 lease: `b567bc8a`.
- t1 census: `8adf4843`.

## Lane A: Mission Control

| # | Symptom | Root cause (read in code) | Earliest detectable | Why missed | Repair | Regression | Status |
|---|---|---|---|---|---|---|---|
| 1 | not_before parked only when no worker remained | `resource_gate` returned early for any non-DEAD owner ("its successor is what waits") | the first clock wait with an idle worker | the not_before gates drove dead owners only | park and stop a LIVE IDLE owner; a busy owner finishes its turn; kill switch `CPP_WAIT_PARK_LIVE` | V-S9-WAIT-IDLE-LIVE-*, MC-PR1 | FIXED, SMOKE pending |
| 2 | an idle worker consumed epochs while waiting | same as #1: the turn continuation ran under an unmet requirement | the ledger's `turn_continued` rows during a wait | no gate counted epochs during a wait | parked means plan_next answers `none`, and the worker is stopped | V-S9-WAIT-STOPPED-NOT-SETTLED, MC-PR1c | FIXED, SMOKE pending |
| 3 | Owner hold was used as a pause | the only pause-shaped verb was `hold`; `hold --stop` existed but nobody used it | the first hold-then-wait | the operator's mental model; nothing refused it | an Owner hold now outlives its worker (parks, does not settle); `requires --not-before` / `checkpoint` are the machine waits | V-S9-HOLD-OUTLIVES-WORKER | FIXED |
| 4 | the hold made the mission terminal | `plan_next`: Owner hold plus DEAD owner meant `settle` meant HALTED (m-38e82763a156) | the first idle worker ending under a hold | the settle rule was written for cost holds (EDD singleflight) and applied to every hold | settle only cost holds; kill switch `CPP_HOLD_SETTLES=on` | V-S9-HOLD-OUTLIVES-WORKER + V-S9-HOLD-COST-STILL-SETTLES | FIXED |
| 5 | release did not resume (the mission was already HALTED) | consequence of #4 | — | — | consequence of #4 | — | FIXED |
| 6 | hours lost despite a known unblock time | #1 plus #4, and max_hours counted waiting time | any long wait | wait time was execution time in `budget_exhausted` | `waited_s` is excluded from max_hours | V-S9-WAIT-NOT-MAX-HOURS | FIXED |
| 7 | the cost breaker measured gen3-pp while the work was in t1 | m-f9560b5e8f1f was armed with `add_dirs []`; nothing could add a repo to a live mission | at arm (a plan naming a sibling repo) | no Workset concept; add_dirs only at arm | `workset --add` on a live mission; every fingerprint site uses `mission_fingerprint` | V-S9-WORKSET-*, MC-PR2 | FIXED, SMOKE pending |
| 8 | real progress was classified as a stall | #7 | — | — | #7 | — | FIXED |
| 9 | a manual status commit in gen3 was the workaround | #7 | — | — | #7; the workaround is retired by workset | — | FIXED |
| 10 | batch spend overshot while jobs were in flight (F6) | `llm_fix.one()` checked `spent >= budget` only at dispatch, with `--jobs` agents in flight | S8d r1: $35.45 against $30 | spend gates measured settled spend only | `Lease`: reserve worst case (5.2 USD, measured max 5.13 over 1081 results) before dispatch; settled + reserved <= budget; `lease.json` receipt | V-LEASE-* 11/11 (the control reproduces 36 > 30) | FIXED; first production receipt at the next llm_fix run |
| 11 | a decision was recorded without waking the idle worker | `deliver_decision` on "host unreachable" left it to "the next launch card", which never comes for a parked idle worker | the first decide from a plain ssh shell | no retry obligation | `pending_wake`; the sweep delivers it when the owner is idle, and never through a standing hold | V-S9-WAKE-*, MC-PR4 | FIXED, SMOKE pending |
| 12 | a second decide was needed | #11 | — | — | #11 | — | FIXED |
| 13 | mission-id handling after a failed arm | operator `ls -t gsd-mission-*.json`; code paths read the arm result correctly (the scan's "helpers glob newest" was a false positive: they enumerate all records) | the first operation after a failed arm | nothing asserted where a mission lives | `--expect-cwd` on decide/hold/release/requires/checkpoint/workset | V-S9-ID-*, MC-PR5 | FIXED, SMOKE pending |
| 14 | `HALTED no_progress` used for "wave complete" | no state meant "wave closed, Goal open"; three fresh workers booted on a closed wave | the first wave close | the state machine had stall and done only | checkpoint states plus the CHECKPOINT blocker class (owner_required False) | V-S9-CKPT-*, V-S6 72/72, MC-PR6 | FIXED, SMOKE pending |
| 15 | Git mutation is the only progress sensor | fingerprint = HEAD tree + dirty paths | — | — | partly: the Workset widens the sensor; semantic receipts are not built | — | OPEN (no evidence-delta receipt yet) |
| 16 | multi-repo missions are not one workset | see #7 | — | — | `workset()` with roles control/product/runtime/evidence | V-S9-WORKSET-ROLES | FIXED (roles are not consumed by any observer yet) |
| 17 | no first-class WAIT state that releases the lease | waits were Owner holds | — | — | WAIT_TIME / WAIT_RESOURCE / checkpoint holds release the worker | MC-PR1 | FIXED, SMOKE pending |

## Found during S9

| # | Incident | Repair | Status |
|---|---|---|---|
| S9-1 | HR-2: the GEX44 PP clone was ff'd to `98504a8d` before its end-to-end smoke. That clone is the live sweep (9 foreign missions), so the ff was a deploy | STOP and report; the Owner chose roll back, then smoke. `git reset --keep fa32ba2f` 6 min later; the ledger shows no new-code event in the window; memory `feedback-gex44-mission-ops-from-ssh` item 6 | CONTAINED |
| S9-2 | `_lease_contention` used `ms` without importing it, so the fail-open block always returned None (lease contention was never reported) | import added | FIXED (V-S9-LEASE-CONTENTION-IMPORT) |
| S9-3 | V-AMCR-ONE-RESOLVER-INVENTORY red: 2 deterministic-path sites derived the root themselves | `mb.execution_root` | FIXED (AMCR 38/38) |
| S9-4 | review race: a pending wake could resume the worker that resource_gate had just parked in the same pass | `retry_pending_wake` clears and never wakes through a hold | FIXED (V-S9-WAKE-NEVER-THROUGH-HOLD) |
| S9-5 | the pp-code-reviewer dispatch was refused twice (agent-solo guard on a foreign pane's agent, then an admission duplicate of the blocked call) | reviewed inline (Regla 12) | PROCESS: the admission ledger should not admit a call the solo guard blocked |
| S9-6 | test_gsd_epoch is 108/111 on both baseline and change; one red varies under <3 GB free | 2026-11-02: laptop 106-108/111 at 2.2-3.6 GB free with a different red set each run; GEX44 (52-53 GB free) 111/111 three times at `9915d59c` and three at `24d117e2`, and 111/111 with `CPP_ADOPT_FINISHED=off` | CLOSED: memory-pressure variance of the laptop plane, not a code defect (T-LOW-RAM-SUITE-NAMES-DRIFT-001) |
| S9-7 | V-MC-PLAN-FACTS-REFUSES-OVERLAP is red on GEX44 only (node v18 against ^22) | Reviewed 2026-11-02: `node_bridge.node_exe()` prefers `CPP_NODE_EXE`; the sweep unit sets it to v22.23.3, so the live path never runs v18. Red only when the suite runs from a plain ssh shell (system node v18.19.1). With the sweep env on GEX44: MC 242/242, gate green | CLOSED: environment, not a product defect. Run suites with the sweep unit's env |
| S9-8 | Canary run 1 (m-514bd00df395, isolated state): a worker that finishes its turn before the next sweep pass is never adopted. `plan_next` LAUNCHING refuses to adopt a launch whose host row is already `done`, waits out the 300 s ack deadline, and relaunches (LAUNCH_RETRY): one wasted boot per retry. Pre-existing (not Lane A). It surfaced because the canary prompt was one word | PP `9915d59c`: `plan_next` LAUNCHING adopts a host row `done` as "ran", FRESH launches only (`pending.kind == worker_start`; a `--resume` continuation reuses the old id, so its `done` row is the previous turn; the first cut turned 5 test_gsd_epoch gates red); `failed`/`stopped`/`exited` still count as failed launches; kill switch `CPP_ADOPT_FINISHED=off`. Plus `24d117e2` (S9-10) | SMOKE: real-host canary 16/16 at `24d117e2` (m-2ddd196123bd, isolated state). Live GEX44 clone NOT moved (still `98504a8d`); deploy needs separate Owner go |
| S9-10 | S9-8 canary run at `9915d59c` (m-8cd4f6e1a7f3) was 15/16. B4 failed: `adopt_launched` armed a worker marker for a mission whose command is not a `/command`, MarkerError raised after the record was RUNNING, and the sweep pass returned rc 3. Already latent (noted 2026-10-06); S9-8 made the adopt path reachable for every fast finisher | PP `24d117e2`: the adopt path ledgers `worker_marker_refused` like session_start; the adoption stands. Gate V-MC-ADOPT-MARKER-REFUSAL-NOT-A-PASS-ERROR (MC 242/242; an unguarded red control reproduces the canary error, 241/242) | FIXED + SMOKE (canary 2 B4 PASS) |
| S9-11 | Canary limitation: the real turn-end judgement chose a fresh worker, not `--resume`, so B1 was judged on a continuation-shaped record built from the real record plus the real prior `done` row; no natural `--resume` launch was observed on the host | unit V-MC-CONTINUATION-DONE-ROW-NOT-ADOPTED + test_gsd_epoch 111/111 x3 on GEX44 (52 GB free) | OPEN (natural `--resume` real-host observation) |
| S9-12 | A mission parked at a checkpoint cannot be closed when a new plan replaces it: `arm --supersedes` refuses ("not an attempt of this goal") because a mission without a workstream has goal key None; `checkpoint --clear` would relaunch the old command. Seen arming S10 over m-9f94bef51619 | left parked (nonterminal, no worker, no spend); S10 armed plainly as m-e6e0340e743d | OPEN (machinery: a `checkpoint --close-superseded-by <mid>` verb or a cwd goal key) |
| S9-9 | Canary run 1 design error: the canary assumed a finished bg worker reads `status: idle` while alive. Real rows read `state: done` (DEAD) within seconds | canary v2 holds the worker BUSY (`sleep 200`) and sets the wait mid-turn, the real incident shape | FIXED (method) |

## Lane B seeds

| Seed | Evidence | Status |
|---|---|---|
| weak capability gate promoted D11 to 10 | S6 report caveat: 21 vs 20 of 40, one sample, within noise | OPEN (B5) |
| D01/D02 do not represent structural gains | S8 moved 73+5 NO_COMPILE to compile, D01 = D02 = 2 | OPEN (B5) |
| 0/27 model follow-up on the unlocked regime | S8d r1; no generic retry on that regime without a causal delta | RULE (enforced by plan) |
| S8 transition corpus not harvested | harvested: 78 rows, 10 classes (t1 `8adf4843`) | FIXED |
| s8b-diagnosis was assumed to be the 73 minus 4 | it overlaps the 73 on 20 only | premise corrected (census) |

## UKDL candidates

Hard rules:
- HR-MISSION-WAIT-ZERO-EXECUTION: a waiting mission spends no epoch, iteration or model call; the wait releases the worker.
- HR-HOLD-IS-NOT-SETTLE: an Owner hold outlives its worker; only a cost hold settles.
- HR-SPEND-RESERVE-BEFORE-DISPATCH: settled + reserved <= envelope.
- HR-LIVE-CLONE-IS-DEPLOY: moving the HEAD of a tree a scheduler runs is a deploy (HR-2 applies).

Process rules:
- PR-WAVE-CLOSE-IS-CHECKPOINT: a closed wave declares a checkpoint, never idles into no_progress.
- PR-SMOKE-IN-ISOLATED-STATE: smoke runtime code from a worktree with its own state dir before moving the live tree.

Traps:
- T-ACTIVITY-AS-PROGRESS.
- T-HOLD-AS-PAUSE.
- T-COMPILE-GAIN-AS-EXACT-GAIN.
- T-21-VS-20-AS-CAPABILITY.
- T-73-RESIDUALS-AS-73-PROMPTS (they are 10 classes).
