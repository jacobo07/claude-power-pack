# WU-P1 -- Tennis closure pilot on the 9 PARTIALs through the router (CPU first), judged in GEX44 job 4

Plan: `vault/plans/recon-factory-locality-routing-2026-10-15.md` sections 4, 13, 14, 15 (Owner approved 2026-10-15 "y",
including reassignment of unused GEX44 job 4 to this batch; budget of 7 jobs unchanged; jobs 8+ NOT approved).
Requires WU-R2 (router, dossier, permute.py, admission) and WU-R1 (judge contract, --l0, supersede, control fixture).
Budget: <= 3.5M tokens; stop and write the receipt at 3.0M. CPU budget below; record cpu_s and wall for everything.

Sample: near_match.json's 9 PARTIAL. Routes (router decides; this is the expected plan, deviations recorded):
- 8021F8BC POINTER_STRIDE (1/34): deterministic fix of the pointee type/stride.
- 80253348 + 8032CF78 sda21_vs_ha_l: flag/section sweep (-sdata/-sdata2 thresholds, section attribute, presets incl O2).
  The O2 preset dimension also covers the D9 O2 arm: record D9 O2 as RETIRED_FOLDED with this result.
- 80254440 REGALLOC, 8022621C SIZE_-1, 80241018 bool_idiom: permuter (only if R2 ADMITTED), 20 min wall each, -j8, stall
  = no best-score gain in 5 min, max 3 runs at a time. Stop-loss: 0 score improvement on the first 3 runs -> permuter
  NO_GAIN for SOURCE_SEARCH, remaining permuter runs not started.
- T1 pairs: a winning change on A is applied UNCHANGED to its partner: (8022621C -> 80278FEC), (80241018 -> 802128D4),
  (80253348 <-> 8032CF78). Record T1 per pair as transferred/not, with the partner's verdict.
- 8021F3E4 PTMF_R12 (SEMANTIC): no CPU search; routed MODEL_PENDING (see step 5).

Steps:
1. Run the routes above (GEX44 CPU). Every attempt writes negative.jsonl on failure, priors.jsonl on a win
   (transform, class, family_key, scope FUNCTION; FAMILY only if its pair partner also wins).
2. Stage ONE candidate batch (GEX44 job 4): every improved source (best per fn) + the 2 control-fixture sources + 3 W3b
   donors. JOBS.md row 4 rewritten BEFORE send (purpose, unit count, Owner reassignment 2026-10-15). Then certify, send,
   wait (<= 540 s per wait), repatriate, judge with `--l0` = the batch L0 (env KSR_CAPSULE_PROFILE=tennis,
   MATCH_ACCEL_GEX44=C:\Users\User\Apps\recon_work\wst_tennis\w10\F).
3. Validity: donors 3/3 MATCH and the control fixture discriminates (correct MATCH, wrong-width non-MATCH). If either
   fails, the job is invalid: record and stop.
4. Classify each fn: MATCH / IMPROVED (objdiff up) / NO_CHANGE / REGRESSION / SEARCH_SPACE_EXHAUSTED / TOOL_INCOMPATIBLE.
5. Model sample gate: run a bounded model attempt (<= 3 fns, <= 1.2M tokens total, tiny context = the dossier only) ONLY
   if after step 4 a class with 0 CPU wins holds > 10% of the residual population (use D3/D12 residual class counts);
   otherwise record MODEL_NOT_ADMITTED with the numbers.
6. EVC table: per class and backend: attempts, closes (MATCH), cpu_s, wall, tokens (worker + its share of coordinator),
   EVC = total cost / MATCH (or "no close" with spend).

Limits: no capsule edit, no jobs beyond 4, no model calls except step 5.
Done-check: job 4 judged with valid donors+controls; receipt written; priors/negative files committed.
Receipt `WU-P1-receipt.md` (DONE / DONE_WITH_LIMITS / PARTIAL): per-fn table, T1 per pair, EVC table, D9 O2 disposition,
transforms that won and their scope.
