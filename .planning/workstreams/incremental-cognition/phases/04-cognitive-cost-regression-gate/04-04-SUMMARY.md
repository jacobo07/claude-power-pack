---
phase: 04-cognitive-cost-regression-gate
plan: 04
subsystem: floor-regression-gate
tags: [pillar-K, IC-K, owner-bundle, laptop-reference, evidence, liveness-disposition]
requires: ["04-01", "04-02", "04-03"]
provides:
  - "vault/programs/incremental-cognition/owner-bundle.md: `## Phase 4 -- floor reference (laptop plane)` section with the `[K]` item (fetch + cherry-pick of the eight K code commits, fixture suite, seeded positive control, option A probe / option B champion session, pathspec commit, PRG that closes K)"
  - "tools/test_floor_regression_gate.py: V-FLOOR-BUNDLE-ARGV-PARSES, build_test_parser, bundle_section, bundle_argv_report"
  - "vault/programs/incremental-cognition/evidence/K.md: pillar K evidence, Status OPEN"
affects: []
tech-stack:
  added: []
  patterns: ["a documented command is a claim with an exit code: every indented command line of the [K] item is split and parsed by the tool's own argparse, with a bad-bundle and a good-bundle control so the checker can fail"]
key-files:
  created: [vault/programs/incremental-cognition/evidence/K.md]
  modified: [tools/test_floor_regression_gate.py, vault/programs/incremental-cognition/owner-bundle.md]
decisions:
  - "Pillar K stays OPEN: ledger state.K is {}, IC-K is not ticked, `--pillar K` still reports `FAIL L3 K: no terminal disposition`; the frozen rule's reference is the laptop one"
  - "No registry entry and no baseline_ledger axis: tools/ is outside the liveness scanner's aperture (registry keys are module units), and baseline_ledger's ledger is under ~/.claude (HR-001)"
  - "The R2-W1 pin (reference-gex44.json window_sha256 dc6d23b90cac..., window_rows 34, pinned to transcript 34f03871) and the gate that re-derives it (V-FLOOR-REAL-REFERENCE-PINNED) are named in evidence/K.md"
status: complete
commits: 2
plan_head_before: 2ceae072374484577a226961be2a27ec71c753b8
actuals:
  tokens: 7200
  tasks: 2
  commits: 2
metrics:
  completed: 2026-10-04
requirements: [IC-K]
requirements-completed: []
---

# Phase 4 Plan 04: the [K] owner-bundle item and pillar K evidence Summary

The Owner now has one parse-proven bundle item (`[K]`) that turns the GEX44-built floor gate into the laptop-plane terminal for pillar K, and `evidence/K.md` records everything the gate was measured to do. **IC-K is addressed, not satisfied**: ledger `state.K` prints `{}`, IC-K is unticked, `--pillar K` still exits 1 with `FAIL L3 K: no terminal disposition`, and `evidence/K.md` ends `## Status: OPEN`.

**Commits:** `d40bd16c` (Task 1, tracer: bundle item + `V-FLOOR-BUNDLE-ARGV-PARSES`), `7f2cdf64` (Task 2: `evidence/K.md`).

## Observed results

- `python3 tools/test_floor_regression_gate.py` -> `FLOOR_PASS=60/60  threshold=60/60  skipped=0  inconclusive=0`, exit 0 (was 59/59 at dispatch). `PASS V-FLOOR-BUNDLE-ARGV-PARSES 6 gate lines and 2 test lines of the Phase 4 [K] item parse with their own argparse (controls: bad bundle raises 3 problems, good bundle none)`.
- `python3 tools/test_floor_regression_gate.py --drill` -> `PASS DRILL-CONTROL 50/50 (skipped 0)`, 13 `KILLED`, `DRILL killed=13/13`, `PASS DRILL-RESTORE gate file sha256 775574882200de2e before == after`.
- `python3 tools/test_incremental_cognition_program.py --pillar K` -> exit 1, `FAIL L3 K: no terminal disposition`; `--selftest` -> exit 0 (`CEP_SELFTEST=PASS`, `ICP_SELFTEST=PASS`). `state.K` -> `{}`; `grep -c '\[x\] \*\*IC-K\*\*' REQUIREMENTS.md` -> `0`.
- Bundle acceptance: `grep -c '^- \*\*\[K\]\*\*'` -> `1`; `grep -c 'NOT RUNNABLE HERE'` -> `2`; the pinned diff `d40bd16c^..d40bd16c` of owner-bundle.md has 0 removed lines (append only); `git cat-file -t` prints `commit` for all 8 cherry-pick shas (`7fdef637`, `e4459393`, `8422eb2d`, `13f3bffe`, `11686c8d`, `f065ac8e`, `17228d2f`, `09bb9142`, taken from `git log --reverse` on the three K artifacts before the bundle commit).
- evidence/K.md acceptance: one each of `## Product Delta`, `## Intelligence Delta`, `## Status: OPEN`; the frozen rule is byte-equal to the ledger's text; the three LF sha256 values match a fresh run (gate `775574882200de2e...`, test `4f7b094b7282425a...`, reference-gex44 `4d88fe83a164ecd0...`); `git diff --name-only 73d546152cc6edc7e9fe223ec49acf70de08c734..HEAD -- modules hooks commands agents SKILL.md CLAUDE.md vault/liveness` printed nothing; `git show --stat 7f2cdf64` lists only `evidence/K.md`.
- Fresh GEX44 within-bound check (interactive session against the plane-gex44 reference): `FLOOR verdict=WITHIN_BOUND exit=0 reason=within_bound`. Default-reference check: `FLOOR verdict=UNMEASURABLE exit=2 reason=reference_missing`.
- Liveness today, plane gex44: `modules: 490 | REACHABLE: 310 | ORPHAN: 180 | UNKNOWN: 0 | gate offenders: 64`, exit 1; all 64 pre-existing, none from this phase.

## RED output (Task 1, before the section existed)

```
FAIL V-FLOOR-BUNDLE-ARGV-PARSES no `## Phase 4` section; the Phase 4 section holds 0 gate lines and 0 test lines; needs at least 6 and 2; exactly one `- **[K]**` item is required
FLOOR_PASS=59/60  threshold=60/60  skipped=0  inconclusive=0
```

## Deviations from Plan

**1. [Plan interpretation] `build_test_parser`** - the test file read `sys.argv` inline (no parser existed), so I added `build_test_parser()` declaring the three flags the module already honours (`--drill`, `--gate-path`, `--real-session`); the existing inline `sys.argv` handling is unchanged. The docstring gained the `--real-session` usage line.

**2. [Rule 2 - integrity] extra gate checks** - `V-FLOOR-BUNDLE-ARGV-PARSES` also fails on a `<` or `>` token in any command line (a placeholder is shell redirection) and on anything other than exactly one `- **[K]**` item, and carries a bad-bundle control (unknown gate flag, unknown test flag, placeholder -> 3 problems) and a good-bundle control, so the checker is shown able to fail.

**3. [Honesty] hedged SKIP expectation** - the plan said the laptop's probe-stub and read-only gates SKIP on Windows. The test file skips `chmod`, script-as-argv[0] and file-mode gates on nt (lines `SKIP ... on nt`); which gates those are was read from the source, not run on the laptop, so the bundle and K.md word it "expected, not measured".

**4. [Evidence wording] one Intelligence Delta bullet dropped** - a draft bullet about total-versus-row masking was not supported by a measured number and was removed before commit.

**5. [Trailer]** commits end with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` (the session's attribution reminder), as in 04-02 and 04-03, rather than the dispatch's Opus 5.5 line.

**6. [Tooling note]** the PreToolUse hook repeatedly advised using `& 'C:\Program Files\Git\cmd\git.exe'` (a Windows PowerShell trap); this host is Linux bash, so plain `git` was used throughout.

## Known Stubs

None. The laptop commands in the bundle are documented and parse-proven, not stubs; the bundle states they are NOT RUNNABLE HERE and have not been run.

## Threat Flags

None. T-04-04-01 (unrunnable laptop command): all 6 gate and 2 test lines parse with their own argparse, shas resolve, status sentence says NOT RUNNABLE HERE. T-04-04-02: option A is labelled one headless session, spends quota, Owner decision; option B costs none. T-04-04-03: Status OPEN, `--pillar K` red, `state.K` `{}`, IC-K unticked. T-04-04-04: append only (0 removed lines). T-04-04-05: K.md quotes gate output only. No real `claude` session was started; nothing was written under `~/.claude`.

## Self-Check: PASSED

- `evidence/K.md`, the bundle `## Phase 4` section and `V-FLOOR-BUNDLE-ARGV-PARSES` exist; commits `d40bd16c` and `7f2cdf64` are on `mission/incremental-cognition-run`; `git rev-list --count 2ceae072374484577a226961be2a27ec71c753b8..HEAD` = 2 before this SUMMARY commit.
- `FLOOR_PASS=60/60` and `DRILL killed=13/13` observed after the last code commit.
