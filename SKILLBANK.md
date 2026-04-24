---
title: Claude Power Pack SkillBank (Index)
tier: discovery
purpose: Single-page index of every activatable surface in this skill. Makes the pack's capabilities scannable without grepping. Each row names a Skill, its Type (command / module / sleepy-part / tool), and the 1-line Process → Rules → Output contract.
---

# Claude Power Pack SkillBank (Index)

> This index is **documentation**, not the loader. Actual routing lives in `SKILL.md` (tier table + triggers) and `parts/core.md` PART A0 (manifest scan). The SkillBank names what's available so a new user can answer "what can this pack do?" in one scan.

## How to read

- **Skill** — the activation name (slash command, module directory, sleepy part, or tool CLI).
- **Type** — `cmd` (user-facing slash command) / `mod` (internal module loaded by overlay) / `sleepy` (on-trigger content block) / `tool` (CLI script).
- **Process** — what happens when this skill runs, in one line.
- **Rules** — hard constraints the skill enforces or obeys.
- **Output** — the observable artifact produced.
- **Path** — where the skill lives.

## Slash Commands (10)

| Skill | Type | Process | Rules | Output | Path |
|-------|------|---------|-------|--------|------|
| `/audit-all` | cmd | Unified breadth-first audit across every subsystem in current repo — scores on edit-thrashing / drift / completion / env-mapping + OVO delta overlay. | Zero-stub policy enforced; drill-down via `/audit-all <N>` or by subsystem id. | Summary table + GREEN/YELLOW/ORANGE/RED verdicts + oracle_delta footer. | `commands/audit-all.md` |
| `/investment-ready-audit` | cmd | Project-agnostic investor-grade scoring on 5 axes: Scalability / Resilience / Traceability / Zero-Stub / ROI-Wiring. | Zero-Stub weighted 3×, ROI-Wiring 2×; verdict thresholds 85/75/60. | Progress-bar summary + per-axis + per-subsystem table + Series-A/Seed/Angel/NotInvestable verdict. | `commands/investment-ready-audit.md` |
| `/ira` | cmd | Alias for `/investment-ready-audit` — short-form invocation for quick runs. | Same engine, same thresholds. | Same as `/investment-ready-audit`. | `commands/ira.md` |
| `/cpp-autoupdate` | cmd | Toggle automatic update-check on session start. | Must not block session startup. | Boolean flag in settings. | `commands/autoupdate.md` |
| `/cpp-customclaw create <name>` | cmd | Scan current project, generate a custom AI daemon tailored to its stack. | Project-aware; must not overwrite existing daemons; 11 stacks supported (GAL v1.6). | New daemon module + command. | `commands/customclaw.md` |
| `/obsidian-setup` | cmd | Generate a Knowledge Graph vault from the current project. | Max 10 nodes per task; follows wikilinks. | `_knowledge_graph/INDEX.md` + node files. | `commands/obsidian-setup.md` |
| `/resume` | cmd | Restore context from previous session via Lazarus Protocol. | Read `HANDOFF_TASK.md` if present; `/resume last` = instant warm-up. | Session rebirth with prior state. | `commands/resume.md` |
| `/cpp-update` | cmd | Update Claude Power Pack to latest from GitHub. | Preserves local patches; reapply via `gsd:reapply-patches`. | Updated SKILL.md + modules. | `commands/update.md` |
| `/cpp-vault-setup` | cmd | Extract monolithic CLAUDE.md into an Obsidian governance vault. | On-demand loading; keeps CLAUDE.md < 100 lines. | `~/.claude/vault/INDEX.md` + topic pages. | `commands/vault-setup.md` |
| `/cpp-vault-sync` | cmd | Regenerate governance vault INDEX.md + sync metadata. | Wikilinks must resolve; entries 1-line compressed. | Refreshed INDEX.md + frontmatter. | `commands/vault-sync.md` |

## Modules (13)

| Skill | Type | Process | Rules | Output | Path |
|-------|------|---------|-------|--------|------|
| `agent-governance` | mod | AGT policy scaffolding, Ring 0-3 privilege mapping, OWASP ASI 10-item check. | Default Ring 3 (least privilege); kill switch required per loop. | Policy file + agent audit. | `modules/agent-governance/` |
| `agent-lightning` | mod | Lightweight agent dispatch shim. | Respects blast-radius limits. | Dispatched task result. | `modules/agent-lightning/` |
| `autoresearch` | mod | Self-improving competitive intelligence (3-4×/day on every SaaS). | RSS + YouTube firehose + cross-signal bus. | `signal_scorer` rankings. | `modules/autoresearch/` |
| `daemon` | mod | Background daemon orchestration for long-running agents. | OTP-style supervision preferred (Elixir-first for score ≥2). | Supervised daemon process. | `modules/daemon/` |
| `dispatcher` | mod | Task router across skills, modules, and sub-agents. | Skills > MCP tools (MCP costs 13-14% context). | Dispatch verdict. | `modules/dispatcher/` |
| `executionos-lite` | mod | Tiered loading engine: LIGHT / STANDARD / DEEP / FORENSIC. | Overlay match per domain (python/typescript/minecraft/…). | Loaded overlay content. | `modules/executionos-lite/` |
| `governance-overlay` | mod | Full lifecycle interception: pre-task / during-task / pre-output / post-output + Council of 5. | Blocks on Council B/REJECT; max 3 recovery iterations. | Verdict + failure capture. | `modules/governance-overlay/` |
| `infrastructure` | mod | VPS + daemon + shared-infra helpers. | No destructive ops without confirmation. | Infra config + health report. | `modules/infrastructure/` |
| `memory-engine` | mod | Hot/cold context splitter; session handoff builder. | Hot ≤ 200 lines; cold paged on demand. | `HANDOFF_TASK.md` + memory index. | `modules/memory-engine/` |
| `omnicapture` | mod | Telemetry capture for forensic post-mortems. | No PII in captures; opt-in per project. | Capture bundle. | `modules/omnicapture/` |
| `sleepless_qa` | mod | Closed-loop empirical verification pipeline for any repo. | Ley DNA-400 mandate: sandbox/synthetic-test evidence per complex-logic delivery. | `verdict.json` + captured stdout. | `modules/sleepless_qa/` |
| `token-optimizer` | mod | CLAUDE.md linter, cross-project dedup, prompt pattern optimizer, session cost estimator. | CLAUDE.md < 1500 words; MEMORY.md < 200 lines. | Compressed files + cost report. | `modules/token-optimizer/` |
| `zero-crash` | mod | TTY isolation, advisory quality gates, process sandboxing, golden-pattern injection. | TTY restore mandatory after every Bash. | Sandboxed shell + gate verdict. | `modules/zero-crash/` |

## Sleepy Parts (10 — load only on trigger)

| Skill | Type | Process | Rules | Output | Path |
|-------|------|---------|-------|--------|------|
| `agent-governance` (W) | sleepy | Load when task involves agent systems. | Triggers on `langchain/langgraph/crewai/autogen/ag2/claude_agent_sdk/semantic_kernel`. | Agent overlay rules loaded. | `parts/sleepy/agent-governance.md` |
| `autoresearch` (G) | sleepy | Load on /autoresearch or competitive research. | Cross-signal dedup; score threshold. | Research rules loaded. | `parts/sleepy/autoresearch.md` |
| `executionos` (I) | sleepy | Load when user requests ExecutionOS / governance overlay. | Follows tier routing. | ExecutionOS rules loaded. | `parts/sleepy/executionos.md` |
| `frontend` (F) | sleepy | Load on React / Next.js / Vue / CSS / frontend keywords. | Distinctive-design bias; avoids generic AI aesthetics. | Frontend rules loaded. | `parts/sleepy/frontend.md` |
| `governance-vault` (GV) | sleepy | Load on vault / leyes / mistakes / gates / vault-sync. | Max 5 vault pages per task. | Vault rules loaded. | `parts/sleepy/governance-vault.md` |
| `infrastructure` (O+P+S+V+X) | sleepy | Load on daemon / dispatch / omnicapture / infra / VPS. | Ley 28-29: terminal autonomy, no outsourcing. | Infra rules loaded. | `parts/sleepy/infrastructure.md` |
| `knowledge-graph` (KG) | sleepy | Load on knowledge graph / graphify / obsidian / vault. | Max 10 graph nodes per task. | KG rules loaded. | `parts/sleepy/knowledge-graph.md` |
| `token-tools` (C+H+R) | sleepy | Load on token audit / compress / dedup / optimize. | Must cite savings in tokens. | Token-tools rules loaded. | `parts/sleepy/token-tools.md` |
| `video-re` (VRE) | sleepy | Load on reverse engineer / video analysis / YouTube / competitor / SOTA. | Frame-by-frame citation required. | Video-RE rules loaded. | `parts/sleepy/video-re.md` |
| `zero-crash` (ZC) | sleepy | Load on zero-crash / TTY / sandbox / process isolation. | TTY restore after every command. | Zero-crash rules loaded. | `parts/sleepy/zero-crash.md` |

## Tools (CLI scripts, 11)

| Skill | Type | Process | Rules | Output | Path |
|-------|------|---------|-------|--------|------|
| `audit_cache.py` | tool | Hash-based source file skip for FORENSIC audits. | SHA-256 truncated 16-char; skip `.git/node_modules/target/build/dist/__pycache__`. | `_audit_cache/source_map.json`. | `tools/audit_cache.py` |
| `baseline_ledger.py` | tool | Multi-axis ecosystem-baseline tracker (k_qa, k_router, engineering_baseline, highest_dna). | Monotonic elevation; CD#10 no-BOM. | `~/.claude/vault/global_baseline_ledger.json` + Obsidian mirror. | `tools/baseline_ledger.py` |
| `chatgpt_distiller.py` | tool | Distill ChatGPT transcripts into vault entries. | Strips PII; tags entries. | Distilled .md in vault. | `tools/chatgpt_distiller.py` |
| `council_verdict.py` | tool | Record a Council-of-5 verdict artifact. | Verdict grade A+/A/B/REJECT only. | Verdict JSON. | `tools/council_verdict.py` |
| `kobi_graphify.py` | tool | Knowledge Graph engine for Obsidian vaults. | Resolves wikilinks; caps node count. | `_knowledge_graph/*` files. | `tools/kobi_graphify.py` |
| `memory_manager.py` | tool | Hot/cold memory splitter + session-log cleaner. | Hot ≤ 200 lines; cold paged. | Updated MEMORY.md + cold archive. | `tools/memory_manager.py` |
| `mistake_frequency.py` | tool | Mistakes→Curriculum counter; top-N query for pre-task watchlist. | Threshold default 3; Mistake-IDs `M<N>` only. | `modules/governance-overlay/mistake-frequency.json`. | `tools/mistake_frequency.py` |
| `obsidian_enrich.py` | tool | Enrich vault entries with frontmatter + wikilinks. | Existing frontmatter preserved. | Enriched .md in vault. | `tools/obsidian_enrich.py` |
| `vault_extractor.py` | tool | Extract monolithic CLAUDE.md into topic pages. | Each page ≤ 100 lines; index entry 1-line. | Topic pages + INDEX.md. | `tools/vault_extractor.py` |
| `vault_sync.py` | tool | Regenerate vault INDEX.md + sync metadata. | Wikilinks must resolve. | Refreshed INDEX.md. | `tools/vault_sync.py` |
| `electron_priority_manager.ps1` | tool | OS priority management for Electron (Cursor/VSCode) during Claude work. | No kill of user processes without confirm. | Process-priority adjustments. | `tools/electron_priority_manager.ps1` |

## Activation Flow (for reference)

1. `SKILL.md` is always loaded → picks tier + routes to `parts/core.md` + `parts/execution.md`.
2. `parts/core.md` PART A0 scans the workspace → derives STACK / DOMAIN / OVERLAY.
3. Sleepy parts load only on trigger match (see top of `SKILL.md`).
4. Modules under `modules/*/` are loaded by overlays or invoked directly by commands.
5. Tools under `tools/*` are CLI-invoked (by commands, by hooks, or by the operator).

## Not Listed Here

- Hooks under `modules/*/hooks/` and `~/.claude/hooks/` — these are event-wired, not slash-addressable. See `~/.claude/settings.json` hook table for the authoritative list.
- `.claude/settings.local.json` — machine-local permission allowlist; managed by `/cpp-allow` or the `fewer-permission-prompts` skill.
