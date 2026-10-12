# Phase 4 Plan Check

Verdict: 1 BLOCKER, 3 WARNING. All 13 requirements map to named gates; RED list is gated and drilled; wave order sound; judge.py untouched; no new Context field.

Spot-checks confirmed: convergence.py:350, reconcile.py:115, git_state.py:131, proof.py defs 129/174/273/425/509. Minor drift: _start_gate is at sweep.py:406 (RESEARCH says 429+).

## BLOCKER
- B1 (04-03, 04-04): inherited set never reaches frontier path. frontier.py calls rc._needs_a_gate_here(o, ctx) (272, 329) and cv.goal_closure(st, ctx.tree_hash) (304, 413) with no inherited arg; 04-03 files_modified omits frontier.py and 04-04 task 1 only reads it. Context cannot gain a field. Inherited claims would close in legacy decide but still be re-gated in frontier decide. Fix: add frontier.py to 04-03; compute inherit.inherited_ids(st, ctx.tree_hash) in each decide path (shared helper) and pass at all five call sites; add gate V-INV-FRONTIER-CONSUMES-INHERITED driven red first; keep frontier 40/40.

## WARNING
- W1 (04-03): no gate drives the sweep step observe->plan->apply end to end (event written, gate not dispatched for INHERIT, dispatched for INVALIDATE). Add a tmp-repo sweep gate.
- W2 (04-05): no drill for D20 UNKNOWN->FULL nor event-disagreement. Add d7 (V-INV-VSET-UNKNOWN-FULL) and d8 (V-INV-EVENT-DISAGREES).
- W3 (04-01): candidate.py imported in sweep.py with no call until 04-02/03; liveness intent. Call snapshot in the dispatch path in 04-01 or defer the import.

## Dispositions (one iteration)
- BLOCKER 04-03/04-04 frontier does not receive `inherited`: FIXED in 04-03 (frontier.py added to files; pass inherited_ids at every call site; gate V-INV-FRONTIER-CONSUMES-INHERITED, red first).
- W1 end-to-end sweep gate: FIXED, V-INV-SWEEP-E2E added to 04-03.
- W2 drills: FIXED, d7 (UNKNOWN->FULL) and d8 (event premises not re-derived) added to 04-05.
- W3 premature import: FIXED, the sweep import moves to 04-02 with its first call.
- Note: `_start_gate` is at sweep.py:406, not 429+; 04-02 task 1 reads it there.
