# caa-wake W1R-1 receipt

status: GREEN

## Decision
Fix the salvaged engine in place. wake_check.py delegates --waits/--delta/--declare/--supersede to mission_wait.cli; --consume unchanged; any other argument exits 2 before any gate or write. git_object leaves take an optional `contains` (git cat-file -p through run_cmd; unreadable body = UNKNOWN).

## Effect
tools/mission_wait.py, tools/wake_check.py, tools/test_mission_wait.py committed. The engine needed no fixes beyond `contains`; all 11 gates passed first run.

## Proof
WAIT_PASS=13/13 (V-WAIT-PRESAT, OFFLINE, DUP, CONCURRENT, INVALIDATOR, EXHAUSTED, NOWORK, REFUSED, CYCLE, KILL, WORKTREE, ARGV, CONTENT: all PASS)
WAKE_CONSUMER_PASS=8/8

## Unknowns
Mutants (edge-triggered, no-CAS, skipped invalidator, work-tree read, UNKNOWN-as-satisfied) not run: W1R-2. Live probes (mission_spend goal-status, gsd_mission _scan) are injected in tests, not exercised.

## Commits
675d573f (code + tests)

## Close
Mission m-3f3c48d7404d (cwd pp-caa-wake-t2, W1R-2, capsule-v2, max-cycles 3, max-hours 4). Envelope set 600000 sonnet. Admit verdict: ROUTE ADMISSIBLE need=227002 target=550000.
