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
| F1 | `modules/recon_fabric/` core: ingest Tennis (existing DTK split) into a Fabric-owned WROS DB as a `dtk` run (identity = WROS `bin_entities`, s13), then lift D3 residual + census + autonomy, D7 dirty closure and D4 frontier onto those entities. Corpus-general, Tennis = first corpus | EXECUTION | M | F0 | 3.5 | 4.5 | 6.0 |
| F2 | Oracle Provider Contract = EXTEND WROS `bin_runs.backend` with a provider capability record (format / arch / endian / loader / ops / host / env, each scoped) + typed failure semantics + provider health; REA-absent independence test (s13) | EXECUTION | S | F1 | 1.5 | 2.0 | 2.5 |
| F3a | D27-P0 upstream disposition: finalize the s13 scan as a scoped, self-invalidating capability record (version, target, host, date, invalidators) | EXECUTION | coordinator | -- | 0.3 | 0.4 | 0.5 |
| F3b | Ghidra-direct canary on GEX44: pinned install of Ghidra 12.1.2 + GameCubeLoader 12.1 (hashes from the laptop copy), headless import of SportsPackEP.dol, export functions / calls / xrefs, ingest as a WROS `ghidra` run, substitution test against the DTK boundaries | EXECUTION | S | F2 | 1.0 | 1.4 | 1.8 |
| F3c | REA canary (only if F3b passes): user-local Node 22 + rea-agents (pinned) on GEX44, DOL -> ELF32 ET_EXEC bridge (ours, no fork), `REA_GHIDRA_LANGUAGE_ID=PowerPC:BE:32:Gekko_Broadway`; one receipt per capability; economic adoption gate | EXECUTION | S | F3b | 0.8 | 1.1 | 1.5 |
| F4 | Cross-title homology v0: lift W3 step0's exact-shape comparison (408 / 1,797 already measured) onto WROS entities, add RELOCATED / NEAR / UNKNOWN + call neighbourhood; precision on W3b donors, shuffled red control | EXECUTION | M | F1 | 2.0 | 2.8 | 3.5 |
| F5 | Lift D12a/D12b tools (hypergraph, joint delta, motif mass, counterexample classes, bulk verify) into the module after their receipts; replay | EXECUTION | M | D12b receipt | 3.5 | 4.5 | 6.0 |
| F6 | Proof of Non-Work in front of recon units: connect v2 disposition to the Fabric census (ALREADY_SATISFIED / REUSE / DETERMINISTIC / MODEL_REQUIRED / UNKNOWN) | EXECUTION | S | F1 | 1.6 | 2.0 | 2.6 |
| F7 | CBR Reconstruction Birth + Construction Return records; fresh-process inheritance canary (no transcript, comparable target) | PLAN then EXECUTION | M | F1,F2,F6 | 3.5 | 4.5 | 6.0 |
| F8 | Economic + compounding canary (section 9), shadow-only | EXECUTION | S | F5,F7 | 1.6 | 2.0 | 2.6 |
| F9 | KV / FIOS / UKDL / CBR closeout | EXECUTION | S | all | 1.2 | 1.6 | 2.0 |
| -- | Coordinator tax (cap) | -- | -- | -- | 1.5 | 2.0 | 2.5 |
| -- | Recovery reserve (residual re-arms, breaker closeouts) | -- | -- | -- | 2.4 | 3.4 | 4.5 |
| | **Total** (rev 2 with the s13 addendum; rev 1 was 24.9 / 31.8 / 41.0) | | | | **25.0** | **33.0** | **43.0** |

Semantic lower bound ~9M (F1+F2+F4+F7 at face value, no residuals). Confidence: medium on F1/F2/F6/F9 (direct
analogues measured in D3/D7), low on F3b/F3c (first Tennis Ghidra import, first REA PPC run) and F7 (no prior
Birth/Return code). F4 shrank because W3 step0 already measured exact shapes.
**Ceiling = P95 43.0M of new spend** (Owner chose P95 on rev 1 = 41.0M; rev 2 moves P95 by +2.0M). Zero ULTRA-PLAN;
F7 has one PLAN step for the CBR contract. Entity identity is NOT minted here: it is WROS `bin_entities`
(artifact, section, start, generation), which already exists (s13).

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

## 12. Owner decision (the only one, consolidated with the s13 addendum)

Approve gsdx-factory Part C (Reconstruction Fabric) under goal gsdx-factory-2 at **P95 = 43.0M of new spend**
(programme ceiling 51,817,916 = settled 8,817,916 + 43,000,000; P50 25.0M / P80 33.0M), 0 GEX44 compute jobs,
1 Sonnet worker on GEX44, shadow-only toward D28. The Part A units stay parked. This includes the F3b/F3c installs
on GEX44 (Ghidra 12.1.2 + GameCubeLoader 12.1, user-local Node 22 + rea-agents), each behind the s13 supply-chain gate.
Packet rev 1 (55d12633, 49.8M) is withdrawn from pending and replaced by the rev 2 packet.

On approval: create the worktree and branch, declare the goal on that cwd, write the chain
(F0 -> F1 -> {F2, F3a, F4, F6} -> F3b -> F3c -> F7 -> F5 (gated on D12b) -> F8 -> F9), and arm F1, with arm,
envelope and admit in one call. F3a is coordinator work, done in the same session.

## 13. Addendum 2026-10-14: oracle capability over oracle product (merged into F2/F3)

### Reality Delta (measured 2026-10-14 ~17:00 local)

| Fact | Value | Source |
|---|---|---|
| REA latest release | **rea-agents v6.5.0, released 2026-10-14** (6.4.0 on 10-11, 6.3.0 on 10-09). The W4 REJECT was measured on 6.3.0 and is stale as the "current" result | github.com/morluto/rea/releases |
| REA PowerPC lane | `docs/ghidra-ppc.md`: admits **ELF32 EM_PPC big-endian ET_EXEC**, default `PowerPC:BE:32:default`, override `REA_GHIDRA_LANGUAGE_ID` admitted against the installed Ghidra catalog. Refuses ELF64, LE, **ET_REL / shared** (so DTK split `.o` files stay refused), EF_PPC_EMB. Verified on a 750-family fixture | upstream doc |
| REA DOL | **Not supported.** It is Milestone 2 of issue #1741 (OPEN, P3): DOL header, Gekko/Broadway language, SDA base | issue #1741 |
| Milestone 1 commit | `c86b09a` (2026-10-13, PR #1747). Which release ships it: **UNKNOWN** (it falls between 6.4.0 and 6.5.0; verify in the published tarball, F3c step 1) | issue #1741 |
| REA raw binary | caller-selected CPU family limited to x86 / x86_64 / arm / arm64 / 6502, **little-endian only**, one mapping at one address (no DOL multi-section map). Not a PPC path | `docs/raw-binary.md` |
| REA host scope | the PPC lane is **Linux/macOS only**; Windows Ghidra P0 is PE x86/x86-64 (+ raw 6502). On this laptop, REA PPC = TARGET_UNAVAILABLE by host, independent of JDK | `docs/ghidra-ppc.md`, `docs/raw-binary.md` |
| REA Node requirement | Node 22.19+ / 24.11+ / 26+. **GEX44 has Node v18.19.1** -> ENVIRONMENT_BLOCKED on GEX44 until a user-local Node is supplied | README, `node -v` on GEX44 |
| JDK | Laptop now has `Apps\jdk-21` beside jdk-17 (W4's blocker was JAVA_HOME = 17: an ENVIRONMENT failure, misfiled at the time as part of a target REJECT). GEX44 has OpenJDK 21.0.12 | `ls`, `java -version` |
| Ghidra | Laptop: Ghidra 12.1.2 + **GameCubeLoader 12.1** (Cuyler, Apache-2.0, jar sha256 803D7A3C...EF53) giving the DOL/REL loader and `PowerPC:BE:32:Gekko_Broadway`; stock Ghidra has no Gekko id. Existing project RZTP01_PAL (Resort) + scripts DumpLoaderXrefs / FindSDA. **GEX44: no Ghidra installed** | `extension.properties`, ldefs, `ls` |
| Existing provider substrate | WROS binary extension (KEOS-DTK M1, `tools/wros/binary/schema_ext.sql`): `bin_runs` (content-derived run_id over tool + input + config + output, `backend` dtk / ghidra / ea_xref, tool_identity, config_sha256, output_digest), `bin_entities` (canonical identity, generation, ACTIVE / CLOSED), `bin_observations`, `bin_aliases` (trust classes incl. REFUTED), `bin_lineage` (RESIZE / SPLIT / MERGE). `levels.py` already runs two producers (ghidra, m2c) with `abi_compare == AGREE` consensus. Used for Resort; **Tennis was never ingested** | read |
| Cross-title shape evidence | W3 step0: 408 / 1,797 Tennis fns have an EXACT Resort shape, 166 loose | `TENNIS-TOOLCHAIN.md` |
| GitHub MCP | 401 Bad credentials (public pages used instead) | tool error |

### Iteration pass (after Reality Delta)
- Premise false: "the old 6.3.0 REJECT is the current REA result" (CLASE 2). Two releases later, REA has a PPC BE ELF
  lane. DOL is still absent, and so are relocatable objects.
- Premise false: "F2 builds an oracle contract". WROS already holds identity, provenance, run reuse, aliases,
  lineage and two-producer consensus. F2 adds only the missing **capability record + typed failures + health**.
- Misfiled in W4: JDK 17 < 21 was an ENVIRONMENT_PREREQUISITE recorded inside a target REJECT. Kept as negative
  knowledge (TARGET_UNSUPPORTED / ENVIRONMENT conflation).

### F2: Oracle Provider Contract (extend WROS, no new store)
New table `bin_provider_caps` (additive, like `schema_ext.sql`): provider, version, host_os, capability
(one of: dol_load, rel_load, elf32_ppc_exec, elf32_ppc_rel, raw_bin, ppc_be_decode, gekko_paired_single,
section_map, relocations, functions, cfg, calls, xrefs, data_refs, strings, types, decompile, headless,
evidence_export), status (AVAILABLE / PARTIAL / TARGET_UNAVAILABLE / ENVIRONMENT_BLOCKED / DEGRADED /
SUPERSEDED / ECONOMICALLY_INFERIOR / UNKNOWN), evidence (receipt path or run_id), measured_at, invalidators
(version change, host change, upstream release). Failures on `bin_runs` get a typed class: FORMAT_UNSUPPORTED,
ARCH_UNSUPPORTED, ENDIANNESS_UNSUPPORTED, ENVIRONMENT_PREREQUISITE, PROVIDER_STARTUP_FAILURE, ANALYSIS_FAILURE,
TIMEOUT, RESOURCE_LIMIT, INVALID_OUTPUT, UNKNOWN. Health (configured / healthy / unhealthy) stays separate from
capability. Normalization = existing `bin_observations` + `bin_aliases`. Conflicts between providers become WROS
claims with the existing REFUTED trust, never an average. Selection: cheapest provider whose cap row is
AVAILABLE for the obligation; an existing `bin_runs` row with the same run_id is reused (read once / singleflight
by content). No provider SDK until two real adapters show the same shape (DTK + Ghidra will be the first two).

**Independence test (mandatory, F2 done-gate):** with every REA cap row removed, the Tennis obligations
{section_map, functions, calls, xrefs, relocations} resolve through DTK (+ Ghidra after F3b). A test drives the
red branch: also remove DTK, and the same query must return a typed blocker, not an empty success.

### Capability matrix (initial, to be proven per row)

| Capability | DTK | m2c | Ghidra 12.1.2 + GameCubeLoader | REA 6.5.0 | compiler + objdiff |
|---|---|---|---|---|---|
| DOL load / section map | AVAILABLE (Tennis split, step0) | -- | UNKNOWN on Tennis (works on Resort) | TARGET_UNAVAILABLE (M2 open) | -- |
| REL load | AVAILABLE | -- | UNKNOWN (loader claims it) | TARGET_UNAVAILABLE | -- |
| ELF32 PPC ET_EXEC | -- | -- | AVAILABLE (stock) | PARTIAL: Linux/macOS only; release UNKNOWN | -- |
| ELF32 PPC ET_REL (DTK `.o`) | produces | consumes | AVAILABLE | TARGET_UNAVAILABLE | consumes |
| Gekko paired-single decode | UNKNOWN | -- | AVAILABLE (Gekko_Broadway id) | UNKNOWN (catalog override untested) | -- |
| functions / boundaries | AVAILABLE | -- | UNKNOWN on Tennis | UNKNOWN | -- |
| calls / xrefs / relocations | AVAILABLE (relocs) | -- | UNKNOWN on Tennis | calls verified upstream; xrefs not stated | -- |
| decompile | -- | AVAILABLE (per fn) | AVAILABLE | AVAILABLE (upstream fixture) | -- |
| equivalence proof | -- | -- | -- | -- | AVAILABLE (GEX44 jobs) |
| headless on Windows laptop | yes | yes | yes | PPC: TARGET_UNAVAILABLE by host | GEX44 only |
| headless on GEX44 | yes | yes | ENVIRONMENT_BLOCKED (not installed) | ENVIRONMENT_BLOCKED (Node 18) | yes |

### F3: D27-P0 as capability discovery
- **F3a (done in this scan, sealed in the record):** upstream reality above. Minimum delta from the current Wii path
  to "REA as a Tennis provider" = **PROVIDER_BRIDGE + ENVIRONMENT_ONLY**: a DOL -> ELF32 ET_EXEC wrapper
  (one PT_LOAD per DOL text/data section, entry from the header; ours, ~100 lines, no REA fork), the Gekko language via
  `REA_GHIDRA_LANGUAGE_ID` (admitted only if the catalog includes GameCubeLoader's id), a Linux host, Node 22.
  Not upstream work. Branch: **B (small delta, our side)**, pending F3c's economic gate.
- **F3b:** Ghidra-direct on Tennis, headless on GEX44. Each capability (dol_load, section_map, functions, calls,
  xrefs, gekko decode) gets its own receipt, compared with DTK boundaries as a substitution test (agreement %,
  conflicts listed, CPU / RAM / wall time). Opening the file proves only dol_load.
- **F3c:** REA on the same artifact through the bridge. Adoption needs REA to beat or match F3b on at least one
  obligation **and** to lower a measured cost (latency, normalization code, model context, proof cost). Otherwise
  the disposition is ECONOMICALLY_INFERIOR, recorded and inactive, with no architectural loss. If 6.5.0's tarball
  does not contain the PPC lane: TARGET_UNAVAILABLE (version-scoped) and F3c stops.
- **Upstream opportunity:** only as a packet (missing capability = DOL loader, M2 of #1741; patch surface; acceptance
  odds; maintenance; alternative cost = Ghidra-direct, already working). No fork.
- **Freshness:** the REA cap rows carry the release tag as an invalidator. Re-probe on a new rea-agents release
  (checked when a Fabric campaign starts, never polled).

### Supply-chain gate (before any F3b/F3c install)
Origin (NSA Ghidra release asset, Cuyler/Ghidra-GameCube-Loader repo, npm rea-agents), pinned version, sha256
recorded in `vault/programs/gsdx-fabric/supply-chain.json`. For the loader, a hash identical to the laptop copy.
License (Ghidra Apache-2.0, GameCubeLoader Apache-2.0, REA MIT). Isolated prefix under `~/fabric-tools/`, nothing
global. Rollback = delete that prefix. No install happens before the s12 approval is applied.

### Resource budget for F2/F3
Laptop: none (coordinator only). GEX44: Ghidra headless import of one ~4-5 MB DOL with a 6 GB heap, <= 4 cores,
~10-20 min; REA run similar; disk < 3 GB for the tools. 0 GEX44 compute jobs; D28 jobs untouched.

### Knowledge and closeout (inside F9)
FIOS / KV candidates confirmed by this scan: STALE_PROVIDER_CAPABILITY_ASSUMPTION (6.3.0 result treated as
current), ENVIRONMENT_FAILURE_MISCLASSIFIED_AS_TARGET_UNSUPPORTED (W4 JDK), FORMAT_SUPPORT_CONFLATED_WITH_ARCH_SUPPORT,
UNSCOPED_NEGATIVE_TOOL_CLAIM. UKDL candidates go to promotion only after F2's independence test and F3b's canary
pass. The CBR candidate is "capability over product", promoted only with a second domain consumer.

### Done-gates F2-1..6, F3-1..10
F2-1..4 belong to F2 (schema + tests), F2-5 to F3b (substitution), F2-6 to the independence test. F3-1..5 are met
by this scan except the release that ships `c86b09a` (closed in F3c step 1, or recorded UNKNOWN). F3-6 = minimum
delta above. F3-7 = the F3c disposition. F3-8 = per-capability receipts. F3-9 = independence test. F3-10 = every
row in the matrix labelled with the evidence that proved it.
