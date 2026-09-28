# Phase 3: P3 pre-flight P0 - Context

**Gathered:** 2026-09-28
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

Decide, without spending model calls, whether the predeclared ablation
(`vault/plans/cognitive-resource-os-P3-ablation-protocol.md`) can run an arm WITHOUT ~/.claude/rules while
touching neither global config nor credentials.
Requirement: CRO-03. Success criteria: see ROADMAP.md Phase 3.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — discuss phase was skipped per user setting. Use ROADMAP phase goal, success criteria, operating constraints and codebase conventions to guide decisions.

### Fixed by the roadmap / protocol
- Zero model calls in this phase. Evidence comes from `claude --help`, the installed version's documented flags and
  static inspection only. No ablation run.
- Verdict is exactly one of PASS (named mechanism) or STOP (per protocol: do not improvise).
- A mechanism that needs a copied credential or an edited global file is REJECTED.

### Run-environment note
Work happens in the isolated worktree `.claude/worktrees/cro-gex44` on branch
`mission/cognitive-resource-os-gex44`, branched from `cd4e436` (tip of `mission/cognitive-resource-os`).
Phase 1: gates PASS, full suite BLOCKED (pytest not installed; install awaits Owner). Phase 2: CRO-02 MEASURED.

</decisions>

<code_context>
## Existing Code Insights

Codebase context will be gathered during plan-phase research.

</code_context>

<specifics>
## Specific Ideas

No specific requirements — discuss phase skipped. Refer to ROADMAP phase description and success criteria.

</specifics>

<deferred>
## Deferred Ideas

None — discuss phase skipped.

</deferred>
