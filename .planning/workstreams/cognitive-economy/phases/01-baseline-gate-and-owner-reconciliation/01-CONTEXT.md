# Phase 1: Baseline gate and owner reconciliation - Context

**Gathered:** 2026-10-03
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

Pillar A becomes IMPLEMENTED_AND_VERIFIED through a re-runnable gate, and the pillars whose capability already
exists in a live owner (I work packet, N event-driven, O cognitive IR, Q capital accounting) are closed by
verified handoffs, not by assertion. Requirements CE-A, CE-I, CE-N, CE-O, CE-Q.

</domain>

<decisions>
## Implementation Decisions

### Binding (ROADMAP operating constraints + frozen ledger + verifier)
- Evidence kinds come from `tools/test_cognitive_economy_program.py` REQUIRED_KINDS: IMPLEMENTED = gate (argv)
  + prg (file, sha256); MERGED = owner (a frozen owner) + handoff (under handoffs/, names `[P]` and an owner,
  committed after FROZEN_AT). sha256 = LF-normalized.
- `frozen` is immutable; only `state.<P>` is written.
- Never ask the Owner mid-run; Owner items go to `owner-bundle.md`.

### Run location (deviation from plan s10, recorded)
The harness refuses edits in the shared checkout for a background session, so the run works in the worktree
`.claude/worktrees/cognitive-economy` on branch `cognitive-economy/autonomous-run`, created from HEAD 8b62b6ce
(contains the freeze). This is the audit's own G2(a)/G5 fix. Merging the branch is an Owner item.

### Claude's Discretion
Gate internals: expected values read from the ledger's frozen object; `--perturb DENOM.KEY=VALUE` for the red
drill only.

</decisions>

<code_context>
## Existing Code Insights

- Owners: I `modules/gsd_x/goal/brief.py`, `tools/gsd_mission.py`; N `tools/goal_sweep.ps1`,
  `tools/gsd_long_run_sweep.ps1`; O `modules/gsd_x/goal/`; Q the ledger.
- Audit G1-G4: `vault/audits/cognitive-economy-phase4-audit.md:12-115`.

</code_context>

<specifics>
## Specific Ideas

ROADMAP Phase 1 success criteria 1-4, literally.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>
