# L5 live install receipt (WU-ADV2b advance stage) -- zero model work

Status: INSTALLED
- Merge: tools/lifecycle_stage_merge.py, with ours = LIVE HEAD f0ecee15, base 4caca0e9, theirs b11eaeef, in stage
  pp-live-stage5. One conflict: live's _unit_done sits next to the branch's supervise -> _supervise_core rename.
  It was resolved by keeping both, with a single-shape regex resolver that refuses any other shape.
- Stage suites: ADVANCE 12/0, HALT 21/0, STEWARD 22/22, ADM 43/43, LIFE 6/0, OWNER_HOLD 32/32, MC 226/227 (pre-existing).
- Patch: install/L5-advance.patch, sha256 CB891671FD6D250EDBD834A40EF3BE837589C2E06AE014AE26227A6663DFD1DA.
- Live commit: f3c0f8a0 (was f0ecee15) via tools/lifecycle_install_apply.ps1. Foreign E4a edits (3,877 bytes)
  were re-applied on top.
- Live suites: LIFE 6/0, HALT 21/0, ADM 43/43, ADVANCE 12/0, STEWARD 22/22, OWNER_HOLD 32/32. MC 226/227: the only
  FAIL is the pre-existing V-MC-SUP-HOST-UNANSWERED-NOT-BLOCKED. The script exits 2 on any rc!=0, by design.

Live from f3c0f8a0: every sweep pass runs advance_pass after the missions (CPP_SWEEP_ADVANCE=off disables).
With no <state>/approvals dir it is a no-op. An approval record {approval_id, plan_path, goal, repo, cap_delta?}
on a plan with front matter {status: APPROVED, units, packet_dir} arms the next listed unit once.
