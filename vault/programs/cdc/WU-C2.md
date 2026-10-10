# WU-C2 -- Cognitive effect classes + Cognitive ABI on route/packet

Common brief: `vault/programs/cdc/PROGRAMME.md`. Plan section: 3 (C2).

Goal: one effect vocabulary, carried by every route/packet, so a known path cannot silently open a model boundary.
1. PLAN (<= 1 page, `vault/programs/cdc/C2-decision.md`): map cost_to_completion classes and tier_routing work
   classes onto ONE enum: ZERO_COGNITION, DETERMINISTIC, BOUNDED_COGNITION, NOVEL_COGNITION, OWNER_COGNITION. Keep
   existing names as aliases; no rename churn.
2. `tools/cognitive_effects.py`: the enum, alias map, `validate_route(route)` and ABI fields on route.json /
   unit packets: `effect`, `deopt` (list of explicit assumptions whose violation allows escalation), `invalidators`,
   `expected_boundaries`. Absent `effect` = BOUNDED_COGNITION (backward compatible, logged).
3. Wire into `route_admission.py`: a ZERO/DETERMINISTIC route that requests model workers without a `deopt` entry
   -> verdict REFUSED_EFFECT. tier_routing reads the enum.
4. Tests + mutation drill: deterministic route with a worker and no deopt is refused; with deopt it is admitted.
Land via land_worktree. Iterate (iteracion-avanzada) after step 1.
