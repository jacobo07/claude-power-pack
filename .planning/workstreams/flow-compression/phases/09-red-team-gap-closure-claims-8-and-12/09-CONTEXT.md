# Phase 9: Red-team gap closure (claims 8 and 12) - Context

**Gathered:** 2026-10-25
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

Claim 8: the progress fingerprint must not move for the three BREACH cases of 08-REDTEAM (root
RESUMPTION_FILE.md-only edit, tracked junk file, untracked test log) while the six HELD cases stay held AND
real work still moves it (code under tools/, a new untracked source file, .planning PLAN/SUMMARY/VERIFICATION).
A positive control is mandatory (a blind fingerprint already caused a false no_progress halt, m-3d5f0a27e41d).
Keep the CPP_PROGRESS_BOOKKEEPING=count kill switch.

Claim 12: the replay headline is bounded: an open mission ends at its last row, not at the pin; the open count
and the unobserved tail are reported beside the figure, never folded into it.

Re-run the red team for claims 8 and 12: both must turn HELD with controls still firing; regenerate 08-REPORT /
the done gate; update the breach incident's Repair section.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion. Use the ROADMAP phase section, vault/specs/flow-compression.md and codebase conventions.

</decisions>

<code_context>
## Existing Code Insights

Gathered during plan-phase research (see 08-REDTEAM and the phase 8 artifacts).

</code_context>

<specifics>
## Specific Ideas

None beyond the ROADMAP phase section.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>
