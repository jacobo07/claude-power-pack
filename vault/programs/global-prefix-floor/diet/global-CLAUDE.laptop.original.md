# Claude Code — Global Config (K-Router v2.1)

## HARD RULES — ROUTER (global, sealed 2026-05-29)

Before any of the three trigger actions below, read the compiled digest `~/.claude/knowledge_vault/core/HARD-RULES-DIGEST.md` (~2 KB, always readable), match the action to a trigger class, and fetch that class's rules IN FULL:

```
python ~/.claude/skills/claude-power-pack/tools/hardrule_compile.py --class DEPLOY
```

Violación de un HR-NN = STOP inmediato + reporte al Owner. Sin excepción.

Triggers (any one fires the read):
1. `files/write` to production (any deploy substrate — load-bearing config.yml, server.properties, plugins/*/data/*, etc.)
2. Any deploy to a live server (Pterodactyl `power: restart|start`, JAR upload to /plugins, schematic paste, world-edit on prod)
3. Declaring a server / feature as "done" (commit subject containing "done", "ready", "ship", "v\d+ final", or a human-facing completion claim)

Trigger 4 (plugin install) RETIRED 2026-07-27 -- zero corpus in 148 compiled rules. Machine-checked in `modules/rule_compiler/digest.py` `RETIRED_CLASSES`, which keeps the class defined, carries the reopen condition, and raises if it is ever silently dropped.

Anatomy of a Hard Rule: `TRIGGER` (when it fires) · `ACCIÓN` (STOP + the verification/backup ritual) · `EXCEPCIÓN` (the literal Owner phrase authorizing bypass for ONE turn) · `ORIGEN` (the incident that birthed it).

Añadir HR nuevo = 1 entrada en el UKDL §HARD-RULES del proyecto donde apareció el bug, 0 cambios en este router.

UI/design work → check UKDL `HR-VISUAL-01` + `HR-VISUAL-02` BEFORE any token/style edit. A UI calco needs pixel-exact tokens (source of truth = rendered pixels, never code/config) AND layout/navigation matching the source app. Screenshot comparison vs the primary source is a mandatory done-gate; HTML-reference-first, code-second is inviolable. Generalizes (PR-VISUAL-01): never declare done from a secondary artifact without validating against the primary source.

Digest-repair history + full visual doctrine: `~/.claude/knowledge_vault/claude-doctrine/hard-rules-router-detail.md`.
## Background Process Hygiene (MANDATORY)
On Windows, `run_in_background: true` spawns a child tree TaskStop does NOT reliably reap (next/turbopack, Playwright MCP, corepack all fan out helper node processes).
- Background dev servers/watchers spawn ONLY when the current turn needs them. Kill with TaskStop AND verify the reap before turn end.
- Never start a second dev server on the same port while the first is alive — TaskStop + restart, never overlap.
- `browser_close` closes the TAB, not the MCP server tree; children become zombies after disconnect.
Safety net: `~/.claude/hooks/orphan-dev-server-reaper.ps1` (SessionEnd) reaps orphan node.exe against a tight allow-list. Detail: `~/.claude/knowledge_vault/claude-doctrine/windows-execution-detail.md`.
## Windows Execution (MANDATORY; hook-enforced, full text + incidents: `~/.claude/knowledge_vault/claude-doctrine/windows-bridge-and-closer-doctrine.md`)
Guards: `windows-bash-bridge-guard.js` (blocks + delivers the pivot), `closer-guard.js` (Stop), `agent-solo-guard.js` (Agent bound). Read the full file when a guard blocks, a sentinel fires, or before building ssh scripts from PowerShell.
- Bash is not the default on Windows: hook-enforced (windows-bash-bridge-guard, test `hooks/_tests/test-bash-bridge-guard-v15.js` 31/31); the block message delivers the PowerShell pivot.
- Never `sleep && read`, `tail -f`, or `python ... | head` through Bash. On `[Tool result missing due to internal error]`: verify state first, never retry the same shape, re-issue only the single failed call.
- **PowerShell -> ssh:** never pipe a here-string (BOM). Write a no-BOM LF temp file, run `cmd /c "ssh -i $key -o BatchMode=yes $target bash -s < $tmp"`; keep `${VAR%%@*}`-style expansion and `rm` out of remote bodies built in PowerShell. Remote long-lived tools: nohup + disown server-side.
- **Batch caps:** <=4 Read/Glob/Grep, <=3 Edit/Write on different files, <=2 shell calls; never two Edits on one file in a batch; producer and consumer in separate batches. An `Agent` call and a `run_in_background` call are each SOLO in their message.
- **Subagents:** <=2 in parallel; every prompt carries "Prefer Read/Grep/Glob; avoid Bash, use PowerShell", a write-as-you-go deliverable path, and a bound. On a subagent sentinel: do it inline or re-dispatch ONE agent.
- **Never background a verification you need this turn** (foreground, bounded, narrowest scope). Script polling loops carry a hard timeout (180 s default).
- **A `<task-notification>` is work, not an ack:** Read its output file in that same turn and continue; never poll or re-run to check status.
- **Every turn ends with text:** a deliverable or a concrete question; never "waiting / standing by / in progress", never a bare "Let me X." closer. After a sentinel: name the dropped frame, re-issue it alone, state the next action.
- A guard ships with a test that drives its red branch; a tool rename must degrade to "fires too often", never "never fires".

## Global Alignment Ledger (MANDATORY)
Read `~/.claude/governance/GLOBAL_ALIGNMENT_LEDGER.md` at session start. Core Directives always apply. Flywheel: "SYSTEM OVERRIDE: Register error in domain [X]: [description]".

## CARL Integration
Follow all rules in <carl-rules> blocks from system-reminders.

## Sovereign Baseline (Apex Standard)
KARIMO (PRD auto-ingest) ∩ Design (`/cpp-design`, atomic branding) ∩ Lazarus (heartbeat + FTS5). Every multi-file build inherits all three.
- Raw PRD in the prompt → `/cpp-prd-parse <file|text>` (or the `prd-keyword-sentinel` hook on `PRD:`/`<prd>`) before Q&A.
- **Apex completeness mandate (BL-0068)**: every NEW multi-file stream MUST pre-wire (1) an isolated FTS5 sidecar (own table+triggers, never `turns_fts`), (2) a deterministic fail-open keyword-sentinel where a raw-input fast path exists, (3) atomic design-token isolation for any UI. Plan-time audit, not a runtime hook.
- DONE for a KARIMO build = `python tools/test_karimo.py` exit 0.
Detail (axes, parsers, Jobs/Woz token budget): `~/.claude/knowledge_vault/claude-doctrine/sovereign-baseline-detail.md`.
## Session Safety (UNIVERSAL LAW)
See `~/.claude/SESSION_SAFETY_CONTRACT.md`. Durability (§1 Sacred Invariant: no `.jsonl` destroyed by automation) + Discoverability (§8: a `.jsonl` invisible to `/resume` is loss-equivalent). Conflicts → contract wins.

## Knowledge Vault Protocol (Obsidian-native)
All rules live in `~/.claude/knowledge_vault/` (also openable as Obsidian vault).
Classify task tier, then Read relevant vault files before writing code:
- **LIGHT**: Router rules below suffice. No vault read needed.
- **STANDARD** (1-5 files): `core/mistakes-global.md` + `core/leyes-core.md` + `core/protocols.md`
- **DEEP** (5+ files): STANDARD + `core/quality-gates.md` + domain files
- **FORENSIC** (prod risk): ALL vault files
Full index: `~/.claude/knowledge_vault/INDEX.md` | Sync: `python tools/vault_sync.py --validate`
- **Documentation contract (KobiiDistillerOS v1.2 Sovereign Sealing):** every project distillation MUST conform to the 22-section schema (`~/.claude/skills/claude-power-pack/tools/distiller/schema.json`) — Tandas T1/T2/T3 × Partes I/II/III, voice-gate enforcing. Triggered by `/cpp-distill`.

## ExecutionOS Lite (Tiered Loading)
Load from `~/.claude/skills/claude-power-pack/modules/executionos-lite/`:
- LIGHT: `core.md` only. STANDARD: +phases. DEEP: +overlays. FORENSIC: +artifacts.
- Auto-Invoke: explicit criteria below. Tier self-assessment is NOT the gate (T-PP-SILENT-SKILL-001).

## PP Activation Criteria (MANDATORY — every repo, not just the PP repo)
Invoke the `claude-power-pack` skill when the task matches a row. Do not wait for a "STANDARD+" judgement — an implicit criterion is not a criterion (PR-PP-ACTIVATION-EXPLICIT-001).

| If the task involves | Invoke PP for |
|---|---|
| Architecture / design decision, new system from scratch | `/ultra` 7-phase, ExecutionOS tiers, spec gate |
| Multi-file feature (>1 file, >50 lines new) | Plan-first gate, Intent-Lock, One-Shot contract |
| A failure that recurred across sessions | CEPS recurring-error analysis, bug-to-hardrule |
| "is this done" / "ready to ship" / any deploy | Zero-issue completion gates, DEPLOY hard rules |
| Code review, quality, security audit | `pp-code-reviewer`, UQF, Pre-Report Gate |
| Datasets, knowledge vault, distillation | `/cpp-distill`, knowledge graph, UKDL |
| Token / context / cost pressure | `tco_compact_gate`, token austerity, model routing |
| Session recovery, handoff, multi-session work | Lazarus, `/kclear`, RESUMPTION_FILE |
| Infra, VPS, daemons, hooks | Infrastructure part, zero-crash, `/liveness` |
| Owner mentions a new brand/logo/identity; requests any visual asset, variant set, palette, or typography; or a project needs a brand package | `cpp creative init <project>` (CCF, `modules/ccf/`) — brief→spec→generate→select→package pipeline, produces config.json/spec.json then a PDF brand kit; trademark-collision-scanned before release |

Silence is a decision too: on a trivial single-file edit, do NOT invoke PP.

## Governance Overlay Auto-Activation
When ANY dev skill activates, load from `modules/governance-overlay/`:
- Always: `core.md`. STANDARD+: +`pre-task.md`+`pre-output.md`. DEEP+: +`during-task.md`. FORENSIC: +`mistakes-registry.md`.

## First-Time Project Setup
Check `~/.claude/projects/{project-id}/.bootstrapped`. If missing: run `node ~/.claude/hooks/token-optimizer-bootstrap.js`, check MCP servers, create marker.

## KobiiAI Stack
See `~/.claude/knowledge_vault/stacks/kobiicraft-ai.md`. Frontend=frozen (Next.js 16+React 19+Prisma+SQLite). Backend=Elixir/OTP/Phoenix.

## USAP — Universal Skill Activation Protocol (MANDATORY)
Activate ALL relevant domain skills before writing code. Governance auto-triggers with any dev skill. Pre-commit gate: code-reviewer for 3+ files. Evidence: list activated skills on completion.

## Critical Rules (Inlined — Always Active)
- **Ley 26**: >1 file = Plan-first. No plan = no edits.
- **Ley 28-29**: Terminal autonomy. Agent executes via Bash/SSH. NEVER outsource to Owner.
- **Mistake #16**: Compiles != works. Grep callers. Integration test before units.
- **Mistake #17**: Static verification does NOT prove runtime works.
- **Ley 24**: Crashed system = radioactive. Null-guards + diagnostic logs.
- **Ley 25 + Gate 7**: DONE = QA Pipeline PASS with observed evidence.

## Anti-Antipattern Protocol
8 mandatory rules (Rule 1 hook-enforced): `~/.claude/knowledge_vault/core/anti-antipatterns.md`.
**Regla 12 — 2-CONSECUTIVE-FAILURES LAW.** Same tool-call shape failing twice (same structure, same error class) → MANDATORY PIVOT: a different code path, tool, or abstraction layer. Not a retry, not a sleep, not a tweak. Applies to every tool (HTTP 4xx/5xx, ssh resets, npm, FileNotFound, Permission denied). On the 2nd identical failure write a 1-line diagnostic, then change approach; never a 3rd attempt of the same shape.
## Sovereign Standard (Mandatory Baseline)
- **ULTRA mandate**: every multi-file build (>1 file, >50 lines new) MUST run `/ultra plan <target>` — 7 phases, Q&A pause non-skippable.
- **Apex Completion Standard**: every new feature ships Axis A (Intent-Lock concurrent-exec protection, fail-open) + Axis B (async background auditing, READ+PROPOSE-only).
- **Future skills MUST be latent-card + JIT-full-depth, never always-on.**
Detail (Lazarus resurrection, Compound Learnings, GraphQL/JIT baseline, register commands): `~/.claude/knowledge_vault/claude-doctrine/sovereign-standard-detail.md`.
## Environment Awareness (MANDATORY — every project, every session)
Detect host before deciding execution path. Probe: `uname -s 2>/dev/null && whoami`.
- **Linux + user `kobicraft`** → **Sovereign VPS** (`204.168.166.63`, KobiiClaw). You ARE the VPS — exec `mix`, `npm`, `pm2`, `psql`, `systemctl` natively via Bash. Wrapping in `ssh kobicraft@204.168.166.63 ...` from inside the VPS is a self-detect failure; refuse and re-exec native.
- **Windows (`win32` / cmd / PowerShell)** → **Local dev**. SSH bridges to VPS work. Default key: `~/.ssh/kobicraft_vps`. Use `~/.ssh/kobicraft_gex44` only for KobiiCraft / KobiiSports Resort / video-pipeline work. Other VPS hosts: declare per-project before SSH.
- Project-specific build / deploy commands belong in per-project `CLAUDE.md`, never here.

## Reality Contract (MANDATORY — every file you ship)
Zero placeholders, zero mocks, zero stub returns, zero empty catch blocks in production code. If a feature cannot be wired end-to-end this turn, do NOT scaffold the shell: state the gap and stop. Enforced by the `scaffold-auditor.js` Stop hook and the Jobs/Woz write gate; violations create `BLOCKED_DELIVERY.md` (Mistake #16, Scaffold Illusion).
The exhaustive banned-token list, and the Analytical-Log Exemption for detectors that must legitimately carry those tokens: `~/.claude/knowledge_vault/claude-doctrine/reality-contract-detail.md`.
## Context Pressure Response
On a Stop-event `decision:"block"` whose reason contains `CONTEXT THRESHOLD CROSSED` (the wall is 70% by default, but a run may narrow it per session via `gsd_long_run.py thresholds`, so read the percentage in the message rather than assuming): the watchdog has ALREADY written the checkpoint and dropped the trigger flag. End your next response with a SINGLE trailing line, no preface, no markdown, exactly: `/compact focus on <5-12 word current-task summary>`. **Delivery is exact or nothing.** The daemon routes that line by SESSION id to the terminal inbox, and it is typed only if the extension that owns that terminal accepts — focus is never consulted, and neither is the window title. With no owning extension the request is REFUSED and ledgered, nothing is typed into whichever window is in front, and the Owner submits the line in the pane. The old foreground-SendKeys fallback is Owner opt-in only (`CPP_LEGACY_FOREGROUND_SENDKEYS=1`): unconditional, it is what typed `/absw2-continue` into a stranger's session on 2026-09-18.
Detail (checkpoint paths, daemon, BL-0003 precedent): `~/.claude/knowledge_vault/claude-doctrine/context-pressure-detail.md`.
## ULTRA / ONESHOT Protocol (BL-0063 / MC-SYS-118) — UNIVERSAL LAW
`/ultra plan <target>` activates the 7-phase ONESHOT workflow: 1) Ultra Plan, 2) Q&A Pass (6 questions, MANDATORY stop), 3) Revised Plan, 4) Audit (spawn `oneshot-architect-auditor` sub-agent), 5) Fix Injection, 6) Auto Mode Execution, 7) Real-input Verification. Skipping phase 2 is REJECTED — six honest answers > one vague paragraph. Plan-quality is bounded by prompt-quality. See `~/.claude/commands/ultra.md`. **MANDATORY in every repo**: any `/ultra plan` invocation MUST execute all 7 phases in order, no skipping, no fast-pathing; `subagent_type: oneshot-architect-auditor` is globally dispatchable; PP mirrors at `commands/ultra.md` + `agents/oneshot-architect-auditor.md` are the version-controlled reference.

## Completion Gates (MANDATORY)
Run ALL applicable: 1. tsc --noEmit 2. Lint 3. Build 4. Tests 5. Schema 6. Scaffold Audit 7. Empirical Evidence

## Intent Compiler (MANDATORY for code tasks)
DECOMPOSE → SUBJECTIVE CHECK → VERIFY UNDERSTANDING → LEDGER CHECK → EXECUTE → VERIFY → AUTO-REGISTER

## Token Efficiency (MANDATORY)
CLAUDE.md < 100 lines. MEMORY.md < 200 lines. Parallel-first tool calls. Read>cat, Edit>sed, Grep>rg, Glob>find.
Before re-reading source during audit, check `_audit_cache/source_map.json`. Hash match = use cached summary.
Vault entries are 1-line compressed. For verbose explanation, Read `_details/` subfolder (never auto-loaded).

## Anti-Overlap (shared repos)
Fetch-first + pathspec-scoped commits: RETIRED R268 → `~/.claude/rules/concurrent-writers-shared-tree.md` (richer; names pathspec's file-granular limit).

**Message-leg caveat:** pathspec scoping does NOT close the shared `.git/COMMIT_EDITMSG` race. After every commit verify `git log -1 --format='%s'` matches your tempfile's first line; if not, `git commit --amend -F <msgfile>`.

**HR-G2-REBASE-RACE:** never rebase while G2 (`pp-code-reviewer` / `woz`) is reading the worktree — it changes the file under analysis and can invalidate the APPROVE. Wait for the verdict.

Rationale + deferred worktree-per-pane migration: `~/.claude/knowledge_vault/claude-doctrine/commit-doctrine-detail.md`.
## Session Logging
RETIRED R268 → mechanised by `session-logger.js` in the dispatcher.

## Sovereign RTK Baseline (Token Proxy)
RTK ("Rust Token Killer", MIT) is a per-command output compressor (`~/.claude/bin/rtk.exe`) wired as a fail-open PreToolUse Bash rewriter. **Compliance: RTK proxy must be active/available.** Binary/hook wiring, Owner activation command + DONE-gate (`verify_rtk_fusion.py`, PASS ≥60 %) → `~/.claude/knowledge_vault/claude-doctrine/rtk-baseline-detail.md`.

## Vault Index
Full index + Obsidian graph: `~/.claude/knowledge_vault/INDEX.md`
NexumOps (143 files): `C:\Users\User\Desktop\Repos-GitHub\knowledge_vault\base-knowledge-vault\00_Governance\nexumops\`

## Agent Teams — HANDOFF BLOCK (MANDATORY session-output discipline)
Every pane ends its session with a compact HANDOFF BLOCK as the LAST visible content — nothing after it. Fixed ≤8 lines: `PANE / SPRINT / STATUS (COMPLETE|BLOCKED:<reason>|STANDBY) / LIVE (last main hash, git-log-verified, never a rebasable local hash) / NEXT (one action) / DEBT (or NONE)`. Detail: `~/.claude/knowledge_vault/claude-doctrine/session-continuity-detail.md`.
## Long-Session Resumption — RESUMPTION_FILE (MANDATORY, multi-session)
Any task spanning more than one session MUST maintain `RESUMPTION_FILE.md` at the project root: a self-contained execution prompt (<400 words, imperative) that a fresh session reads to continue with zero prior context. Five blocks: identity/path/thesis · exact state (sealed vs pending + a coherence anchor) · active decisions · next 3 concrete actions · start instruction. **Update after EVERY sealed unit, never only at the end** — write proactively at ≤70% context, so a mid-run crash always leaves a valid resume point.
Detail + origin: `~/.claude/knowledge_vault/claude-doctrine/session-continuity-detail.md`.
## SDD-OS — Spec-Driven Development (MANDATORY, every repo)
Spec First. Execution Second. Validation Always. Classify EVERY task 0-3 before executing; not a judgment call.
T0 typo/label → inline mini-spec (objective/scope/acceptance). T1 option/command/clear-cause bug → brief spec + impact map + regression risk.
T2 agent/workflow/module/endpoint/integration/persistence/auth/billing/migration → written spec BEFORE the first edit (PRD + Arch Spec + AC + rollback).
T3 new OS/standard/framework/security layer/cross-repo → T2 + governance + migration + kill switches.
Also T2+ on: user-behaviour change, persisted data, multi-file, regression risk, new reusable standard, or "done" not clearly stateable. T2+ without a spec is prohibited (PARTE I §4).
A spec covers a task ONLY via `covers: [tokens]` front matter — without it, a pile of old plan files does NOT satisfy the gate.
`/cpp-sdd-os` · full rules: `skills/claude-power-pack/governance/SDD_OS_GOVERNANCE.md`
