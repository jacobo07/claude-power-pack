---
status: APPROVED (Owner "y" 2026-10-08)
covers: [bootstrap-deadlock, approval-consumer, halted-without-receipt, prospective-binding, ledger-repair, ctx-rent-canary]
goal: ce-lifecycle-v2 (lineage of ce-lifecycle-v)
amended_by: ce-a3 Amendment D (pp-ce-a3 3aa002af, Owner "y" ~18:05, +5,600,000 applied as ledger seq 26)
units: [WU-1H, WU-ADV, WU-1C, WU-1D, WU-INST, WU-TRIP, WU-FLOOR, WU-GEX, WU-CLOSE]
packet_dir: vault/programs/cognitive-economy/lifecycle
---

# ce-lifecycle-v2 -- bootstrap deadlock closure + continuation (Master Plan)

## Reality delta (measured 2026-10-08 ~14:31 UTC, read-only, from a pane outside every goal root)
- The prompt's premise is stale. After "y", the Owner chose "A": goal ce-lifecycle-v2 (cap 3,247,012), worktree
  Apps\pp-ce-lifecycle-v2, commit 1039b703 = WU-1R APPROVED + WU-1F/WU-1B packets and routes. Clean tree.
- WU-1 salvage is frozen byte for byte as a patch (e71f3a0b). The old worktree is still dirty, but the patch is canonical.
- WU-1F = mission m-e6ff77095a67. It was PREPARED and ADMISSIBLE at 14:28:49 UTC. gsd_mission supervise maps PREPARED to
  launch (gsd_mission.py:529), and the PP-GsdLongRun-Sweep pass is running now. Launch by the host is expected, not yet observed.
- The out-of-band lane EXISTS: Task Scheduler (PP-GsdLongRun-Sweep, PP-GoalSweep) -> gsd_mission supervise. It runs
  outside every pane and outside the hook guard. It launched WU-1 at 10:08. What it lacks is one capability: it only
  launches what a pane armed. Nothing consumes an approval, and nothing turns a receipt or a HALT into the next arm.
- Ledger poisoned, not just the guard: the ce-lifecycle-v journal seq 14 settles fc54a743 = 6,855,731 with closes=[].
  The "1.57M ledger vs 9M guard" split has collapsed into one wrong number (used 9,036,077).
- Root cause in the LIVE guard = this checkout hooks/session_budget_guard.js (the dispatcher points at
  ../skills/claude-power-pack/hooks). Binding is cwd-under-root (:196-200), and spend is measured from goal.since over the
  whole transcript (:342), then settled into the canonical journal. Any coordinator that touches pp-ce-lifecycle-v2 is
  bricked again in the same way.
- ctx-rent: 0f8713fe, dirty S2 (rollover.py, rollover_replay.py, RESUMPTION), goal ctx-rent-s2 cap 3,000,000. Untouched.

## Answers to the required questions
1. Why "y" did not produce WU-1B: approvals live only in panes. supervise launches PREPARED missions but never arms.
   The pane that held the y was bricked by the guard, so the transition needed a new pane (the Owner opened one and said A).
2. Approval consumer: an `advance` stage added to `gsd_mission supervise` (EXTEND, not new). It reads approved plans
   (frontmatter status APPROVED + `units:` list + packet sha) and arms the next unit whose precondition receipt exists.
3. Survival: it runs from Task Scheduler via python. No pane, no PreToolUse hook, no CPP_GOAL, no cwd binding.
4. Not a bypass: typed ops only (settle / fault-capsule / arm / admit / launch). It can arm only a packet that is
   already committed in an APPROVED plan, under route admission against the goal's remaining executable authority.
   It cannot edit code, raise a cap, or arm an unlisted packet.
5. Cycle broken: WU-1F/1B launch via the sweep, so the guard is never on the launch path. The only arm left that is
   driven by a pane (WU-1B after WU-1F) is done by THIS pane through the canonical CLI from an unbound cwd. That is not
   an Owner operation, and it is the last time a pane is used for it.
6. Ledger convergence: one truth = journal ops. WU-1B adds op `prebind` (PRE_BINDING_PROGRAM_CAPEX). The guard settles
   only from the bind epoch (since = max(goal.since, bind.since_ts)). A compensating `reclassify` op moves the
   6,855,731 to pre-bind capex on ce-lifecycle-v. History is appended to, never rewritten. ce-lifecycle-v is marked SUPERSEDED.
7. WU-1B launches without an Owner pane: armed through the CLI here, launched by the sweep.
8. HALTED without receipt: `advance` writes fault-capsule.json (HEAD, commits since arm, dirty paths + diffstat, last
   gate lines, spend, final text) and a partial receipt. It re-arms the same packet minus DONE steps through the existing
   budget-halt successor path (gsd_mission.py:2163). Gate V-LIFE-HALT-CONTINUES.
9. No giant coordinator: units chain receipt -> advance -> arm -> launch. This pane exits after the WU-1B arm.
10. Not throwaway code: the advance stage IS the WU-5 automatic-successor substrate, pulled forward. WU-5 is re-scoped to
    harden it, not to replace it.
11. ctx-rent canary: after WU-ADV is live, an APPROVED ctx-rent-s2 plan + S2 packet is committed. The advance stage arms
    it under ctx-rent-s2 (3.0M) with no pane.
12. Ratchet: each gate that turns green is added to the CBR baseline. The manual "open a fresh pane" recovery text is retired.

## Units (after approval; each one is a sweep-launched mission in pp-ce-lifecycle-v2 with a capsule-v2 receipt)
| unit | scope | lease |
|---|---|---|
| WU-1F | running/launching now: flaky 53/54 capture | 0.5M est (already admitted) |
| WU-1B | as packeted: apply salvage, goal-prebind + resolve_binding in mission_spend.py, observer isolation (read-only calls never bind), V-LIFE-BIND-RETRO/CONTROL/OBSERVER + mutants | 0.45M+0.15M |
| WU-1B-I | install: cherry-pick the guard fix into the live checkout (path-scoped commit, test_session_budget_guard.py + new gates green before and after), plus the compensating `reclassify` op for fc54a743 | 0.2M |
| WU-ADV | supervise `advance` stage: approval reader, receipt/HALT -> fault capsule -> next arm, singleflight (goal_refusal + approval-consumed ledger op keyed by plan sha+unit), gates V-LIFE-HALT-CONTINUES / APPROVAL-ONCE / NO-ARBITRARY-PACKET | 0.6M+0.2M |
| WU-1C, WU-1D | recomputed from reality after WU-1B; armed by `advance`, not by a pane | ~0.75M |
| WU-2..N | the original ce-lifecycle-v plan, each re-checked by Proof of Non-Work before arm | within remaining authority |
| ctx-rent S2 | first production canary of advance: S2 finish, 4 suites, commit, 150K gate | ctx-rent-s2 goal |

Executable authority v2 ~= 3.25M - 0.3M checkpoint reserve. WU-1F+1B+1B-I+ADV+1C/1D ~= 2.9M worst case. If WU-2+ do not
fit, `advance` stops at WAITING_FOR_AUTHORITY and asks ONE semantic question. No new money is assumed.

## Canaries (Production Reality)
- Bricked-coordinator replay: a pane with large history enters the v2 root -> no deny, no retro settle.
- Approval observed twice -> one arm. HALT injected -> capsule + re-arm, Owner action none.
- Pane-less chain: WU-1C is armed and launched with no pane open (sweep log + mission record are the evidence).

## Knowledge / UKDL / CBR
Taxonomy entries are written once, deduped against UKDL: CONTROL_PLANE_INSIDE_EXECUTION_FAILURE_DOMAIN,
APPROVAL_WITHOUT_CONSUMER, RETROACTIVE_ATTRIBUTION_ON_BIND (with its settle-into-ledger variant), HALTED_WITHOUT_RECEIPT.
HR candidates are promoted only after their gate is green.

## Rollback
Guard: revert the path-scoped commit in the live checkout. Advance stage: env kill switch CPP_SWEEP_ADVANCE=off (the
supervise behaviour from before the change). Journal: reclassify is an appended op and is reversible by a counter-op.

## Not done here
Nothing was mutated. This plan is committed into pp-ce-lifecycle-v2 as the first post-approval action, after
checking that no other writer holds that tree.
