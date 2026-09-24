---
covers: [gex44-resident, goal-resident, resident-health, mission-record, recovery-census, cancel-by-handle, stagnation, F7, F8, F9, F10, F14]
status: APPROVED-BY-PLAN (kseip-p8-gdd-resident-20260924 §§28-34, 51-53; fixes F7-F10, F14)
owner: LANE RESIDENT (PP worktree factory/resident; NEW files only; never edits tools/gsd_x_goal.py
       or existing modules/gsd_x/goal/*.py — those belong to LANE GDD)
---

# GOAL RESIDENT (provisional working name) — the goal engine's supervised driver

## What it is and is not
A restartable driver of the EXISTING goal engine: each cycle it runs the engine's reconcile and
admission, dispatches through the engine's providers, and writes goal events only through the engine
API. It owns no goal truth, no judge, no second store, no second recursion. It is `sweep` made
resident, bounded and recoverable.

## Durable state (under a state dir from env GSDX_RESIDENT_STATE; default <goals_root>/../resident)
- `lock`: single-instance lock (O_EXCL file with pid + process start time; a stale lock is reclaimed
  only on positive evidence the holder is dead: pid absent OR start time differs).
- `heartbeat.json` (atomic replace): generation, pid, host, health, current goal@rev, mission id,
  provider, last_progress_ts, last_evidence_ts, budget snapshot, blockers.
- `missions/<id>.json` (atomic replace, CAS by a version field): identity, goal, revision, provider,
  provider attempt id, worktree, base commit, declared write set, pgid, process start time, scope unit
  name / claude bg id when present, state, uncertainty flags, created/updated ts. States:
  PROPOSED, ADMITTED, ISOLATED, DISPATCHED, RUNNING, RETURNED, HARVESTED, JUDGED, RECONCILED; terminal
  CANCELLED, EXPIRED, LOST, STALE_REVISION, UNCERTAIN. Illegal transitions raise.
- `intents.jsonl` (append-only): intent + provider attempt id written BEFORE any dispatch (F9).
- `gain.jsonl` (append-only): per goal per cycle, the information-gain verdict (F10).
- `leases/<resource>.json`: holder, heartbeat ts, TTL; expired leases are reclaimable (F14).
- STOP file: `<state>/STOP` — present ⇒ the loop exits cleanly after cancelling owned missions.

## Health (computed, never asserted)
HEALTHY, IDLE_NO_APPROVED_GOAL, RUNNING, WAITING_FOR_PROVIDER, WAITING_FOR_EVIDENCE,
WAITING_FOR_AUTHORITY, STALLED, DEGRADED, RECOVERING, FAILED. HEALTHY requires progress (gain) within
a configured window; an alive loop with no gain is STALLED, never HEALTHY.

## Cycle (bounded: max cycles per wake, max wall per mission, sleep bounds)
recover → load goals that are governed (authority.is_governed, when mode != ABSENT) and autonomous
and not paused → for each: engine reconcile → pick at most one mission per goal by the reconciler's
decision → admit (licence verdict, provider caps, leases, pause, stop file) → record intent → dispatch
via the engine provider → persist mission → observe/harvest on later cycles → hand receipts to the
engine (never judge itself) → gain verdict → heartbeat.

## Recovery census (F9)
On start: for every non-terminal mission record: probe the provider by its handle (probe/observe) and
the process by pgid + start time; classify DONE (receipt available), INCOMPLETE (provably not
started or provably dead with no effect), UNCERTAIN (anything else). UNCERTAIN missions are reconciled
against the provider's own record (intent attempt id) before any retry; a mission is never
re-dispatched blind.

## Cancel (F7)
By handle, not by pgid alone: provider cancel (which kills the POSIX process group since 908b543),
plus scope unit stop / `claude stop <id>` when the record carries one; then an orphan census by pgid
(POSIX: /proc scan for the pgid) whose result is recorded; a failed stop is a recorded failure, never
swallowed.

## Stagnation (F10)
Gain = change in obligation state, verdict, or failure signature set for the goal between cycles.
Commits, receipts and tree moves alone are NOT gain. K consecutive no-gain cycles ⇒ STALLED for that
goal ⇒ escalation record in order: RCA mission, provider/method change, subgoal, decision packet.

## Entrance
`tools/gsd_x_resident.py` with `run` (the loop, what systemd calls), `once` (one cycle), `status
[--json]`, `stop` (writes STOP), `census`. The systemd USER unit template under
`install/gex44/goal-resident.service` (Restart=always, RestartSec bounded, KillMode=control-group,
ExecStopPost = `census`, absolute PATH including /home/factory/.local/bin — non-interactive ssh does
not read ~/.profile, measured 2026-09-24).

## Proof (tools/test_gsd_x_resident.py, V-RES-*; both poles each; fake providers + temp stores)
lock refusal + stale reclaim only on evidence · STOP honoured mid-cycle and owned missions cancelled
· intent written before dispatch (a crash injected between intent and dispatch yields UNCERTAIN and
no second dispatch) · census classifies DONE/INCOMPLETE/UNCERTAIN · reused pid with different start
time is not "alive" · noise-committing fake provider reaches STALLED within K (control: a provider
that closes an obligation keeps HEALTHY) · expired lease reclaimed, live lease respected · health is
never HEALTHY without gain · cancel records orphan census; a failing stop is recorded · ungoverned or
paused goal is not admitted. Linux-only cases (process groups, /proc) print UNJUDGED on Windows.
Chaos on GEX44 later (wave H): kill -9 mid-mission, unit stop during mission, real reboot.
