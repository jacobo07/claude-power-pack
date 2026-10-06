# Phase 1: Reality scan + ownership matrix + spec - Context

**Gathered:** 2026-10-06
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

Replace the laptop pre-scan with a traced ownership matrix and a binding spec.

Success criteria (from ROADMAP.md, binding):
1. `.planning/workstreams/edd/OWNERSHIP_MATRIX.md` classifies every dataset concept as ALREADY IMPLEMENTED / UNDER ANOTHER
   NAME / PARTIAL / DOCUMENTED ONLY / DATASET ONLY / REGISTERED-UNREACHABLE / REACHABLE-NOT-COMPLETION-EFFECTIVE / NEW, each
   with file:line of the producer AND consumer it traced.
2. Every NEW row passes the HR-NOVELTY-001 13-question proof or is reclassified.
3. `vault/specs/edd.md` exists with `covers: [edd, expectation-driven-development, semantic-conservation, self-evolution-debt, decision-frontier, reference-frontier]`,
   PRD + architecture + acceptance criteria + rollback, and records conflicts between the iteration standard, CLAUDE.md, UKDL and the mission.
4. D-01/D-02 persisted as decision provenance in the canonical decision owner the scan finds.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — discuss phase was skipped per user setting. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions.

### Binding inputs (not discretionary)
- Contract: `.planning/workstreams/edd/source/MISSION_PROMPT.md` (FIRST ACTION — FULL REALITY SCAN lists the systems to inspect).
- Design input, not truth: `.planning/workstreams/edd/source/DATASET_EDD_1.md`.
- Iteration standard: `.planning/workstreams/edd/source/iteracion-avanzada-universal.txt`.
- Operating constraints in ROADMAP.md apply (pathspec commits, never edit `tools/gsd_mission.py`, never touch `~/.claude` global config, Founder unreachable → `DECISION_FRONTIER.md`).

</decisions>

<code_context>
## Existing Code Insights

Laptop pre-scan (ROADMAP.md) names `modules/gsd_x/mission/{obligation,closure,coverage,structured_facts,contract}.py` and
`modules/gsd_x/goal/*` as the probable owners; it must be re-verified by tracing producers and consumers, not filenames.

</code_context>

<specifics>
## Specific Ideas

No specific requirements — discuss phase skipped. Refer to ROADMAP phase description and success criteria.

</specifics>

<deferred>
## Deferred Ideas

None — discuss phase skipped.

</deferred>
