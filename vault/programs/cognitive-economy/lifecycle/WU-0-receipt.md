# WU-0 receipt -- bootstrap (deterministic, coordinator pane, no worker)

Decision: Owner "y A" 2026-10-08 on vault/plans/ce-lifecycle-vertical-slice-plan-2026-10-08.md. Program envelope stays 8,000,000.

Program accounting (MEASURED from goal-budget/ce-lifecycle/spend.journal.jsonl seq 1-17):
| Category | Tokens | Rows |
|---|---|---|
| POST_BINDING_GOAL_SPEND (settled) | 1,897,717 | f5f5a496 670,543; bf948408 7,020,962-5,920,094; 6e96dc51 1,023,487-897,181 |
| OPEN reservations (worst case, unsettled) | 976,203 | f5f5a496 lease:2 684,435 (dead pane, phantom); 6e96dc51 final:3 64,853; bf948408 final:3 226,915 |
| PRE_BINDING_PROGRAM_CAPEX (not Goal spend) | 6,817,275 | bf948408 first settle 5,920,094; 6e96dc51 first settle 897,181 (goal-wide `since`, session_budget_guard.js:342) |
| Lineage remaining -> goal ce-lifecycle-v cap | 5,126,080 | 8,000,000 - 1,897,717 - 976,203 |

The old ledger keeps its rows unchanged (append-only). The reattribution is recorded HERE, not as a journal op: the
ledger has no `prebind` op until WU-1 adds it; WU-1 back-fills nothing. ce-lifecycle stays exhausted and holds root
pp-ce-lifecycle until WU-1's `goal-unroot` exists.

Effect: worktree C:\Users\User\Apps\pp-ce-lifecycle-v on branch ce/lifecycle-v; goal ce-lifecycle-v declared (root =
that worktree, source = the APPROVED plan); WU-1 armed there. Exact ids/commits: see RESUMPTION.md.
UNKNOWN: whether the 976,203 open reservations settle lower (they are counted at worst case, so the new cap cannot overshoot the envelope).
Bootstrap note: declaring a NEW goal without Owner TTY proof is the F5 loophole; used once here with real Owner
authority ("y A") recorded in the plan; WU-2 closes it.
