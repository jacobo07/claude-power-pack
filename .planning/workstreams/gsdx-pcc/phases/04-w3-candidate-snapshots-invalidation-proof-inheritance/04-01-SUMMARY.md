# 04-01 Summary: R12, candidate snapshot, candidate.promoted

Result: DONE. RED first (logs/04-01-red.log: invalidation 2/10, R12 closure + needs-gate red, candidate gates red "module absent"), then GREEN (logs/04-01-green.log).

- R12: `convergence.tree_equal` (an `unknown:` id equals nothing, itself included) used at goal_closure and reconcile._needs_a_gate_here. Deliberate legacy change (DENOMINATOR R12).
- `candidate.py`: `snapshot` (temporary GIT_INDEX_FILE, add -A, write-tree; unknown: on any doubt, empty tree, scope escape) and `drift` (None when unknown).
- `candidate.promoted` landed: `proof.PROMOTED` in NEW_TYPES, required v/candidate/tree/fingerprint, `ProofLedger.promoted`; spec S7 row moved from frozen to landed table.
- Phase 2 suites adapted, not weakened: sample payload for the new type (semantics, replay), type count 4->5 (V-PCC-ADDITIVE-ONLY, still scoped to the Phase 2 git range), frozen list drops candidate.promoted, V-PCC-STATE-UNKNOWN-TREE now expects a gate to be required for unknown==unknown (R12 fixed), replay ignore-new-types count includes `promoted`.

Gates (laptop): GSDX_INVALIDATION_PASS=10/10, GSDX_PCC_SEMANTICS_PASS=48/48, GSDX_PCC_REPLAY_PASS=28/28, GSDX_FRONTIER_PASS=40/40.
Deviation: candidate.py is not imported by sweep.py yet; the import lands in 04-02 with its first call (PLAN-CHECK W3).