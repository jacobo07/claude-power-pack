# Claude Power Pack v7.1

Universal AI execution framework for Claude Code. Zero-issue delivery, self-healing governance, tiered token loading, video-enhanced reverse engineering.

**66 files | 12 modules | 8 sleepy parts | 4 depth tiers | Cross-platform (Windows + Unix)**

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

---

## Getting Maximum Value: Power User Guide

### 1. Let the AI plan before executing

The single most impactful rule. For any task touching 2+ files, type your request and let the AI present a plan. Review it. Say "y". This prevents 80% of wasted iterations.

**Bad:** "Refactor the auth system and add OAuth and fix the login bug"
**Good:** "Refactor the auth system to support OAuth" → review plan → approve → "Now fix the login bug"

### 2. Correct the AI explicitly

When the AI does something wrong, say exactly what's wrong. The RCA Self-Healing cycle will trace the root cause and persist the lesson to `USER_CRITERIA_MEMORY.md`. Next session, it won't repeat the mistake.

**Example:** "Don't mock the database in these tests — we need integration tests with a real DB"
**Result:** Memory stores: "Integration tests must hit real database, not mocks" → applies to ALL future sessions.

### 3. Use `!kclear` before context rots

After 15+ exchanges or when the AI starts re-reading files it already read, type `!kclear`. It checkpoints memory + pending task to disk, then you `/clear` for a fresh context. The next session picks up where you left off.

### 4. Trigger sleepy parts with keywords

Don't load heavy modules manually. Just use the right words:

- "Do a **token audit** on this project" → loads Token Tools (~300 tok)
- "**Reverse engineer** how Stripe handles webhooks" → loads Video-RE (~350 tok)
- "Check the **VPS** status" → loads Infrastructure (~400 tok)
- "Run **autoresearch** for this project" → loads Autoresearch (~350 tok)

### 5. Enable video analysis for competitive intelligence

```json
// In modules/autoresearch/config.json
"video_analysis_enabled": true
```

Now every YouTube video detected by autoresearch gets: frames extracted, transcript captured, frames scored for architectural value, and results fed into signal scoring. Competitor demo videos become 5x more useful than blog post summaries.

### 6. Use the sandbox wrapper for heavy processes

When running emulators, servers, or long processes via Claude Code:

```bash
zero-crash-sandbox dolphin-emu --batch game.iso
zero-crash-sandbox gunicorn app:app --bind 0.0.0.0:8000
```

This isolates the process from Claude Code's TTY, preventing terminal corruption and session hangs.

### 7. Route complex tasks through Omni-Plan

For high-complexity work (new architecture, CI/CD pipelines, system design), the Smart Trigger auto-activates the Omni-Plan route: Auto-Research → Architecture Design → Validation Design → Plan Presentation → Approval → Execution. You get a researched, evidence-based plan before any code is written.

---

## Top 10 Most Powerful Use Cases

### 1. Zero-Issue Feature Delivery
**What:** Build a complete feature with guaranteed quality gates.
**How:** Describe the feature. The AI plans, executes, then runs compile + scaffold audit + tests before claiming "done". If any gate fails, it fixes and re-runs. `BLOCKED_DELIVERY.md` is created as evidence trail.
**Why it's powerful:** Eliminates "it works on my machine" entirely. Every delivered feature has compile + lint + test evidence.

### 2. Video-Enhanced Competitor Reverse Engineering
**What:** Deeply analyze a competitor's product by watching their demo videos.
**How:** "Reverse engineer how [competitor] handles [feature]". The AI searches YouTube for their demos, extracts frames + transcripts, scores frames for architectural diagrams/UI patterns/metrics, and produces a decomposition at macro (service topology) and micro (API contracts) scales.
**Why it's powerful:** A 10-minute demo video contains 8-12 architectural insights that a blog post misses. Frame analysis detects system diagrams, live metrics, and UI patterns automatically.

### 3. Self-Healing Across Sessions
**What:** The AI permanently learns from every correction you make.
**How:** Correct the AI once ("don't use relative imports in this project"). The RCA cycle persists this to `USER_CRITERIA_MEMORY.md`. Every future session reads this file first. The AI never repeats the same mistake.
**Why it's powerful:** Compounding intelligence. After 10 sessions, the AI knows your codebase conventions, testing preferences, deployment patterns, and naming standards without being told.

### 4. Cross-Repo Prompt Dispatch
**What:** Run Claude on any repo from anywhere.
**How:** `claude-dispatch --repo my-backend "Add rate limiting to the /api/users endpoint"`
**Why it's powerful:** One terminal, multiple projects. The dispatcher finds the repo, builds context, and runs Claude with the right working directory and project-specific governance.

### 5. Crash-Proof Development Sessions
**What:** Never lose a session to TTY corruption or hook failures again.
**How:** The Zero-Crash module: (a) restores terminal state after every Bash command, (b) warns when you're about to run risky processes without I/O isolation, (c) runs quality gates in advisory mode (warns but never blocks).
**Why it's powerful:** Before Zero-Crash, a failed `zero-issue-gate` or a misbehaving child process could kill your session. Now sessions always continue, with `BLOCKED_DELIVERY.md` as evidence instead of a dead terminal.

### 6. Autonomous Competitive Intelligence (Autoresearch)
**What:** Monitor competitors, industry trends, and YouTube channels automatically.
**How:** Configure `modules/autoresearch/config.json` with your project domains, RSS feeds, YouTube channels, and keywords. The system runs 2x/day, scores signals by authority + keyword density + recency + vision quality, and emits actionable intelligence.
**Why it's powerful:** You wake up to a digest of competitor moves, new tools, and industry shifts — scored and ranked by relevance to YOUR specific projects.

### 7. Token Cost Forensics
**What:** Understand exactly where your Claude tokens go and reduce waste.
**How:** "Run a token audit on this project". The Token Tools suite: lints CLAUDE.md for bloat, detects cross-project duplication, compresses ExecutionOS rules, identifies unused plugins, estimates session costs, and performs token autopsies on past sessions.
**Why it's powerful:** Users typically waste 20-40% of context on redundant rules, stale memories, and unused MCP tools. One audit can recover 30% of your context budget.

### 8. Production-Risk Forensic Analysis
**What:** Investigate production issues with maximum rigor.
**How:** The FORENSIC tier loads ALL parts including: full ExecutionOS constitution (20 phases), all domain overlays, complete mistakes registry (30+ documented failure patterns), and the zero-issue baseline cascade.
**Why it's powerful:** When production is down, you need the AI operating at maximum awareness of failure patterns, not guessing. The mistakes registry alone prevents re-introducing 30+ known error classes.

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
├── SKILL.md                    # Skill manifest — tiered loading triggers
├── VERSION                     # 7.1.0
├── install.sh / install.ps1    # Cross-platform installers (6 phases)
├── parts/
│   ├── core.md                 # Always-active rules (~800 tok)
│   ├── execution.md            # Standard+ rules (~800 tok)
│   └── sleepy/                 # On-demand parts (0 tok until triggered)
│       ├── frontend.md
│       ├─��� autoresearch.md
���       ├── token-tools.md
│       ├── executionos.md
│       ���── infrastructure.md
│       ├── agent-governance.md
│       ├── zero-crash.md
│       └── video-re.md
├── modules/
│   ├── autoresearch/           # RSS + YouTube + signal scoring + video analysis
│   ├── daemon/                 # Crash recovery + memory tuning
│   ├── dispatcher/             # Cross-repo prompt routing
│   ├── executionos-lite/       # 25-rule constitution + 20 phases + 6 overlays
│   ├── governance-overlay/     # Pre-task, during-task, pre-output gates
│   ├── infrastructure/         # VPS query tools
│   ├── memory-engine/          # RCA self-healing persistence
│   ├── omnicapture/            # Runtime telemetry (VPS backend + adapters)
│   ├── agent-governance/       # OWASP ASI, trust rings, policy templates
│   ├── agent-lightning/        # Trace-based performance optimization
│   ├── token-optimizer/        # 6 token analysis tools
│   └── zero-crash/             # TTY isolation, sandbox, advisory gates
│       ├── hooks/              # 3 hooks (gate, tty-restore, process-sandbox)
│       ├── sandbox-wrapper.sh  # Unix process isolation
│       ├── sandbox-wrapper.ps1 # Windows process isolation
│       └── vps/                # Anonymous crash telemetry receiver
└── knowledge/                  # AKOS briefs, playbooks, integration plans
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

---

## License

MIT
