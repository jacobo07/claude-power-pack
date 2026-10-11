---
covers: [mission-cost-hold, cost-hold-stops-worker, estimate-calibration, token_estimate_basis]
status: LIVE once the commit carrying this spec, gsd_mission.py, gsd_epoch.py, hooks/mission_wall.js and tools/test_gsd_mission_cost_hold.py lands
parent: vault/specs/mission-owner-hold.md, vault/specs/mission-envelope-and-compiled-wu.md
---

# A cost-breaker hold stops the spend; a hand-set estimate meets its lineage's measured cost

## Why (measured 2026-10-10/11, TUA-X Clock-A mission m-560939805e63)
1. The cost breaker tripped at 22:21Z on 74,491,187 processed tokens (estimate 36M, trip 2x). It set the
   Owner hold, whose contract is "nothing is launched, stopped, halted or renewed". The worker was mid-turn.
   It stayed in that one turn for 8.5 h, autocompacting itself 11 times (ledger `epoch_compacted`), and
   reached 265,537,374 processed: **191M spent after the breaker "stopped" it**. Its sibling m-4a0f39b59a60
   (estimate 31M) reached 152M the same way. The wall never fired either: each autocompaction reset the
   context percentage below the 40 % advisory, so `mission_wall.js` never asked for a hand-off.
   A cost hold whose purpose is "the Owner sees estimate, actual and cause BEFORE more is spent" could not
   reach the only thing spending.
2. The 36M estimate was typed by the arming session from a bottom-up guess, while the same lineage
   (m-f24648f187c5) had measured ~243M over ~24 h for Phases 7-9. Nothing compared the number with history.

## Contract
* **Cost hold kind.** `_cost_breaker` sets `owner_hold.kind = "cost"`. A hold whose reason begins
  `cost breaker` (records written before this change) is also a cost hold. Owner holds keep their contract.
* **The worker is told.** `mission_wall.js` (PostToolUse, every tool call of a mission worker) reads the
  mission record named by the worker's marker. Under a cost hold it returns `decision:"block"` with a COST
  HOLD notice: finish only the atomic step in progress, make it durable, end the turn with `HANDOFF NOTE:`,
  start nothing new. This runs before, and independently of, the context-wall check. The first notice is
  recorded in `mission-costhold-<sid>.flag` (`asked_at` ms, `n`, `hold_set_at`); later notices keep the first
  `asked_at`. A flag whose `hold_set_at` is not the current hold's `set_at` belongs to an earlier, released hold
  and is ignored by both the hook and the supervisor, so a re-trip always starts a fresh grace.
* **Progress is measured where the worker writes.** `mission_fingerprint` hashes the base work tree plus every
  `add_dirs` tree (unchanged when there are none). Measured 2026-10-11: m-4a0f39b59a60 (cwd InfinityOps,
  `--add-dir io-sidecar-fbig`) made 22 commits in the add-dir while the stall breaker, fingerprinting the cwd
  only, read 151M "since the work tree last changed" and held it. Used by the breaker, the T5 relay stall
  count, the renewal unchanged-tree refusal and the arm-time origin.
* **The worker is stopped.** `gsd_epoch.cost_hold_overdue(rec)` is true once the first notice is older than
  `COST_HOLD_GRACE_S` (600 s; per mission `wall.cost_hold_grace_s`). In `supervise`, a RUNNING mission under a
  cost hold whose owner is LIVE and overdue is stopped through `stop_owner` (background workers only, waits
  for the pid). On success the hold gains `worker_stopped_at` and `stop`; ledger `cost_hold_worker_stopped`.
  A failed stop is ledgered and retried on the next pass; nothing else changes.
* **Parked, not settled.** Under a hold carrying `worker_stopped_at`, a DEAD owner answers `none` (parked),
  not `settle`. Release then follows normal supervision: a DEAD owner is replaced by a fresh worker with the
  rehydration card, or halted if the budget is spent.
* **Every worker is reachable by the hook.** `mission_wall.js` named a mission worker only through its v2
  marker `gsd-autorun-<sid>.json`, and `_arm_worker_marker` refuses any resume command over 200 characters
  (the marker's typing limit). Measured 2026-10-11: both TUA-X missions (commands of 400+ and 213 chars) had
  NO marker, so neither the context wall nor the cost notice ever reached them, and the refusal was recorded
  nowhere. `session_start` now writes `mission-worker-<sid>.json` (identity, epoch, wall; no command, so
  nothing can type it) on every worker start, and the hook falls back to it. A refused marker is ledgered as
  `worker_marker_refused`.
* **Estimate calibration.** `set_envelope(token_estimate=...)` walks the `supersedes` chain (at most 6
  predecessors) and measures each one's processed tokens and lifetime hours. With at least one measurable
  predecessor, `expected = lineage tokens/hour x max_hours`. An estimate below `0.5 x expected` is refused
  unless `estimate_basis` (CLI `--estimate-basis`) states why; the basis and the calibration line are stored
  (`token_estimate_basis`, `token_estimate_calibration`). No measurable predecessor = accepted, with the
  calibration recorded as `no lineage history` (never treated as a zero rate).

## Acceptance (each can go red)
1. Hook: cost-held record -> block naming COST HOLD; same record with an Owner (non-cost) hold -> no cost
   notice; unheld -> null. The cost notice fires even when context is under the wall.
2. `cost_hold_overdue`: notice older than grace -> dict; younger -> None; no flag -> None.
3. Supervise: cost hold + LIVE owner + overdue -> stop_owner called once, hold gains `worker_stopped_at`;
   control: Owner hold + LIVE owner + overdue flag -> stop not called.
4. plan_next: cost hold with `worker_stopped_at` + DEAD owner -> none; without it -> settle (old behaviour).
5. Calibration: predecessor measured 240M over 24 h, max_hours 12, estimate 36M -> refused; with a basis ->
   accepted and stored; estimate 80M -> accepted; no predecessor -> accepted with `no lineage history`.
6. Mutation drills: drop the supervise stop -> 3 red; drop the calibration check -> 5 red.

## Rollback
Revert the commit. Records carrying `kind`, `worker_stopped_at` or the calibration fields are ignored by old
code. Kill switch for the stop alone: `CPP_COST_HOLD_STOP=off` (notice still sent, nothing stopped).
