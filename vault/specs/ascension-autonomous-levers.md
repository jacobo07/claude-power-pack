---
spec: ascension-autonomous-levers
status: IMPLEMENTED (pending deploy)
tier: T2 (autopilot behaviour change: lanes no longer wait on the Owner for a new lever)
covers: [ascension-autopilot, evolve, lever synthesis]
owner_decision: "Owner 2026-11-16 pane 08cba76c: 'rec, y deberia haberse hecho de forma autonoma'"
---
# Ascension: the autopilot designs its next lever

## Problem (observed 2026-11-16)
FIFA, MKWLIB, TENNIS and WIIPARTY parked or stopped on "no open lever of another family" / "planner found no admissible
next lever" / research stop rule, and waited hours for the Owner to invent a route that their own residuals already named.
The Owner's standing authorization (pane f3df357a, 2026-11-14) covers new routes; only budgets are his.

## Design
- `evolve.synthesize` / `_synth_or_park`: at every park for want of a lever (plateau with no lever, research stop rule,
  INSTRUMENT_FAIL with no repair lever, repair cap) and at a planner stop, call `designer(family)`; admit the result by
  `synth_problems` (new id, family different from the one left, research kind, blockers, `what` >= 200 chars citing the
  residual file, `requires` present); append to levers.json with `origin: autopilot`; enter RESEARCH with it.
- `autopilot.design_lever`: one read-only model call (`lever_designer_prompt.md`) over the residual, negative knowledge,
  the lane's levers, brief and digest; may answer `{"none": why}`. Ledger rows `lever_design` (tokens) and
  `lever_designed`; an Owner-queue NOTICE (not a gate).
- Bounds: `SYNTH_MAX = 3` designed levers in a row without a verified CAPABILITY/CERT park the lane; an Owner resume
  resets the streak. Research generation cap 10M, lane research cap 100M, envelope and day cap unchanged.

## Acceptance
`test_autopilot.py` V-EVO-SYNTH-{PLATEAU, PERSISTED, SAME-FAMILY-REFUSED, MUST-CITE-RESIDUAL, BOUNDED, RESEARCH-STOP,
PLANNER-STOP, NONE-STOPS-AS-BEFORE}; mutants evo_synth_off, evo_synth_admits_anything, evo_synth_unbounded,
evo_synth_residual_unchecked, synth_not_persisted killed; whole gate AUTOPILOT_GATE_PASS.

## Rollback
Restore autopilot.py / evolve.py from the `*.bak-08cb-synth-*` copies on GEX44 (or the previous commit of the mirror).
With `EVO_OFF` the path is inert.
