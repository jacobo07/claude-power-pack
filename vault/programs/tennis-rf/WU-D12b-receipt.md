# WU-D12b receipt -- Status: DONE_WITH_LIMITS (test_d12b.py exit 0, 8/8; naive arm and job 4 NOT run)

Evidence: `evidence/d28/d12b/` (scaling.json, split_lbl_80513E74.json, arm2_hdr_e74_v1.h.json, arm2_e74_ladder.json, hdr_e74_v1.h, tools/pack.py arm2.py ladder.py test_d12b.py). Scaling verdict: **INSUFFICIENT**.

## Shared-residual arm (measured, GEX44, d5.run_set on all 91 dependents)
- Cluster family: global `lbl_80513E74` (C0004 + pointee clusters C0001, C0035, C0585, C4246), 91 dependents, seed 20261014, 45 pack / 46 held-out, disjoint. The layout fact (hdr_e74_v1.h: singleton struct, +0x0 vtable ptr, +0x100, +0x6A8, +0xA00 sub-object, +0xA4C byte) was written from pack-half accesses only.
- Newly lint-clean: **0/45 in-sample, 0/46 held-out**. m2c output changed in 87/91 fns (the fact is consumed). 1 new lint code (UNRESOLVED_TYPE) in each half.
- Held-out transfer: **YES in vars** (23/46 fns lose vars; 1285 -> 1221, 5.0%), **NO in lint-clean, NO ladder move** (0 fns with zero vars left; 0 of 91 had the cluster as sole blocker). In-sample 993 -> 921 (7.3%).
- Stop-loss FIRED (held-out lint-clean = 0): clusters 2 and 3 (C0039, C0038) not resolved.

## Not run, and why
- Naive arm (8 fns): the Tennis capsule `cap1-fee7b09f053d` fixes its 14 model targets (`capsule_profile.TENNIS_MODELS`, `expected_units` derived from it); 8 new targets need a capsule-profile edit and rebuild plus 8 hand-composed sources. Naive baseline = UNPRICED.
- Job 4: newly lint-clean batch is empty, so the bulk job would carry only the control. Not sent, JOBS.md row 4 records it (job 4 kept). No throughput, BAF, marginal-function, counterexample or donor figure is stated.

## Synthesis
- Joint delta (D12a): top bundles unlock 11-12 fns; one struct layout alone unlocks 0. Complementarity is in prototype+field bundles, not in a single layout.
- Motif mass 38.5% of class 2-5 insns, VALID idioms 6.1% of fns; search ABSENT; proof family UNKNOWN.
- Forecasts (plan s5): (1) naive upper baseline UNPRICED; (2) measured current Factory UNPRICED; (3) compounding UNPRICED; (4) 7-day and (5) 72-hour NOT REACHABLE on measured inputs, unchanged; (6) theoretical frontier 13,811 vars (96% private) vs 1,522 raw fns, structure not cost.
- W13: NOT ADMITTED, not armed, no jobs 8+ requested. Next abstraction to test before any scale request: a joint prototype+field bundle (D12a top bundles) propagated by D7 and composed with one layout fact, measured on held-out lint-clean.
- Tokens: no per-arm model tokens separated (the layout was written by the session; route accounting only).

## Plan delta
MDG shared-layout reuse: held-out var transfer 5.0%, lint-clean transfer 0. Model-needed fraction after propagation: UNPRICED. KV/UKDL: not written (single-cluster result, one confirmed pattern SHARED_LAYOUT_TRANSFERS_VARS_NOT_CLEANLINESS awaits a second cluster).