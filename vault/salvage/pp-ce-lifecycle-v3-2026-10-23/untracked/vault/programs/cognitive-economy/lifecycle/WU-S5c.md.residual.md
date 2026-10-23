# WU-S5c -- receipt-gated completion, calls-wall closeout, mission-scoped capsule, explained non-renewal

Goal ce-lifecycle-v3. cwd = this worktree. Work class: REPAIR (four small fixes in two files, each with a gate).

Faults (all measured; do not re-derive):
- F1 (WU-S4-receipt.md): a slim worker that finished with is_error=False and no receipt was marked COMPLETED, so
  halt_continue never ran.
- F3: the guard's calls-ratio deny (hooks/session_budget_guard.js judge(), `st.calls > ratio * est`) bypasses closeout(),
  so a worker over the calls wall cannot even write its receipt. The token stop gets 4 closeout calls.
- F4: the capsule DONE list is the whole branch history. It must be only commits since the mission was created (the
  steward, now in tools/mission_steward.py, has _git_log(tree, since)).
- F5: for WU-S5 (m-b2fefaf352e1, HALTED) halt_continue wrote the capsule but no renewal happened, and the
  slim_worker_finished ledger row carries neither `capsule` nor `renewal`. For WU-S3 it did carry them and it renewed.
  A non-renewal must ALWAYS leave its reason on the row.

Read ONLY:
- tools/gsd_mission.py: `grep -n "def halt_continue\|def slim_finished\|def write_fault_capsule\|halt_continue("`,
  then +-40 lines around each hit;
- hooks/session_budget_guard.js 100-170.

Budget: about 16 physical calls. Commit after each green gate group.

Steps:
1. F5 first. Find why the row lost its fields: an exception swallowed after the capsule write, or a row written before
   halt_continue filled it. Fix it so that every exit path sets row["renewal"].
   Gate V-LIFE-NONRENEW-HAS-REASON: force the exception path and the row must carry a reason.
2. F1: in the slim finish path, is_error=False with _receipt_present(rec) False must go to HALTED (fault "no receipt")
   and through halt_continue.
   Gates: V-LIFE-SUCCESS-NO-RECEIPT-NOT-COMPLETED, plus a control where a DONE receipt makes it COMPLETED.
3. F4: write_fault_capsule's commit list = commits since rec["created_at"] (reuse the steward helper).
   Gate V-LIFE-CAPSULE-MISSION-SCOPED.
4. F3: the calls-ratio deny goes through closeout().
   Gate in tools/test_session_budget_guard.py: the receipt write is allowed after the calls wall.
5. Mutants (tools/mutation_drill.py), one per fix; each must go red. Suites: halt 16/0+, guard 20/20+, MC 226/227,
   ADM 43/43, steward 18/18.
6. Commit by pathspec with -F. Write WU-S5c-receipt.md (<= 20 lines). Commit.
7. Arm WU-INST2 with LIVE gsd_mission.py arm-chain (--parallel-unit lc3-WU-INST2, packet WU-INST2.md, route
   route-WU-INST2.json, token-estimate 600000) if remaining - open >= 600,000.

NEVER write "needs a fresh pane" or "/kclear". End your final message with: HANDOFF NOTE: WU-S5c done


## Residual
Proposed by the steward for stopped mission m-b6b4894378dd (PROPOSAL ONLY: arming it needs the Owner/coordinator).
- Partial receipt: C:\Users\User\Apps\pp-ce-lifecycle-v3\vault\programs\cognitive-economy\lifecycle\WU-S5c.md.partial.json
- RESUMPTION_FILE: C:\Users\User\Apps\pp-ce-lifecycle-v3\RESUMPTION_FILE.md
- Salvage: C:\Users\User\Apps\pp-ce-lifecycle-v3\vault\specs\salvage\m-b6b4894378dd
