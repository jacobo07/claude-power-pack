# S11H — S11 Institutional Harvest: plan proposal (coordinator, 2026-11-03)

Status: PROPOSED (awaiting Owner one-click). Inline copy presented in chat; this file is the canonical backup.

## Reality (measured 2026-11-03, read-only; H2 content not read)
- Denominator 1797 (t1 evidence/frontier/counters.json n). CERTIFIED_C 1086, CERTIFIED_CXX 9, cxx_receipts_overlapping_c [] -> unique 1095/1797 (re-derived independently in H0).
- States: COMPILES_NO_MATCH 204 (pct >=99: 10; 95-99: 2; 90-95: 19; <90: 173), NO_COMPILE 507.
- H2: manifest sha256 922f214e... intact; unread; unspent.
- fn_80222480 is CERTIFIED_CXX since S10b (hand fixture, IDENTIFIED:cxx/sd8). The 98.9 % is the raw-m2c regeneration used as OM-PR1 positive control. Closing it adds 0 to the product frontier.
- Six S11 CXX (fn_8020BA74, fn_8021B694, fn_80225200, fn_80225778, fn_8022E7A0, fn_8024BE58): ablation receipts exist (b5_dev.json attribution). Registry (vptr offset) necessary 6/6; callee-prototype propagation necessary 4/6 (3 through the same callee fn_80205EDC). Toolchain: 4 IDENTIFIED:cxx/sd8, 2 UNDERDETERMINED.
- Cohort blockers (dev 102 + old H 160, dev/replay only): m2c lift (NO_M2C_LIFT 27, M2C_ERROR 46), C compile errors, NOT_A_THIS_CALL 5, BELOW_SEARCH_MIN 27. Register-only residual observed on 1 control.
- S11 method_graph.json: 12 routes, 3 switches, per-epoch decisions: narrative JSON, not typed.
- Existing owners (t1 modules/recon_fabric): search_plan (Pareto plans, plateau, first Genome rule, supercompiled trajectories), microscope (solved-lineage hunks), compiler_causality (edit class -> pct moved), fingerprint (objdiff per-instruction rows, eq_regs, DIFF_ARG_MISMATCH), causal_diff, residual, build_twin, toolchain_sd, permute, maturity, cbr (CBR + Construction Return), atoms/claims (WROS), om, om_skeleton.
- PP: hold.blocker already typed (class, unblock_condition.kind); pivot_decision gates on reason text; no prompt-debt owner.
- Capital: mission m-f0b595fd509f token authority 60M, used 50.7M, left 9.3M. Campaign model USD $331.03 of $471.10 (left $140.07); S11 model USD $0 (b5 receipts). Open leases: none known (H0 verifies).
- Stale: S9 m-9f94bef51619 and S10 m-e6e0340e743d still RUNNING at checkpoint holds (spend 0) after their closeouts.
- t1: 1033 untracked generated files; no live t1 worker.

## Lanes and units (micro-commits; extend existing owners)
H (t1 worker, $0 model): H0 reconcile; H1 typed S11 Method Graph + step classes + trajectory compression; H2x six-CXX causal factorization (microscope over raw m2c -> ablated skeleton -> final unit); H3 C++ Genome v1 as atoms claims (vptr offset, slot signature, callee prototype; provenance, fixtures, counterexamples, scope); H4 Negative Search Memory as claims consulted by search_plan/permute before search.
R (allocator, gated): R0 residual normalization of fn_80222480 (first divergence, live ranges) + fan-out census of the 31 CNM >= 90 % via fingerprint (REG_ONLY vs other) -> institutional-value verdict. Only if >= 3 register-only near-misses: R1 natural experiments (certified corpus), R2 toolchain discriminators (build_twin sd0/sd8), R3 discriminating probes (each names its hypothesis), R4 inverse-rule candidate replayed on the near-miss set. Moratorium 6M tokens without lift -> freeze.
M: OM-PR maturity decomposition in maturity.py (release contract unchanged); leave-one-CXX-out sanity on dev (never held-out evidence).
S: Strategy Genome rule candidates from S11 in search_plan, replayed on >= 2 cases; fresh dev residual selects it (S11H-PR4).
P (PP, coordinator; canary then ff of the live GEX44 clone): P1 typed Method Failure Receipt (`checkpoint --receipt`), consumed by pivot_decision; P2 typed authority objects (may only ADD Owner requirement; regex stays as fallback); P3 Pivot Gen2 (early stop after 2 zero-delta receipts in one method class; extension past 3 to hard cap 5 only for distinct classes with evidence delta and authority left); P4 Owner-question compiler fields; P5 debt (D3 "Owner to waive X"; launch_cause "stopped").
K: Knowledge Vault incidents, UKDL (deduped), CBR via cbr.py, Construction Return, Prompt Debt registry (instruction -> mechanism -> gate -> fresh consumer).
U: upstream desk audit (decomp-toolkit, objdiff, decomp-permuter, m2c, register-allocation literature): decision matrix, no installs.

## Gates
S11H-PR1..5, RA-PR1..2 (always), RA-PR3..6 (only if R proceeds), PA2-PR1..5. H2 is not part of the done-gate.

## Budget (no new capital without this approval)
Worker tokens: low 12M / central 20M / high 30M (+5M contingency); allocator inside, capped by the 6M moratorium. Model USD: $0 central (deterministic), $10 ceiling. Coordinator lane P/K: ~3-5M session tokens, outside mission authority. Owner decision requested: m-f0b595fd509f authority 60M -> 80M (+20M), no top-ups.
