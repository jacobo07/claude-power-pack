# Claude Power Pack v8.0

Universal AI execution framework for Claude Code. Zero-issue delivery, self-healing governance, tiered token loading, video-enhanced reverse engineering, project-aware daemon generation, and a cross-project engineering-rigor Flywheel.

**130+ files | 13 modules | 10 sleepy parts | 7 commands | 4 depth tiers | Cross-platform (Windows + Unix)**

See the [SkillBank Index](./SKILLBANK.md) for a scannable catalog of every command, module, sleepy part, and tool with their Process / Rules / Output contracts.

---

## Quick Start

```bash
# Unix/macOS/Linux
bash install.sh /path/to/project

# Windows PowerShell
.\install.ps1 -TargetDir "C:\project"
```

This installs:
- `USER_CRITERIA_MEMORY.md` — persistent learning file (AI reads before every task)
- Doctrine block in your `CLAUDE.md` — execution rules injected into project governance
- `claude-dispatch` — cross-repo prompt dispatcher
- `claude-daemon` — crash recovery loop with hardware-aware memory tuning
- `omnicapture-query` — runtime telemetry CLI
- `zero-crash-sandbox` — process isolation wrapper

---

## What's New in v8.0: CustomClaw

**The OpenClaw replacement that actually works with Claude Code's policies.**

```
/cpp-customclaw create my-helper
```

This single command scans your project, detects the stack (11 languages, 10+ frameworks), identifies structure patterns (monorepo, MVC, API-only, full-stack), reads your test/build/lint commands, and generates a **custom AI daemon** at `.claude/commands/my-helper.md` — fully tailored to your project.

**Supports:** Node/TypeScript, Python, Elixir, Rust, Go, Java/Kotlin, Ruby, C#/.NET, Dart/Flutter, PHP, C/C++, plus a generic fallback for anything else.

**Every generated daemon includes:**
- Stack-specific best practices (not generic advice — actual rules for your framework)
- Guardrails: max iteration caps, retry limits, forbidden file patterns (.env, secrets)
- Auto-detected project commands (test, build, lint, dev)
- The OBSERVE > PLAN > EXECUTE > VERIFY > HARDEN protocol
- Jargon-free explanation of what was created and how to use it

---

## The Flywheel Stack (recent)

Five interlocking systems that make engineering rigor compound across projects and sessions:

**1. Global Baseline Ledger** — `tools/baseline_ledger.py` tracks four independent rigor axes (`k_qa`, `k_router`, `engineering_baseline`, `highest_dna`) across every registered project. A Translator Hook (`~/.claude/hooks/baseline-translator.js`) fires on every prompt, detects which axis the prompt is advancing, and elevates the per-axis `global_max`. Obsidian mirror at `~/.claude/knowledge_vault/governance/global_baseline_ledger.md`.

**2. Council of 5 (TheWarRoom)** — `modules/governance-overlay/council.md` defines an inline 5-advisor structured self-review (Contrarian, First Principles, Expansionist, Outsider, Executor) that runs before every STANDARD+ emission. Verdicts are `A+/A/B/REJECT`; B or REJECT blocks output and triggers Rejection Recovery (max 3 iterations, then HALT). No external model calls — diversity comes from structured prompts, not sub-agents.

**3. Mistakes→Curriculum Loop** — `modules/governance-overlay/mistake-frequency.json` + `tools/mistake_frequency.py` count how often each Mistake-ID from the 51-entry registry recurs. Post-output failure capture increments the counter; pre-task Section 9 surfaces entries crossing the threshold (default 3) as a `WATCH: Mistake #N recurring` banner and auto-loads the prevention rule into the Never-Do Matrix. Recurring errors get more prompt real estate until they stop recurring. The Council's Howard's Loop also reads this file so advisors see recurring patterns on every verdict.

**4. Doctrine Law-ID Registry** — `knowledge/doctrine-laws.md` canonicalizes named doctrine laws (DNA-400 Supremacía Empírica, DNA-2500 Visual Sovereignty, DNA-25000 Global Singularity Baseline), keeping law identifiers separate from the rigor-measurement axis tracked in the ledger.

**5. Token Shield (Austerity Rule)** — `tools/audit_cache.py` + `_audit_cache/source_map.json` (SHA-256 integrity map) + `_audit_cache/semantic_tags.json` (capability-tag sidecar). Before Explore agents or bulk-reads, the Austerity Rule (in `SKILL.md` + `parts/core.md` PART Q) directs use of `--check-all` and cached `--summary <path>` output when hashes match. Raw-reads only on hash mismatch, missing cache, or explicit deep-refactor.

---

## How It Works: Tiered Loading

The Power Pack never loads everything at once. It classifies each task and loads only what's needed:

| Tier | When | What Loads | Token Cost |
|------|------|-----------|------------|
| **LIGHT** | Fix, lookup, single file | `core.md` only | ~800 tok |
| **STANDARD** | Feature, 1-5 files | core + `execution.md` | ~1,600 tok |
| **DEEP** | Architecture, 5+ files | core + execution + relevant sleepy parts | ~2,500 tok |
| **FORENSIC** | Production risk, prior failures | all parts | ~4,000 tok |

**Sleepy parts** cost zero tokens until triggered by keywords in your prompt. When you say "reverse engineer this competitor", only the Video-RE sleepy part wakes up.

---

## Commands

| Command | What It Does |
|---------|-------------|
| `/cpp-customclaw create [name]` | Scan project and generate a custom AI daemon tailored to its stack |
| `/cpp-update` | Update Claude Power Pack to the latest version from GitHub |
| `/cpp-autoupdate` | Toggle automatic update checking on session start |
| `/obsidian-setup` | Generate a Knowledge Graph vault from the current project (architecture discovery via wikilinks, max 10 nodes/task) |
| `/cpp-vault-setup` | Extract monolithic CLAUDE.md into an Obsidian-compatible governance vault |
| `/cpp-vault-sync` | Regenerate governance vault `INDEX.md` and sync metadata |
| `/resume` | Restore context from previous session via Lazarus Protocol (`/resume last` for instant warm-up) |

---

## Complete Module Reference

### Always-Active Rules (every session)

#### A) OBSERVE > PLAN > EXECUTE > VERIFY > HARDEN
Every task follows this cycle. For multi-file changes, the AI stops after PLAN and waits for your approval. Single-file trivial fixes execute directly.

#### B) Anti-Monolith / Prompt Quality Gate
If you request 3+ disconnected massive changes in one prompt, the AI rejects it and proposes micro-prompts. This prevents context rot and token waste.

#### C) Memory Flywheel
Before any task, the AI reads `USER_CRITERIA_MEMORY.md` and applies all learned preferences. Every correction gets persisted via the RCA Self-Healing cycle.

#### D) Zero-Issue Delivery Standards
No code is claimed "done" without evidence. Compile output, test results, and runtime logs are required. "It should work" is not evidence.

#### E) RCA Self-Healing (HALT > TRACE > HEAL > FIX)
When you correct the AI, it doesn't just fix the code. It: halts all execution, traces the root cause (missing context? wrong assumption?), updates governance, THEN fixes code. The fix sticks permanently.

### Sleepy Parts (load on demand)

| Part | Triggers | What It Does |
|------|----------|-------------|
| **Frontend** | React, Next.js, Vue, CSS | 21st.dev MCP integration, component architecture |
| **Autoresearch** | /autoresearch, competitive research | RSS + YouTube monitoring, signal scoring, cross-project relay |
| **Token Tools** | token audit, compress, optimize | 6-tool suite: linter, dedup, compressor, waste detector, cost estimator, autopsy |
| **ExecutionOS** | load ExecutionOS, governance | 25-rule constitution, 20 phases, 6 domain overlays |
| **Infrastructure** | daemon, dispatch, VPS, omnicapture | Cross-repo dispatch, crash recovery, runtime telemetry |
| **Agent Governance** | AGT, OWASP ASI, agent security | Trust rings (0-3), policy templates, SDK verification |
| **Zero-Crash** | TTY, sandbox, process isolation | TTY restoration, process sandboxing, advisory quality gates |
| **Video-RE** | reverse engineer, video analysis, YouTube, SOTA | Whisper transcription, frame analysis, vision scoring, competitor decomposition |
| **Knowledge Graph** | knowledge graph, graphify, obsidian, vault | `kobi_graphify.py` engine, wikilink resolution, Obsidian-native architecture discovery |
| **Governance Vault** | governance vault, leyes, mistakes, gates, vault sync | On-demand rule loading, max 5 vault pages/task, `vault_sync.py` metadata regeneration |

---

## Getting Maximum Value: Power User Guide

### 1. Let the AI plan before executing

The single most impactful rule. For any task touching 2+ files, type your request and let the AI present a plan. Review it. Say "y". This prevents 80% of wasted iterations.

**Bad:** "Refactor the auth system and add OAuth and fix the login bug"
**Good:** "Refactor the auth system to support OAuth" > review plan > approve > "Now fix the login bug"

### 2. Generate a CustomClaw for every project

First thing you do in a new project:

```
/cpp-customclaw create my-project-helper
```

Now you have a `/my-project-helper` command that knows your stack, your test commands, your framework conventions, and your guardrails. Use it as your daily driver instead of raw Claude Code — it already has the context of your project baked in.

### 3. Correct the AI explicitly

When the AI does something wrong, say exactly what's wrong. The RCA Self-Healing cycle will trace the root cause and persist the lesson to `USER_CRITERIA_MEMORY.md`. Next session, it won't repeat the mistake.

**Example:** "Don't mock the database in these tests — we need integration tests with a real DB"
**Result:** Memory stores: "Integration tests must hit real database, not mocks" > applies to ALL future sessions.

### 4. Use `!kclear` before context rots

After 15+ exchanges or when the AI starts re-reading files it already read, type `!kclear`. It checkpoints memory + pending task to disk, then you `/clear` for a fresh context. The next session picks up where you left off.

### 5. Trigger sleepy parts with keywords

Don't load heavy modules manually. Just use the right words:

- "Do a **token audit** on this project" > loads Token Tools (~300 tok)
- "**Reverse engineer** how Stripe handles webhooks" > loads Video-RE (~350 tok)
- "Check the **VPS** status" > loads Infrastructure (~400 tok)
- "Run **autoresearch** for this project" > loads Autoresearch (~350 tok)

### 6. Enable video analysis for competitive intelligence

```json
// In modules/autoresearch/config.json
"video_analysis_enabled": true
```

Now every YouTube video detected by autoresearch gets: frames extracted, transcript captured, frames scored for architectural value, and results fed into signal scoring. Competitor demo videos become 5x more useful than blog post summaries.

### 7. Use the sandbox wrapper for heavy processes

When running emulators, servers, or long processes via Claude Code:

```bash
zero-crash-sandbox dolphin-emu --batch game.iso
zero-crash-sandbox gunicorn app:app --bind 0.0.0.0:8000
```

This isolates the process from Claude Code's TTY, preventing terminal corruption and session hangs.

### 8. Route complex tasks through Omni-Plan

For high-complexity work (new architecture, CI/CD pipelines, system design), the Smart Trigger auto-activates the Omni-Plan route: Auto-Research > Architecture Design > Validation Design > Plan Presentation > Approval > Execution. You get a researched, evidence-based plan before any code is written.

---

## Top 10 Most Powerful Use Cases

### 1. CustomClaw: Your Own OpenClaw (Policy-Compliant)
**What:** Generate a custom AI daemon for any project — your own OpenClaw that works within Claude Code's policies.
**How:** `/cpp-customclaw create my-bot` in any project root. The scanner detects your stack (11 languages), structure (monorepo, MVC, API-only, full-stack), framework, test/build/lint commands, and existing governance. Outputs a fully wired `.claude/commands/my-bot.md` with stack-specific rules, guardrails, and the OBSERVE-PLAN-EXECUTE-VERIFY-HARDEN protocol.
**Why it's powerful:** OpenClaw got banned. CustomClaw generates the same kind of tailored AI assistant — but from scratch, per-project, with guardrails, and fully compatible with Claude Code's current policies. No external dependencies, no policy violations.

### 2. Zero-Issue Feature Delivery
**What:** Build a complete feature with guaranteed quality gates.
**How:** Describe the feature. The AI plans, executes, then runs compile + scaffold audit + tests before claiming "done". If any gate fails, it fixes and re-runs. `BLOCKED_DELIVERY.md` is created as evidence trail.
**Why it's powerful:** Eliminates "it works on my machine" entirely. Every delivered feature has compile + lint + test evidence.

### 3. Video-Enhanced Competitor Reverse Engineering
**What:** Deeply analyze a competitor's product by watching their demo videos.
**How:** "Reverse engineer how [competitor] handles [feature]". The AI searches YouTube for their demos, extracts frames + transcripts, scores frames for architectural diagrams/UI patterns/metrics, and produces a decomposition at macro (service topology) and micro (API contracts) scales.
**Why it's powerful:** A 10-minute demo video contains 8-12 architectural insights that a blog post misses. Frame analysis detects system diagrams, live metrics, and UI patterns automatically.

### 4. Self-Healing Across Sessions
**What:** The AI permanently learns from every correction you make.
**How:** Correct the AI once ("don't use relative imports in this project"). The RCA cycle persists this to `USER_CRITERIA_MEMORY.md`. Every future session reads this file first. The AI never repeats the same mistake.
**Why it's powerful:** Compounding intelligence. After 10 sessions, the AI knows your codebase conventions, testing preferences, deployment patterns, and naming standards without being told.

### 5. Cross-Repo Prompt Dispatch
**What:** Run Claude on any repo from anywhere.
**How:** `claude-dispatch --repo my-backend "Add rate limiting to the /api/users endpoint"`
**Why it's powerful:** One terminal, multiple projects. The dispatcher finds the repo, builds context, and runs Claude with the right working directory and project-specific governance.

### 6. Crash-Proof Development Sessions
**What:** Never lose a session to TTY corruption or hook failures again.
**How:** The Zero-Crash module: (a) restores terminal state after every Bash command, (b) warns when you're about to run risky processes without I/O isolation, (c) runs quality gates in advisory mode (warns but never blocks).
**Why it's powerful:** Before Zero-Crash, a failed `zero-issue-gate` or a misbehaving child process could kill your session. Now sessions always continue, with `BLOCKED_DELIVERY.md` as evidence instead of a dead terminal.

### 7. Autonomous Competitive Intelligence (Autoresearch)
**What:** Monitor competitors, industry trends, and YouTube channels automatically.
**How:** Configure `modules/autoresearch/config.json` with your project domains, RSS feeds, YouTube channels, and keywords. The system runs 2x/day, scores signals by authority + keyword density + recency + vision quality, and emits actionable intelligence.
**Why it's powerful:** You wake up to a digest of competitor moves, new tools, and industry shifts — scored and ranked by relevance to YOUR specific projects.

### 8. Token Cost Forensics
**What:** Understand exactly where your Claude tokens go and reduce waste.
**How:** "Run a token audit on this project". The Token Tools suite: lints CLAUDE.md for bloat, detects cross-project duplication, compresses ExecutionOS rules, identifies unused plugins, estimates session costs, and performs token autopsies on past sessions.
**Why it's powerful:** Users typically waste 20-40% of context on redundant rules, stale memories, and unused MCP tools. One audit can recover 30% of your context budget.

### 9. Audio Transcription Pipeline (Whisper Integration)
**What:** Transcribe any audio/video with local AI — no API costs, no data leaves your machine.
**How:** `python modules/autoresearch/whisper_bridge.py --audio meeting.mp3`. Uses faster-whisper (CTranslate2) for speed or falls back to openai-whisper. Outputs timestamped segments with language detection.
**Why it's powerful:** Integrate transcription into any workflow: meeting notes, podcast analysis, competitor webinar extraction. The video_analyzer chains this with frame analysis for complete video understanding.

### 10. Elixir-First Architecture Evaluation
**What:** Automatically evaluate whether your new system should use Elixir/OTP instead of TypeScript/Python.
**How:** When you propose a new system, the AI evaluates 6 criteria: needs supervisor trees? handles concurrent connections? requires hot code reloading? is a daemon/CLI? cost-per-request matters? needs distributed clustering? If >= 2 match, it recommends Elixir with concrete evidence.
**Why it's powerful:** Prevents defaulting to familiar languages when a better tool exists. The evaluation is evidence-based, not opinion-based.

---

## Module Architecture

```
claude-power-pack/
├── SKILL.md                    # Skill manifest — tiered loading triggers + Austerity Rule
├── SKILLBANK.md                # One-page catalog of every command/module/sleepy-part/tool
├── VERSION                     # 8.0.0
├── install.sh / install.ps1    # Cross-platform installers (6 phases)
├── commands/                   # 7 slash commands
│   ├── customclaw.md           # /cpp-customclaw — project-aware daemon generator
│   ├── update.md               # /cpp-update — pull latest version
│   ├── autoupdate.md           # /cpp-autoupdate — toggle auto-update check
│   ├── obsidian-setup.md       # /obsidian-setup — Knowledge Graph vault for a project
│   ├── vault-setup.md          # /cpp-vault-setup — extract CLAUDE.md into vault
│   ├── vault-sync.md           # /cpp-vault-sync — regenerate vault INDEX
│   └── resume.md               # /resume — Lazarus Protocol session restore
├── parts/
│   ├── core.md                 # Always-active rules (~800 tok) + PART Q Austerity Rule
│   ├── execution.md            # Standard+ rules (~800 tok)
│   └── sleepy/                 # On-demand parts (0 tok until triggered)
│       ├── frontend.md
│       ├── autoresearch.md
│       ├── token-tools.md
│       ├── executionos.md
│       ├── infrastructure.md
│       ├── agent-governance.md
│       ├── zero-crash.md
│       ├── video-re.md
│       ├── knowledge-graph.md
│       └── governance-vault.md
├── modules/                    # 13 pluggable subsystems
│   ├── autoresearch/           # RSS + YouTube + signal scoring + video analysis
│   ├── daemon/                 # Crash recovery + memory tuning + KobiiClaw
│   ├── dispatcher/             # Cross-repo prompt routing
│   ├── executionos-lite/       # 25-rule constitution + 20 phases + 6 overlays
│   ├── governance-overlay/     # Pre-task, during-task, pre-output gates + Council of 5
│   │   ├── council.md          # 5-advisor inline structured self-review (A+/A/B/REJECT)
│   │   ├── mistakes-registry.md# 51-entry error catalog
│   │   └── mistake-frequency.json # Recurrence counter fed by post-output → pre-task loop
│   ├── infrastructure/         # VPS query tools
│   ├── memory-engine/          # RCA self-healing persistence
│   ├── omnicapture/            # Runtime telemetry (VPS backend + adapters)
│   ├── agent-governance/       # OWASP ASI, trust rings, policy templates
│   ├── agent-lightning/        # Trace-based performance optimization
│   ├── sleepless_qa/           # Closed-loop empirical verification (DNA-400 evidence)
│   ├── token-optimizer/        # 6 token analysis tools
│   └── zero-crash/             # TTY isolation, sandbox, advisory gates
│       ├── hooks/              # TTY-restore, process-sandbox, zero-issue-gate, golden-pattern-inject
│       ├── sandbox-wrapper.sh  # Unix process isolation
│       ├── sandbox-wrapper.ps1 # Windows process isolation
│       └── vps/                # Anonymous crash telemetry receiver
├── tools/                      # CLI utilities
│   ├── baseline_ledger.py      # Multi-axis ecosystem rigor ledger (k_qa / k_router / engineering_baseline / highest_dna)
│   ├── mistake_frequency.py    # Mistakes→Curriculum recurrence counter
│   ├── audit_cache.py          # SHA-256 integrity map + cached summaries (Token Shield)
│   ├── council_verdict.py      # Council verdict recorder
│   ├── kobi_graphify.py        # Knowledge Graph engine for Obsidian vaults
│   ├── vault_sync.py           # Governance vault INDEX regenerator
│   ├── vault_extractor.py      # CLAUDE.md → topic pages extractor
│   ├── memory_manager.py       # Hot/cold context splitter
│   ├── obsidian_enrich.py      # Vault frontmatter + wikilink enrichment
│   ├── chatgpt_distiller.py    # Transcript distiller
│   └── electron_priority_manager.ps1 # OS priority management for Electron
├── _audit_cache/               # Token Shield artifacts (source_map.json generated, semantic_tags.json committed)
└── knowledge/                  # AKOS briefs, playbooks, integration plans, iteration prompts, doctrine-laws registry
```

---

## Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `ANTHROPIC_API_KEY` | Claude API for vision scoring | For video-RE only |
| `OMNICAPTURE_API_KEY` | Runtime telemetry to VPS | Optional |
| `ZERO_CRASH_ENFORCE` | Enable hard-blocking quality gates | Optional (default: false) |
| `ZERO_CRASH_API_KEY` | Anonymous crash telemetry | Optional |

---

## Key Principles

1. **Tiered loading** — Never load everything. Match task complexity to tier.
2. **Skills > MCP tools** — MCP consumes 13-14% of context. Skills load on-demand.
3. **Evidence over claims** — Compile output, test results, and runtime logs. "Should work" is not evidence.
4. **Corrections compound** — Every correction persists via RCA Self-Healing. The system gets permanently smarter.
5. **Advisory over blocking** — Quality gates warn and create evidence, never kill sessions.
6. **Video > text for RE** — A 10-minute demo video contains 8-12 architectural insights a blog post misses.
7. **Cross-platform always** — Every script works on Windows + Unix. No platform-specific assumptions.
8. **Policy-compliant by design** — CustomClaw generates project-specific daemons that work within Claude Code's policies, not around them.

---

## License

MIT
