# S25 plan: maximize legitimate certifications (KSR + Tennis), PROPOSED 2026-11-11T13:50Z

Status: AWAITING OWNER APPROVAL. Nothing below is executed. Coordinator pane ddf4990e (laptop).

## Reality scan (measured 2026-11-11 13:46-13:50Z on GEX44)
- Mission m-97b5a3985b92 RUNNING, epoch 3, iterations 5. Record authority 62,459,318 processed; spent 17,137,271 (budget.md X2 row) -> ~45.3M left. Fresh 0 in S24X. USD 0.
  Lineage: m-f27c61b9e75c -> m-3f44ac4c922c -> m-97b5a3985b92 (2 of 3 renewals). Owner wall 2026-11-12T16:40Z; S24 stop rule 2026-11-11T20:00Z.
- Repos: t1-campaign `t1/campaign` f6d1a806 (S24X X2); gen3-pp `mission/gen3` f8546b10 (S24X 2/2 phases ticked). Laptop CPP efd51dd2.
- S24X COMPLETE. Coordinator re-ran both gates at f6d1a806: test_s24x_holes rc=0 S24X_X1_PASS (mutants red), test_s24x_probe rc=0 S24X_X2_PASS (mutants red, tree-sha catches a 1-byte write).
- KSR frontier (evidence/ksr-frontier/frontier.jsonl, recounted): 30,388 = CERTIFIED 8,687 / COMPILES_NO_MATCH 9,941 / NO_COMPILE 5,453 / FLAGS_SPLIT 3,447 / NO_TARGET 2,858 / XF_ERROR 2. Unchanged.
- Tennis (evidence/frontier/counters.json): columns CERTIFIED_C 1,139 and CERTIFIED_CXX 58 (never merged); cxx_receipts_overlapping_c = 3 fns; c_lane_receipts_via_cert_cxx = 1 fn; cxx_cert input has 62 rows. UNIQUE total is NOT yet derived: it is 1,139 + (CXX fns not in the C set), to be computed from function identities in W0, not by subtraction.

## S24X result (the decisive fact)
- 2,858 NO_TARGET -> 290 holes. 2,837 fns / 287 holes = CAPSULE_OMITTED_UNIT: the pinned capsule ships 304 of the 877 objects dtk v1.8.4 produces; its own config lists all 877. 8 DOL .init, 11 splitter unit without symbol, 2 unknown.
- dtk v1.8.4 re-split in a sandbox on the same DOL (sha1 7752caae...) reproduces all 877 objects byte-identically; the 304 shared ones equal the pinned ones.
- Probe of the 3 largest holes (1,758 fns), KSR lane's own transform/prelude/arms/judge: compiles in some arm 1,016; objdiff 100 % in some arm 463 (172+212+79). Sandbox identity, NOT certified, NOT counted. 284 smaller holes (1,079 fns) unprobed.
- sd0 vs sd8 arms disagree per object (e.g. 207 vs 212) -> per-object arm choice needed.

## Bottleneck hypotheses per population (each with its discriminating experiment)
| pop | n | hypothesis (H) | rival | smallest experiment | proof path | authority |
|---|---|---|---|---|---|---|
| NO_TARGET | 2,858 | stage assembly omitted 573 objects (S24X: supported) | - | build additive stage, run the existing lane sweep as its own generation | certify.py against a NEW stage identity -> Owner (Checkpoint C / R2 family) | stage build: plan approval; certification on it: Owner |
| FLAGS_SPLIT | 3,447 | arm disagreement within one object (sd0/sd8 small-data flags) resolvable by ONE recipe per object | per-function flags (inline/pragmas) | read ksr_lane FLAGS_SPLIT definition; group by object; test "one arm per object makes all its exact rows exact" | existing certifier if the recipe is the canonical ctx's arm | inside plan |
| NO_COMPILE | 5,453 (+Tennis 494) | few shared context blockers (missing types/protos per TU) | m2c output defects local to fns | cluster compiler first-error by (TU, message class); fix the top class in an ISOLATED ctx variant; measure NO_COMPILE->COMPILES | canonical ctx is never mutated; a variant world is not canonical | inside plan; promotion of a ctx change: Owner |
| COMPILES_NO_MATCH | 9,941 (+Tennis 164) | residual classes (regalloc/order/types) that O6 families partly cover | need per-fn search | residual-class census on a frozen sample before any search | existing certifier | inside plan |
| structural / cert | 141 local VALID; 0/16 canonical | refusal has a FIRST blocking condition shared by most of the 16 | each refusal distinct | refusal anatomy: run unchanged certify.py with a per-requirement trace on the 16 | - | read-only |

## Work units (EXECUTION mode; ULTRA only for a certifier-profile proposal)
W0 accounting (≤3M, 0 fresh): Tennis unique count from function identities (C set ∪ CXX set, overlaps listed) + gate with mutants (double-count, drop, relabel); KSR frontier gate pins receipts sha, not counts.
W1 additive stage (≤8M, 0 fresh, CPU): ksrmb-<new> = all 877 dtk v1.8.4 objects via the S24X sandbox recipe, new id, new path, never touching ksrmb-20261001-101754 / its 8,687 receipts / its sweep; run the lane sweep over the 2,837 omitted-unit fns as generation G-NT1 with its own frontier file. Report per stage transition: target-present / source / compiles / exact-in-arm / exact-in-canonical-arm. Gate test_s25_stage: pinned tree sha unchanged, 304 shared objects byte-identical, mutants (mutated object, pinned write, double-listed fn) red.
W2 FLAGS_SPLIT (≤6M, ≤0.2M fresh): definition read from ksr_lane; object-level arm census; pilot on a frozen 200-fn cohort drawn after freeze; pass = rows become exact under ONE recipe per object with recipe identity recorded.
W3 refusal anatomy (≤4M, 0 fresh): first blocking condition for each of the 16 S24 refusals + the 3 byte-contradicted rows get a versioned CONFLICT disposition (append-only history, no rewrite).
W4 NO_COMPILE shared blockers (≤8M, ≤0.3M fresh): first-error clustering for KSR+Tennis; one isolated-ctx repair of the largest cluster; measure transitions; canonical headers untouched.
W5 COMPILES_NO_MATCH census (≤5M, ≤0.3M fresh): residual-class census on frozen 300 sample; Tennis 55 never-fired: selector vs expressiveness split.
W6 knowledge (≤2M): UKDL traps T-CAPSULE-OMITS-SPLIT-OBJECTS-001, T-STATE-WITHOUT-CAUSE-001 (+ cause field proposal for frontier), family baseline judge, handoff.
Total ≤36M processed + 2M closeout, ≤0.8M fresh, USD 0, inside the remaining ~45M of the record.

## First-value gate
W1 green = the omitted-unit population has real target objects in a versioned stage and a measured exact-in-canonical-arm count. That is a Product Delta (targets acquired), NOT certifications.

## Stop rules / rollback
Stop at 38M processed, 0.8M fresh, or 2026-11-12T16:40Z (existing Owner wall), or when only Owner acts remain. Two failed pilots per lever -> retire lever. Rollback: every t1 change is a micro-commit; the new stage is a new directory (delete = rollback); pinned stage, receipts, certifier, ctx never written; `gsd_mission.py hold` restores the checkpoint; CPP_MISSION_AUTORESUME=off.

## Not authorized by this plan
Certifying anything against the new stage; any certifier or canonical-ctx change; R2/H2; receipt rewrites; push; paid/cloud; deploy to live CPP; budget beyond the record.

## Owner decisions
1. Approve S25 under m-97b5a3985b92 with the stop moved from 2026-11-11T20:00Z to the existing wall 2026-11-12T16:40Z (no new tokens)?
2. Approve W1 building the additive stage ksrmb-<new> (877 objects) as an experimental generation, no certification?
3. (Later, Checkpoint C) certifying against the new stage: stays deferred.
