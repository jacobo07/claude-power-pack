---
id: PLAN-CE-A3-AMENDMENT-D
covers: [chain-deadlock, atomic-arm, success-without-receipt, shared-failure-record, same-goal-extension, approval-consumer, certified-install, a3-u3-u5, a3b-r-merge]
status: AWAITING OWNER APPROVAL (one reply)
source: unbound pane b42025e1, main-checkout cwd, reads by absolute path / git -C, 2026-10-08 ~18:00
extends: ce-a3 Amendment C (4f1fe9ae); lifecycle-v2 bootstrap master plan (79350a8e, APPROVED)
---

# Amendment D: one lineage, one consumer, one approval

## 1. Reality delta (measured 17:48-17:57)
- DEADLOCK. lifecycle-v2 coordinator c8 ceded the WU-1C/WU-1H slots to Amendment C (be7549c1, RESUMPTION action 1:
  "Amendment C coordinator: commit WU-1C, arm with --supersedes m-1783bda2a44b"). Amendment C had withdrawn and moved
  its scope into WU-1H instead (2bed6e14). Each waits for the other; nothing is armed. CLASE 2: each read the other's
  uncommitted on-disk state as ownership.
- Packetless launch root cause: `arm()` defaults to launch=True (tools/gsd_mission.py:3141); the packet is bound later
  by a separate `envelope` call. A bare `arm` therefore launches /gsd-autonomous with no packet. By design, not a fluke.
- Terminal settlement under a hold: ALREADY LIVE (gsd_mission.py:520-534, sweep code ebd98a85dee0): positive DEAD
  settles, hold kept, UNKNOWN stays parked. m-413f1e324aa5 settled on its own. Remaining gap: a hold does not stop a
  LIVE worker (m-23568bbcd2f9, m-906ce1fae68c ALIVE under cost-breaker holds, 5-6M each; other programs).
- Stray m-d84de9dd1edb (sid a0912e61) was answered "go" at 17:54 and runs /gsd-new-milestone in pp-ce-a3b-r: 1.59M
  bound so far. ce-a3b-r: used 8,707,222 / cap 8.6M, remaining -107,222. Treated as an Owner action; not touched.
- Observer isolation holds: this pane is absent from every goal autopsy.
- Live guard still has the substring GOAL_STATE regex (hooks/session_budget_guard.js:221). Install hazard recorded by c8:
  the live guard carries six commits the branches lack, so a copy would revert them; install must be a 3-way merge.
- lifecycle-v2: remaining 1,426,798, open 489,605 (WU-1B leases, releasable). Route admission prints remaining=None.
- A3 U3 = Fresh Focus Floor (2.5M forecast); tools/floor_regression_gate.py exists and is worked by TOK-18; E1 moved
  8 rules out of the prefix on 2026-10-05 -> U3 likely partly MERGED. U4 = GEX44 binding (0.8M). U5 = KV/UKDL/CBR + CI
  wiring, same scope as a3b-r R7 -> MERGE.

## 2. Ownership
One lineage: ce-lifecycle-v2 owns every remaining control-plane unit. ce-a3b-r R3/R4/R6/R7 MERGE into it (a3b-r is
over cap and two worktrees already edit the same three files). ce-a3 stays terminal. WU-ADV/WU-1H = the only consumer.

## 3. Units (each a sweep-launched slim mission in pp-ce-lifecycle-v2; forecast at ~34K/call, measured)
L1 WU-1C = WU-1H + addendum A-C: failure record (reuse R5 fault_capsule, one format, process status vs work-unit
   status as separate fields), success-without-receipt fails closed, `arm` launch=False by default + one atomic
   arm/envelope/admit step that holds on failure. Arm with --supersedes m-1783bda2a44b. 0.6M
L2 WU-ADV + WU-4 core: sweep advance stage consumes APPROVED plan units and authority events; `goal-extend` journal op
   (scoped, bounded, approval-id singleflight, cap_effective = original + sum(extensions), spend untouched); route
   admission reads goal remaining. First event consumed: this approval. 0.7M
L3 WU-1C2 roots, L4 WU-1D close WU-1: existing packets, unchanged. 1.05M
L5 Installer (ex a3b-r R3): staged 3-way merge into the live checkout by pathspec, suites run there, sha receipt,
   drift check, rollback. Installs only hashes covered by an Owner approval (section 5). 0.8M
L6 Tripwire (ex a3b-r R4): spend without durable progress -> checkpoint + failure record + reforecast; a hold on a LIVE
   worker ends its process after checkpoint (closes the m-23568/m-906 leak class). 0.7M
L7 U3: deterministic floor measurement first (Proof of Non-Work); execute only the residual cut it proves. <=1.0M
L8 U4: Proof of Need for GEX44 binding (does any laptop goal run a GEX44 worker?); NO_WORK or execute. <=0.8M
L9 U5 + R6/R7 closeout: UNKNOWN fails closed at admit_route/loop_budget, canaries, KV/UKDL/CBR, CI. 0.8M
Total 6.45M + 1.0M checkpoint/proof reserve = 7.45M. Available ~1.9M (after WU-1B leases release). New: up to 5.6M.

## 3b. Approved (Owner "y" 2026-10-08 ~18:05: plan + up to 5,600,000 on ce-lifecycle-v2)
Premise correction before execution: the live ledger already has a same-goal extension primitive.
`ledger.declare_cap` (modules/provider_routing/ledger.py:233) appends a `cap` op with a provenance `source`, leaves
every settle/reserve untouched (cumulative spend preserved, original cap kept in the journal) and refuses a crossed
cap. L2 therefore EXTENDS it: the consumer applies a durable, hash-bound, consume-once approval record through
declare_cap; no new `goal-extend` op. Extension event #1 = this approval, applied once by the bootstrap pane with
source naming this card's commit.

## 4. This pane after approval (bootstrap only, ~15 tool calls, then SAFE_TO_FORGET)
Resolve the deadlock (commit WU-1C + routes for L1, L2, L5-L9; amend the bootstrap plan's units list; arm L1 with
--supersedes), tell c8 the slot is resolved, update RESUMPTION files, stop. L1 -> L2 run on current authority; from L2
on the sweep consumes this approval as extension event #1 and arms the rest. No pane after that.

## 5. Security deviation (HR-001)
Guard code is written by the agents it constrains, so an installer that deploys any committed guard change unattended
is a self-modification channel. Approval of this plan authorizes installing the named fixes (GOAL_STATE R1b, WU-1B
binding, L1/L2/L6 gsd_mission changes) once each passes its gates; the receipt lists their hashes. Any later guard
change needs one semantic YES bound to its hash, never a command.

## 6. Done-gate
Canaries on real edges: packetless arm -> no process; success without receipt -> RECOVERY_PENDING + record; held DEAD
worker settles; held LIVE worker stops after checkpoint; extension keeps cumulative spend and no new goal id; live guard
hash = approved hash and spec read passes while protected write is denied; one sweep-armed successor with no pane.
A3: U2 SUPERSEDED, U3/U4/U5 each DONE / NO_WORK / MERGED with evidence. UNKNOWN 296,437 stays UNKNOWN.
