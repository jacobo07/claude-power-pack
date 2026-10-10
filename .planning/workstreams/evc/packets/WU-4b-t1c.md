# WU-4b-t1c — finish plan 01-02 Task 1 on the half-edited tree (evc/e2)

You are in `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\evc` (branch `evc/e2`). Work only here.
Use the PowerShell tool for git and python. git = `& 'C:\Program Files\Git\cmd\git.exe'`,
python = `& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'`. Set `$env:PYTHONIOENCODING='utf-8'` first.

## State you inherit (do not redo it)
The previous unit was stopped mid-task. Uncommitted and KEPT: `tools/test_evc_usage_truth.py` (section_statement gates),
`tools/mission_spend.py` (V_* constants, format_age, snapshot_of, spend_statement, hold_text). In `tools/gsd_mission.py`
ONE edit landed: the final `plan_next` hold reason calls `_ms.hold_text(hold, verdicts, now)` — but `_ms` and `verdicts`
are not defined yet, so `plan_next` raises NameError. Confirm with `git diff --stat` first.

Spec reference only if needed: `.planning/workstreams/evc/phases/01-usage-truth-plane/01-02-PLAN.md`, Task 1 `<action>`.

## Do exactly these 4 edits to tools/gsd_mission.py, ONE Edit call per message, never in parallel
(Parallel edits to one file are refused by this host; that is what stopped the previous unit.)
1. In the `plan_next` hold branch, before the RUNNING/BLOCKED check: `import mission_spend as _ms` (lazy, inside the
   function), `verdicts: list = []`, `lrow = None`; inside the RUNNING/BLOCKED-with-owner case set
   `verdicts = [(verdict, evidence)]` from the liveness() pair already computed there.
2. In the LAUNCHING case: `verdicts = [(DEAD, <host row state>)]` when the launched row is listed finished, else
   `[(LIVE, <host row state>)]` when listed; empty when not listed.
3. `set_owner_hold(mission_id, reason, now=None, measured=None)`: when `measured` is a dict, store it in the owner_hold
   dict under "measured". Record reason text, event name and ledger row unchanged.
4. `_cost_breaker`, on a trip, before set_owner_hold: in its own try block
   `measured = ms.snapshot_of(ms.usage_truth(rec), spent, now)`; on any exception
   `measured = ms.snapshot_of(None, spent, now)` and ledger one `cost_breaker_snapshot_failed` row (exception class +
   message cut to 300 chars). Pass `measured=measured`. Keep `spent = (measure or ms.processed_tokens)(rec)` unchanged.

Re-read the lines around each anchor before editing (line numbers moved).

## Verify (each once, foreground)
- `python tools\test_evc_usage_truth.py` (V-EVC-STATEMENT-ALIVE and -CONTROL must PASS)
- `python tools\test_gsd_mission_owner_hold.py`
- `python tools\test_mission_spend.py`
One fix attempt per failure, at most 3 in total.

## Finish
All three exit 0 → `git commit -m "feat(evc-01-02): task 1 -- Tracer -- breaker trip stores a snapshot and plan_next prints the live-worker statement" -- tools/gsd_mission.py tools/mission_spend.py tools/test_evc_usage_truth.py`.
Otherwise do not commit; report BLOCKED.

## Never
No edits outside those three files. No reset, clean, restore, stash, amend, rebase, push or force. No subagents.
No EnterWorktree. No questions.

## Report (your final message, nothing else)
```
WU-4b-t1c STATUS: DONE | BLOCKED:<reason>
HEAD: <git rev-parse --short=8 HEAD>
COMMIT: <sha or none>
VERIFY: <each command: exit code and its final summary line>
```
