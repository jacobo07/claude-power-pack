---
covers: [ccr, ccr-v2, cognitive-runtime-mod, prompt-materialization-firewall, tool-linker, skill-linker, constitution-linker, memory-linker, epoch-compiler, intra-epoch-governor, semantic-gc, boundary-py-decomposition, madzia-r4]
status: AWAITING_OWNER
goal: ccr
supersedes_sections_of: vault/plans/ccr-mods-backend-2026-10-11.md (v0.1 plan stays the record of M1/S1/S2)
---
# CCR v2 — from shadow to engine-level enforcement (Master Plan, 2026-10-11)

## 0. Reality Delta (bounded scan, read-only; nothing changed)
| Fact | Evidence |
|---|---|
| Claude Code 2.1.296; CCR release 0.1.0-feaae8b0 active, user scope, OFF=false, no prior release | `claude --version`; `tools/ccr_release.py status` |
| CCR v0.1 enforces only on SUBAGENTS (instructions → kernel+index, skill_listing drop). Main = shadow receipts | `mods/cpp-cognitive-runtime/hooks/register.ts` L96-121 |
| Goal ccr: cap 36.88M, used 4.15M, remaining 32.73M | `mission_spend.py goal-status --goal ccr` |
| PP HEAD 909ad75b (cdc writer active on this branch; 30+ foreign dirty files). CCR paths clean | `git status -- mods vault/programs/ccr` |
| boundary.py lives in KSR (`CursorProjects/tools/kobiimii/boundary.py`), HEAD 65e00ad, and is **uncommitted-modified by the Madzia owner**; KSR `RESUMPTION_FILE.md` dirty (theirs) | KSR `git status` |
| Madzia driver state RUNNING; a worker is live now (claude.exe pid 17144, started 21:53) | driver_state.json, process list |
| Ablation medians (Opus, trivial prompt, KSR cwd): A 73,400 · B 68,897 · C 43,551 · D 18,730 · E 10,407 | `runs/madzia_ctx_20261011/ablation.json` |
| Lever sizes: B plugins/skills/MCP −4.5K · C `--tools` 7 −25.3K · D claudeMdExcludes −24.8K · E autoMemory off −8.3K | same, `levers` |
| A–A spread on the default arm: 72,775 vs 74,026 = **1,251** | ablation rows |
| Madzia worker p4p1a1: call1 **14,401**, 26 calls, **1,192,347** processed input (cache_read 1,116,830) | driver_state epochs + CCR receipt d6343597 |

## 1. Root Question 1 — why CCR saves ~nothing on the measured first call
Traced from the worker's own CCR receipt (d6343597): zero `link` rows (instructionFiles empty: claudeMdExcludes removed them at launch), no `instructions`/`skill_listing` attachments (removed at launch), zero subagents (`--tools` has no Agent). **Every surface v0.1 enforces was already gone before CCR ran.** What remained controllable and was only shadowed: `hook_additional_context` ×10 (~2.5K chars each, carried every later call), `total_tokens_reminder` ×26, `session_context` 806.
- "Default + CCR saves ~800": **false premise** — inside the 1,251 A–A spread. Real effect = 0 ± noise (main is shadow).
- "+275 on lean": hypothesis H-275 = CCR's own registered `page` tool + its `mcp_instructions_delta` row (225 chars seen). Verify in R0; fix = defer the tool.
- boundary.py docstring "no hook can remove any of it" is **false for 2.1.296** (iteration pass: CLASE 1, assumed API). See §2.

## 2. Mods capability matrix (2.1.296, types-verified; RUNTIME = proven in M1/S1)
| Surface | Authority | Main | Subagent | -p worker | Status |
|---|---|---|---|---|---|
| `prompt.compose` sections | ADD/DROP/REWRITE/REORDER | yes | no (M1) | yes | RUNTIME (observe) |
| `prompt.section` (`memory`, env…) | REWRITE/DROP | yes | ? | yes | types; probe P2 |
| `prompt.context` blocks (claudeMd…) + instructionFiles | DROP/REWRITE per block/file, once/conversation | yes | no | yes | RUNTIME (observe) |
| `prompt.attachment` (`instructions`, `skill_listing`, `agent_listing_delta`, `deferred_tools_delta`, `hook_additional_context`, reminders) | REWRITE/DROP (null), cached per process | yes | yes (agentId) | yes | RUNTIME (drop proven on subagents) |
| `tool.describe` | REWRITE, `isDeferred` true/false | yes | yes | yes | RUNTIME for non-core (−6.8 %); **core built-ins UNKNOWN** → P1 |
| tool REMOVAL (the `--tools` effect) | none | — | — | — | NOT_SUPPORTED → launch adapter or defer |
| `agent.offer` | hide type + refuse dispatch | yes | yes | yes | types; P3 |
| `skill.prompt` | REWRITE expanded skill text (projection) | yes | yes | yes | types; P4 |
| `session.append` | REWRITE row content before it is stored AND sent (tool results) | yes | yes | yes | types; **P5 (incl. images)** |
| `session.compact` / `$.session.compact()` | own `{messages}` = compaction without the summariser; rejects while a turn runs | yes | yes (agentId) | between turns only | UNKNOWN under -p (M1) → P6 interactive |
| `turn.step` | model/effort per request; messages pinned | yes | yes | yes | types |
| `session.measure` / `$.session.usage()` | OBSERVE fill per turn | yes | — | yes | types |
| Host core system text, transcript rows already stored, managed tier | — | | | | HOST_INTERNAL / MANAGED_PROTECTED (none managed on this machine) |
| Hot reload | installed plugin: new release loads at next session start; running sessions keep their module | | | | RUNTIME (install) |

## 3. Root Question 2 — which 74K→10K reductions move into CCR
| Lever (Δ tokens) | Launch mechanism | CCR mechanism | Safe | Exact | Dynamic | Host-limited |
|---|---|---|---|---|---|---|
| D CLAUDE.md+rules (24.8K) | `claudeMdExcludes` | `prompt.context`: claudeMd → kernel (HARD-RULES digest) + always-keep + file index; delinked files pageable | yes (kernel proven on subagents) | yes | per Work Unit | no |
| E auto-memory (8.3K) | `autoMemoryEnabled:false` | `prompt.section{memory}` → index lines matching the Work Unit; rest pageable | yes | yes | yes | no (P2 confirms section name) |
| B skills/plugins/MCP (4.5K) | disable plugins, `--strict-mcp-config`, `--disable-slash-commands` | drop `skill_listing` (main), `mcp_instructions_delta` filter, defer MCP tools, `agent.offer` | yes | ≈ (MCP server process still starts) | yes | partly (process/handshake) |
| C tools (25.3K) | `--tools` 7 | drop `agent_listing_delta` (~7K tok), defer every tool outside the closure (`isDeferred:true`), ToolSearch = page fault | yes | **only if P1 proves core built-ins defer** | yes | YES for removal; residual = deferred-name list |
| ContextImage | `--append-system-prompt-file` | `prompt.compose` `ccr:image` section (scope session) from the compiled Work Unit | yes | yes | yes | no |
**Root Question 3 (first-generation success):** yes for D, E, B and most of C *if P1 passes*; forecast default+CCR ≈ 12–17K vs lean 10.4K. If P1 fails, the C residual (~core schemas of unused built-ins) is host floor for default sessions and stays a launch adapter for drivers.
**Root Question 4 — hard host floor:** core system sections (~9.4K chars ≈ 2.6K tok) + schemas of the linked closure + environment/date/model attachments + settings-hook context that is security-bearing. Measured target: arm E′ = E with CCR, every reducible block removed (R0 benchmark row).

## 4. Root Questions 5–6 — after the first call (the real cost)
Worker p4p1a1: floor 14.4K × 26 calls = 374K; actual 1.19M → **~69 % of the epoch is intra-epoch carry** (tool results, images, advisory hook context, reminders). First-call work alone cannot fix Madzia's economics.
Mods can alter live materialization at exactly three points, and nowhere else:
1. **Ingestion (`session.append`)**: a large tool result is stored raw in the CCR page store (sha-addressed, per repoKey) and the row keeps a projection + page handle. Raw transcript evidence survives on disk; the model carries the projection. (P5 proves rows incl. images.)
2. **Attachments**: advisory `hook_additional_context` (non-blocking paragraphs only; `advisoryBytes` already separates them) and repeated reminders → dropped or deduped after first delivery.
3. **Turn boundaries (`session.compact` with own messages)**: Semantic GC — replace the transcript with ContextImage + sealed Semantic Delta; raw stays in the transcript file. Interactive/multi-turn only (rejects mid-turn).
No mid-turn surgery of already-stored rows exists → for single-turn `-p` workers, epoch rotation stays a driver decision fed by CCR's carry forecast (§7). No unsafe emulation.

## 5. Root Question 7 — boundary.py decomposition (one owner each)
| Responsibility | Verdict | Owner after v2 |
|---|---|---|
| ContextImage pages + consumer + sha staleness | KEEP (domain-specific obligation compiler) → emits a **Work Unit file** CCR reads | boundary.py (Madzia domain) |
| Launch profile flags (plugins off, claudeMdExcludes, autoMemory off) | RETIRE after R4 proves CCR parity | CCR (prompt.context/section/attachment) |
| `--tools` closure | KEEP AS HOST-LIMITATION ADAPTER until P1; then CCR defers | CCR Tool Linker (adapter retired if P1 passes) |
| `strips_ccr` refusal | KEEP | boundary.py |
| Admission (floor + image forecast) | MOVE: CCR publishes the floor per Work Class (PGO); driver keeps the yes/no | CCR forecast, driver decides |
| Fresh process per epoch | KEEP (host-limitation backend for -p single-turn) | boundary.py, cadence from CCR carry forecast |
| Usage accounting (`run_epoch`) | KEEP but **bug**: output counted from the first streamed usage per message id → 281 vs 33,525 real (receipt) | boundary.py owner (report; not mine to edit) |
| Reviewer/accept/rollback/commit loop | NO_WORK (domain control plane) | boundary.py |
| ctx_ablation.py | KEEP AS TEST HARNESS; add arms F (default+CCR v2) and G (lean+CCR v2) | KSR, benchmark consumer |

## 6. Architecture (minimum; one canonical owner)
- **Compiler = the mod** (`policy.ts`, pure, deterministic, unit-tested). Input: Work Unit = a driver-supplied file (`CPP_CCR_WORKUNIT` env → JSON: obligation, required ops, pages) or, in default sessions, the first prompt + repoKey + PGO profile. Output: a **closure plan** {tools, skills, agents, rule files, memory lines, image, epoch policy, budget}. No second runtime in Python; `tools/ccr_pgo.py` only aggregates receipts offline.
- **Linkers** (each = closure function + firewall hook + page-fault path):
  Tool: required-ops → tool set; outside → `isDeferred:true` (never remove core Read/Edit/Write/shell); fault = ToolSearch (receipt).
  Skill: `skill_listing` → lines matching the Work Unit (empty by default); fault = `page{skills}`; `skill.prompt` projection = later, only if P4 shows positive EVC.
  Agent: `agent_listing_delta` drop on main unless the Work Unit needs fan-out; `agent.offer` for hard closure.
  Constitution: claudeMd → kernel + ALWAYS_KEEP + per-file trigger match (v0.1 `linkInstructionFiles`, now enforced) + index; managed kind never touched; fault = `page{file}`.
  Memory: `memory` section → matching index lines; fault = Read of the memory file (receipt via tool.call observe).
  Evidence: ingestion projection (§4.1).
- **Semantic CSE**: exact paragraph hash across claudeMd files + memory + image; keep first. Nothing semantic.
- **Firewall**: every hook above = the earliest controllable boundary; mode per tier `{main, subagent}` ∈ off|shadow|enforce, per-surface switches in `modes.json`.
- **Receipts** (cheap, already flushed per turn): surface, identity, bytes in/out, reason, cached?, fault?, host-mandatory?, dedup?. Plus per-call `usage` → growth curve.
- **Page faults**: `page` tool (deferred itself) + ToolSearch + Read-of-delinked-path detection; fault rows → PGO; ≥2 faults of one page per Work Class → prefetch.
- **Intra-epoch governor**: per turn, `session.measure` fill + receipts → carry forecast = Σ(carried rows) vs locality; above budget → (interactive) `$.session.compact` with own messages = ContextImage + Semantic Delta (decisions, claims, failures, frontier, next obligation); (-p driver) writes `rotate` advice the driver reads between epochs.
- **ASER**: stays the 70 % backstop; CCR rotation acts before it.
- **PGO**: per (Work Class, repoKey-free) → closures, faults, floor, carry p50, epoch length. Names and counts only, never content. Invalidated by fingerprint {CC version, tool list hash, skill list hash, rules digest hash, runtime version}.
- **Compat**: `COMPAT=['2.1.296']`; any other version → shadow everywhere (existing gate) + receipt.

## 7. Security / fallback
Optimisation hooks fail OPEN to stock context. Never touched: managed kind, settings hooks (security runs as settings hooks, CCR only removes advisory prose), HARD-RULES digest (always in kernel), Owner authority (never read from repo text; CCR has no authority surface). Malicious repo instructions: a repo CLAUDE.md is either kept whole or delinked to its index — never summarised into the kernel. Cross-repo: receipts, page store, PGO keyed by repoKey; PGO carries no content and no secrets (HR-SECRET-006). Kill switches: `ccr_release.py off`, `rollback`, per-tier modes, version gate. Quality stop-loss trips → that tier returns to shadow automatically for the ring.

## 8. Probes, rings, canaries (canonical names R0–R5 of this programme kept)
- **R0 synthetic** probes P1 core-tool deferral · P2 `memory` section · P3 agent.offer · P4 skill.prompt · P5 append rewrite incl. image rows · P6 own-messages compaction (interactive) · H-275 · hook ordering (prompt.submit before context/describe). Autonomy-CI fixtures (§9).
- **R1 isolated sessions**: first-call 6-arm benchmark (default/lean × no-CCR/v0.1/v2), n=3 per arm, Opus, KSR cwd copy-free (ablation harness pattern), + multi-call benchmark on a fixed 8–15-call Work Unit (growth curve, cumulative rent, cache read).
- **R4 Madzia** (only at a driver boundary, never against a live worker): new profile arm F = default + CCR v2 + Work Unit file. Applied by patch when boundary.py is clean and the driver is stopped; spend books to KSR goal. Measure §DoD set; quality = reviewer verdict parity vs lean arm on the same phase.
- **R2 self-host / second Work Class**: CCR's own remaining development (code-edit class in PP) runs under main-tier enforce.
- **R3 non-CPP** repo session, then **R5 global**: main tier default `enforce` in a new release.
Stop-losses: quality (reviewer verdict or answer correctness worse than the lean/stock arm on the same unit → tier back to shadow); context regression (> +5 % provider tokens vs prior release on any CI arm → no promotion); page-fault storm (> 3 faults/Work Unit → closure widened, not retried).

## 9. Autonomy CI (V-CCR2-*; `claude plugin test` + Python harness)
default/lean/main/subagent/headless/resume; large tool, skill, rules, memory, transcript catalogs (elasticity: CWS bounded as unrelated surfaces grow); required tool/skill/rule missing → fault or refusal (mutation tests); stale profile/image; managed file present → keep; mod disabled/crash → stock; version mismatch → shadow; rotation + restart mid-rotation; cross-repo isolation.

## 10. Mode by workstream
ULTRA-PLAN: this document only. PLAN: P1/P5/P6 outcomes if they contradict §3/§4. EXECUTION: everything else, micro-commits per linker/surface/test, pathspec-scoped.

## 11. Token budget (processed input incl. cache reads; this pane's floor 100–215K/call; self-hosting expected to cut it)
| Workstream | P50 |
|---|---|
| Reality delta + R0 probes (P1–P6, H-275, ordering) | 2.0M |
| Compiler + Work Unit contract | 2.5M |
| Tool / Skill / Agent linkers | 2.5M |
| Constitution linker (main enforce) | 1.2M |
| Memory + Evidence linkers (ingestion projection, page store) | 2.5M |
| Semantic CSE | 0.5M |
| Firewall wiring + receipts + telemetry | 1.5M |
| Page faults + prefetch | 1.0M |
| Intra-epoch governor + epoch compiler + Semantic GC/ASER bridge | 4.5M |
| PGO + invalidation | 1.2M |
| Autonomy CI | 3.0M |
| First-call benchmark (6 arms × 3) | 1.5M |
| Multi-call benchmark (3 arms × fixed WU) | 4.0M |
| Madzia R4 canary (CCR overhead; worker spend books to KSR goal) | 2.0M |
| Second Work Class / self-host | 2.5M |
| Global promotion + boundary.py retirement patch | 1.0M |
| Knowledge Vault / FIOS / UKDL / CBR | 1.5M |
| Recovery reserve | 4.0M |
| Meta-optimisation tax | 2.0M |
| **Total P50** | **39.4M** |
Semantic lower bound 12M · LOWER 26M · **P50 39M** · P80 50M · P95 62M (confidence medium; widest terms: multi-call benchmarks and P5/P6 outcomes). **HARD AUTHORITY requested: goal ccr cap raised to 4.15M used + P80 50M = 54.2M.**

## 12. Owner approval envelope (one reply)
In scope: everything above, autonomously, in rings R0→R1→R4→R2→R3→R5. May modify: `mods/cpp-cognitive-runtime/**`, `tools/ccr_*.py`, `tools/test_ccr*.py`, `vault/programs/ccr/**`, `vault/plans/ccr-*`, knowledge/UKDL/CBR entries; global `~/.claude/ccr/**` (new releases, modes.json) with backup before each; KSR `tools/kobiimii/{boundary.py,ctx_ablation.py,test_boundary.py}` **only** when they are clean, the driver is stopped at a boundary, path-scoped commit. Global install may be updated (new release); running sessions are not hot-reloaded (they pick it up at restart). Rollback authority: mine, any time. Security exclusions: managed tier, settings hooks, HARD-RULES digest, secrets, other sessions' files. Genuine Owner boundaries left: a P1/P5/P6 result that makes the target unreachable (re-scope), a quality stop-loss on R4 Madzia, spend past the cap, any managed-policy change.
**Reply `y go p80` (54.2M) or `y go p95` (66.2M).**
