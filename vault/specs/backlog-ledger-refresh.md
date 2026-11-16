---
covers: [backlog-ledger-refresh, reconciliation-ledger, sessionstart-backlog]
tier: T2
owner_decision: "campaign 1 obligation 3; Owner 'go ahead' 2026-11-16"
---
# Backlog ledger: autonomous refresh (campaign 1, obligation 3)

## Problem (measured)
The reconciliation ledger (`modules/backlog_autopilot/ledger.py`, 2 coverage metrics) is rebuilt only when someone
runs `/backlog-to-capability`. The tracked copy `vault/programs/ascension/phase2/reconciliation_ledger.json` says 471
obligations (GEX44, base 2f9386f6); a laptop rebuild on 2026-11-16 says **472**, RECONCILIATION 373/472, OPERATIONAL
3/374, VERIFY PASS, **148 s** wall. Nothing autonomous notices that drift. Law 1: a built ledger nobody re-runs is
presence, not reconciliation.

## Constraints that shape the design
- 148 s is far past any SessionStart deadline (chain budget 4000 ms, 7.4 s already measured before its pool under
  RAM starvation). The build therefore never runs inside the hook: the hook is a cheap GATE that may launch a
  detached worker.
- Host RAM is the recurring hazard (2.3 % free measured this session). The gate refuses below a free-memory floor.
- ~80 PP worktrees exist on this host. Cardinality is bounded: the gate acts only for the PP tree the hook itself
  lives in (`path.resolve(__dirname, '..')`), only when the session cwd is inside it, at most once per interval, one
  worker per tree (O_EXCL lock).
- The live tree has concurrent writers and thousands of dirty paths: the refresh writes ONLY under
  `~/.claude/state/backlog_ledger/`, never the tracked JSON (that stays an explicit, committed `/backlog-to-capability`
  act).

## Architecture
1. `hooks/backlog_ledger_refresh.js` (SessionStart-chain member, Node, <100 ms):
   kill switch `CPP_BACKLOG_REFRESH=off` -> cwd inside PP root -> PP root has the ledger module ->
   ANNOUNCE (if the newest history row is newer than the `.announced` marker, emit ONE additionalContext line with
   coverage, delta vs the previous row, verify verdict, age, and write the marker) -> lock held and < 1 h old: skip ->
   newest attempt younger than `CPP_BACKLOG_REFRESH_INTERVAL_H` (24): skip -> `os.freemem()` below
   `CPP_BACKLOG_REFRESH_MIN_FREE_MB` (3072): skip, gate row written -> spawn the worker detached, hidden, unref'd.
   Every spawn and every low-memory skip is a row in `<slug>.gate.jsonl`.
2. `tools/backlog_ledger_refresh.py --root R --slug S` (worker): acquires `<slug>.lock` with O_EXCL (stale > 1 h is
   broken once), lowers its own priority, builds inventory + ledger + verify, writes `<slug>.json` atomically
   (tmp + os.replace) and appends one row to `<slug>.history.jsonl` -- including on failure (`error` field), so a
   broken refresh is visible and also rate-limited. Releases the lock in `finally`.
3. Consumer: the gate's ANNOUNCE step on the next PP session start. The snapshot is also the input
   `/backlog-to-capability` can diff against.

## Acceptance (V-BLR-*, `tools/test_backlog_ledger_refresh.py`, both poles, hermetic state dir)
- GATE-SPAWN: fresh state, cwd inside root, memory ok -> decision spawn.
- GATE-KILL / GATE-OUTSIDE / GATE-FRESH / GATE-LOCKED / GATE-LOWMEM: each one skips, with its own reason.
- GATE-STALE-LOCK: a lock older than 1 h does not block.
- ANNOUNCE-ONCE: a new history row is announced once, with delta; the second session start is silent.
- WORKER-REAL: the worker run against a small synthetic root writes snapshot + history with VERIFY result.
- WORKER-FAIL-VISIBLE: a root without the module writes an `error` history row and releases the lock.
- WORKER-SINGLE-FLIGHT: a held fresh lock makes a second worker exit without building.
- WIRED: the dispatcher's SessionStart-chain lists the gate.

## Evidence (laptop, 2026-11-16, worktree Apps\pp-bcap-verify)
- `tools/test_backlog_ledger_refresh.py`: V-BLR 18/18, rc 0. The worker's contract runs against a stub package with
  the same interface: the real package cannot be lifted out of the repo (`__init__` -> engine -> modules.ias_c2).
- End to end, through the real entrypoint (`node hooks/backlog_ledger_refresh.js`, SessionStart JSON on stdin, private
  state dir): the gate spawned pid 6852; the detached worker built the REAL ledger at head d3840f07 in 118 s, verify
  PASS, RECONCILIATION 373/472, OPERATIONAL 3/374, and released its lock. The next start announced exactly that line;
  the one after was silent and launched nothing (1 gate row).
- Honest caveat: free memory was 3044 MB, under the 3072 MB floor, so the proof ran with
  `CPP_BACKLOG_REFRESH_MIN_FREE_MB=0`. On this host as measured, the default gate would have refused (by design).
- Neighbours: test_hook_registration_integrity 15/15, test_floor_regression_gate 70/70. test_kresume_autotype 30/35
  fails identically on the committed control d3840f07 without this change (pre-existing, not caused here).

## Live-tree incident and fix (2026-11-16, same pane)
- Observed: the first LIVE-tree worker (pid 33948) was still building after 30 min, then vanished with no history row
  and its lock left behind. A kill from outside runs neither `except` nor `finally`, so the failure was invisible: the
  gate would have said "worker running" for an hour, then "never refreshed".
- Cause of the slowness (faulthandler stack dumps every 60 s, two probes > 540 s): `inventory._grep_refs`, once per
  unresolved seed, walked the WHOLE root, including 24 nested PP worktrees under `.claude/worktrees` (each with its own
  `.git`), so roughly 25 repo copies, read in full, per seed. It also let another branch's copy answer
  REFERENCED_ELSEWHERE.
- Fix 1 (`modules/backlog_autopilot/inventory.py`): a subdirectory holding `.git` is another checkout and is skipped;
  every unresolved seed is answered in ONE sorted walk (`_grep_refs_multi`). Old vs new on the worktree: identical
  statuses and sources, 80.4 s -> 3.7 s. LIVE tree, full build: 318 s (inventory 277, ledger 41), VERIFY PASS,
  RECONCILIATION 400/542 (the live tree holds more obligation files than the worktree's 472).
  V-ASC-INV: nested checkout stays NOT_OBSERVED (fails against the unfixed module), plain subdir still found.
- Fix 2 (gate): a lock whose pid is no longer alive becomes a history row `{killed: true, error: ...}` dated at the
  lock, the lock is removed and a `reaped` gate row written; the next start announces it as FAILED and the interval
  rate-limits it (no respawn loop). Replayed on the real incident state: announced "worker pid 33948 died without a
  result ... killed from outside", no spawn. V-BLR 25/25 (7 new REAP checks, including a live holder left untouched).
- Not established: WHAT killed pid 33948 (no OS evidence collected). The fix makes the next one visible; it does not
  name the killer.

## Rollback
`CPP_BACKLOG_REFRESH=off` (per process), or delete the one SessionStart-chain line. State lives only under
`~/.claude/state/backlog_ledger/`; deleting that directory loses nothing that the tracked ledger does not hold.

## Not in scope
The live dispatcher line (`~/.claude/hooks/hook-dispatcher.js`) is obligation 5 (Owner-gated, after the branch is
fast-forwarded). Until then the gate is proven at the repo copy of the dispatcher and by its test.
