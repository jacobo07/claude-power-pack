---
phase: 06-consume-owners-and-close
plan: 01
subsystem: testing
tags: [r2, owner-ledger, done-gate, read-only-helper, mutation-drill, python]
status: complete

requires:
  - phase: 05-kme-replay
    provides: the program done-gate wrapper tools/test_incremental_cognition_program.py (R2-R4) this plan extends
provides:
  - tools/ic_r2_evidence.py: read-only R2 evidence printer for consuming pillars J and M
  - tools/test_ic_r2_evidence.py: 12 V-ICR2-* gates and a 6-mutant drill
  - "`--pillar <P>` now executes R2 for P (check_consumed only=, load_ledger)"
affects: [06-02 owner bundle [J]/[M] items, 06-04 close-out]

actuals:
  tokens: 8000      # chars/4 over the realized diff (28337 chars in the two new files + ~3500 chars net in the wrapper)
  tasks: 3
  commits: 3        # MEASURED: git rev-list --count 594745b6..HEAD
plan_head_before: 594745b687ef1de80a7dba8608ffb73cede44056
commits: 3

tech-stack:
  added: []
  patterns:
    - "helper reads the other program's ledger through the SAME reader the done-gate uses (icp.OwnerLedgers), so the printed terminal is the one R2 will read"
    - "rows are printed only when every consumed pillar is READY at a reachable commit, and only after a round trip through icp.check_consumed"
    - "the ce.REPO rebinding seam lives only in the test (bound_repo) and is proven restored"

key-files:
  created: [tools/ic_r2_evidence.py, tools/test_ic_r2_evidence.py]
  modified: [tools/test_incremental_cognition_program.py]

key-decisions:
  - "J and M are addressed, NOT satisfied: no state.<P> terminal written, IC-J / IC-M not ticked, requirements.mark-complete not called (R2 externally blocked: CE and SC ledgers carry no terminal on this line of history)"
  - "`--pillar X` runs R2 for X because the owner bundle will name that command and CE clause L4 accepts any owner_ledger row without reading it"
  - "the helper never rebinds a REPO global; scratch-git gates rebind ce.REPO in the test only"

requirements-completed: []   # IC-J and IC-M are addressed here, not satisfied (06-CONTEXT decision J/M)

coverage:
  - id: D1
    description: "ic_r2_evidence.py prints, on the real repo, which owner pillars block J and M at a commit, and never prints a row while any is open"
    requirement: "IC-J"
    verification:
      - kind: integration
        ref: "python3 tools/test_ic_r2_evidence.py (V-ICR2-TRACER-REAL-HEAD, -REAL-FREEZE-POLE, -REAL-UNREADABLE-POLE, -PARTIAL-NO-PASTE)"
        status: pass
    human_judgment: false
  - id: D2
    description: "printed rows pass R2 as pasted and every safety property can be driven red"
    requirement: "IC-M"
    verification:
      - kind: integration
        ref: "python3 tools/test_ic_r2_evidence.py --drill (killed=6/6, control green before and after)"
        status: pass
    human_judgment: false
  - id: D3
    description: "--pillar <P> executes R2 for P; today's done-gate verdicts unchanged"
    requirement: "IC-J"
    verification:
      - kind: unit
        ref: "python3 tools/test_incremental_cognition_program.py --selftest (V-ICP-R2-ONLY-SCOPED, V-ICP-R2-PILLAR-MODE, V-ICP-MUT-r2-absent-from-pillar-mode)"
        status: pass
    human_judgment: false

duration: 25min
completed: 2026-10-04
---

# Phase 6 Plan 01: R2 evidence printer and R2-in-`--pillar` Summary

**Read-only `ic_r2_evidence.py` that prints R2 `owner_ledger` rows for J/M only when every consumed CE pillar is closed at a reachable commit, plus `--pillar <P>` now running R2 so the per-pillar done-gate reads the owner ledger.**

## Performance

- **Tasks:** 3 of 3
- **Files:** 2 created, 1 modified
- **Commits:** 3 (measured, `594745b6..HEAD`)

## Accomplishments

- `python3 tools/ic_r2_evidence.py --pillar J --commit HEAD` discovers CE D, E, I from `frozen.consumes.J`, reads the CE ledger at the commit through `icp.OwnerLedgers`, prints one `OPEN ... no terminal (owner predicted MERGED_INTO_EXISTING_OWNER)` line per pillar, ends `ICR2_READY=NO pillar=J commit=<40 hex> open=['D', 'E', 'I']`, exit 1. `--pillar M` does the same for Q, N, O, M (M's owner predicted `DEFERRED_STRONGER_OWNER`, shown). `--pillar A` and an unresolvable commit exit 2 `ICR2_COULD_NOT_RUN`.
- On scratch git: closed owner -> JSON array of `{kind, ref, commit(40 hex), pillar, terminal}` rows in `frozen.consumes` order, `NEEDS` lines derived from `ce.REQUIRED_KINDS`, `ICR2_READY=J commit=<40 hex>`, exit 0. Partial closure, side-branch commit and unreadable ledger print no row.
- The wrapper defect is fixed: `--pillar` previously ran only R3 and R4, so a J terminal with a misquoted owner terminal printed `ICP_PILLAR_J=PASS`. It now runs `check_consumed(led, OwnerLedgers(), only=[pid])`.

## Task Commits

| Task | Commit | Subject |
| ---- | ------ | ------- |
| 1 (tracer) | 143eaca5 | feat(06-01): R2 evidence printer -- reads the owner ledger at a commit, prints owner_ledger rows only when every consumed pillar is closed (J, M) |
| 2 | 6ebccec7 | test(06-01): R2 printer -- closed, partial and unreachable poles on scratch git, round trip through check_consumed, drill 6/6 |
| 3 | f0d16652 | fix(06-01): --pillar runs R2 for its pillar -- the per-pillar check the owner bundle names now reads the owner ledger (J, M) |

## Verification (observed output)

RED before the build (Task 1): `python3 tools/test_ic_r2_evidence.py` -> `ModuleNotFoundError: No module named 'ic_r2_evidence'`, rc 1.

- `python3 tools/test_ic_r2_evidence.py` -> `ICR2_PASS=12/12  threshold=12/12  skipped=0  inconclusive=0`
- `python3 tools/test_ic_r2_evidence.py --drill` -> `PASS DRILL-CONTROL (11/11)`, `KILLED M1..M6` (each by its named gate), `PASS DRILL-CLEAN-AFTER-MUTANTS (11/11)`, `DRILL killed=6/6`
- `python3 tools/test_incremental_cognition_program.py --selftest` -> rc 0, 107 `ok` lines (104 before + 3), `ICP_SELFTEST=PASS`, with `ok   V-ICP-R2-ONLY-SCOPED`, `ok   V-ICP-R2-PILLAR-MODE`, `ok   V-ICP-MUT-r2-absent-from-pillar-mode killed by V-ICP-R2-PILLAR-MODE`
- `--pillar A..N` and `--final` outputs (stdout+stderr+rc) captured before and after Task 3: `diff -r /tmp/ic-p6-01-t3-before /tmp/ic-p6-01-t3-after` printed nothing
- `KMEP_PASS=89/89`, `KMER_PASS=45/45`, `FLOOR_PASS=67/67`
- Helper commands on HEAD 594745b6: `--pillar J` rc 1 (OPEN D, E, I; ICR2_READY=NO), `--pillar M` rc 1 (OPEN Q, N, O, M), `--pillar A` rc 2, `--commit zzzz` rc 2
- Protected paths: none of this plan's 3 commits touches the CE / SC verifiers, either owner ledger or the program ledger; `git diff HEAD` over those paths is empty (`own 3 touching protected []`)
- `ast` count of `REPO` assignments in the helper = 0; `grep -c setattr tools/ic_r2_evidence.py` = 0

## Deviations from Plan

None to scope. Implementation notes:

- `main` runs the round trip BEFORE printing any line (the plan said "before printing a ready result"), so a row set that fails R2 prints nothing but `ICR2_COULD_NOT_RUN rows fail R2: ...`.
- Test-only fixes found while building: the in-process runner catches `SystemExit` (argparse refusing `--commit -x` is a refusal, not a crash; the bad-commit gate passes `--commit=<spec>` so the helper's own guard is reached), and the rows parser ends at the JSON array's closing bracket because `NEEDS` lines follow it. An intermediate drill run showed M3 and M5 "killed" while the control was red; fixed and re-run so every kill is against a green control.

## Known Stubs

None.

## Threat Flags

None. The helper reads ledgers and git objects and prints ledger paths, pillar ids, terminals and shas only.

## Hard prohibitions honoured

No `state.<P>` ledger write, IC-J / IC-M not ticked, `requirements.mark-complete` not called, no edit to the CE / SC verifiers or any ledger, no abbreviated commit in a printed row, no partial paste.

## Self-Check: PASSED

- FOUND: tools/ic_r2_evidence.py, tools/test_ic_r2_evidence.py, tools/test_incremental_cognition_program.py
- FOUND commits: 143eaca5, 6ebccec7, f0d16652 (all in `git log`)
