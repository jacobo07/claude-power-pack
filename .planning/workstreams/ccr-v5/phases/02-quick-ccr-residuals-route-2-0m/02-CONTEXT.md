# Phase 2: Quick CCR residuals (route 2.0M) - Context

**Gathered:** 2026-10-15
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

X2 step 5: copy `vault/programs/ccr/stage3/a3/pgo-classes.json` and `stage3/a4/pgo/*.breakeven.json` into
`~/.claude/ccr/state/pgo/`; verify DEFLATE reads them; document the `CPP_CCR_DEFLATE=off` hold.

Version the GEX44 driver (`kobii@gex44:~/missions/ccr-s3-data/drive3.sh`, read via ssh `gex44`) into
`vault/programs/ccr/stage3/driver/` with a regression test proving a string-`message` line and an empty/ERR
measurement trip the breaker (the v3 `over()` already fails closed: prove it, do not re-fix it).

Bring the CCR RESUMPTION_FILE continuation into a durable owner (Phase 4 defines the seal; here: commit its
current content on ccr/v5).

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion. Use the ROADMAP phase goal and codebase conventions.
Constraints carried from STATE.md: the worktree disables the github/notion/21st-dev MCP servers; the mission needs none.
Writes under `~/.claude/` are Owner-side registration steps per HR-001 where the classifier blocks them.

</decisions>

<code_context>
## Existing Code Insights

Codebase context will be gathered during plan-phase research.

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond the ROADMAP phase description.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>
