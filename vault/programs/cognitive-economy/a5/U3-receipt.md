STATUS: DONE
COMMITS: be7c3c69
Packet sha256 6752c29e1b99 verified. Scope: tools/cost_to_completion.py (extended in place), tools/test_a5_u3.py.
GATE tools/test_a5_u3.py: A5_U3_PASS=26/26 (0.1 s)
GATE tools/test_cost_to_completion.py: CTC_PASS=18/18 (unchanged, absent fields keep behaviour)
Semantic stage: obligations on claims; classes NO_WORK, NO_COMPUTE, FAMILY, SHARED_OBS, SHARED_PROOF (+ STALE_RECOMPUTE, MODEL, OWNER).
Output `semantic`: lower bound (novel decisions + distinct observations + assurance judgments + owner decisions, labelled estimate),
  overhead_multiplier_input (doc historical_calls / lower bound; null when unknown), interrupt_budget per class, alternatives per obligation.
Refusals (each paired with an admitting control): MISSING_INVALIDATOR, FAMILY_NO_PROOF, HISTORICAL_PROFILE; PHASE_MULTIPLIER unchanged.
Mutants red: stale invalidator accepted, family/proof/observation priced N times, missing invalidator accepted, historical label accepted.
Deviations / chosen semantics (packet silent):
 - Stale invalidator ({"stale":true} or {"valid":false}) voids reuse: obligation recomputed as known_transform, listed in semantic.stale.
 - Obligations replace the claim's own class cost; satisfied/sleeping claims still cost 0.
 - HISTORICAL_PROFILE key only emitted when obligations or `label` are present (keeps old output identical); true unless all 3 model classes
   come from `profiles` (actuals/priors count as historical). `actuals` still outrank `profiles` (existing order).
 - Obligation unit prices: PROOF/OBSERVATION/stale = known_transform; first FAMILY = bounded_coding (novel if "novel":true); MODEL = novel default.
 - No real-claims run on dws-budget-compiled.json (inputs carry no obligations; U10 supplies them). Lower-bound ± not computed: UNKNOWN.
