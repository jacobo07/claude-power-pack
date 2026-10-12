---
covers: [ccr, boundary-cost-contract, boundary-admission, tool-output-projection, output-size-admission, cost-attribution, cost-isolation, m4-runs-tree, cognitive-pgo, long-horizon-text, one-read, non-convergence, epoch-economics]
goal: ccr
status: PROPOSED (awaiting Owner approval)
supersedes-order-of: vault/plans/ccr-v3-long-horizon-text-2026-10-12.md (v3 units kept, re-sequenced into Stage 2)
authority: existing goal ccr, cap 36,880,000; used 5,171,864; settled 4,138,289; open 1,033,575; remaining 31,708,136 (goal-status 2026-10-12 ~16:40)
---
# CCR v4: Cognitive Boundary Compiler, so every model boundary has a cost contract (2026-10-12)

Continuation of goal `ccr`. This is not a new programme and not a second runtime. It extends the mod
`mods/cpp-cognitive-runtime` (hooks/register.ts + policy.ts) and the existing ledgers. v3 stays the plan of record
for long-horizon text. v4 puts the per-boundary cost layer in front of v3 and re-sequences v3 behind it.

## A. Frontier (measured in this scan)
- HEAD a7c88d6f (v3 plan, docs only) on feature/knowledge-acquisition. The shared tree has ~1000 foreign dirty files, so commits are pathspec-scoped only.
- Sealed: S1-S4, M1 226fcc12, M2 53b4941d, M3 11444399, M4 evidence 164ae73f, v3 plan a7c88d6f. Release is still 0.1.0-feaae8b0, and M1-M3 are not released yet.
- The CCR owner per RESUMPTION_FILE is c13cda65. Its transcript was idle at 16:24 according to v3, and this scan found no process carrying that id. The fencing below is required.
- The Madzia driver is LIVE ON THE LAPTOP: pid 13924 `tools/kobiimii/boundary.py run`, and worker pid 48160 is running phase 2, attempt 8. The move to GEX44 has not happened yet.
- The mod has hooks session.start, prompt.*, tool.describe, agent.spawn, session.append/compact, turn.step/complete and session.end, plus a `tool.call` that serves only the `page` tool. There is NO tool-result projection, NO forecast and NO admission. carryAdvice is observe-only and nothing reads it.
- Lobby figures (2,044 boundaries / 755M / 194M) are NOT in the vault and remain unverified (v3 U1).

## B. Owner / fencing
One writer. On approval, this session takes CCR ownership by rewriting the RESUMPTION_FILE owner line, with c13cda65 marked STANDBY. Proceed only if the Owner confirms that c13cda65 is not working. Driver-owned files (KSR `tools/kobiimii/*`) are not touched while pid 13924 is live. The M4 fix lands between attempts, or after the Owner stops the driver. The work happens in a private worktree `.claude/worktrees/ccr` (branch ccr/v4) and merges by pathspec.

## Root-cause matrix (this scan + v3 facts)
| class | verdict | basis |
|---|---|---|
| BOUNDARY_COST_CONTAMINATION | CONFIRMED | M4: one call-2 listing = 0.30-0.34M per attempt, 14-18 % |
| RUNS_TREE_TOOL_POLLUTION | CONFIRMED | same; still in the live path (a8 runs with the old ContextImage, unverified) |
| TOOL_OUTPUT_OVERMATERIALIZATION | PARTIAL | shell results 32-38 % (M4), text 44.9 % (M3 a3); estate-wide K = 2.67 % |
| MODEL_BOUNDARY_COST_UNEXPLAINABLE | CONFIRMED | 0.73M of a3 is invisible in the stream |
| SEMANTIC_COST_ADMISSION_MISSING | CONFIRMED | no admission code in the mod |
| BOUNDARY_FORECAST_MISSING | CONFIRMED | carryAdvice is post hoc and observe-only |
| COGNITION_NECESSITY_NOT_ENFORCED | PARTIAL | WorkUnit tool/attachment deferral exists; no deterministic-path check |
| READ_NECESSITY_NOT_ENFORCED | PARTIAL | instruction/skill linking yes; tool reads no |
| REREAD_NECESSITY_NOT_ENFORCED | CONFIRMED (no code) / value UNKNOWN | estate 1.88 % (CE F falsified); Lobby cross-epoch unmeasured |
| SEMANTIC_CAPITALIZATION_INCOMPLETE | CONFIRMED | no receipt store |
| REASONING_RECONSTRUCTION_RENT | UNKNOWN | 0.73M not yet attributed; do not call it thinking |
| LONG_HORIZON_TEXT_CARRY | CONFIRMED (Madzia) / UNKNOWN (Lobby) | a3 ctx 20K -> 113K over 53 calls |
| CACHE_WRITE_ROTATION_PENALTY | CONFIRMED | cw 80,256 per rewrite |
| MULTIMODAL_CARRY | CONFIRMED, minority | 16.8 / 9.3 / 10.5 %; no more pixel-only work |
| CONTEXT_ELASTICITY_UNPROVEN | CONFIRMED | no benchmark exists |

## Owner map
| capability | class | owner / plan |
|---|---|---|
| Semantic Boundary Compiler | EXTEND | WorkUnit (policy.parseWorkUnit) + ContextImage -> BoundaryContract |
| Semantic Cost Contract | IMPLEMENT | schema in policy.ts, receipt under mod state dir |
| Proof of Cognition Necessity | PARTIAL -> EXTEND | contract field `necessity`; DETERMINISTIC_PATH verdict |
| Proof of Read / Re-read | PARTIAL / IMPLEMENT (gated on D1) | linkInstructionFiles; H1 for tool reads |
| Live Dependency Closure | EXTEND | ContextImage refs, typed (path+hash+fields) |
| Context/Capability Linker | ALREADY_DONE (skills/rules/tools) / EXTEND (evidence) | tool.describe, prompt.attachment |
| Tool Output Projection | IMPLEMENT or HOST_LIMITATION | first probe whether the host exposes a mutable tool-result event; fallback = query wrappers + PostToolUse advisory |
| Output-Size Admission | IMPLEMENT | same seam; persist the full result under the mod state dir, return ref + projection |
| Semantic Cost Forecast | IMPLEMENT | turn.step: floor + carry + expected tool output, from PGO |
| Boundary Admission | IMPLEMENT | turn.step verdict; enforce on driver/worker boundaries first (ContextImage), observe elsewhere |
| Cost Attribution | EXTEND | rowFacts -> per-bucket receipt incl. thinking/sealed |
| Semantic Delta Capitalization | IMPLEMENT (small) | v3 G1 receipt store |
| UTVM | EXTEND | L0 jsonl + L1 usage_index; page kind history/fact (v3 K1) |
| One-Read | IMPLEMENT if D1 GO | v3 H1 |
| Semantic Paging | EXTEND | mod `page` |
| Intra-Epoch Governor | EXTEND | turn.step re-forecast every call |
| Epoch Compiler | EXTEND | carryAdvice -> weighted break-even incl. cw (v3 E1) |
| Cognitive PGO | IMPLEMENT (small) | work-class distribution from usage_index |
| Mission Recompiler bridge | CONNECT | emit ZERO_PROGRESS_COGNITIVE_PATTERN; gsd_mission NO_PROGRESS consumes (v3 U3) |
| Economic Runtime bridge | CONNECT | P50/P80 forecast -> mission_spend / lease admission |

## C. Semantic Cost Contract (schema, one row per material boundary)
`{boundary_id, goal, work_class, obligation, necessity: ZERO|DETERMINISTIC|BOUNDED|NOVEL|OWNER, closure:{refs[path,hash,fields]},
capabilities:{tools,skills,rules,mcp}, forecast:{floor,constitution,state,evidence,tool_out,history,images,think_out,p50,p80},
verdict: ADMIT|DEFLATE|PROJECT|PAGE|SPLIT|ROTATE|DEFER|DETERMINISTIC_PATH|INCIDENT|OWNER_BOUNDARY, reasons[],
expected_delta, postcondition}`. After the call the contract gets `{actual buckets, variance, delta_receipt_ids, capital_yield}`.
If a field cannot be compiled it stays UNKNOWN, and an UNKNOWN forecast never ADMITs above the work-class P80.

### Contract example: M4 predecessor-evidence lookup (not executed)
- Obligation: give reviewer attempt aN the evidence of a(N-1), i.e. the receipt, the accepted artifacts and the reviewer verdict.
- Necessity: DETERMINISTIC. The driver knows N, and the predecessor is N-1 under runs/<phase>/a<N-1>/.
- Live closure: 1 receipt path + <= 3 artifact refs + verdict fields. That is about 3 refs and < 2K chars.
- Forecast buckets: floor ~20K (a3 start ctx) + state ~1-3K + evidence refs < 1K + tool_out ~0. Discovery spend = 0 model calls.
- Excluded contamination: a recursive runs-tree listing (0.30-0.34M cumulative carry per attempt), sibling attempts and other phases.
- Verdict under v4: DETERMINISTIC_PATH. The driver resolves the paths in Python and writes them into the ContextImage. If a worker still emits a recursive listing, the result is PROJECTed to the matching refs, or the boundary is an INCIDENT.
- Verdict under today's code: ADMIT, blindly. Nothing forecasts the call, nothing projects the result and nothing refuses it.

## Workstreams (execution order; mode)
Stage 1: boundary-cost core. P80 fits the current authority.
| # | unit | mode | done-gate |
|---|---|---|---|
| B1 | M4 fix: driver ContextImage carries exact predecessor evidence refs; no runs-tree listing | EXECUTION (fenced on pid 13924) | a(N+1) call-2 shell result < 2K chars; processed/attempt vs a4/a5 at reviewer parity |
| B2 | M4 elasticity CI: synthetic runs estate 10/100/1k/10k, fixed lookup -> model-facing bytes | EXECUTION | elasticity < 0.05 after floor; old behaviour goes red |
| B3 | Attribution: per-bucket receipt (floor/tool_out by tool/thinking/sealed/images/user/assistant/UNKNOWN); attribute a3's 0.73M from live receipts (GEX44 or laptop a8+) | EXECUTION | residual UNKNOWN < 10 % of carry, or named host limit |
| B4 | Contract schema + compiler (WorkUnit/ContextImage -> contract rows) | EXECUTION | every driver boundary emits a contract; UNKNOWN fields explicit |
| B5 | Host probe, then Tool Output Projection + Output-Size Admission (persist full, return ref+projection) | EXECUTION; ULTRA-PLAN only if the host has no seam | tool-pollution mutation test: an injected 1 MB result never reaches provider input (provider usage, not the transcript) |
| B6 | PGO + forecast + pre-boundary admission at turn.step (observe first, then enforce on driver boundaries) | EXECUTION | forecast error P50 < 25 % on held-out calls; a contaminated replay is refused before spend; a clean control is admitted |
| U3 | Non-convergence progress receipt -> ZERO_PROGRESS_COGNITIVE_PATTERN -> gsd_mission | EXECUTION | 25-09 replay halts earlier; real-progress control not halted |
| D1 | Read attribution on Lobby (repeated unchanged reads share) | EXECUTION | GO/NO-GO at 3 % |
Re-forecast gate: measured cost per unit after Stage 1 -> new P80 for Stage 2 before any Stage-2 spend.

Stage 2: v3 long-horizon text and certification.
| U1/U2 Lobby figures + autopsy · E1 epoch economics with cw · M1 tiny continuation · G1/H1/K1 receipts + One-Read + history paging (only if D1 GO) · R1 history/tool/knowledge elasticity · V1 real canary (contract recorded before the call) · X1 certify or abstain · KV/FIOS/UKDL/CBR | EXECUTION; V1 PLAN for ownership |

## Benchmark matrix
| test | fixed | varied | metric | pass |
|---|---|---|---|---|
| M4 elasticity | predecessor lookup | runs estate 10..10k | model-facing bytes/tokens | slope < 0.05 after floor |
| tool pollution | one WU | injected oversized irrelevant result | provider input tokens | unchanged within floor noise |
| long-session text | Lobby WU | history H/2H/4H | weighted tokens | elasticity < 0.05 |
| One-Read | unchanged file reread | epochs/sessions | raw reread count | -> receipt hits; changed file still re-read |
| epoch economics | held-out sessions | arms A-F | weighted cost incl. cw | rule beats A |
| reasoning rent | a3-like WU | none | bucket shares | UNKNOWN < 10 % |
| real boundary | one bounded WU | policy on/off | provider usage + reviewer parity | weighted saving >= 15 % |

## Effectiveness contract
EFFECTIVENESS_NOT_CERTIFIED -> EFFECTIVENESS_PARTIAL (B1+B2+B5+B6 gates green on real provider usage) ->
EFFECTIVENESS_CERTIFIED_BOUNDARY_COST (two work classes: Madzia driver real + Lobby offline/R1, forecast error and
admission proven) -> EFFECTIVENESS_CERTIFIED_LONG_HORIZON (v3 contract). A miss produces an ABSTAIN with the named limit.

## Token budget (this continuation)
| item | P50 |
|---|---|
| reality delta (done) | 0.4M |
| B1 M4 fix | 1.0M |
| B2 M4 elasticity CI | 0.8M |
| B3 attribution + 0.73M | 1.5M |
| B4 contract schema/compiler | 1.8M |
| B5 host probe + projection + size admission | 2.5M |
| B6 PGO + forecast + admission | 2.5M |
| U3 non-convergence | 2.0M |
| D1 read attribution | 1.2M |
| Stage 1 meta tax + reserve | 1.8M |
| **Stage 1** | **15.5M** (P80 19M) |
| U1/U2 + E1 | 3.0M |
| M1 + R1 | 2.0M |
| G1/H1/K1 (D1 GO only) | 4.0M |
| V1 canary | 3.0M |
| X1 + KV/FIOS/UKDL/CBR + self-host | 1.5M |
| Stage 2 reserve | 1.5M |
| **Stage 2** | **15.0M** (11M if D1 NO-GO) |
Semantic lower bound 7M · LOWER 12M · P50 30.5M (26.5M if D1 NO-GO) · P80 36M · P95 45M ·
HARD AUTHORITY 31,708,136 remaining. Stage 1 P80 fits with ~12.7M margin. The full P80 does NOT fit. No raise now: the
approved 66.2M raise stays unapplied (stale). At the end of Stage 1, re-forecast Stage 2 from measured unit costs.
Ask for capital only if that measured P80 exceeds the remainder, with the evidence.
Confidence: medium. The floor is 100-215K per call on this estate, so roughly 10-15 calls per M of P50.

## Stop-losses
D1 < 3 % makes G1/H1 NO_WORK. A reviewer or test regression kills the arm. If B5 finds no host seam, record HOST_LIMITATION and
fall back to query wrappers + the driver ContextImage. Spend at 28M settled triggers a stop and a re-forecast. Never run two writers.
