---
type: improvement
created: 2026-10-02
updated: 2026-10-04
sources: [2026-10-02-token-economy-internal-inventory]
status: IN-PROGRESS
effort: S
graduated_to: tools/jit_skill_loader.py, hooks/graph_first_gate.js, hooks/advisory_once.js, hooks/cascade_check_bash.js
---

## Done 2026-10-04 (Owner "yes")

Census of one 2.9 MB session (session c47b1f78, scratchpad `hook_census.py`): 34 injections, 65.5k
chars (~28k tok fitted). Top: JIT active spec 27.6 % (the same 6.8 KB, 3x), per-prompt composite
(tier + Tower + SDD-OS + AKOS) ~35 %, cascade-aperture 12x, Graph-First 5x.

- **JIT spec** (LIVE): keyed by content hash in the existing per-session state; repeat = one-line
  pointer, edited spec = re-injected, new session = full (`tools/jit_skill_loader.py`).
- **Graph-First** (LIVE): cooldown 15 min -> 2 h, the JIT dedupe bound (`hooks/graph_first_gate.js`).
- **cascade-aperture** (LIVE, uncommitted): full sentence once per session, then a per-command tag via
  new `hooks/advisory_once.js`; the sink note never shortened. Sits on another session's uncommitted
  elision feature, so it ships with that commit.
- **Tower baseline: NOT changed.** `modules/gsd_x/cli.py:34-38` offers it on the first 3 prompts on
  purpose: the chain can abandon stdout and the child cannot see delivery. Already bounded.
- Gates: `tools/test_hook_injection_diet.py` (DIET 14/14; 6 red on the old code, controls green).
- **Open:** re-run the census on a fresh session to measure the real delta (step 3).

# Advisory-text diet for PP hooks

## Problem

Hook `additionalContext` reaches the model (fitted ~0.43 tok per stored char) and stays in context
for the rest of the session. Over 7 d of main threads: 17,722 injections, ~7.8 M tokens inserted,
~0.70 B tokens re-read, ~$202 est. (fit R² 0.20, rough;
`wiki/tools/token_economy_deep.2026-10-02.out`). Plain `hook_success` records do NOT reach the
model (fitted 0; a 1.85 MB record moved context by 864 tok), so only `additionalContext` and
system messages matter.

Observed in one session (2026-10-02): the inherited "Tower baseline" bullets on every prompt, the
GK-12 graph advisory on each Grep and PowerShell call, the skill advisor on Write, and the
cross-project baseline on PowerShell. Several repeat verbatim many times per session.

## Proposed steps

1. Census: per hook, injections and characters per session over 7 d (from `attach:hook_additional_context`
   records, keyed by hook name).
2. For each repeating advisory: inject once per session, then a one-line pointer, as
   `power-pack-reminder.js` already does ([[2026-10-02-token-economy-internal-inventory]]).
3. Re-measure with the same instrument.

Owner: PP hooks (no program owns this). Related: [[token-economy-brainstorm]] B3.
