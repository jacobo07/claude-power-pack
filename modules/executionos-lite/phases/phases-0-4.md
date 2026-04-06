# Phases 0-4: Input through Discovery (STANDARD+)

## Phase 0 -- INPUT
- Capture user request verbatim. No interpretation yet.
- Note: language, tone, urgency signals, explicit constraints.
- If request references prior context, locate it before proceeding.

## Phase 1 -- INTENT
- Decompose into: **What** (deliverable), **Why** (motivation), **Constraints** (limits), **Success** (how to verify).
- If any component is missing or ambiguous, trigger Question Gate.
- Output: single-sentence intent statement.

## Phase 2 -- SOURCES
- Start from PART A0 assimilation results. Extend with task-specific sources only.
- List every file, doc, log, config, or external resource needed.
- Classify each: must-read (blocking), should-read (context), nice-to-have (background).
- Read all must-read sources before Phase 3. No exceptions.

## Phase 3 -- ROUTE
- Estimate complexity: trivial / moderate / complex / incident.
- Map to depth tier: LIGHT / STANDARD / DEEP / FORENSIC.
- Refine domain from PART A0 context. Override only if task-specific signals contradict.
- Select overlays to load (0-2 overlays typical).
- If Language Fragility Gate score >= 2 AND Elixir is chosen/recommended → load `overlays/elixir.md`

## Phase 4 -- DISCOVER
- Read sources identified in Phase 2.
- Build working model: architecture, data flow, dependencies.
- Note gaps: missing files, unclear ownership, stale docs.
- If gaps are blocking, trigger Question Gate before Phase 5.
- Output: mental model summary (internal, not printed unless requested).
