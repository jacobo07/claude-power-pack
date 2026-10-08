---
covers: [event-driven-wake, mission-wait, dependency-wake, cheap-architecture-admission, caa-wake, ce-lifecycle-wu5-dependency]
status: APPROVED (Owner 2026-10-08: "go caa-wake 5M, accept WU-1 supersede")
goal: caa-wake (cap 5,000,000, root C:\Users\User\Apps\pp-caa-wake, branch ce/caa-wake)
extends: vault/plans/cheap-architecture-admission-2026-10-07.md ; tools/wake_check.py ; ce-lifecycle WU-5 (pp-ce-lifecycle-v)
source: planner pane 41f83b39, bounded Reality Delta, 2026-10-08 ~10:35Z
---

# Event-driven dependency wake + Cheap Architecture Admission continuation

## Owner decisions (2026-10-08)
1. Goal `caa-wake`, cap 5M. It funds the wake capability and CAA's remaining work. It does NOT fund or continue A3.
2. The CAA wake predicate is ANY_OF(A3 U2 receipt, ce-lifecycle-v WU-1 receipt). Reason: CAA's real need from U2 is a goal-binding resolver, and WU-1 delivers one. The U2 coordinator sub-cap becomes CAA deny-rule 2 inside T3.

## Measured reality (2026-10-08 10:35Z)
- `ce-a3`: cap 9,900,000; used 10,797,470; remaining -897,470; open 1,781,175. A3 is EXHAUSTED.
- pp-ce-a3 @ 2b59d938 is the U2 *packet* only; evidence/a3/ holds U1 only. No live A3 mission; 8 dirty files belong to the A3 owner.
- False premise in the brief (CLASE 2): "A3 U2 will appear". Under the current authority it cannot.
- gsd_mission BLOCKED means a human permission prompt. It has no dependency-wait state.
- ce-lifecycle-v m-3403c155ecb8 is RUNNING WU-1 @ 9bc030c9. It owns the future sweep `lifecycle` stage (WU-5).
- Sweep heartbeat 10:34Z rc 0. Host: 6.2 GB free, 28 claude.exe.

## Ownership correction found during W0 (supersedes the inline plan's "new mission_wait store")
- `tools/wake_check.py` already has a zero-model producer (`evaluate`, refuses a model-shaped argv) and a consumer (`consume`). The consumer writes flag -> one `wake` event on a gsd_x `GoalLog` (seq-CAS append, sha256 dedupe), plus REFUSED/DUPLICATE/MOVED receipts. Gate: `tools/test_wake_flag_consumer.py`. **EXTEND it**: today its producer knows one predicate (floor regression); W1 generalizes it to declared dependency predicates. Singleflight = the GoalLog seq-CAS. Idempotency = the digest dedupe. No second store.
- `ce/gen2-completion` (be88dee5, unmerged) holds `tools/test_ce_t1_waiting.py`: WAITING zero-hot via WAKE_FLAG, plus stale-pane revalidation. **MERGE/REUSE** its assertions; do not rewrite them.
- A4 (86ad6f16, PROPOSED) lists zero-hot WAITING and event-driven wake as BRANCH_ONLY with merge + canary owed (A4 rows 10, 11, W2c). caa-wake lands them; A4 W2c then consumes them, not rebuilds them.
- ce-lifecycle WU-5 `lifecycle.decide` must CALL the wait evaluator for its WAIT branch. W5 writes that handoff.

## Work Units (goal caa-wake, worktree Apps/pp-caa-wake)
| WU | Deliverable | Lease (work + reserve) |
|---|---|---|
| W0 | deterministic bootstrap (this pane) | 0 model |
| W1 | dependency-wait contract + wake_check extension + wake admission + delta + tests/mutants + offline canaries 1,3,5,6,7,8 | 1.3M + 0.3M |
| W2 | bounded sweep stage + heartbeat fields + land on live tree + canaries 2,4 | 0.5M + 0.1M |
| W3 | register the CAA wait (+ this mission's W4 as its consumer) and exit | 0.1M |
| W4 | woken by the sweep: delta + Proof of Non-Work + CAA T3 residual + canaries 10,11 | 1.6M + 0.3M |
| W5 | KV/UKDL/CBR/CI, ce-lifecycle/A4 handoff, retire manual text, Master Done-Gate | 0.6M + 0.1M |

Packets live in `vault/programs/cognitive-economy/caa-wake/`. Every WU ends with `<WU>-receipt.md` (decision / effect / proof / unknowns / spend / reforecast) committed on ce/caa-wake. Serial workers on Sonnet, no Agent fan-out, one at a time below 4 GB free. A gate that fails twice stops and escalates to the Owner.

## CAA wait (registered in W3)
ANY_OF:
- `git cat-file -e ce/a3:vault/programs/cognitive-economy/gen2/evidence/a3/U2-RECEIPT.md`
- `git cat-file -e ce/lifecycle-v:vault/programs/cognitive-economy/lifecycle/WU-1-receipt.md`

Invalidators: the CAA plan status is COMPLETED or SUPERSEDED, or goal caa-wake is exhausted. On wake, arm W4 in pp-caa-wake. Kill switch: `CPP_MISSION_WAIT=off`.

## Master Done-Gate
As stated in the approved inline plan, section 6.
