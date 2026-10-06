---
opportunity: OPP-001
programme: IC-gen2 autonomous-optimization
plane: gex44
measured_at: "2026-10-06T11:28:27Z"
spec: vault/specs/autonomous-optimization.md
commits: [ea8c51f6c2510e914fa5324088f5ed1a0ac13b4a, 62152c0bba4ff7d9dbfdf052ddd86aa871e2e0a0, 21bafb5d9b3d87c2d23df7ad6261b80fc3d9aa0d]
status: observed -> priced evidence only; no dividend claimed, nothing promoted (the row itself is written by plan 00-04)
---

# OPP-001: pp_install judged by commit-hash ancestry only

First opportunity of the IC-gen2 programme (autonomous-optimization), governed by
`vault/specs/autonomous-optimization.md` (covers entry `pp-install-floor-by-pick`). Owner of the fix: the existing
`tools/gex44_env_preflight.py` (EXTEND; no new tool).

## Symptom

The one-arm waiver recorded in `.planning/workstreams/autonomous-optimization/STATE.md` (Decisions, 2026-10-05):

> default env with CPP_NODE_EXE=/opt/node-v24.14.0/bin/node NOT_READY on pp_install_stale only = hash-floor false
> positive (picks 25a10ce5/308da56b in live 4856b50d; PFP 28/28, LG 20/20 on GEX44). [...] The waiver covers this arm
> only; a re-arm needs exit 0 or a new waiver.

Pre-fix output, measured on this worktree (plane gex44), command `python3 tools/gex44_env_preflight.py --current --checks pp_install`
(the pre-fix blob run at HEAD 21bafb5d):

```
NOT_READY    pp_install    floor 5962571c is not in this install's history (head 21bafb5d)
PREFLIGHT=NOT_READY reasons=pp_install_stale
```

(measured at planning time on HEAD 3f48f2e3 with the same text, exit 1). The code the floor stands for is present; the
install reads stale, so every re-arm of the default env needs an Owner waiver.

## Root cause

`check_pp_install` judged the floor by commit-hash ancestry alone: `rev-parse --verify` of the floor (pre-fix source line 293:
`is not in this install's history`) then `merge-base --is-ancestor` (pre-fix lines 295-300: `does not contain the floor`);
pre-fix `tools/gex44_env_preflight.py` as of commit ea8c51f6c2510e914fa5324088f5ed1a0ac13b4a. On GEX44 the floor object
(`5962571c`, which equals `PP_COMMIT_FLOOR`) is ABSENT from the clone (`git cat-file -t 5962571c` fails), while the code
arrived as `git cherry-pick -x` picks: commit 25a10ce568d43a7a0d12296803d8fe8a4ffd537a ends
`(cherry picked from commit 5962571c...)` (the full 40-hex equals `PP_COMMIT_FLOOR`) and commit
308da56b0b9c5aff5b5f449c5b83cfefc44be70e carries the exact trailer for `60e7947d`. A pick has a different hash from its
source, so hash ancestry cannot see it. With the floor object absent a patch-id comparison against the floor is
impossible too, so on this host only the trailer can establish the pick.

## Red first

Test-only commit ea8c51f6c2510e914fa5324088f5ed1a0ac13b4a, recorded run `/tmp/envpf-red.txt` against the unfixed source
(plane gex44, HEAD 8170c940):

```
ENVPF_PASS=57/64
FAIL V-ENVPF-PP-READY-VIA-ANCESTRY      (no floor_via detail yet)
FAIL V-ENVPF-PP-PICK-TRAILER-READY      state=NOT_READY reasons=['pp_install_stale']
FAIL V-ENVPF-PP-PICK-FLOOR-ABSENT-READY state=NOT_READY: floor a1f63488 is not in this install's history
FAIL V-ENVPF-PP-PICK-PATCHID-READY      state=NOT_READY: head bdd493fb does not contain the floor a1f63488
FAIL V-ENVPF-PP-TRAILER-SPOOF-STALE     refuses, but with the floor-absent message
FAIL V-ENVPF-PP-REAL-READY, V-ENVPF-PP-STALE-REAL   (the two inherited reds, same cause)
PASS V-ENVPF-PP-UNRELATED-STALE, V-ENVPF-PP-PICK-REQUIRED-FILE
```

The fixtures are hermetic temp repos (`make_pick_install`); the floor-absent fixture is a
`git clone --no-local --single-branch --branch main` so the floor object is genuinely missing, as on GEX44.

## Fix

Three accept paths, first one that holds wins, reported in `detail.floor_via`:

1. `ancestry`: HEAD contains the floor (unchanged).
2. `cherry_pick_trailer`: `git log -F --grep "(cherry picked from commit <full 40-hex floor>)"` over HEAD (commit
   62152c0bba4ff7d9dbfdf052ddd86aa871e2e0a0). Fixed string, full 40-hex only: a different sha or the floor abbreviated to 8 hex does
   not match. Works with the floor object absent.
3. `patch_id`: only where the floor object exists, an equal `git patch-id --stable` among the last
   `PP_PATCH_ID_SCAN = 300` non-merge commits of HEAD (commit 21bafb5d9b3d87c2d23df7ad6261b80fc3d9aa0d). No stored patch-id
   constant (D-OQ2).

Any non-ancestry accept adds the non-refusing finding `floor_by_pick`. `detail.floor_present` records whether the floor
object exists. Unchanged: required files are checked on every path, a probe git cannot answer is UNMEASURABLE (never READY),
a timeout is UNMEASURABLE. Drill: M7-M10 added, M3 retargeted to the hermetic `V-ENVPF-PP-STALE-NOT-ANCESTOR`.

## Proof

All on plane gex44, this worktree.

- `python3 tools/test_gex44_env_preflight.py` -> `ENVPF_PASS=64/64  threshold=64/64`, including
  `V-ENVPF-PP-PICK-TRAILER-READY`, `V-ENVPF-PP-PICK-FLOOR-ABSENT-READY`, `V-ENVPF-PP-PICK-PATCHID-READY`,
  `V-ENVPF-PP-UNRELATED-STALE`, `V-ENVPF-PP-TRAILER-SPOOF-STALE`, `V-ENVPF-PP-PICK-REQUIRED-FILE`,
  `V-ENVPF-PP-READY-VIA-ANCESTRY`, `V-ENVPF-PP-REAL-READY`, `V-ENVPF-PP-STALE-REAL`.
- `python3 tools/test_gex44_env_preflight.py --drill` -> `PASS DRILL-CONTROL unmutated run: 64/64 gates green`,
  `KILLED` for M1..M10 (M3 by V-ENVPF-PP-STALE-NOT-ANCESTOR; M10 "ancestry path dropped" by V-ENVPF-PP-READY-VIA-ANCESTRY),
  `PASS DRILL-CLEAN-AFTER-MUTANTS ... 64/64`, `DRILL killed=10/10`, exit 0.
- `python3 tools/gex44_env_preflight.py --current --checks pp_install` -> `READY pp_install head 62152c0b contains the
  floor 5962571c via cherry_pick_trailer`, `PREFLIGHT=READY reasons=-` (`--json`: `floor_present: false`,
  `floor_via: cherry_pick_trailer`, findings include `floor_by_pick`).
- `python3 tools/test_persistent_failure_park.py` -> `PFP_PASS=28/28  threshold=28/28`.
- `python3 tools/test_mission_launch_gate.py` -> `LG_PASS=20/20  threshold=20/20`.

## Honest limits

- A trailer asserts a pick; it does not prove the code is identical. A conflict-resolved pick has a different patch-id, and an
  unrelated commit carrying the exact full-sha trailer would be accepted (threat T-00-07, accepted: the install is the
  Owner's own checkout, and the acceptance is visible as `floor_by_pick`).
- On GEX44 the patch-id path cannot run because the floor object is absent; only the trailer path can accept. A stored floor
  patch-id (which would let a no -x pick be accepted without the object) needs the laptop where the floor exists: owner-bundle
  `[P0]` (IC-gen2), status PLANNED, not built in Phase 0.
- The live GEX44 install is never updated by hand; it receives this fix only through its normal fast-forward sync, so the
  realized effect on that install is UNMEASURED until that sync happens and its own preflight is read. The READY above is the
  mission worktree, whose HEAD contains the pick 25a10ce5.
- The pre-fix and fixed timings below compare runs whose verdicts differ (NOT_READY vs READY), so the carrying delta is an
  upper-level indication for one host, not a benchmark.

## Cost

- Build: `git diff --stat 8170c940 HEAD` -> 2 files changed, 185 insertions(+), 17 deletions(-)
  (`tools/gex44_env_preflight.py` 102 lines changed, `tools/test_gex44_env_preflight.py` 100).
- Proof: `python3 tools/test_gex44_env_preflight.py` 4.8 s wall, `--drill` 20.4 s wall (Python `time.monotonic` around
  `subprocess.run`).
- Carrying: command `python3 <script> --current --checks pp_install`, three runs each via Python `time.monotonic`.
  Pre-fix blob (`git show ea8c51f6c2510e914fa5324088f5ed1a0ac13b4a:tools/gex44_env_preflight.py`, written to a temp file inside `tools/`,
  run, then removed): runs 0.045, 0.047, 0.047 s, median 0.047 s. Fixed source: runs 0.059, 0.060, 0.053 s, median
  0.059 s. Median delta +0.012 s per preflight (one extra `git log --grep` probe on the trailer path; the patch-id probes do
  not run on GEX44).
- No token or money figure is claimed.
