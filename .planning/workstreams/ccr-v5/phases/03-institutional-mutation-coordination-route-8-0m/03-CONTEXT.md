# Phase 3: Institutional Mutation Coordination (route 8.0M) - Context

**Gathered:** 2026-10-15
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

Extend `modules/lease/store.py` from ledger mutex to resource leases (resource id, intent, expected base revision, writer identity).
Writer probe for a dirty shared path (live pane/session if discoverable, else UNKNOWN). Conflict => durable `WAIT_ON_RESOURCE` row
(extend `tools/mission_recovery.py` DURABLE_WAIT): blocked goal/WU, resource, writer, expected event, resume action, validation, timeout.
Wakeup from the existing PP-GsdLongRun-Sweep pass (no model polling) on commit / lease release / writer death. Fold the scratchpad
`step2.ps1` logic into `tools/land_worktree.py` as the resume action (dirty-path check, merge, tests, rollback on ANY test failure --
fixes the a6-test no-revert bug). Abandoned writer: never touch its bytes; bounded merge WU instead. Register the real case: merge
`ccr/v4` (then `ccr/v5`) into the main tree, waiting on `vault/knowledge_base/ukdl-universal.md`.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion. Use the ROADMAP phase goal, the plan `vault/plans/ccr-v5-svm-imc-2026-10-14.md`
and codebase conventions. Extend existing owners (grep first), never build parallel modules. UNKNOWN is never zero. No push, no main-tree
writes to foreign dirty bytes (ukdl-universal.md in the main tree is a foreign writer's: never touch). Every phase ends with 03-EVIDENCE.md.
Hook/registration changes outside the registered dispatcher chain are OWNER STEPs written to EVIDENCE.

</decisions>

<code_context>
## Existing Code Insights

Gathered during planning.

</code_context>

<specifics>
## Specific Ideas

None beyond the ROADMAP goal.

</specifics>