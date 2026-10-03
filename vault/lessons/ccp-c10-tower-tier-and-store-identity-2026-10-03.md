# Two premises falsified while closing CCP §13 c10 (2026-10-03)

Both came from the plan of record and a handoff, both read as "small, obvious" steps,
and both were wrong in a way only the source showed.

## 1. "Record the receipt contract in the tower, EXPERIMENTAL"

- **Previous belief:** the tower can hold an entry at EXPERIMENTAL maturity.
- **Contradiction:** CBR generations (`modules/tower/baselines.py`, `vault/tower/baselines/`)
  carry `reviewed` / `auto` / `reverted`; `active_entries` drops only `reverted`, so every
  other entry is injected into prompts and judged by the family done-gate. FD deposits
  (`modules/tower/capsule.py`, `fable_distillation/deposits_*.jsonl`) have destinations,
  no maturity, and are inherited by every repo.
- **Root cause:** the plan named a destination and a maturity without checking that the
  destination can represent that maturity (CLASE 2: assumed repo state).
- **Correction:** Owner option A, `4656197f` — the receipt contract is recorded EXPERIMENTAL
  in plan §13 (status table), not in the tower. Nothing binding was written.
- **Universal pattern:** a maturity is only real where something reads it. Writing
  "EXPERIMENTAL" into a store whose readers ignore the field publishes a binding rule
  with a misleading label.
- **Promotion status:** PROCESS RULE CANDIDATE ("a maturity tier needs a home before it can
  be recorded"), 1 occurrence. Not promoted.

## 2. "Switch usage_index._store_dirs to tis_observed.store_dirs"

- **Previous belief:** the two are duplicates; swap the call.
- **Contradiction:** `usage_index._store_dirs` also returned an alias map that drives the
  destructive row rewrite, and kept an out-of-store link under its own spelling, while
  `tis_observed` used the resolved path. Same fact, different contract.
- **Root cause:** a shared name and a shared happy path hid a divergent edge contract.
- **Correction:** one producer, `tis_observed.store_identity -> (dirs, aliases)`;
  usage_index consumes it and its copy is deleted; the out-of-store edge follows the S1
  decision (resolved path), pinned red-first by V-SIC-UX-CANON-OUT-OF-STORE; a static gate
  (V-SIC-UX-ONE-PRODUCER) refuses a second copy.
- **Live effect:** none on today's store (298 dirs, 3 in-store junctions, identical sets,
  anchor 23,925 / 6,230,548,450 unchanged). The divergence was latent.
- **Universal pattern:** consolidating duplicates starts with diffing their CONTRACTS,
  edge cases and outputs, not their names. Measure the live inputs where they could differ.
- **Promotion status:** pairs with the Hard Rule candidate "a semantic fact has one
  authoritative producer" (also evidenced by `child_last_call`, `9b28175c`): 2 occurrences
  this week. Still a candidate.

## Not changed by either

LAUNCHED / ASYNC_RAN / RETURNED / HOOK_BLOCKED (`3924a106`): PRG window 200 / 1 / 39 before
and after. The four §13 candidate laws stay candidates.
