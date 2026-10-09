# INCIDENT 2026-10-09: the coordinator pane bound itself to ce-lifecycle-v2

## What happened
- The coordinator pane (session 97a3d9cf) ran a PowerShell `Set-Location` into C:\Users\User\Apps\pp-ce-lifecycle-v2 to run
  `_logs\inst-l1\mutants.py`. This broke its own rule: "coordinators never cd into a goal root".
- The harness moved the session's primary cwd into the goal root.
- The live session_budget_guard then bound the pane by cwd and measured it from goal.since. That is the retroactive
  attribution R4 (WU-1B's fix, b62f9019, is NOT installed live).
- The guard refused the next Edit with: "used 39,407,773 of cap 8,847,012".
  - Before the bind: used 6,605,944, so the pane's attributed spend is about 32.8M.
- UNKNOWN: whether the guard already appended a settle for sid 97a3d9cf to `goal-budget/ce-lifecycle-v2/spend.journal.jsonl`
  (the earlier poisoning of ce-lifecycle-v, fc54a743, did settle).
  - If it did, every worker on this goal is now refused.

## State at the stop (nothing committed since b5f441b6, the approved continuation plan)
Uncommitted on ce/lifecycle-v2, verified:
- tools/gsd_mission.py: three install-blocking defects in WU-1H's halt_continue, fixed.
  1. `_receipt_present` now treats "stub" (any case) or `Status: IN PROGRESS|PARTIAL` as no receipt. WU-ADV's stub had read
     as done.
  2. New `spend_goal(rec)` resolves ce_goal / CPP_CE_GOAL / the cwd binding in the goal index. Sweep-armed records carry no
     goal or workstream, so halt_authority was always None and the code never renewed.
  3. The renewed successor is re-admitted against the predecessor's route_path, or held with the reason. renew_mission never
     carries admission, so launch would refuse it.
- tools/test_halt_continues.py: 13/0, adding V-LIFE-HALT-STUB-LOWERCASE, -READMITTED and -GOAL-BY-CWD.
  - _logs/inst-l1/mutants.py: 2/3 killed.
  - The STUB mutant survives because the test receipt matches both detectors.
  - Planned (refused) edit: split it into "checkpoint stub." and a separate "Status: IN PROGRESS" case (V-LIFE-HALT-STATUS-IN-PROGRESS).
- Also uncommitted from the dead WU-ADV worker: modules/provider_routing/ledger.py and the progress note.
- Live tree: UNTOUCHED.
  - Its gsd_mission.py / route_admission.py carry a foreign uncommitted LAUNCHABLE_VERDICTS change (cost-collapse E4a).
  - The install must commit by index (`git apply --cached`), never by pathspec, or it absorbs that change.

## Remaining plan steps (b5f441b6)
B1: merge with gsdx S1 (pp-gsdx-factory-2), not started. B2: L1 install, after the stub test split. B3: settle the 8 stopped
sids. B4: WU-ADV2. B5: packet immunization. B6: the chain.

## Next exact actions
1. Unbind the coordinator: its cwd goes back to C:\Users\User\.claude\skills\claude-power-pack.
2. Read the journal.
   - If sid 97a3d9cf was settled: a ledger repair, which needs an Owner decision. The live ledger has no lowering op;
     S1's `correct` is uncommitted.
   - If not: continue at the stub test split.
3. Trap for every packet and coordinator: never Set-Location / cd into a goal root. Use `python <abs path>` with `-C`-style
   absolute paths, or `Start-Process -WorkingDirectory` for a child.
