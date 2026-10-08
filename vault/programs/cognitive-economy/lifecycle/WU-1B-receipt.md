WU-1B receipt
Packet sha 7810a4323cc3. Base e634546d.
Step 1: salvage patch git apply --check OK, applied whole (2 files, 0 rejected hunks, SALVAGE_REJECTED: none). node --check OK on both.
Step 2: tools/mission_spend.py: goal_prebind + CLI goal-prebind, resolve_binding (+ read/write_binding, is_read_only_call,
  prospective_bind) = twin of hooks/lib/goal_binding.js; CPP_PROSPECTIVE_BIND=0 kill switch kept.
  modules/provider_routing/ledger.py: GoalLedger.prebind + fold op "prebind" -> PRE_BINDING_PROGRAM_CAPEX, never in `used`.
Step 3: tools/test_process_lifecycle.py: V-LIFE-BIND-RETRO, V-LIFE-BIND-CONTROL, V-LIFE-OBSERVER (+ V-LIFE-BIND-TWIN).
  Mutants (tools/mutation_drill.py, isolated copy), all KILLED:
   RETRO    guard: since = goalSince                      (_logs/wu1b/drill-retro.txt)
   CONTROL  goal_binding.js prospective() -> true         (drill-control.txt)
   OBSERVER goal_binding.js read-only branch disabled      (drill-observer.txt)
Step 4: test_process_lifecycle LIFE_PASS=6 LIFE_FAIL=0 | test_goal_budget_admission GOAL_PASS=54/54 |
  test_hook_boundary HOOK_PASS=7/7 | test_gsd_mission MC_PASS=224/225.
  The 1 failure, V-MC-SUP-HOST-UNANSWERED-NOT-BLOCKED, is PRE-EXISTING: also FAILs on a git-archive export of HEAD
  (_logs/wu1b/gsd_head.txt, 223/225 there). Not caused by this change; open point for the owner of the supervisor.
Calls: 1 epoch, ~21 model calls (over the 13 target; context stayed small).
Deploy recipe (NOT run, HR-001; Owner/live-checkout step), from this worktree to the live checkout <LIVE>:
  Copy-Item hooks\lib\goal_binding.js        <LIVE>\hooks\lib\goal_binding.js
  Copy-Item hooks\session_budget_guard.js    <LIVE>\hooks\session_budget_guard.js
  Copy-Item tools\mission_spend.py           <LIVE>\tools\mission_spend.py
  Copy-Item modules\provider_routing\ledger.py <LIVE>\modules\provider_routing\ledger.py   (needed by goal-prebind)
  then in <LIVE>: node --check both js files; python tools\test_goal_budget_admission.py; hooks reload live.
  Rollback: CPP_PROSPECTIVE_BIND=0 in the env, or restore the four files from git.
WU-1C: WU-1C.md and route-WU-1C.json exist (untracked); arming: see below.
