---
gsd_state_version: "1.0"
milestone: v1
milestone_name: incremental-cognition
current_phase: 1 — Mission relay in a shared checkout
current_plan: Not started
status: planning
stopped_at: P0 freeze sealed interactively; Phase 1 starts in-pane (RAM below the arming boundary)
last_updated: "2026-10-03T00:00:00.000Z"
last_activity: 2026-10-03
last_activity_desc: Workstream created from the approved incremental-cognition program
progress:
  total_phases: 6
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
workstream: incremental-cognition
created: 2026-10-03
current_phase_name: Mission relay in a shared checkout
---

# Project State

## Mission

Incremental Cognition Program: a delta over cognitive-economy and skill-capability. Drive pillars A-N to
evidence-backed terminals. Mission terms: incremental-cognition, context-rent, institutional-memoization,
invalidation, cognitive-compiler, baseline-ratchet.

## Current Position

**Status:** Ready to plan
**Current Phase:** 1 — Mission relay in a shared checkout

## Decisions

- [Plan / audit G1]: the CE verifier's stale V-CEP-REAL-HANDOFF is replaced in the wrapper (SC precedent); the CE
  file is never edited. The defect is handed to the CE owner.
- [Audit G3]: consuming pillars (H, I, J, M) close only through R2 against the owner ledger at a commit on HEAD.
- [Audit G4]: pillar A design = a non-blocking status for a worktree the predecessor provably worked in; the Brand
  #001 shape stays blocked.
- [Audit G6]: the gsd_mission.py repair is deployed only at >= 4 GB free RAM.
- [Plan]: arming waits for pillar A and >= 4 GB free; until then phases run in the interactive pane.

## Session Continuity

**Stopped At:** Phase 1 (pillar A), RED step. P0 committed 18e928af, FROZEN_AT d4d35059.
`tools/test_gsd_mission_cwd_align.py` has 4 NEW uncommitted cases (V-MCA-DIVERGED-FOLLOWED / -UNPROVEN /
-STALE-ROADMAP / -THREE-RELAYS) calling `gm.align_cwd(cwd, wt, proven_workstream="ws")`; the
`threshold=9/9` line still needs 13/13. Not yet run (expected RED: align_cwd has no proven_workstream).
**Next exact action:** run `python tools/test_gsd_mission_cwd_align.py` -> confirm RED; then in a SCRATCH copy
of tools/gsd_mission.py add `proven_workstream=None` to align_cwd: in the diverged branch return
`diverged_followed` (NOT in CWD_ALIGN_BLOCKING) iff proven_workstream and work_dir is a worktree top of the
same repo and `_worktree_carries_workstream(work_dir, cwd, proven_workstream)`; at supervise ~1481 split
`ew = effective_workdir(...)`, `work_dir = ew or rec.get("work_dir")`, pass
`proven_workstream=rec.get("workstream") if ew and ew != rec["cwd"] else None`, ledger event
`cwd_diverged_followed`. Run cwd_align + test_gsd_mission + test_gsd_epoch + legacy golden; mutation drill;
deploy into the live file only at >= 4 GB free RAM (audit G6).
**Resume File:** this STATE.md + vault/plans/incremental-cognition-program-2026-10-03.md
