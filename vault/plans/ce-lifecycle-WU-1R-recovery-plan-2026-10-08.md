---
status: APPROVED (Owner "A+" then "A", 2026-10-08)
covers: [wu-1-recovery, halted-without-receipt, executable-authority, lease-estimator]
amends: vault/programs/cognitive-economy/lifecycle/WU-1.md
supersedes-draft: pp-ce-lifecycle-v/vault/plans/ce-lifecycle-WU-1R-recovery-replan-2026-10-08.md (session fc54a743, untracked)
---

# WU-1R -- recovery of the halted WU-1, on goal ce-lifecycle-v2

## Why a v2 goal
- At 15:42 the A1 planning pane (session fc54a743) entered pp-ce-lifecycle-v. The live guard bound it by cwd and charged
  its whole history since goal.since: first settle 6,855,731 (journal seq 14). This is R4 again.
- ce-lifecycle-v then read settled 8,206,486, remaining -3,608,719. No unit can be armed under it.
- Owner chose A: lineage goal ce-lifecycle-v2, root C:\Users\User\Apps\pp-ce-lifecycle-v2, branch ce/lifecycle-v2 off e71f3a0b.

## Program accounting (8,000,000 envelope, unchanged)
| item | tokens | source |
|---|---|---|
| ce-lifecycle post-binding settled | 1,897,717 | WU-0-receipt.md |
| ce-lifecycle open reservations (worst case) | 976,203 | WU-0-receipt.md |
| ce-lifecycle-v WU-1 worker 8c8d50de settled | 1,198,372 | ce-lifecycle-v journal seq 2-12 |
| worker lease :6 open (pid 17460 gone, host lists nothing) | 375,930 | seq 13; releasable with evidence, no release op yet |
| fc54a743 post-binding settled | 152,383 | seq 16 minus seq 14 |
| fc54a743 final :2 open (pane alive) | 152,383 | seq 17 |
| fc54a743 PRE_BINDING_PROGRAM_CAPEX (not goal spend) | 6,855,731 | seq 14 |
| **v2 cap = remainder** | **3,247,012** | 8,000,000 minus the six settled/open rows (PRE_BINDING excluded) |
| checkpoint reserve held back | 300,000 | |
| safe executable authority | 2,947,012 | |

## Cost autopsy of WU-1 (measured from transcript 8c8d50de)
- 24 model calls. Context per call grew from 17,961 to 72,998. Output was 16,622 tokens in all. Sum 1,255,650.
- Rereads were negligible (ledger.py twice). The tool mix was 11 PowerShell, 6 Edit, 4 Read, 4 Bash, 3 Write.
- Verdict: the cost is calls x resident context (context rent), not scope alone and not reread.
- The admission assumed ~23K per call (need 608,619 for 26 calls). The real mean was 52K.
- Estimator from now on: floor ~18K, growth ~2.4K per call. A unit rotated at 50K context costs ~34K x calls.
- At that rate 2.95M buys about 85 model calls. That completes WU-1 and probably WU-2. It does not complete the WU-1..WU-8
  vertical slice as planned. The successor and context-rent units (WU-4/5/6) must lower the rate before the rest is admitted.

## Units (one live writer; each unit commits, writes its receipt, then arms the next)
| unit | scope | calls cap | lease + reserve |
|---|---|---|---|
| WU-1F | BLOCKER. Name the test that makes test_goal_budget_admission.py read 53/54 and classify it: regression, preexisting flaky, interference or nondeterminism. Fix only if causal. | 12 | 0.40M + 0.10M |
| WU-1B | Verify and land the salvage patch. Add the goal-prebind journal op and resolve_binding in tools/mission_spend.py. Gates V-LIFE-BIND-RETRO, -CONTROL and -OBSERVER, with mutants. | 13 per epoch, max 2 epochs | 0.90M + 0.20M |
| WU-1C | Step 5: an overlapping goal-declare is refused; add goal-unroot. Gates ROOT-OVERLAP and UNROOT. | 12 | 0.40M + 0.10M |
| WU-1D | Step 6: arm --goal with a launcher record. Gates LAUNCHER-WINS and ARM-GOAL; 4-suite run; WU-1 receipt with deploy recipe; WU-2 packet. | 13 | 0.45M + 0.10M |
| WU-1H | V-LIFE-HALT-CONTINUES. On HALTED the supervisor writes a fault capsule: HEAD, commits since arm, dirty paths with diffstat, last gate lines, spend, and the final text. It also writes a partial receipt splitting DONE from SALVAGE, and arms the recompiled next unit with no Owner step. The mutant that requires a normal receipt goes red. | 13 | 0.45M + 0.10M |

- Total 2.60M + 0.60M worst case.
- Rotation rule for every worker: when context passes ~50K, or the calls cap is reached, commit what is green and append a
  progress note to the unit's receipt. End with a HANDOFF NOTE so the capsule-v2 successor starts fresh.
- Every unit cites amendment A1. Deploys still go to receipts (HR-001) until WU-7.
- Coordinators never cd into a goal root. Use git -C and absolute paths; the cwd binding is live until WU-1B deploys.
