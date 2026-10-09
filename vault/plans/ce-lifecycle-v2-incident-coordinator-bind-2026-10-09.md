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

## Repair (Owner "yes" 2026-10-09, after 13:05 local)
- The settle was confirmed: journal seq 91-94 all carry sid 97a3d9cf, and that sid appears nowhere earlier.
  - seq 91: settle 32,579,283
  - seq 92: final reserve 222,546
  - seq 93: settle 32,801,829 (closes :1)
  - seq 94: final reserve 222,546 (:2)
- Backup: `~/.claude/state/goal-budget/ce-lifecycle-v2/spend.journal.jsonl.bak-pre-incident-repair-20261009`
  (23,405 bytes, 94 records).
- The four trailing rows were removed (1,012 bytes, sha256 32910ffff94d67cbe6c910533af1a868fd88f99409d616d34d28b12bb87afefd).
  - Byte-compare before replace; atomic os.replace.
- Re-fold, read-only (scratchpad fold_goal.py, mirrors GoalLedger._gfold): 90 records, cap 8,847,012, used 6,605,944,
  settled 4,469,374, open 2,136,570 (the 8 terminal leases, LEAKED), remaining 2,241,068. This is the pre-poison state.
- Superseded: the program moved to lineage ce-lifecycle-v3 (plan acaf6ad3, Owner option A). The v3 cap of 4,295,976
  already counts v2's certain remainder.
- v2 is therefore no longer bricked, but it is RETIRED.
- Double-spend check:
  - halt_continue fires only at a supervise stop transition, never on the six already-HALTED v2 records.
  - v2's halt authority is 2,241,068 - 2,136,570 = 104,498, below every packet estimate.
  - Closing v2 for good (lowering its cap to used) is an Owner decision; it was not done.
- Live L1 (3f9b57cc, prospective binding) means a coordinator cwd bind now measures from the bind point, so this shape
  cannot recur at this size.
