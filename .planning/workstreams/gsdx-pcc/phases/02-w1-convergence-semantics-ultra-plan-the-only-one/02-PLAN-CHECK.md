# Phase 2 -- plan check (gsd-plan-checker, iteration 1)

Persisted by the orchestrator (the checker has no write tool). Verdict: **ISSUES FOUND -- 0 blockers, 2 warnings,
4 info**. Requirements D01, D03, D10, D43, D44 all covered; dependency graph acyclic; locked decisions honoured.

## Issues (checker's structured list)

```yaml
issues:
  - plan: null
    dimension: research_resolution
    severity: warning
    required_property: "RESEARCH.md carries no unresolved open question"
    description: "02-RESEARCH.md:506 '## Open Questions' lacks the (RESOLVED) suffix and inline markers on questions 1-5; resolutions exist in STATE.md:52-57 and the plans follow them"
    fix_hint: "Mark the heading '(RESOLVED)' with a pointer to the STATE decisions"
  - plan: "02-01"
    dimension: key_links_planned
    severity: warning
    required_property: "Every gate cited in a spec Gates line exists in a suite under the same name"
    description: "S11 cites V-PCC-REPLAY-IGNORE-NEW-TYPES; 02-02 defines -FUTURE and -PCC only; no discovered cross-check ties spec gate tokens to suite check() names"
    fix_hint: "Align the name and add a discovered spec-token -> suite check to V-PCC-SPEC-RESOLVED"
  - plan: "02-01"
    dimension: scope_sanity
    severity: info
    required_property: "Each task stays within the per-plan context budget"
    description: "Task 2 bundles S1,S3-S16, Rollback, six Q&A, premise record; estimate confidence low"
    fix_hint: "Commit a mid-task checkpoint (e.g. after S1-S8)"
  - plan: "all"
    dimension: claude_md_compliance
    severity: info
    required_property: "Commit trailer follows the session's Co-Authored-By line"
    description: "Plans hardcode 'Claude Opus 5.5 (1M context)' while ROADMAP says use the session's line"
    fix_hint: "Reference the session's line"
  - plan: "02-04"
    dimension: verification_derivation
    severity: info
    required_property: "The legacy-equivalence truth matches the rule the gate asserts"
    description: "Truth says FRESH == _needs_a_gate_here empty, mapping also requires o.revision == revision, which reconcile.py:101-121 ignores"
    fix_hint: "State equivalence over public-writer logs in S2, or drop the clause"
  - plan: "02-02 / 02-06"
    dimension: verification_derivation
    severity: info
    required_property: "A live-store SAME/CHANGED gate cannot fail from a legitimate concurrent sweep"
    description: "Live-store fingerprint gates can flip on a PP-GoalSweep write (A7)"
    fix_hint: "Treat CHANGED with an active sweep as UNJUDGED, not a code failure"
```

Checker method note: static read of the six plans, CONTEXT, ROADMAP, STATE, DENOMINATOR, RESEARCH (Open
Questions), convergence.py, reconcile.py, mutation_drill.py and gsdx_reality_baseline.py flags. It did not read
02-VALIDATION.md, 02-PATTERNS.md or REQUIREMENTS.md, and did not run estimate-check (no shell).

## Orchestrator dispositions

| # | severity | disposition |
|---|---|---|
| 1 research_resolution | warning | FIXED: `## Open Questions (RESOLVED -- see STATE.md Decisions, 2026-10-07 worker epoch 3)` |
| 2 key_links_planned | warning | FIXED: the 02-01 S11 Gates line names `V-PCC-REPLAY-IGNORE-NEW-TYPES-FUTURE` and `-PCC`. The 02-05 spec-resolution gate gains a discovered cross-check: every `V-PCC-*` token in the spec must resolve to a `check()` name in one of the two suites, with a positive control |
| 3 scope_sanity | info | TAKEN: 02-01 Task 2 commits a checkpoint after S1-S8 |
| 4 claude_md_compliance | info | NOT CHANGED: the literal equals this session's attribution line. A later executor on another model follows its own session line per ROADMAP, which binds over the plan text |
| 5 verification_derivation | info | TAKEN: S2 states that the `o.revision == revision` clause is a no-op over public-writer logs (`satisfy` refuses a stale `ob.revision`, convergence.py:264), and that a raw log where they differ maps to UNKNOWN, never FRESH |
| 6 verification_derivation | info | TAKEN: a live-store CHANGED observed while a `PP-GoalSweep` run is active is recorded UNJUDGED (with the sweep evidence), never as a code failure and never as SAME |
