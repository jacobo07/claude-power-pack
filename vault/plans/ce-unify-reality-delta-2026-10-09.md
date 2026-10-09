# CE unify (Gen1 science + Gen2 compiler + ce-a3b-r): Reality Delta, 2026-10-09

Status: PROPOSED. Scan PARTIAL. It stopped when this session's cwd was moved into the
pp-ce-a3b-r worktree, which bound it to goal ce-a3b-r, already over its cap, and the goal
guard refused every further call. This is the second recorded case of the trap in
memory/feedback_coordinator_set_location_binds_goal.md.

## Measured (goal-status from the pp-ce-a3b-r tool, 2026-10-09)
| goal | cap | used | open | remaining |
|---|---|---|---|---|
| ce-a3b-r | 8,600,000 | 8,857,222 (includes this scan) | 173,826 | below 0 |
| ce-lifecycle-v2 | 8,847,012 | 39,630,319 | 2,359,116 | -30,783,307 |
| ce-lifecycle-v3 | 4,295,976 | 1,361,881 | 396,885 | 2,934,095 |
| ce-a4 | 16,600,000 (Owner approved) | 1,945,693 | 563,845 | 14,654,307 |

## Facts from git (pp-ce-a3b-r, HEAD 5db1e40e)
- R5 has code (88d37fe9, 6902264d) and a receipt (R5-receipt.md). The receipt says the regression suites have not been run since the session_budget_guard.js regex edit.
- goal-autopsy is in the ce/a3b-r branch only. Main's tools/mission_spend.py does not have it.
- R5c (m-447ca8005684) COMPLETED. Its Close ran `arm` twice without --no-launch, which started two packet-less strays that cost 866,883 (measured).
- ce-a3b-r takes no new units. ce-a3 Amendment D (pp-ce-a3 3aa002af, Owner "y") merged R3/R4/R6/R7 into ce-lifecycle-v2.
- Main HEAD 3f9b57cc installed lifecycle L1 from ce/lifecycle-v3 WU-S1. ce-a4 is active.

## Not verified (UNKNOWN)
- The dataset "Dataset CE Gen1 Gen2 Optimization and Evolution 1.md" was not found under Downloads. It was not read.
- The ce-a4 plan scope and overlap, R3-R7 progress inside lifecycle-v2, the 2026-10-11T18:00Z Tier-3 gate, and the iteration prompt.

## Proposal
1. No new programme. HR-NOVELTY-001: ce-a4 (14.65M left) and lifecycle-v3 already own the compiler and lifecycle work. The dataset's obligations get mapped onto those owners.
2. A fresh pane, started in the main repo and never using Set-Location into a goal worktree, opens a new goal ce-unify with a cap of 1.2M. Its work: finish the scan, write the obligation ledger (dataset item -> existing owner/disposition), file the lifecycle-v2 overrun of 30.8M as an economic incident, and make goal-autopsy reach main if ce-a4 does not already own that.
3. ce-a4 funds all later implementation. No authority beyond ce-unify's 1.2M is requested now.
