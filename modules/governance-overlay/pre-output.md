# Governance Overlay — Pre-Output Gate

> Loaded for STANDARD, DEEP, and FORENSIC tiers. ~150 tokens. Final gate before returning code.
> Inherits workspace context from PART A0 Assimilation Scan. All file references use `./` relative paths.

## Full 15-Mistake Scan

Before claiming ANY work is complete, verify each item:

| # | Mistake | Check |
|---|---------|-------|
| 1 | Building Without Wiring | Every new file has ≥1 import somewhere |
| 2 | Detail Without Integration | New utilities are called in the same session |
| 3 | Data Without Save Triggers | Save() exists in every completion path |
| 4 | Events Without Sources | Every listener has a corresponding emitter |
| 5 | Config Without Consumers | Every config getter has a reader |
| 6 | File Exists ≠ Works | Consumer + observable output verified |
| 7 | Upgrade Without Replacement | Wired into existing call chain, old refs updated |
| 8 | Constants Drift | Ratios verified after geometry/layout changes |
| 9 | Deprecated Patterns | Used existing utilities, didn't rebuild |
| 10 | Report Gaps Instead of Fixing | Fixed issues in the same pass, didn't just note them |
| 11 | Remote != Localhost | No hardcoded localhost for remote targets |
| 12 | Approximating Instead of Implementing | Solved the actual hard problem |
| 13 | Assumptions Without Verification | Read files before editing, verified existence |
| 14 | Analyzing Callee Without Caller | Traced full call chain upward |
| 15 | Static Display of Dynamic Data | Counters track real state, not initial totals |
| 36 | Hardcoded Path Injection | Zero absolute paths in global skills/shared code (E11) |
| 27 | Agent Without Kill Switch | Every agent loop has max_iterations + breaker + cost_limit |
| 28 | Unbounded Tool Access | allowed_tools explicitly defined, no open shell access |
| 29 | Trust Without Verification | Agent-to-agent calls authenticated |
| 30 | Privilege Escalation via Tool Chain | No transitive escalation paths |
| 31 | SLO-Blind Deployment | SLOs defined before agent deployment |
| 32 | Unsigned Plugin | Agent plugin signatures verified |
| 33 | Stateful Without Saga | Multi-step workflows have rollback |
| 37 | Silent Quality Degradation | Every fallback logs WARNING + is observable |
| 38 | Producer-Consumer Gap | Every new data output has a consumer wired |
| 39 | Synchronous Default Trap | No sync I/O in async/event-loop contexts |
| 47 | Success Hallucination (Ley 25) | Runtime-behavior features require Sleepless QA PASS ticket; compile ≠ verdict |
| 48 | Zero-Shot Execution (Ley 26) | No >1-file edit without approved plan in `.planning/` or `~/.claude/plans/` |
| 49 | Untwinned Feature (Ley 27) | Every new runtime feature ships with a `.yml` action script twin in the same commit |
| 51 | Razonamiento Supuesto (Ley DNA-400) | Complex logic cites a session-local execution trace (sleepless_qa verdict OR captured stdout); pure reasoning ≠ evidence |

## DNA-400 Gate (Ley de Supremacía Empírica — MANDATORY for complex logic)

Before delivering any non-trivial logic change (>20 LOC, cross-module, state machine, concurrency, protocol handler), confirm ONE of:

1. **Sleepless QA verdict** — `~/.claude/sleepless-qa/runs/<run-id>/verdict.json` exists with `status=PASS` and was produced in this session. Cite the run-id.
2. **Synthetic test execution** — a standalone script was run in this session against the changed logic; stdout and exit code were captured and inspected.
3. **Honest deferral** — neither is possible (no runtime, destructive target, missing credentials). Phrase the delivery as *"code reasoned statically; empirical verification deferred to [specific owner step]"*. Never silently collapse reasoning into a completion claim.

Model reasoning about correctness ("this should work because X") is NOT evidence. See Mistake #51.

## Evidence Check (Ley 25 — Empirical Evidence Law)

Before returning ANY output claiming "done", "fixed", "ready", or "complete" on a runtime-behavior change (UI, gameplay, API response, daemon output, command handler):

1. Did the Sleepless QA pipeline (`modules/sleepless_qa/`) run against this change? → If NO and feature touches runtime, **BLOCK output**; either run it or explicitly label the work as "code written, empirical verification pending VPS".
2. Did it emit a PASS ticket at `~/.claude/sleepless-qa/runs/<run-id>/verdict.json`? → If status ≠ PASS, re-dispatch healing circuit (retry budget 3) or escalate.
3. Is the evidence artifact (screenshot hash, log excerpt, HTTP signature) archived? → If NO, the ticket is incomplete.
4. If the pipeline itself cannot run from this session (no VPS shell, no API key, no network), the agent MUST NOT collapse "code written" and "behavior verified" into a single claim. The honest phrasing is: *"code scaffolded and statically valid; empirical verification pending Owner execution on VPS."*

### Priority Ladder (Ley 24 — Veto de la Realidad)

Reject any output that works on a lower priority while a higher-priority issue is open:
1. **Estabilidad** (crashes, segfaults, uncaught exceptions, ISI on Wii)
2. **Funcionalidad** (input handling, state transitions, API contracts)
3. **Estética** (rendering, visuals, GX)
4. **Pulido** (particles, audio, animation polish)

L4 work while an L1 issue is open → auto-reject with "Priority Violation: fix L1 first."

## Quality Gates (Run ALL That Apply)

Execute the applicable commands and verify output:

```
TypeScript:  npx tsc --noEmit          → 0 errors
Python:      mypy --strict / ruff check → 0 errors
Lint:        project linter             → 0 errors
Tests:       npm test / pytest          → all pass
Build:       project build command      → passes
Schema:      prisma validate / etc      → valid
Agent:       agt audit owasp-asi <dir>  → 0 CRITICAL (if agent system)
Agent Policy: agt policy validate <file> → valid (if agent system)
```

**Evidence required.** Run the command. Read the output. THEN claim the result. "Should pass" is not evidence.

## End-to-End Functional Verification (Gate 5 — MANDATORY)

After compile/build/test gates pass, verify the system WORKS:

| Project Type | Verification |
|-------------|-------------|
| Web app | Start dev server → hit main route → HTTP 200 → hit API endpoints → DB data returns |
| Multi-stack | EACH stack passes Gates 1-4 independently → integrated system verified end-to-end |
| Library | Import → call primary function → confirm expected output |
| CLI | Run `--help` → run primary command → confirm behavior |
| Backend | Boot → health endpoint 200 → primary endpoint returns data |

**Cannot verify end-to-end?** Document what was verified and what wasn't. Never use kill-switch words for unverified functionality.

### Completeness Checklist (ALL must be true before claiming "done")
- [ ] Every route/endpoint responds (not 404/500)
- [ ] Every UI screen renders without console errors
- [ ] Every form submits and result persists
- [ ] Every integration connects and returns data
- [ ] No TODO/placeholder in user-visible UI
- [ ] Mobile responsive at 375px (if web)

## Language Decision Verification

If this task involved writing new backend/infrastructure code:

| Check | Verify |
|-------|--------|
| Fragility score computed? | Score was calculated in pre-task gate |
| If score >= 2, LDR exists? | Language Decision Record was created or Elixir was chosen |
| If non-Elixir chosen, OTP equivalents listed? | Checklist of manually-needed patterns exists |
| If non-Elixir chosen, equivalents implemented? | Supervision, circuit breakers, shutdown handlers present in code |

If OTP equivalents were listed but NOT implemented, flag as incomplete.

### Language Selection Enforcement (BLOCKING at >=4)

Before delivering any new backend service, infrastructure daemon, or CLI tool:

1. Was the Language Fragility Gate (pre-task Section 5) evaluated? If NO → **HALT. Run the gate first.**
2. What was the fragility score? If >=4 and language is NOT Elixir:
   a. Does an LDR exist with explicit user override? If NO → **HALT. Create LDR.**
   b. Are ALL OTP equivalents implemented? Verify each concretely:
      - Supervisor trees → equivalent crash recovery mechanism (restart logic, health checks)
      - Circuit breakers → timeout + retry + exponential backoff pattern
      - Graceful shutdown → SIGTERM/SIGINT handlers + cleanup + drain connections
      - Backpressure → rate limiting, queue depth limits, or flow control
      - State isolation → no shared mutable state across requests (per-request context only)
   c. If any equivalent is missing → **HALT with specific gap listed.**
3. If score 2-3: LDR required, but delivery not blocked. Advisory only.
4. If score 0-1: no language gate.

### Extended Mistake Scan (Mistakes #16-26 + #37-39 — STANDARD+ tier)

In addition to Mistakes #1-15, verify at STANDARD+ tier:
- **Mistake #16 (Scaffold Illusion):** Compiles != works. Commented-out wiring = not delivered.
- **Mistake #20 (Shell Escaping Corruption):** Remote deploy commands with unescaped variables.
- **Mistake #25 (Fragile Language for Critical Systems):** Defaulting to familiar language without evaluating fragility criteria. If fragility score >=4 and non-Elixir was chosen without LDR, this is a delivery-blocking mistake.
- **Mistake #26 (Missing LDR):** Building critical infrastructure without Language Decision Record. Pre-task fragility gate MUST run on every new project.
- **Mistake #37 (Silent Quality Degradation):** Every fallback path must log WARNING + be observable. If fallback is >10x slower or loses data → must abort, not silently degrade.
- **Mistake #38 (Producer-Consumer Gap):** For every new data output (return value, file, event, message) — verify a consumer exists. Zero callers = not done.
- **Mistake #39 (Synchronous Default Trap):** If the runtime has an event loop, main thread, or tick system — verify ALL I/O and heavy computation runs off-thread. No sync I/O in async contexts.

### Section 13: Council of 5 (STANDARD+ MANDATORY)

Before emitting ANY output at STANDARD+ tier, produce an inline Council block per `council.md` and stamp a `[COUNCIL_VERDICT: A+|A|B|REJECT]` banner.

- **A+ / A:** emit the output.
- **B / REJECT:** BLOCK. Do not emit. Route to Rejection Recovery (see `post-output.md`).

The 5 advisors (Contrarian, First Principles, Expansionist, Outsider, Executor) each read the top-3 Howard's Loop antipatterns from `~/.claude/knowledge_vault/governance/visual-antipatterns.md` before rendering their verdict. For KobiiCraft/KobiiSports, also inject from `gex44_antipatterns/`. Full doctrine and template: `council.md`.

Self-grading is protocol — there is no external auditor in the critical path. Dishonest grading will surface on the next session as Mistake #17.

**OVO breadcrumb (no double-render):** If `./_audit_cache/.council_rendered_*.json` exists with mtime <60s, `/ovo-audit` already rendered the Council this turn. Skip the Section 13 render and reuse the verdict that OVO stamped — do NOT emit a second Council block. Breadcrumbs are written by `tools/oracle_delta.py` during Phase C of the OVO protocol.

### Section 14: Adversarial + Security Auto-Gates (STANDARD+ MANDATORY — MC-OVO-21)

After Council verdict A/A+ but before emitting, inspect the delta's surface and fire the relevant gate(s). Pure-doc deltas (markdown-only, no code) are exempt.

**Adversarial-longevity auto-invocation** — fire when the delta touches ANY of:
- user input handlers (command handlers, form submits, packet parsers, CLI arg parsing)
- save writes or shared mutable state (DB writes, file I/O, cache mutations)
- authentication, session, or authorization logic
- external API calls with user-supplied params
- loops processing untrusted input

**Required output:** cite-or-die emission per `~/.claude/skills/claude-power-pack/SKILL.md` § adversarial-longevity — exploit tree (≥5 archetypes), 10x-load proof, drift catalog, budget declarations, all in the same emission. Any gate incomplete → **verdict drops to B** and routes to Rejection Recovery.

**Security-review auto-invocation** — fire when the delta touches ANY of:
- auth / authz / session management
- cryptographic operations (hashing, signing, encryption, token generation)
- shell command construction (`subprocess`, `exec`, `eval`, `Runtime.exec`, backticks)
- file path handling (traversal risk — user-supplied paths, `..`, symlink follow)
- deserialization (JSON, YAML, pickle, XML, untrusted network payloads)
- secrets handling (env vars, config files, key material)

**Required output:** inline 5-point checklist citation: (1) auth present and correct, (2) input validated at boundary, (3) no shell/SQL injection vector, (4) no path traversal, (5) no unsafe deserialization. Cite the specific defenses by file:line. Anything unchecked → verdict B.

**Provenance stamps** — append to the Council block so downstream gates can prove the auto-invocations ran:
- `[ADVERSARIAL: skipped|cited|deferred]`  where:
  - `skipped` = delta surface doesn't trigger (pure docs / internal refactor with no user input path)
  - `cited` = cite-or-die emission present in this turn
  - `deferred` = surface triggers but Owner explicitly accepted deferral to follow-up commit
- `[SECURITY: skipped|cited|deferred]` same semantics

**Enforcement:** verdicts.jsonl records will include `adversarial_status` and `security_status` fields derived from these stamps. Future OVO cold-start audits on the same repo will flag missing stamps as Mistake #38 variants (consumer gap — no auto-gate stamp on a surface that required it).
