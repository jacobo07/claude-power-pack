---
status: AWAITING_OWNER (one decision, section 12)
date: 2026-10-14
program: gsdx-factory (Part C: Reconstruction Fabric)
goal: gsdx-factory-2
covers: [reconstruction-fabric, residual-compiler-lift, oracle-provider-contract, cross-title-homology, rea-d27-p0, cbr-reconstruction-birth, construction-return, d28-shadow-canary]
depends-on: [D28 tennis-rf chain (read-only donor), gsdx-factory/v2 (parked Part A), D27 backlog]
---

# GSD X Reconstruction Fabric -- Master Continuation Plan (gsdx-factory Part C)

Owner prompt 2026-10-14 (`/cpp-gsd-long`, "develop GSD X Reconstruction Fabric in parallel with D28").
This is an extension of gsdx-factory, not a new programme. Nothing is armed until section 12 is answered.

## 1. Reality Delta Scan (measured 2026-10-14 ~16:20 local)

| Fact | Value | Source |
|---|---|---|
| Live PP HEAD | `feature/knowledge-acquisition` 070673cc (gsdx-pcc chain P51->P11) | `git worktree list` |
| gsdx-factory | goal `gsdx-factory-2`, worktree `Apps\pp-gsdx-factory-2`, branch gsdx-factory/v2 cfa5d2d3, **75 commits ahead of live, branch-only**. PARKED 2026-10-10 (D26). Settled 8,817,916; **programme authority: none recorded** (`programme: null`) | `mission_spend.py programme-status --goal gsdx-factory-2` |
| gsdx-factory approved scope | v1 plan: Part A (econ G1..G5) + recon-factory to Phase 9, envelope 40M / hard 55M. Fabric scope is NOT in it | `vault/plans/gsdx-econ-recon-program-plan.md`, D26 |
| Branch-only Part A tools | `gsd_dossier`, `gsdx_obligation_extract`, `gsdx_l1_*`, `test_gsd_dispose` (obligation disposition = Proof of Non-Work v0), route_admission_expected | `git ls-tree` v2 minus live |
| cost-collapse/main | 37 commits ahead of live, last 2026-10-09; route_admission/gsd_dossier branch-only | `git rev-list` |
| CBR (tower) | `tower/constitutive-substrate` 0 ahead = fully in live; no `construction_return` / `reconstruction_birth` code anywhere in `modules/` | grep |
| D28 programme | goal tennis-rf: authority **150M**, settled **101,985,655**, executable 48,014,345, lease **L30**, open 0 | `programme-status --goal tennis-rf` |
| **D28 is STALLED (new finding)** | D9c worker m-e854ad27e947 HALTED (worker stopped 14:51, no receipt). From 15:01 the chain tick logs `refuse_envelope` every 10 min: chain.json `envelope: 100000000` < used 101.99M, need 3.5M. Authority was raised to 150M but the chain's own envelope was not | `~/.claude/state/trf-chain-tick.log`, `vault/programs/tennis-rf/chain.json` |
| D12a / D12b | queued after D9c, not started (route-S 1.6M / route-M 3.5M; D12b owns GEX44 job 4) | chain.json, `d12-factory-scaling-2026-10-13.md` |
| D28 GEX44 jobs | budget 7: used 1,2,3,5; job 4 reserved D12b; job 6 unused; job 7 reserved D9; jobs 8+ (W13) NOT approved | `vault/programs/tennis-rf/JOBS.md` |
| GEX44 now | 20 cores, load 2.5, 54 GB available, 849 GB disk free, 7 claude processes, 0 compiler/objdiff/Dolphin processes | ssh read-only probe |
| Laptop now | 4.9 GB free of 31.3 GB, 16 claude processes: **not safe for heavy work** | Win32_OperatingSystem |
| REA | W4 2026-10-11: REJECT on 6.3.0 (DOL + ELF32-PPC `target_unavailable`; JDK 17 < 21). D11 deferred, D27 P0 never run | `REA-DISPOSITION.md`, git log |

### What D28 already built (the Fabric's v0, Tennis-specific, in PP `vault/programs/tennis-rf/evidence/`)

| Capability | D28 artifact | State |
|---|---|---|
| Residual compiler + census + Distance-to-Autonomy | D3 `residual.py`, residuals.jsonl 1,797 rows, census.json, autonomy.json | DONE, test_d3 11/11 |
| Frontier / dominators | D4 `frontier.py`: 3,429 unresolved vars / 1,521 fns, 18 causal classes | **PARTIAL**: red control does not fall (degree-driven) |
| Single interventions | D5 cror (tool-side), D6 retraction | DONE: zero exact unlock; D6 retracted D5's survivor (variadic prototype) |
| Incremental invalidation | D7 dirty closure reproduces whole-corpus lint set byte-equal (5 variants) | DONE 8/8 |
| Knowledge shock | P1P2 header: lint-clean 175 -> 276 | sealed |
| Reuse without model | D8v2 arm B: 12/14 MATCH at O4p, 0 model calls/fn (vs W12 12/22 with model) | DONE |
| Scale verdict | D11 NO_SCALE (residual compiler has no rerun gate; Scope-B admission not met) | DONE |
| Hypergraph, joint delta, search scan, motif mass | D12a (planned) | NOT STARTED |
| Bulk verify, counterexample compression, naive vs shared arm | D12b (planned) | NOT STARTED |

### Iteration pass (iteracion-avanzada-universal, after Reality Delta)
- Premise false: "D9c is running". It is HALTED and the chain refuses on a stale envelope. CLASE 0/2: the stale
  Programme/Lease authority bug already listed in D28's negative knowledge recurs, this time in the chain's own copy of
  the envelope. Not the Fabric's to fix (section 7); reported to the Owner.
- Premise false: "the Fabric must build residuals, frontier, invalidation, joint delta". D28 already has v0 of four
  of them and D12 is designed to measure the rest. Building them again is the duplication the prompt forbids.
  The Fabric's job is to **lift proven D28 tools into a corpus-general owner, replay-gated against D28's own outputs**,
  and add only what no D28 unit owns: oracle-provider contract, cross-title homology, CBR Birth/Return, fresh-agent
  inheritance.
- Premise false: "gsdx-factory authority covers this". It has no programme capital and its approved scope excludes it.

## 2. Owner map

| Capability | Disposition | Owner after this plan |
|---|---|---|
| GSD X mission persistence (Ralph, chain tick, AMR) | ALREADY_DONE, reuse | gsd_mission + `gsdx_chain.py` (v2) |
| gsdx-factory | EXTEND (Part C) | goal gsdx-factory-2 |
| Part A parked units (AGMIN..PLAN-4) | stay PARKED; only PoNW disposition is CONNECTED (F6) | D26 |
| Proof of Non-Work | IMPLEMENTED_NOT_HOT_PATH (v2 `gsd_dispose`) -> CONNECT | F6 |
| Cost Collapse / route admission | branch-only; CONNECT read-only, no merge here | cost-collapse |
| ContextImage / CCR | CCR live (runtime installed 2026-10-11); reuse for worker context | CCR |
| CBR / tower families | ALREADY_DONE substrate; Birth/Return records IMPLEMENT (thin) | F7 |
| Graphify | reuse for discoverability (one coordinate per Fabric capability) | Graphify |
| FIOS / UKDL / KV | reuse | F9 |
| Goal / Economic / Resource Runtime | reuse (mission_spend, capital packets, admission) | existing |
| Residual compiler | D28 v0 -> EXTEND into `modules/recon_fabric/residual` | F1 |
| Incremental invalidation | D28 D7 -> EXTEND | F1 |
| Frontier allocator | D28 D4 PARTIAL -> lift with red control kept RED as negative knowledge | F1 |
| Hypergraph / joint delta / counterexample / bulk verify | D12a/b own the experiment -> lift only after their receipts | F5 |
| Family / motif machinery | P1P2 `factor.py`, `idioms.py`, D1d -> lift after D12a motif mass | F5 |
| Compiler search | D12a lane F (permuter scan) owns it | D12a, then F5 |
| Oracle providers | IMPLEMENT contract over existing adapters (DTK, m2c, stage.py compile+objdiff, Ghidra, REA) | F2 |
| Cross-title homology | IMPLEMENT (no owner exists) | F4 |
| REA / D11 / D27 | D27-P0 EXECUTION, provider stays unavailable unless proven | F3 |
| Tennis-RF object graph / records.jsonl | D28-owned, READ-ONLY | D28 |

## 3. Workstreams, mode, route, budget (M processed tokens)

Routes are D28-measured: route-S stops 1.6M, route-M stops 3.5M. D28 itself landed near its P95 (plan P50 25.5M,
actual ~38.7M from 63.3M to 102.0M), so the bands below use that overrun ratio, not the routes' face values.

| Unit | Scope | Mode | Route | Depends | P50 | P80 | P95 |
|---|---|---|---|---|---|---|---|
| F0 | This scan + plan + worktree/goal setup | EXECUTION | coordinator | -- | 0.6 | 0.8 | 1.0 |
| F1 | `modules/recon_fabric/` core: entity identity (binary sha256, section, addr, size, normalized-insn hash), residual + census + autonomy lifted from D3, dirty closure from D7, frontier from D4. Corpus-general, Tennis = first corpus | EXECUTION | M | F0 | 3.5 | 4.5 | 6.0 |
| F2 | Oracle-provider contract (target, evidence type, authority, cost, failure semantics, version) over existing adapters; REA declared, unavailable | EXECUTION | S | F1 | 1.6 | 2.0 | 2.6 |
| F3 | D27-P0: read current upstream REA release + docs; isolated-prefix probe on GEX44 only if a PPC/DOL lane is claimed | EXECUTION | S (cap 1.2) | -- (parallel) | 0.6 | 1.0 | 1.2 |
| F4 | Cross-title homology v0: SportsPackEP.dol vs Resort main.dol, EXACT / RELOCATED / NEAR / UNKNOWN on normalized insns + call neighbourhood; precision on W3b donors, shuffled red control | EXECUTION | M | F1 | 3.5 | 4.5 | 6.0 |
| F5 | Lift D12a/D12b tools (hypergraph, joint delta, motif mass, counterexample classes, bulk verify) into the module after their receipts; replay | EXECUTION | M | D12b receipt | 3.5 | 4.5 | 6.0 |
| F6 | Proof of Non-Work in front of recon units: connect v2 disposition to the Fabric census (ALREADY_SATISFIED / REUSE / DETERMINISTIC / MODEL_REQUIRED / UNKNOWN) | EXECUTION | S | F1 | 1.6 | 2.0 | 2.6 |
| F7 | CBR Reconstruction Birth + Construction Return records; fresh-process inheritance canary (no transcript, comparable target) | PLAN then EXECUTION | M | F1,F2,F6 | 3.5 | 4.5 | 6.0 |
| F8 | Economic + compounding canary (section 9), shadow-only | EXECUTION | S | F5,F7 | 1.6 | 2.0 | 2.6 |
| F9 | KV / FIOS / UKDL / CBR closeout | EXECUTION | S | all | 1.2 | 1.6 | 2.0 |
| -- | Coordinator tax (cap) | -- | -- | -- | 1.5 | 2.0 | 2.5 |
| -- | Recovery reserve (residual re-arms, breaker closeouts) | -- | -- | -- | 2.4 | 3.4 | 4.5 |
| | **Total** | | | | **24.9** | **31.8** | **41.0** |

Semantic lower bound ~9M (F1+F2+F4+F7 at face value, no residuals). Confidence: medium on F1/F2/F6/F9 (direct
analogues measured in D3/D7), low on F4 (no prior homology run) and F7 (no prior Birth/Return code).
**Requested hard authority: 45M** (P95 + 4M). Zero ULTRA-PLAN now; F7 has one PLAN step for the CBR contract. Entity
identity is decided here (F1 row) rather than escalated.

## 4. Resource budget

| Resource | D28 claim | Fabric claim |
|---|---|---|
| GEX44 compute jobs | 7 budgeted: 1,2,3,5 used; 4 = D12b; 6 unused; 7 = D9 | **0 jobs.** Fabric does not compile. Any later compile need = new Owner ask |
| GEX44 CPU (no job slot, like D5's m2c+lint) | D12a lanes 1-5 | F1/F4/F5 replays: <= 8 cores, nice 10, one at a time; yields when a D28 unit is RUNNING on the same host |
| GEX44 RAM | -- | <= 8 GB per replay (54 GB available now) |
| Model workers | 1 D28 worker at a time | 1 Fabric worker at a time, Sonnet, GEX44 clone. Never two Fabric workers |
| Laptop | -- | coordinator only (4.9 GB free); no Fabric worker, no replay on the laptop |
| Dolphin / hardware | none | none |
| REA probe | -- | GEX44 isolated prefix, <= 2 GB disk, removed after |

## 5. D28 non-interference contract

- READ-ONLY for the Fabric: `vault/programs/tennis-rf/**` (packets, receipts, chain.json, JOBS.md, evidence),
  `Apps\recon_work\wt_tennis_rf`, `recon_factory\`, GEX44 `M/out/d28/**`.
- The Fabric copies D28 outputs it replays into `modules/recon_fabric/fixtures/d28/` with the source sha256 pinned;
  it never edits them in place.
- Fabric-owned, mutable: branch `gsdx-factory/fabric` from live 070673cc, worktree `Apps\pp-gsdx-fabric`, GEX44
  clone `~/missions/gsdx-fabric`; `modules/recon_fabric/**`, `tools/test_recon_fabric*.py`,
  `vault/programs/gsdx-fabric/**`.
- Never: arm W13, use jobs 4/6/7, rewrite D9c/D12a/D12b packets, change chain.json, mark MATCH, write a D28 receipt.
- Commits: pathspec only, in the Fabric worktree. Landing into live = merge after F9 gates, never during a D28 unit's
  run on the same files (none are shared by design).
- Active integration into D28 (any Fabric code on D28's hot path) needs: deterministic tests, replay byte-equal to the
  D28 output it replaces, a held-out case, a named rollback, and the D28 coordinator's acceptance. Until then: shadow.

## 6. D28 shadow contract

Fabric may read D3/D4/D5/D6/D7/D8v2/D11 (and D12 when sealed) and compute: residual census re-derivation, shared
uncertainty grouping, alternative frontier ranking with the red control, Proof-of-Non-Work dispositions over the
1,797 rows, homology candidates for Tennis fns. Outputs go only to `vault/programs/gsdx-fabric/shadow/`, each labelled
SHADOW. A Fabric number that disagrees with a D28 receipt is a CLAIM_EVIDENCE_DIVERGENCE row, not a correction.

## 7. Finding handed to D28 (not Fabric-owned)

D28 has been stalled since 15:01 today: chain.json `envelope` is 100M while the programme authority is 150M, so the
tick refuses D9c's residual (need 3.5M). Fixing it means one field in D28's chain.json plus re-arming D9c's residual;
that belongs to the D28 coordinator under the 150M the Owner already approved. The Fabric does not touch it. Negative
knowledge for F9: a raised programme authority has to reach every copy of the cap (ledger, lease, chain envelope).
Otherwise the chain halts silently.

## 8. REA contract (F3)

ROI is positive now: <= 1.2M, no D28 resource, settles whether D11 can ever start. Result classes: AVAILABLE / PARTIAL /
TARGET_UNAVAILABLE / ENVIRONMENT_BLOCKED / UNKNOWN. Enabling REA as a provider needs, on SportsPackEP.dol and one DTK
`.o`: the tool's own admission output, a function list that agrees with DTK split boundaries on >= 95% of a seeded
sample, and xrefs that agree with DTK relocations on the same sample. Anything less keeps the provider unavailable.
Upstream changes need a separate ROI decision. F1..F9 never wait on F3.

## 9. Production canaries (highest information first)

1. **Replay canary (F1):** the lifted residual compiler reproduces D3's residuals.jsonl sha and D7's dirty-closure
   result byte-equal. It also adds the rerun gate D11 named as missing for Scope B.
2. **PoNW canary (F6):** dispositions over D3's 1,797 rows. Measures how many would-be units disappear before any
   worker exists. Control: the D8v2 arm-B 14 fns must come out REUSE/DETERMINISTIC, and the D6-retracted fn must not.
3. **Homology canary (F4):** the 3 W3b donors must classify EXACT/RELOCATED, and a shuffled-instruction control must not.
4. **Compounding replay (F8):** W12 (12/22 MATCH, one model call per non-MATCH fn) against D8v2 arm B (12/14, 0 model
   calls/fn). The question is whether the Fabric's reuse + PoNW path would have routed W12's fns to arm B's tier
   without the model. Historical, shadow only.
5. **Fresh-agent canary (F7):** a fresh worker with no transcript gets a comparable target and must find the census,
   negative knowledge (degree-rank fails, structural family fails, REA unavailable) and the Tennis header through
   institutional state alone.

## 10. CBR contract

Birth inputs: corpus binary identity, toolchain pins, available oracles (F2), applicable Fabric capabilities, each
with a disposition (INHERITED / ADAPTED / ALREADY_SATISFIED / NOT_APPLICABLE / CONFLICT / UNKNOWN), no omissions.
Return outputs: new or improved capability, negative knowledge, failed transfers, new oracle, obsolete capability.
Promotion to a tower family needs a held-out replay plus one consumer outside Tennis, or it stays a candidate.
Negative transfer (a capability that hurts a new corpus) is recorded as NOT_APPLICABLE with evidence, never deleted.

## 11. Done-gates mapped (31 master gates)

Gates 1-2 are met by sections 1-2. Gates 3, 4, 13, 14, 16 and 17 belong to F1 and F6. Gate 18 belongs to F4, gate 19
to F2 and gate 20 to F3. Gates 21-23 belong to F7, gates 24-25 to F8 and gates 28-31 to F9. Gates 5-12 and 15 are
proven by D12 first and lifted by F5. If D12 does not run, they close as "exact blocker proven: D12 not executed",
never as PASS. Gate 26 (non-interference) is checked at every unit: a Fabric replay never ran while a D28 unit held
GEX44 CPU. Gate 27: every claim is labelled PROVEN, SHADOW, SIMULATED or HYPOTHESIZED.

Micro-commits: one per unit slice (identity; residual lift; invalidation lift; frontier lift; provider contract; REA
disposition; homology; PoNW connect; Birth; Return; each canary; KV/UKDL).

## 12. Owner decision (the only one)

Approve gsdx-factory Part C (Reconstruction Fabric) under goal gsdx-factory-2 with **programme authority 45M**
(P50 24.9M / P80 31.8M / P95 41.0M), 0 GEX44 jobs, 1 Sonnet worker on GEX44, shadow-only toward D28. The Part A
units stay parked.

On approval: create the worktree and branch, declare the goal on that cwd, write the chain (F0 -> F1 -> {F2, F3, F4, F6}
-> F7 -> F5 (gated on D12b) -> F8 -> F9), and arm F1 and F3, with arm, envelope and admit in one call.
