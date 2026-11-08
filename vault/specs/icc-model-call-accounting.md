---
status: APPROVED-BY-DEFAULT 2026-11-05 (implemented, 5 tests, mutation red->green) (ICC mission m-1f1ba12950ec, Phase 4; autonomous, internal-only, reversible)
covers: [model-call-accounting, zero-model-fraction, zero-model-closeout]
tier: T2
---

# ICC Phase 4 -- model-call accounting + zero-model closeout

## PRD
Today a mission that only needs a known script run already closes without a model (`gsd_mission._run_deterministic`,
`deterministic=res` with `model_calls: 0`, event `deterministic_completed`). Nothing measures how often that happens
versus model-driven epochs, and a mission whose done-gate already passes still spends a model turn to be closed.

## Design (extend, no new meter)
1. `tools/mission_spend.py`: add `model_call_report(rec_or_ledger_rows)` -> per mission: `model_epochs`, `deterministic_closes`,
   `calls_per_obligation` (obligation = one epoch's work unit / packet), and `zero_model_fraction` =
   deterministic_closes / (deterministic_closes + model_epochs), grouped by Work Class when the packet declares one,
   else `unclassified`. Source: mission ledger events (`epoch_started`, `deterministic_completed`), never transcripts guessed.
   Absent data -> `None`, never 0 (real-context-reachability).
2. `tools/gsd_mission.py`: at the point the supervisor would launch an epoch, if the packet carries a done-gate command
   (same `_DETERMINISTIC_RE` family) and running it exits 0, close through the existing `_run_deterministic` transition.
   Same guards: script inside execution root, .py/.sh only, non-zero exit leaves the mission untouched, no model fallback.
3. CLI: `python tools/mission_spend.py model-calls --mission <id>` prints the report as JSON.

## Acceptance criteria
- AC1 report on a ledger with 2 model epochs + 1 deterministic close -> fraction 1/3; empty ledger -> `None`.
- AC2 done-gate passing -> mission COMPLETED, `model_calls: 0`, no epoch claimed; failing gate -> state unchanged.
- AC3 both poles tested (pass and fail gate), one mutation (drop the rc check) turns a test red.
- AC4 live evidence: the report run on one real mission record from `~/.claude/state` ledgers.

## Rollback
Env `GSD_ZERO_MODEL_CLOSE=0` disables item 2 (default on only after tests green); item 1 is read-only. `git revert` of the
phase commit removes both. No schema change to mission records (event fields only added).

## Not in scope
Pricing, new meters, changing the lease/budget judge.

