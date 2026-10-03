# Phase 2: Context lifetime and fresh-epoch economics - Context

**Gathered:** 2026-10-03
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

Replace "savings UNMEASURED" for the live context-lifetime owners with a measured answer, separating realized
saving from displaced rehydration work. Requirements CE-D, CE-E.

</domain>

<decisions>
## Implementation Decisions

- Frozen rules: D = measure realized savings of the live economic trigger with rehydration displacement, hand
  result to owner, no edit of rollover.py / context-watchdog.py. E = measure continuation vs rotation from the
  gsd_epoch census; propose to owner only if a threshold change is worth >= 3 % of D-W7.
- Zero model calls. Import, never edit, `tools/gsd_epoch.py`; read the usage index read-only.
- Every call counted must lie inside D-W7 (same population as the frozen denominator).
- An unobservable counterfactual makes a figure an upper bound, never a saving.

### Claude's Discretion
Pair discovery, rehydration definition boundary (first Edit/Write), ceiling construction for E.

</decisions>

<code_context>
## Existing Code Insights

- Interactive crossings: `~/.claude/state/rollover/rollover-ledger.jsonl` (`successor_claimed`), routes in
  `~/.claude/state/gsd-autorun-ledger.jsonl` (`rollover_kclear_asked`).
- Mission epochs: `tools/gsd_epoch.py` `epochs()`, `census()`.
- KSR instrument: `vault/audits/ksr_archaeology/scripts/ctx_dead.py`.

</code_context>

<specifics>
## Specific Ideas

ROADMAP Phase 2 success criteria 1-4.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>
