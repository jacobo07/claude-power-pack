---
phase: 01-mission-relay-in-a-shared-checkout
status: human_needed
verified: 2026-10-03
plane: gex44 (tests); laptop (PRG, pending)
score: 3/4
human_verification:
  - "Criterion 4 (PRG): a real held mission relays in the laptop's live sweep -- owner bundle line [A]"
---

# Phase 1 verification -- pillar A

Code-complete on the laptop at `d2505df6` (ancestor of this branch). This run did not re-implement A
(ROADMAP, run-plane section).

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | red test reproduces the hold before the fix | ✓ | session c47b1f78: TypeError on proven_workstream before the fix (STATE.md) |
| 2 | Brand #001 shape stays blocked | ✓ | V-MCA-DIVERGED unchanged, in `tools/test_gsd_mission_cwd_align.py` 16/16 on GEX44 |
| 3 | three-relay drill + mutation drill | ✓ | V-MCA-DIVERGED-THREE-RELAYS green; drills m1-m7 KILLED (laptop session) |
| 4 | PRG in the live sweep | ○ | laptop-plane; `vault/programs/incremental-cognition/owner-bundle.md` [A] |

Re-run on GEX44, 2026-10-03, this branch:
- `python3 tools/test_gsd_mission_cwd_align.py` -> MCA_PASS=16/16
- `python3 tools/test_gsd_epoch.py` -> EPOCH_PASS=82/82
- `python3 tools/test_gsd_mission.py` -> MC_PASS=212/213. The red is V-MC-PLAN-FACTS-REFUSES-OVERLAP, a GEX44
  plane fact: `plan_graph_check` reports `engine: node v18.19.1 outside ^22.23.2 || ^24.14.0`. It is not part of
  pillar A's hunk; it is an interpreter-integrity finding routed to pillar B.

Pillar A's ledger state stays open (`state.A = {}`): IMPLEMENTED_AND_VERIFIED needs the `prg` evidence.
