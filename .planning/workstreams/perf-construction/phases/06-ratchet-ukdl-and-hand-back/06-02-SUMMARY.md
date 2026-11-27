---
phase: 06-ratchet-ukdl-and-hand-back
plan: 02
subsystem: ratchet-connection
tags: [perf-construction, tower-ratchet, ukdl-candidates, scratch-root, PERF-06]
requires:
  - phase: 06-01
    provides: inheritance map and mutant matrix records (negative controls and reuse pointers)
provides:
  - ratchet_connect.py: phase-local connector to the real Tower ratchet owner on a scratch root (selftest 12/12)
  - ratchet-entries.json: five proposed entries, evidence derived from existing records
  - RATCHET_STATUS=CONNECTED_SCRATCH LIVE=BLOCKED (4 of 5 promotable under an Owner authority)
  - vault/tower/candidates/perf_construction.md (Tower candidate note, Owner promotion steps)
  - vault/knowledge_base/candidates/perf-construction-20261123.md (append-only UKDL candidates)
  - ukdl_candidate_check.py: shape and pointer checker (selftest 10/10, check 5/5)
affects: [06-03]
tech-stack:
  added: []
  patterns: [scratch generation root with realpath refusal, evidence derived not typed, ownership sweep before drafting]
key-files:
  created:
    - .planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/ratchet_connect.py
    - .planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/ratchet-entries.json
    - .planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/ukdl_candidate_check.py
    - .planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/records/06-02-T1.selftest.txt
    - .planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/records/06-02-T2.connect.txt
    - .planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/records/06-02-T2.classify.txt
    - .planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/records/06-02-T3.ukdl.txt
    - vault/tower/candidates/perf_construction.md
    - vault/knowledge_base/candidates/perf-construction-20261123.md
  modified: []
decisions:
  - "No live promotion: a live generation needs an Owner authority and a perf_construction family file; both are the Owner's (OWNER DECISION NEEDED 12)."
  - "UKDL candidates stay in a new append-only file; none promoted into the aggregates (OWNER DECISION NEEDED 13)."
status: complete
commits: 3
plan_head_before: 1e5cd138521bfc1e1026a8fb3e6cd9489d6cec08
actuals:
  tokens: 19000
  tasks: 3
  commits: 3
requirements-completed: [PERF-06]
---

# Phase 6 Plan 02: Ratchet connection and UKDL candidates Summary

The campaign's five proposed baseline entries were run through the real Tower ratchet owner on a scratch root: `RATCHET_STATUS=CONNECTED_SCRATCH LIVE=BLOCKED`, 4 of 5 promotable under an Owner authority, and the six-family classifier reaches none of this work (`CLASSIFY_NO_FAMILY=4/4`, control reaches `web_surface`).

## What was done

- **Task 1 (tracer, 2be8486c).** `ratchet_connect.py` calls `modules.tower.ratchet.promote_with_evidence`, `verify_chain`, `baselines.locate_quote`/`verify_origin` and `checks.evaluate` against a `mkdtemp` scratch root that is refused (exit 2) when its realpath equals or lies inside `vault/tower/baselines`. Selftest 12/12 (`records/06-02-T1.selftest.txt`) drives the owner's own refusals (no negative control, reuse run equal to the improving run, empty authority, scratch authority naming the Owner), a tamper and a regression on a synthetic fixture, a mutant control that patches `evidence_problems`, and a check that the live tree is untouched.
- **Task 2 (090f779e).** Five entries (`ratchet-entries.json`); origin line numbers come from `locate_quote`; improvement, negative-control and reuse values are read from existing phase records by regex and re-derived on each `connect`. Result: four reach a scratch chain (generations=4, chain_ok=True); `perf_construction-laptop-claim-carries-its-plane` is NOT_PROMOTABLE with the missing parts named (improvement, negative_controls). `classify` re-measured: 0 of 4 prompts reach a family, control reaches `web_surface`.
- **Task 3 (43193734).** Tower candidate note with the five entries, status and the two Owner promotion steps; UKDL candidates file with five blocks, checked by `ukdl_candidate_check.py` (`UKDL_SELFTEST=10/10`, `UKDL_CHECK=5/5`).

## UKDL candidate outcome (ownership sweep first)

Sweep: three aggregates plus `vault/knowledge_base/*.md` (48 files), then `--wide` (576 files).

| Candidate | Outcome |
|-----------|---------|
| (a) failed sample stays in the denominator | NEW (0 hits on every term); drafted as `PR-FAILED-SAMPLE-STAYS-IN-THE-DENOMINATOR-001` |
| (b) unknown host state leaves the window | EXTEND_EXISTING_OWNER (session_resilience_05 "unknown is not green") |
| (c) censored duration is not zero | EXTEND_EXISTING_OWNER (`real-context-reachability` skill, "Absent is not zero") |
| (e) proof inherited by convention | EXTEND_EXISTING_OWNER (`HR-INTENT-FIDELITY-IS-DONE-CRITERION-001`) |
| (f) host plane number never fills the laptop one | EXTEND_EXISTING_OWNER (`develop-here-prove-there` skill) |
| (d) unchanged gate text is NOT_SHOWN | DROPPED from the UKDL file: no measured cost (an executor interpretation, `05-02-SUMMARY.md:85`); kept only as a Tower entry |

No HR candidate was drafted. Nothing was promoted into any aggregate.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Two unsupported claims in the candidate files, corrected before commit**
- **Found during:** Task 3 pointer verification (every cited line was re-read after drafting)
- **Issue:** one block cited "9 of 64 declared criteria" for `HR-INTENT-FIDELITY-IS-DONE-CRITERION-001`, which its text does not say; and the dropped candidate (d) and the Tower note said the text-drift case "did not occur in the real pair", which `05-02-SUMMARY.md:85` does not state.
- **Fix:** replaced with what the sources say (58 gate surfaces, 38 FUNCTIONAL_ONLY; an executor interpretation of a gap in G4, no real drifting pair recorded).
- **Files modified:** `vault/knowledge_base/candidates/perf-construction-20261123.md`, `vault/tower/candidates/perf_construction.md` (both before their first commit)
- **Commit:** 43193734

**2. [Rule 3 - Blocking] Plan verify grep used a backreference ugrep rejects**
- Re-ran with `/usr/bin/grep -E`; passes (`RATCHET_SELFTEST=12/12`).

### Additions beyond the plan (internal, reversible)

- `ukdl_candidate_check.py` also has a `sweep [--wide] TERM...` subcommand, so the ownership sweep is a recorded, repeatable instrument rather than a scratch script.
- No separately committed RED record for Task 1: the selftest passed on its first run; the in-file mutant control (patched `evidence_problems` accepts what the owner refuses) carries the RED shape.

## Known limits

- `ukdl_candidate_check.py` validates shape and that a pointer's path exists; it does not verify that a cited line number says what the block claims. Line pointers were re-read by hand once (deviation 1 came from that); the check does not enforce it.
- The "improvement" values are pass counts of each mechanism's own gate suite before and after the fix, not creation-speed changes. Creation speed on the laptop is UNKNOWN. Zero laptop-judged items in this plan.
- Whether anything schedules the `bench-gate` row is UNKNOWN (from 06-01).

## OWNER DECISIONS NEEDED

- (12) Create `vault/tower/families/perf_construction.json` and make a live B0 under an Owner authority? Pick (unattended, reversible): no; scratch only. Reversal: the two commands in `vault/tower/candidates/perf_construction.md`, "To promote (Owner)".
- (13) Promote any of the five UKDL candidates into `ukdl-universal.md`? Pick: no; they stay in the append-only candidates file.

## Known Stubs

None.

## Threat Flags

None. No network endpoint, auth path or trust-boundary schema was added; the scratch root is refused when it resolves into live ratchet state, and `vault/tower/baselines`, `vault/tower/families`, the aggregates, `hooks/`, `governance/` and `wiki/` show no change (git status empty for each).

## Self-Check: PASSED

- All nine created files exist (checked with `git diff --stat` against `plan_head_before`: 9 files, 1317 insertions).
- Commits 2be8486c, 090f779e, 43193734 exist; `commits: 3` measured with `git rev-list --count` from the ledger base.
- Re-runs: `RATCHET_SELFTEST=12/12`, `UKDL_SELFTEST=10/10`, `UKDL_CHECK=5/5`.
