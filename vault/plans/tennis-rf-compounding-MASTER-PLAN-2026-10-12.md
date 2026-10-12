---
covers: [tennis-rf-compounding, tennis-7day-frontier, whole-program-compression, semantic-factorization, w12-family-economics, w13-reuse-unit, job2-admission-gate, w8b-static-compounding, scale-readiness-gate]
tier: T2
status: awaiting-owner-capital-approval
date: 2026-10-12
extends: vault/plans/tennis-rf-optimization-MASTER-PLAN-2026-10-11.md
---

# Tennis RF -- Compounding Extension + 7-Day Frontier (TRF-C) -- Master Plan, 2026-10-12 (rev 2)

Rev 2 folds in the Owner's two amendment sets of 2026-10-12 (five corrections and the 7-Day Frontier).
Owner scope approval: "Aprobaría con estas cinco enmiendas ... sí me parece correcto aprobar y", then "more amendments, do them all".
Capital is applied ONLY by the Owner typing `approve` against the capital packet hash (capital_authority.py), never by the agent.

## 0. Programme goal (rev 2)
BUILD A RECONSTRUCTION FACTORY CAPABLE OF A 7-DAY TENNIS SCOPE B, THEN PROVE OR FALSIFY THAT TARGET BEFORE SCALING.
7 days is a hypothesis the system has to try to falsify. It is not a promise. Strategic question: what architecture
makes 1,797 outputs need only tens to hundreds of genuinely new cognitive decisions? Scope A/B execution stays unapproved.

## 1. Reality delta (read-only, 2026-10-12 ~17:40)
| Prompt claim | Verified | Source |
|---|---|---|
| HEAD e36b7506 | PP HEAD 9b5290e2 (W12 draw + packet) | git log |
| ~40.5M used / 14.45M left | 43,049,640 used / 11,950,360 left (open 518,315) | mission_spend goal-status |
| W11 DONE | 13 structs + prelude; 10/12 lint-clean; fn_8021EAA8, fn_8022F90C excluded UNK_FIELD | WU-W11-receipt.md |
| W12 waits on prep | Prep DONE on GEX44: +22 cited structs, 22/24 CLEAN, W11 outputs byte-identical, drill 9/9; commit 2ab62e70 in GEX44 clone. W12-PREP-READY.md not written; patch not in PP; laptop has only the W11 header | evidence/w12/W12-prep-receipt.md |
| GEX44 jobs | 2 of 4 used; job 3 = W12; job 4 = reserve | JOBS.md |
| Live tennis worker | none (last two missions HALTED) | gsd-mission-*.json |
| Laptop | 2,122 MB free / 32 GB, 37 claude.exe | CIM, Get-Process |
| 1,797 independent units | W7: 1,255 whole-function families (1,114 singletons = 62 %; 509 fns in families >=3); red-controlled; 167 (9.3 %) deterministic-eligible | WU-W7-receipt.md |
| no cost anatomy | W6: 321 calls / 13.09M, semantic 0 %, exploration 49.9 %, tax 27.0 %, duplication x14.06 | WU-W6-receipt.md |
| (new) free reuse data in W12 | 2 same-family pairs in the 24: fam 8 (36) fn_803315A0 + fn_80257978; fam 755 (35) fn_80278FEC + fn_8025C600 | draw x families.json |

## 2. Owner amendments (binding)
- A1. **No forced classification.** A role/label is written only when a deterministic check proves it; otherwise UNKNOWN. UNKNOWN is never a singleton, never zero.
- A2. **Multi-resolution reuse.** Compounding is not only whole-function families. Every function is indexed at six resolutions: exact-reconstruction family, structural family (CFG/memory/call shape), data family (structs/fields touched), compiler-idiom family, proof family (same verifiable obligations), semantic motif (reusable fragment). A whole-function singleton can still have low residual novelty.
- A3. **Knowledge Shock of the 22 W12-prep structs is measured.** How many of the 1,797 the 35 cited structs (13 W11 + 22 prep) newly make lint-clean / m2c-clean, from a corpus-wide before/after lint. First real Knowledge Leverage Ratio = functions unblocked per M tokens of the prep.
- A4. **Scale Readiness is three-level evidence**, not one ratio (section 6). 0.6x is an indicative target only.
- A5. **W14 automation gate:** rule/pattern derived on learning members -> passes on >=1 held-out member not used to derive it -> verifier (GEX44 judge) confirms -> repair rate not up -> model escalation measurably down. Only then VALIDATED -> COMPILABLE.
- A6. **Semantic Novelty Residual per function:** known architecture + known structs/fields + known idioms + known family/motifs + inherited proof + instance-specific facts. Target metric replacing tokens/function: **tokens per novel semantic obligation resolved.**
- A7. **W13's question:** which reuse unit best explains the fall in marginal cost (whole-function family, structural motif, type knowledge, compiler idiom, proof family, or a combination)? This protects the factory from overfitting to W7's clustering.
- A8. **Authority is not demand.** Runtime grants small leases per unit. Job 5 does not exist economically until W13 is admitted; job 6 not until W14 is admitted. Job 4 stays recovery reserve.

## 3. Owner map
| Capability | Class | Owner / note |
|---|---|---|
| Recon Factory | EXTEND | wt_tennis_rf `tools/wros/binary/decomp` (router, levels, admission, struct_producer, sem_producer, object_graph, l1_taxonomy, donors) |
| Function Family system | EXTEND | `evidence/w7/families.py`, `measure/families.json` -> six-resolution index (A2) |
| Semantic Reconstruction Graph | CONNECT | object_graph.py + families + facts index; no new ontology; a node needs a scheduler/proof/reuse consumer |
| Graphify | NO_WORK | PP knowledge locator |
| Reconstruction IR | PARTIAL / deferred | m2c + certified header + producers = de-facto IR; the P1 facts file is the minimum projection; nothing beyond it until W13 shows a consumer |
| Compiler Idiom Library | IMPLEMENT (small) | seed: struct-ptr stride, ptmf r12 drop (W12-prep); source_lint rules + KNOWLEDGE rows with toolchain applicability + invalidators |
| Theorem cache / proof | EXTEND | header field citations = offset theorems; judge verdicts = instance proof; proof family = shared obligation sets |
| Proof-Carrying Recon | EXTEND | `measure/records.jsonl` row = dossier |
| Hypothesis store (Semantic Superposition) | IMPLEMENT (minimal) | per unresolved field/type: competing hypotheses + dependents; cognition picks the best discriminator |
| Active Learning / Tech Capital Allocator | PLAN -> EXECUTION after W12 | rank questions by dependents unblocked / est. cost; reuse capital_authority, no new allocator |
| Resource scheduler / PRR | CONNECT | pp-prr owner; read-only claude.exe classification, no kills |
| m2c / DTK / Ghidra | ACTIVE | unchanged |
| CCR / UTVM | CONNECT | workers inherit CCR runtime |
| Knowledge Vault / UKDL / CBR | EXTEND | `vault/knowledge_base/tennis_rf/` |

## 4. Five-pass factory (7-Day Frontier architecture)
- **Pass 1 Whole-program extraction** (deterministic, GEX44, zero model): for all 1,797 functions, call graph, CFG fingerprint, field accesses (struct+offset), globals, constants, helper signatures, compiler-motif hits, m2c features, state-transition candidates. Output `measure/facts.jsonl` (the minimum IR projection).
- **Pass 2 Semantic factorization** (deterministic): factor into global facts / subsystem facts / six-resolution families and motifs / instance parameters / true exceptions; residual-novelty estimate per function (A6); **blocker index** = each unresolved field/type/helper with the count of functions it blocks; knowledge-shock ranking. "Tennis must teach us how Tennis was written."
- **Pass 3 Strategic cognition**: the model is asked discriminating questions ("which hypothesis explains these 146 functions", "what is the field blocking 73"), ranked by expected unlock per cost, never "reconstruct function X" when a question resolves more.
- **Pass 4 Batch synthesis**: the answer is compiled into the header / idiom rules / family template and applied to all dependents.
- **Pass 5 Deterministic verification** on GEX44 in batches with backpressure; only misses return to the model, each one capitalised (counterexample -> hypothesis/idiom/classifier update).

## 5. Units (mode, order)
| Unit | Mode | Content | Machine |
|---|---|---|---|
| C0 | EXEC | confirm no other W12 owner; land GEX44 prep patch as `patches/W12-prep-1.patch`; apply in wt_tennis_rf; laptop TENNIS_CONTEXT_DRILL; write W12-PREP-READY.md | laptop (light) |
| C1 | EXEC | prerequisite admission gate in stage.py build: unit context sha == certified header sha, zero `?`, lint CLEAN; RED = replay job 2's 26 units -> 26 refused; GREEN on W12 | laptop |
| P1 | EXEC | Pass 1 over 1,797 + A1 deterministic roles (thunk/tail-call, accessor, ctor/dtor shape, SDK range, unreachable; else UNKNOWN) | GEX44 |
| P2 | EXEC | Pass 2 factorization, six-resolution index, residual novelty, blocker index, hypothesis store; A3 corpus-wide Knowledge Shock of the 35 structs | GEX44 |
| W12 | EXEC | as packeted + per-function records: family ids at six resolutions, ordinal, structs reused, residual novelty, wall_s per stage, model calls, tokens (dedup message.id), novel obligations resolved, failure capital. GEX44 job 3 | laptop send / GEX44 |
| W12a | EXEC | first vs second instance (fam 8, fam 755); model-needed fraction; W6 ledger on W12 sessions; tokens per novel obligation; stop-loss check | either |
| W13 | PLAN -> EXEC | A7 reuse-unit experiment: 2-3 families + 2-3 motif groups with a verified first member, ordinals 1/2/4/8, ~6 out-of-group controls; plus Pass 3 strategic questions on the top blocker-index items (knowledge shock); job 5 | GEX44 |
| W14 | conditional | A5 gate; batch synthesis (Pass 4) of one mature family/motif + Pass 5 verification; job 6 | GEX44 |
| W8b+ | EXEC | STATIC / COMPOUNDING / NAMED-BREAKTHROUGH forecasts; 7-Day Frontier distance table; Scale Readiness verdict | laptop |
| K | EXEC | KNOWLEDGE, negative knowledge, FIOS, UKDL, CBR, HANDOFF | laptop |

## 6. Scale Readiness Gate (all three levels, else NO_SCALE)
- **Family/motif level:** >=1 family or motif with a strong, reproducible marginal-cost fall that includes a held-out member (indicative: ordinal 4 <= 0.6x ordinal 1).
- **Cross-family level:** >=2 families/motifs/reuse units show reuse, curves may differ.
- **Programme level:** over the whole measured sample, model-needed fraction, proof reuse and marginal cognition fraction move the right way across W12 -> W13 -> W14.
- Plus: >=20 verified Tennis fns with measured tokens; zero prerequisite-class 0-of-N jobs since C1; no heavy laptop worker below the RAM floor; compiler discriminator (>=20 insns) confirmed.

## 7. 7-Day Frontier targets (indicative; W8b+ reports the distance to each)
| Property | 7-day target | 3-5-day target |
|---|---|---|
| Model-needed fraction | <= 20-30 % | <= 10-20 % |
| Autonomous/compiled reconstruction | >= 60-75 % | >= 80-90 % |
| Mature-instance cost vs first instance | <= 20-25 % | lower |
| Known-prerequisite job failures | ~0 | 0 |
| Verification | mostly deterministic | batch-mature |
| Resource stalls | ~0 | 0 |
| Marginal cognition | falling per batch | falling |
Throughput needed: 1,797 / 5 days ~ 360 verified fns/day. W8b+ also reports the measured verification throughput per GEX44 batch.
Research scenarios (labelled H, not forecasts): optimised current factory 3-6 weeks; compounding with frequent AI 10-20 days; strong recon compiler <= 30 % model-needed 5-10 days; <= 10-20 % model-needed 3-7 days; breakthrough 1-3 days of production. No evidence yet for any of them.

## 8. Token budget (processed; route sizes from route_admission PP 5983db9d: S 1.6M, M 3.5M)
| Item | P50 |
|---|---|
| C0 coordinator + ownership | 0.6M |
| C1 admission gate | 1.6M |
| P1 whole-program extraction + roles | 3.5M |
| P2 factorization + knowledge shock + hypothesis store | 3.5M |
| W12 (incl. instrumentation) | 3.5M |
| W12a analysis | 1.6M |
| W13 reuse-unit + strategic cognition | 3.5M |
| W14 batch synthesis (conditional) | 3.5M |
| W8b+ forecasts + frontier + gate | 1.6M |
| K knowledge / UKDL / CBR | 1.6M |
| control tax / residuals | 3.0M |
| **Total** | **~27.5M** |
Semantic lower bound (W12 + W8b) ~5.1M. LOWER 24M (no W14). P50 27.5M. P80 ~34M. P95 ~45M. Confidence LOW.
From live used 43.05M: ceilings P50 ~71M, P80 ~78M, **P95 90M**. Rev 1 asked 85M; Pass 1-3 push P95 past it.
Stop-loss 1: after W12a, if fewer than 5 of 22 verify -> NO_SCALE W8b, rest unspent.
Stop-loss 2: a unit settles above 1.5x its route target twice -> return to the Owner.
Stop-loss 3: P1/P2 find no reuse beyond W7 at any resolution -> skip W13 motif arm, go to W8b.

## 9. Resource budget
- GEX44: 2 used; job 3 = W12; job 4 = recovery reserve; job 5 = W13 (exists only on W13 admission); job 6 = W14 (only on W14 admission). Total authority 6. P1/P2 are CPU work in the GEX44 mission workspace, not oracle jobs.
- Laptop: 2.1 GB free; no heavy recon worker; coordinator, patch apply, certify, send, judge only. The 37 claude.exe are classified read-only via PRR; no kills.
- Concurrency: one GEX44 worker at a time + this coordinator.

## 10. Approval surface
Scope: approved by the Owner in chat (sections 2-6). Capital: packet `tennis-rf-compounding-2026-10-12` in
`~/.claude/state/capital-authority/packets/`; the Owner types `approve` (P80 ~78M) or `approve p95` (90M).
