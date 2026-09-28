---
phase: 02-gex44-observed-baseline
plan: 01
subsystem: observability
tags: [tis_observed, budget_monitor, pricing_source, tis_report, transcripts, observed-usage, entrypoint]

# Dependency graph
requires:
  - phase: 01-gate-verdict-on-the-big-host
    provides: workstream gates green on GEX44 (25/25, 7/7, 5/5, 9/9), pytest suite BLOCKED (unrelated to this plan)
provides:
  - "GEX44 observed baseline (per-entrypoint sessions/calls/median-first-call-context/startup_shared_share_median/
    1h-write share/7d USD), reconciled against tis_observed, tis_report and budget_monitor, beside the laptop's
    2026-09-27 figures with explainability labels"
affects: [phase-4-prefix-cache-miss-ab, phase-5-seal-and-hand-back]

actuals:
  tokens: 11912
  tasks: 3
  commits: 3

# #3968: commits measured via `git rev-list --count ${plan_head_before}..HEAD`, not narrated.
commits: 3
plan_head_before: c8b73ae5a3a6502d45dcb9c2e2b1b55418c70d4f

tech-stack:
  added: []
  patterns:
    - "Evidence reproducer composes existing instruments (tis_observed, budget_monitor, tis_report) rather than
      re-implementing dedupe/pricing/context logic -- by_entrypoint.py imports and calls their functions directly"
    - "R1-R6 in-process reconciliation: one snapshot cross-checked against three independent read paths of the
      same corpus, with a bounded (<=3) rerun-on-mismatch rule before a MISMATCH is treated as a tool defect"

key-files:
  created:
    - .planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/by_entrypoint.py
    - .planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/EVIDENCE.md
  modified: []

key-decisions:
  - "by_entrypoint.py lives beside EVIDENCE.md under .planning (not under tools/), per the plan's explicit
    instruction to keep tools/ untouched absent a defect -- it composes tis_observed/budget_monitor/tis_report
    functions rather than re-implementing their dedupe, TTL-split or pricing logic"
  - "TDD sequence followed literally: measure() first raised NotImplementedError (RED, rc=1, no
    BYEP_SELFTEST_PASS line), then the real implementation was written and the selftest re-run to
    BYEP_SELFTEST_PASS=9/9 (GREEN)"
  - "The 9 selftest cases (S1-S9) are each a single check() call aggregating several sub-assertions, so the
    printed line reads exactly BYEP_SELFTEST_PASS=9/9 as the plan's acceptance criteria require, rather than a
    more granular per-assertion count"
  - "trailing_7d's calls figure intentionally includes subagent calls (tis_observed.iter_calls's default),
    matching budget_monitor._aggregate_observed's own definition so R5/R6 reconcile; the all-time calls figure
    instead mirrors tis_observed.summarize's native calls field (main-session calls only, subagent_calls tracked
    separately) -- documented in EVIDENCE.md section 2 as two different, correct bases rather than smoothed
    into one"
  - "No tool defect found: all three instrument gates held Phase 1's pass counts with no [FAIL] line, reconcile
    read MATCH on the first snapshot run (no rerun needed), multi_entrypoint_files read 0, and no path under
    tools/ or modules/ changed -- tool_defects: none, phase_verdict: MEASURED, cro02: SATISFIED"

patterns-established:
  - "Zero-priced dummy price table (_ZERO_PRICES) passed to tis_observed.cost_usd solely to extract its
    ttl_assumed boolean by composition, avoiding a second, drifting implementation of the cache-write TTL-split
    check"

requirements-completed: [CRO-02]

coverage:
  - id: D1
    description: "tis_report --observed --all-projects ran on GEX44 transcripts; state recorded as MEASURED per
      the stated rc/calls rule (ROADMAP Phase 2 criterion 1)"
    requirement: "CRO-02"
    verification:
      - kind: other
        ref: "EVIDENCE.md section 1 (tis_report_rc: 0, run_state: MEASURED); Task 1 verify automated check 1"
        status: pass
    human_judgment: false
  - id: D2
    description: "Per-entrypoint sessions, calls, median first-call context, startup_shared_share_median, 1h
      cache-write share, and 7-day API-rate-equivalent USD, pricing file named, for cli and sdk-cli (ROADMAP
      Phase 2 criterion 2)"
    requirement: "CRO-02"
    verification:
      - kind: other
        ref: "by_entrypoint.py --selftest (BYEP_SELFTEST_PASS=9/9); EVIDENCE.md sections 2b/2c reconciled against
          byep-final.json; Task 2 verify automated checks 1-3"
        status: pass
    human_judgment: false
  - id: D3
    description: "GEX44 figures set beside the laptop's (1.9%/16.4% first-call shared prefix, 79.9% 1h cache
      writes, $90.06/272/62) with explainable/not-explainable labelling (ROADMAP Phase 2 criterion 3)"
    requirement: "CRO-02"
    verification:
      - kind: other
        ref: "EVIDENCE.md section 3 (8 required rows) + 3a; Task 3 verify automated check 1"
        status: pass
    human_judgment: false
  - id: D4
    description: "Evidence written; no code changed absent a tool defect, or a RED-first fix recorded (ROADMAP
      Phase 2 criterion 4)"
    requirement: "CRO-02"
    verification:
      - kind: other
        ref: "EVIDENCE.md section 4 (tool_defects: none); git diff --name-only <phase-start head> HEAD -- tools
          modules (empty); Task 3 verify automated check 3"
        status: pass
    human_judgment: false

duration: 17min
completed: 2026-09-28
status: complete
---

# Phase 02 Plan 01: GEX44 observed baseline Summary

**Per-entrypoint observed-usage baseline (sessions/calls/context/shared-cache-share/1h-write-share/7d-USD for
cli and sdk-cli) measured from GEX44's own transcripts via a new reconciled reproducer, `by_entrypoint.py`, and
set beside the laptop's 2026-09-27 figures with explainability labels -- CRO-02 verdict MEASURED/SATISFIED.**

## Performance

- **Duration:** 17 min
- **Started:** 2026-09-28T12:35:27Z
- **Completed:** 2026-09-28T12:52:03Z
- **Tasks:** 3 (of 3)
- **Files modified:** 2 (both created: EVIDENCE.md, by_entrypoint.py)

## Accomplishments
- Ran `tools/tis_report.py --observed --all-projects` on GEX44's real transcripts (11 project dirs, 42 session
  files, 39-41 subagent files depending on the measurement instant): rc=0, calls=559 (Task 1) / 591 (Task 2
  snapshot, corpus grew between runs) -> run_state MEASURED
- Built `by_entrypoint.py`, a read-only evidence reproducer that composes `tis_observed`, `budget_monitor`,
  `pricing_source` and `tis_report` (never re-implementing their dedupe/pricing/TTL logic) to fill the
  per-entrypoint gap no single tool emits; TDD RED (NotImplementedError stub) then GREEN
  (`BYEP_SELFTEST_PASS=9/9`), reconciled against the same instruments' own read paths (R1-R6, all MATCH on the
  first snapshot run, no rerun needed)
- Measured the per-entrypoint baseline for both all-projects and excluding-this-worktree's-own-project-dir
  scopes: cli (13 sessions, 588 all-time calls, $123.26 trailing-7d) and sdk-cli (3 sessions, 3 all-time calls,
  $0.53 trailing-7d, 98.6% of that spend a 1h cache write)
- Set all required figures beside the laptop's L1-L4 (each cited by source commit and scope), with per-row
  same-definition/can-explain/cannot-explain labelling, closing on the open MCP-tool-list question for Phase 4
- Recorded no tool defect (all three gates held Phase 1's pass counts, reconcile MATCH, no tools/modules diff)
  and wrote the CRO-02 verdict: phase_verdict MEASURED, cro02 SATISFIED

## Task Commits

Each task was committed atomically:

1. **Task 1: Tracer -- pre-checks, corpus inventory and the ROADMAP command recorded end-to-end** - `03fffab`
   (docs)
2. **Task 2: Per-entrypoint baseline -- by_entrypoint.py reproducer (TDD), one reconciled snapshot** - `1766507`
   (feat)
3. **Task 3: Laptop comparison, tool-defect record, CRO-02 verdict** - `cb6fc62` (docs)

_Note: Task 2 was TDD (`tdd="true"`); the RED step (measure() raising NotImplementedError, observed rc=1,
no BYEP_SELFTEST_PASS line) was run and discarded in place rather than committed separately -- only the final
GREEN file was committed, per the plan's instruction to "note the RED result for the SUMMARY" rather than
commit the stub._

## Files Created/Modified
- `.planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/by_entrypoint.py` - read-only
  evidence reproducer: `measure()` composes tis_observed/budget_monitor/tis_report into the per-entrypoint
  all-time + trailing-7d table with R1-R6 reconciliation; `--selftest` (S1-S9, synthetic fixture only, no real
  transcript read) and normal-mode `main()` against the real corpus
- `.planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/EVIDENCE.md` - sections 0-5:
  pre-checks + corpus inventory, tis_report run, per-entrypoint baseline (2a-2d), laptop comparison (3-3a), tool
  defects (4), CRO-02 verdict (5)

## Decisions Made
See `key-decisions` in frontmatter. Summary: reproducer composes rather than reimplements; TDD RED then GREEN
followed literally; selftest output shaped to match the plan's literal `BYEP_SELFTEST_PASS=9/9` acceptance
criterion (one check per S-case rather than per sub-assertion); trailing_7d vs all-time `calls` intentionally use
two different, instrument-native definitions (documented, not reconciled into one number); no tool defect found.

## Deviations from Plan

None - plan executed exactly as written. The only interpretive choice was selftest check granularity (documented
above as a decision, not a deviation, since it produces the literal `BYEP_SELFTEST_PASS=9/9` line the plan's
Task 2 action step and acceptance criteria specify).

## Issues Encountered
- The Task 1 draft of EVIDENCE.md section 1's prose named this worktree's own transcript directory path
  verbatim (a per-project directory name), which the plan's own leak/tag automated check correctly caught before
  commit. Fixed inline (the path was replaced with "name omitted, per-project directory names are not recorded
  here") and the check was re-run clean before staging -- caught by the plan's own verification, not a defect in
  the plan.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 4 (Prefix cache-miss A/B) can read first-call `cache_read_input_tokens`/`cache_creation_input_tokens`
  through the same `tis_observed`/`_shared_by_entrypoint` composition already built here.
- Phase 5 (Seal and hand back) has four `instrument_gaps:` bullets (EVIDENCE.md section 4) queued as follow-ups,
  and the assumption-delta decision (host-qualified baseline) still needs RESUMPTION.md/ukdl-cognitive-resource-os.md
  relabelled by host -- explicitly out of this phase's scope per the plan.
- No blockers for Phase 4 or Phase 5 from this plan. Phase 1's pytest-suite blocker (CRO-01, Owner
  package-legitimacy checkpoint) remains open but is independent of CRO-02.

## Self-Check: PASSED

- FOUND: EVIDENCE.md, by_entrypoint.py, 02-01-SUMMARY.md (all three exist on disk)
- FOUND: 03fffab, 1766507, cb6fc62 (all three task commits present in `git log`)

---
*Phase: 02-gex44-observed-baseline*
*Completed: 2026-09-28*
