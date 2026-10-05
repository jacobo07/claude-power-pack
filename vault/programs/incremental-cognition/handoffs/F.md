# Handoff [F] -- GSD workflow-doc residency, to the GSD owner

Pillar [F] (GSD operational projection) of the incremental-cognition program, owner-bundle row 6.
Owner: `~/.claude/gsd-core/bin/gsd-tools.cjs` (frozen pillar owner). Frozen rule: "measure GSD workflow-doc residency
(char x turns) on KME-L; if gsd-tools init already returns the compact state, hand the residency finding to the GSD
owner; never fork GSD".

Source: `vault/programs/incremental-cognition/measurements/F-KME-L-2026-10-05.md` (kme_pillars, plane gex44,
population_match exact, terminal_evidence true).

## Finding

- `init_json_present: true` -- gsd-tools init already returns the compact state, so the rule's condition holds.
- GSD workflow / reference / template docs, skill bodies, invoked-skill re-injections and gsd command bodies stay
  resident at 0.65 % - 0.97 % of the KME-L weighted denominator (3,828,285 chars). Below the 3 % materiality line: no
  slice is justified in this program.
- Largest kind: `workflow` docs, 83 docs, 2,333,884 chars, weighted 6.5M - 9.75M of the 11.4M - 17.1M total.
- In the 4 human-prompt turns where a workflow doc and the init JSON appear together, the doc carries 21.27x the init's
  chars (239,726 vs 11,272): when both are loaded, the doc, not the init, is the residency.

## What the GSD owner may do with it

Nothing is required by this program (below materiality). If GSD wants to shrink residency, the measured lever is
loading workflow docs only when the init JSON does not already answer the step; the ratio above is the size of that
lever per paired turn. GSD is not forked or edited here.
