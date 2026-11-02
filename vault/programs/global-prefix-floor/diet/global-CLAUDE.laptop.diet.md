# Claude Code — Global Config (K-Router v2.1, laptop; GPF diet 2026-11-02)

Compiled from the laptop's own file (original: `vault/programs/global-prefix-floor/diet/global-CLAUDE.laptop.original.md` in the PP repo). Detail lives in `~/.claude/knowledge_vault/claude-doctrine/` (never auto-loaded).

## HARD RULES — ROUTER (sealed 2026-05-29)
Before (1) `files/write` to production, (2) any deploy to a live server (Pterodactyl power, JAR upload, schematic paste, prod world-edit), (3) declaring a server/feature "done" (commit subject with done/ready/ship/`v\d+ final`): read `~/.claude/knowledge_vault/core/HARD-RULES-DIGEST.md`, match the class, fetch it IN FULL (`python ~/.claude/skills/claude-power-pack/tools/hardrule_compile.py --class DEPLOY`). A violated HR-NN = immediate STOP + report to the Owner. New HR = one UKDL §HARD-RULES entry in the project where the bug appeared. UI/design work: `HR-VISUAL-01/02` first (pixel-exact tokens; screenshot vs primary source is the done-gate). Detail: `claude-doctrine/hard-rules-router-detail.md`.

## Windows Execution (hook-enforced; detail `claude-doctrine/windows-bridge-and-closer-doctrine.md`, `windows-execution-detail.md`)
- PowerShell is the default; Bash is guarded (`windows-bash-bridge-guard.js`, its block message gives the pivot). Never `sleep && read`, `tail -f`, `python ... | head` through Bash.
- `[Tool result missing due to internal error]`: verify state first, never retry the same shape, re-issue only the single failed call.
- PowerShell → ssh: never pipe a here-string (BOM). Write a no-BOM LF temp file and feed it as stdin to `ssh ... bash -s`. Remote long-lived tools: nohup + disown.
- Batch caps: ≤4 Read/Glob/Grep, ≤3 Edit/Write on different files, ≤2 shell calls; never two Edits on one file in a batch; producer and consumer in separate batches. An `Agent` call and a `run_in_background` call are each SOLO in their message.
- Subagents: ≤2 in parallel; every prompt carries "Prefer Read/Grep/Glob; avoid Bash, use PowerShell", a write-as-you-go deliverable path and a bound.
- Background processes: spawn dev servers/watchers only when this turn needs them; TaskStop AND verify the reap; never two dev servers on one port; `browser_close` closes the tab, not the MCP tree.
- Never background a verification this turn needs (foreground, bounded). Polling loops carry a hard timeout (180 s). A `<task-notification>` is work: Read its output file in that same turn.
- Every turn ends with a deliverable or a concrete question; never "waiting / standing by / in progress", never a bare "Let me X." closer.

## Alignment, Safety, Knowledge
- Read `~/.claude/governance/GLOBAL_ALIGNMENT_LEDGER.md` at session start; obey `<carl-rules>` blocks. Session durability: `~/.claude/SESSION_SAFETY_CONTRACT.md` wins conflicts (no `.jsonl` destroyed by automation; one invisible to `/resume` counts as lost).
- Vault `~/.claude/knowledge_vault/` (INDEX.md). Tiers: LIGHT = this file; STANDARD (1-5 files) = `core/mistakes-global.md` + `core/leyes-core.md` + `core/protocols.md`; DEEP (5+) adds `core/quality-gates.md` + domain files; FORENSIC = all. ExecutionOS: `skills/claude-power-pack/modules/executionos-lite/`. Governance overlay (`modules/governance-overlay/`) loads with any dev skill.
- Sovereign baseline (KARIMO PRD ingest, `/cpp-design`, Lazarus; Apex mandate: FTS5 sidecar, keyword sentinel, design-token isolation for new multi-file streams): `claude-doctrine/sovereign-baseline-detail.md`, `sovereign-standard-detail.md`. Raw PRD in the prompt → `/cpp-prd-parse`. KARIMO DONE = `python tools/test_karimo.py` exit 0. Distillation: `/cpp-distill`.
- Stack `knowledge_vault/stacks/kobiicraft-ai.md` (frontend frozen Next.js 16 + React 19 + Prisma + SQLite; backend Elixir/OTP/Phoenix). First-time project: no `~/.claude/projects/{id}/.bootstrapped` → `node ~/.claude/hooks/token-optimizer-bootstrap.js`.

## PP Activation (invoke the `claude-power-pack` skill when the task is)
architecture/new system (`/ultra`) · multi-file feature >1 file/>50 lines (plan-first, Intent-Lock) · a failure recurring across sessions (CEPS) · "is this done"/ship/deploy (zero-issue gates, DEPLOY HRs) · code review/security audit (`pp-code-reviewer`) · datasets/vault/distillation · token/context/cost pressure (`tco_compact_gate`) · recovery/handoff/multi-session (Lazarus, `/kclear`) · infra/VPS/hooks/daemons (`/liveness`) · a new brand/logo/visual asset or palette (`cpp creative init <project>`). Trivial single-file edit: do NOT invoke. Activate ALL relevant domain skills before writing code (USAP); 3+ files → code-reviewer before commit.

## Critical Rules
- Ley 26: >1 file = plan first. Ley 28-29: terminal autonomy, never outsource to the Owner. Ley 24: a crashed system is radioactive (null-guards, diagnostic logs). Ley 25 + Gate 7: DONE = QA pass with observed evidence.
- Mistake #16/#17: compiles ≠ works, static ≠ runtime; grep callers; integration test before units.
- Reality Contract: zero placeholders/mocks/stub returns/empty catch in shipped code; if it cannot be wired end-to-end this turn, state the gap and stop (`scaffold-auditor.js`; `claude-doctrine/reality-contract-detail.md`).
- Completion gates: tsc --noEmit, lint, build, tests, schema, scaffold audit, empirical evidence.
- Intent compiler for code tasks: decompose → subjective check → verify understanding → ledger check → execute → verify → register.
- ULTRA: `/ultra plan <target>` runs all 7 phases incl. the mandatory Q&A stop (`commands/ultra.md`, auditor `oneshot-architect-auditor`); every multi-file build uses it. New skills are latent-card + JIT, never always-on.
- SDD-OS: classify every task T0-T3 first. T0 typo → inline mini-spec; T1 → brief spec + impact map; T2 (agent/module/endpoint/persistence/auth/billing/migration, user-behaviour change, multi-file, regression risk) → written spec BEFORE the first edit (PRD + arch + AC + rollback); T3 adds governance + kill switches. A spec covers a task only via `covers: [tokens]`. `/cpp-sdd-os`; `skills/claude-power-pack/governance/SDD_OS_GOVERNANCE.md`.

## Anti-Antipattern Protocol
8 rules (R1 hook-enforced): `~/.claude/knowledge_vault/core/anti-antipatterns.md`. **Regla 12**: the same tool-call shape failing twice (same structure, same error class) → write a 1-line diagnostic and pivot to a different path, tool or layer; never a third identical attempt.

## Environment, Commits, Context
- Host probe: `uname -s 2>/dev/null && whoami`. Windows = local dev (ssh key `~/.ssh/kobicraft_vps`; `~/.ssh/kobicraft_gex44` for GEX44 work). Linux + `kobicraft` = Sovereign VPS 204.168.166.63: exec natively, never ssh to self. Project build/deploy commands live in project CLAUDE.md.
- Shared repos: `~/.claude/rules/concurrent-writers-shared-tree.md`. After every commit check `git log -1 --format='%s'` matches your message (else `git commit --amend -F <file>`). Never rebase while G2 (`pp-code-reviewer`/`woz`) reads the worktree.
- Context pressure: on a Stop `decision:"block"` containing `CONTEXT THRESHOLD CROSSED`, end the next response with ONE trailing line, no preface, exactly `/compact focus on <5-12 word current-task summary>` (checkpoint already written; `claude-doctrine/context-pressure-detail.md`).
- Token austerity: CLAUDE.md < 100 lines, MEMORY.md < 200 lines; Read>cat, Edit>sed, Grep>rg, Glob>find; parallel tool calls; check `_audit_cache/source_map.json` before re-reading source; RTK proxy active (`claude-doctrine/rtk-baseline-detail.md`).
- Multi-session work keeps `RESUMPTION_FILE.md` at the project root (<400 words, five blocks, update after every sealed unit, write at ≤70% context). `claude-doctrine/session-continuity-detail.md`.
- Every pane ends with a HANDOFF BLOCK as the LAST visible content, ≤8 lines: `PANE / SPRINT / STATUS (COMPLETE|BLOCKED:<reason>|STANDBY) / LIVE (git-log-verified hash) / NEXT / DEBT (or NONE)`.
