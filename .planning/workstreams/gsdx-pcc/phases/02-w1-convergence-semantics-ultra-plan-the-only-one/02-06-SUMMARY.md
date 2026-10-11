# 02-06 SUMMARY -- phase-end evidence

PLAN_BASE = f234ad16 (02-05 summary commit)

## Done
- Task 1 (`a051673e`, `c8c58d91`): 12 isolated-copy mutation drills, every one `MUTANT KILLED` after a passing control (`drills/<id>-drill.log`). Two needed one gate fix (below). Live tree untouched: proof.py and convergence.py hashes equal before and after.
- Task 2 (`425db6d3`): guard SAME before and after; 19 suites, 0 DIFFERS, all exit 0, 17 incumbent counts equal Phase 1, `GSDX_PCC_SEMANTICS_PASS=48/48`, `GSDX_PCC_REPLAY_PASS=28/28`; liveness `gate offenders: 0`, `EXIT=0`; V-PCC-NO-LEGACY-EDIT: the only row is `A modules/gsd_x/goal/proof.py`; golden `98609c4f` is an ancestor of proof.py's adding commit `735170c0` (exit 0).
- Task 3 (`0b46f2bd`): COVERAGE.md, 02-EVIDENCE.md (gaps 6 = rows 6, 8 edge-probe rows, verdicts never upgraded), DENOMINATOR D43 and D44 DONE, D01/D03/D10 OPEN with the Phase 2 part cited, UKDL `T-FAILURE-SENTINEL-COMPARES-EQUAL-TO-ITSELF-001`.

## Deviations
- Drill blind spots (Regla 12, one fix each, tests only): `V-PCC-STATE-NOT-IN-DISPOSITION` survived a `setattr(o, "disposition", ...)` write, so `scan_disposition` now flags it; `V-PCC-FINGERPRINT-OUTSIDE-ROOT` survived removing the `..` clause because the resolve check also refuses escaping paths, so the gate now pins `sub/../a.txt` as unknown. No known limit remains.
- Three first drills were `CONTROL_INVALID`: the copy lacked the phase dir that V-PCC-SPEC-RESOLVED reads. `copy_dirs` of every spec now includes it.
- The drill `EXIT=` line is appended with `$LASTEXITCODE` (`%ERRORLEVEL%` expands at parse time).
- Fixture judge replay 4.8 s and 12.3 s vs Phase 1's 0.4 s (CLI wall 14.591 s and 37.826 s vs 1.558 s): over 2x on a host at 100% CPU and 1.1-3.4 GB free; judge.py unchanged. Recorded OBSERVED, not as a regression claim (a repeat run is in `02-timeline-fixture-repeat.*`).
- The UKDL append shows one deleted line in `git diff --numstat`: the old last line had no trailing newline and gained one; `--ignore-space-at-eol` shows 0 deleted.
- A PowerShell case-insensitivity slip (`$G` overwrote `$g`) broke the first git-invariants log; it was rewritten with distinct names before commit.

## Open
- D01, D03, D10 stay OPEN (Phase 4, Phase 10). R12 fix is Phase 4.
