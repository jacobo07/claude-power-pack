---
phase: 01-baseline-integrity-repair
plan: 02
subsystem: tower-donegate
tags: [ucep, tower, donegate, h5, h6, red-green]
requires: []
provides:
  - "donegate.judge: test: checks UNJUDGED (test-not-run), counts/unjudged_tests/would_block_on_violated, NA_REASONS + NA_SHARE_CAP_PERCENT"
  - "tools/test_ucep_donegate_exits.py: 13-gate instrument for done-gate exits H5/H6"
affects: [01-03, 01-04, 01-05, phase-6-stop-judge]
key-files:
  created: [tools/test_ucep_donegate_exits.py]
  modified: [modules/tower/donegate.py, tools/test_tower_donegate.py]
decisions:
  - "Vocabulary and cap live as constants in donegate.py (no new module, no liveness entry); Phase 6 imports them from there (D-07)"
  - "Over the cap every valid claim is voided, not just the excess: choosing which claims are legitimate would be gameable"
metrics:
  duration: "about 30 minutes"
  completed: 2026-10-03
status: complete
commits: 2
plan_head_before: 33a01501a857838318874fbc7677e54e372de1b9
requirements: [UCEP-01]
actuals:
  tokens: 6300    # chars/4 over the changed files (donegate.py ~8.5k, new test ~16.5k, 2 lines in test_tower_donegate.py); the plan carried no estimate
  tasks: 2
  commits: 2
---

# Phase 1 Plan 2: Done-gate exits H5/H6 Summary

H5 (every entry declared N/A with free text) and H6 (an existing `test:` file that fails) no longer pass the done-gate: both give
`would_block` True, with machine-readable `unjudged_reason`s and UNJUDGED counted apart from VIOLATED.
`UCEP_DONEGATE_EXITS_PASS=13/13`, `TOWER_DONEGATE_PASS=10/10`, `TOWER_CHECKS_PASS=23/23`, `checks.py` byte-unchanged.

Commits (measured `git rev-list --count 33a01501..HEAD` = 2): `d0064ee7` (Task 1), `84e77499` (Task 2).

Status: COMPLETE. Production Reality: OBSERVED (real commands, real exit codes in this worktree; both RED runs recorded on the
unfixed module). The gate stays REPORT-ONLY: nothing here enforces, `would_block` states what enforcement would do.

## Environment notes

- No PowerShell tool in this executor session; all commands ran through Bash with the absolute Git for Windows exe and the
  absolute Python 3.12 interpreter (as 01-01 did). Python run directly, never under `timeout`.
- Pinned root verified: `C:/Users/User/.claude/skills/claude-power-pack/.claude/worktrees/ucep`, branch `ucep/mission`.
- Dirty-path SET before Task 1 (orchestrator-owned only): ` M .planning/workstreams/ucep/STATE.md`, `?? .gsd/`,
  `?? .planning/workstreams/ucep/milestone.lock`, `?? .planning/workstreams/ucep/state.json`.

## Task 1 (tracer): `test:` -> UNJUDGED

### RED run H6 (unfixed donegate.py)

`git rev-parse HEAD` = `33a01501a857838318874fbc7677e54e372de1b9` (donegate.py unchanged; test file new and uncommitted).
Command: `python tools/test_ucep_donegate_exits.py`.

```
V-UCEP donegate exit gates
  FAIL V-UCEP-H6-TEST-UNJUDGED                  {'row': {'entry_id': 'has-test', 'verdict': 'DELEGATED', 'check_outcome': 'DELEGATED', 'detail': 'test exists; run by the repo, not here', ... 'judged_under': 'ucep_dg_1/B0'}, 'unjudged_tests': None, 'counts': None, 'would_block': False, 'would_block_on_violated': None}
  PASS V-UCEP-H6-MISSING-TEST-STILL-VIOLATED    missing test file -> VIOLATED, not in unjudged_tests
  PASS V-UCEP-REGISTRY-STILL-DELEGATED          registry: with a registered verifier -> DELEGATED (the remap is test:-only)
  FAIL V-UCEP-REPORT-COUNTS                     {'counts': {}, 'sum': 0, 'entries': 5}
  PASS V-UCEP-H6-MARKER-CONTROL                 running the file by hand writes the marker (rc=1): the instrument can fire
  PASS V-UCEP-NO-EXEC-IMPORTS                   checks.py and donegate.py import/call no exec facility (AST scan)
  PASS V-UCEP-NO-EXEC-SCAN-CONTROL              scanner flags a fixture with one forbidden import and one os.system
  PASS V-UCEP-H6-NOT-EXECUTED                   marker absent after every judge() call (control: by-hand run writes it)

UCEP_DONEGATE_EXITS_PASS=6/8  threshold=8/8
rc=1
```

FAIL lines are exactly V-UCEP-H6-TEST-UNJUDGED and V-UCEP-REPORT-COUNTS, as the plan predicted. The H6 verdict is the real
exit: an existing, failing-by-construction test file is DELEGATED and `would_block` is False.

### GREEN (Task 1)

Implemented in `modules/tower/donegate.py` (checks.py untouched): `REASON_*` constants (`prose`, `empty`, `test-not-run`,
`na-no-reason`, `na-not-in-vocabulary`, `na-over-cap`, `unreadable`, `other`), the `test:`+DELEGATED -> UNJUDGED remap, a row
`unjudged_reason`, and report keys `counts`, `unjudged_tests`, `would_block_on_violated`; docstring verdict table updated.

| command | exit | result line |
|---|---|---|
| `python tools/test_ucep_donegate_exits.py` | 0 | `UCEP_DONEGATE_EXITS_PASS=8/8  threshold=8/8` |
| `python tools/test_tower_donegate.py` | 0 | `TOWER_DONEGATE_PASS=10/10  threshold=10/10` |
| `python tools/test_tower_checks.py` | 0 | `TOWER_CHECKS_PASS=23/23  threshold=23/23` |
| `git diff --quiet HEAD -- modules/tower/checks.py tools/test_tower_checks.py` | 0 | byte-unchanged |

Observed on the mixed family: `counts {'applied': 1, 'violated': 1, 'delegated': 1, 'not_applicable': 0, 'unjudged': 2,
'unjudged_tests': 1}`. Dirty-path SET after the runs = before (plus my own two files and this SUMMARY); the tests wrote
nothing outside their temp dirs (hermetic HOME, `root=<tmp>/gens`).

Acceptance greps: `"test-not-run"` matches in donegate.py (constant + docstring); no `import|from subprocess|runpy|importlib`
line. `git show --stat HEAD` lists exactly `modules/tower/donegate.py` and `tools/test_ucep_donegate_exits.py`.

Commit: `d0064ee7` `fix(01-02): donegate reports test: checks UNJUDGED (never run), counted apart from VIOLATED`.

## Task 2: N/A closed vocabulary + share cap

### RED run H5 (no vocabulary)

`git rev-parse HEAD` = `d0064ee704f5d923c9e1a2fd3fe89a72d1fe99f4` (Task-1 donegate.py; the 5 new gates appended, uncommitted).
Command: `python tools/test_ucep_donegate_exits.py`.

```
V-UCEP donegate exit gates
  PASS V-UCEP-H6-TEST-UNJUDGED ... PASS V-UCEP-H6-MISSING-TEST-STILL-VIOLATED ... PASS V-UCEP-REGISTRY-STILL-DELEGATED ...
  PASS V-UCEP-REPORT-COUNTS ... PASS V-UCEP-H6-MARKER-CONTROL ... PASS V-UCEP-NO-EXEC-IMPORTS ... PASS V-UCEP-NO-EXEC-SCAN-CONTROL
  FAIL V-UCEP-H5-FREE-TEXT                      {'verdicts': [('NOT_APPLICABLE', None)], 'would_block': False}
  FAIL V-UCEP-H5-OVER-CAP                       {'na_cap': None, 'na_over_cap': None, 'verdicts': [('NOT_APPLICABLE', None)], 'would_block': False}
  PASS V-UCEP-H5-WITHIN-CAP-CONTROL             3/10 valid-token N/A -> NOT_APPLICABLE, other 7 APPLIED_VERIFIED, would_block False (na_count=None na_cap=None)
  PASS V-UCEP-H5-TOKEN-WITH-NOTE-CONTROL        token plus note -> NOT_APPLICABLE; detail keeps both
  PASS V-UCEP-H5-NO-REASON                      blank reason -> UNJUDGED/na-no-reason
  PASS V-UCEP-H6-NOT-EXECUTED                   marker absent after every judge() call (control: by-hand run writes it)

UCEP_DONEGATE_EXITS_PASS=11/13  threshold=13/13
rc=1
```

FAIL lines are exactly V-UCEP-H5-FREE-TEXT and V-UCEP-H5-OVER-CAP. The H5 exit is real: all 10 entries declared N/A with the
text `n/a` give 10x NOT_APPLICABLE and `would_block` False.

(In the block above the PASS lines are abbreviated with `...` to save space; the FAIL lines, the PASS lines that matter for the
controls, the tally and rc are verbatim. Full raw output was kept under `C:\Users\User\.claude\jobs\300ac3a1\tmp\red_h5.txt`.)

### Implementation (`modules/tower/donegate.py`, D-04; values per D-07 discretion)

- `NA_REASONS` (12 kebab-case tokens, one per absent trait of ROADMAP Phase 2 criterion 1 plus two structural ones):
  `no-persistent-state`, `single-actor`, `no-bulk-operation`, `no-destructive-operation`, `not-distributed`,
  `no-external-effect`, `not-scheduled`, `no-money`, `single-policy-layer`, `no-user-interface`, `platform-not-targeted`,
  `superseded-by-entry`.
  Rationale: each token names a structural fact about the entry's subject that a reviewer can check; a reason that only
  defers the work is deliberately absent (a deferral is not non-applicability, and it is the excuse this mission exists to stop).
  A comment beside the tuple states this without quoting the phrase as a token.
- `NA_SHARE_CAP_PERCENT = 30`; allowed claims = `(30 * n) // 100` over the active entries, integer arithmetic. Rationale: a
  family that is mostly N/A is not being judged; 30% leaves room for a few genuine structural exclusions (the 15-17 entry real
  families allow 4-5) while an all-N/A family can never pass. A family under 4 entries admits no N/A, deliberately fail-closed
  (threat T-01-09, accepted; documented in the docstring).
- `parse_na_reason(reason) -> (token, note)`: split on the first `:`, match the stripped head against `NA_REASONS`, else
  `(None, text)`.
- `judge()`: blank reason -> UNJUDGED `na-no-reason`; no token -> UNJUDGED `na-not-in-vocabulary`; valid claims over the cap ->
  EVERY valid claim voided to UNJUDGED `na-over-cap` (detail `N/A share %d/%d over cap %d`; choosing which claims are
  legitimate would itself be gameable); otherwise NOT_APPLICABLE with detail `token` or `token: note`. Report adds `na_count`,
  `na_cap`, `na_over_cap`.
- `tools/test_tower_donegate.py`: exactly two hunks, the reason string only, to `platform-not-targeted: desktop-only admin tool`
  (`git diff HEAD~1 HEAD --stat` = 2 insertions, 2 deletions).

### GREEN (Task 2)

| command | exit | result line |
|---|---|---|
| `python tools/test_ucep_donegate_exits.py` | 0 | `UCEP_DONEGATE_EXITS_PASS=13/13  threshold=13/13` |
| `python tools/test_tower_donegate.py` | 0 | `TOWER_DONEGATE_PASS=10/10  threshold=10/10` |
| `python tools/test_tower_checks.py` | 0 | `TOWER_CHECKS_PASS=23/23  threshold=23/23` |
| `python tools/test_tower_select.py` (regression) | 0 | `TOWER_SELECT_PASS=15/15  threshold=15/15` |
| `python tools/test_tower_inheritance.py` (regression) | 0 | `TOWER_INHERITANCE_PASS=16/16  threshold=16/16` |
| `git diff --quiet HEAD -- modules/tower/checks.py tools/test_tower_checks.py` | 0 | byte-unchanged |

Within-cap control line: `V-UCEP-H5-WITHIN-CAP-CONTROL ... (na_count=3 na_cap=3)`: the gate does not refuse every N/A.

Dirty-path SET bracket around the Task 2 multi-test run. BEFORE (sorted `git status --porcelain`): `M STATE.md` (orchestrator),
`M modules/tower/donegate.py`, `M tools/test_ucep_donegate_exits.py` (this task's uncommitted edits), `?? .gsd/`,
`?? milestone.lock`, `?? 01-02-SUMMARY.md`, `?? state.json`. AFTER: the same set plus `M tools/test_tower_donegate.py` (the migrated
reason strings, made before the run). No path appeared that this plan did not write, so the tests left nothing in the tree.
The `cbr_probe.py` run was done after this bracket; `git status` after it showed the same set.

### Probe H5/H6 lines (secondary observation, not this plan's oracle)

`python wiki/tools/cbr_probe.py`, rc=0, P5 section:

```
control  real web_surface B0 vs empty repo: would_block=True {'UNJUDGED': 17}
H5 every entry declared N/A with reason 'n/a': would_block=True {'UNJUDGED': 17}
H6 test:<file> whose only test fails: verdict=UNJUDGED would_block=True
```

H5 `would_block=True` with all 17 UNJUDGED and H6 `verdict=UNJUDGED`, as expected. (The probe's P3 ratchet lines show
`ok=False` for H1/H2/H3b: that is the ratchet, owned by plans 01-03/01-04, and not touched here.)

Commit: `84e77499` `fix(01-02): donegate N/A needs a closed-vocabulary reason within a 30% share cap`
(`git show --stat`: donegate.py, test_tower_donegate.py, test_ucep_donegate_exits.py). `NA_SHARE_CAP_PERCENT = 30` appears once
in donegate.py. `git diff --name-status 33a01501..HEAD -- modules` shows only `M modules/tower/donegate.py`: no new module, so
no liveness entry.

## Deviations from Plan

### Auto-fixed Issues

None. Plan executed as written, with these notes (not rule-driven fixes):

1. **Commit subject scope.** The plan's subjects used `fix(ucep-01): ...`; the dispatcher required scope `(01-02)`, so the
   subjects are `fix(01-02): ...` (same wording after the scope).
2. **Gate order.** `V-UCEP-H6-NOT-EXECUTED` is evaluated last in the file (it reads a list filled after EVERY `judge()` call
   including the H5 gates), so the printed order differs from the plan's numbering. Gate names and count are as specified.
3. **Scanner is slightly wider than specified.** `_exec_findings` also flags `from os import system|popen|exec*|spawn*`; the
   fixture control still yields exactly 2 findings, and the real files yield none.
4. **New row/report keys on the no-baseline path.** `NO_BASELINE` reports carry zero `counts`, empty `unjudged_tests`, and
   `na_*` zeros so consumers never branch on a missing key. Existing keys are unchanged.

## Authentication gates

None.

## Known Stubs

None. No hardcoded filler value flows to any surface; `unjudged_reason` is None by design for non-UNJUDGED rows.

## Threat Flags

None: no new endpoint, auth path or file access. `judge()` still executes nothing; the AST scan pins that for `checks.py` and
`donegate.py` and has a positive control.

## Threat model dispositions

| ID | Disposition | Evidence |
|---|---|---|
| T-01-05 | mitigated | `NA_REASONS` + cap; `V-UCEP-H5-FREE-TEXT`, `V-UCEP-H5-OVER-CAP` RED then GREEN, within-cap control PASS both times |
| T-01-06 | mitigated | `V-UCEP-NO-EXEC-IMPORTS` with `V-UCEP-NO-EXEC-SCAN-CONTROL`; marker gate with by-hand control |
| T-01-07 | mitigated | `test-not-run` remap, `counts`, `would_block_on_violated`; `V-UCEP-H6-TEST-UNJUDGED` RED then GREEN |
| T-01-08 | mitigated | `git diff --quiet` exit 0 and `TOWER_CHECKS_PASS=23/23` |
| T-01-09 | accepted | n below 4 admits no N/A; documented in the module docstring |

## Self-Check: PASSED

- FOUND: `tools/test_ucep_donegate_exits.py`, `modules/tower/donegate.py`, `tools/test_tower_donegate.py`
- FOUND commits: `d0064ee7`, `84e77499` (`git log` subjects match their message files)
- `STATE.md` and `ROADMAP.md` were not edited or staged by this plan.
