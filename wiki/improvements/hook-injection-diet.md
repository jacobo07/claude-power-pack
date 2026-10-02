---
type: improvement
created: 2026-10-02
updated: 2026-10-02
sources: [2026-10-02-token-economy-internal-inventory]
status: IDEA
effort: S
graduated_to:
---

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
