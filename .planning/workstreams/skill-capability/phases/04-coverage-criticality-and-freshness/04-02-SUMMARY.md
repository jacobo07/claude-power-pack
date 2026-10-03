---
phase: 04-coverage-criticality-and-freshness
plan: 02
subsystem: skill-capability / pillar H (live-vs-mirror drift)
tags: [drift, freshness, mirror, pillar-H, gate]
status: complete
requires: [tools/verify_global_mirrors.py primitives]
provides: [tools/skill_mirror_drift.py, tools/test_skill_drift.py, evidence/H-live-gex44.json, evidence/H-drift.md]
affects: [04-03 (card half, reuses evidence_current/render), 04-04 (ledger closure)]
key-files:
  created:
    - tools/skill_mirror_drift.py
    - tools/test_skill_drift.py
    - vault/programs/skill-capability/evidence/H-live-gex44.json
    - vault/programs/skill-capability/evidence/H-drift.md
decisions:
  - "New tool, discovery.py and verify_global_mirrors.py untouched (git diff vs plan base 2dd5ab6c is empty for both)"
plan_head_before: 2dd5ab6ce2410b40a976d20dbc3f77875601991e
commits: 3
actuals:
  tokens: 20000
  tasks: 2
  commits: 3
metrics:
  completed: 2026-10-03
---

# Phase 4 Plan 02: Pillar H skills mirror drift Summary

Skills-specific mirror pass that compares each repo `skills/<name>/` (committed blobs, whole directory, LF-normalized digest) with the live copy, a gate driven from temp-git-repo poles, and a recorded, blob-reproducible gex44 plane.

`commits: 3` is the measured `git rev-list --count 2dd5ab6c..HEAD`; one of the three is plan 04-01's concurrent commit (1ad9ee71). This plan's commits are 97ded664 and a94256e6, plus the SUMMARY commit that follows.

## Commits

- 97ded664 `feat(04-02): H -- skills mirror drift tracer over committed blobs, temp-repo poles`
- a94256e6 `feat(04-02): H -- gex44 mirror recording, reproduction check, live red pole`

## Measured (gex44, recorded repo_commit 97ded6643... = the task 1 commit, which holds every skills/ blob)

Counts: IDENTICAL 13 (of which eol_only 10), DRIFT 1, ABSENT_LIVE 10, INCONCLUSIVE 0, 24 repo skills. Matches the plan-time figures.

`python3 tools/skill_mirror_drift.py --live` exit 1. DRIFT line:
`DRIFT android-reverse-engineering missing_live=['scripts/check-deps.ps1', 'scripts/decompile.ps1', 'scripts/find-api-calls.ps1', 'scripts/install-dep.ps1'] extra_live=[] changed=[]`

Reconciliation recorded in `H-drift.md`: the CONTEXT's "4 identical / 10 differ / 10 absent" is raw-byte SKILL.md; recomputed from the recording's raw shas it gives exactly 4/10/10. The whole-directory LF comparison gives 13/1/10 (the 10 raw "differ" are CRLF-vs-LF with equal content; the one DRIFT is invisible to a SKILL.md-only compare).

## Gate

`python3 tools/test_skill_drift.py`: 9/9 ok, exit 0. Last line: `SKD_PASS=9/9`.
Clauses: V-SKD-POLE-IDENTICAL, V-SKD-POLE-DRIFT (changed byte, truncated, deleted, extra), V-SKD-POLE-ABSENT, V-SKD-COMMITTED-NOT-WORKTREE, V-SKD-RECORD-REPRODUCES, V-SKD-RECORD-DRILL (9 mutants each landing on its own first non-ok part, plus unmutated and CRLF controls), V-SKD-GIT-FAILURE, V-SKD-EVIDENCE-CURRENT, V-SKD-EVIDENCE-DRILL.

Red runs:
- Tampered recording (android row re-typed IDENTICAL) via `--recording /tmp/04-02-tampered.json`: exit 1, `FAIL V-SKD-RECORD-REPRODUCES ... status FAIL: android-reverse-engineering: recorded IDENTICAL but the comparator gives DRIFT; counts FAIL ...`, `SKD_PASS=0/1`.
- `--live --repo /tmp/not-a-repo`: `INCONCLUSIVE git rev-parse rc=128: fatal: not a git repository ...`, exit 1, 0 `Traceback` lines.
- CE contract one-off (`_check_evidence("H", prg ...)`): `[]`. `H-drift.md` has no CR bytes.

## Deviations from Plan

1. [Rule 3 - scope] `find ~/.claude/skills -newer /tmp/04-02-start | wc -l` printed 2, not 0. Both files are hook logs in the separate claude-power-pack install (`claude-power-pack/vault/ceps/fires.jsonl`, `.../.auto-spawned.log`), written by the Woz/CEPS PostToolUse hook, not by this plan. No file under any repo-skill live directory changed; the pass only reads.
2. The CE one-off in the plan imports `test_skill_capability_program`, but `_check_evidence` lives in `test_cognitive_economy_program` (imported by the wrapper); the one-off imports both. No CE file edited.
3. Recorded rows carry extra fields beyond the plan's list (`repo_raw`, `live_raw`) so `eol_only` and the CONTEXT's raw-byte figures reproduce from the recording; digests only, no content.
4. Recorded `repo_commit` is the task 1 commit (97ded664), not the final HEAD: it contains every blob the recording depends on, and the recording cannot name a commit that contains itself.

## Known Stubs

None.

## Threat surface

No new surface: read-only on the live tree, digests and relative paths only in the recording (`~/` prefix).

## Notes for later plans

- 04-03 reuses `evidence_current(raw, rendered)`, `render()`, `recordings()` in `tools/test_skill_drift.py`; the card half should append to `render()` and `CLAUSES`.
- Laptop-plane `--live` run is an Owner-bundle `[H]` item (04-04). The recorded repo_commit must exist in the laptop clone for V-SKD-RECORD-REPRODUCES there (it is INCONCLUSIVE, never ok, otherwise).

## Self-Check: PASSED
Files exist (tools/skill_mirror_drift.py, tools/test_skill_drift.py, evidence/H-live-gex44.json, evidence/H-drift.md); commits 97ded664 and a94256e6 present on the branch; gate 9/9.
