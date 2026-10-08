# WU-1H progress (session budget breaker tripped at 630,045 > stop 620,000; nothing in tools/ changed)

State: checkpoint commit with stub vault/programs/cognitive-economy/lifecycle/WU-1H-receipt.md exists (status IN PROGRESS).
No code edit landed: the one python patch was blocked by the breaker before it ran. tools/gsd_mission.py is untouched.

## Findings (read, verified)
- Precondition OK: WU-1B-receipt.md says done.
- slim_finished branch: tools/gsd_mission.py ~2790 (`elif act == "slim_finished"`), transitions straight to HALTED/COMPLETED.
- Dead-pid/no-JSON branch: slim_result() ~861 returns status "failed" -> plan_next ~559 `halt` with reason "slim worker failed: ..."; handled by the legacy halt path ~2780-2789 (no capsule, `_renewal_why_not` needs budget halt, so never renews).
- renew_mission ~2161 already takes continuity_from; carried wu_packet. launch_prompt ~1582 builds the successor prompt.
- Goal authority: GoalLedger.status() -> {remaining, open}; reach via mission_spend._goal_ledger(goal_id).status(). A mission record has no CE goal id (rec["goal"] is {repo, workstream, unit}); use rec.goal.ce_goal, then env CPP_CE_GOAL, then workstream; unmeasurable -> not renewed.
- Fixtures for tests: tools/test_gsd_mission_admission.py lines 252-324 (finish_slim helper with fake out.json and session-budget state file for tripped). Reuse that pattern; tripped=true comes from state file {"tokens":350000,"closeout":1}.
- Residual B: the existing fault_capsule (6902264d) is session/goal level in mission_spend.py + session_budget_guard.js, which WU-1B also changed; cherry-pick not attempted. A mission-level capsule is a different object (state dir, per mission epoch).

## Design to apply (next epoch, ~8 calls)
1. gsd_mission.py helpers before the capsule-v2 (T6) section: halt_continue_on (CPP_HALT_CONTINUE=off), write_fault_capsule (open mode "x", path lr.state_dir()/fault-capsules/<mid>-e<epoch>.json; fields HEAD, git log origin..HEAD, status --porcelain, diff --stat, last ^(PASS|FAIL|[A-Z_]+_PASS=) lines, spend, result[:2000], partial_receipt DONE/SALVAGE; read-only git), _receipt_present (<packet stem>-receipt.md exists and no STUB), halt_authority, halt_continue (checks: wu_packet, no receipt, no owner_hold, no prior mission_renewed in ledger, renewal < 2, authority >= token_estimate; else row["renewal"]="not renewed: <why>"; else renew_mission(continuity_from={mission_id, kind:"fault_capsule", capsule_path})).
2. Call halt_continue from slim_finished when stopped OR (COMPLETED and receipt absent), and from the legacy halt branch when reason starts "slim worker failed" (then `continue`).
3. launch_prompt: prepend "FAULT CAPSULE ... start from <path>" when rec.continuity_from.capsule_path is set.
4. Tests V-LIFE-HALT-CONTINUES / -ONCE / -NO-AUTHORITY / -KILL / -DEAD-NO-RESULT / -SUCCESS-NO-RECEIPT in a new tools/test_halt_continues.py (hermetic state dir, temp git repo with 1 commit + 1 dirty file, monkeypatch gm.halt_authority). Mutants through tools/mutation_drill.py: drop receipt check; drop singleflight; provider success counts as receipt.
5. Run four suites, commit by pathspec with -F msgfile, write the receipt (<= 40 lines, deploy recipe, no deploy), commit.
6. Step 9 (arm WU-ADV) NOT done: needs goal-status remaining-open >= 1,100,000; check it, arm with --no-launch then envelope then admit, hold on failure.

Needs a fresh pane (/kclear); this pane's envelope is spent.

HANDOFF NOTE: WU-1H not done -- breaker stop, design and findings above
