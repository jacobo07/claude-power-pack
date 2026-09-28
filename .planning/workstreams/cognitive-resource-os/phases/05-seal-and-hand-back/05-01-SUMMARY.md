---
phase: 05-seal-and-hand-back
plan: 01
subsystem: infra
tags: [gsd, mission-workflow, evidence, seal-check, ukdl, resumption]

requires:
  - phase: 01-gate-verdict-on-the-big-host
    provides: CRO-01 gate/suite verdict (BLOCKED) and its EVIDENCE.md
  - phase: 02-gex44-observed-baseline
    provides: CRO-02 MEASURED verdict, by_entrypoint.py, laptop-figure relabel instruction
  - phase: 03-p3-pre-flight-p0
    provides: CRO-03 PASS verdict (claudeMdExcludes mechanism)
  - phase: 04-prefix-cache-miss-a-b
    provides: CRO-04 UNJUDGED verdict, 04-REVIEW.md (CR-01 open)
provides:
  - Read-only seal_check.py (content/hashes/preserve/status modes, 9-case selftest)
  - RESUMPTION.md carrying the GEX44 hand-back, sealed list, all four phase verdicts, open follow-ups, three ranked next actions, laptop figures relabelled by host
  - UKDL carrying the GEX44 run paragraph and six evidence-cited entries (all six gated WRITE), laptop figures relabelled by host
  - Phase 05 EVIDENCE.md (sections 0-5): pre-checks, per-phase inputs, RESUMPTION/UKDL change log, hand-back ancestor check, final status, CRO-05 line
affects: [laptop resume session, any future GEX44 workstream phase]

actuals:
  tokens: 20860
  tasks: 3
  commits: 4
plan_head_before: 9528d2d5b072b46313ef96a32c83131ae5193554

tech-stack:
  added: []
  patterns:
    - "Read-only checker fed git facts on stdin (never runs git itself), mirroring by_entrypoint.py's import-safety and selftest conventions"
    - "Evidence-cited knowledge entries: every new UKDL ID cites its phase EVIDENCE path and a resolvable commit, gated on downstream VERIFICATION/REVIEW status read at execution time"

key-files:
  created:
    - .planning/workstreams/cognitive-resource-os/phases/05-seal-and-hand-back/seal_check.py
    - .planning/workstreams/cognitive-resource-os/phases/05-seal-and-hand-back/EVIDENCE.md
  modified:
    - vault/plans/cognitive-resource-os-RESUMPTION.md
    - vault/knowledge_base/ukdl-cognitive-resource-os.md

key-decisions:
  - "Both Phase 4 gates (04-VERIFICATION status, 04-REVIEW CR-01 presence) read WRITE at execution time, so all six planned UKDL entries were written -- 14 total entry-ID lines (8 original + 6 new)."
  - "seal_check.py enforces (not just documents) the threat model: verdict-token equality against each phase's own EVIDENCE key line, figure-in-cited-file provenance, a closed UKDL ID set gated by re-derived gates, no lost word from the cd4e436 baseline, and a privacy/slop scan -- all five automated checks per task actually gate the commits, not just narrate them."

requirements-completed: [CRO-05]

coverage:
  - id: D1
    description: "seal_check.py: read-only checker with content/hashes/preserve/status modes and a 9-case selftest, fed every git fact on stdin"
    requirement: CRO-05
    verification:
      - kind: unit
        ref: "seal_check.py --selftest (SEALCHK_SELFTEST_PASS=9/9 threshold=9/9)"
        status: pass
      - kind: integration
        ref: "seal_check.py content --stage 1..4 / hashes --stage 1..2 / preserve res|ukdl --stage 1..2 / status"
        status: pass
    human_judgment: false
  - id: D2
    description: "RESUMPTION.md: GEX44 hand-back, sealed list, verdicts of phases 1-4, open follow-ups, three ranked next actions, laptop figures relabelled by host, no laptop fact lost"
    requirement: CRO-05
    verification:
      - kind: integration
        ref: "seal_check.py content --stage 2 and preserve res --stage 2 (both exit 0)"
        status: pass
    human_judgment: false
  - id: D3
    description: "UKDL: GEX44 verdict paragraph plus six evidence-cited, correctly gated entries; ukdl-universal.md untouched"
    requirement: CRO-05
    verification:
      - kind: integration
        ref: "seal_check.py content --stage 4 and preserve ukdl --stage 2 (both exit 0)"
        status: pass
    human_judgment: false
  - id: D4
    description: "All work committed on mission/cognitive-resource-os-gex44, which fast-forwards mission/cognitive-resource-os; final porcelain status is TRACKING_ONLY (STATE.md only, orchestrator-owned)"
    requirement: CRO-05
    verification:
      - kind: other
        ref: "git merge-base --is-ancestor mission/cognitive-resource-os HEAD (rc=0); seal_check.py status"
        status: pass
    human_judgment: false

duration: 25min
completed: 2026-09-28
status: complete
---

# Phase 05 Plan 01: Seal and hand back Summary

**Read-only seal_check.py plus a fully evidence-cited RESUMPTION/UKDL hand-back: all four phase verdicts, six gated UKDL entries, laptop figures relabelled by host, branch fast-forwards the mission line.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-09-28T15:16:22Z
- **Completed:** 2026-09-28T15:39:26Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- `seal_check.py`: a phase-local, read-only checker (content/hashes/preserve/status modes) that verifies verdict-token equality, EVIDENCE-path citation, figure provenance, UKDL gating, word preservation and a privacy/slop scan -- all fed git facts on stdin, never running git itself. 9-case TDD selftest (`SEALCHK_SELFTEST_PASS=9/9`).
- `RESUMPTION.md` complete: `1a` hand-back (worktree, branch, base, fast-forward + fetch commands), `2c` GEX44 sealed commit list, `2d` all four phase verdicts read from their own EVIDENCE, `2e` open follow-ups, `4` three ranked next actions, `4a` the superseded laptop actions kept verbatim. Every laptop figure now names the laptop; no original word lost.
- `ukdl-cognitive-resource-os.md`: a GEX44 run paragraph plus all six planned entries (both Phase 4 gates read WRITE at execution time), each citing its phase EVIDENCE path and a resolvable commit. `ukdl-universal.md` untouched.
- Phase 05 `EVIDENCE.md` sections 0-5: pre-checks, per-phase inputs (verdict lines, verification/review status, the two Phase 4 gates), RESUMPTION/UKDL change logs, the hand-back ancestor check (rc=0), and the final status (`TRACKING_ONLY`, CRO-05 SATISFIED for this plan's own paths).

## Task Commits

Each task was committed atomically:

1. **Task 1: Tracer -- seal_check.py (TDD, 9-case selftest), EVIDENCE sections 0-1 from every phase artifact, and ONE verdict carried end-to-end (Phase 3)** - `471c749` (feat)
2. **Task 2: RESUMPTION complete -- hand-back, laptop relabel, sealed list, verdicts of phases 1, 2 and 4, follow-ups, three next actions, previous actions kept, start instruction; EVIDENCE section 2** - `c34511a` (feat)
3. **Task 3: UKDL complete -- GEX44 verdict paragraph, planned entries per gate, laptop relabel, hand-back ancestor check, seal commit, final git status; EVIDENCE sections 3-5** - `9044735` (feat, commit A) and `bef510d` (docs, commit B)

_Note: Task 1 was TDD (`tdd="true"`). The RED step was observed iteratively rather than via a formal
NotImplementedError stub: the module was implemented directly, then `--selftest` was run and failed
`SEALCHK_SELFTEST_PASS=7/9  threshold=9/9` (S5 and S6 failing) before two bugs were fixed -- a docs-slop token
("placeholder") in the fixture prose that tripped the checker's own `privacy()` rule, and a VERIFICATION-status
mutation in the S6 gate fixture that left the RESUMPTION Phase-4 bullet's `verification:` text stale. After both
fixes, `--selftest` read `SEALCHK_SELFTEST_PASS=9/9  threshold=9/9` (GREEN)._

## Files Created/Modified
- `.planning/workstreams/cognitive-resource-os/phases/05-seal-and-hand-back/seal_check.py` - Read-only seal checker (content/hashes/preserve/status modes, 9-case selftest)
- `.planning/workstreams/cognitive-resource-os/phases/05-seal-and-hand-back/EVIDENCE.md` - Pre-checks, per-phase inputs, RESUMPTION/UKDL change logs, hand-back check, final status
- `vault/plans/cognitive-resource-os-RESUMPTION.md` - GEX44 hand-back, sealed list, verdicts 1-4, follow-ups, next actions, laptop relabel
- `vault/knowledge_base/ukdl-cognitive-resource-os.md` - GEX44 verdict paragraph, six evidence-cited entries, laptop relabel

## Decisions Made
- Both Phase 4 gates (04-VERIFICATION.md status `passed`, 04-REVIEW.md `### CR-01:` heading containing `env_check`) resolved to WRITE at execution time, so `T-BACK-TO-BACK-REUSE-001` and `T-TRUTHY-PRESENCE-GUARD-001` were both written -- the full planned set of 6 new UKDL entries, giving 14 total entry-ID lines (8 original + 6 new), matching the plan's own planning-time expectation.
- `seal_check.py`'s heading-order and per-line figure-labelling checks (stage 2) drove a design choice: every 2d/2c/2e/1a/4 bullet in RESUMPTION.md was kept to a single physical line so the "every figure line names GEX44 or laptop" rule could be verified unambiguously rather than needing per-wrapped-line tracking.
- Task 3's action item 3 ("Prefix-miss follow-up") used the standard wording, not the 04-VERIFICATION-gaps variant, because `04-VERIFICATION.md` read `status: passed` at execution time.

## Deviations from Plan

None - plan executed exactly as written. Task 1's TDD RED step was observed via an iterative implement-then-fail
cycle rather than a formal NotImplementedError stub (documented above under Task Commits); this is a process note
on how RED was reached, not a deviation from the plan's required tasks, files, or verification.

## Issues Encountered
None beyond the two seal_check.py selftest bugs described above, both fixed before the first commit.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- The laptop session can resume from `vault/plans/cognitive-resource-os-RESUMPTION.md` alone (section 1a names the fetch/fast-forward commands; sections 2c-2e carry everything phases 1-4 produced).
- `mission/cognitive-resource-os-gex44` fast-forwards `mission/cognitive-resource-os` (`git merge-base --is-ancestor` rc=0); the Owner (or the laptop) completes the literal hand-back with the commands recorded in RESUMPTION section 1a.
- Open items carried forward: CRO-01 (Owner review of the pinned pytest/pluggy/iniconfig install), the laptop-side P3 pre-flight + P1 A/A, and the prefix-miss zero-call follow-up from the laptop's own transcripts -- all three are RESUMPTION section 4's ranked next actions.
- 04-REVIEW's CR-01/WR-01/WR-02 stay open; `ab_runner.py` may not be reused until they are fixed under a new runner sha (RESUMPTION section 2e, UKDL `T-TRUTHY-PRESENCE-GUARD-001`).

## Self-Check

- FOUND: `.planning/workstreams/cognitive-resource-os/phases/05-seal-and-hand-back/seal_check.py`
- FOUND: `.planning/workstreams/cognitive-resource-os/phases/05-seal-and-hand-back/EVIDENCE.md`
- FOUND: commit `471c749`
- FOUND: commit `c34511a`
- FOUND: commit `9044735`
- FOUND: commit `bef510d`
- Re-ran `seal_check.py status` after all task commits: `final_status: TRACKING_ONLY ( M .planning/workstreams/cognitive-resource-os/STATE.md)` -- STATE.md is orchestrator-owned and expected to be updated by this execute-plan workflow's own state-update step next.

## Self-Check: PASSED

---
*Phase: 05-seal-and-hand-back*
*Completed: 2026-09-28*
