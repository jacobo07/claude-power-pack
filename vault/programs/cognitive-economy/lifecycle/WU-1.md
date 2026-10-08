# ce-lifecycle-v WU-1 -- prospective binding + observer isolation (EXECUTION)

Card: vault/plans/ce-lifecycle-vertical-slice-plan-2026-10-08.md sections 1 (R4, R5, R7), 3 (WU-1 row), 4 (items 4, 5) and
vault/plans/ce-lifecycle-L2-addendum-2026-10-08.md items 2, 3, 5. Read nothing else. No transcripts, never the bootstrap prompt.
Goal ce-lifecycle-v. Lease 0.9M work + 0.25M checkpoint reserve; plan <= 26 tool calls; commit after each step.
cwd = C:\Users\User\Apps\pp-ce-lifecycle-v (branch ce/lifecycle-v). Edit and commit ONLY here, never under ~/.claude (HR-001).
git = & 'C:\Program Files\Git\cmd\git.exe'; python = & 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'.
Commit with `git commit -F <msgfile> -- <paths>` (one new msgfile per commit), verify `git log -1 --format=%s`.
Never push, reset, stash, merge, checkout another branch. PowerShell tool, not Bash.

Do:
1. Extract the resolver (ex-L1 step 2): move goalBinding/normPath/under (hooks/session_budget_guard.js:183-206) to
   hooks/lib/goal_binding.js, same behaviour; guard requires it. tools/test_goal_budget_admission.py stays at its HEAD
   result (it is flaky 52-54/54 at HEAD -- run twice, record both). Commit.
2. Binding record: goal_binding.js resolves, in order, (a) state/goal-binding/<sid>.json if present (immutable once
   written: {goal, since_ts, source: launcher|explicit|cwd, pid}), (b) env CPP_GOAL only when that record exists and
   agrees (else ignore + ledger warning), (c) cwd under a goal root -> WRITE the record with since_ts = now (first call
   of this session that sees the binding). A session whose record already names another goal (or "none") is never
   re-bound by cwd. Python twin in tools/mission_spend.py (same order). Honour stateDir() / GSD_LONG_RUN_STATE_DIR.
3. Prospective measure: session_budget_guard.js goal accounting (lines ~271-344) counts a session's records only at or
   after max(goal.since, binding.since_ts). Pre-binding tokens of that session go to a `prebind` counter written as a
   journal op `{op:"prebind", sid, measured}` once (category PRE_BINDING_PROGRAM_CAPEX, never in `used`). Kill switch
   CPP_PROSPECTIVE_BIND=0 restores old behaviour. Commit.
4. Observer isolation: a session whose binding record is source=launcher for goal X never binds goal Y by cwd; a session
   whose only tool calls are read-only (Read/Grep/Glob, `goal-status`, `git log/status/show`) does not write a cwd
   record until its first mutating call (Write/Edit/git commit/arm). Commit.
5. Roots: goal-declare refuses a --root already held by another goal whose remaining > 0 (exit non-zero, names it);
   add `goal-unroot --goal G --root R` that removes a root only from a goal with remaining <= 0 or state superseded
   (no --owner needed: it removes authority, never adds). Commit.
6. `gsd_mission.py arm --goal G`: stored in the record; at launch the supervisor writes
   state/goal-binding/<new sid>.json {source: launcher} for the worker (where the sid is known: --session-id), so the
   worker never binds by cwd. Commit.
7. tools/test_process_lifecycle.py (keep existing V-LIFE-PREMODEL-TRANSPORT gates) + V-LIFE-BIND-RETRO (replay: goal
   since 09:09, session records from 08:00, binding at 09:41 -> used counts only >= 09:41; prebind row present),
   V-LIFE-BIND-RETRO-CONTROL (session bound at start -> all counted), V-LIFE-OBSERVER (read-only session in root ->
   no record), V-LIFE-LAUNCHER-WINS, V-LIFE-ROOT-OVERLAP (declare refused), V-LIFE-UNROOT (refused on live goal),
   V-LIFE-ARM-GOAL. Hermetic temp state dir. Mutants (copied file): drop the since_ts max -> RETRO red; let cwd
   override launcher -> LAUNCHER-WINS red. Run test_process_lifecycle, test_goal_budget_admission, test_hook_boundary,
   test_gsd_mission. Record exit codes; pre-existing reds recorded vs HEAD, not fixed.
8. Receipt vault/programs/cognitive-economy/lifecycle/WU-1-receipt.md (<= 30 lines): commits, gates + exit codes,
   mutants, deploy recipe (files + sha256 + backup + rollback; deploy is NOT yours), spend, reforecast, UNKNOWNs.
9. Write WU-2.md + route-WU-2.json (same shape as this file / route-WU-1.json; lease from the plan's WU-2 row) from
   plan section 3/4 item 1-3. Commit all. Do NOT arm.
Two failures of the same shape = stop, blocker into the receipt. End with `HANDOFF NOTE: WU-1 done` (or the blocker).
