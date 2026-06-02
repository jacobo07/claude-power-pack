# Apex Completeness Doctrine — BL-0068

**Sealed:** 2026-05-16 · mirror of the `~/.claude/CLAUDE.md` Sovereign
Baseline section (non-git live file; this is the version-controlled
reference).

## The mandate

Every NEW multi-file feature stream MUST start pre-wired with all
three pillars. A stream missing any pillar is **incomplete by
definition** — not a deferred follow-up, not a v2 item.

1. **Isolated FTS5 sidecar** — any searchable surface gets its own
   FTS5 content table + its own insert/delete/update triggers. It
   never shares the conversation `turns_fts` rowid space and never
   issues a global `('rebuild')` against a shared index. (KARIMO
   `design_tools_fts` is the reference implementation.)
2. **Keyword-sentinel gating** — wherever a raw-input fast path
   exists, a deterministic UserPromptSubmit-style pre-extractor runs
   first, fail-open, no model call, emitting structured constraints.
   (KARIMO `prd-keyword-sentinel.js` + `prd_parser.py` is the
   reference.)
3. **Atomic design-token isolation** — any UI surface is fed by a
   generator that emits self-contained design tokens, budgeted per
   the Jobs/Woz hybrid (signature visuals → Jobs precedence;
   utilities → Woz absolute veto; measured token threshold). (KARIMO
   `atomic_branding.py` is the reference.)

## Enforcement model

Doctrine-enforced (human + agent review at plan time), deliberately
NOT a heavyweight runtime hook — adding another synchronous gate to
the 11-deep PreToolUse chain would tax latency for marginal benefit.
The plan-time auditor (`oneshot-architect-auditor`) is the natural
checkpoint: a stream proposal lacking a pillar is a gap it should
flag.

## Provenance

Materialized across BL-0068 commits: PRD parser + engine, FTS5 design
index + `/cpp-design`, atomic branding, and the config-harness
closure (sentinel registration + advisory `/ultra` pre-pass). All
gates empirically green; the only honest limit is cold-load (a newly
registered hook fires next `/restart`, never claimed as proven
in-pipeline the turn it lands).

## Hook Startup Authorization Gate (sealed 2026-05-17, BL Intent-Lock/L3)

For ANY feature that wires a startup hook (SessionStart, SessionEnd, Stop, PreToolUse, PostToolUse, UserPromptSubmit) to spawn a process or auto-fire autonomous work:

1. An EXACT-PATH `permissions.allow` rule for the target hook file (e.g. `Edit(file:~/.claude/hooks/<name>.js)`) MUST exist in `settings.json` BEFORE execution begins. A broad glob (`hooks/**`) does NOT clear the auto-mode self-modification classifier — it is a separate gate above `permissions`, and `AskUserQuestion` soft-consent does not clear it either.
2. The capability is built INERT and harness-verified (real-input, no mocks) before any activation edit is attempted.
3. Post-wire gate: `node --check <hook>` exit 0 + the empirical harness still green + (live-fire confirmed after the Owner `/restart`s, since hooks cold-load at session start, BL-0067).

This gate prevents the mid-session triple-block: pre-authorize, then wire. Reference cycle: Intent-Lock/L3 — `intent_lock.js` + `learning-sentinel.js` `maybeSpawnL3` + `tools/test_l3_intent.js`.

## L3 / Stop-hook S++ Gate (sealed 2026-05-19)

1. Hook en registry live post-restart (no solo en disco).
2. SessionEnd real con >5 learnings → `~/.claude/cache/compound-proposals/` archivo real (bare timestamp, NOT `verify-`-prefixed).
3. Timestamp del archivo = post-restart (no caché previo).

Este gate aplica a cualquier hook Stop/SessionEnd que genere outputs externos. 12/12 en harness aislado es prerequisito de S+, NO de S++ — S++ exige el archivo real producido por el hook DESPLEGADO vía un evento genuino, no un `--dry-run` ni una reimplementación de harness. El archivo es el único done-gate: existe o no existe.

## Apex Onboarding Standard (sealed 2026-05-19)

The pre-existing Apex Completeness mandate (BL-0068) governs what a feature ships INSIDE the Power Pack. The Apex Onboarding Standard governs what makes that feature **reachable to a new operator on a clean host**. Both are mandatory, neither is sufficient alone.

**Mandate.** Every NEW component that lands in `tools/`, `hooks/`, `modules/`, `commands/`, `agents/`, `vault/standards/`, or `vendor/` MUST include all four:

1. **An umbrella row** in `tools/verify_full_install.py` or `tools/verify_spp.py` (whichever umbrella the component belongs to) that calls the component's own verifier and reports the result. No row, no inclusion.
2. **A step in `install-global.ps1` + `install-global.sh`** that copies / registers the component on a fresh `~/.claude/` (or whatever the component's surface area requires), with the idempotent diff-copy semantic and exit non-zero on preflight failure.
3. **A section in `docs/INSTALL.md` and / or `docs/INSTALL-GLOBAL.md`** that walks the new operator through the component in plain language, with no assumed prior PP knowledge.
4. **A clean-machine verification** (Path A real `git clone` into a temp dir + HOME-redirected install, OR Path B documented dry-run + idempotent re-run) that exits 0 on the new component in under 5 minutes wall-clock.

**Done-Gate.** `python tools/verify_full_install.py` exit 0 on the just-installed clean machine. The same gate the Owner runs on the reference host MUST be reachable by a stranger who only knows `git clone <url> && cd claude-power-pack && ./install-global.{ps1,sh} && python tools/verify_full_install.py`.

**Status.** Effective immediately for any new feature post-2026-05-19. Pre-existing features are grandfathered — they do NOT need retroactive umbrella rows. New features that omit any of the four pillars are non-conformant and CANNOT pass OVO at verdict >= A.

**Cross-link.** The Programmatic Budget Standard (`vault/standards/programmatic-budget-standard.md`, sealed 2026-05-19) is the first feature audited under this combined Apex Completeness + Onboarding gate. Its umbrella row, install-global handling (Owner-action for ~/.claude/hooks/ writes), `docs/INSTALL.md` section, and clean-machine path are the reference implementation of the standard.

## Spec-Driven Gate cross-link (sealed 2026-05-20)

The Spec-Driven Gate (PASO -1) governs feature *intent* upstream of the three pillars above. It is sealed in the global apex standard, not duplicated here, to preserve single-source-of-truth.

> See: `~/.claude/knowledge_vault/core/apex-completion-standard.md` § **Spec-Driven Gate (sealed 2026-05-20, PASO -1)**.

**Order of gates for any new feature:**

1. **PASO -1** — Spec-Driven Gate (constitution + spec + plan + tasks + analyze; `vault/templates/speckit/*.template` + `commands/speckit-*.md`).
2. **PASO 0** — Apex Onboarding Standard (this file, sealed 2026-05-19).
3. **PASO 1+** — Apex Completeness three pillars (this file, BL-0068 sealed 2026-05-16).

A feature missing PASO -1 is INCOMPLETE at the planning stage and CANNOT enter the onboarding/completeness pipeline. A feature passing PASO -1 but missing PASO 0 or the three pillars is non-conformant per the existing rules in this file.

## Zero-Command Standard cross-link (sealed 2026-05-21)

The Zero-Command Standard governs feature *activation* — if a PP capability improves results, saves tokens, or removes a recurring manual step, it MUST activate without an Owner-typed slash command. Sealed in the global apex standard, not duplicated here, to preserve single-source-of-truth.

> See: `~/.claude/knowledge_vault/core/apex-completion-standard.md` § **Zero-Command Standard (sealed 2026-05-21)**.

**Reference implementation (this commit chain on `feat/rtk-compressor-fusion`):**

- Component A — `hooks/zero-command-bootstrap.js` (SessionStart). Stubs `.specify/memory/constitution.md` on first encounter of a real project (`.git` + manifest + no `.specify/`).
- Component B.2 — `tools/jit_skill_loader.py::_detect_new_feature_intent_and_flag`. Drops `.pp-pending-spec.json` when prompt matches new-feature regex.
- Component B.3 — `hooks/pending-keystrokes-daemon.ps1`. Generalized SendKeys dispatcher polling `~/.claude/hooks/pending-keystrokes/*.flag`. Cursor-focused dispatch only, TTL + .disabled kill-switch, BL-0003 intact.
- Component C — `hooks/background-verifier.js` + `tools/background_verifier_run.py`. Stop-time mirror parity + OVO staleness + spec coherence; handoff-only, never auto-fixes.
- Component D — `hooks/first-time-project.js` + `tools/first_time_project_init.py`. SessionStart prereq probe (4 quick checks).
- Harness — `tools/test_zero_command.py` (G1-G8). Exit 0 on this host with 7 PASS + 1 SKIP (G1 awaiting sibling E.1 audit artifact).

**Order of gates extended:**

0. **PASO -2 (NEW)** — Zero-Command Standard. Every new capability has an auto-activation path before any of the below applies.
1. PASO -1 — Spec-Driven Gate.
2. PASO 0 — Apex Onboarding Standard.
3. PASO 1+ — Apex Completeness three pillars + Programmatic Budget Gate.

Pre-existing features (`/ovo-audit`, `/cpp-distill`, `/speckit-*` slash commands themselves) are grandfathered. Post-2026-05-21 features that ship slash-only must declare WHY a hook can't trigger them, in the spec's Constraints section.

## SCS C21 — Performance-by-default in hot-path hooks (sealed 2026-05-31, BL-JIT-001)

Every Python script bound to a hot Claude Code event (`UserPromptSubmit`, `PreToolUse`, `PostToolUse`) MUST meet the three perf criteria below, OR document the gap with an empirical benchmark.

1. **Always-fire decorators carry a cheap pre-check.** A decorator that imports a subpackage and dispatches work on every call MUST first check whether ANY downstream evaluator could possibly fire. The pre-check budget is one cheap filesystem scan (mtime stat on a small dir) or one env-var read — no module imports, no JSON parse beyond a handful of bytes.
2. **Filesystem walks have a disk-persisted cache.** Any walk that scans more than ~20 dirents per call MUST persist its result to `STATE_DIR/<scope>-<sha1(cwd)>.json` with a TTL appropriate to how often the walk's answer can change (1 h for "does cwd contain *.graphql"; 5 min for "does .specify/specs/ have an active spec"; etc.).
3. **First-prompt cold start is masked by a SessionStart pre-warmer.** When the script's end-to-end subprocess time is >300 ms cold, a SessionStart hook (detached, fire-and-forget, NEVER blocks session start) MUST spawn the script with a `PP_WARM_RUN=1` short-circuit that primes the OS page cache + walk + spec disk caches + .pyc bytecode. The warm path MUST NOT call `run()` directly (that would mark side-effects like "already injected this session" before the user has typed).

**Benchmark obligation:** every PR that adds or modifies a hot-path Python hook MUST land `tools/bench_<name>.py` capturing pre/post end-to-end timings to `vault/benchmarks/<name>_pre_fix.json` + `<name>_post_fix.json`. The PR description quotes the e2e gain. ≥20 % is the soft threshold; <20 % is allowed when the script was already perf-clean (pre baseline already <300 ms e2e) and the benchmark documents it.

**Reference implementation:**

- `tools/jit_skill_loader.py` (the hook under control)
- `tools/bench_jit_loader.py` (microbench)
- `hooks/jit_warm.js` (SessionStart pre-warmer)
- `tools/test_jit_performance.py` (11 V-JIT-* gates)
- `vault/benchmarks/jit_loader_lazy_plan.md` (honest analysis: imports were not the bottleneck)
- `vault/knowledge_base/ukdl-universal.md` § UKDL TRAP T-JIT-001

## SCS C22 -- Restart-and-Input-Latency-by-default (sealed 2026-05-31 evening, BL-RESTART-001 + BL-LAG-001)

Every PP slash command that exits the current session AND every SessionStart hook that PP installs MUST meet the three criteria below, OR document the gap with empirical timing.

1. **/restart NEVER terminates the pane.** It MUST drop the prior session via the platform's own exit pipeline (on Windows: `WriteConsoleInputW` of `/exit\r` into the shared CONIN$ console buffer). `Stop-Process -Force` is a fallback only, gated behind a verified failure of the graceful path (e.g., CONIN$ open returned INVALID_HANDLE_VALUE OR the write returned 0 events). Every /restart write a UNIVERSAL marker (`~/.claude/state/restart_pending.json` with cwd + sid + branch + timestamp) so a SessionStart hook can offer a continuation hint when the platform-specific resume wrapper (kclaude.bat on Windows) is not the parent.
2. **PP-owned SessionStart hooks are fire-and-forget by default.** A hook that does watchdog / cleanup / warmup work MUST spawn the heavy work detached and exit < 200 ms median, OR be explicitly justified as needing synchronous emission of additionalContext. PP ships `hooks/async_wrapper.js` to retrofit Owner-side hooks that the classifier-blocked PP cannot rewrite directly.
   - **Windows hard rule (sealed 2026-06-01, T-ASYNC-WRAPPER-001):** the wrapper MUST use `stdio: 'ignore'` for ALL THREE streams. `stdio: ['pipe', 'ignore', 'ignore']` + `child.unref()` + `process.exit(0)` is an antipattern -- the stdin pipe keeps the Node event loop open until the wrapped child reads it, defeating the detachment. Wrapped hooks lose the SessionStart stdin payload by design; if a hook genuinely needs it, that hook stays synchronous (not wrappable).
   - Verification: every PP wrapper must pass `time (echo '{}' | node hook.js) < 300 ms` directly AND via `python -c "subprocess.run('node hook.js', shell=True, input='{}')"` (the path Claude Code actually uses).
3. **Empirical timing gate.** Every PR that adds or modifies a SessionStart-registered hook MUST run `tools/measure_session_start.py` and document the before/after wall time. Target: individual hook < 300 ms, total < 1000 ms wall. Failures land WITH the timing evidence; never declared resolved on theory.

**Benchmark obligation:** the timing script's JSON output (`--json`) gives a `verdict` field (OK / WARN / FAIL). The PR description quotes the verdict + the slow_hooks list when the verdict is not OK, and the WHY (e.g., "Node cold-start floor; consolidating into hook-dispatcher is a separate roadmap item").

**One-time Owner activation** (per HR-001 -- PP cannot mutate ~/.claude/settings.json under auto-mode): the Owner runs the appropriate optimizer once per host. PP ships the scripts; the Owner invokes them:

```
python tools/register_global_hooks.py     # registers PP hooks
python tools/optimize_session_start.py    # removes the duplicate
                                          # orphan reaper +
                                          # async-wraps slow hooks
python tools/measure_session_start.py     # verify timing
```

**Reference implementation (sealed 2026-05-31, extended 2026-06-01):**

- `~/.claude/scripts/restart-claude.ps1` -- CONIN$ inject + flag + marker + fallback.
- `~/.claude/commands/restart.md` -- Win32 console architecture rationale.
- `hooks/restart_resume.js` -- SessionStart marker consumer (cwd-guarded, BOM-tolerant).
- `hooks/async_wrapper.js` -- generic detached spawner for slow hooks.
- `hooks/session_start_hub.js` -- single Node process for ALL PP SessionStart concerns (BL-SESSION-HUB-001).
- `tools/optimize_session_start.py` -- Owner-runnable, idempotent rewiring.
- `tools/migrate_to_hub.py` -- Owner-runnable, collapses 5 PP entries into 1 hub entry.
- `tools/measure_session_start.py` -- empirical timer + verdict.
- `tools/test_restart_and_lag.py` -- 15 V-RESTART-* + V-LAG + V-HUB gates.
- `vault/knowledge_base/ukdl-universal.md` § UKDL TRAP T-RESTART-001 + T-LAG-001 + T-NODE-COLD-001 + T-WIN-AV-001.

## SCS C23 -- Session-Hub-by-default (sealed 2026-06-01, BL-SESSION-HUB-001)

Successor / amendment to SCS C22 (which still applies). When the count of
PP-owned SessionStart entries in `~/.claude/settings.json` reaches 3 or
more, they MUST be consolidated into ONE Node hub process.

1. **Single hub entry.** PP-owned SessionStart concerns live as
   functions in `hooks/session_start_hub.js`. Adding a new SessionStart
   concern means adding a function call in the hub's `main()`, NOT
   adding a new entry to settings.json. The hub is the ONLY PP entry on
   SessionStart in steady state. Owner-side hooks (auto-vault-bootstrap,
   token-shield-refresh, learning-sentinel, lazarus-*) remain as
   separate entries -- the hub does not touch them.

2. **Inline vs detached partition.** The hub has at most ONE function
   that may write to stdout (the one that emits additionalContext). All
   others MUST be fire-and-forget: `spawn(..., { detached: true, stdio:
   'ignore', windowsHide: true }) + child.unref()`. The Windows stdio
   hard rule (T-ASYNC-WRAPPER-001) applies to the hub's spawns.

3. **Empirical budget.** `python tools/measure_session_start.py` must
   show `verdict: OK` on a majority of consecutive runs after the hub
   migration. Variance spikes (T-WIN-AV-001) are documented as OS
   noise, not regressions. The hub itself must run in < 1500 ms via
   `node hooks/session_start_hub.js` direct invocation (V-HUB-FAST
   gate).

**Sealed evidence (this host):**

| Stage | Individual max (ms) | Serial total (ms) | Verdict |
|---|---|---|---|
| Baseline | 4696 | 7375 | FAIL |
| Iter 2 (wrapper stdio fix) | 195 (clean run) | 888 | OK |
| Iter 3 (auto-vault wrap) | 491 (variance) | 2028 | WARN |
| **Hub (this clause)** | **220** | **430** | **OK** |

**95.3% reduction on individual max, 94.2% on serial total vs baseline.**

**One-time Owner activation flow (sealed 2026-06-01):**

```
python tools/optimize_session_start.py    # phase 1 (kept for backwards-compat)
python tools/migrate_to_hub.py            # phase 2 (collapses to hub)
python tools/register_global_hooks.py     # picks up restart_resume etc.
python tools/measure_session_start.py     # verify post-hub OK
```

Sealed BL-SESSION-HUB-001. Extends SCS C22, does not replace it.

## SCS C25 -- Dataset-Baseline-by-default (sealed 2026-06-01, BL-DATASET-BUILD)

Every system built using the Power Pack after 2026-06-01 MUST conform
to the Dataset Baseline -- the empirical floor proven by the
PP_DATASET_20260531T122242Z.md ingestion (15,425 lines, 10 Parts I-X
+ MASTER TOC, all under `vault/knowledge_base/pp_dataset/`):

1. **Spec in vault first**: the system's capability spec lands in
   `vault/knowledge_base/pp_dataset/` OR `vault/specs/` BEFORE the
   first line of production code is written. Code that lands without
   a corresponding spec is provisional, not Apex.

2. **Gap-prioritized**: an actionable gap list with explicit ROI /
   priority lives alongside the spec. Gaps not on the list are
   implicitly out of scope.

3. **Hard Rules derived before DONE**: every architectural decision
   that risks a future bug is encoded as a namespaced Hard Rule
   (`HR-<NAMESPACE>-NNN`) and installed in `CLAUDE.md` before the
   capability is marked DONE. Reference series this commit:
   HR-SECRET-001..007.

4. **V-tests empirical in cold state**: every capability ships a
   V-gate test that passes in cold state with no prior context. The
   consolidated suite is `tools/test_dataset_build.py`; new modules
   append at least one representative gate before DONE.

5. **OD-aligned**: budgets, thresholds, and escalation flow conform
   to the OD1..OD7 Owner-decisions table (compacted plan 2026-06-01).
   OD3 budgets: S=$5 / M=$15 / L=$30 / XL=$100.
   OD7 escalation: 2 fails -> Opus once, 3 -> STOP.

**Sealed evidence (this baseline cycle):**

| Module                  | Files | V-gates |
|---|---|---|
| Secret Firewall (M1)    |  5    |  9 |
| PreToolUse hook (M2)    |  1    |  7 |
| Hard Rules (M3)         |  2    |  3 |
| Cascade Prevention (M4) |  5    | 14 |
| Output Contracts (M5)   |  6    | 12 |
| One-Shot Compiler (M6)  |  4    | 14 |
| Cost Collapse (M7)      |  2    | 11 |
| Backlog Autopilot (M8)  |  3    | 11 |
| CPC-OS MVP (M9)         |  6    | 15 |
| Slash commands (M10)    |  2    |  1 |

**Consolidated done-gate**: `python tools/test_dataset_build.py` ->
`DATASET_BUILD_PASS=25/25` exit 0.

The PP_DATASET file is the quality floor for all future PP-built
systems. A new system is NOT Apex-complete until it demonstrates
parity with this baseline on the five clauses above.

Sealed BL-DATASET-BUILD 2026-06-01.

## SCS C26 -- Benchmark-Driven-by-default (sealed 2026-06-01, BL-BENCH-ROADMAP-001)

Every PP module that touches a hot path (SessionStart, UserPromptSubmit,
Stop, PreToolUse) MUST be measurable through `tools/bench_all.py`. A
module that cannot be measured cannot be governed. A measured module
that degrades the baseline >15% without documented justification
violates the standard.

1. **A bench is mandatory, not optional.** Adding a new PP capability
   in a hot path is incomplete until `tools/bench_all.py` has a
   benchmark function for it AND a corresponding entry in `TARGETS`.
   The target value is a concrete number drawn from empirical
   measurement, never an aspirational guess.

2. **A ledger is the source of truth, not memory.** Every bench run
   appends to `vault/benchmarks/ledger.json`. The last 50 entries
   are retained. `python tools/bench_all.py --compare` shows the
   delta against the prior entry; a >15% slowdown on any benchmark
   that previously sat at OK status is a regression and must be
   triaged before the session yields.

3. **A doctrine artifact is sealed, not assumed.** Major perf changes
   (a parallel patch, a port to a different language, a cache layer)
   carry both: a benchmark delta line in the commit body AND a
   UKDL trap entry in `vault/knowledge_base/ukdl-universal.md`. The
   trap explains the physical floor or the architectural constraint
   so the next agent does not re-attempt the same dead end.

4. **A failure is the empirical floor, not a stop sign.** Some
   benchmarks have physical floors that the PP cannot move (Windows
   AV variance, Python cold-start, Node cold-start, real network
   latency, SQLite cold open). When a benchmark sits at its floor,
   the target is RAISED to the floor + 10 % rather than the
   benchmark being "fixed". The honest read is sealed as a
   T-PERF-FLOOR-* trap, not buried.

**Sealed evidence (this host, audit 61d7807 -> S0_baseline e9d65af):**

| Benchmark | Pre-roadmap (61d7807) | Post-S0/S1.3 (e9d65af) | Status | Notes |
|---|---|---|---|---|
| session_start_worst_ms | 231 (pass2 median) | 440 (full-suite cold AV) | WARN | T-WIN-AV-001 dominant |
| jit_cold_start_avg_ms | 767 | 170 | OK | -78% (AV warm cache hit) |
| verify_spp_ms | 155 268 | 155 268 (S1.1 rolled back) | unchanged | T-PERF-VERIFY-SPP-PARALLEL-001 |
| vgate_total_ms | 111 466 (serial) | 71 204 (parallel in bench_all) | -36% | parallel runner inside bench_all |
| monitoring_once_ms | 6 002 | 4 429 | -26% | S1.3 parallel probes (modules/monitoring/observe.py) |
| pytest_total_ms | 27 019 | 9 901 | -63% | warm process state |
| anti_patterns_ms | 86 | 79 | OK | at floor |
| ceps_record_ms | 35 | 1 | OK | inner-only measurement |
| never_again_ms | 66 | 1 | OK | log near-empty |

**Reference implementation:**

- `tools/bench_all.py` -- unified runner + TARGETS dict + ledger writer
  + regression detector.
- `vault/benchmarks/ledger.json` -- append-only history (last 50 runs).
- `vault/benchmarks/bench_all_S0_baseline.json` -- first labeled
  snapshot of the post-bench_all + post-S1.3 state.
- `vault/audits/benchmark_audit_2026-06-01T12-34-21Z.md` -- the
  pre-roadmap audit; the authoritative reference baseline.
- `vault/knowledge_base/ukdl-universal.md` § T-PERF-VERIFY-SPP-PARALLEL-001
  + § T-TOOL-SENTINEL-RECOVERY-001 + § T-NODE-COLD-001 + § T-WIN-AV-001
  -- the trap library that documents physical floors.

**Apex axis v16 -- Benchmark-Driven Development.** Sealed 2026-06-01.
The PP has measured every clause it has shipped since BL-LAG-001; SCS
C26 makes that practice contractual rather than optional. Future
clauses that ship a hot-path component must produce a bench_all delta
line under the BL-X-NNN sealing block.

Sealed BL-BENCH-ROADMAP-001. Pairs with SCS C22 (latency floor) and
SCS C23 (hub consolidation); the three together govern the hot-path
budget for SessionStart + UserPromptSubmit.

## UKDL TRAP T-PERF-FLOOR-001..004 -- Documented physical performance floors

**Level:** UKDL Traps (OS / process-creation / network / storage floors).
**Sealed:** 2026-06-01 BL-BENCH-ROADMAP S4.1.

These are listed here in the doctrine file because SCS C26 references
them. The full body of each entry lives in
`vault/knowledge_base/ukdl-universal.md`.

| ID | Floor | Approx wall (Windows host) | Mitigation |
|---|---|---|---|
| T-PERF-FLOOR-001 | Python cold-start per subprocess | ~150 ms | Port to Node OR pre-warm daemon |
| T-PERF-FLOOR-002 | Node cold-start per process | ~25-50 ms | Consolidate via hub (already C23) |
| T-PERF-FLOOR-003 | Real network probe (curl / tcp) | ~500-1500 ms each | Parallelize (already S1.3 monitoring) |
| T-PERF-FLOOR-004 | SQLite cold open | ~10-20 ms first query | Pre-warm via daemon (not worth it) |

Cross-floor: T-WIN-AV-001 (300-700 ms variance on cold spawn) is
ORTHOGONAL and stacks on top of any floor above. Owner-side AV
exclusion on `C:\Users\User\.claude\skills\claude-power-pack` is the
ONLY mitigation; PP cannot fix this layer.

## SCS C27 -- Integration-Wiring-by-default (sealed 2026-06-02, BL-INTEGRATION-WIRING)

Every module built using the Power Pack MUST have its activation
mechanism wired in the SAME build cycle. There is no "module built --
wiring pending" state: a module that imports cleanly and passes its
unit V-gates but is not reachable from a hook, signal, decorator,
slash command, or agent is **not done** -- it is ORPHAN, and an orphan
module is a false sense of progress (it never runs in production).

**The wiring-mechanism decision is made by MEASURED latency**, not by
tool name (cross-ref: `feedback_automation_mechanism_by_measurement`):

| Activation cost | Mechanism | Example |
|---|---|---|
| < 200 ms, must see the event first | PreToolUse / Stop hook (inline) | Cascade Bash check, Secret Firewall |
| < 50 ms, additive context | UserPromptSubmit decorator on the JIT loader | One-Shot contract, Cost route |
| signal that fires on a condition | ProactiveSignal in the dispatcher | Backlog P0 surfacing |
| session-lifecycle, fire-and-forget | SessionStart hub function (detached) | CPC-OS pane register |
| > 1 s | Task Scheduler (Mechanism F), never inline | (none this cycle) |

**Sealed evidence (this cycle -- 5 ORPHAN modules -> 5 WIRED):**

| Module | Mechanism | Surface | V-gates |
|---|---|---|---|
| cascade_prevention | PreToolUse hook | hooks/cascade_check_bash.js | 6 |
| cost_collapse | TCO-gate function | tools/tco_compact_gate.py route_prompt | 1 |
| backlog_autopilot | ProactiveSignal | modules/pp_agents/signals/backlog.py | 8 |
| one_shot | JIT decorator | tools/jit_skill_loader.py | 5 |
| cpc_os | SessionStart hub | hooks/session_start_hub.js | 3 |

Consolidated gate: `python tools/verify_integration_wiring.py` ->
`INTEGRATION_WIRING_PASS=9/9`. The gap between "module importable" and
"module active" is technical debt of the first order; closing it is a
DONE precondition, codified as UKDL Trap T-ORPHAN-MODULE-001.

Sealed BL-INTEGRATION-WIRING 2026-06-02.

## SCS C28 -- Acceptance-Contracts-compose-not-reinvent (sealed 2026-06-02, BL-CPCOS-002)

Every multi-step acceptance contract added to an existing module MUST be
built against that module's REAL API and MUST compose its existing
primitives -- never reinvent them, never clobber a sibling function, and
never assume an API shape from a plan without verifying it in source.

Empirical origin: the CPC-OS section 208.2-208.5 build. The originating
plan supplied code against an assumed registry API (dict access,
`pause_pane`, `session_id`, `last_heartbeat`) that did NOT exist; running
it verbatim would have crashed on contact and would have OVERWRITTEN the
existing `recovery.py` (corruption recovery) with a same-named crash
detector. Reading `registry.py` / `router.py` / `handoff.py` first turned
a broken transcription into a correct composition.

Sealed standard:
1. **Read the real API before writing against it.** A plan's code is a
   hypothesis; the source is the contract. Diverge toward the real API
   and document the divergence.
2. **Compose, don't reinvent.** section 208.2/208.3 layer on the existing
   `route_intent` (unknown/dead/stale gate) + `record_handoff`; they do
   not re-implement pane safety.
3. **Extend, don't overwrite.** section 208.4 ADDED `detect_crash_state`
   alongside `recover_corrupt_registry`. A new function whose name
   collides with an existing file's purpose is a regression in disguise.
4. **Backward-compatible schema growth.** New `PaneRecord` fields carry
   defaults (`session_id=None`) so pre-existing JSON records still load.
5. **Intent-only at the session boundary.** section 208.2 restart
   validates + records a handoff; it NEVER writes
   `~/.claude/state/restart_pending.json` (owned by the legacy
   restart_resume.js flow) -- mixing writers there destabilises session
   restart (cross-ref BL-LAZ-STALE-001).

Gate: `python tools/test_dataset_build.py` -> 35/35 (the four CPC-OS
gates V-CPC-RESTART / V-CPC-SWITCH / V-CPC-RECOVERY / V-CPC-BACKLOG).
Cross-ref UKDL Trap T-ORPHAN-MODULE-001 (C27) and
`feedback_automation_mechanism_by_measurement`.

Scope honesty: the originating plan's DONE-GATE projected 39/39 and five
slash commands (/secret-scan /cost-autopsy /one-shot-compile /demo-ready
/revenue-ready) + tools secret_scan_repo.py / readiness_check.py. Those
artifacts are NOT present on this branch; their gates were NOT added (no
gate may reference a missing file). Real sealed total: 35/35.

Sealed BL-CPCOS-002 2026-06-02.
