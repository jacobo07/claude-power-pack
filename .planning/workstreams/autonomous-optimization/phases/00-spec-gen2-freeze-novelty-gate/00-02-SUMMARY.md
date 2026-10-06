---
phase: 00-spec-gen2-freeze-novelty-gate
plan: 02
subsystem: env-preflight
tags: [pp-install, cherry-pick, patch-id, v-gates, mutation-drill, ic-gen2, opp-001]
requires: [00-01]
provides:
  - "check_pp_install with three accept paths: ancestry, exact cherry-pick trailer, equal patch-id (floor object present only)"
  - "7 new V-ENVPF-PP-* gates, drill mutants M7-M10, M3 retargeted; drill killed=10/10 with a green control"
  - "OPP-001 evidence file and the IC-gen2 owner bundle with the [P0] patch-id line"
affects: [00-04]
tech-stack:
  added: []
  patterns: ["hermetic temp-repo fixtures (git clone --no-local for an absent object)", "helper-per-accept-path so each path is one patchable mutant seam"]
key-files:
  created:
    - vault/programs/incremental-cognition/gen2/evidence/OPP-001-pp-install-hash-floor.md
    - vault/programs/incremental-cognition/gen2/owner-bundle.md
  modified:
    - tools/gex44_env_preflight.py
    - tools/test_gex44_env_preflight.py
key-decisions:
  - "D-OQ2 honoured: no stored patch-id constant; on GEX44 only the trailer path can accept, the [P0] owner-bundle line requests the laptop-side value"
  - "Single unified refusal message 'head <h8> does not contain the floor <f8> (<why>)' for every refusal, which keeps V-ENVPF-PP-STALE-REAL's assertion true when the floor object is absent"
requirements-completed: [AO-02]
duration: 25min
completed: 2026-10-06
status: complete
commits: 4
plan_head_before: 8170c940ab31b80ed350dfe0419fd56078a026bd
actuals:
  tokens: 7206
  tasks: 3
  commits: 4
---

# Phase 0 Plan 02: pp_install floor-by-pick Summary

**`check_pp_install` now accepts the floor by ancestry, by an exact full-sha `(cherry picked from commit <floor>)` trailer (works with the floor object absent, the GEX44 case), or by an equal `git patch-id --stable` where the object exists; `--current --checks pp_install` is READY on this worktree, the drill kills 10/10 behind a green control, and the red tests were committed first.**

## Performance

- Tasks: 3 of 3 complete (task 1 tracer, task 2 auto/tdd, task 3 auto); 4 commits (red, fix, fix, docs), the plan-level SUMMARY commit follows this file
- Files: 2 created, 2 modified; `git diff --stat 8170c940 HEAD` before this file: 185 insertions, 17 deletions in the two tools files, plus the 2 docs files
- Plane: gex44

## Accomplishments

- Red first: `ea8c51f6` added `make_pick_install()`, `case(..., expect_detail, expect_why)` and seven gates; recorded run `ENVPF_PASS=57/64` with PICK-TRAILER-READY, PICK-FLOOR-ABSENT-READY, PICK-PATCHID-READY, READY-VIA-ANCESTRY (and TRAILER-SPOOF-STALE on its message) red.
- `62152c0b`: `_has_pick_trailer` (`git log -F --grep`, argv list, full 40-hex only), `floor_present` / `floor_via` detail keys, `floor_by_pick` finding, one refusal message. Tracer re-verified end-to-end before expanding.
- `21bafb5d`: `_Sandbox.run(input_text=)`, `PP_PATCH_ID_SCAN = 300`, `_patch_ids` / `_patch_id_match`, drill M7-M10, M3 retargeted to `V-ENVPF-PP-STALE-NOT-ANCESTOR`.
- `14e7518a`: OPP-001 evidence (all seven sections, three commit-pinned shas, measured cost) and the gen2 owner bundle with the `[P0]` line.
- The fixture's floor-absent clone raises if the floor object is present, so the gate cannot pass by accident of a plain local clone.

## Task Commits

| Task | Commit | Subject |
|---|---|---|
| 1 (red) | ea8c51f6 | test(00-02): red gates for pp_install floor-by-pick |
| 1 (green) | 62152c0b | fix(00-02): pp_install accepts the floor through an exact cherry-pick trailer |
| 2 | 21bafb5d | fix(00-02): pp_install patch-id path where the floor object exists + drill M7-M10, M3 retargeted |
| 3 | 14e7518a | docs(00-02): OPP-001 evidence + IC-gen2 owner bundle [P0] |

## Verification Observed (plane: gex44, run at HEAD 14e7518a)

- `python3 tools/test_gex44_env_preflight.py` -> `ENVPF_PASS=64/64  threshold=64/64`, exit 0 (was 55/57 at plan start; the two inherited reds V-ENVPF-PP-REAL-READY and V-ENVPF-PP-STALE-REAL are now green).
- `python3 tools/test_gex44_env_preflight.py --drill` -> `PASS DRILL-CONTROL ... 64/64`, KILLED M1..M10 (M3 by V-ENVPF-PP-STALE-NOT-ANCESTOR, M10 by V-ENVPF-PP-READY-VIA-ANCESTRY), `PASS DRILL-CLEAN-AFTER-MUTANTS ... 64/64`, `DRILL killed=10/10`, exit 0.
- `python3 tools/gex44_env_preflight.py --current --checks pp_install` -> `READY ... via cherry_pick_trailer`; `--json` shows `floor_present: false`, `floor_via: cherry_pick_trailer`, `floor_by_pick` in findings.
- `python3 tools/test_persistent_failure_park.py` -> `PFP_PASS=28/28`; `python3 tools/test_mission_launch_gate.py` -> `LG_PASS=20/20`; `python3 tools/test_ao_p0.py` -> `AOP0_PASS=22/22`.
- `git diff --quiet 3f48f2e3 HEAD -- tools/gsd_mission.py tools/test_cognitive_economy_program.py .planning/STATE.md` exit 0.
- OPP-001 verify one-liner exit 0; every 40-hex sha in the file is `commit` per `git cat-file -t`; `grep -c "[P0]"` on the owner bundle prints 1; `grep -c floor_by_pick` on the tool prints 3; `grep -c PP_PATCH_ID_SCAN` prints 3.
- Carrying cost (medians of 3, `python3 <script> --current --checks pp_install`): 0.047 s pre-fix, 0.059 s fixed; the verdicts differ, so this is an indication for one host, not a benchmark.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Floor sha omitted from the OPP-001 text**
- **Found during:** Task 3
- **Issue:** the acceptance criterion requires every full 40-hex sha in the evidence file to be a commit in `git cat-file -t`, but the floor `5962571c...` is the object that is ABSENT on this host (the whole point of the fix).
- **Fix:** the floor and the `60e7947d` pick source are named by 8 hex plus "the full 40-hex equals `PP_COMMIT_FLOOR`"; the five full shas in the file are all present commits.
- **Commit:** 14e7518a

**2. [Plan consistency] V-ENVPF-PP-TRAILER-SPOOF-STALE is red in the red run for a message reason**
- The spoof fixture uses a floor-absent clone, so before the fix it refused with the old "not in this install's history" message and the gate's `expect_why` ("does not contain the floor") failed. It passes once the unified message lands. The behavioural half (NOT_READY, `pp_install_stale`) held before and after.

**3. [Scratch file] Pre-fix blob run inside `tools/`**
- To time the pre-fix source with the repo as install, I wrote `git show ea8c51f6:tools/gex44_env_preflight.py` to an untracked `tools/_prefix_gex44_env_preflight.py`, ran it, and removed it (recoverable from the commit). `git status --short` is clean afterwards.

**Total deviations:** 1 auto-fixed (Rule 3) plus 2 notes. **Impact:** none on the plan's outcomes.

## Known Stubs

None.

## Threat Flags

None. No new endpoint, auth path or file-access surface; probes remain argv lists in the throwaway-HOME sandbox, the floor is `re.fullmatch`-validated 40-hex before any probe (T-00-08), the spoof gate covers a different sha and an 8-hex abbreviation (T-00-06), UNMEASURABLE-never-READY is pinned by the existing M1 plus the new M9 (T-00-10).

## Notes for Later Plans

- Plan 00-04 writes the `OPP-001` row in the gen2 ledger; its evidence file is `vault/programs/incremental-cognition/gen2/evidence/OPP-001-pp-install-hash-floor.md` (sha256 to be taken at that point) and the commit list is in its front matter.
- The live GEX44 install `4856b50d` gets the fix only through its normal fast-forward sync; its realized effect is UNMEASURED until then.
- `PP_PATCH_ID_SCAN = 300` is a cost bound: a pick older than 300 non-merge commits is not found by the patch-id path (the trailer path has no such bound).
- STATE.md and ROADMAP.md were not edited; the orchestrator owns tracking writes.

## Self-Check: PASSED

- FOUND files: tools/gex44_env_preflight.py, tools/test_gex44_env_preflight.py, vault/programs/incremental-cognition/gen2/evidence/OPP-001-pp-install-hash-floor.md, vault/programs/incremental-cognition/gen2/owner-bundle.md
- FOUND commits: ea8c51f6, 62152c0b, 21bafb5d, 14e7518a (`git rev-list --count 8170c940..HEAD` = 4); red commit precedes the fix commit
