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

### SCS C26 addendum -- verify_spp L3-row wall floor (sealed 2026-06-03)

The `verify_spp.py` umbrella verifier has a wall-time floor that
SCS C26 cannot move from outside the row implementation. The
`l3-engine` row (`tools/test_l3_intent.js`) measures **~75-86 s
wall on this host** in isolation. This is the L3 Intent-Lock
end-to-end self-test; rewriting it is a separate multi-day project
that lives OUTSIDE the perf-roadmap scope.

**Empirical seal (audit `61d7807` -> seal commit):**

| Mode | verify_spp wall | Notes |
|---|---|---|
| Serial (the default) | 155 s | Sum-of-rows; unchanged from audit baseline |
| `--parallel 3` (Sprint 2) | 76 s | -50.6 % vs serial; L3 dominates |
| `--parallel 3` (this seal) | 92 s | -40 % vs serial; sibling-pane rows added ~16 s of non-L3 work |
| `--parallel 3` theoretical floor | ~76-86 s | max(L3, sum(others)/workers) |

**The 90 % reduction target stated in the original roadmap plan
was overoptimistic.** It assumed the per-row times were uniform
and small. The empirical per-row profile (collected Sprint 2 and
re-confirmed in this seal) shows L3 dominates everything else by
an order of magnitude.

**Decision rule for future iterations:**

- `verify_spp --parallel N` with N in [2, PARALLEL_MAX_WORKERS=4]
  is the supported optimization path. The empirically-survived
  cap is N=3 on this host; N=6 reproduces
  T-PERF-VERIFY-SPP-PARALLEL-001 (>300 s regression).
- A serious-iteration roadmap targeting verify_spp wall below ~70 s
  MUST start by either (a) rewriting the L3 test harness to
  finish in <30 s, or (b) marking L3 as an opt-in row that
  verify_spp can skip for "fast" runs. Either is a separate scope
  with its own UKDL trap on landing.
- Until then, **76-92 s is the honest verify_spp wall under
  parallel mode on this Windows host**, not 15 s. Sealed.

Cross-ref: `vault/audits/benchmark_roadmap_final_2026-06-03T08-30-00Z.md`
for the full roadmap closure (Pane 1 perf track).

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
/revenue-ready) + tools secret_scan_repo.py / readiness_check.py. At C28
seal time those artifacts were NOT present and their gates were NOT added.
They were subsequently built against verified real APIs (commit 5a3e32a)
and the allowlist wiring closed (commit c87950b); the gate is now 44/44.
The projected "39/39" was never the real total -- 35 at C28 seal, 44 after
the commands shipped honestly.

Sealed BL-CPCOS-002 2026-06-02.

## SCS C29 -- Dataset-spec-is-vision-not-worklist (sealed 2026-06-02, BL-DATASET-INVENTORY)

A plan that asserts "N remaining gaps in the vault" is a HYPOTHESIS about
scope, exactly as plan code is a hypothesis about API (C28). Before
building any item a plan calls a "remaining gap", VERIFY its real
implementation status against the repo -- do not treat a concept listed
in a dataset spec as pending work.

Empirical origin: the "BUCKET B FINAL -- ~12 remaining gaps" plan. PASO-1
found there is NO authoritative remaining-gap tracker. `pp_dataset_04_gaps.md`
and `_05_improvements.md` are the dataset VISION SPEC (Parts III/IV --
cascade engine, output potency, PIEE, backlog harvester, etc.), and
`pp_dataset_MASTER.md` is an index, not a status board. Of the plan's five
"probable gaps":
- **hard_rules cascade->HR derive**: ALREADY shipped (extractor.py,
  BL-HARDRULE-001) -- it already admits cascade-failure lessons. Not a gap.
- **secret-scan allowlist wiring**: the ONE real, safe, composable gap.
  Built by composing the PROVEN sources (rotation_advisor.KNOWN_SAFE_VALUES
  + allowlist.is_allowed), not the plan's imagined `KNOWN_SAFE_VALUES` on
  the firewall. Live tree 12 CRITICAL hits -> 0 with --honor-allowlist.
- **ukdl_sync.py**: does not exist + would mutate OTHER repos' vaults
  (high blast radius) -> Owner-side, not auto-build.
- **budget_monitor / session_cost_estimator "integration"**: both modules
  exist; "integration" = settings.json / hook registration that HR-001
  denies in auto-mode -> Owner-side (C18 one-time-registration pattern).

Sealed standard:
1. **Inventory is a hypothesis.** Glob/grep/read the repo for each named
   gap before building. A listed concept that is already implemented,
   already Owner-side, or high-blast cross-project is NOT this turn's work.
2. **Build the smallest real gap with a verified API; skip the rest with a
   reason.** Anti-monolith: one composable gap > five speculative shells.
3. **Do not seal a triumphant "ALL N CLOSED".** Report the real number and
   the honest disposition of each non-built item (done / Owner-side /
   needs-architecture). A grand close on an unanchored count is the
   output-drift cascade the dataset itself warns against (39.9 / 45.x).

Gate: `python tools/test_dataset_build.py` -> 44/44 (the allowlist gate
V-SECRET-SCAN-ALLOWLIST). Cross-ref C28 (plan code is hypothesis), C18
(one-time-registration for config writes), and
`feedback_plan_code_is_hypothesis_verify_source`.

Sealed BL-DATASET-INVENTORY 2026-06-02.

## SCS C30 -- Sleepy-Skills-by-intent: extend the chokepoint, don't add a hook (sealed 2026-06-02, BL-SLEEPY-SKILLS-001)

A new "inject context on prompt intent" capability is almost never a new
hook. The UserPromptSubmit chokepoint already exists
(`tools/jit_skill_loader.py`) with a budget, session-dedupe, fail-open
contract, and a 5-deep decorator idiom (`_tco_inject_routing`,
`_pp_proactive_inject`, `_oneshot_contract_inject`, ...). A second
always-on hook for the same event is the "two systems for one job"
anti-pattern the plan itself flagged, and it risks double-injection.

Empirical origin: the "Sleepy Skills" plan proposed a parallel
`skill_router` hook (option B) or in-place JIT edits (option A). FASE -1
showed the JIT loader is ALREADY sleepy-by-default -- it just only
triggers on the 11 vendored Apollo modules. The right answer was Hybrid:
a testable `modules/skill_router/` (index + classifier) wired as ONE new
decorator on the existing `run()`.

Premise correction (report loudly, per `feedback_audit_disproves_owner_premise`):
the plan's "87 skills x 5KB = 110K tokens wasted if all active" is false --
skill BODIES are already lazy (loaded only on Skill-tool invocation); only
the ~1-line descriptions sit in the always-on registry. Nothing wastes
110K. The real gap was AUTO-ACTIVATION (the right skill firing with no
Owner command), not token waste.

Sealed standard:
1. **Reuse the injection chokepoint.** New intent-injection = a decorator
   on the JIT loader's `run()`, not a new UserPromptSubmit hook. Inherit
   its budget / dedupe / fail-open / additionalContext shape.
2. **Triggers come from the author's frontmatter `description`**, the
   curated trigger surface -- never word-frequency counting (which
   surfaces "should/using/context" noise). Match with WORD BOUNDARIES:
   a substring test makes "ui" match "build" and mis-classifies everything.
3. **Pointer cards, not bodies.** Inject an ~80-token nudge ("skill X
   matches -- invoke it via the Skill tool"), like `LATERAL_CARD`. The
   model pulls the full SKILL.md on demand; injecting the body is
   redundant with the model's own Skill-tool access.
4. **Hot path stays cache-read only.** The classifier receives a candidate
   pool; the disk walk (frontmatter heads, never whole files) is
   SessionStart-warm + tests, cached 1 h. Measured added cost: ~24 ms/prompt
   (classify itself 1 ms), under the 200 ms hub floor (C21).
5. **Negative signals are the precision layer.** A hard veto on
   backend/ops terms (jwt, deploy, sql, server) keeps "fix the JWT bug"
   asleep even when an incidental UI word appears.

Gate: `python tools/test_sleepy_skills.py` -> 8/8 (V-SKILL-INDEX-BUILDS,
V-SKILL-FRONTEND, V-INTENT-WAKEUP/SLEEP/CTX-FORCE/ACCURACY,
V-JIT-INTEGRATION, V-BASELINE-INTACT) + verify_spp `sleepy-skills` row.
Cross-ref C21 (performance-by-default in hot-path hooks), C27
(integration-wiring: prove activation, not just unit gate), and
`feedback_audit_disproves_owner_premise`.

Sealed BL-SLEEPY-SKILLS-001 2026-06-02.

## SCS C31 -- Spec-Driven-for-L/XL + premise-verification (sealed 2026-06-03, BL-SPEC-GATE-001 + BL-PREMISE-001)

Two structural fixes for the error classes the agent repeats, plus the
honest scoping that FASE -1 forced.

**Premise correction (report loudly, per C29 + feedback_audit_disproves_owner_premise):**
the spec-driven pipeline was NOT absent -- it LARGELY pre-existed and
fires today: `_oneshot_contract_inject` (scope+done-gate+budget on L/XL),
`_arch_check_inject` (design prompts), `_active_spec` (.specify + vault/specs
injection), `_detect_new_feature_intent_and_flag` (drops .pp-pending-spec.json
-> /speckit-spec). This block ADDED the missing pieces, it did not build
a parallel pipeline. And the plan's `compile_contract(task, size, max_files,
cwd)` 4-param signature did not exist (real: `compile_contract(description,
size)`) -- caught at plan time, which is the whole point of premise verification.

**Evidence-based taxonomy (the plan's assumed classes vs the NEVER_AGAIN
data):** the real #1 recurring PP error is "modules built but not
auto-activated cross-repo" (the orphan/wiring class -- already SCS C27),
NOT "plan assumes a nonexistent API" (CLASE 1, real but less-evidenced).
So premise_verifier was wired Tool + HR + verify_spp row (never a bare
library), because shipping it as a plain module would have made it an
instance of the very #1 error it is meant to prevent.

Sealed standard:
1. **L/XL gets a spec gate; S/M does not.** `modules.spec_gate.check_spec_gate`
   finds an existing spec (.specify/vault/specs/vault/plans/PRD.md/...) ->
   read_spec; none -> create_spec (One-Shot contract or karimo PRD parser).
   Advisory, never hard-block. The One-Shot compiler's optional `cwd`
   surfaces the advisory WITHOUT polluting the pure frozen-contract builder.
2. **Verify premises before acting on a plan.** `assert_premises([...])`
   confirms named files/functions exist and returns the REAL API as the
   correction on failure. A premise verifier shipped as a bare library is
   an orphan -- wire it (CLI self-test + HR-PREMISE-001 + verify_spp row).
3. **Mutex overlapping auto-injectors.** The spec-domain sleepy card is
   suppressed when `_oneshot_contract_inject` already fired (decorator
   reorder so skill_router runs outer of one_shot). Adding a domain that
   overlaps an existing always-on injector without a mutex = triple-injection
   noise.
4. **Synthetic cards only for tools that import.** auto-testing fails to
   import -> no card; karimo + arch-decision work -> cards emitted, and
   only when the target file exists on disk.

Gate: `python tools/test_spec_driven.py` -> 11/11 (spec domain, spec gate,
premise file/fn true+false, cross-repo, baseline-intact) + verify_spp
`spec-driven` & `premise-verifier` rows. HR-PREMISE-001 / HR-SPEC-001 /
HR-CONTEXT-001 sealed in the CLAUDE.md HARD RULES block (34 total).
Cross-ref C27 (orphan/activation), C28 (read source before code), C29
(inventory is a hypothesis), C30 (extend the chokepoint).

Sealed BL-SPEC-GATE-001 + BL-PREMISE-001 2026-06-03.

## SCS C32 -- Spec-Driven Department: real-contract signals on the existing dispatcher (sealed 2026-06-03, BL-SPEC-DEPT-001)

Three proactive agents -- pp-spec-guardian (L/XL task with no spec),
pp-premise-guardian (CLASE 1 unverified-premise risk), pp-error-analyst
(recurrence >= 3 without a Hard Rule) -- ride the EXISTING
proactive_dispatcher, not a parallel mechanism. This is C30 applied to
the agent layer: extend the chokepoint.

FASE -1 forced four premise corrections (the plan's snippets would have
crashed on every dispatch -- exactly the CLASE 1 class the department
exists to prevent):
1. Signals expose `evaluate(...) -> ProactiveSignal | None` (a dataclass),
   not custom `check_*` functions returning raw dicts. The dispatcher
   calls `module.evaluate(...)`.
2. `top_recurring()` returns `list[NeverAgainEntry]` dataclasses --
   attribute access (`.recurrence`, `.issue`), never `.get`; the field is
   `recurrence`, not `count`.
3. Registration is the `plan` list + `AGENT_CONFIGS` (throttle =
   `AgentConfig.cooldown_minutes`, already built-in). `dispatch()` returns
   `list[str]`, not dicts.
4. The dispatcher context carried no `prompt`/`cwd` -> the spec signal
   would be a CLASE 0 orphan. The JIT `ctx_in` now feeds both; the
   `V-DEPT-CTX-FEED` gate asserts the wiring so it cannot silently regress.

Two invariants enforced beyond the plan: (a) all three signals gate on a
context field (`session_had_errors` / large-task `prompt`) so a clean
context still dispatches to `[]` -- `test_proactive_agents::V-DISPATCHER-CLEAN`
stays green (16/16, verified). (b) error_recurrence reads installed-HR
text in-process (one file read), never a subprocess on UserPromptSubmit
(measurement doctrine: >1s belongs in Task Scheduler, not a hot hook).

HR-001: the three agent .md files are staged in `vault/agents/` + an
installer (`tools/install_department_agents.ps1`), NOT written to
`~/.claude/agents/` (auto-mode denies; new agent files cold-load and need
/restart). The installer + /restart is the documented Owner-side step.

Adding a new department agent = 3 artifacts: `vault/agents/<name>.md` +
`modules/pp_agents/signals/<domain>.py` (evaluate -> ProactiveSignal) + a
plan/AGENT_CONFIGS entry, plus a `test_spec_department.py` gate. Activation
gate: `verify_spp --row spec-department` (13/13). Cross-ref C27
(orphan/activation), C28 (read source before code), C30 (extend the
chokepoint), C31 (spec-driven for L/XL).

Sealed BL-SPEC-DEPT-001 2026-06-03.

## SCS C33 -- CPC-OS Session Snapshot: capture the unwired field, don't add a store (sealed 2026-06-03, BL-CPCOS-SNAPSHOT-001)

Goal: after any crash, restore every pane to its exact context from one
file. PASO -1 (read source first, C28) found that most of the asked-for
"enrich registry" work already shipped: `PaneRecord` already stores cwd,
started_at, session_id, status; `recovery.detect_crash_state()` already
builds a confidence-split restore plan (`claude --resume <id>` when a
session_id is known, else `cd <cwd> && claude`). The genuine deltas were
small and surgical:

1. One new optional field (`last_commit`), backward-compatible exactly the
   way session_id was (old JSON omits it -> None). NOT a parallel store.
2. `snapshot.py` renders `~/.claude/state/session_snapshot.md` by COMPOSING
   the registry + mark_stale_panes + recovery's confidence split + a live
   per-cwd git HEAD. No new source of truth.
3. The real bug: the SessionStart hub parsed stdin for cwd and **discarded
   session_id**, so every record was null and recovery's high-confidence
   `--resume` path was DEAD by starvation -- a built path with no producer
   (CLASE-0 sibling: not an orphan module, an orphan *field*). Fix = capture
   session_id from the single stdin parse and feed register_pane; the hub
   then register-THEN-snapshots in one detached process (no race).

Honest limitation documented, not hidden: the registry `task` is the literal
"active" for every live pane because the SessionStart payload has no
conversational task (no `PP_PANE_TASK` is set in practice). The snapshot
shows what the registry honestly knows; it does not fabricate a task.

Recognizer (CLASE-0-field): a data-model field + a downstream consumer that
both exist, with NO producer populating the field -> the consumer's path is
silently dead. Grep the producer (here: the hub's stdin parse) before
trusting that a built recovery path actually fires. Verified end-to-end:
piped a SessionStart payload with a session_id -> registry captured it ->
snapshot rendered `Resume: claude --resume <id>`. Hermetic gates 9/9 x3,
pytest 43, node --check OK. Cross-ref C27 (orphan/activation), C28 (read
source before code).

Sealed BL-CPCOS-SNAPSHOT-001 2026-06-03.

### C33 addendum -- the write->read->restore triad (sealed 2026-06-03, BL-CPCOS-RESTORE-001)

A state-snapshot writer with no reader that CONSUMES it is an incomplete
system -- documentation, not recovery. The snapshot half (write) shipped
first and looked done; the missing half was the restore script that READS
the snapshot and reopens the panes. This is the orphan-field lesson at the
SYSTEM level: a producer with no consumer is as dead as a consumer with no
producer. A recovery feature is complete only when all three legs exist and
are empirically chained end-to-end: WRITE (snapshot.py -> session_snapshot
.md + .json) -> READ (restore_panes.ps1 parses the json) -> RESTORE
(`cursor <path>` per repo + the exact `claude --resume <id>` per pane).

Mechanism reality (verify before building, C28): `wt` (Windows Terminal) was
NOT installed and, more importantly, wt tabs are a DIFFERENT surface from
Cursor panes -- spawning wt tabs would not restore the Cursor workspace. The
correct unit is `cursor <path>` per distinct repo (Cursor restores its own
panes via state.vscdb layoutInfo). Exact-conversation restore works even when
the registry never captured a session_id, by recovering the cwd's most-recent
transcript from `~/.claude/projects/<encoded-cwd>/<uuid>.jsonl` (encoding =
every non-alnum char -> '-'); existence-validated (BL-LAZ-STALE-001).

New Hard Rule (HR-CPCOS-RESTORE): if a state snapshot/checkpoint writer
exists and the reader/restore path does NOT, the system is INCOMPLETE by
definition -- do not declare the feature done. Ship the reader same cycle or
state the gap explicitly. Cross-ref C27 (orphan/activation), C28 (mechanism
reality before code), C33 (snapshot writer).

Sealed BL-CPCOS-RESTORE-001 2026-06-03.
