# Requirements — owner-control-plane

Source of truth: `vault/plans/owner-control-plane-2026-10-19.md`. Capital: packet `owner-control-plane-programme-22m-2026-10-19` (22,000,000 programme; checkpoint at 13M).

## Must
- OCP-1 Owner control input is classified before provider budget admission; safe typed operations run with zero model tokens.
- OCP-2 Closed deterministic grammar: ADD, SET, KEEP, STOP; Spanish `por` = ADD, `a` = SET; ambiguity yields a providerless choice, never a guess.
- OCP-3 Capital mutations are idempotent, versioned (CAS), target-bound and auditable; a replay never double-adds.
- OCP-4 Goal state WAIT_OWNER_CAPITAL is separate from session tombstone, generation and lease state.
- OCP-5 A programme change wakes the frontier automatically: residual recompiled, successor lease sized by the runtime, activated with no clear, no manual lease-open, no second Owner message.
- OCP-6 Dirty residual and valid proof survive the capital boundary; FOREIGN or UNKNOWN paths are never committed.
- OCP-7 Workers cannot grant capital; unknown principal, target, ADD-vs-SET or receipt state is never applied.

## Must not
- Apply any change to the econ-safex programme without a typed Owner capital message.
- Merge to main, push, delete transcripts or ledger rows, or edit another pane's worktree.
- Declare done without the fault matrix and the canary evidence (observed, not described).

## Stop-loss
- A stage settles above 1.5x its forecast P80 twice: return to the Owner.
- Total spend reaches 22M: AUTHORITY_REQUIRED, never a silent raise.
