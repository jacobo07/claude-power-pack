# L4 live install receipt (ADV2a + S5d) -- zero model work end to end

Status: INSTALLED
- Merge: tools/lifecycle_stage_merge.py. It did a deterministic 3-way merge-file on LF-normalised blobs (ours = LIVE HEAD
  2daf0f62, base c6b61030, theirs 4caca0e9) in stage pp-live-stage4, with 0 conflicts. No merge worker was needed. That
  replaces the WU-INST2-style model unit, which cost 511K for the same job.
- Stage suites: STEWARD 20/20, HALT 21/0, ADVANCE 4/0, ADM 43/43, LIFE 6/0, MC 226/227 (pre-existing FAIL).
- Patch: install/L4-steward-adv.patch, sha256 9A227234B0C15F29C9A97CFDC8091D9FDB4D9305BC727BA255D87BDD09FE26AC.
- Live commit: ed566db0 (was 2daf0f62), applied by tools/lifecycle_install_apply.ps1. Foreign edits (3,877 bytes) were
  re-applied on top.
- Live suites:
  - pass: HALT 21/0, ADM 43/43;
  - MC 226/227: the FAIL is pre-existing;
  - LIFE 5/1 in the script run: V-LIFE-PREMODEL-TRANSPORT. Re-run alone twice on live it gave 6/0 and 6/0, so it is
    flaky under host load. L4 touches no hook.
- Stage removed.

Live from ed566db0:
- the steward settles every terminal worker (including COMPLETED and goal-less records);
- a title-line PARTIAL is not a receipt;
- consume-once approval_id;
- goal-aware admit_route.
The manual settle_terminal.py workaround is retired.
