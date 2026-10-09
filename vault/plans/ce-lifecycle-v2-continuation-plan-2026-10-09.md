---
id: PLAN-CE-LIFECYCLE-V2-CONTINUATION
status: APPROVED (Owner "y" 2026-10-09)
extends: ce-lifecycle-v2 bootstrap master plan (79350a8e) + ce-a3 Amendment D (3aa002af, f6707f50)
covers: [bootstrap-install-l1, steward-merge, stopped-reservation-settle, wu-adv-finish, resource-admission, sibling-immunization, a3-u3-u5]
---

# ce-lifecycle-v2 continuation (2026-10-09)

## Reality delta (measured 2026-10-09 ~09:30 UTC)
- WU-1H closed DONE in four epochs: 926K, 755K, 645K and a 7-call fourth. Code is in d948be61 and the receipt in 62a62dfb.
  - HALT_CONTINUES 10/0, mutants 3/3 killed, ADM 43/43, MC 224/225 (the one FAIL is pre-existing).
  - LIFE 5/1: V-LIFE-PREMODEL-TRANSPORT is open. It is not attributed to this change.
  - The gsd_mission.py sha256 is 48B2AED4... It is NOT installed.
  - m-93c9624fb4cc (WU-1H2) is HALTED/DEAD. The later epochs were armed by the workers themselves.
- WU-ADV epoch 1 tripped at 833K (stop 800K) at 22:42 local on 10-08.
  - Only a stub receipt was committed (014f1edb).
  - These are uncommitted: the ledger.py approval_id change, plus _logs/wuadv/block.py and patch1.py, written but not applied.
  - No successor was armed, so the chain has been idle for about 11 h.
  - Cause: halt-continues lives on the branch, but the sweep runs the LIVE tree.
- Goal ce-lifecycle-v2: cap 8,847,012, used 6,605,944 (settled 4,469,374 + open 2,136,570), remaining 2,241,068.
  - The open amount is exactly the last lease of 8 sids, all from terminal missions: 2749eadd, 08e522e6, e175caf4 (WU-1C dead), 25dbb281, e20d53dc, d15aa8c5, d2954408, a09325c7.
- OWNERSHIP COLLISION. In C:\Users\User\Apps\pp-gsdx-factory-2 (branch gsdx-factory/v2), unit WU-S1 "mission steward" is being built. The packet says Owner "y" option b; the plan frontmatter still says PROPOSED.
  - Its scope: settle_stopped/correct ledger ops, a fallback receipt, salvage, a residual packet, arming a successor, and forgotten-mission detection.
  - It edits the same files: ledger.py, gsd_mission.py, mission_spend.py.
  - Its worker m-ffb75e73f813 halted at 2.71M. 18/18 tests pass, but nothing is committed.
- Resource: free RAM 2.3 of 31.3 GB, 27 claude and 39 Cursor processes.
  - Zero Resource-Exhaustion-Detector events in the System log in the last 3 days.
  - Whether RAM pressure killed WU-1C is UNKNOWN; there is no evidence either way.

## Ownership
- STOPPED-worker settle, fallback receipt, salvage, residual and successor arm: OWN = S1 (steward). lifecycle-v2 REUSES it and does not duplicate it.
- HALTED-with-capsule renew: OWN = WU-1H (d948be61). S1 calls into it, or the merge keeps one path; the decision comes from a bounded diff of the two.
- Approval consumer, advance stage and goal-aware admission: OWN = WU-ADV.
- Installer: WU-INST (L5).
- Progress tripwire plus resource admission: WU-TRIP (L6).
- A3: U3 = WU-FLOOR, U4 = WU-GEX, U5 = WU-CLOSE (merged with a3b-r R7). U2 is SUPERSEDED.

## Units
B1. Merge decision, zero model, this pane.
  - Diff S1 against WU-1H at the supervise() tail. One owner per transition, written in both RESUMPTION files.
  - Tell the gsdx coordinator.
B2. Bootstrap break: certified install of L1, authorized by Amendment D section 5, which names L1/L2/L6 gsd_mission changes.
  - Stage a worktree of the live HEAD, run a 3-way merge-file, and run the 4 suites there.
  - Pathspec commit in LIVE; sha receipt; revert if red. No Owner copy.
B3. Reservation reconcile, zero model.
  - For each of the 8 sids: process dead (host list plus pid), then transcript-measured tokens vs. the last settle.
  - Settle the tail and close the lease. A missing transcript stays held as UNKNOWN.
  - Expected release is up to 2,136,570 minus the unsettled tails.
B4. WU-ADV2, slim and capped at 18 calls.
  - Apply patch1.py and continue from the progress note. No re-read.
  - Then the L2 install in the same way as B2. This is the first unit running under live halt-continues.
B5. Packet immunization before funding anything else.
  - Every remaining packet gets: cited line ranges only, checkpoint first, no fresh-pane ending, a call cap.
  - Estimates are rebased on measured epochs: WU-1H cost about 2.4M against a 0.6M forecast.
  - Resource admission goes into WU-TRIP: free-RAM floor, then HOLD the launch with the reason RESOURCE_PRESSURE, retry each sweep, never kill. Free RAM is logged at every launch and exit.
B6. Chain: WU-1C, 1D, INST, TRIP, FLOOR, GEX, CLOSE through the sweep, the advance stage and the steward.
  - Units run in priority order inside the existing cap.
  - The first unit that does not fit writes WAITING_FOR_AUTHORITY. There is never an overrun.

## Done-gate
Amendment D section 6, plus:
- WU-ADV continued with no pane.
- The 8 stopped sids settled or held as UNKNOWN.
- RESOURCE_PRESSURE hold canary green.
- A3 U3/U4/U5 each DONE, NO_WORK or MERGED.
