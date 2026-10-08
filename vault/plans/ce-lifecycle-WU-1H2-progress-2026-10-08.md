# WU-1H2 progress (session budget breaker tripped at ~731K > stop 700K; code landed, NOT committed)

Landed in the worktree, uncommitted:
- tools/gsd_mission.py: halt_continue_on, _git_ro, write_fault_capsule, _receipt_present, halt_authority, halt_continue
  (before the capsule-v2 section); call sites in slim_finished and in the legacy "slim worker failed" halt branch;
  launch_prompt FAULT CAPSULE prefix; arm_chain() + `arm-chain` CLI subcommand (parser + dispatch).
- tools/test_halt_continues.py (new): gates HALT-CONTINUES, CAPSULE-IN-PROMPT, HALT-ONCE, NO-AUTHORITY, KILL,
  DEAD-NO-RESULT, SUCCESS-NO-RECEIPT, HALT-RECEIPT-PRESENT, SUCCESS-WITH-RECEIPT-COMPLETES, ARMCHAIN-ATOMIC.

First run: successor created (suc=1) but the test looked for the capsule under Path(TMP)/fault-capsules while the code
writes under lr.state_dir(). A sed fixing the test to gm.lr.state_dir() was blocked by the breaker; apply it
(`Path(TMP) / "fault-capsules"` and `Path(TMP, "fault-capsules", ...` -> `gm.lr.state_dir() / "fault-capsules"`), rerun.

Next exact actions: 1) fix test path, run it until green; 2) mutants via tools/mutation_drill.py: replace
`if _receipt_present(rec):\n        return` with `if False:\n        return` (gate V-LIFE-HALT-RECEIPT-PRESENT);
`elif any(e.get("event") == "mission_renewed"` -> `elif False and any(` (V-LIFE-HALT-ONCE);
`(stopped or not _receipt_present(fin))` -> `(stopped)` (V-LIFE-SUCCESS-NO-RECEIPT); 3) four suites into _logs/wu1h2/;
4) commit by pathspec with -F msgfile; 5) replace WU-1H-receipt.md (<=40 lines, deploy recipe hashes, B = second format,
mission-level); 6) goal-status ce-lifecycle-v2, arm WU-ADV via arm-chain if remaining-open >= 1,100,000.

HANDOFF NOTE: WU-1H not done -- breaker stop; code written, uncommitted; remaining steps above
