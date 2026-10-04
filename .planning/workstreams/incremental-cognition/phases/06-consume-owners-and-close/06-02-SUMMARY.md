---
phase: 06-consume-owners-and-close
plan: 02
subsystem: testing
tags: [r2, owner-bundle, evidence, coverage-by-construction, python]
status: complete

requires:
  - phase: 06-consume-owners-and-close
    provides: tools/ic_r2_evidence.py and R2 inside --pillar (plan 06-01)
provides:
  - "vault/programs/incremental-cognition/evidence/JM-blocked.md: J and M R2 inputs, measured blocker, Status OPEN"
  - "owner bundle [J] and [M] items (Phase 6 section) with summary rows 29 and 30"
  - "V-ICR2-BUNDLE-ARGV-PARSES and V-ICR2-JM-BLOCKED-COVERS"
  - "pending-check discovery over every phase directory NN-*"
affects: [06-03, 06-04 close-out]

actuals:
  tokens: 14000     # chars/4 over the realized diff (~55 KB across the evidence file, bundle lines and two test files)
  tasks: 2
  commits: 2        # MEASURED: git rev-list --count 4315379f..HEAD at SUMMARY write
plan_head_before: 4315379f15b3a5b06dfac13a8faceefc793e4b2f
commits: 2

tech-stack:
  added: []
  patterns:
    - "bundle commands are parsed by the printer's own build_parser, filed under their own item, and each paired with the per-pillar check"
    - "evidence coverage is read from the ledger's frozen.consumes, never from a list in the test"
    - "pending-check discovery globs every phase directory, with an in-gate control on a synthetic 06-* directory"

key-files:
  created: [vault/programs/incremental-cognition/evidence/JM-blocked.md]
  modified: [vault/programs/incremental-cognition/owner-bundle.md, tools/test_ic_r2_evidence.py, tools/test_kme_replay.py]

key-decisions:
  - "J and M are addressed, NOT satisfied: no state.J / state.M, no handoffs/J.md or M.md, IC-J / IC-M not ticked, requirements.mark-complete not called"
  - "the program plan's drafting note about CE's branch is quoted as a laptop-side statement, not as a measurement of this host"

requirements-completed: []   # IC-J and IC-M are addressed here, not satisfied (R2 externally blocked)

duration: 35min
completed: 2026-10-04
---

# Phase 6 Plan 02: J and M evidence and bundle items Summary

**`evidence/JM-blocked.md` names every R2 input of J (CE D, E, I) and M (CE Q, N, O, M) with the measured `ICR2_READY=NO` outputs, the owner bundle gains runnable `[J]` and `[M]` items (rows 29-30), and the pending-check discovery now covers every phase directory.**

## Accomplishments

- `JM-blocked.md`: frozen rules verbatim, the table of consumed (ledger, pillar, name, owner prediction, terminal at HEAD) read from `frozen.consumes` and the CE ledger, the closing shape of `state.J` / `state.M` from the printer's `NEEDS` lines, every measured command with output and exit code, why it is external (the program plan's drafting note quoted and labelled laptop-side), what closes it, an appendix with the printer's H and I outputs, Product / Intelligence Delta, Named debts, `## Status: OPEN`.
- Owner bundle: `## Phase 6 -- consumed owners (R2) and closeout` with `[J]` and `[M]`, each two indented commands (`python3 tools/ic_r2_evidence.py --pillar <P> --commit HEAD`, `python3 tools/test_incremental_cognition_program.py --pillar <P>`), summary rows 29 and 30 whose command cells equal those lines, and one paragraph noting rows from 29 on and the widened discovery. Insert only.
- `V-ICR2-BUNDLE-ARGV-PARSES` (6 in-gate controls) and `V-ICR2-JM-BLOCKED-COVERS` (4 in-gate controls).
- `uat_keys` globs `[0-9][0-9]-*`; control `a phase 06 directory is discovered` (SUMMARY-UAT now reports 10 controls).

## Task Commits

| Task | Commit | Subject |
| ---- | ------ | ------- |
| 1 (tracer) | a17ddd68 | docs(incremental-cognition): J -- R2 blocked on this host (evidence/JM-blocked.md), [J] bundle item with the printer and the per-pillar check, summary row 29 (06-02) |
| 2 | 017c09b3 | docs(incremental-cognition): M -- R2 inputs and [M] item (row 30); H / I appendix; pending-check discovery over every phase directory (06-02) |

## Verification (observed output)

RED before Task 1 (REQUIRED_JM = (J,)): `python3 tools/test_ic_r2_evidence.py` rc 1, `FAIL V-ICR2-BUNDLE-ARGV-PARSES printer lines for [] (required ['J'])`, `FAIL V-ICR2-JM-BLOCKED-COVERS ... JM-blocked.md does not exist`, `ICR2_PASS=12/14`.

RED before Task 2 (REQUIRED_JM = (J, M), control added): `ICR2_PASS=12/14` (BUNDLE-ARGV-PARSES `printer lines for ['J'] (required ['J', 'M'])`; JM-BLOCKED-COVERS `M: input ...#Q not named`, ...); `python3 tools/test_kme_replay.py` rc 1, `FAIL V-KMER-BUNDLE-SUMMARY-UAT controls failed: ['a phase 06 directory is discovered']`, `KMER_PASS=44/45`.

GREEN after Task 2:

- `python3 tools/test_ic_r2_evidence.py` -> rc 0, `ICR2_PASS=14/14`; `--drill` -> `DRILL killed=6/6`
- `python3 tools/test_kme_replay.py` -> `KMER_PASS=45/45`; SUMMARY-ITEMS `22 item key(s) incl. sync (>= 19), 30 row(s)`; SUMMARY-UAT `14 pending UAT key(s) ... 1 VER key(s) ... 10 controls report`; `--drill` -> `DRILL killed=19/19`
- `python3 tools/test_incremental_cognition_program.py --selftest` -> `ICP_SELFTEST=PASS`
- `KMEP_PASS=89/89`, `FLOOR_PASS=67/67`
- region-scoped globs in `uat_keys`: `['[0-9][0-9]-*', '*-UAT.md', '*-VERIFICATION.md']`
- owner bundle insert-only: `git diff --numstat 23979ec2 HEAD -- owner-bundle.md` -> `45 0`; per commit `24 0` (Task 1) and `21 0` (Task 2)
- `--pillar J` and `--pillar M` -> rc 1, `FAIL L3 <P>: no terminal disposition`; ledger `state.J`, `state.M` print `{} {}`; `handoffs/` lists only `ce-verifier-defect.md`; `grep -c '\[x\] \*\*IC-[JM]\*\*' REQUIREMENTS.md` -> 0
- Measured in this plan: `python3 tools/ic_r2_evidence.py --pillar J|M --commit HEAD` -> `ICR2_READY=NO` (open D,E,I / Q,N,O,M); `git cat-file -t 21671d6c` -> `fatal: Not a valid object name`; neither owner ledger has a terminal at HEAD or `origin/mission/skill-capability`; no CE ledger on `origin/feature/knowledge-acquisition`

## Deviations from Plan

- The plan's read-first said `tools/test_kme_replay.py` has `g_summary_uat` controls at 9 today; confirmed (10 after). No scope deviation.
- The duplicate-status slip (an old `## Status: OPEN` left under the new one after the Task 2 extension) was caught by `grep -n '^## '` before the commit and removed; only one Status section was committed.

## Known Stubs

None.

## Threat Flags

None. Reads ledgers and git objects; writes docs and test gates only.

## Hard prohibitions honoured

No `state.J` / `state.M`, no handoffs, no `owner_ledger` row written anywhere a gate reads as evidence, IC-J / IC-M not ticked, `requirements.mark-complete` not called, no bundle line removed or changed, nothing under `~/.claude` written by the plan's work, no `claude` session started.

## Self-Check: PASSED

- FOUND: vault/programs/incremental-cognition/evidence/JM-blocked.md, owner-bundle.md Phase 6 section, tools/test_ic_r2_evidence.py, tools/test_kme_replay.py
- FOUND commits: a17ddd68, 017c09b3
