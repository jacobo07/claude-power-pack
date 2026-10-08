# A3-U2 receipt -- CLOSED SUPERSEDED (not a success receipt)

Written by the control plane (unbound pane b42025e1, main checkout cwd, git -C only) under Amendment C
(`vault/plans/ce-a3-amendment-C-out-of-band-control.md`, Owner "y" 2026-10-08). No worker produced this.

## Worker facts
- U2 worker 3cf87020 (packet 2b59d938): refused by the cap guard on call 1 (used 10,003,096 >= 9,900,000).
  Provider subtype `success`, 4 turns, $0.45. It wrote the closeout `vault/plans/a3-u2-receipt.md`: deliverables 1-4
  NOT STARTED. Retry 98e93726: 2 calls, 2 refusals. No U2 commit exists past 2b59d938.
- Provider SUCCESS was a refusal. Work Unit status: never started -> now SUPERSEDED.

## Why SUPERSEDED, deliverable by deliverable (proof = owner gate, re-run at merge)
| # | Deliverable | Owner | Evidence |
|---|---|---|---|
| 1 | GOAL_STATE canonical policy | ce-a3b-r R1/R1b | d0d0eb2b, GOAL_PASS 67/67, mutation KILLED. NOT LIVE (main guard :221 regex); install = a3b-r R3 |
| 2 | default binding by program path | ce-lifecycle-v2 WU-1/WU-1B | prospective bind; WU-1B RUNNING m-8b571c4b78f7 |
| 3 | coordinator sub-cap | lifecycle WU-4 (executable-authority admission) | UNKNOWN until WU-4 packet; carried as an open item |
| 4 | stale/late usage | ce-a3b-r R2 goal-reconcile | 10bf871b, GOAL_PASS 72/72, mutation KILLED |
| a | goal refusal gets no Read closeout | goal-admission fix | 5ecd559b |
| b | UNKNOWN spend fail-closed in admit_route / loop_budget | lifecycle WU-4 | open item |

## Economics (measured 2026-10-08)
goal-autopsy (read-only), bound 11,101,707: pane 2aa0b0fb 4,964,742 | pane 3aaeab7f 3,701,465 | worker 6af8e044 (U1)
1,822,163 | worker 3cf87020 (U2) 425,692 | worker 98e93726 187,645. Panes 78%, workers 22%.
goal-reconcile: used 11,400,957 -> 11,398,144, open 1,932,625 -> 0; all three holds SPENT+RELEASED, so the overshoot
(1,498,144 over cap) is MEASURED spend, not phantom. The U2 worker share of the jump from 6,804,052 is 0.61M
(MEASURED); the rest is the two coordinator panes' bound calls (INFERRED: per-session totals are measured, the
before/after-launch time split was not computed). UNKNOWN: 296,437 = used 11,398,144 minus autopsy bound 11,101,707.

## Next
ce-a3 is terminal for spend. U3, U4, U5: Reality Delta each, then folded into the ce-a3b-r chain's single authority
request (Amendment C, C2). No new goal id.
