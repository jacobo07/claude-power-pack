# CCR Boundary Cognitive Working Set - Master Plan (Reality Delta, 2026-10-17)

Status: PLAN ONLY. No mission armed, no packet changed, no capital applied, no code touched, Tennis untouched.
Scan: 9 small reads/probes from this pane (host free RAM 4.3%). Anything not read is labelled UNVERIFIED.
The chat copy of this plan is the approval surface; this file is the backup.

## 1. Reality (measured this scan)
- Claude Code installed: 2.1.302 (`claude --version`). CCR release 0.1.0-54f1824b ACTIVE since 2026-10-14 21:03 (`~/.claude/ccr/ACTIVE.json`).
- `mods/cpp-cognitive-runtime/hooks/policy.ts:8` is still `COMPAT = ['2.1.296']`. Host is 6 releases past the pin (2.1.297..302), so by the 10-16 measurement every non-off CCR mode degrades to shadow. Not re-measured today; the 10-16 receipt count (69 of 71 starts incompatible) was on 2.1.299-301.
- Programme `ccr`: settled 233,379,193; lease L17 cap 13,000,000, used 461,508, open 1,033,575, remaining 12,538,492 (`mission_spend goal-status --goal ccr`). The v5 packet is scoped to Envelopes 0-3 only.
- Goal `ccr-vm`: settled 0, open 0, cap null. Packet `vault/plans/capital-packet-ccr-vm.json` exists, ceilings P50 2.5M / P80 3.5M / P95 3.5M, expires 2026-10-19, and is invalidated if WU-T0.md scope changes.
- The brief's "CCR is a new idea" premise is false. Already exist: `ccr-v4-boundary-cost-2026-10-12.md` (Semantic Cost Contract per boundary), `ccr-hypervisor-master-plan-2026-10-16.md` (matrix, owner map, Epoch Zero audit: 13,394 calls, 2,803.3M cache read, 97.8% hit), and the v5 plan in `.claude/worktrees/ccr-v5` (floor decomposition, boundary ledger, PGO, physical forecast gate, code-map projection, fresh epoch per plan).
- Names UCVM / UTVM / UCWSM: 0 matches in `modules|tools|mods` (py/ts/md). Either they live under other names or they are SPEC_ONLY. Classified in T0A, not assumed.
- `modules/cognitive_os/` holds context.py, gc.py, memory.py, router.py, economics.py, hibernation.py, rehydration.py, process_governor.py. These are the likely owners; classification is T0A work.

## 2. WU-T0 gap analysis (`vault/programs/ccr-vm/WU-T0.md`)
Covers: Mod capability matrix, caller coverage, owner map, Tennis forensics, T1+ plan. Budget 3.5M hard / 2.5M P50.
Missing from the brief: Context Reclamation Capability Matrix (avoid / reclaim / rotate per source), hard host floor vs CPP floor, same-session reclamation experiments, physical per-boundary measurement, rotation fallback feasibility, session-age elasticity design, flamegraph.
Redundant with prior work: matrix and owner map are ~70% already written (master plan sections 3-4). T0 must delta them on 2.1.302, not redo them.
Decision: do NOT patch WU-T0.md in place (that voids the armed packet's hash and scope invalidator). Add `WU-T0A.md` + `WU-T0B.md` as new files that split the work, and leave WU-T0.md as the superseded parent. Packet ceiling stays 3.5M total across both. If the Owner prefers one file, the packet must be re-issued.

## 3. Mod capability matrix and reclamation matrix (starting point, NOT re-probed on 2.1.302)
Source: master plan section 3, probed on 2.1.296. T0A re-probes every row on 2.1.302 and records classes with file:line or probe output.
| Context source | Avoid | Filter pre-materialize | Block future append | Replace with handle | Reclaim resident | Fallback |
|---|---|---|---|---|---|---|
| prompt.section/context/attachment | DIRECT | DIRECT | n/a | DIRECT | UNKNOWN | rotate |
| tool schemas (tool.describe isDeferred) | DIRECT (defer, never delete) | DIRECT | n/a | ToolSearch handle | UNKNOWN | rotate |
| skills (skill.prompt) | DIRECT | DIRECT | n/a | DIRECT | UNKNOWN | rotate |
| tool output (session.append) | n/a | DIRECT (rewrite before storage) | DIRECT | DIRECT (B5: shell carry -77% at parity) | NOT_EXPOSED for already-resident rows | rotate |
| model narrative / thinking blocks | n/a | UNKNOWN | UNKNOWN | via session.append | NOT_EXPOSED | rotate (B3: thinking = 40.8% of carry) |
| host system prompt, managed tiers | PROTECTED_BY_HOST | - | - | - | - | HARD_HOST_FLOOR |
| compaction output (session.compact) | - | - | - | - | UNKNOWN interactive (hung under -p in M1) | rotate |
Honest answer to "can CCR evict already-resident transcript rows": NOT_EXPOSED per prior probe. Do not claim reclamation. Avoidance + rewrite-at-append + rotation is the realistic triad; T0B tests this on 2.1.302.

## 4. Floors
Measured earlier (not re-measured): default launch ~74-78K; CCR lean 21K (tool schemas dominate); real GSD workers 100-215K/call, previous median session-start floor 116-128K. v5 decomposition: ~59K invisible floor.
HARD_HOST_FLOOR vs CPP_ADDED_FLOOR: T0B measures both with a bounded headless probe (haiku, ~1.5M guard per V1 lesson).

## 5. Cache-read diagnosis
Hit 97.8% is not the lever. CRA is UNKNOWN until a minimum-CWS proxy exists. Main sessions are 86.1% of spend and run shadow, so CCR as deployed cannot have lowered main spend. Dead ends not to retry: epoch rotation on Madzia (-0.2%), One-Read (2.4%), docs-reset elasticity, haiku harness without guard.

## 6. What the brief adds on top of v4/v5 (new vs reused)
REUSE and extend: `tools/token_ground_truth.py` (audit), `tools/ccr_pgo.py`, `tools/ccr_release.py`, `tools/context_floor_census.py`, `modules/capability_runtime`, ASER/rotation, `gsd_mission`, `mission_spend`, `modules/cognitive_os/*`, v5 boundary ledger and physical forecast gate.
NEW (the real delta): (a) per-boundary Boundary ContextImage + live-dependency closure + consumer graph; (b) Context Justification Receipt and Context Admission (justified-CWS vs physical-CWS comparator); (c) page-liveness states on the existing page model; (d) session-age / project-age / estate-size / tool-universe elasticity CI; (e) flamegraph by causal class; (f) boundary-level output authority and model routing; (g) transparent rotation as Owner-free default.
Items 12-40 of the brief's list are mostly design vocabulary for (a)-(g). No new IR framework until a measured hotspot needs it.

## 7. Owner resolution (PLAN, not ULTRA)
No canonical-owner conflict seen: UCVM-by-name absent, so Boundary Context Compiler extends `modules/cognitive_os/context.py` + v5 boundary ledger; CCR Mod is the enforcement/linking plane only; economic admission stays in the economic kernel (`mission_spend`, v5 gate). ULTRA-PLAN only if T0A finds two live owners.

## 8. Mode by workstream
T0A reality + re-probe: EXECUTION. T0B floors, reclamation experiments, flamegraph of one historical boundary: EXECUTION. Compiler owner contract: PLAN. Compiler shadow, justification receipt: EXECUTION after contract. Consumer graph, page liveness, exposure reservation, epoch migration, model/output routing, PGO prefetch, DVFS: PLAN then shadow EXECUTION. Ablation/elasticity CI: EXECUTION. CBR: EXECUTION after proof.

## 9. Staged budget (processed tokens incl. cache reads, ledger unit). Only T0A+T0B requested.
Basis: measured Stage 3 units 1.7-6.4M. `ccr_pgo` forecast is 93% wrong and was not used. T1+ are sizing placeholders with ZERO authority.
| Tranche | Scope | Sem LB | Lower | P50 | P80 | P95 | Hard | Boundaries | Avg CWS | Conf |
|---|---|---|---|---|---|---|---|---|---|---|
| T0A | re-probe matrix on 2.1.302, owner/coverage delta, UCVM-name classification, WU split | 0.4M | 0.6M | 1.0M | 1.4M | 1.7M | 1.8M | ~25 | 30-40K | med |
| T0B | hard/CPP floor probe, 3 reclamation experiments, physical-context measurement, one Tennis flamegraph (script, totals only) | 0.6M | 0.9M | 1.5M | 2.0M | 2.4M | 1.7M | ~35 | 30-40K | med-low |
| T0 total | | | | 2.5M | | | 3.5M (packet ceiling) | | | |
| T1 | Boundary Context Compiler shadow + Justification Receipt | 1.5M | 2.5M | 4M | 6M | 9M | not requested | | | low |
| T2 | consumer graph + page liveness + semantic CSE | 2M | 3M | 5M | 8M | 12M | not requested | | | low |
| T3 | exposure reservation + economic integration (rides v5 gate) | 1.5M | 2.5M | 4M | 6M | 9M | not requested | | | low |
| T4 | transparent epoch migration + continuation canary | 3M | 4M | 6M | 10M | 15M | not requested | | | low |
| T5 | tool-result virtualization + cognitive DMA canary | 1.5M | 2.5M | 4M | 6M | 9M | not requested | | | low |
| T6 | boundary model routing + output authority shadow | 2M | 3M | 5M | 8M | 12M | not requested | | | low |
| T7 | flamegraph + allocation profiler (durable) | 1M | 1.5M | 2.5M | 4M | 6M | not requested | | | low |
| T8 | PGO prefetch/eviction | 2M | 3M | 4M | 7M | 10M | not requested | | | low |
| T9 | age/estate/tool-universe invariance suite | 2M | 3M | 5M | 8M | 12M | not requested | | | low |
| T10 | DVFS + estate shadow | 2M | 3M | 4M | 7M | 10M | not requested | | | low |
| T11 | vault/FIOS/UKDL/CBR + regression budgets | 1M | 1.5M | 2.5M | 4M | 6M | not requested | | | low |
Self-deflation: T1+ are re-forecast from T0B measured spend before any request. Likely to collapse: T4 (Madzia rotation was -0.2%), T8 (needs T7 data), and any item v5 Env 1-3 already lands.

## 10. CAPEX / OPEX / amortization
CAPEX = goal `ccr-vm` (institutional). OPEX = tennis-rf, Two Builders, none spent here. Addressable value: main-session carry on 86.1% of ~2,865M weekly processed tokens; 62% of spend is above 200K context. These are addressable bounds, not savings. Observed savings: NONE. Break-even for T0 (2.5M ~= 1.6 equivalent units, ~0.07% of one week) is any sustained saving above that.

## 11. Micro-commits
Pathspec-scoped, one per: WU split files, 2.1.302 matrix re-probe, hard-floor probe result, reclamation experiment receipts, T0-reality.md, tranche plan, receipt. Verify `git log -1 --format=%s` after each. Shared tree has many foreign dirty files; vault/ files only.

## 12. Minimum immediate authority
T0A + T0B under the existing `capital-packet-ccr-vm` ceiling (3.5M hard, stop-and-receipt at 3.0M), goal `ccr-vm`. Time ceiling 1 working day, expiry 2026-10-19. Touches: vault/programs/ccr-vm, vault/plans, read-only on mods/ and ~/.claude/ccr. Read-only probes on 2.1.302 (headless `-p --plugin-dir`, haiku, 1.5M guard). NO mod code change, NO release, NO settings.json, NO Tennis capital in T0. Authority to patch the Mod / UCVM / telemetry / run synthetic growth tests / auto-rotate epochs is requested at T1, not now, because T0 cannot justify it yet.
Executor: a fresh slim worker armed through the Ralph mission (`gsd_mission.py arm`), never this pane.

## 13. Conditions for T1
T0A shows a single live owner for context compilation; T0B shows at least one source that avoidance or rewrite-at-append removes from physical context with parity (else CCR closes at PARTIAL on this axis); version gate decision made (widen COMPAT to verified versions, or fall back to a re-probe-on-update gate).

## Open risks
1. Unit Zero (restore enforcement on live host) is a prerequisite for any enforced measurement. It is covered by v5 Env 1 and is not part of this ask; without it T0B measures shadow. 2. Host 2.1.302 auto-update can shift the matrix again during T0. 3. The brief's elasticity CI needs synthetic aged sessions; design only in T0.
