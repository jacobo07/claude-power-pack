---
id: PLAN-CE-A3-AMENDMENT-C
covers: [ce-a3-closure, u2-proof-of-non-work, out-of-band-succession, success-without-receipt, a3-u3-u5-fold]
status: AWAITING OWNER APPROVAL (one reply)
source: unbound pane b42025e1 in the main checkout, 2026-10-08; reads by absolute path / git -C only
extends: gen2/AMENDMENT-A3-2026-10-07.md; reuses ce-a3b-r Amendment B and ce-lifecycle-v2 plan
---

# Amendment C: close ce-a3 on evidence, put succession in the sweep, fold U3-U5 into the live chain

## 1. Reality delta (measured 2026-10-08)
- ce-a3: HEAD 2b59d938 (U2 packet). Dirty: ce-a3-RESUMPTION.md, session_lessons.md; untracked a3-u2-receipt.md,
  4 docs stubs for tools/a3_pane_autopsy.py, .pp-capabilities. No U2 commit.
- U2 worker: refused by the cap guard on its first call (used 10,003,096 >= 9.9M). It read only the packet and wrote
  a closeout receipt at vault/plans/a3-u2-receipt.md: all 4 deliverables NOT STARTED. The receipt was not missing;
  the provider SUCCESS flag hid a refusal.
- Ledger (mission_spend goal-status): used 11,400,957 = settled 9,468,332 + open 1,932,625; cap 9.9M; remaining -1,500,957.
- goal-autopsy (read-only, R5 tool), bound tokens 11,101,707:
  pane 2aa0b0fb 4,964,742 (A3 ULTRA pane) | pane 3aaeab7f 3,701,465 (U2 launcher) | worker 6af8e044 1,822,163 (U1)
  | worker 3cf87020 425,692 (U2, 1 refusal) | worker 98e93726 187,645 (2 refusals). Panes 78%, workers 22%.
  Pre-bind history 4,866,773 is reported but outside bound. Open holds 1,932,625 across 4 dead-looking sessions.
- U2 deliverables already owned elsewhere:
  1 GOAL_STATE canonical policy -> ce-a3b-r R1b d0d0eb2b (67/67, mutation killed). NOT LIVE: main checkout
    hooks/session_budget_guard.js:221 still has the substring regex. Install owner = a3b-r R3 (installer reused by WU-7).
  2 default binding by program path -> ce-lifecycle-v2 WU-1 (prospective binding), WU-1F RUNNING m-e6ff77095a67.
  3 coordinator sub-cap -> UNKNOWN owner; candidate WU-4 executable-authority admission.
  4 stale/late usage -> R2 goal-reconcile 10bf871b. Addendum (a) closeout deny -> 5ecd559b. Addendum (b) UNKNOWN
    fail-closed in admit_route -> lifecycle WU-4.
- Fault Capsule / autopsy: R5 6902264d. R5c m-447ca8005684 RUNNING (closes R5, arms R4).
- Deterministic out-of-band supervisor: gsd_mission sweep, Task Scheduler, "SWEEP OK running 61 s ago".
  Gap proved by R5 (halted on breaker before its Close -> chain parked): the sweep judges liveness but never
  advances a chain whose unit ended without its Close. Successor-by-sweep is lifecycle WU-5 (not yet built).

## 2. Root cause (one line each)
R1 continuation lives in the worker's last step (Close), so an overrun or refusal parks the chain -> Owner pane.
R2 cwd binding charges a coordinator's history (2aa0b0fb pre-bind 4.37M) -> caps cross on panes, not work.
R3 guard install has no certified path -> fixed code sits on branches while the live regex keeps refusing.
R4 seven economy mega-prompts in two days re-plan in-flight recoveries; each re-plan is itself coordinator spend.

## 3. Decisions (approve all with one reply)
C1 ce-a3 U2 = SUPERSEDED (no rerun). Proof of Non-Work: each deliverable's owner gate run green at merge time.
   ce-a3 closes with a non-success closure receipt; its ledger is reconciled once (goal-reconcile, before/after recorded).
C2 No new goal id. U3/U4/U5 get a Reality Delta each, then fold into the ce-a3b-r chain's ONE pending authority
   request (already planned for R6+R7). Owner answers that request once, by amount, in OWNER_QUEUE.
C3 Out-of-band succession = lifecycle WU-5, pulled forward to directly after WU-1F. Scope: the sweep reads each
   terminal mission; COMPLETED/HALTED without its Close -> generate the R5 Fault Capsule, then arm the packet's
   declared residual or successor through the existing admit gate, or write one AUTHORITY_REQUEST row. Singleflight
   by (mission_id, epoch). No new scheduler, no model in the loop.
C4 Success semantics: the sweep requires the packet's receipt file + done-gate line; process SUCCESS alone =
   RECOVERY_PENDING. Part of C3, same unit.
C5 Installer: a3b-r R3 as already approved. HR-001 makes ONE first-activation Owner command unavoidable in auto mode;
   after that pointer exists, every guard update is zero-Owner.
C6 This pane executes only C1 (deterministic, ~10 tool calls), writes the WU-5 packet + route into lifecycle-v2's
   queue via its receipt chain (never under its live writer), then checkpoints SAFE_TO_FORGET.

## 3b. Execution delta after approval (2026-10-08 ~17:05)
- C3's owner already exists as lifecycle **WU-1H** (recovery plan row: on HALTED the supervisor writes a fault capsule
  + partial receipt and arms the recompiled next unit; a mutant that requires a normal receipt goes red). "WU-5 pulled
  forward" = WU-1H inserted directly after WU-1B, reusing R5's `mission_capsule.fault_capsule` (DO_NOT_DUPLICATE).
- Third live instance of the failure: R5c's Close ran `arm` twice WITHOUT `--no-launch`, launching two packet-less
  `/gsd-autonomous` sessions in pp-ce-a3b-r with the 7.5M auto envelope (m-413f1e324aa5 NO_PHASES, m-d84de9dd1edb
  blocked on a question), then handed "run these two commands" back to a person. Both put on owner hold by this pane.
  ce-a3b-r went 5.87M -> 8.23M used (open 1,435,755 held by those sessions, reconcile classes them LIVE).
  Remaining 370,249: R4 (1.73M) no longer fits -> per B1, ONE authority request instead of arming.
- WU-1H must therefore also own: the arm recipe as ONE deterministic call (arm --no-launch + envelope + admit), so a
  worker can never half-arm or launch without a packet.

## 4. Done-gate
V-A3C-SUPERSEDED: U2 gates green on their owner branches. ce-a3 closure receipt + reconcile before/after committed.
V-SWEEP-SUCCESSION: a unit ending without its Close is advanced by the sweep with no pane (canary: re-run R5's shape).
V-SUCCESS-WITHOUT-RECEIPT: process success + no receipt -> RECOVERY_PENDING, no dependent launch.
R1 guard live by hash (R3). One authority request raised once; YES continues, NO defers.
A3 terminal: U3-U5 each DONE, SUPERSEDED or DEFERRED-by-Owner-NO, with evidence.
