# dgl chain -- units, authoring rule, Owner gates

Programme: durable goal / disposable lease (plan vault/plans/durable-goal-lease-2026-10-09.md, Owner "y" 2026-10-09).
Goal `dgl`, cap 17.0M; chain envelope 16.0M (1.0M proof reserve). Armed only by the zero-model tick
(gsdx_chain.py tick --chain vault/programs/dgl/chain.json, task PP-DglChain-Tick, 15 min). No coordinator pane.

## Authoring rule (every unit, last step)
Unit Wn ends by writing packets/W(n+1).md (<= 9 KB, W1.md format: goal line, hard limits, numbered steps, receipt,
"author the next unit" step pointing back to THIS file) and packets/route-W(n+1).json sized from Wn's MEASURED
per-call cost. Delta only: current state, open obligations, exact frontier, known traps, evidence paths. No history,
no transcript excerpts. Commit both files. The tick arms W(n+1) only when Wn's receipt says `Status: DONE`.

## Units
| id | plan | scope | edits allowed |
|---|---|---|---|
| W1 | E0-E2 | ownership note; lease/programme tests first; GoalLedger lease epochs + programme envelope | ledger.py, mission_spend.py, new tests |
| W2 | E3 | workspace lease registry + generation CAS; binding precedence; cwd-entry = OBSERVE; zombie fencing | + hooks/lib/goal_binding.js, hooks/session_budget_guard.js (worktree only) |
| W3 | E4-E5a | terminal reconciliation (process-proven terminal, UNKNOWN_RESERVED with TTL); atomic succession as NEW tools/goal_succession.py, idempotent, journaled per succession id; called from the chain tick on `stopped_without_done` and budget halts | new module, chain driver copy in tools/ |
| W4 | E5b-E6 | predictive DRAIN in the guard; SessionEnd wake; goal-autopsy against binding records; full crash matrix (7 points), double successor, lost event, context loss, authority exhaustion; migration canary on a fixture goal | tests + the above |
| W5 | install | DEPLOY class: read `hardrule_compile.py --class DEPLOY` first. Merge to the live checkout by pathspec; never touch tools/gsd_mission.py or tools/mission_steward.py while ce-lifecycle-v3 has them dirty. Re-point PP-DglChain-Tick to the live tools/goal_chain.py. Smoke from the same commit | live tree |
| W6 | E7 | P3b self-host: lineage P3b {L1 = rf-p3b (crossed, immutable), L2 = rf-p3b2}; workspace holder wt_keosdtk_home = P3b/L2 gen 1; reconcile c2ae4b5c hold 169,870 by measured transcript; autopsy table corrected; no row rewritten | live state via the new CLI only |
| W7 | E8 | P3b-2 (cwd = wt_keosdtk_home, charged to P3b/L2): preflight, RF_CURRENT_PHASE 3, send job 1 of 2, zero-hot wait, repatriate, judge, assemble, promote; verify PROVEN delta. Needs D2-owner.md | recon worktree |
| W8 | E9 | fresh-project canary (inherits without prompt mention); UKDL HR/PR/TRAPS; CBR; retire manual root-retirement / successor-declare instructions (cold copy kept); final economics report | vault, docs |

## Owner gates
- D2 (P3b-2 control drift on the 5 PROVEN rows): `D2-owner.md` must exist with the Owner's choice before W7 arms.
- Any refusal `AUTHORITY_REQUIRED` from the programme envelope: one notification, then the chain waits.
