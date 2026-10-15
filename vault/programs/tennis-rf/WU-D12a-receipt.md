# WU-D12a receipt -- Status: DONE (test_d12a.py exit 0, 7/7)

Evidence: `evidence/d28/d12/` (struct_clusters.json, residuals_v1.jsonl, hypergraph.json, joint_delta.json, search_scan.json, motif_mass.json, tools/, hg_scan_*.txt). All curves are STRUCTURE, not cost.

## Bounds (hg_scan, reproduced)
Optimistic (offsets shared globally): 3962 vars / 13994 occ. Pessimistic (offsets private): 8274 offset vars.

## Base-identity collapse (step 1)
- Vars before: 8274 per-fn offset vars (13994 occ). Tier A (no call edges): 8145 distinct traced struct ids (1.6% collapse); tier B (call edges): 6379 but INCONCLUSIVE: width-conflict rate real_A 0.0033, real_B 0.0181, shuffled-edge control 0.0342, so the optimistic 3962 bound is NOT supported. 1665 offset vars have untraceable base (private `STRUCT:UNK...` ids). Conflict clusters: A 4, B 7 (kept).
- After collapse (residuals_v1, all var kinds, tier A): 13811 distinct vars over 1306 fns (16471 occ); private-var fraction 0.956; vars/fn p25/med/p75/p90/max 2/7/16/31/194; 46 fns have only shared vars; 532 components (largest 727, 506 singleton); 184 fns RESIDUAL_UNKNOWN (m2c var; never counted closed); 32 fns no named var.

## Closure curve (fns fully unblocked, vars resolved)
(50,31) (100,81) (200,181) (400,550) (600,1314) (800,2647) (1000,4928) (1200,8893) (1306,13811). Strongly convex: the tail costs most vars; no linear price per fn.

## Joint delta (step 3), D7 recompile
| bundle | size | targets | unlock | complementarity | hidden blockers |
|---|---|---|---|---|---|
| H801C7770+H801C9670 | 2 | 11 | 11 | 1 | none |
| +H801C83F4 | 3 | 12 | 12 | 2 | none |
| H801C7770+H801C83F4 | 2 | 6 | 6 | 1 | none |
| top-3 by EBU unlock 11/12/6; stop-loss not triggered. Others in joint_delta.json (several unlock 0, revealing 4-5 hidden-blocker fns; STRUCT:C3556+0x80 bundle unlock 1, reveals M2C unset-register blocker). | | | | | |
Controls: no-op unlock 0 byte-identical; D5 wrong-delta rejected (fewer GPR params than callee reads); matched-null bundle unlock 0.

## Search (step 4)
decomp-permuter ABSENT on GEX44 (/opt/ksr-decomp = dl ghidra jdk m2c venv). Install: `git clone https://github.com/simonlindholm/decomp-permuter && pip install -r decomp-permuter/requirements.txt` (not run). No runs on W12 PARTIAL / D2 near_match.

## Motif mass (step 5)
Classes 2-5: 1522 fns, 98706 insns; motif-covered 38.5%; VALID-idiom 6.1% (975 fns with an idiom). Proof family: all UNKNOWN in D3 certification (d1d structural_family real=926 INCONCLUSIVE). MODEL_NEEDED for family-level coverage.

## Ranked struct clusters for D12b (no conflict, GLB root, by n_fns)
C0004 (91 fns/202 acc), C0039 (59/106), C0038 (50/106), C0033 (48/108), C0114 (34/54), C0160 (33/43), C0129 (31/50), C0085 (30/65), C0155 (29/44), C0135 (25/48). 291 clusters carry width conflicts: resolve last.

## Plan delta
1. Base-identity collapse gives only 1.6% (tier A); call-edge merging is unreliable (conflict rate approaches the shuffled control). Do not price on the 3962 bound.
2. 95.6% of vars are private: the remainder scales near-linearly in the tail; the only cheap mass is the HELPER bundles (top 3 unlock 6-12 fns at 2-3 vars).
3. Prioritize HELPER bundles first, then GLB-root struct clusters above.