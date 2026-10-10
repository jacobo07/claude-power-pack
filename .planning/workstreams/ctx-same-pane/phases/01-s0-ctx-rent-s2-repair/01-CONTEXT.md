# Phase 1: S0 ctx-rent S2 repair - Context

**Gathered:** 2026-10-10
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

The PROTOCOL rehydration basis lands correctly. Input: `vault/programs/ctx-same-pane/S0-ctx-rent-s2-halfedit.patch`
(diff of pp-ctx-rent vs 0f8713fe) plus read-only `C:\Users\User\Apps\pp-ctx-rent\vault\plans\ctx-rent-RESUMPTION.md`
and `ctx-rent-s2-recovery.md`. If `git apply` fails, port by hand. Success criteria are in ROADMAP.md Phase 1.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion. Binding constraints: ROADMAP "Operating constraints" and the
contract `vault/plans/context-rent-same-pane-2026-10-10.md`. Work in place in this worktree; never call
EnterWorktree. pp-ctx-rent is read-only. Live install only by clean cherry-pick, otherwise one line in OWNER.md.

</decisions>

<code_context>
## Existing Code Insights

Owners to extend: tools/rollover.py, rollover_econ.py, rollover_replay.py, hooks/rollover_wall.js. Gathered in plan-phase research.

</code_context>

<specifics>
## Specific Ideas

None beyond ROADMAP Phase 1 success criteria.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>
