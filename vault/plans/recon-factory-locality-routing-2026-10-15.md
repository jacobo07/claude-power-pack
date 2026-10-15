---
covers: [recon-factory-routing, function-closure-router, transferability-gate, strategy-exhaustion, permuter-backend, tennis-rf-continuation]
status: PROPOSED (awaiting Owner approval, 2026-10-15)
parent: vault/plans/d12-factory-scaling-2026-10-13.md
---

# Reconstruction Factory: locality routing + tennis-rf continuation (Stage A then B)

## 1. tennis-rf reality (measured 2026-10-15 ~12:30)
- Goal tennis-rf: programme 150,000,000 (capital a14696400e97). Ledger settled 113,899,490; executable 36,100,510; open lease L39 (D12c, 1.28M), no open coordinator lease.
- **Unbooked coordinator spend:** pane 85b7c296 transcript = 26,890,074 processed / 151 calls (`mission_spend.py session-status`). Only 12,392,178 was ever settled (onto D9's L29). About **14.5M is off-ledger**. Real remaining is about **21.6M, not 36M**.
- Heads: PP 353780a7 (a gsdx-fabric chain is live in this tree; 1173 dirty paths from other writers). wt_tennis_rf ee16eab (21 dirty).
- D12a DONE 9907e830 (7/7), D12b DONE_WITH_LIMITS 6cf5bcb9 (8/8), D12c DONE_WITH_LIMITS 77e1cbf0 (10/10). All re-read, not re-run.
- Candidate ledger (`wst_tennis/w10/F/candidate_ledger.jsonl`): 136 rows, 39 entities, **15 exact MATCH** (12 W12 + 3 donors). D8v2's 12 MATCH exist only in `evidence/d28/d8/rejudge_l0.json`: the ledger is append-only with no supersede, so canonical MATCH is 15 and the evidenced count is 27. `cost` is null in 136/136 rows; `cpu_s` is present.
- The D2 near-match set is the same 9 W12 PARTIALs (`evidence/d28/d2/near_match.json`), not a separate sample.
- GEX44: 20 cores, 55 GB free, load ~2. `mwcceppc.exe` + wibo + objdiff-cli in each job's work/tools, `powerpc-linux-gnu-objdump`, devkitPPC, venv pip working. decomp-permuter absent.

## 2. D12a-c evidence matrix
| unit | intervention | measured | limit |
|---|---|---|---|
| D12a | base-identity collapse | 8274 -> 8145 vars (1.6%); call-edge merge conflict 1.8% vs shuffled 3.4% | 1665 untraceable bases get private ids (inflates "private") |
| D12a | helper bundles (D7 recompile) | B1 unlocks 11-12 = its own targets; controls OK | in-sample by construction |
| D12b | layout C0004, pack/held-out | lint-clean 0/45, 0/46; held-out vars -5.0% | lint-clean, not MATCH |
| D12c | B1 + layout + 2 bundles | held-out 0/46, other 0/45, complementarity 0; 2 UNRESOLVED_TYPE regressions | held-out overlaps top-10 bundle targets in 1/46; wrong-width control non-discriminative |
"95.6%" = `private_var_fraction` 0.9558 in hypergraph.json (vars seen in one fn), not a closure claim.

## 3. Transferability matrix
- **T0 same-target:** helper bundle POSITIVE (12/12 targets, reproduced). Layout T0 for lint-clean = 0 (0/45 pack). D9 source variants T0 = 0/31 MATCH.
- **T1 same-family cross-target:** layout family (C0004 dependents): vars +5%, closure 0/46. Helper family: **UNMEASURED** (1/46 overlap). Codegen-signature family: **UNMEASURED**, but natural pairs exist (below).
- **T2 broad:** 0/91, complementarity 0; Wilson 95% upper bound about 4%. Strong only for the tested helper/layout interventions.
- Regressions count against transfer: layout -2.

## 4. Locality-unit hypothesis
Closure is function-local for helper/layout facts (measured). Learning locality is hypothesised to be the **codegen-signature family**. The 9 PARTIALs fall into pairs with identical signatures:
- (8022621C, 80278FEC): SIZE_-1, missing `beq` at index 9, 22 vs 23
- (802128D4, 80241018): bool_idiom
- (80253348, 8032CF78): sda21 vs @ha/@l

Singletons: 80254440 REGALLOC 98.4% at O2, 8021F8BC POINTER_STRIDE 1/34, 8021F3E4 PTMF_R12. These pairs are a free T1 test: a fix found on A is applied unchanged to B.

## 5. Owner map (factory; D = wt_tennis_rf tools/wros/binary/decomp)
PRODUCTION:
- compile-in-loop (match.py, attempt.py, gex44/runner_lib)
- candidate gen (m2c_producer, donors, tennis_inputs)
- judge (gex44/candidate.py judge_tree/oracle2/audit)
- Tennis adapters (capsule_profile)

PARTIAL:
- router (D/router.py, Resort tiers)
- negative knowledge: misses are written to the ledger, nothing reads them
- priors (donors, d1d idioms)
- bench (Resort)
- family clustering

SHADOW / SPEC_ONLY: info-gain scheduler (D4 frontier, EBU), EVC for decomp.

MISSING:
- function dossier
- CPU/permutation search
- strategy exhaustion
- RECON/REA link

HOST_LIMITED: compiler archaeology (fixed presets).

## 6. Strategy-exhaustion gap
`gsdx_chain.decide()` returns `complete` (:416) or `residual_exhausted` -> "Owner decides" (:91, SILENT). No code compiles a next strategy. That is why the chain ended in an Owner question.

## 7. Function Closure Router (extend D/router.py, no parallel module)
Input: a function dossier (`dossier.py`: identity, current best source, target asm via L0 locator, preset, near-match signals, prior attempts from the ledger, family key). Classes, keyed by near_match `primary`:
- DETERMINISTIC_FIX (POINTER_STRIDE, known idiom)
- FLAG_SEARCH (sda21_vs_ha_l, preset-sensitive)
- SOURCE_SEARCH (REGALLOC, SIZE_±1, bool_idiom)
- SEMANTIC (PTMF_R12, unknown blockers, RESIDUAL_UNKNOWN)
- PROOF_ONLY

Each class has an ordered backend list. The pick is min EVC = expected cost / P(close), where P comes from per-class history (Laplace prior, Wilson-bounded). Every run writes back to the ledger. A class whose search exhausted with no win routes up a rung, never back into the same search (negative-knowledge read).

## 8. Backend ladder
Order:
1. deterministic rewrite
2. cached prior (family transform)
3. flag/preset sweep (CPU)
4. decomp-permuter (CPU, bounded)
5. model-assisted local closure (bounded, tiny context image)
6. deep RE escalation (returns a STOP verdict to the scheduler)

The order is a default. The router reorders by measured EVC per class.

## 9. Blind judge audit
`candidate.py` oracle receives obj bytes, symbol, entity and asm unit only (:516). Producer/variant/strategy/source are copied into the row as metadata after the verdict (:452). L0 is a **locator** (start, insns, bytes_sha256): it is REQUIRED and BENIGN, not leakage. The real defect is COUPLING: the profile is chosen by env var, and judging silently reads the profile L0, so held-out rows were refused (D8v2).
Fix:
- `judge_tree(..., l0_path=)` is mandatory for out-of-profile batches
- the judge contract is written down (may know / must not know)
- a test fails if `oracle()` gains a producer/source/arm argument or reads ledger metadata before the verdict
- a supersede row type so a rejudge enters the ledger (the D8v2 12 MATCH become canonical)

## 10. Negative control repair
Standard: a control is admitted only if the correct and incorrect arms are predicted to differ.

Fixture: a sealed MATCH donor (W3b) whose source reads a struct field. The correct width gives MATCH; u8->u32 at that field gives a non-MATCH diff. Both are judged in the same GEX44 batch.

The D12c wrong-width control is recorded as NON_DISCRIMINATIVE (not re-run).

## 11. Full-cost accounting
- **Now:** open lease `tennis-rf:coord-85b7c296` and `goal-settle --measured` this pane's unbooked about 14.5M in the same call, so it lands nowhere else (memory: goal-correct never unbooks).
- **Structural:**
  - the chain tick refuses to arm a unit while a goal-bound coordinator session has unbooked spend above 2M (reported as `coord_unbooked`), so attribution happens before the next unit, not after
  - experiment receipts carry worker + coordinator + retries + cpu_s + wall
  - ledger `cost` filled from the lease
- Restated cost of D12c: worker 1.28M plus the coordinator share, about 0.6M for the arming turns.

## 12. Search backend reality gate
decomp-permuter README: "supports MIPS ..., PowerPC, and ARM32"; ships `mwcceppc_compile_example.sh`; input dir = single-function .c, target .o, compile .sh, settings .toml; `-j` multithreaded; scoring = objdump diff, 0 = match. GEX44 has every dependency.

Install = git clone at a pinned commit + `pip install toml` (Levenshtein optional) into a separate venv `/opt/ksr-decomp/permuter-venv`. Classification: COMPATIBLE-PENDING-PILOT.

Admission test: on a sealed MATCH donor, permuter scores 0 at iteration 0 with our compile.sh and the target .o built from the DOL bytes. If not 0, the backend is TOOL_INCOMPATIBLE and is not used.

The permuter is a **generator only**. Its 0 score is never a verdict: winners go to the canonical judge.

## 13. Tennis pilot
- **Sample:** the 9 PARTIALs (8 after a cheapest-first split; 8032CF78 and 802128D4 keep their D9 negative knowledge as exclusions).
- **Arms:**
  - 8021F8BC: deterministic stride fix
  - (80253348, 8032CF78): flag/section sweep (-sdata/-sdata2 thresholds, presets incl. O2)
  - 80254440, 8022621C, 802128D4: permuter, 20 min wall, -j8, stall = no score gain in 5 min
  - then each winning transform applied unchanged to its pair partner (T1)
- **Judge:** one GEX44 job (job 4, unused) carrying all winners + 3 donors + the control fixture.
- **Stop-loss:** 0 improved after the first 3 permuter runs means permuter is classed NO_GAIN for SOURCE_SEARCH and the rest are not run.

## 14. CPU vs model decision
A model-assisted sample (≤3 fns, ≤1.5M) runs only if, after the pilot, a SEMANTIC/residual class exists whose CPU EVC is unbounded (0 wins) and that class's population share is above 10% of the residual. Compared on: verified closures, full cost (tokens + cpu_s × rate), wall, transfer of the found transform to its pair.

## 15. Priors and negative knowledge
`priors.jsonl` (wt_tennis_rf factory): {transform, class, signature, wins, tries, scope: FUNCTION/FAMILY/COMPILER, evidence job}.
- Promotion to FAMILY needs a win on its pair partner (T1 > 0). COMPILER scope needs 3 families.
- `negative.jsonl`: {fn, class, backend, search space digest, budget spent} is read by the router before scheduling.

## 16. Tennis continuation
1. Pilot (13).
2. Reprice the residual by class, from the class counts of the D3/D12 residual rows × pilot EVC per class.
3. If a positive-EVC class exists inside the remaining capital, the chain gets compiled units for that class (bounded batches).
4. Otherwise tennis-rf closes with a terminal economic verdict.

D9 O2: folded into the flag sweep as one preset dimension (cost ~0) and retired as a separate arm. Remaining 7 D12 bundles: retired (negative.jsonl entry, reason flat T2).

## 17. Mode by workstream
- EXECUTION for everything below.
- PLAN mode only for router class semantics if the pilot contradicts section 7.
- No ULTRA-PLAN: owners exist, and the gaps are wiring.

## 18. Micro-commits (pathspec; PP tree is shared with a live chain)
- A1: D12 negative knowledge + T-matrix (vault)
- A2: coord lease reconcile + chain `coord_unbooked` guard + test
- A3: strategy exhaustion in gsdx_chain (`complete`/`residual_exhausted` with `strategy.json` -> emit transition packet + arm a compiled unit if admitted) + tests
- A4: dossier.py + router classes + tests
- A5: judge contract + l0_path mandatory + supersede row + leakage test
- A6: control fixture
- A7: permuter adapter (gex44/permute.py) + admission test
- B1: pilot run + job 4 + receipts
- B2: priors/negative caches populated
- B3: repricing + next units
- K: KV/FIOS/UKDL/CBR

## 19. Token budget (processed tokens, ledger unit; this scan ≈3M of coordinator spend, inside 11)
**Envelope A, factory:**
| item | P50 |
|---|---|
| D12 institutionalization | 0.4 |
| T-matrix | 0.3 |
| coord reconcile + guard | 0.8 |
| strategy exhaustion/compiler | 1.5 |
| dossier + router | 1.6 |
| judge contract/supersede | 0.9 |
| control fixture | 0.4 |
| permuter adapter + admission | 1.2 |
| KV/FIOS/UKDL/CBR | 0.6 |
| iteration passes | 0.4 |
| recovery reserve | 0.7 |
| meta tax | 0.5 |
| **total** | **9.3** |

Lower bound 5.5, lower 7, P50 9.3, P80 11, P95 13. **Hard 11M.** Confidence medium.

**Envelope B, Tennis:**
| item | P50 |
|---|---|
| pilot orchestration | 1.2 |
| permuter/flag CPU (0 tokens, cpu_s recorded) | 0 |
| job 4 judge | 0.3 |
| prior harvest + T1 pairs | 0.6 |
| model sample if admitted | 1.0 |
| D9 O2 fold | 0.1 |
| repricing | 0.6 |
| first class batch if admitted | 1.5 |
| reserve | 0.5 |
| **total** | **5.8** |

Lower bound 2.5, lower 3.5, P50 5.8, P80 7.5, P95 9. **Hard 8M.** Confidence low-medium (permuter yield unknown).

Combined hard 19M against about 21.6M real remaining after reconciliation. No new capital.

## 20. Authority
Within tennis-rf 150M. Two items need the Owner:
- (a) charging PP-global CAPEX (A2, A3: about 2.3M) to tennis-rf as its canary
- (b) reassigning unused GEX44 job 4 from D12 to the pilot judge batch (JOBS.md budget stays 7)

## 21. Approval surface: see the chat message of 2026-10-15 (the same text).
