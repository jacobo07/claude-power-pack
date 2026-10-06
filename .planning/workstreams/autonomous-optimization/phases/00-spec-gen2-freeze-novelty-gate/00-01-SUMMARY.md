---
phase: 00-spec-gen2-freeze-novelty-gate
plan: 01
subsystem: spec-gate
tags: [sdd-os, hr-novelty-001, v-gates, ic-gen2, spec, mutants]
requires: []
provides:
  - "T3 programme spec vault/specs/autonomous-optimization.md (READY at tier 3, REFERENCED binding)"
  - "HR-NOVELTY-001 record, verdict EXTEND_EXISTING_OWNER, 13 of 13 mechanically resolved citations"
  - "tools/test_ao_p0.py judge with 22 gates and 10 mutants"
affects: [00-02, 00-03, 00-04, 00-05]
tech-stack:
  added: []
  patterns: ["spec judged by modules.sdd_os readiness + spec_binding", "citations pinned to a sweep_commit and resolved via argv-list git"]
key-files:
  created:
    - vault/specs/autonomous-optimization.md
    - vault/audits/autonomous-optimization-novelty-2026-10-05.md
    - tools/test_ao_p0.py
  modified:
    - .planning/workstreams/autonomous-optimization/STATE.md
key-decisions:
  - "D-OQ1..D-OQ5 recorded as RESOLVED Q1..Q5 in the spec; D-OQ3 also a Decisions bullet in the workstream STATE.md"
  - "Novelty citations resolve against the file as committed at front-matter sweep_commit, not the live working tree"
requirements-completed: [AO-01, AO-02]
duration: 30min
completed: 2026-10-06
status: complete
commits: 2
plan_head_before: 9b2bb43a12c81b148a8ae51f38b43d8ea6f95dce
actuals:
  tokens: 12970
  tasks: 2
  commits: 2
---

# Phase 0 Plan 01: T3 spec and HR-NOVELTY-001 record Summary

**T3 spec for IC-gen2 (READY, REFERENCED, disjoint covers, D-OQ1..D-OQ5) plus a 13-answer novelty record with verdict EXTEND_EXISTING_OWNER, both judged by `tools/test_ao_p0.py` (22/22, every rule killed by a mutant).**

## Performance

- Duration: about 30 minutes
- Tasks: 2 of 2 complete, 2 task commits (the plan-level docs commit follows this file)
- Files: 3 created, 1 modified

## Accomplishments

- `vault/specs/autonomous-optimization.md`: flat readiness front matter (`covers` x5, `open_questions` Q1-Q6 RESOLVED, `acceptance` AC-1..AC-13, `must_still_pass` x4, `checkpoints` CP-1..CP-11), all Tier 3 headings, kill switches KS-1..3 LIVE and KS-4..5 PLANNED, measured baseline with commands, section 11 states the D-OQ3 done-gate verbatim.
- `modules.sdd_os.readiness.assess(spec, 3)` returns `READY` with an empty `missing`. `find_bound_spec("vault/specs/autonomous-optimization.md gen2 ledger freeze")` is REFERENCED to the spec; every covers entry probe is STRONG to the spec; the plan-of-record probe stays STRONG to the plan; nothing AMBIGUOUS.
- `vault/audits/autonomous-optimization-novelty-2026-10-05.md`: live keyword-gate output (plan and ROADMAP silent, two positive controls fire), a sweep of ten recorded commands with hit counts including two absence claims each with a positive control, 13 rows in the exact order of `NOVELTY_PROOF_QUESTIONS`, 33 citations.
- `tools/test_ao_p0.py`: spec gates (READY, SECTIONS, COVERS-DISJOINT, BINDS, DECISIONS, STATE-D-OQ3), novelty gates (13, CITES-RESOLVE, GATE-CONTROL, VERDICT, SWEEP-RECORDED), 3 spec mutants and 6 novelty mutants, each behind a clean control. Run: `python3 tools/test_ao_p0.py` prints `AOP0_PASS=22/22  threshold=22/22`.
- Novelty gates were written RED first: with the record absent the run printed `AOP0_PASS=10/12` with both novelty gates FAIL, then went 22/22 once the record existed.

## Task Commits

| Task | Commit | Subject |
|---|---|---|
| 1 (tracer) | a83d1d71 | docs(00-01): T3 spec for IC-gen2 autonomous-optimization + spec V-gates |
| 2 | 48e41f9e | docs(00-01): HR-NOVELTY-001 record for IC-gen2 + novelty V-gates |

Tracer gate: after task 1, `python3 tools/test_ao_p0.py` (10/10) and `assess(..., 3)` were re-run and passed before task 2 started. Tracer verified end-to-end, expanding.

## Verification Observed

- `python3 tools/test_ao_p0.py` exit 0, 22/22, zero FAIL lines.
- `python3 -c "... check_novelty_gate('new autonomous optimization operating system') ..."` prints `True operating system`.
- `grep -c "^verdict: EXTEND_EXISTING_OWNER"` on the record prints 1; the table has 13 data rows.
- `git diff --quiet 3f48f2e3 HEAD` over the plan of record, root `.planning/STATE.md`, `tools/gsd_mission.py`, both CE/SC program verifiers exits 0; no module file was added since `3f48f2e3`.
- Baselines re-run on 2026-10-06 at 9b2bb43a: `ENVPF_PASS=55/57` (fails `V-ENVPF-PP-REAL-READY`, `V-ENVPF-PP-STALE-REAL`), `PFP_PASS=28/28`, `LG_PASS=20/20`, IC `--final` red: L3 A,B,C,I,J,K,M,N, L8 x4, `CEP_VERDICT=FAIL failures=12`, `ICP_VERDICT=FAIL failures=1`. These are inherited state, reported verbatim, never claimed green.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Novelty citations pinned to a sweep commit instead of the live tree**
- **Found during:** Task 2 design
- **Issue:** the plan resolves citations against the current file. Phase 1 edits `tools/usage_index.py` (schema v5) and later phases edit the kme and ratchet files, so the cited lines would move and `V-AOP0-NOVELTY-CITES-RESOLVE` would go red for legitimate work.
- **Fix:** the record carries `sweep_commit: a83d1d71...` in its front matter; each citation must be a git-tracked path inside the repo (`git ls-files --error-unmatch`, argv list, no shell) AND verbatim on that line of the file at the sweep commit (`git show <sha>:<path>`); the sweep commit must be an ancestor of HEAD. All the plan's mutants are still killed.
- **Files modified:** tools/test_ao_p0.py, vault/audits/autonomous-optimization-novelty-2026-10-05.md
- **Commit:** 48e41f9e

**2. [Rule 3 - Blocking] STATE.md staged by blob, not by pathspec**
- **Found during:** Task 1 commit
- **Issue:** the plan commits STATE.md by pathspec, but the working copy already held the orchestrator's uncommitted tracking edits (frontmatter, Current Position); a pathspec commit would have swept them in against the instruction that the orchestrator owns tracking writes.
- **Fix:** built the blob as HEAD plus only the D-OQ3 bullet, staged it with `git update-index --cacheinfo`, committed. The orchestrator's edits remain uncommitted in the working tree, untouched (the working copy also carries my bullet, so the working file matches the commit plus their edits).
- **Commit:** a83d1d71

**3. [Plan consistency] Q6 text**
- The plan quotes `PFP_PASS=28/28 and LG_PASS=20/20 re-measured ... at 3f48f2e3`; I wrote that verbatim and appended "reproduced on 2026-10-06 at 9b2bb43a" after actually re-running both suites.

## Known Stubs

None.

## Threat Flags

None. No new network endpoint, auth path or file-access surface; the temp git fixtures run with `GIT_CONFIG_GLOBAL`/`GIT_CONFIG_SYSTEM` set to `/dev/null` and `SDD_OS_STATE_DIR` set to a temp dir (T-00-05).

## Notes for Later Plans

- Every later Phase 0 plan and task text should name `vault/specs/autonomous-optimization.md` literally; REFERENCED outranks STRONG.
- `ICP_GEN2_VERDICT`, `ICP_GEN2_SELFTEST`, `ICP_GEN2_AUDIT` and the `--generation 2 --status|--selftest|--audit|--final` modes are named in the spec's contract section and do not exist yet; plan 00-03 builds them. Spec acceptance AC-3..AC-6 depend on them. This is stated in the spec as the Phase 0 end state, not as present capability.
- The novelty record is HR-NOVELTY-001 satisfied: verdict EXTEND_EXISTING_OWNER, so the slice does not stop.

## Self-Check: PASSED

- FOUND: vault/specs/autonomous-optimization.md, vault/audits/autonomous-optimization-novelty-2026-10-05.md, tools/test_ao_p0.py
- FOUND commits: a83d1d71, 48e41f9e (`git rev-list --count 9b2bb43a..HEAD` = 2)
