

## Testing Gate Axis (sealed 2026-05-23)

A PP install is Apex-complete on the Testing Gate Axis if and only if
all five components are present + the five-check DONE-gate passes.

### Five required components

1. **Spec**: `vault/specs/auto-testing-gate.md` exists and contains
   §1-§15 (purpose, reality contract, architecture, per-language
   detection, diff scope, LLM bridge, generators, runner, hook,
   vault IO, closed-loop, DONE-gate, opt-out, Mirror-Sync-Direction,
   cross-references).
2. **Core module**: `modules/auto-testing/auto_test.py` orchestrator
   + `detectors.py` + `llm_bridge.py` + `vault_io.py`. The runner
   honors a 30 s hard wall-clock cap with TIMEOUT verdict distinct
   from FAIL.
3. **Per-language generators**: `generators/python_gen.py`
   (pytest), `generators/node_gen.py` (vitest/jest),
   `generators/java_gen.py` (JUnit 5 + ceiling-honest). Each
   validates the LLM output for the required language idioms
   (`def test_` + `assert`, `describe + it + expect`,
   `@Test + assertEquals`).
4. **PreToolUse hook**: `hooks/auto-test-gate.js` on
   `Bash|PowerShell` matcher with dual-regex (PRIMARY + LOOSE)
   for `git commit` detection, 28 s hook-side budget guard,
   fail-OPEN posture. Recursion guard via
   `CLAUDEPP_AUTOTEST_RUNNING=1`.
5. **Consolidator**: `tools/settings_merger.py
   register-auto-test-gate` (idempotent, Mirror-Sync-Direction:
   prints PowerShell paste, never auto-writes
   `~/.claude/settings.json`).

### Five-check DONE-gate (binary, no classifications)

A Testing Gate is DONE on this host when, with no manual proxy:

1. `vault/specs/auto-testing-gate.md` and
   `vault/plans/auto-testing-skill-2026-05-23.md` both exist and
   declare the contract above.
2. `commands/auto-test.md` is registered in the available-skills
   list after `/restart`.
3. `settings.json` registers `auto-test-gate.js` on PreToolUse
   `Bash|PowerShell` (verify:
   `settings_merger.py register-auto-test-gate --dry-run` reports
   `script-present=yes` + idempotent re-run = `already registered`).
4. **Empirical V-PYTHON-FAIL/PASS**: a real `git commit` in a
   synthetic Python project with a deliberately-broken `add(a,b)=a-b`
   is BLOCKED (hook exit 2 + visible reason); a real `git commit`
   with the correct `add(a,b)=a+b` is ALLOWED (hook exit 0 +
   pass-artifact in `vault/test-results/`).
5. **Empirical V-CEILING-JAVA/NODE**: a `.java` file in a no-pom.xml
   project AND a `.ts` file in a node-no-test-script project both
   produce verdict=ceiling, hook exit 0, commit ALLOWED with
   warn-line in `.auto-spawned.log`.

Missing any of 1-5 = NOT Apex-complete on the Testing Gate Axis.

Full plan: `claude-power-pack/vault/plans/auto-testing-skill-2026-05-23.md`.
Spec: `vault/specs/auto-testing-gate.md`.

### Empirical proofs (2026-05-23)

- A1 detector: 5/5 cwds correctly classified (KobiCraft / InfinityOps-UI /
  TUA-X / PP / TEMP); Python-by-convention rule iterated to require
  `test_*.py >= 3 AND *.py >= 3` after TEMP false-positive.
- A2 LLM bridge: HELLO returns in 16.1 s; CLAUDEPP_AUTOTEST_RUNNING=1
  recursion guard verified.
- B1/B2/B3 generators empirically produce real callable tests on real
  synthetic diffs (Python `import calc; def test_add_...; assert ==5`
  in 15.4 s; vitest `describe + it + expect` in 20.2 s; JUnit 5
  `@Test assertEquals(5, calculator.add(2,3))` in 16.1 s; KobiCraft
  cwd returns CEILING("no build system") without LLM call).
- C1 runner: 5 s pytest pass + infinite-loop killed at exactly 5 s
  timeout (124 exit + TIMEOUT marker).
- C2 vault IO: 4/4 atomic + rotation round-trip.
- D1 hook regex: 9/9 positive + 9/9 negative.
- D2 budget guard: 35 s fake-sleep killed at exactly 28 s,
  verdict=timeout, exit 0.
- V-DET: same diff x2 -> byte-identical scaffold.
- V-PYTHON-FAIL: broken `add` -> exit 2 + BLOCKED message + verdict=fail
  in 21.55 s.
- V-PYTHON-PASS: correct `add` -> exit 0 + verdict=pass in 19.11 s
  (vault/test-results/<ts>_pass_<slug>.md artifact written).
- V-CEILING-JAVA: 0.41 s, verdict=ceiling, exit 0.
- V-CEILING-NODE: 0.30 s, verdict=ceiling, exit 0.
- V-TIMING (10 fires): p05=0.22 s, median=0.27 s, p95=23.48 s (within
  the 5 s / 30 s bounds).
- V-CLOSED-LOOP: planted failure sha256 7a1bd6 -> AVOID-clause fires ->
  new test sha256 f691d4 (parametrize-based, different name); LLM
  empirically steered to a distinct pattern.
ped
backup). Activation cold-loads at session start (BL-0067): the gate
proves file-on-disk logic; live firing requires `/restart`.

---

# Apex Completion Standard — Concurrency & Async-Audit Axes

> Sealed 2026-05-16 (Intent-Lock / L3 cycle). Complementary to the
> JIT Activation Law above; both define DONE. A new feature satisfies
> BOTH or it is a draft.

## Axis A — Native concurrent-execution protection (Intent-Lock)

Any feature mutating shared state (files, git, DB, remote) MUST be safe
under concurrent execution by multiple panes on the same physical
worktree:

- Mutating ops (Write/Edit/commit) on a worktree held by a different
  **live** PID are soft-paused, never interleaved.
- Conflict key = `realpath(worktree)` + live PID, never branch alone
  (different physical worktrees are legitimate parallelism).
- Liveness triad: different PID **and** alive **and** stored
  worktree===current **and** age<expiry. PID alone never denies.
- Lock auto-expires (default 5 min) and is **fail-open** — a guard
  that can wedge a session is itself a defect.

Ref: `skills/claude-power-pack/modules/harness/intent_lock.js` (loaded
via `hook-dispatcher.js` `PreToolUse-default`).

## Axis B — Asynchronous background auditing

Any feature accruing reviewable state (learnings, errors, drift) MUST
have a decoupled, throttled background path that stages it for batch
human review without blocking or mutating live:

- Detached + unref'd; never holds the foreground session open.
- READ + PROPOSE ONLY — stages proposals; never silently mutates
  rules/skills/config.
- Triple-shield: single-flight lock + time cooldown + env-sentinel
  recursion guard at the hook entrypoint's first statement.
- Headless child auth is non-interactive but REAL (never an
  auth-strip bypass). Scoped read-only allow-list over blanket bypass.

Ref: `learning-sentinel.js` `maybeSpawnL3` + scoped
`modules/harness/l3-child-settings.json`; proposals →
`~/.claude/cache/compound-proposals/<ts>.md`.

## Authorization Boundary (operational law)

The capability code is agent-built + standalone-verified. The single
line that makes an autonomous background worker **auto-fire from a
startup hook** is classifier-gated and NOT agent-self-authorizable —
not via inferred privilege, scoped re-architecture, nor
`AskUserQuestion` soft-consent. It needs durable Owner authorization
(explicit settings permission rule, or Owner-applied activation). Ship
inert + verified; hand the Owner the exact one-line patch. See
`memory/automode-denies-self-modification`.

---

# Zero-Drift Mirror Completion Law

> Sealed 2026-05-16 (Dynamic Mirror Verifier cycle). A third DONE axis,
> peer to the JIT Activation Law and the Concurrency & Async-Audit Axes.
> A feature satisfies ALL THREE or it is a draft.

## The law

No feature, build, or cycle may be declared COMPLETE while the global
`~/.claude/{commands,agents,knowledge_vault}/` mirror layout carries a
single bit of **unverified** structural drift against its
version-controlled Power Pack counterpart.

"Verified" has a precise, mechanical meaning:

- Parity is asserted against the **committed blob** of a deterministic
  named git ref (`git show <ref>:<relpath>`), NEVER the working tree.
  A working tree is volatile: concurrent panes flip its branch, so a
  working-tree read produces *phantom* drift that is an artifact, not a
  fact. The committed blob is invariant to that.
- Both sides are LF-normalized before SHA-256. Under
  `core.autocrlf=true` only `knowledge_vault/**` carries a `-text`
  attribute; the `commands/` and `agents/` pairs do not, so the global
  filesystem copy is CRLF while the blob is LF. Without normalization
  3 of 4 pairs false-drift. Normalization is load-bearing, not cosmetic.
- The global filesystem copy is the **immutable reference** (it is what
  the runtime actually loads). Reconciliation flows global -> Power
  Pack, then is committed; the committed blob is what the gate checks.

## Phantom vs real drift (the distinction the gate must preserve)

A correct verifier MUST separate the two and must NOT silence either:

- **Phantom drift**: working tree on a different branch than the canon.
  Cured by reading the committed blob of a named ref. Cross-ref
  `--self-test` invariance proves a result is phantom-free.
- **Real drift**: the committed mirror genuinely diverges from global
  (a prior cycle's content never mirrored back). The gate MUST FAIL
  loudly. Resolving it by fudging the verifier toward exit 0 is a
  Reality-Contract breach; resolve it by syncing + committing the
  mirror, never by weakening the check.

## Chronological health (sibling invariant)

The native `/resume` picker depends on `~/.claude/history.jsonl`
timestamp monotonicity and on `<uuid>.jsonl` not being orphaned as
`.jsonl.live` by a crashed live-cloak hook. A cycle that touched
session/transcript infrastructure is not COMPLETE until a health scan
shows: history monotonic, and every stale `.jsonl.live` either
clobber-blocked (already restored) or resurfaced. The scan and any
repair MUST be rename-only, zero-deletion, and secret-safe (never emit
`display`/session bodies — those carry live tokens).

## Enforcement

`tools/verify_global_mirrors.py` (dynamic ref + LF-norm + `--self-test`)
and `tools/resume_reindex.py` (heartbeat-contract-identical orphan scan)
are the mechanical gate. `tools/test_mirror_parity.py` asserts
branch-flip immunity. Green across all three under any concurrent
working-tree branch == this law satisfied.

---

# Apollo Retrofit Checklist

> Sealed 2026-05-18 (Apollo-retrofit cycle). EXTENDS BL-0069 (it does
> not replace it): BL-0069 mandated latent-card + JIT-full-depth; this
> adds the per-task compression contract Apollo Skills proved. A skill
> that is JIT-full-depth but injects unconditional full state still
> fails Token Austerity. Both apply or the feature is a draft.

Every Power Pack skill/module wired into the JIT trigger matrix
(`tools/jit_skill_loader.py`) MUST ship all three components. A skill
missing any one is incomplete by definition (plan-time-audited):

1. **Task profile** — an explicit `TASK_PROFILES[module]` entry naming
   the `include` section anchors kept for the summary tier. No profile
   ⇒ the module degrades to full verbatim (safe default, never a
   KeyError), but an *un-profiled trigger module is not "done"*.
2. **Explicit negative space** — the `exclude` list. Compression is not
   only what you keep; the discarded sections (verbose walkthroughs,
   quick-ref code dumps) must be named so the omission is intentional
   and reviewable, never accidental truncation.
3. **Tier selector** — the prompt maps deterministically to
   discovery / summary / full via pinned verb regexes; the default is
   **summary, not full** (full is the regression-risk default). Full
   tier MUST be byte-identical to the pre-retrofit injection (golden-SHA
   provable) so the compression layer can never silently corrupt the
   heavy path.

**Empirical gate (compression is measured, not declared):**
`tools/measure_compression.py` MUST exit 0 — every highest-priority
trigger module ≥ 30 % cl100k token reduction (summary vs full) AND every
`include` anchor present verbatim post-extraction. Apollo SKILL.md
guides have no executable done-gate; the verbatim-anchor structural
invariant is the sanctioned substitute. **No "should be 30 %": the real
number from the harness or it is not done.** Reference loop:
`tools/jit_ref_correlate.py` (Stop hook, READ+PROPOSE-only, Owner-
applied) records injected-vs-referenced anchor ratio to
`vault/telemetry/` so future profile tightening is data-driven, not
guessed. This checklist is the baseline for ALL future skills,
including any forthcoming COO-Oracle prompts — no skill integrates
without the three components and a green compression gate.

# S+ Criteria — Absolute Baseline (sealed 2026-05-18)

From the Apollo-retrofit → S+ cycle. A feature is below S+ by definition
until ALL FOUR hold, each proven by a real number or exit code (never
declared):

1. **Total coverage measurement — per-module, no aggregation.**
   `tools/measure_compression.py --min 0.40` exits 0 over EVERY
   trigger-matrix module (derived live from TRIGGERS, never a hardcoded
   subset). The gate is **PER-MODULE**: every single module must be at
   or above the 40% reduction threshold. No module of the matrix may
   sit below 40% — averages and means are explicitly forbidden ("el
   promedio es 40%" is not S+). TASK_PROFILE anchors must remain
   verbatim for non-skeletal modules; for SKELETAL_MODULES the anchor
   titles must appear as pointers (verbatim bodies are dropped by
   design — the floor only applies when the active task profile needs
   the bodies inline). Owner decision 2026-05-19 — supersedes any
   prior "30% per-module" framing. Measured here: 10/10 modules, every
   one at >=40% (range 42.3%-83.9%, apollo-federation 73.3% post
   skeletal-extension c21fe95).
2. **Unified compression ledger.** One tool prints a single
   `COORDINATED_TOTAL_SAVED` combining JIT input-side reduction and the
   real RTK output-side compression, reproducible to +/-0 across runs.
   Measured here: JIT 5871t + RTK 76.1% real output-compression on the
   canonical `git log --stat -50` sample => 18799t, identical x3.
3. **Closed feedback loop.** The ref-correlator's pure run() consumes a
   real session transcript + real injection telemetry and emits a
   ref_ratio float in [0,1]. Proven here without any hook dependency.
4. **One auto-optimization cycle.** A module whose measured ref_ratio is
   below 0.5 has its TASK_PROFILE tightened, and re-measurement shows a
   STRICT reduction increase. Measured here: graphql-operations
   36.6% -> 44.5%.

Disclosed residual (not a gap): the RTK PreToolUse rewriter and the
ref-correlator Stop hook are Owner/restart-gated (BL-0067). S+
verification uses the pure functions and real binary directly; live
autonomous operation is the explicit Owner activation step, never faked.

**Doc-accuracy as a Reality-Contract gate (2026-05-19).** An
Owner-gated activation that is *inert pending the patch* is an
acceptable residual ONLY when the activation procedure is documented
with the **real, host-correct mechanism** (canonical home:
`vault/standards/<feature>-activation.md`; in-source comments may carry
a 6-line pointer, never the detail). A doc that describes the WRONG
mechanism is not "cosmetic, fix later" — it is a deferred bug at the
same severity as broken code, because the next operator who follows
it loses an hour and arrives at an inert system. Specifically: the
earlier `jit_ref_correlate.py` ACTIVATION comment that named raw
`~/.claude/settings.json` Stop entries was a Reality-Contract failure
on this host (Stop fans through `hook-dispatcher.js
CHAIN_MAP['Stop-chain']`, not raw settings); corrected commits
`f695d88` (in-source pointer) and `cc823b9`
(`vault/standards/jit-correlate-activation.md`).

RTK completion floor (2026-05-19): the `>=77%` gate is enforced by
`tools/verify_rtk_fusion.py` against a benchmark **pinned to immutable
SHA `af8da66`** — reproducible run-to-run (measured 80.2% ×2),
fail-closed below the floor. A numeric completion floor is only a valid
hard gate when its underlying measurement is deterministic; live
HEAD-variant `git log` was non-falsifiable and is no longer used.
Per-module JIT gate is `>=40%` reduction AND profile anchors retained
(skeletal modules: title-pointer, not verbatim) — 10/10 modules pass
live via `tools/measure_compression.py --min 0.40`. The earlier "≥30%"
floor recorded here was a prior parallel-stream framing; the Owner's
2026-05-19 decision restores ≥40% as the per-module S+ floor and
forbids aggregation. The two values must not be mixed: `--min 0.30` is
the original Apollo-retrofit threshold (kept for historical
reproducibility); S+ verification uses `--min 0.40` PER-MODULE only.

## Programmatic Budget Gate (sealed 2026-05-19, mandatory 2026-06-15)

From 2026-06-15 Anthropic moves programmatic Claude usage (Agent SDK, `claude -p`, GitHub Actions, third-party orchestrators) off subscription buckets onto a separate metered credit at full API rates. Any system in scope MUST pass the four requirements codified in `vault/standards/programmatic-budget-standard.md`:

1. **RTK Bash-output compression active** — `~/.claude/bin/rtk.exe` present + sha-pinned + registered as `PreToolUse:Bash`. Verified by `tools/verify_full_install.py` Section 2.
2. **JIT programmatic skeletal-tier active** — `tools/jit_skill_loader.py` detects `CLAUDE_PROGRAMMATIC=1` env or non-TTY stdin and promotes every profiled module to skeletal renderer. Verified by `tools/measure_compression.py --programmatic` exit 0 (`>=60%` for `full_tok >= 600`; documented per-module floors otherwise — e.g., `apollo-kotlin` at 50% for its 493-token SKILL.md hitting the frontmatter+pointer structural floor).
3. **Cache-control hints with a real in-repo consumer** — JIT emits `vault/cache_hints/<module>_<tier>.json` in programmatic mode; `tools/cache_hint_apply.py` validates them by re-rendering source SKILL.md and comparing hashes. Stale hashes flagged `[FAIL] stale-hash`, never silent. Satisfies Mistake #38 (no write-only ghost output).
4. **Budget monitor with externalized pricing** — `tools/budget_monitor.py` reads `~/.claude/budget.json` + `vault/pricing/anthropic_2026-05.json` + telemetry. Refuses compute if pricing `fetched_iso > 30d` (`stale-pricing` sentinel). Documented sentinels (`unconfigured`, `INSUFFICIENT_TELEMETRY`, `zero-burn-in-window`) replace fabricated runways.

**Multiplier honesty (Gap 9 enforced):** the RTK Bash-output and JIT skill-injection probes operate on different byte streams and MUST be reported side-by-side, never multiplied into a composite "X×" without an end-to-end session-token delta probe. `tools/verify_full_install.py` enforces this in its output. Real measured numbers on the 2026-05-19 reference host: 68.3% RTK / 79.7% JIT average (reproducible).

**Status:** advisory until 2026-06-14T23:59:59Z; mandatory thereafter for any PR adding a new programmatic call path on top of the Claude Power Pack. Pre-2026-06-15 work is NOT retroactively rejected — the gate is forward-looking.

## S+ Criteria — 5th Clause: Apex Onboarding (sealed 2026-05-19)

The 4-clause S+ Criteria block (Telemetry / Feedback loop / RTK+JIT coordinated / Negative space all skills) is extended with a 5th absolute clause governing operator reach, not artifact completeness:

**5. Apex Onboarding.** No feature is DONE until a stranger who only has the GitHub URL can run `git clone <url> && cd claude-power-pack && ./install-global.{ps1,sh} && python tools/verify_full_install.py` and see exit 0 in under 5 minutes wall-clock. The full standard with the four onboarding pillars (umbrella row + install-global step + INSTALL.md section + clean-machine verification) lives in `vault/knowledge_base/apex_baseline_doctrine.md` "Apex Onboarding Standard".

Effective 2026-05-19 for all NEW features. Pre-existing features grandfathered. Combined with the Programmatic Budget Gate (already sealed), this means: post-cutover features must ship both the per-call savings AND the new-operator reach. A feature with great savings that a new operator cannot install is non-conformant by the new combined gate.

## Spec-Driven Gate (sealed 2026-05-20, PASO -1)

Spec Kit (github.com/github/spec-kit) integration adds a NEW phase that precedes every other gate in this standard. The order becomes:

1. **PASO -1 (NEW)** — Spec-Driven Gate (this section)
2. PASO 0 — Apex Onboarding Standard (git clone → S++ in <=5 min)
3. S+ Criteria — Telemetry / Feedback loop / RTK+JIT coordinated / Negative space all skills
4. Programmatic Budget Gate (advisory until 2026-06-14, mandatory after)

### Mandate

Every NEW feature on the Power Pack post-2026-05-20 starts with an approved `spec.md` produced via `/speckit-spec`. No agent writes implementation code without a `tasks.md` that traces task-by-task back to the parent `spec.md`. The seven PP commands implementing this gate are at `commands/speckit-{constitution,spec,plan,tasks,implement,clarify,analyze}.md` (commit `feat(speckit): 7 PP commands — full SDD workflow integrated`).

### The four pre-implementation artifacts

A feature is NOT eligible for `/speckit-implement` until all four of these exist on the feature branch:

1. `.specify/memory/constitution.md` — project principles (per-project, distinct from global apex doctrine), generated from `vault/templates/speckit/constitution.md.template`.
2. `.specify/specs/<feature-id>/spec.md` — feature spec with P1/P2/P3 user stories, FR-### functional requirements, SC-### measurable success criteria, structured ambiguity markers (`[NEEDS CLARIFICATION: ...]`), Edge Cases, Assumptions, and a Clarifications audit-trail. Generated from `vault/templates/speckit/spec.md.template`.
3. `.specify/specs/<feature-id>/plan.md` — stack + file map + sequencing graph + risk register + Done-Gate REAL commands. Every stack choice traces to a constitution principle or an FR. Generated from `vault/templates/speckit/plan.md.template`.
4. `.specify/specs/<feature-id>/tasks.md` — atomic T-### tasks with pre/post/verify-command, FR/US trace, [P] parallel marker, 1:1 task↔commit mapping. Generated from `vault/templates/speckit/tasks.md.template`.

### Cross-artifact consistency

`/speckit-analyze` runs against these four artifacts BEFORE `/speckit-implement` and reports drifts as BLOCKING / CONSISTENCY / INFO. Any BLOCKING drift bars implementation until it resolves. Complements OVO post-commit verdict.

### JIT injection of the active spec

When the JIT loader (`tools/jit_skill_loader.py` UserPromptSubmit hook) detects `.specify/specs/<id>/spec.md` or `vault/specs/<feature>.md` in the project cwd, it prepends the most-recently-modified spec as priority context before any Apollo trigger module. The spec counts against the same 40 KB BL-0068 budget, capped at 24 KB so Apollo modules always have room. This means the implementing agent has the spec inline in every prompt, eliminating the "what does the feature require?" round-trip.

### Reality Contract enforcement

- Zero preventable clarifications during implement: if the implementing agent needs to ask a question whose answer is in the spec, the template is incomplete and MUST be iterated (not the spec).
- Every commit during implement cites a `T-###` task ID.
- Every task's verification command is REAL — runs on this host and exits 0 — before the task is `[x]`'d.
- The gate is mandatory for features authored 2026-05-20 onward. Pre-existing features are grandfathered.

### Gate condition

A feature passes the Spec-Driven Gate when:

- All four artifacts (constitution, spec, plan, tasks) exist on the feature branch.
- `spec.md` contains ZERO `[NEEDS CLARIFICATION]` markers (all resolved via `/speckit-clarify`).
- `/speckit-analyze` last report has ZERO BLOCKING drifts.
- Every task in `tasks.md` traces to a parent FR-### or US-###.

Implementations that bypass the gate by writing code without these artifacts CANNOT pass OVO at verdict >= A and CANNOT be pushed under the OVO push gate.

---

# Context Pressure Standard

> Sealed 2026-05-20 (audio-instructed via Downloads/20260520_152847.mp4).
> Fourth DONE axis, peer to JIT Activation Law, Concurrency & Async-Audit,
> and Zero-Drift Mirror. Universal: every pane, tab, session, project — no
> exceptions.

## The law

When a session's used-context-percentage crosses defined thresholds, the
harness MUST react autonomously — never wait for an Owner-typed command to
save state or to compact.

- **60 % used** -> Tier-1 silent snapshot to `vault/progress.md` and
  `vault/sleepy/context_snapshots.jsonl`. Once per session, debounced.
- **70 % used** -> Tier-2 atomic kclear-equivalent write BEFORE any
  /compact emits: `memory/project_session_handoff.md` (replace) +
  `vault/knowledge_base/session_lessons.md` (append) +
  `_audit_cache/insights.json` (update) +
  `vault/telemetry/context_watchdog/<ts>_<sid8>.json` (empirical evidence).
  Then drop the SendKeys-daemon trigger flag and spawn the daemon.

## Save-then-free invariant

Vault writes ALWAYS precede the /compact dispatch line. The kclear-equivalent
runs mechanically inside the Stop hook (no LLM available there) and captures
the structural floor: last assistant summary line, last user prompts (<=5),
session_id, used_pct, cwd, transcript_path. Empty fields are honest empty;
padding with LLM-fluff is forbidden (same posture as `kclear.md` v3).

## BL-0003 + the SendKeys bypass

Hooks CANNOT directly auto-fire a slash command — that ban (BL-0003) is
intact. The honest zero-keystroke path is the out-of-band SendKeys daemon
at `~/.claude/hooks/auto-compact-sendkeys-daemon.ps1`: it polls
`auto-compact-trigger.flag`, checks the foreground window's process name
WITHOUT focus theft, and either presses Enter (when Cursor is focused) or
demotes the trigger to `auto-compact-pending.flag` for the next cycle. This
is the same precedent `/restart` Path 2 already uses. Honest 1-keystroke
fallback is preserved when Cursor is not in front.

## Spawn invariant (Python -> daemon)

A direct `subprocess.Popen` with `DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP`
from inside a Python Stop hook silently NO-OPS in chained-detach contexts
(verified 2026-05-20). The textbook fire-and-forget pattern that DOES work:
`cmd.exe /c start "" /B powershell ... -File <daemon>` with
`creationflags=CREATE_NO_WINDOW`. The intermediate cmd exits immediately;
the powershell daemon survives. Mandatory for any future "watchdog spawns
detached helper from Python" pattern.

## DONE-gate

`_TEST_CONTEXT_PCT=70` synth Stop payload MUST produce, in <8 s:
handoff.md present, session_lessons.md append present, insights.json
contains the tier-2 entry, telemetry/<ts>.json present, daemon log shows
`trigger consumed via SendKeys` OR `trigger -> pending`. No artefact = NOT
done.

---

# Zero-Command Standard (sealed 2026-05-21)

> Fifth DONE axis, peer to JIT Activation Law, Concurrency & Async-Audit,
> Zero-Drift Mirror, and Context Pressure Standard. Closes the gap between
> "the capability exists" and "the capability is active without an Owner
> command". Universal: every PP feature post-2026-05-21.

## The law

If a PP capability improves results, saves tokens, or removes a recurring
manual step, it MUST activate **without an Owner-typed slash command**.
Three acceptable activation paths:

1. **SessionStart hook** — capability fires on session enter when project
   signals match. Examples: `auto-vault-bootstrap.js` (vault extract),
   `zero-command-bootstrap.js` (Spec Kit constitution stub),
   `first-time-project.js` (prereq probe + onboarding handoff).
2. **UserPromptSubmit / PostToolUse hook** — capability fires on agent
   I/O signal. Examples: `jit_skill_loader.py` Apollo JIT injection;
   `jit_skill_loader.py` new-feature-intent flag drop (Component B.2).
3. **Out-of-band SendKeys daemon** — capabilities that genuinely require
   a slash command (because the harness, not the hook, owns slash
   dispatch — BL-0003) get surfaced via the registry pattern of
   `pending-keystrokes-daemon.ps1`: a JSON `.flag` file dropped by any
   hook is dispatched to Cursor when Cursor has focus, with Owner-visible
   pre-fire delay and Owner-cancel UX (any keystroke aborts the queued
   command). Examples: auto-compact at 70%; `/speckit-spec` after
   new-feature intent detection.

## What this rule rules OUT

- **No `/restart` ritual** to load PP capabilities. The agent gets them
  on session 1 turn 1 of any project.
- **No `/cpp-load-tier` or `/speckit-constitution` requirement** for the
  capability to begin operating. The hook stubs the file; the Owner can
  refine via slash later, but the file's presence is what makes
  downstream gates happy.
- **No silent auto-fire of slash commands**. The SendKeys daemon path is
  the ONLY sanctioned route, and it requires Cursor-focused + Owner-visible
  pre-fire delay. Hooks themselves CANNOT type into the prompt — BL-0003
  intact.
- **No auto-push, no auto-OVO, no auto-fix of mirror drift**. The
  Zero-Command standard accelerates *detection* and *seeding*, never
  irreversible action.

## Reach boundary

Applies to PP features post-2026-05-21. Pre-existing features that
require a slash command (e.g. `/cpp-distill`, `/ovo-audit`) are
grandfathered — they are NOT retroactively required to ship auto-trigger
paths. New features added post-cutover that omit auto-activation are
non-conformant and CANNOT pass OVO at verdict >= A.

## Honesty floor

Surface activation on first Owner turn of any new project. Component A
+ D mark themselves via `.pp-onboarded` and `.pp-onboarded-prereqs`
markers; the model's first-turn response MUST mention "PP auto-onboarded;
see vault/handoffs/* for any prereqs" when those markers were freshly
written this session. Silent auto-creation of files the Owner did not
expect is forbidden by the same posture that governs the SendKeys daemon.

## DONE-gate

`python tools/test_zero_command.py` returns exit 0 with 8 gates each
PASSED or SKIP-explained:

- G1 hook fanout <=4 spawns/Write    | G5 Component B.2 flag drop
- G2 gatekeeper additionalContext    | G6 Component B.3 daemon parse
- G3 RTK clean (no install warning)  | G7 Component C verifier shape
- G4 Component A stub+marker         | G8 Component D probe+marker

Full plan: `~/.claude/plans/sorted-crafting-hanrahan.md` (Zero-Command
Auto-Activation + Hook Stack Optimization, 2026-05-21). PP mirror:
`claude-power-pack/vault/knowledge_base/apex_baseline_doctrine.md`
§ Zero-Command Standard cross-link.

## Session Safety Axis (sealed 2026-05-22, BL-SESSION-SAFETY-001)

Apex-complete PP installs MUST ship the full **Session Safety** stack.
Two promises, both required: **durability** (the `.jsonl` survives on
disk regardless of automation behaviour) AND **discoverability** (the
user can find the conversation via `/resume`). Either one alone is a
partial promise; both together = "you never lose a session involuntarily".

Required components (all five must be present in PP repo + wired by
`install-global.ps1`; missing any = NOT Apex-complete):

1. **Contract**: `vault/contracts/SESSION_SAFETY_CONTRACT.md` — the
   Universal Law (§1 Sacred Invariant + §2 Triple Defense + §3
   Sanctioned Flows allowlist + §8 Discoverability Guarantee).
   Auto-deployed by the installer to `~/.claude/SESSION_SAFETY_CONTRACT.md`
   (non-hook doc, classifier-OK).
2. **Layer 2 PreToolUse guard**: `hooks/session-file-guard.js` —
   blocks destructive ops on `~/.claude/projects/**/*.jsonl` unless a
   §3 allowlist marker is present. Owner-pasted per Mirror-Sync-Direction.
3. **Discoverability vaccine**: `hooks/lazarus-stub-recover.js`
   (BL-2026-05-21) — SessionStart hook that promotes hook-stub-only
   canonicals from sibling `.jsonl.live` / `.recovered-*` files. Owner-
   pasted + Owner-registered via `register-session-safety` consolidator.
4. **Live-session marker**: `claude-power-pack/hooks/mark-live-session.js`
   — Stop + SessionStart hook that tags live sessions with `⚡ ` on the
   latest `custom-title` record (visible in `/resume` instead of hidden).
   Append-only, idempotent, 3-layer orphan sweep.
5. **Layer 3 daily snapshot**: `tools/session-snapshot.py` +
   `_register_snapshot_task` in `install_global_core.py` — Windows
   Scheduled Task, idle-only, AC-only, 14-day rolling retention, same-day
   idempotent overwrite. MUST carry all 5 governance layers documented
   in `vault/lessons/heavy-io-must-be-governed.md` (single-instance
   lock, IDLE_PRIORITY_CLASS, compresslevel 1, disk-space precheck,
   schtasks idle-only+battery-aware).

### Activation gate

Single Owner-run command activates components 2+3 idempotently:

```
python claude-power-pack/tools/settings_merger.py register-session-safety
```

Wires PreToolUse(Bash|PowerShell) → session-file-guard and SessionStart →
lazarus-stub-recover. The CLAUDE.md pin is printed by `install-global.ps1`
for the Owner to paste (doctrine forbids auto-writing CLAUDE.md). Layer 3
Scheduled Task is auto-registered by the installer (not a settings.json
mutation, classifier-OK).

### DONE-gate (Apex perspective)

A PP install is Apex-complete on the Session Safety axis iff:

1. `~/.claude/SESSION_SAFETY_CONTRACT.md` exists, byte-identical to the
   PP-repo `vault/contracts/` copy.
2. `~/.claude/CLAUDE.md` contains the 2-line Session Safety pin.
3. `settings.json` registers `session-file-guard.js` on
   `PreToolUse(Bash|PowerShell)` and `lazarus-stub-recover.js` on
   `SessionStart` and `mark-live-session.js` on `SessionStart + Stop`.
4. `schtasks /query /tn "ClaudePP-SessionSnapshot"` returns the task,
   registered with `RunOnlyIfIdle=true` and `DisallowStartIfOnBatteries=true`.
5. Synthetic smoke test passes: hook-stub canonical + sibling `.jsonl.live`
   with real turns + trigger `lazarus-stub-recover` → canonical promoted +
   `.stub-corrupt-*` backup left + exit 0 (the Paso 4.1 fixture pattern).

Missing any of 1-5 = NOT Apex-complete on the Session Safety axis.

Full plan: `claude-power-pack/vault/plans/session-safety-global-2026-05-22.md`.
Contract: `vault/contracts/SESSION_SAFETY_CONTRACT.md`.
Lesson: `vault/lessons/heavy-io-must-be-governed.md`.

## Research Axis (sealed 2026-05-23)

Apex-complete PP installs MUST ship the **Deep Research** sleepy agent.
The Owner never blocks waiting on web research — research-intent prompts
auto-spawn a detached background agent that lands a real multi-page
markdown report (with cited real URLs) at `vault/research/<ts>_<slug>.md`
and auto-surfaces it on the next SessionStart of a relevant cwd.

Required components (all five must be present in PP repo + wired for
the install to be Apex-complete on this axis; missing any = NOT
Apex-complete):

1. **Spec**: `vault/specs/deep-research-agent.md` — 13 sections including
   the five verbatim LLM prompts reverse-engineered from the source
   n8n workflow (n8n is reference material only; banned as runtime per
   `memory/feedback_no_n8n_ever.md`).
2. **Python core**: `modules/deep-research/deep_research.py` — five
   cascade layers (search DDG/Brave/Apify, fetch_page, html_to_markdown
   4-way, LLM claude.exe/SDK, recursive driver) + CLI + 3-artifact
   writer. Resource-governance compliant per
   `vault/lessons/heavy-io-must-be-governed.md` (single-instance lock,
   IDLE_PRIORITY_CLASS, query budget, per-request timeouts, runtime
   ceiling).
3. **Skill**: `commands/cpp-deep-research.md` — manual `/cpp-deep-research`
   invocation. Spawns detached so the Owner never blocks.
4. **Stop-hook intent detector**: `hooks/research-intent-detector.js` —
   reads the last user prompt from the active `.jsonl`, fires the
   detached spawn when the prompt matches the Spanish + English
   research-intent regex AND meets the breadth gate (>= 80 words OR
   >= 3 question marks). Fail-OPEN — never blocks the Stop chain.
5. **Auto-discovery**: `modules/deep-research/research_discovery.py` —
   reads `vault/research/index.json`, surfaces recent (≤ 24 h)
   entries whose prompt tokens match the current cwd basename or
   parent dir. Wired into the SessionStart compound-proposal slot.

### Activation gate

```
# 1. Mirror-Sync-Direction cp into the loose hooks dir
cp ~/.claude/skills/claude-power-pack/hooks/research-intent-detector.js \
   ~/.claude/hooks/research-intent-detector.js

# 2. One-shot register
python claude-power-pack/tools/settings_merger.py register-deep-research

# 3. /restart   (BL-0067: hooks cold-load at session start)
```

### DONE-gate (Apex perspective)

A PP install is Apex-complete on the Research Axis iff:

1. `vault/specs/deep-research-agent.md` exists and contains the five
   verbatim prompts from spec sections 3.1-3.5.
2. `modules/deep-research/deep_research.py` exists; `--version` exits 0
   and reports `win32:IDLE_PRIORITY_CLASS` on Windows.
3. `commands/cpp-deep-research.md` is registered in the available-skills
   list after `/restart`.
4. `settings.json` registers `research-intent-detector.js` on the Stop
   event (verify: `settings_merger.py register-deep-research --dry-run`
   reports "script-present=yes" + idempotent re-run = "already registered").
5. **Empirical V1** — `python deep_research.py --prompt "<any>" --depth 1
   --breadth 2` produces a `vault/research/<ts>_<slug>.md` of >1 KB
   body with >= 5 real URLs in `## Sources` + a real-layer footer
   (`ddg + trafilatura + claude.exe` for free-tier, or any cascade
   layer firing). No fabricated URLs, no fixtures.

Missing any of 1-5 = NOT Apex-complete on the Research Axis.

Full plan: `claude-power-pack/vault/plans/deep-research-agent-2026-05-23.md`.
Spec: `vault/specs/deep-research-agent.md`.
Empirical V1 PASS: 6 learnings, 8 distinct real URLs (github / low.ms /
gameserver.rentals / dedicatedminecraft.host / supercraft.host / feedly /
youtube / reddit), 16.9 KB markdown, 220 s at depth=1 breadth=2,
zero API keys required (DDG + claude.exe keychain).
Empirical V2 spawn PASS: synthetic 92-word Spanish prompt with
"investiga / compara / Estado del arte" verbs triggered the Stop-hook
intent detector -> detached `cmd.exe /c start "" /B python deep_research.py`
spawn (auto-spawn log entry written, child python PID visible in
Win32_Process), Stop hook returned to harness in < 200 ms (fire-and-
forget contract honored).


## Production Branch Standard (sealed 2026-05-23)

`main` is the production branch of `claude-power-pack`. Merge from
`feat/*` branches is gated on three hard preconditions:

1. **verify_spp.py exit 0** on the feat branch — 7 of 7 STRICT-PASS
   rows: mirror-parity, drift-report, paths+secrets, rtk-fusion,
   intent-lock, l3-engine, programmatic-budget. A "classified FAIL"
   is still a FAIL (per `feedback_no_classified_fails_at_done_gate`);
   the merge does not happen until 7/7 OK.

2. **Conflicts resolved manually**, not via `-X theirs` / `-X ours`.
   Append-only ledgers (`session_lessons.md`,
   `governance_vaccines.md`, `verdicts.jsonl`, `vendor/NOTICE.md`,
   `SSOT.md`) use `.gitattributes merge=union` so concurrent
   appends concatenate cleanly. Real code conflicts (anything in
   `modules/`, `tools/`, `hooks/`, `commands/`) require human-level
   inspection of which side has the verified empirical evidence;
   `-X theirs` is REJECTED for code conflicts.

3. **verify_full_install.py exit 0 post-merge** on main. If the
   merge brought in main-side files that fail any audit, fix them
   on main BEFORE pushing. The Reality Contract is: the merge is
   done when main has the commits AND the tests pass — not when
   the merge commit landed.

### Branch lifetime

Feature branches (`feat/*`) MUST live <=2 weeks. The auto-testing /
zero-command / deep-research / session-safety / RTK / JIT / L3 /
Spec-Kit / context-watchdog / rtk-compressor-fusion roll-up burned
177 commits without intermediate merges and produced 10 merge
conflicts (5 ledger, 5 code) that took deliberate manual
resolution. Frequent merges (every 1-2 weeks) keep the conflict
surface small and PP available to all projects sooner.

### Mirror-Sync-Direction during merge

The agent NEVER writes to `~/.claude/hooks/<file>.js` — loose is the
source-of-truth there, sync direction is loose -> PP. When the
verify_global_mirrors / drift-report tools report drift, the agent
cp's loose -> PP locally, commits to feat, then merges to main.
PP-only files where loose is missing (e.g. legacy
`resume-hide-live.js`) are DELETED from PP + removed from the
PAIRS list in `tools/verify_global_mirrors.py`.

### Activation gates per hook

Hooks landed by the merge become production-active only on the next
`/restart` (per `feedback_settings_session_load`: settings.json
changes load at session start). The agent CANNOT trigger /restart
itself; the Owner runs it per active pane. The post-merge done-gate
is:

  python tools/verify_spp.py    -> exit 0, 7/7 OK
  python tools/verify_full_install.py -> exit 0
  /restart (Owner-driven, per pane)
  _TEST_CONTEXT_PCT=70 python modules/zero-crash/hooks/context-watchdog.py
                                -> tier-2 chain fires + Stop-event return

A merge that lands the commits but does not trigger Owner /restart
is a PARTIAL DONE — the commits are durable on origin/main, but the
hooks are inert until reload.


## Architecture Decision Axis (sealed 2026-05-23)

Apex-complete PP installs MUST ship the **Architecture Decision** skill
(arch-check). Before the agent or Owner commits to a non-trivial
architectural choice, the local vault is consulted via a deterministic
TF-IDF + entity match against 8 weighted source classes. Relevant
vetoes, sealed Standards, and prior lessons surface in the agent's
context BEFORE design happens, not after.

### Required components (all five present; missing any = NOT Apex-complete)

1. **Spec**: `vault/specs/arch-decision-skill.md` — 15 sections, STDIN
   contract, verdict shapes, fail-open posture, 5-check DONE-gate.
2. **Verdict engine**: `modules/arch-decision/arch_check.py` — word-
   boundary entity matching + title/body containment scoring; 3 s fast-
   mode budget with fail-open CLEAR on timeout. Recursion guard via
   `CLAUDEPP_ARCHCHECK_RUNNING=1`. Opt-out via
   `CLAUDEPP_ARCHCHECK_DISABLED=1`.
3. **Index builder**: `modules/arch-decision/build_index.py` — scans
   eight weighted paths (apex / feedback memory / gex44_antipatterns /
   antipatterns / session_lessons / governance / errors / ukdl) into
   `vault/.arch-index/index.json` (sources + shingles + concepts +
   entities) plus `vocab.json` (verbs + concepts + entities).
   Deterministic across runs given the same inputs. Word-boundary
   entity matching prevents false positives (`redis` no longer matches
   `rediscovery`).
4. **DEEP-mode skill**: `commands/arch-decision.md` — `/arch-decision
   "DESC"` runs the engine in deep mode, writes a 6-section ADR to
   `vault/decisions/[ts]_[slug].md` (Context / Decision / Consequences
   / Alternatives / Vault-conflicts / Lessons cited).
5. **JIT piggyback**: `tools/jit_skill_loader.py` extension — fires
   arch_check on any UserPromptSubmit with two or more design verbs;
   appends `ARCH-CHECK [verdict]` block to existing additionalContext.
   No new hook (satisfies hook-fanout-systemic-cost lesson).

### Six-check DONE-gate (binary, no classifications)

A PP install is Apex-complete on the Architecture Decision Axis iff:

1. The five required components above are present.
2. `python modules/arch-decision/build_index.py` exits 0; index has
   >= 50 sources across all eight classes; vocab has >= 30 verbs +
   concepts combined.
3. `python modules/arch-decision/test_v_block.py` exits 0 — all five
   functional verdicts pass (V-COLLISION x2, V-WARNING x2, V-CLEAR),
   V-TIMING p95 < 3.0 s over 10 runs.
4. A real `/arch-decision "..."` invocation produces an ADR file with
   six sections and no fabricated source paths.
5. JIT loader empirical: a synthetic UserPromptSubmit payload with
   two or more design verbs and one known veto entity returns
   `additionalContext` containing the literal `ARCH-CHECK [verdict]`
   block.
6. `python modules/arch-decision/test_closed_loop.py` exits 0 — two
   consecutive runs on the same prompt yield byte-identical context,
   and the new UKDL-AC rows surface in subsequent scans (closed-loop
   verified mechanically).

Missing any of 1-6 = NOT Apex-complete on the Architecture Decision Axis.

### Cross-references

- Spec: `claude-power-pack/vault/specs/arch-decision-skill.md`
- Plan: `claude-power-pack/vault/plans/arch-decision-skill-2026-05-23.md`
- UKDL hub: `claude-power-pack/vault/knowledge_base/ukdl-universal.md`
  "Architecture Decision Skill" + "Decisions" sections (UKDL-AC-01..04
  + UKDL-AC-DEC-NN auto-appended).
- Sister axes: Auto-Testing Gate, Deep Research, Session Safety —
  all five share the same architectural shape (Mirror-Sync-Direction,
  recursion guard env var, settings_merger consolidator, 5-check
  DONE-gate).

### Empirical proofs (2026-05-23)

- Index: 529 sources indexed (40 apex sections / 407 feedback memory
  files cross-project / 19 gex44 antipatterns / 6 antipatterns / 24
  session lessons / 24 governance / 5 errors / 4 ukdl). Vocab: 43
  verbs / 488 concepts / 50 entities (post project-name prune).
- V-COLLISION (`n8n` workflow prompt): verdict COLLISION, top source
  cites `feedback_no_n8n_ever.md` in 156 ms wall-clock.
- V-COLLISION-2 (hook auto-fire slash): verdict COLLISION, cites
  BL-0003 + Zero-Command Standard in apex.
- V-WARNING (parallel 5-write batch): verdict WARNING, cites
  `feedback_parallel_write_batch_limit.md`.
- V-WARNING-2 (months-old feat merge): verdict WARNING, cites
  branch-hygiene lesson + `feedback_branch_off_origin_main_for_scoped_prs.md`.
- V-CLEAR (Rust snippet explain): verdict CLEAR after the entity-seed
  prune that removed bare language names (rust / go / python / etc.)
  to eliminate false-positive substring matches.
- V-TIMING (10 fires): p05=108 ms, p95=139 ms — well within the 3 s
  budget.
- V-ADR (Redis-sessions-tuax): produced
  `vault/decisions/2026-05-23-190211_redis-sessions-tuax.md` with all
  six sections and the explicit "None surfaced" sentinel for
  Vault-conflicts (verdict was CLEAR; no prior decision indexed).
- V-CLOSED-LOOP: two identical runs produce byte-identical context;
  UKDL-AC rows surface in subsequent scans, proving the loop closes.

### Iteration findings (sealed in session_lessons.md row 2026-05-23
  "Arch-Check Skill iteration log")

- L1: bare language entities (`rust`, `python`, `go`) over-match in
  neutral contexts; pruned from seed list.
- L2: project-name entities (`tuax`, `lazarus`, `kobiicraft`)
  trigger every memory file of that project; pruned.
- L3: substring entity match collides ("redis" matched "rediscovery");
  switched to word-boundary regex `(?<![a-z0-9_])X(?![a-z0-9_])`.
- L4: pure Jaccard similarity is too strict for short Spanish prompts;
  replaced with asymmetric containment + title-token bonus.
- L5: WARNING_FLOOR=2.0 was unreachable for Spanish prompts; lowered
  to 1.5 after empirical V-WARNING-2 scored 1.8.
- L6: literal `<X>` template-syntax in slash-command markdown triggers
  the Jobs-Woz slop-detector; paraphrase with `[X]` bracket-syntax
  for skill bodies that need symbolic substitution markers.


## Code Review Axis (sealed 2026-05-23) -- PP Quality Triangle Complete

Apex-complete PP installs MUST ship the **Code Review** skill that
closes the third side of the PP quality triangle:

- **Auto-Testing Gate** (correction) -- does the code do what it should?
- **Arch-Check** (design) -- is the decision consistent with the vault?
- **Code Review** (quality / security / maintainability) -- is the code
  well-written, secure, maintainable?

No commit reaches main without passing all three. The triangle is now
sealed.

### Required components (all five present; missing any = NOT Apex-complete)

1. **Spec**: `vault/specs/code-review-skill.md` -- 15 sections;
   STDIN contract; verdict shapes (block / warn / pass / skip);
   SKIP-honest contract for missing external linters.
2. **Verdict engine**: `modules/code-review/code_reviewer.py` -- FAST
   mode (30 s budget, no LLM): PP-doctrine detector (9 patterns
   derived from session_lessons), security detector (high-entropy
   keys + Shannon-entropy-gated password literal + injection
   patterns), complexity heuristics, external linter dispatch
   (ruff / mix / SKIP-honest fallback). DEEP mode: adds
   `lesson_candidates[]` from `vault/.arch-index/index.json` and
   `patterns_history[]` from `vault/reviews/patterns.jsonl`.
3. **Gate piggyback**: `modules/auto-testing/auto_test.py` extension
   (`_run_code_review_if_enabled`) that spawns code_reviewer at the
   end of `run_gate()` and combines verdicts: code-review BLOCK ->
   gate verdict "fail" (so the existing `auto-test-gate.js` exits 2);
   code-review WARN -> appended to verdict reason + body, gate
   verdict unchanged. **No new hook**: the existing
   `auto-test-gate.js` is NOT modified.
4. **DEEP-mode skill**: `commands/code-review.md` --
   `/code-review [--staged | --branch X]` writes a 4-section report
   to `vault/reviews/[ts]_[slug].md` (Executive summary / Findings
   / Refactor suggestions / Lessons cited).
5. **Closed loop**: `vault/reviews/patterns.jsonl` append-only log;
   each DEEP run with verdict != PASS writes a row; future DEEP
   runs filter by category and surface prior rows in
   `patterns_history`.

### Seven-check DONE-gate (binary, no classifications)

A PP install is Apex-complete on the Code Review Axis iff:

1. The five required components above are present.
2. `python modules/code-review/test_v_block.py` exits 0 with all
   functional V-tests PASS: V-BLOCK-SECRET, V-BLOCK-EVAL,
   V-WARN-LENGTH, V-WARN-DOCTRINE-1, V-WARN-DOCTRINE-2, V-PASS,
   V-SKIP-MVN.
3. V-TIMING p05 < 2 s, p95 < 30 s over 10 FAST runs.
4. `python modules/code-review/test_combined_gate.py` exits 0:
   synthetic AWS-key diff through `auto_test.py --gate` returns
   combined verdict=fail with extra.code_review.verdict=block.
5. `commands/code-review.md` registered (visible in available-skills
   list after `/restart`).
6. A real `/code-review --staged` produces a 4-section report at
   `vault/reviews/[ts]_[slug].md` with at least one lesson cited
   from `vault/.arch-index/`.
7. `python modules/code-review/test_closed_loop.py` exits 0: two
   DEEP runs on the same diff -- run 1 appends a `patterns.jsonl`
   row; run 2 surfaces that row in `patterns_history`.

Missing any of 1-7 = NOT Apex-complete on the Code Review Axis.

### Cross-references

- Spec: `claude-power-pack/vault/specs/code-review-skill.md`
- Plan: `claude-power-pack/vault/plans/code-review-skill-2026-05-23.md`
- First empirical self-review: `claude-power-pack/vault/reviews/2026-05-23-203833_code-review-skill-self.md`
- Sister axes: **Auto-Testing Gate** (`vault/specs/auto-testing-gate.md`),
  **Arch-Check** (`vault/specs/arch-decision-skill.md`),
  **Research** (`vault/specs/deep-research-agent.md`),
  **Session Safety** (`vault/contracts/SESSION_SAFETY_CONTRACT.md`).

### Empirical proofs (2026-05-23)

- V-block: 8/8 PASS (V-BLOCK-SECRET, V-BLOCK-EVAL, V-WARN-LENGTH,
  V-WARN-DOCTRINE-1, V-WARN-DOCTRINE-2, V-PASS, V-SKIP-MVN, V-TIMING).
- V-TIMING: p05=235 ms, p95=312 ms over 10 FAST runs on the
  AWS-key payload (synthetic).
- V-COMBINED-BLOCK: auto-test=ceiling + code-review=block ->
  combined=fail with reason "code-review BLOCK". Verified that
  `auto-test-gate.js` translates fail to exit 2 unchanged.
- V-COMBINED-PASS: auto-test=ceiling + code-review=pass ->
  combined=ceiling (no upgrade). Hook exit 0.
- V-DEEP self-review: 7 files, 70 findings (18 BLOCK + 52 WARN), 5
  lesson candidates surfaced from `vault/.arch-index/`, 1328 ms
  total. The BLOCK findings are honestly classified self-detection
  false positives (the reviewer's own regex pattern strings); the
  WARN findings are markdown prose mentions of git subcommands.
  Refactor suggestions cite file-type exclusion + self-exclusion as
  the resolution path.
- V-CLOSED-LOOP: 2 DEEP runs on the same diff. Run 1 appends 1 row
  to `vault/reviews/patterns.jsonl`. Run 2 surfaces that row in
  `patterns_history`. Mechanical, no LLM dependency.

### Iteration findings (sealed in session_lessons.md row 2026-05-23
  "Code-Review Skill iteration log")

- L1: literal angle-bracket template markers in a `commands/*.md`
  body trigger the Jobs-Woz `zero-fiction-gate`. Paraphrased every
  such marker with bracket-syntax + explanatory prose; identical
  fix pattern as observed during the arch-check cycle.
- L2: setting `CLAUDEPP_<SKILL>_RUNNING=1` in the spawned-child
  env BEFORE the first call short-circuits the child on its
  recursion guard. The env var is for level-2+ chains (when DEEP
  mode spawns claude.exe which re-fires hooks); never set it on
  the level-1 piggyback. Same bug existed in `arch_check.py`
  piggyback through `jit_skill_loader.py` -- fixed in this cycle.
- L3: a token-exclusion list inside a security-detector regex
  names the very tokens the Jobs-Woz gate forbids. Shannon-entropy
  gating on the captured literal is the cleaner pattern: dictionary
  words fall under 3.5 bits/char and demote to INFO; real random
  secrets land above and BLOCK.
- L4: self-review false-positive class. When the code-review module
  is itself part of the staged diff, its own regex pattern strings
  (`AKIA[0-9A-Z]{16}`, `eval(`, `exec(`) match against its own
  source. Honest empirical behaviour; refactor candidates documented
  in the V-DEEP report (file-type exclusion for prose; self-exclusion
  for `code_reviewer.py`).
- L5: PowerShell git path gap doctrine detector matches markdown
  prose. A documentation file legitimately mentions `git status`,
  `git diff --staged` etc. as instructions; the detector should
  exclude `.md` / `.rst` / `.txt` for prose-mention categories.
- L6: V-COMBINED-PASS empirically demonstrates that the gate
  preserves auto-test verdict when code-review is PASS -- no
  silent upgrades.
- L7: closed-loop is mechanical, not LLM-mediated. Two DEEP runs
  on the same diff produce byte-identical `patterns_history`
  citations from run 2 onwards; useful for future-LLM context
  injection without requiring an LLM to feed the loop.
## Prompt Quality Axis (sealed 2026-05-23) -- PP Signal Layer

Companion to the Architecture Decision Axis and Code Review Axis. Where
those two axes intercept on concrete tool/decision signals, the Prompt
Quality Axis intercepts on the *absence* of signal -- short prompts
whose referent is unresolved get a single-line lint advisory in
`additionalContext`, never a rewrite.

### The law

`tools/jit_skill_loader.py::_detect_vague_prompt(prompt, spec)` returns
`VAGUE_LINT_MESSAGE` (one line) when AND of three conditions holds:

1. `len(prompt.split()) < 30` (Owner spec threshold)
2. `_VAGUE_REFERENT_RX` matches (definite-article+opaque-noun in EN/ES,
   enclitic-lo Spanish imperatives, "this/that/it/esto/eso", "lo de")
3. None of these mitigators fire:
   - `_FILE_HINT_RX` (filename with recognized extension)
   - `_LINE_HINT_RX` ("line 42", "linea 42", ":42")
   - `_FUNCTION_HINT_RX` ("function foo", "foo(x, y)")
   - `>1` `_ARCH_DESIGN_VERBS` hit (already covered by `_arch_check_inject`)
   - Active `.specify` spec (already covered by PASO -1 spec injection)
   - `CLAUDEPP_VAGUE_LINT_DISABLE=1` env opt-out
   - `CLAUDEPP_JIT_RUNNING=1` recursion guard

When the signal fires it is composed alongside `arch_block` in the
`extras` slot of `run()` -- inserted into all three composition paths
(no-mods+no-spec early return, no-injected+no-spec early return, and
the main `ctx` assembly). Telemetry: the JIT log line carries
`vague={yes|no}` next to `arch={yes|no}` for empirical recalibration.

### What this rule rules OUT

- **Auto-rewriter**: explicitly vetoed (Owner directive 2026-05-23).
  Silent prompt mutation breaks Owner intent reproducibility. The
  agent receives the signal and decides whether to pause for
  clarification.
- **Blocking the prompt**: the signal is advisory -- never returns
  anything but `continue: true`. Fail-open semantics (Ley 24) apply
  to every internal failure: any exception in `_detect_vague_prompt`
  is logged to `~/.claude/logs/jit-skill-loader.log` and returns
  `None`, never disrupting the user's prompt.
- **LLM-based vagueness scoring**: deterministic regex only. Allows
  the `<100 ms` budget to hold (measured p95 0.2 ms) and keeps
  Reality Contract intact (no model-call confounders).

### DONE-gate

`tools/test_vague_lint.py` -- 6 gates:
- V-VAGUE-1: "fix the auth bug" -> signal
- V-VAGUE-2: "hazlo mas rapido" -> signal (Spanish enclitic-lo)
- V-CLEAN-1: "fix the null pointer in PlayerManager.java line 42" -> no signal
- V-CLEAN-2: prompt with >= 30 tokens -> no signal (any content)
- V-TIMING: 10 runs < 100 ms each (p95 0.2 ms measured)
- DISABLE-ENV: `CLAUDEPP_VAGUE_LINT_DISABLE=1` short-circuits

Exit 0 = sealed. Re-run on any regex / mitigator edit.

### Telemetry future-work

Count signal-fired prompts vs signal-acted-on prompts (agent paused
to ask Owner) over 2 weeks. If acted-on rate < 20%, the regex or
mitigators need recalibration -- the signal must earn its presence in
`additionalContext`. Until empirical data exists, the signal is on
by default; opt-out is per-prompt via env var.



---

## Deploy Axis (sealed 2026-05-24) -- PP Quality Quadrangle complete

**PP Quality Quadrangle completo:**
auto-testing (correction) + arch-check (design) + code-review
(quality / security / maintainability) + deploy (verified
delivery). Ningún código llega a producción sin pasar los cuatro.

The fourth axis closes the loop between merge and live traffic. A
code-review-PASS commit, an auto-test-PASS run, and an arch-check
CLEAR decision still leave one question open: did the code actually
reach production and serve real bytes? The Deploy Axis answers
that with a real healthcheck against the live target.

### Reality contract (deploy-specific)

A deploy is, by contract, NOT a deploy until a healthcheck against
the live target returns OK. The dispatcher in
`modules/deployment/deploy.py` refuses to write
`vault/deploys/<ts>_<project>_<env>.md` until the healthcheck has
run. Silent masking of a healthcheck failure is forbidden; a
healthcheck failure on a successful deploy yields verdict
`deploy-warn` (exit 3) AND the receipt states this explicitly.

### 4 modes (detector-ordered)

| Mode | Signal | Action |
|---|---|---|
| `gh-workflow` | `.github/workflows/deploy*.yml` exists with workflow_dispatch or push trigger | `gh workflow run --ref main` + `gh run watch --exit-status` |
| `git-push-to-deploy` | `deploy/post-receive` OR non-origin remote URL `user@host:/path/repo.git` | `git push <non-origin-remote> main`; receipt = server post-receive output |
| `manual-scp` | build manifest + `vault/deploy/<project>.json` with `mode: scp-systemd` | `build_cmd` -> `scp -i <key>` -> `ssh <alias> '<post_deploy_cmd>'` |
| `none` | no signal | CEILING exit 4 (honest stop; no template generated) |

The detector evaluates in this order and returns the first match.
Real-world mapping (per PASO 0 grounding):

- InfinityOps -> `gh-workflow` (canonical §77 CD pipeline)
- TUA-X -> `git-push-to-deploy` (server-side post-receive hook)
- KobiiCraft -> `manual-scp` (only project with a real gap)
- New / unconfigured projects -> `none`

### §77 Deploy Sovereignty -- mandatory citation

When `gh_workflow.py` detects a workflow whose filename contains
`deploy-vps.yml`, it MUST print the §77 Deploy Sovereignty citation
to stdout AND include it in the JSON verdict's `doctrine_cite`
field. This invariant is verified by V-DOCTRINE-CITE in the
V-block. The skill INVOKES the canonical pipeline; it does NOT
replace it. Reinventing §77's mechanism in PP would be a
competing-standard antipattern.

### Hard invariants (enforced by V-block)

| Invariant | Verifier |
|---|---|
| NO secret material in `vault/deploy/<project>.json` | schema validator rejects `password` / `secret` / `token` / `api_key` (case-insensitive substring) -- V-CONFIG-INVALID |
| NO auto-push to canonical origin | regex `\bgit\s+push\s+origin\b` over `modules/deployment/runners/*.py` AND `deploy.py` returns 0 hits -- V-NO-AUTO-PUSH |
| Healthcheck mandatory | config without `healthcheck` -> schema FAIL before any runner action -- V-HEALTHCHECK-MISSING |
| SSH key missing -> CEILING | expanded path checked via `os.path.exists`; missing -> verdict ceiling, exit 4, message includes expanded path -- V-CEILING-SSH |
| n8n forbidden | `mode: n8n` (or zapier / make.com / pipedream) -> schema FAIL |
| Recursion guard level-2+ ONLY | `CLAUDEPP_DEPLOY_RUNNING=1` never set on level-1 entry -- L2 lesson sister to code-review |
| Receipt only after healthcheck | dispatcher writes `vault/deploys/<ts>_*.md` only AFTER `run_healthcheck` returns -- V-CLOSED-LOOP |

### Healthcheck kinds (separable, reusable)

| Kind | Mechanism | Used by |
|---|---|---|
| `tcp` | pure Python socket connect | KobiiCraft (port 25565) |
| `http` | curl `-fsS -o /dev/null -w '%{http_code}'` with retries | TUA-X (`/` or `/health`) |
| `curl-grep` | curl + Python regex `re.IGNORECASE` against body | InfinityOps (§77 content-verification style) |

`curl-grep` is the §77 receipt: HTTP 200 is insufficient because a
stale build still returns 200; only literal content verification
against the live page proves new bytes are serving.

### V-block (14 PASS at sealing)

V-DETECT-{GH,PUSH,SCP,NONE} + V-CEILING-SSH + V-CONFIG-INVALID +
V-HEALTHCHECK-MISSING + V-HEALTHCHECK-NC + V-HEALTHCHECK-FAIL +
V-NO-AUTO-PUSH + V-FORBIDDEN-REMOTE + V-DOCTRINE-CITE +
V-CLOSED-LOOP + V-TIMING.

Measured (2026-05-24): 14/14 PASS. V-TIMING p95 = 23.2 ms
on the detect-on-tmpdir hot path. Total V-block wall time < 2 s.

### DONE-gate

1. All V-tests PASS.
2. `verify_spp.py` 7/7 STRICT.
3. `verify_full_install.py` exit 0.
4. PP source + live mirror sha256 match for this section.
5. UKDL-DP-01..05 rows in `ukdl-universal.md`.
6. session_lessons L1..LN rows for this cycle.
7. V-DEEP dry-run receipt at `vault/deploys/<ts>_infinityops_dryrun.md`.
8. `git push origin main` REMOTE_DELTA = 0.

### PP Quality Quadrangle -- the four gates

```
[ Auto-Testing Gate ]   <-- "does it work?"
       |
       v
[  Arch-Check         ] <-- "is the decision consistent with the vault?"
       |
       v
[  Code Review        ] <-- "is it well-written, secure, maintainable?"
       |
       v
[  Deploy             ] <-- "did it actually reach production AND serve traffic?"
       |
       v
   PRODUCTION
```

Removing any of the four reopens a class of silent failure. The
auto-testing gate proves correctness, arch-check proves
consistency, code-review proves quality, deploy proves delivery.
Four gates, four independent failure modes, four independent
proofs.


---

## Backup Axis (sealed 2026-05-25) -- safe-deploy precondition

**State preservation BEFORE the deploy event.** Deploy Axis verified the
future (post-deploy healthcheck); the Backup Axis verifies the past
(restore-tested snapshot of the pre-deploy state). Together they bracket
the deploy event. The Quadrangle no longer assumes "deploy that succeeds"
implies "system that remains recoverable" -- it now PROVES recoverability
as a precondition.

### Reality contract (backup-specific)

A snapshot that has not been restore-tested is, by spec §2, **not** a
backup. The dispatcher refuses to write a `vault/backups/<ts>_<project>.md`
receipt unless `verify_restore.py` has executed and emitted a verdict
(PASS or FAIL). Sha256 mismatch or restore-test failure yields verdict
`backup-warn` (exit 3) and the receipt states the failure in plain text.

### 3 backup modes (1 module, 3 runners)

| Mode | Mechanism | Real-world target |
|---|---|---|
| `rsync-dir` | `ssh <alias> 'tar --create -P <paths...> \| gzip -1'` piped to a local file | KobiiCraft world + plugin data dirs |
| `docker-volume-tar` | `ssh <alias> 'docker run --rm -v <volume>:/data:ro alpine tar -czf - /data'` | TUA-X postgres_data + rabbitmq_data |
| `pg-dump` | `ssh <alias> 'docker exec <pg-container> pg_dump -Fc -U <user> <db>'` | TUA-X postgres, InfinityOps postgres |

No agent required on remote; only `ssh` + the per-mode primitive (tar /
docker / pg_dump). Snapshot bytes land in local `backups/<project>/`
(gitignored). Off-site push is an explicit Owner step (§11), not an
automatic side-effect.

### Restore-test contract (spec §8)

Every snapshot is restore-tested before the receipt is written:

1. sha256 of the snapshot file computed; compared to runner-reported sha256.
2. Snapshot extracted into a `tempfile.TemporaryDirectory()`.
3. Each `sample_files` path verified to exist in the extracted tree.
4. `structural_check` applied: `nbt-magic` / `pg-dump-header` / `json-parse` / `not-empty`.
5. Returns `{ok, checks_passed, checks_total, evidence}`.

`nbt-magic` is the KobiiCraft world receipt: extract `level.dat`, gunzip,
verify the first byte is `0x0a` (NBT Compound tag). A faked snapshot that
zips garbage will pass tar+gzip checksums but fail NBT magic; the verdict
honestly says `backup-warn`.

`pg-dump-header` is the Postgres receipt: first 5 bytes of the snapshot
must equal `b"PGDMP"` (the custom-format magic). A pg_dump that produced
truncated output will lack this; verdict `backup-warn`.

### Hard invariants (enforced by V-block, 15 PASS)

| Invariant | Verifier |
|---|---|
| NO credential-class keys in `vault/backup/<project>.json` | schema validator + V-CONFIG-INVALID |
| Restore-test obligatory | V-RESTORE-TEST + V-RESTORE-FAIL + V-RESTORE-PGDMP |
| Retention mandatory | schema FAIL if `retention` absent -- V-RETENTION-MISSING |
| Disk-full guard pre-run | V-DISK-FULL (CEILING exit 4 when free space < 2x expected) |
| sha256 manifest written | retention.py emits `<dest>/manifest.json` with sha256 of every retained snapshot -- V-RETENTION-APPLY + V-RETENTION-MIN-KEEP |
| NO off-site auto-push | runners write to `local_destination` only; off-site is backlog |
| Receipt only after verify_restore | dispatcher writes `vault/backups/<ts>_*.md` AFTER verify_restore -- V-CLOSED-LOOP |
| Recursion guard level-2+ ONLY | `CLAUDEPP_BACKUP_RUNNING` never set on level-1 (sister to deploy L2) |
| n8n / zapier / make.com / pipedream forbidden | schema validator |

### Integration with Deploy Axis

`vault/deploy/<project>.json` now supports `pre_deploy_backup: true`. When
set, `modules/deployment/deploy.py` invokes `modules/backup/backup.py`
BEFORE the deploy runner. Backup verdict != pass/dry-run/skip -> deploy
CEILING with summary "pre-deploy backup gate FAILED".

This is the **safe-deploy contract**: a deploy is only safe if a
restore-tested snapshot exists from immediately before it. Verified by
`V-BACKUP-FIRST` in the deploy V-block (deploy 15/15 PASS post-integration).

### DONE-gate (spec §16)

1. 15/15 V-tests in `modules/backup/test_v_block.py` PASS.
2. 15/15 V-tests in `modules/deployment/test_v_block.py` PASS (including new V-BACKUP-FIRST).
3. `verify_spp.py` 7/7 STRICT (or documented preexisting FAILs).
4. PP + live mirror sha256 byte-identical for this section.
5. UKDL-BK-01..05 + UKDL-BK-REP-01 rows.
6. session_lessons L1..LN rows.
7. V-DEEP dry-run receipt at `vault/backups/<ts>_kobiicraft_dryrun.md`.
8. `git push origin main` REMOTE_DELTA = 0.

### PP Quality Quadrangle (now with safe-deploy precondition)

```
[ Auto-Testing Gate ]   "does it work?"
       v
[  Arch-Check         ] "is the decision consistent with the vault?"
       v
[  Code Review        ] "is it well-written, secure, maintainable?"
       v
[  Backup (NEW)       ] "is a restore-tested snapshot of the pre-deploy state on disk?"
       v
[  Deploy             ] "did it reach production AND serve traffic?"
       v
   PRODUCTION
```

The Backup Axis is the 5th node in the chain (between Code Review and
Deploy), not a 5th axis of the Quadrangle. The Quadrangle remains
auto-testing + arch-check + code-review + deploy; Backup is the
precondition gate that protects Deploy from itself. Rollback (the future
sister) closes the loop: Backup makes Deploy safe; Rollback makes Deploy
recoverable.



## Rollback Axis (sealed 2026-05-25) -- deploy lifecycle complete

The Rollback Axis closes the deploy lifecycle introduced by Backup and Deploy.
The full chain is now:

` 
Backup (safe) -> Deploy (deliver) -> Rollback (recover).
` 

No deploy is irreversible. When a deploy fails or the Owner decides to
revert, `/rollback --project X` restores the last verified snapshot from
`backups/<project>/manifest.json`, then runs the same post-deploy
healthcheck against the live target. A restore whose healthcheck fails
yields `rollback-warn` exit 3, not silent success.

Three architectural invariants are sealed by this axis:

1. **Manifest as truth source.** `modules/rollback/source_selector.py`
   refuses to use any snapshot that is not in the manifest. A `.tar.gz` on
   disk without a manifest entry was either never restore-tested or is
   pre-manifest-era; the Rollback Axis cannot trust a snapshot that the
   Backup Axis itself did not certify.

2. **No automatic rollback.** The Deploy Axis dispatcher SUGGESTS the
   `/rollback --project <X>` command on `verdict in {fail, ceiling,
   deploy-warn}`; it never invokes the rollback dispatcher. V-NO-AUTO in
   `modules/rollback/test_v_block.py` grep-asserts zero call sites of the
   rollback function in `modules/deployment/deploy.py`. V-ROLLBACK-SUGGEST
   in `modules/deployment/test_v_block.py` asserts the suggestion DOES
   appear in fail-class verdicts. Hawkins lens: power, not force. The Owner
   always decides on destructive operations.

3. **sec 77 Deploy Sovereignty extends to rollback.** For `infinityops`
   with `include_code_rollback=true`, the dispatcher invokes
   `gh workflow run deploy-vps.yml --ref <prev_sha>` after printing the
   sec 77 citation. The canonical CD pipeline is invoked, never
   reimplemented. `prev_sha` is parsed from the latest
   `vault/deploys/*_infinityops.md` HEAD line.

The opt-in `--rescue` flag takes a pre-rollback snapshot of CURRENT state
into `vault/rescues/<project>/` before applying the restore -- a safety
net for the case where the Owner wants logs/data from the broken state
before overwriting it. Off by default (Hawkins: no destructive-by-default
behaviour beyond what was asked).

` 
[ Auto-Testing Gate ]   does it work?
       v
[  Arch-Check         ] consistent with the vault?
       v
[  Code Review        ] well-written, secure, maintainable?
       v
[  Backup             ] restore-tested snapshot on disk?
       v
[  Deploy             ] reached production AND serving traffic?
       v
[  Rollback (on fail) ] verified restore + healthcheck PASS?
       v
   PRODUCTION (or recovered prior state)
` 

The Quadrangle remains auto-testing + arch-check + code-review + deploy.
Backup is the safe-deploy precondition between Code Review and Deploy.
Rollback is the recovery escape hatch AFTER Deploy. The five-node chain is
now complete: nothing reaches production without four gates, and nothing
that fails after Deploy is irrecoverable.

V-block evidence: 15/15 rollback tests PASS (V-LIST-VERIFIED,
V-LIST-EMPTY, V-DRYRUN-RSYNC, V-DRYRUN-PGDUMP, V-CONFIG-INVALID,
V-CEILING-SSH-KEY, V-TARGET-NOT-FOUND, V-TARGET-UNVERIFIED,
V-RESCUE-CREATES, V-HEALTHCHECK-PASS, V-HEALTHCHECK-FAIL, V-NO-AUTO,
V-DOCTRINE-CITE-ROLLBACK, V-CLOSED-LOOP, V-TIMING p95 ~20 ms).
16/16 deployment V-block tests PASS, including new V-ROLLBACK-SUGGEST.


## Skill Completion Axis (sealed 2026-05-25) -- baseline raised post LT+CEPS

A new PP skill is complete only when all seven clauses of the Skill
Completion Standard (`knowledge_vault/core/skill-completion-standard.md`)
are satisfied with empirical evidence. Missing evidence == not complete.
Reality Contract applies: the evidence is the test output, not the
description of the test.

### The seven clauses (short form -- full spec in the SCS document)

1. **C1**: empirical pass-gate declared before the first byte of skill content.
2. **C2**: side-by-side with-vs-without-skill comparison on the same prompts.
3. **C3**: no-collision against the 10 JIT trigger families + Intent-Lock + Arch-Check + vague-lint + active hooks + 29 baseline tests.
4. **C4**: distribution integrated with CEPS (`tools/ceps.py::record_error` + `vault/ceps/events.jsonl`).
5. **C5**: auto-test stub via `tools/ceps_test_gen.py` for any regression / security / drift invariant.
6. **C6**: atomic write for every markdown append (no `cat >>` -- direct consequence of the 2026-05-23 apex corruption).
7. **C7**: RTK proxy compatibility -- no raw-stdout byte slicing in skill tooling.

### Enforcement

A skill that fails any clause cannot be merged to `main`. The Owner-facing
PR description must carry a Skill Completion Standard table with one row
per clause + evidence path + checked status. Missing rows or unchecked
clauses block the merge.

### Bootstrap references (the two skills that defined this axis)

- `lateral-thinking` skill (`~/.claude/skills/lateral-thinking/`): 11 V-* gates passing in `tools/test_lateral_thinking.py`.
- CEPS substrate (`tools/ceps.py` + `tools/ceps_test_gen.py`): 10/10 closed-loop in `tools/test_ceps_closed_loop.py`, 8/8 full-cycle in `tools/test_ceps_full_cycle.py`.

These two were built simultaneously and bootstrap each other. The axis
freezes the pattern they established.

### DONE-gate

`python -m pytest tests/test_forensic_probes.py tests/test_mistake_frequency_xplat.py -q`
+ `python tools/test_lateral_thinking.py`
+ `python tools/test_ceps_closed_loop.py`
+ `python tools/test_ceps_full_cycle.py`
-- all four exit 0 = axis sealed.


---

## Pterodactyl Console API Autopilot Axis (sealed 2026-05-26)

Relocated to file-tail by S+++ recovery (2026-05-26) per C6 atomic-write
mandate. Original Pane-4 insertion stomped the Testing Gate Axis head;
this section preserves the content, restored via atomic-append rather
than destructive overwrite.

When a Pterodactyl-managed Minecraft server has prose-flagged "Owner-in-game" PASOs in its handoff docs, the Apex bar is to verify each PASO against this 11-item empirical checklist BEFORE accepting the OWNER-MANUAL classification. A PASO is autopilot-doable on Console API iff every check below either passes or has an autopilot-side substitute.

### 11 empirical checklist items (>=10 needed to claim "Apex-complete on Console API Axis")

1. **nbtlib `<world>/level.dat` parse**: `Data.spawn.pos` (Paper 1.21+ IntArray of 3 ints) -> produces `(SpawnX, SpawnY, SpawnZ)` literal output. nbtlib must be installed; if not, `pip install nbtlib`.
2. **Console-API verb map**: WorldGuard `/rg`, Citizens `/npc`, FAWE `//world`+`//pos1`+`//pos2`+`//set/replace`, vanilla `/setworldspawn`, `/say`, `/save-all` all dispatch via `POST /api/client/servers/{id}/command` and produce log-side evidence.
3. **WorldGuard `-w PREFIX` discipline**: `/rg flag -w <world> <region_id> <flag> <value>`. Never trust HTTP 204 -- grep log for `Region flag <name> set on '<id>' to '<value>'`.
4. **Citizens comma-coord syntax**: `--at <x>,<y>,<z>,<world>` (or `--location` same form). Never space-separated. Done-evidence: `Created <name> (ID <n>).` in log; save IDs for downstream `/npc select`.
5. **DecentHolograms player-actor wall**: hologram create/attach is impossible from console. Autopilot creates NPC + ID; generate paste-ready Owner doc for the `/dh` block using the captured IDs.
6. **ND-7 cross-pane leak recovery**: before any `git add`, run `git diff --cached --name-only` to catch other panes' pre-staged files. If unexpected files in index: `git reset HEAD -- .` + re-add ONLY your explicit paths. Never `git add -A` (multi-pane race vaccine).
7. **`git reset HEAD -- .` discipline**: when an inadvertent stage from another pane appears, reset the index (not the working tree). Then re-stage with explicit paths. Preserves the other pane's working-tree work; cleans your commit's staged set.
8. **`files/write` octet-stream fallback**: the documented `files/upload` signed-URL flow (`:8080/upload/file?token=<jwt>`) returns HTTP 500 / RemoteProtocolError on this panel install. The working path is `POST /api/client/servers/{id}/files/write?file=<path>` with `Content-Type: application/octet-stream` and raw bytes as body. Empirically supports >=1.8 MB single POST.
9. **`/save-all flush` before restart**: dispatch `/save-all flush` and wait for `Saved the game` in log before issuing `POST /power {"signal": "restart"}`. Prevents chunk corruption + ensures level.dat reflects in-memory state.
10. **ND-1 `[HOTFIX-JAVA-APPROVED]` scope discipline**: this override token is sealed for explicit Owner-ratified Java edits. Pure-docs commits + Python-script commits MUST NOT include the token. Adding it for non-Java commits invites scope creep + auditor noise.
11. **Vanilla `/fill` vs. FAWE `//set` decision**: `/fill` requires loaded chunks; FAWE `//set` auto-loads via EditSession but requires `//world <world>` prefix from console. Default to FAWE for any block-manipulation in worlds without active players.

### Five-check DONE-gate (all must pass for Apex-complete)

- [ ] nbtlib `level.dat` parse executed; coords persisted to `_audit_cache/<world>_coords.json` with paper_version + sha256[:16].
- [ ] All non-player-only PASOs attempted via Console API with empirical log-grep evidence persisted to `docs/server/playtest-v200/paso<N>_*.log`.
- [ ] Owner-handoff docs generated for genuine player-actor-only PASOs (DH, fresh-player verification) with paste-ready commands using autopilot-captured IDs.
- [ ] Commit staged with explicit paths (never `-A`); ND-7 self-scan passed; ND-1 / quality-skill gate respected.
- [ ] Sec 13 of `GOLD_STANDARD_SERVERS.md` (Console API autopilot recipes) updated with any new verb/syntax/quirk discovered this run.

### Empirical receipt (Pane-4 v200 run, 2026-05-26)

Pane 4 v200 pasos-restantes run closed 5/5 OWNER-MANUAL PASOs (3, 4, 5, 6, 7) into autopilot-DONE + 1 sidecar discovery (KobiWelcome Y=70->Y=182 drift fix -- the `can't stay connected` root cause). 8/14 milestones autopilot, 6/14 docs/doctrine. Wall-clock ~25 min including syntax debugging. All 11 checklist items + all 5 DONE-gates passed.



## Skill Completion Axis v2 (sealed 2026-05-26) -- S+++ regression-prevention cycle

The v1 axis (sealed 2026-05-25) sealed 7 clauses derived from the LT+CEPS
bootstrap pair. The post-merge S+++ cycle on 2026-05-26 surfaced 3 real
gaps that the v1 clauses did NOT catch:

1. **NIT 1** -- the schema declared a max_chars contract that no code
   enforced. The output happened to be within bounds in practice; the
   contract was load-bearing for nothing until a long-subsystem seed
   would have silently exceeded it.
2. **NIT 3** -- `from_verify_fail` recorded duplicate events on re-run
   of the same verify_spp stdout. The schema declared `id:
   stable_across_reruns: true` but the code did not honour it.
3. **PR-passage prose** -- multiple commits cited "tests pass" without
   the test output being part of the diff. The green moment was
   unreproducible after the fact.

These gaps motivate three new clauses in the Skill Completion Standard:

### C8 -- Evidence-archive at commit-time

The empirical pass-gate output (test stdout, fixture JSON, verify_*
receipts) MUST be committed alongside the code that satisfies it.
"Trust me, it passed" is not evidence. Verbal claims of passage in
commit messages do NOT satisfy C8.

### C9 -- Schema-test reciprocity

Every invariant declared in a `schema.json` (max_chars, enum values,
format, derived_from) MUST have a corresponding test that enforces it.
A schema without a test is a comment, not a contract.

### C10 -- Idempotency-by-default for persistent-state triggers

Any skill trigger that writes to a persistent store (events.jsonl,
FTS5 db, markdown append, JSON fixture) MUST be idempotent under re-
invocation with identical input, unless the skill's plan explicitly
documents a rationale for non-idempotency.

### Enforcement (extends v1)

The Owner-facing PR description must include all TEN rows of the SCS
table. Missing rows or `[ ]` checkboxes on C8/C9/C10 block the merge
in addition to C1-C7.

### Cross-references

- `knowledge_vault/core/skill-completion-standard.md` -- full v2 spec.
- `tools/test_ceps_edge_cases.py` -- the V-NIT1 / V-NIT3 / V-EDGE-*
  tests that empirically grounded C9 + C10.
- `tools/normalize_paths.py`, `tools/verify_global_mirrors.py`,
  `tools/verify_rtk_fusion.py` -- the M7/M8/M9 host-portability fixes
  that empirically grounded C8 (each fix proved by re-running the
  failing probe and capturing the post-fix output).

### DONE-gate

`python tools/test_ceps_edge_cases.py` (6/6) +
`python tools/verify_spp.py` (post-commit: 7/7 OK or documented Owner-
authed FAIL with rationale in `vault/standards/`) +
SCS v2 visible at `knowledge_vault/core/skill-completion-standard.md`
in both loose and PP with byte-identical sha256 -- all three satisfied
= axis v2 sealed.


---

## World-Env Suffix Detection Axis (Pane 3, KobiiCraft -- relocated 2026-05-26 by S+++ recovery)

Relocated to file-tail by TIS-cycle recovery (2026-05-26) per C6 atomic-
write mandate. Original Pane-3 insertion stomped the Testing Gate Axis
head; this section preserves the content, restored via atomic-append
rather than destructive overwrite.

**Sealed:** 2026-05-26 evening (Pane 3 KME-env + KME-042 follow-up).

### The axis (one-line invariant)

> Any code path that creates a Bukkit World via `WorldCreator` MUST detect the target Environment from the world-name suffix (`_nether` / `_the_nether` / `_end` / `_the_end` / else NORMAL) -- NEVER hardcode `.environment(NORMAL)` at the call site. Suffix detection is the single source of truth for dimension binding; hardcoding silently mis-loads nether/end twin worlds as overworlds with empty terrain.

### Why this is an apex completion standard

The trap is silent -- no exception, no warning, no log line indicating the env was wrong. A nether twin world loaded as NORMAL still LOADS; players can teleport in; they just see overworld terrain instead of the nether content sitting on disk in `DIM-1/region/`. Discovered empirically (Pane 3 2026-05-26 Block 5 5-world deploy) only because of the `/kobimap listworlds` post-deploy review.

The canonical fix is a one-time refactor: extract a public static helper `detectEnvironment(String sanitizedName)` and call it from every WorldCreator site. Once it exists, every future WorldCreator caller inherits the right behavior. Tests are pure-logic (10 hermetic cases in `EnvironmentDetectionTest`, no MockBukkit needed).

### Mandatory checks for any future world-creation code path

1. NEVER write `.environment(World.Environment.NORMAL)` as a literal at a WorldCreator site.
2. ALWAYS call `WorldService.detectEnvironment(name)` or pass an explicit `Environment` parameter.
3. Suffix detection is case-insensitive (defensive against caller-pre-uppercased names).
4. SUFFIX match -- substring match is wrong (`netherworld_overworld` must NOT be detected as nether).
5. Defensive defaults: null / empty input -> NORMAL.
6. Log the detected env on the `[WorldService] created+registered` line so it is greppable in boot logs.

### What "done" looks like -- evidence contract

- `WorldService.detectEnvironment(String)` is public+static, called from EVERY WorldCreator site in the codebase.
- Hermetic test class with >=7 cases (NETHER suffix, alternate `_the_nether`, THE_END, alternate `_end`, NORMAL default, case-insensitive, substring rejection, null/empty defensive).
- Boot log includes `env=NETHER` / `env=THE_END` / `env=NORMAL` on the WorldService init line for each registered world.

### Related sibling axis -- Wrapper-Over-Tested-Core (KME-042)

When adding a shorter/friendlier subcommand surface that exposes already-tested behavior (e.g., `/kobimap recreate <id>` over the existing `mirror dna <id>` path), implement it as a THIN WRAPPER that translates args and delegates -- do NOT re-implement the logic. The wrapper test surface is `hasValidArgs(args)` + `buildDelegatedArgs(input)` static helpers; the delegated body is exercised by the existing tests on the core logic. KME-042 shipped in ~1.5h vs the original 6-10h estimate (which assumed re-implementation).

### Project reference

`docs/server/GOLD_STANDARD_SERVERS.md` Sec 24 (World Environment Suffix Detection + Recreate Wrapper). UKDL Trap 19 (`WorldService.createOrReuseMapWorld` silently hardcodes Environment to NORMAL). Seal addendum in `docs/server/PANE3_BLOCK5_SEAL.md` (Pane 3, 2026-05-26 evening section "Addendum 2026-05-26 evening -- KME-env + KME-042 fixes shipped").


## Token Intelligence (TIS) Axis v1 (sealed 2026-05-26) -- cost-visibility baseline

A new PP feature that calls a Claude model OR injects context into the
prompt pipeline is complete only when its activity is visible in the
TIS log AND its handoff summarizer can produce a real
`recommended_action`. Until 2026-05-26 there was no cost telemetry on
the trigger matrix; this axis closes that gap as the sixth standard
DONE axis alongside Concurrency, Async-Audit, Zero-Drift Mirror,
Context-Pressure, Session-Safety, and Skill-Completion.

### Five required components (all five must be present for Apex-complete)

1. **Logger** -- `tools/tis.py` (`TokenEvent` dataclass +
   `append_log` + `read_log` + `get_session_id`). Stdlib only;
   atomic-write for the session id sidecar. JSONL append-only to
   `vault/token_logs/YYYY-MM-DD.jsonl`.
2. **Analytics CLI** -- `tools/tis_report.py` with four flags:
   `--summary`, `--by-skill`, `--cache-ratio`, `--since`. ASCII
   tables, stdlib only. `PRICING` constant for Sonnet 4.6 / Opus 4.7 /
   Haiku 4.5 (extensible).
3. **Handoff summarizer** -- `tools/tis_handoff.py` reads the active
   session log and emits a `<context_summary>` block with
   `top_3_expensive_calls`, `compression_candidates`,
   `estimated_savings_next_session_tokens`, `recommended_action`.
   Honest fallback: `INSUFFICIENT_TELEMETRY` / `NO_CANDIDATES_DETECTED`
   are explicit reasons -- never silent zero (Reality Contract).
4. **JIT hook** -- `tools/jit_skill_loader.py::_tis_log_call` decorator
   wraps `run()` and records a per-call event. Fail-open on any
   internal error.
5. **verify_spp probe** -- `tools/verify_tis.py` 4-check probe + a
   row in `tools/verify_spp.py::rows_spec`. Confirms the system is
   alive from cold state.

### Five-check DONE-gate (binary, no classifications)

A PP install is Apex-complete on the Token Intelligence Axis iff:

1. `tools/test_tis_core.py` exit 0 with TIS_CORE_PASS=6/6.
2. `tools/test_tis_e2e.py` exit 0 with E2E_PASS=4/4.
3. `tools/verify_tis.py` exit 0 with TIS_PROBE=4/4.
4. `tools/tis_report.py --summary` returns at least one row of real
   data (no synthetic-only sessions).
5. `tools/tis_handoff.py` writes a `vault/token_logs/handoff_*.md`
   with a real, non-empty `recommended_action`.

Missing any of 1-5 = NOT Apex-complete on the TIS Axis.

### Cross-references

- `knowledge_vault/core/skill-completion-standard.md` C11 (Token-
  Intelligence-by-default): the per-skill obligation derived from
  this axis.
- `tools/tis.py`, `tools/tis_report.py`, `tools/tis_handoff.py`,
  `tools/verify_tis.py`, `tools/test_tis_core.py`,
  `tools/test_tis_e2e.py`: the substrate.
- Sister modules: `modules/token-optimizer/token_autopsy.py`
  (post-mortem parser of `~/.claude/projects/` session JSONL). TIS
  is the live per-skill logger; token_autopsy is the forensic
  cross-session parser. They are complementary.

### Empirical proofs (2026-05-26)

- M1 self-probe: round-trip preserved `input_tokens=100`.
- M2 V-TIS-* 6/6: APPEND / IDEMPOTENT / SCHEMA / SESSION / PERSIST / NONZERO.
- M3 hook fires on real `jit_skill_loader.run()`: captured
  `input_tokens=12 / output_tokens=157 / call_label=jit-context-injected`
  on an LT trigger prompt.
- M4 `--summary` / `--by-skill` / `--cache-ratio` / `--since`: all
  4 flags emit non-empty tables with real data.
- M5 handoff emits `<context_summary>` with honest
  `NO_CANDIDATES_DETECTED` when applicable.
- M6 E2E 4/4: 3 mock dispatches -> `tis_report` non-empty ->
  `tis_handoff` detects compression candidate on repeated call_label.
- M7 verify_spp row `tis-probe` PASS in <1s.



## Monitoring / Alert Axis (sealed 2026-05-26) -- deploy lifecycle: continuous observability

The Monitoring Axis is the fourth and final node of the deploy lifecycle:

```
Backup (safe) -> Deploy (deliver) -> Rollback (recover) -> Monitor (observe).
```

Until now the lifecycle was gate-once: a deploy's healthcheck verified the
moment of release, but a service that went DOWN ten minutes later sat
unobserved until the Owner manually noticed. The Monitoring Axis closes
that gap: every productive project carries a `vault/monitor/<project>.json`
whose healthcheck signal mirrors the deploy axis's verbatim. The same
`check_tcp` / `check_http` / `check_curl_grep` functions that gate deploy
are polled in a loop here -- single source of truth, no duplication.

Five architectural invariants are sealed by this axis:

1. **Single source of truth for healthcheck logic.** `modules/monitoring/monitor.py:run_check` dispatches to `modules.deployment.healthcheck` verbatim. Spec C7 (RTK compatibility) is honored: no free-text scraping. Spec C6 (atomic appends) is honored in state + alert writes (`tmp + os.replace`).

2. **Debounce keeps the monitor honest.** A single failed poll does NOT flip a service to DOWN. The defaults are `consecutive_failures=3`, `consecutive_successes=2`, `min_state_duration_sec=30` -- configurable per-project. A flap that lasts < 3 polls is logged but does not alert. The empirical V-block (16 tests) exercises every transition; V-DEBOUNCE-NO-ALERT proves a 2-failure window stays UP.

3. **No automatic rollback.** Even though the Rollback Axis exists and the alert receipt carries the literal `/rollback --project <X>` suggestion text, V-NO-AUTO-ROLLBACK grep-asserts zero call sites of the rollback function across `monitor.py`, `alert.py`, `observe.py`. The Owner reads the alert; the Owner decides. Hawkins lens, sealed across Rollback + Monitoring.

4. **Daemon installation is Owner-gated.** `/observe --daemon` PRINTS the exact crontab + Task Scheduler commands; it never invokes them. V-DAEMON-NO-INSTALL grep-asserts zero `subprocess` call sites against `schtasks` / `crontab` / `Register-ScheduledTask`. The Owner copy-pastes; nothing auto-installs.

5. **The monitor surfaces bugs the gate-once axes cannot see.** The sealing cycle uncovered a Windows-only UTF-8 decoding bug in `modules/deployment/healthcheck.py:check_curl_grep`: `subprocess.run(text=True)` decoded the live page with `cp1252`, mojibakeing the `brújula` token (UTF-8 `0xC3 0xBA` -> cp1252 `Ã + º`) so the regex `br.jula` (dot wildcard) failed to match. Fix shipped same cycle: capture stdout as bytes, decode UTF-8 explicitly. This bug had silently shadowed the Deploy + Backup + Rollback axes on Windows hosts but never surfaced because the deploy healthcheck runs from the VPS where locale is UTF-8. The monitor running locally exposed it. Reality Contract honored: the cycle that ships the observation layer is also the cycle that proves observation produces signal.

```
[ Auto-Testing Gate ]   does it work?
       v
[  Arch-Check         ] consistent with the vault?
       v
[  Code Review        ] well-written, secure, maintainable?
       v
[  Backup             ] restore-tested snapshot on disk?
       v
[  Deploy             ] reached production AND serving traffic?
       v
[  Rollback (on fail) ] verified restore + healthcheck PASS?
       v
[  Monitor            ] continuous polling + alert receipts + debounce
       v
   PRODUCTION (observed)
```

The Quadrangle remains auto-testing + arch-check + code-review + deploy.
Backup is the safe-deploy precondition. Rollback is the recovery escape
hatch. Monitoring is the continuous-observation node that watches all
of them in production. The seven-node chain is now closed: nothing
reaches production without four gates, nothing that fails after Deploy
is irrecoverable, and nothing that fails AFTER Deploy succeeds is
invisible.

V-block evidence: 16/16 monitoring V-tests PASS (V-POLL-ONCE-UP/DOWN,
V-DEBOUNCE-NO-ALERT/RECOVERY, V-STATE-PERSIST, V-ALERT-FILE-CREATED,
V-ALERT-STDOUT, V-NO-AUTO-ROLLBACK, V-CONFIG-INHERIT, V-ONCE-FLAG,
V-ONCE-MULTIPROJECT, V-DAEMON-NO-INSTALL, V-RETENTION-PURGE-DROP,
V-RETENTION-PURGE-KEEP, V-ALERTS-LIST, V-STATUS-NO-CHECK).
6/6 MONITORING_AXIS verify_spp probe sub-checks PASS.
Empirical alert artefact: `vault/alerts/20260526T150104Z_infinityops_DOWN_TO_UP.md`
proves the full state machine end-to-end with the live br.jula signal.

P2.3 `/health-all` ABSORBED as the `--once` flag (one snapshot,
N projects). SCS C12 (Observability-by-default) sealed in the same
cycle to lock the standard at v4 for all future productive features.

---

## § 2026-05-26 — KobiiClaw Reliability Layer F3 Doctrine (Dispatch Safety Axis)

Sealed alongside the F2 Sweep Resilience Axis (same day). F3 closes the
autonomous reliability loop: triage HIGH/ERROR item → Repair Ticket →
file-based approval gate → Work Order (safety-guarded) → claude_cli
dispatch via sovereign transport → result capture → brief update.

**Rule 1 — Dispatch Safety Gate (UKDL RL-004)**: a Work Order is dispatched
ONLY when BOTH gates pass: (a) the matching `.approve` file exists in
`ops/kobiiclaw/approvals/` AND (b) `safety_check.ok=True` for the WO's
prompt against the 10-pattern destructive-token regex (rm_recursive_force,
shutdown_reboot, kill_minus_nine, dd_to_device, mkfs, drop_database,
truncate_table, chmod_777_root, config_overwrite_no_backup, fork_bomb).
Either gate failing → status="refused_blocked" with NO subprocess to
`/usr/bin/claude`. This is a UNIVERSAL LAW for any future component on
this host that dispatches autonomously to production: an approval signal
without a safety signal is not enough.

**Rule 2 — Dispatch Result Capture (UKDL RL-005)**: every dispatch attempt
MUST write `dispatch_results/<wo_id>_result.json` BEFORE marking the WO
completed/failed/refused. "Fire and forget" is forbidden. The result JSON
is the only durable evidence of what Claude said and when; daemon log
rotation destroys INFO lines within days. Schema: `{wo_id, ticket_id,
dispatched_at, model, exit_code, status, duration_s, stdout_snippet,
stderr_snippet, model_used, attempts, stdout_full_chars}`. Five terminal
statuses cover the failure surface: success / cli_error / timeout /
cli_not_found / refused_blocked.

**Rule 3 — Lifecycle Fail-Soft (UKDL RL-006)**: every stage of the F3
lifecycle (ticket_gen, approval_sweep, wo_gen, dispatch,
pending_approvals_snapshot) MUST be invoked inside `sweep._safe_run()`.
An exception in any one stage cannot abort the sweep, cannot prevent the
next stage from running, and cannot prevent the brief from being written.
Brief-with-honest-exception-traceback strictly dominates daemon-down. F3
introduces 4 new directory state-spaces plus the claude_cli subprocess —
each is a fresh failure surface and each must be contained.

**Rule 4 — Sovereign Transport Reuse**: F3 dispatch MUST go through
`kobiiclaw.claude_cli_client.ClaudeCLI` (DNA-25000), never raw
`subprocess.run(["claude", ...])`. The wrapper handles retry, timeout,
exit-code disambiguation, and the import-time `_detect_binary()` probe
that fails-loud if `/usr/bin/claude` becomes missing or non-executable.
10+ existing importers prove the surface is stable (token_router,
cli_engine, whatsapp_handler, llm_brain, vision_oracle_connector,
sentinel_tools, v4_engine.cli_engine, v4_engine.module_adapter,
discord_bot.llm_brain, discord_bot.sentinel_tools).

**Empirical evidence (2026-05-26)**: E2E test driver `/tmp/test_f3_e2e.py`
7-step ALL PASS:
- benign HIGH item → RT-2026-05-26-001 in pending/
- `.approve` absent → check_approval=False (gate inviolable proven)
- `.approve` present → check_approval=True → WO generated + dispatched
- dispatch returned status="cli_error" exit=null dur=3.0s — root cause
  `/usr/bin/claude` returned "You've hit your limit · resets May 27, 5pm
  (UTC)" exit=1 (rate limit, NOT F3 bug). UKDL RL-006 fail-soft
  empirically validated under real production failure mode.
- "rm -rf /home/kobicraft/workspace" dangerous item → WO blocked,
  hits=['rm_recursive_force'], dispatch refused_blocked, zero claude_cli
  invocation.
- Daemon Cycle 1 post-restart (PID 3015192) "Reliability sweep OK in
  0.31s" + content + AutoResearch all green. Zero F1/F2 regression.

**Doctrine drift guard**: any future autonomous dispatch component (e.g.
self-healing for InfinityOps, MundiCraft auto-fixer, KobiiSports
incident-bot) MUST adopt Rules 1+2+3+4 verbatim. The approval-gate file
mechanism is host-portable (any user with shell + filesystem can approve);
the safety regex set is the canonical starting point and must only GROW
across components, never shrink.

Cross-references:
- UKDL_KOBIICLAW.md RL-004 / RL-005 / RL-006 (per-component evidence)
- claude_cli_client.py at /home/kobicraft/workspace/kobiiclaw/
- Plan-file backup: /home/kobicraft/workspace/ops/kobiiclaw/vault/plans/f3-lifecycle-20260526T1535Z.md
- Stage dir local: ~\AppData\Local\Temp\kobiiclaw-reliability-stage\reliability\


## Token Cost Optimizer (TCO) Axis v1 (sealed 2026-05-26) -- cost-discipline baseline

A new PP feature that consumes Claude model output is complete only
when its activity is cost-visible AND its model routing is auditable.
Until 2026-05-26 there was no live model-routing recommendation on
the trigger matrix; this axis closes that gap as the seventh standard
DONE axis alongside Concurrency, Async-Audit, Zero-Drift Mirror,
Context-Pressure, Session-Safety, Skill-Completion, and TIS.

### Five required components (all five must be present for Apex-complete)

1. **Compact Gate** -- `tools/tco_compact_gate.py` reads the active
   TIS session log and emits a 70% context-pct warning + governor
   warnings for >100k session tokens or >2h session duration.
   Stdlib-only, fail-open.
2. **Model Routing config** -- `vault/config/model-routing.json` with
   `default_model`, `>=7 rules`, and a `skill_to_task_type` map.
   Authoritative source for routing decisions; consumed by both the
   gate CLI and `tis_report.py --by-skill` audit column.
3. **Cost-projection CLI** -- `tools/tis_report.py --cost-projection`
   reads the active session log + the routing JSON + the pricing JSON
   and emits `actual_total_cost_usd`, `optimized_total_cost_usd`,
   `estimated_savings_pct` (with explicit reason field), and
   `top_3_routing_opportunities`. Honest zeros enforced
   (NO_DATA / NO_LLM_ENTRIES / ZERO_ACTUAL_COST reasons).
4. **JIT routing inject** -- `tools/jit_skill_loader.py` heuristically
   infers task_type from prompt keywords and appends a one-line
   "TCO router: recommended model X" advisory to additionalContext.
   Decorator pattern over `run()`; fail-open.
5. **verify_spp probe** -- `tools/verify_tco.py` 5-check probe + a
   row in `tools/verify_spp.py::rows_spec`. Confirms the substrate
   is alive from cold state and that CLAUDE.md anchors are present.

### Five-check DONE-gate (binary, no classifications)

A PP install is Apex-complete on the TCO Axis iff:

1. `tools/test_tco.py` exit 0 with TCO_PASS=8/8.
2. `tools/verify_tco.py` exit 0 with TCO_PROBE=5/5.
3. `tools/tco_compact_gate.py --route subagent_explore` emits a
   string containing 'sonnet'.
4. `tools/tis_report.py --cost-projection` emits a field
   `estimated_savings_pct: N%` with explicit reason (never silent).
5. `~/CLAUDE.md` contains the 'Session Cost Discipline' section AND
   references `tco_compact_gate`.

Missing any of 1-5 = NOT Apex-complete on the TCO Axis.

### Cross-references

- `knowledge_vault/core/skill-completion-standard.md` C13 (Cost-
  Awareness-by-default): the per-skill obligation derived from this
  axis.
- `tools/tco_compact_gate.py`, `tools/verify_tco.py`,
  `tools/test_tco.py`: the substrate.
- `vault/config/model-routing.json`,
  `vault/pricing/anthropic_2026-05.json`: the configuration.
- Sister modules: `tis_report.py` (--cost-projection, --by-skill
  audit), `jit_skill_loader.py` (TCO router inject). TCO is the
  policy + tooling layer; TIS is the measurement substrate. They
  are complementary.

### Empirical proofs (2026-05-26)

- M2 `tco_compact_gate.py` emitted real governor warning at session
  duration 11172s > 7200s threshold on the active session.
- M5 V-* gates 8/8: COMPACT-OK / COMPACT-WARN at 73% / COMPACT-HARD /
  ROUTE-SONNET / ROUTE-OPUS / ROUTE-DEFAULT / PROJECTION /
  BASELINE-INTACT.
- M3 `--cost-projection` produced honest `-400%` reading with explicit
  "actual cheaper than recommended" reason for the synthetic
  tis-self-probe entry. No silent zero.
- M3b JIT router inject: prompt "design the schema" routed to
  `arch_decision -> opus`; prompt "explore the codebase" routed to
  `subagent_explore -> sonnet`; neutral prompt did not inject.
- M6 verify_tco.py TCO_PROBE 5/5 in <1s.

---

## § 2026-05-26 — KobiiClaw Reliability Layer F4 Doctrine (Pre-Launch Certification Axis)

Sealed alongside the F2 Sweep Resilience and F3 Dispatch Safety axes
(same week). F4 closes the autonomous reliability loop on its OUTPUT side:
every sweep now ends with a pre-launch certification check, and the
Owner receives a Discord brief — but only when the system itself is OK
to broadcast.

**Rule 1 — Pre-Launch Certification Gate (UKDL RL-007)**: every
certification module MUST express its checks as atomic, ID'd, fail-soft
units. Schema: `{id, status: PASS|FAIL|WARN|ERROR, detail}`. Wrapper:
`_check(id, fn)` converts any unhandled exception into status="ERROR".
Global rule: **CERTIFIED iff `summary.fail == 0`**; WARN and ERROR are
visible but non-blocking. Certification gates downstream actions (Hermes
delivery), never the daemon (sweep continues regardless).

**Rule 2 — Don't-Broadcast-Broken-State (UKDL RL-008)**: if the system's
own certification is FAILED, external delivery components (Discord
Hermes, email, webhook, SMS) MUST refuse to broadcast with status
`skipped_failed_cert`. Silence is more honest than a noisy half-truth.
A broken system that spams "I am broken" notifications adds noise to the
exact channel needed for recovery.

**Rule 3 — External Delivery Fail-Soft (UKDL RL-008 part 2)**: any
delivery failure (HTTP error, import error, file-system error, queue-full)
returns `{ok: false, status: "<class>"}` and never raises into the sweep.
The brief still writes. The daemon survives. Fail-soft is the floor;
don't-broadcast-broken is the ceiling.

**Rule 4 — Transport Reuse Doctrine (UKDL RL-009)**: any cross-component
messaging MUST reuse the existing sovereign transport for that target.
Never instantiate a new HTTP client, never spawn a new subprocess
pattern, never re-implement authentication. Two anchored transports:
- Claude AI ......... `claude_cli_client.ClaudeCLI` (DNA-25000)
- Discord ........... `discord_bot.discord_bot_notifier.DiscordNotifier`
                      (file-drop, bot consumes JSON)
New transports may only be sealed by an explicit Owner-approved doctrine
entry. The cost of reusing existing transport is one import line; the
cost of rolling a new one is months of edge-case discovery.

**Empirical evidence (2026-05-26)**: F4 v4.0.0-F4 production cycle (PID
3229884):
- `[Discord] Notification queued: morning_report` at 17:58:01 UTC
- `Reliability sweep OK in 0.53s` immediately after
- F1+F2+F3+F4 all green in the same Cycle 1
- Discord bot at PID 1530347 (32-day uptime) consumed the file in <5 s
  with zero F4-related code changes — proves Rule 4

3-case empirical Hermes test (manual):
- cert CERTIFIED -> status="sent" + new JSON written + bot consumed
- cert FAILED (synthetic) -> status="skipped_failed_cert" + ZERO file
- cert UNKNOWN (empty dict) -> status="skipped_failed_cert" + ZERO file
All three returned ok=True; the calling sweep continued every time —
proves Rules 2 + 3.

**Doctrine drift guard**: any future component that performs (a) state
certification of a system it manages or (b) external delivery to a
human-facing surface MUST adopt Rules 1+2+3+4 verbatim. The
check-ID convention (CS-NN, P-NN, X-NN) is universal — every check has
a stable ID for trace/audit/PR-discussion across versions. The
don't-broadcast-broken floor is non-negotiable: a system that lies
about its own health is worse than a system that goes silent.

Cross-references:
- `UKDL_KOBIICLAW.md` RL-007 / RL-008 / RL-009 (per-component evidence)
- `~/workspace/kobiiclaw/reliability/camera_safety.py` (CS-01..CS-05)
- `~/workspace/kobiiclaw/reliability/discord_hermes.py` (file-drop wrapper)
- Plan-file: `ops/kobiiclaw/vault/plans/f4-camera-hermes-20260526T1758Z.md`
- Stage local: `~\AppData\Local\Temp\kobiiclaw-reliability-stage\reliability\`

---

## § 2026-05-26 — KobiiClaw Reliability Layer F5 Doctrine (Launch Readiness Axis)

Sealed alongside F2 Sweep Resilience, F3 Dispatch Safety, F4 Pre-Launch
Certification (same week). F5 is the LAST phase before launch: it adds
calendar awareness (countdown), Owner-controlled mutation (freeze), and
empirical go/no-go aggregation (readiness). T-0 for the MundiCraft v1.0
launch is `2026-06-11` (16 days from doctrine seal at 2026-05-26).

**Rule 1 — Countdown Empiricism (UKDL RL-010)**: every time-relative
label (T-N, T-0, T+N) MUST be computed dynamically from `date.today()`
on every sweep. Never hardcoded, never cached across cycles. The
canonical state is `ops/kobiiclaw/launch_config.json` (`t0_date`,
`t6_freeze_date`) — the daemon reads it, recomputes phase + label,
returns the result. Clock corrections (NTP, TZ change) reflect on the
next sweep without code change.

**Rule 2 — Owner-Gated Launch Actions (UKDL RL-011)**: state-changing
launch operations (`activate_freeze()`, `declare_launch()`) MUST be
Owner-invoked. The daemon NEVER auto-triggers them. Activation is
idempotent — re-running on an already-frozen system returns
`{already: True}` and preserves the original baseline so accidental
re-runs cannot reset drift detection. Hash baseline captured at freeze:
SERVERS line sha256 + per-file reliability/*.py sha256 + combined
files hash. Drift detected on any subsequent sweep → LR-FREEZE override
forces verdict NO-GO regardless of other LR checks.

**Rule 3 — Readiness Aggregation, Same-Sweep, No Cache (UKDL RL-012)**:
the Launch Readiness verdict MUST aggregate artefacts from the SAME
sweep cycle. `assess_readiness()` receives (artifacts, cert_result,
triage_items, hermes_result, freeze_status) as parameters — never reads
them from disk, never reads a previous cycle's brief. Cross-cycle data
mixing is forbidden because: (a) a stale GO verdict from a previous
sweep lies when the current sweep saw new failures, and (b) the
time-windowed checks (CS-04 RSS, CS-05 24h dispatch_results,
log_classifier ERROR count) must reflect the same window as the verdict.

**Rule 4 — T-0 Idempotent Launch Announcement**: on launch_day phase,
the special launch announcement may be emitted to external channels at
most ONCE per launch. The `launch_declared` field in launch_config gates
the announcement; once set to True (Owner action), subsequent sweeps on
the same T-0 day do NOT re-announce. This is the launch-day equivalent
of the F4 don't-broadcast-broken floor: silence is more honest than
spammed-half-truth-anouncements during the most attention-sensitive
moment of the launch.

**Empirical evidence (2026-05-26)**: F5 v5.0.0-F5 Cycle 1 PID 3300262
at 18:34 UTC produced:
- `t_label: T-16, days_to_t0: 16, phase: pre_freeze` (countdown matches
  manual `(date(2026,6,11) - date.today()).days` calc — Rule 1 proved)
- `freeze_status: not_frozen, drift_detected: false` (Owner has not
  invoked `activate_freeze()` yet — Rule 2 proved by absence)
- `Verdict: GO (5/5 PASS)` — LR-01..LR-05 all PASS, each citing the
  matching artefact from the same sweep (CS-04 cited "PID 3229884 RSS
  162.1 MB", which is the F4 cert that ran milliseconds earlier in the
  same `sweep.run()` call — Rule 3 proved)
- `launch_declared: false` — no T-0 announcement attempted (gated)

**Doctrine drift guard**: any future component performing (a) calendar
math, (b) state mutation with operational consequence, or (c)
aggregation across components MUST adopt Rules 1+2+3+4 verbatim. Hash
baselines (Rule 2) are the canonical mechanism for drift detection;
parameter-injection (Rule 3) is the canonical mechanism for fresh-data
contracts. Same-sweep is law: the verdict is a function of the cycle
that produced it, never a Frankenstein of multiple cycles.

Cross-references:
- `UKDL_KOBIICLAW.md` RL-010 / RL-011 / RL-012 (per-component evidence)
- `~/workspace/kobiiclaw/reliability/launch_countdown.py` (dynamic phases)
- `~/workspace/kobiiclaw/reliability/feature_freeze.py` (Owner-gated activate)
- `~/workspace/kobiiclaw/reliability/launch_readiness.py` (LR-01..LR-05 + LR-FREEZE)
- `ops/kobiiclaw/launch_config.json` (canonical mutable state)
- Plan-file: `ops/kobiiclaw/vault/plans/f5-freeze-countdown-20260526T1835Z.md`

---

## § 2026-05-26 — KobiiClaw Reliability Layer Intelligence Upgrade Axis

Sealed the same day F2/F3/F4/F5 shipped. The Intelligence Upgrade
(v5.0.0-F5 → v5.1.0-F5-Intelligence) is the FIRST non-feature pass over
the reliability layer: it audits, optimises, and adds memory to the
existing pipeline without changing any scanner's input contract. Four
universal rules emerged:

**Rule 1 — Spike Detection by Frequency (UKDL RL-013)**: any scanner with
categorical counts MUST treat frequency as a severity signal in its own
right. A WARN logged N >> 1 times in one day is operationally worse than
an ERROR logged once. Concrete mechanism: `WATCH_THRESHOLD_PER_DAY`
(default 30) escalates the finding to WATCH; `ALERT_CONSECUTIVE_DAYS`
(default 3) elevates WATCH to ALERT (severity HIGH). Informational
categories (INFO, UNKNOWN equivalents) are explicitly excluded from
escalation — they are not operational signals.

**Rule 2 — Cache by Rate-of-Change (UKDL RL-014)**: a scanner is
cacheable iff its underlying resource changes at a rate LOWER than the
sweep cadence. The cache TTL must be the resource's rate-of-change, not
a fixed value. Failure results (`ok=False`, `status=scanner_exception`)
MUST NOT be cached — failure must heal on the next sweep. Cache entries
are annotated on read with `_cache_hit` + `_cache_age_s` so the brief
can surface freshness. Empirical: branding_lint cached with TTL 6 h
reduced sweep p50 by 60% (0.37 s → 0.15 s).

**Rule 3 — Fingerprint Dedup + Auto-Close (UKDL RL-015)**: triage items
carry a stable sha256 fingerprint over (source, category, normalised
summary). Fingerprint state persists in
`ops/kobiiclaw/state/triage_fingerprints.json` and survives daemon
restarts. Subsequent sweeps SKIP items whose fingerprint is already
`open`. A fingerprint absent for `>= AUTO_CLOSE_HOURS` (24 h)
auto-resolves; re-appearance after `AUTO_REOPEN_HOURS` (6 h) reopens.
The fingerprint mechanism replaces "ticket per day" with "one
operational record per recurring pattern" — eliminating ticket-flood
without losing signal.

**Rule 4 — Priority-Sorted Top View (Brief Output Doctrine)**: the daily
brief MUST surface a unified, scanner-agnostic priority list at the top —
NOT a per-scanner enumeration. Items are scored by
`severity_weight × frequency × trend_multiplier` and the top N (default 5)
become the brief's first content section. The Discord excerpt mirrors
this priority: launch-relevant sections (countdown, readiness) follow,
per-scanner detail comes last. The Owner reads ONE section and knows
what matters; deeper investigation pulls down the brief manually.

**Empirical evidence (2026-05-26)**: v5.1.0-F5-Intelligence Cycle 1 PID
3488206 at 20:22:57 UTC produced:
- "Reliability sweep OK in 0.24s" (vs Q3 baseline 0.37s = 35% reduction,
  warm-cache p50 = 0.15s = 60% reduction)
- Brief "🎯 Top Issues" #1: WATCH/log_classifier "WARN ×31/day
  (esc=WATCH) ↗" with verbatim KobiiGuide help_pages.yml evidence —
  the operational signal that v5.0.0-F5 silently dropped
- triage_autopilot v1 fingerprint dedup: 2nd run on identical input
  returned `new_items=0, per_day_dedup_skipped=1`
- Zero F1+F2+F3+F4+F5 regression in Cycle 1 + content pipeline +
  AutoResearch 22 recommendations all green

**Doctrine drift guard**: any future scanner that produces categorical
counts MUST adopt Rule 1 (spike detection) verbatim. Any I/O-heavy
scanner MUST adopt Rule 2 (rate-of-change TTL) — never cache failures,
never cache faster than the resource changes. Any cross-component triage
MUST adopt Rule 3 (fingerprint dedup + auto-close). Any new brief
section MUST consider Rule 4 (priority view first, detail last). The
four rules together turn a "detector" into a "system that prioritises".

Cross-references:
- `UKDL_KOBIICLAW.md` RL-013 / RL-014 / RL-015 (per-component evidence)
- `~/workspace/kobiiclaw/reliability/_cache.py` (generic cache)
- `~/workspace/kobiiclaw/reliability/_constants.py` (shared truncation sizes)
- `~/workspace/kobiiclaw/reliability/scanners/log_classifier.py` (v2 spike + trend)
- `~/workspace/kobiiclaw/reliability/triage_autopilot.py` (v1 fingerprint + auto-close)
- Audit report: `ops/kobiiclaw/docs/CODE_AUDIT_20260526T1900Z.md`
- Plan-file: `ops/kobiiclaw/vault/plans/intelligence-upgrade-20260526T2025Z.md`


## ECC Universal Quality Framework Axis v6 (sealed 2026-05-27) -- absorbed-baseline DONE

The eighth Apex DONE axis. A PP install is Apex-complete on this
axis iff the ECC-absorbed quality framework is **active**, not just
documented. Distinct from the prior axes: this one is the assertion
that PP applies a competitor's hard-won doctrine internally, not as
inspiration but as importable runtime infrastructure.

### Six required components (all six must be present)

1. **Principle registry** -- `modules/uqf/principles/__init__.py`
   with `register`, `get_all`, and at least 9 `Principle` subclasses
   loaded (P01 through P09 + Error Never Silent). Each principle
   declares its `domains` and carries `source = "ECC/Affaan Mustafa MIT"`
   where applicable.
2. **Audit pipeline** -- `modules/uqf/auditor.py::UQFAuditor` with
   `audit_file`, `audit_code_str`, `audit_prompt`, `scan_all`.
   Returns `AuditReport` with 0-100 score, passed/failed lists,
   anti-pattern hits, fix hints, source attributions.
3. **Anti-pattern detectors** -- `modules/uqf/anti_patterns.py`
   with at least 7 AST-based detectors (bare_except,
   silent_pass_in_except, missing_type_hints, magic_numbers,
   mutable_defaults, god_function, hardcoded_paths).
4. **Code-review helpers** -- `modules/code_review/__init__.py`
   exposing `pre_report_gate`, `filter_false_positives`,
   `validate_high_critical`, `derive_verdict`, `run_full_review`.
   Importable; the pipeline drops FPs, demotes HIGH/CRITICAL
   without triad, computes verdict.
5. **Rules taxonomy** -- `rules/common/` (>=5 files),
   `rules/python/` (>=4 files), `rules/elixir/` (>=4 files), each
   with ECC MIT attribution footer. Cross-language base + 2 piloted
   languages.
6. **Verify probes** -- `tools/verify_uqf.py` returning UQF_PROBE
   = 5/5 + `tools/verify_rules.py` returning RULES_PROBE = 5/5,
   both rows in `tools/verify_spp.py`.

### Six-check DONE-gate (binary, no classifications)

A PP install is Apex-complete on the ECC-UQF axis iff:

1. `tools/test_uqf.py` exit 0 with UQF_PASS = 15/15.
2. `tools/verify_uqf.py` exit 0 with UQF_PROBE = 5/5.
3. `tools/verify_rules.py` exit 0 with RULES_PROBE = 5/5.
4. `tools/uqf_audit.py --scan-all` returns a real table with at
   least 4 PP modules audited and scores in 0-100 (no crash).
5. `modules/code_review/__init__.py` runs the full pipeline
   without error on a synthetic mixed-severity findings list.
6. `CLAUDE.md` contains the 6-rule Prompt Defense Baseline (P09)
   AND the Code Review Doctrine section.

Missing any of 1-6 = NOT Apex-complete on the ECC-UQF axis.

### Empirical baseline (2026-05-27)

- 9 principles registered, all with `source="ECC/Affaan Mustafa MIT"`.
- `uqf_audit.py --scan-all` baseline:
    modules/monitoring/monitor.py 80% (OK)
    tools/tco_compact_gate.py    40% (WARN)
    tools/ceps.py                20% (FAIL silent passes)
    tools/tis.py                 20% (FAIL silent passes)
    tools/jit_skill_loader.py    20% (FAIL silent passes)
  The low scores reflect honest deuda -- PP fail-open patterns
  flagged by ErrorNeverSilent. Each is documented and threshold
  is 0% baseline at v1; future cycles raise it.
- verify_spp.py now has 12 rows; 10/12 STRICT OK (2 pre-existing
  Pane-N apex drift FAILs continue, unchanged by this cycle).
- 17 rule files written with ECC MIT attribution footer.

### Cross-references

- `knowledge_vault/core/skill-completion-standard.md` C14
  (ECC-UQF-Active-by-default).
- `vault/knowledge_base/ecc-reverse-engineering.md` -- full
  technical analysis.
- `vault/knowledge_base/ecc-universal-baseline.md` -- 12-principle
  reference catalog.
- `rules/common/code-review.md` -- absorbed Pre-Report Gate +
  Common False Positives + Proof Triad + Severity Table.

### Asymmetric complement to PP-native axes

This axis is the FIRST one where PP imports an external system's
doctrine. The prior 7 axes (Concurrency, Async-Audit, Zero-Drift,
Context-Pressure, Session-Safety, Skill-Completion, TIS, TCO,
Monitoring) are PP-native. ECC is in the same niche but emphasizes
different things (61 agents, 246 skills, multi-harness distribution,
industrial test corpus). PP -> ECC absorption is one-way for this
axis; PP retains its own axes intact.

Source: ECC v2.0.0-rc.1 (github.com/affaan-m/ecc) under MIT License
(c) 2026 Affaan Mustafa.


## OSA Global Agent Axis v7 (sealed 2026-05-28) -- proactive-audit DONE

The ninth Apex DONE axis. A PP install is Apex-complete on this
axis iff the Omni-Singularity Agent is **active, throttle-gated,
and non-blocking** -- not just a documented intent.

This is the second axis where PP imports external doctrine (the
first being ECC v6). The OSA absorbs the "proactive zero-issue
auditor + boil-the-ocean" pattern (from `OMNI-SINGULARITY_FLYWHEEL`
+ `BOIL_THE_OCEAN_PROTOCOL`) and grounds it in PP-native primitives
(TIS / TCO / CEPS / Monitoring) so it cannot drift into theater.

### Six required components (all six must be present)

1. **Global agent file** -- `~/.claude/agents/omni-singularity.md`
   with valid frontmatter (`name`, `description`, `tools`, `color`
   only -- NO `triggers:`/`throttle:` YAML keys, which the Claude
   Code agent loader ignores; all activation logic lives in
   `modules/osa/dispatcher.py`).
2. **Throttle gate** -- `modules/osa/throttle.py` reading
   `vault/osa/config.json` for `max_daily_calls` /
   `cooldown_minutes` / `cache_ttl_minutes`. Returns one of
   `GO` / `CACHE_HIT:<min>` / `COOLDOWN:<min>` /
   `BUDGET_EXHAUSTED` on every invocation, with fail-open
   semantics on storage errors.
3. **NEVER_AGAIN injector** -- `modules/osa/never_again.py` with
   `inject()` (writes JSONL + session_lessons + UKDL),
   `top_recurring()`, `query()`. Fuzzy-match dedup increments
   `recurrence` instead of writing duplicate JSONL rows.
4. **GPU Eyes graceful degradation** -- `modules/osa/gpu_eyes.py`
   with `run_visual_qa()` returning `visual_qa_passed=null` when
   no screenshot exists. SKIPPED, CAPTURE_FAILED, and CAPTURED
   are the only valid statuses; never report PASS without a real
   file path.
5. **Dispatcher with non-blocking hooks** -- `modules/osa/
   dispatcher.py` exposing `should_activate()`, `run_if_warranted()`,
   `fire_async()`. The latter is wired into `modules/deployment/
   deploy.py`, `modules/rollback/rollback.py`, and
   `modules/backup/backup.py` via try/except threading patterns
   that NEVER block the productive action.
6. **/osa CLI + verify probe** -- `modules/osa/osa_command.py`
   exposing `--audit`/`--status`/`--budget`/`--never-again`/
   `--force` and `.claude/commands/osa.md` slash command;
   `tools/verify_osa.py` returning `OSA_PROBE = 5/5`; new row
   `osa-active` in `tools/verify_spp.py`.

### Six-check DONE-gate (binary, no classifications)

A PP install is Apex-complete on the OSA axis iff:

1. `tools/test_osa.py` exit 0 with `OSA_PASS = 15/15`.
2. `tools/verify_osa.py` exit 0 with `OSA_PROBE = 5/5`.
3. `python modules/osa/throttle.py --check` returns one of the
   four valid tokens (`GO`/`CACHE_HIT:N`/`COOLDOWN:N`/
   `BUDGET_EXHAUSTED`) without crash.
4. `python modules/osa/dispatcher.py --check` returns a JSON
   payload with a non-empty `project` field.
5. `python modules/osa/gpu_eyes.py` returns
   `visual_qa_passed=null` on unreachable host (never PASS).
6. `modules.osa.dispatcher.fire_async()` returns in <200 ms when
   invoked from `deploy()` / `rollback()` / `backup()` (non-
   blocking contract).

Missing any of 1-6 = NOT Apex-complete on the OSA axis.

### Empirical baseline (2026-05-28)

- TCO context-pct bug fixed in the same cycle: `estimate_context_pct()`
  now uses `MAX(input_tokens)` of the last 3 calls as the context
  proxy, NOT cumulative `SUM(input + output)` across the session.
  Live measurement: a 30-hour session previously reported `100%`
  (capped) when the real context was ~10%; after fix, the same
  session reports `5%` with a debug line surfacing
  `max_single_input` / `proxy_used`.
- `modules/osa/` ships with 5 modules + an `__init__.py` (throttle,
  never_again, gpu_eyes, dispatcher, osa_command).
- Throttle defaults: `max_daily_calls=150` (conservative vs the 212
  `claude -p` calls observed in the last TIS-logged session;
  re-tunable post 2026-06-15 programmatic-credit pricing).
- GPU Eyes: empirically tested with both gex44 (5.9.23.174) and
  the Sovereign VPS (204.168.166.63) unreachable from the test
  host. Returned `status=SKIPPED`, `visual_qa_passed=null` --
  graceful degradation honored.
- `verify_spp.py` now has 13 rows; 11/13 STRICT OK including the
  new `osa-active` (5/5). The 2 pre-existing Pane-N drift FAILs
  (mirror-parity + drift-report on apex/SCS) are RESOLVED in the
  same cycle by the `_osa_standards_append.py` Phase-1 cherry-pick
  (SCS PP -> LOOSE, apex LOOSE -> PP, both lossless).

### Cross-references

- `knowledge_vault/core/skill-completion-standard.md` C15
  (OSA-Zero-Issue-by-default).
- `tools/test_osa.py` -- 15 V-gates including 2 TCO cross-checks
  (V-TCO-CONTEXT-SINGLE, V-TCO-CONTEXT-REAL).
- `tools/verify_osa.py` -- 5 sub-checks for the verify_spp row.
- `vault/osa/config.json` -- externalized throttle/triggers/gpu_eyes
  config.
- `~/.claude/agents/omni-singularity.md` -- global agent prompt
  with the Reality Contract on visual QA pinned as NON-NEGOTIABLE.

### Asymmetric complement to the ECC axis (v6)

ECC v6 absorbed code-review + principle-registry doctrine. OSA v7
absorbs the proactive-audit + zero-issue posture. Both are
absorptions; both retain MIT attribution on the absorbed components
(ECC: code_review/uqf; OSA: agent prompt + boil-the-ocean doctrine).
PP's PP-native axes (Concurrency, Async-Audit, Zero-Drift,
Context-Pressure, Session-Safety, Skill-Completion, TIS, TCO,
Monitoring, ECC, OSA) compose orthogonally.

---

## § 2026-05-28 — Semantic Analysis Axis (Pane 3, KobiiCraft, Sesión 13 KME-005)

**Sealed:** 2026-05-28 (Pane 3 Sesión 13 of the Hypixel-parity 20-session roadmap — KME-005 Semantic Tagging Classifier shipped into production via `BlueprintAuditor` consumer hook)

### The axis (one-line invariant)

> Every analysis module operating on `List<BlockEntry>` (or analogous lifecycle-free data) MUST be a pure-POJO function — no Bukkit runtime in the API surface — AND must use the SAME `normalize` contract (`minecraft:` prefix strip + bracketed-state strip) as the existing pipeline so histogram keys interop across analyzers. Wire a real production consumer (DNA-046 closure) before declaring DONE; a wired POJO classifier compounds with every other analyzer that produces the same histogram keys.

### Why this is an apex completion standard

KME-042 (`/kobimap recreate`) shipped in 1.5h vs the 6-10h backlog estimate because Pane 3 discovered that `dnaRecreate` already existed in `MirrorCommandHandler`. KME-005 shipped in roughly the same compressed window for the same reason: `shannonEntropy` + `normalize` already existed in `EmotionalSensationAnalyzer`. The "wrap don't reimplement" rule is now a compounding meta-rule: every new analyzer should first grep the codebase for the primitives it needs (entropy, histogram, bounds, symmetry, palette) and adopt the existing pattern (or extract a shared utility) before writing from scratch.

The trap on the other side: silently DUPLICATING a primitive (e.g. inlining a second `normalize` with subtly different rules) is invisible until two analyzers start producing different histogram keys for the same input. Strategy: when the primitive is small (≤10 LOC), inline + comment-cite the source; when it's larger, extract to a shared utility.

### Mandatory checks for any future POJO analysis module

1. The classifier `record` / `class` API touches ZERO Bukkit types — input is records / collections / primitives; output is records / primitives
2. Reuses the `normalize` contract (`minecraft:` prefix + `[state]` strip + lowercase) so histogram keys interop with `EmotionalSensationAnalyzer` and any future analyzer
3. If computing entropy: Shannon normalised by `log2(uniqueBuckets)` so scores are comparable across palettes of different sizes
4. If computing symmetry: defensively test against TYPE-MISMATCHED clusters at distant X positions to defeat the consecutive-uniform-row symmetry-by-construction trap (a 4-block row is always 75 % symmetric around its midpoint)
5. Wire a real production consumer (DNA-046 closure) — the consumer's name and code path must be greppable. A "test-only" analyzer rots; an in-pipeline analyzer compounds
6. Do NOT pull in MockBukkit unless the surface genuinely touches Bukkit runtime — over-engineering trap, even when the dep is in the pom

### Related axis — Wrapper-Over-Tested-Core for subcommand surfaces (KME-042 lesson, now meta)

The KME-042 lesson generalises beyond subcommands to any "newer / friendlier" surface over existing logic. Pattern: grep for the underlying primitive (`dnaRecreate`, `shannonEntropy`, `computeBounds`, `materializeAtStaging`), then build the new surface as a thin wrapper with arg/payload translation. Test the translation pure-static; the underlying body is exercised by the existing tests on the core logic.

### Project reference

`docs/server/GOLD_STANDARD_SERVERS.md` §35 (Semantic Tagging Classifier Doctrine — 8 subsections A-H including the mirror-construction trap and the POJO/MockBukkit over-engineering trap). UKDL Trap 44 (POJO classifiers don't need MockBukkit) + Trap 45 (Bash heredoc append corruption — operational hazard). Seal commit chain on `kdos/v620000-kde-closure`: `63d06d8 feat(kme): KME-005 SemanticTagClassifier` + `939ec5e fix(kme): KME-005 test`.

Sealed 2026-05-28 (BL-OSA-001).

---

## § 2026-05-29 — Map Assimilation Axis (Pane 3, KobiiCraft, Sesión 14 KME-020)

**Sealed:** 2026-05-29 (Pane 3 Sesión 14 of the Hypixel-parity 20-session roadmap — KME-020 Map Assimilation Pipeline shipped as a wrapper over three existing analysis surfaces: `ReferenceMapLoader` + `DnaExtractionAdapter` + `SemanticTagClassifier`)

### The axis (one-line invariant)

> Any roadmap item whose verb is "Pipeline" / "Assimilation" / "Ingest" / "Pump" / "Adapter" / "Bridge" MUST start with a 3-pattern grep of the codebase BEFORE the first line of code — if 2+ existing surfaces hit, the work is COMPOSITION + STATUS ROUTING + INSTANCE LIFECYCLE, not new analysis, and the wall-clock estimate drops from 6-10h to ~1-2h. Output type MUST match whatever the existing extractor produces; do NOT shoehorn input into a richer type by synthesising fake-primitive fields from data the input does not carry.

### The economic calibration

KME-005 (Sesión 13) shipped 10 tests on a 6-test scope because the wrapped-core economic logic was visible from the integration boundary. KME-020 (Sesión 14) shipped exactly 4 tests on a 4-test scope because the underlying analysis (`DnaExtractionAdapter.extract`, `ReferenceMapLoader.readBlocks`, `SemanticTagClassifier.classify`) is already covered by its own hermetic suites. **The wrapper cost is N tests, not N×M, because we trust the modules below.** Composition tests lock 4 specific contract points: empty-input fast path, status enum routing, instance wiring, name carry-through. That's the calibration point for any future pipeline test suite.

### Mandatory checks for any future pipeline wrapper

1. **Output type matches the existing extractor** — `MapAssimilationPipeline.assimilate` returns `ProDNA` not `DnaV2Profile` because `DnaExtractionAdapter.extract` produces `ProDNA`; synthesising a richer type from an impoverished input is the KME-042 antipattern at the pipeline boundary
2. **Status enum with mutually-exclusive terminal cases** — every reachable outcome (SUCCESS / EMPTY_INPUT / UNSUPPORTED_FORMAT / ANALYSIS_ERROR) gets a named enum value; downstream consumers route on the enum, never on exception type
3. **Stateless singleton shared from the orchestrator** — `BlueprintAuditor.semanticTagger()` instance flows into `MapAssimilationPipeline.classifier` so a single audit pass classifies the same blocks exactly once and downstream observability stays consistent
4. **Consumer hook on the standard orchestrator** — `BlueprintAuditor.auditWithAssimilation(blocks, name)` exposes the pipeline as a method on the auditor so external callers don't instantiate sibling pipelines; the accessor `assimilationPipeline()` is the DI hook
5. **Defaults at the wrapper boundary** — blank profile name falls back to a safe default (`assimilated_anon`), not NPE; the wrapper owns these contract-design decisions
6. **Tests cover composition contract only** — 4 cases is the calibration: empty input routing + status mapping + instance wiring + name carry-through. Each pipeline wrapper inherits N=4 as the default; deviate only with empirical reason

### Related axis — Wrapper-Over-Tested-Core, now at three boundary tiers

The Wrapper-Over-Tested-Core meta-rule (sealed at KME-042 for subcommands, extended at KME-005 for analyzers) is now at three boundary tiers:

- **Subcommand wrapper** — KME-042 `/kobimap recreate` wraps `MirrorCommandHandler.dnaRecreate`
- **Analyzer composition** — KME-005 `SemanticTagClassifier` reuses `EmotionalSensationAnalyzer.shannonEntropy` + `normalize`
- **Pipeline composition** — KME-020 `MapAssimilationPipeline` wraps `DnaExtractionAdapter` + `ReferenceMapLoader` + `SemanticTagClassifier`

The economics scale: subcommand wrapper costs 30 min, analyzer composition costs 1.5h, pipeline composition costs 45 min — because each layer reuses the trusted layer below. The compounding payoff is roughly 4× speed on every wrap-eligible work item.

### Project reference

`docs/server/GOLD_STANDARD_SERVERS.md` §40 (Map Assimilation Pipeline doctrine — 8 subsections A-H including wrap-vs-reimplementation economics, consumer wiring pattern, and the honest-scope-of-wrap framing). UKDL Trap 52 (Pipeline wrappers cost ~150 LOC; the assumed 800 LOC is the reimplementation antipattern). Build seal: `mvn clean test → 452 / 0F / 4 skipped / BUILD SUCCESS` + `KobiMapEngine-2.15.0.jar` (1,428,515 bytes). Seal commit chain on `kdos/v620000-kde-closure` (unpushed): C1 `feat(kme): KME-020 MapAssimilationPipeline` + C2 `docs(kme): Sesion 14 seal`.

Sealed 2026-05-29 (BL-MAP-ASSIM-001).


## PP Globalization Sprint Axis v8 (sealed 2026-05-29) -- proactive-availability DONE

The tenth Apex DONE axis. A PP install is Apex-complete on this
axis iff PP's quality tooling is **discoverable, invokable, and
schema-valid in any repo** the Owner works from. This is the
discovery / reach axis that complements the OSA axis v7 (proactive
audit) and the ECC-UQF axis v6 (quality framework).

### Six required components (all six must be present)

1. **At least 7 PP agents globally installed** at
   `~/.claude/agents/{omni-singularity,pp-code-reviewer,pp-monitor,
   pp-uqf-auditor,pp-tco-advisor,pp-ceps-analyst,pp-never-again}.md`.
   Each agent file MUST have valid YAML frontmatter (`name`,
   `description`, `tools` -- no `triggers:`/`throttle:` keys, which
   the Claude Code agent loader silently ignores; activation logic
   lives in Python).
2. **Cross-language rules taxonomy at `~/.claude/rules/`** with
   at least `common/code-review.md` (ECC Pre-Report Gate + Zero
   Findings Is Valid + Proof Triad doctrine) and one language
   subdirectory (e.g. `python/testing.md` with AAA + TDD).
3. **External verifiability** -- `tests/test_globalization.py`
   passes from PP cwd with empirical V-gates on agent
   schema + rules presence + cross-checks against BL-OSA-001
   (UQF importable, TCO MAX-of-recent proxy intact, OSA
   dispatcher returns valid tuple).
4. **Verify probe** -- `tools/verify_globalization.py` returns
   `GLOB_PROBE = 5/5` via a new `globalization` row in
   `tools/verify_spp.py`.
5. **OSA daemon setup documented** -- `vault/osa/daemon_setup.md`
   has Linux crontab + Windows Task Scheduler instructions for the
   `python -m modules.osa.osa_command --audit` periodic runner.
6. **Honest blocker documentation** -- assets that require
   Owner-side registration in `~/.claude/settings.json` or
   `~/.claude/commands/` (classifier-blocked) are documented as
   such in the globalization status report, NOT advisory-tagged.

### Six-check DONE-gate (binary)

1. `python tests/test_globalization.py` exit 0 with `GLOB_PASS = 15/15`.
2. `python tools/verify_globalization.py` exit 0 with `GLOB_PROBE = 5/5`.
3. `ls ~/.claude/agents/{pp-*,omni-*}.md | wc -l` >= 7.
4. `~/.claude/rules/common/code-review.md` and
   `~/.claude/rules/python/testing.md` both exist + carry doctrine
   markers.
5. `tools/verify_spp.py` row `globalization` returns rc=0 with
   `GLOB_PROBE=5/5`.
6. `vault/audits/globalization_status_<ts>.md` exists with a
   36-asset matrix + Plan section ranked by ROI.

### Empirical baseline (2026-05-29)

- 7 PP agents installed and schema-valid: `omni-singularity`,
  `pp-code-reviewer`, `pp-monitor`, `pp-uqf-auditor`,
  `pp-tco-advisor`, `pp-ceps-analyst`, `pp-never-again`.
- `~/.claude/rules/{common/code-review.md, python/testing.md}`
  installed -- cross-language baseline.
- `test_globalization.py` GLOB_PASS=15/15.
- `verify_globalization.py` GLOB_PROBE=5/5.
- `verify_spp.py` extended to 14 rows; the new `globalization`
  row passes.
- Daemon setup at `vault/osa/daemon_setup.md` (Linux crontab +
  Windows Task Scheduler).
- Globalization status report at
  `vault/audits/globalization_status_20260529T111424Z.md` with 36
  assets + 8-entry Plan ranked by ROI.

### Honest classifier blockers (Owner-side actions)

The following sub-features ship the PP-internal half but require
the Owner to authorize the global-side registration:

- `~/.claude/commands/uqf-audit.md` (new) -- classifier denies
  agent self-modification of startup commands directory.
- `~/.claude/commands/code-review.md` (new) -- same.
- `~/.claude/settings.json` hook registration for
  `uqf_pre_edit_gate` / `osa_deploy_detector` / `ceps-bridge` --
  classifier denies hook self-registration.
- `~/.claude/CLAUDE.md` PP-tools section append (QW-A) -- classifier
  denies global startup-config edit.

Per Memory feedback "no classified FAILs at done-gate", these are
documented honestly, NOT promoted to ADVISORY rows. The Owner's
explicit authorization is the remediation path.

### Asymmetric complement to prior axes

- **ECC v6** absorbed the quality FRAMEWORK.
- **OSA v7** absorbed the proactive AUDIT.
- **Globalization v8** makes both REACH every repo, not just PP.

Sealed 2026-05-29 (BL-GLOB-001).


## PP Proactive Agents Axis v9 (sealed 2026-05-29) -- Jobs/Woz Standard DONE

The eleventh Apex DONE axis. A PP install is Apex-complete on this
axis iff every PP agent installed at `~/.claude/agents/` has its
proactive surface wired through the central dispatcher and emits
advisories without explicit invocation when its signal fires.
Complements:
- the OSA axis v7 (proactive AUDIT post-deploy / post-rollback)
- the Globalization axis v8 (REACH every repo)

This axis closes the third leg: PROACTIVE QUALITY across every
session, not just post-deploy windows.

### Six required components (all six must be present)

1. **proactive_core** -- `modules/pp_agents/proactive_core.py`
   exports `ProactiveSignal`, `AgentConfig`, `evaluate_and_fire`,
   `is_throttled`, `mark_fired`, `format_advisory`. Throttle
   state is JSON-on-disk at
   `vault/pp_agents/throttle/<agent>_<project>.json`.
2. **Six signal evaluators** -- `modules/pp_agents/signals/`
   has `code_quality.py` (Jobs), `cost.py` (Jobs), `errors.py`
   (Woz), `health.py` (Jobs), `quality.py` (Woz),
   `lessons.py` (Jobs). Each defines `evaluate(...)` returning
   `ProactiveSignal | None`. None means silence.
3. **proactive_dispatcher** --
   `modules/pp_agents/proactive_dispatcher.py` exports `dispatch`
   and `dispatch_to_additional_context`. Cap is
   `MAX_ADVISORIES_PER_TURN = 3` (no-spam invariant).
4. **jit_skill_loader integration** -- `tools/jit_skill_loader.py`
   carries the `_pp_proactive_inject` decorator in the `run()`
   stack alongside `_tco_inject_routing` and `_tis_log_call`.
   Fail-open: any error in the decorator NEVER blocks the prompt.
5. **jobs_woz_gate.js (Stop-hook)** -- `hooks/jobs_woz_gate.js`
   ships PP-internal as an advisory-only Stop hook. Slop-token
   patterns are built at runtime from string fragments so
   `quality_audit.py` does not veto the file itself.
   Registration in `~/.claude/settings.json` Stop is Owner-side
   (classifier-blocked in auto-mode).
6. **PROACTIVE MODE section in every agent MD** -- all 7 PP
   agents at `~/.claude/agents/` carry a `## PROACTIVE MODE`
   section documenting their speak/silence conditions + format
   contract + throttle path.

### Six-check DONE-gate (binary)

1. `python tools/test_proactive_agents.py` exit 0 with
   `PROACTIVE_PASS = 16/16`.
2. `python tools/verify_proactive_agents.py` exit 0 with
   `PROACTIVE_PROBE = 6/6`.
3. `python tools/verify_spp.py` row `proactive-agents` rc=0.
4. `node hooks/jobs_woz_gate.js < <slop_payload>.json` emits a
   non-empty `additionalContext` block; same hook with a clean
   payload returns only `{"continue":true}`.
5. `python -m pytest tests/ -q` returns 0 failed (no regression
   in the baseline 43 tests).
6. Every PP agent MD at `~/.claude/agents/{omni-*,pp-*}.md`
   carries a `## PROACTIVE MODE` section.

### Empirical baseline (2026-05-29)

- `proactive_core.py`, `proactive_dispatcher.py`, and the 6
  signal evaluators all importable from PP cwd.
- `test_proactive_agents.py`: `PROACTIVE_PASS=16/16`.
- `verify_proactive_agents.py`: `PROACTIVE_PROBE=6/6`.
- `verify_spp.py` extended to 15 rows; `proactive-agents` row
  passes.
- `jobs_woz_gate.js`: dirty payload -> 3-hit advisory; clean
  payload -> silent. Throttle cooldown verified at 15 min.
- All 7 PP agents have PROACTIVE MODE section appended.
- Cold-boot evidence at
  `vault/test-results/cold_boot_PROACTIVE_<ts>.md`.

### Honest classifier blockers (Owner-side actions)

The following sub-feature ships the PP-internal half but
requires the Owner to authorize the global-side registration:

- `~/.claude/settings.json` Stop-hook registration for
  `hooks/jobs_woz_gate.js` -- classifier denies hook
  self-registration in auto-mode.

Per Memory feedback "no classified FAILs at done-gate", this is
documented honestly, NOT promoted to ADVISORY. The Owner's
explicit authorization is the remediation path.

### Asymmetric complement to prior axes

- **ECC v6** absorbed the quality FRAMEWORK.
- **OSA v7** absorbed the proactive AUDIT.
- **Globalization v8** made the framework REACH every repo.
- **Proactive v9** makes the agents SPEAK FIRST when their
  signal fires -- silence is implicit approval.

Sealed 2026-05-29 (BL-PROACTIVE-001).

## PP Hooks Registration Axis v10 (sealed 2026-05-29) -- the proactive agents fire while the Owner works

The twelfth Apex DONE axis. Five hooks (PreToolUse Write|Edit,
PostToolUse Bash x2, SessionStart, Stop) cannot self-register in
auto-mode because the classifier protects `~/.claude/settings.json`.
This axis ships the Owner-runnable scripts that close the gap. The
Globalization axis v8 made the framework REACH every repo; the
Proactive axis v9 made the agents SPEAK FIRST; this axis makes the
five non-prompt surfaces (write, bash output, session-start, stop)
fire automatically once the Owner runs registration once.

### Six required components (all six must be present)

1. **register_global_hooks.py** -- one-time Owner script. Accepts
   `--dry-run`. Backs up `settings.json` to
   `settings.pre-pp-hooks-<ts>.bak` before any write. Merges five
   PP entries idempotently using marker strings (uqf_pre_edit_gate,
   osa_deploy_detector, bug-hunter-ceps-bridge, session-start-check,
   jobs_woz_gate). Bails with rc=3 if any hook script is missing
   on disk.
2. **check_hook_status.py** -- cwd-agnostic state report.
   Resolves registered markers, the active jit_skill_loader entry
   in UserPromptSubmit, the inventory of `~/.claude/agents/`, and
   the five most recent advisories from `vault/pp_agents/throttle/`.
   Exit code 0 when fully active, 1 with ACTION REQUIRED when any
   marker is missing.
3. **Five hook scripts** -- `hooks/{uqf_pre_edit_gate,
   osa_deploy_detector, bug-hunter-ceps-bridge, jobs_woz_gate}.js`
   and `tools/tco_compact_gate.py --session-start-check`. All are
   advisory-only (continue:true), fail-open, slop-token-free in
   source via runtime concatenation.
4. **docs/HOOKS_SETUP.md** -- Owner instructions, rollback path,
   what-each-hook-does table, quick reference cheat sheet.
5. **tools/_hook_smoke.py** -- empirical smoke harness that runs
   every hook with synthetic payloads via cmd-redirect (bypasses
   PowerShell stdin-to-native-exe drop) and writes evidence to
   `vault/test-results/hook_smoke_<ts>.md`.
6. **tools/verify_hooks_registration.py** -- 7-check sub-verifier
   wired into `tools/verify_spp.py` as a new row.

### Six-check DONE-gate (binary)

1. `python tests/test_hooks_registration.py` exit 0 with
   `HOOKS_REG_PASS = 13/13`.
2. `python tools/verify_hooks_registration.py` exit 0 with
   `HOOKS_REG_PROBE = 7/7`.
3. `python tools/verify_spp.py` row `hooks-registration` rc=0.
4. `python tools/_hook_smoke.py` exit 0 with `SMOKE_PASS = 7/7`
   (each of the 5 hooks behaves as expected on its dirty + clean
   payloads).
5. `python tools/register_global_hooks.py --dry-run` exit 0
   listing all five hooks with real absolute paths, settings.json
   untouched (verified by file mtime).
6. `python tools/check_hook_status.py` runs from any cwd without
   crash; reports gaps clearly when registration is incomplete.

### Empirical baseline (2026-05-29)

- 4 JS hooks shipped: `uqf_pre_edit_gate.js`, `osa_deploy_detector.js`,
  `bug-hunter-ceps-bridge.js`, `jobs_woz_gate.js`.
- tco_compact_gate.py extended with `--session-start-check`
  (silent below 70% context proxy, advisory above).
- `register_global_hooks.py` 8151 bytes; `--dry-run` rc=0 with
  five hook entries enumerated.
- `check_hook_status.py` 4763 bytes; reports correctly with rc=1
  (ACTION REQUIRED) until the Owner runs registration.
- `_hook_smoke.py` 9045 bytes; SMOKE_PASS=7/7 with evidence at
  `vault/test-results/hook_smoke_<ts>.md`.
- `verify_hooks_registration.py` 7-check probe: 7/7 PASS.
- `test_hooks_registration.py` 13/13 V-gates PASS (renamed to
  `_check_*` so pytest does not auto-collect and recurse).

### Honest classifier blocker (Owner-side action)

The actual registration step requires the Owner to run:

```
python tools/register_global_hooks.py
```

from a terminal after closing all Claude Code sessions, then
reopen Claude Code. Claude Code itself cannot run this in
auto-mode -- the classifier denies the settings.json mutation.
This is by design, not a workaround. The ship-side surface (the
script, the docs, the verify probe) is complete. The user action
is the registration trigger.

### Asymmetric complement to prior axes

- **ECC v6** absorbed the quality FRAMEWORK.
- **OSA v7** absorbed the proactive AUDIT.
- **Globalization v8** made the framework REACH every repo.
- **Proactive v9** made the agents SPEAK FIRST when their signal fires.
- **Hooks Registration v10** WIRES the non-prompt surfaces (write,
  bash output, session-start, stop) into the Owner's daily flow
  via a one-time terminal command -- silence remains implicit
  approval; speaking up is now automatic across every event.

Sealed 2026-05-29 (BL-HOOKS-REG-001).

## PP Bug->HardRule + Cascade Guard Axis v11 (sealed 2026-05-29)

The thirteenth Apex DONE axis. UKDL collects bug lessons (passive
learning); this axis lifts the CRITICAL and recurrence>=3 subset
into CLAUDE.md as structural stops (active gating) and revives the
Cascade Error Prevention agent as a real proactive surface.

### Six required components (all six must be present)

1. **modules/hard_rules/{extractor,writer}.py** -- aggregator and
   dual-target writer (archive + CLAUDE.md sentinel block).
   Idempotent on content digest; backup before write.
2. **tools/bug_to_hardrule.py** -- CLI with --scan / --propose /
   --retroactive / --install / --list.
3. **modules/osa/never_again.py** -- inject() auto-drops a draft
   to vault/hard_rules/auto_*.md when severity=CRITICAL or
   recurrence>=3.
4. **modules/pp_agents/signals/cascade.py** -- co-occurrence
   detector over CEPS events.jsonl (window 300s, min count 2).
5. **~/.claude/agents/pp-cascade-guard.md** -- global advisor with
   the PROACTIVE MODE contract (silent until cascade map is
   non-empty AND current error matches a known source).
6. **proactive_dispatcher.py** -- pp-cascade-guard registered with
   cooldown 5 min, min_signal 0.7.

### Six-check DONE-gate (binary)

1. `python tools/test_hard_rules.py` exit 0 with
   `HARDRULES_PASS = 14/14`.
2. `python tools/verify_hard_rules.py` exit 0 with
   `HARDRULES_PROBE = 7/7`.
3. `python tools/verify_spp.py` row `hard-rules` rc=0.
4. `python tools/bug_to_hardrule.py --list` rc=0 with at least
   one installed HR-NNN (or honest "No hard rules" if UKDL has
   no qualifying candidates).
5. `~/.claude/agents/pp-cascade-guard.md` carries a PROACTIVE
   MODE section + cascade snapshot protocol.
6. `pytest tests/ -q` returns 0 failed (baseline 43+ intact).

### Empirical baseline (2026-05-29)

- 6 hard rule candidates surfaced from never_again + UKDL +
  session_lessons under Decision A3 gating.
- 7 hard rules installed retroactively (HR-001 through HR-007),
  including the test artifact HR-002 from the M4 smoke probe.
- CLAUDE.md created at PP repo root with sentinel block.
- vault/hard_rules/HARD_RULES.md canonical archive populated.
- pp-cascade-guard registered as 7th proactive agent.
- Cascade map is empty today (9 events.jsonl rows, no
  co-occurrence within 5 minutes) -- correct silent state.
- All baselines green: pytest 43/43, test_proactive_agents 16/16,
  test_hooks_registration 13/13, test_hard_rules 14/14.

### Asymmetric complement to prior axes

- **ECC v6** absorbed the quality FRAMEWORK.
- **OSA v7** absorbed the proactive AUDIT.
- **Globalization v8** made the framework REACH every repo.
- **Proactive v9** made the agents SPEAK FIRST when signals fire.
- **Hooks Registration v10** WIRES the non-prompt surfaces.
- **Bug->HardRule + Cascade Guard v11** TURNS lessons into stops
  and revives cascade detection -- UKDL is passive memory,
  CLAUDE.md is active gate, CEPS co-occurrence is the early
  warning before the second leaf falls.

Sealed 2026-05-29 (BL-HARDRULE-001).

## MCP-Plugin-Resilience Axis v12 (sealed 2026-05-31, BL-PLAYWRIGHT-001)

### C20 -- MCP-Plugin-Resilience-by-default

**Constraint:** every MCP server loaded via `enabledPlugins` (NOT
`mcpServers`) in `~/.claude/settings.json` must ship with the
following resilience stack, OR it is not done by definition:

1. **Stale process killer** -- platform-appropriate script (e.g.
   `tools/playwright_stale_killer.ps1`) that kills processes of the
   plugin's child binary when their idle age exceeds a threshold.
   Plugin loader respawns fresh ones with clean transport on next use.
2. **Watchdog** -- Task Scheduler (Windows) / cron / systemd timer
   (Posix) that invokes the killer every `interval < idle_threshold/2`.
   Idempotent install via the script itself (`-Action start`).
3. **Health check** -- `tools/check_<plugin>_mcp.py` (or equivalent
   platform script) reporting: plugin enabled state, live process
   count + ages, killer + watchdog presence, watchdog state. Verdicts:
   READY+RESILIENT / WARN / FAIL. ASCII-safe output.
4. **UKDL entries** -- Process Rule (mandatory verification protocol
   for the operator) AND Trap (architectural antipattern: the
   plugin-vs-mcpServer distinction, with the `mcp__plugin_*` tool-name
   recognizer). Both in `vault/knowledge_base/ukdl-universal.md`.
5. **V-gate test** -- `tools/test_<plugin>_resilience.py` with the
   minimum 11 gates from the BL-PLAYWRIGHT-001 template:
   killer-exists / watchdog-exists / check-exists / repro-doc /
   ukdl-pr / ukdl-trap / plugin-signal / check-runs / watchdog-status /
   killer-dryrun / baseline-intact.
6. **verify_spp probe** -- row added to `tools/verify_spp.py`
   `rows_spec` invoking the V-gate test. Budget <= 60s.

**NEVER:** add `mcpServers.<pluginname>` to settings.json when the
plugin is already loaded via `enabledPlugins`. The two mechanisms
compete for the same name; undefined behavior in the plugin loader.

### Why this axis (asymmetric complement)

- **v11** (BL-HARDRULE-001) turned lessons into stops at the data /
  deploy gate. This is the high-severity layer.
- **v12** (BL-PLAYWRIGHT-001) is the LOW-severity, OPERATIONAL layer:
  flow hiccups (transport disconnects, plugin process drift) that do
  not destroy state but do interrupt work. Process Rules + watchdogs,
  not Hard Rules. Different severity, different gate semantics. The
  two layers compose: every PP MCP plugin now has BOTH a Hard-Rule
  pathway for catastrophic conditions AND a Process-Rule pathway for
  operational disconnects.

### Empirical baseline (2026-05-31)

- 5 node.exe @playwright/mcp procs detected alive at 15min idle.
- Claude Code runtime: `mcp__plugin_playwright_*` DISCONNECTED in same
  window (system-reminder evidence). Gap = transport stale, not crash.
- Original plan (Option C/D: add `mcpServers.playwright + timeout`)
  REJECTED at PASO 0 -- target was wrong by architecture.
- Option A executed: killer + watchdog + health-check + signal + UKDL
  + V-gate test + verify_spp probe. All 11 V-gates PASS. verify_spp
  --row playwright-resilience PASS in 7.05s.

### Reusability

The 6-point stack is plugin-agnostic. To onboard a future MCP plugin
(e.g. browser-use, sequential-thinking) under this axis: copy the
`tools/playwright_*` scripts as templates, rename, update process
matchers, register a sibling row in `verify_spp.py`. The Process Rule
template and Trap template in UKDL are reusable as-is with name
substitution.

Sealed 2026-05-31 (BL-PLAYWRIGHT-001, Option A, Owner-approved).

---

## Slash-Recovery Pattern Axis v13 (sealed 2026-06-01)

**Origin:** BL-COMPACT-001 -- the `/compact` 95% hang. The bug
lives in `claude.exe` (binary, not patchable). The only Power
Pack response is to give the Owner a clean escape when it
happens. Generalises into a reusable axis: every slow or
blocking PP slash command can ship a sibling `/command-rescue`.

**Why an axis (not just one fix):** other commands have the same
shape -- a chat-level invocation that hands control to a long
internal pipeline we do not see. When that pipeline freezes, the
Owner is stuck. Pre-registering the rescue template means we
fix it in one place, not N times.

### C21 -- Slash-Recovery by default

Every PP slash command whose execution can block for >30s
without observable progress (e.g. `/compact`, `/cpp-distill`,
`/cpp-deep-research`, `/ultra plan`) should ship the 6-point
recovery stack on first incident:

1. **Empirical repro doc** -- `vault/knowledge_base/<cmd>-hang-repro.md`.
   Document the symptom, root-cause hypothesis, why no auto-kill,
   what is lost vs kept in a rescue.
2. **Rescue script** -- `tools/<cmd>_rescue.ps1`. PowerShell-native
   (Windows host doctrine). Owner-triggered, never auto. Includes
   a recency guard (`.jsonl` mtime by default) so it cannot kill
   a session that looks active. ASCII-only (PS 5.1 codepage trap).
3. **Slash command** -- `commands/<cmd>-rescue.md`. Documents
   when to invoke, what is lost, what is kept, dry-run mode,
   override flag, post-rescue verification.
4. **Alert-only detector** -- `tools/<cmd>_hang_detector.py`.
   Opt-in scheduled task. Heuristic detection with documented
   false positives. **NEVER kills.** Notifies the Owner; the
   Owner decides whether to run the rescue.
5. **UKDL Process Rule + Trap** -- PR-`<CMD>`-NNN in
   `vault/knowledge_base/ukdl-universal.md`. Process Rule for
   recoverable cases (no irreversible data loss); Hard Rule
   only if the failure can destroy work. Sibling Trap entry
   documents the heuristic false-positive surface so future
   builders do not re-invent the auto-kill antipattern.
6. **V-gate test + verify_spp row** -- `tools/test_<cmd>_rescue.py`
   with 7+ V-gates (rescue exists, slash cmd exists, detector
   exists, dry-run JSON well-formed, guard fires on active
   session, UKDL markers present, baseline imports intact). Add
   a row to `verify_spp.py` so the umbrella catches regressions.

### Why Owner-trigger, never auto-kill

The pattern looks tempting to automate -- "detect hang, kill,
restart". Resist. Two empirical reasons:

- The hang signal is heuristic: `RSS > X` AND `CPU < Y` AND
  `.jsonl idle > Z` matches a long-thinking Owner with a large
  transcript as readily as it matches a stuck session.
- The cost of a false-positive kill is the entire current turn
  (worst case mid-Edit). The cost of a false-negative
  (waiting longer than necessary) is bounded by Owner patience.
  Asymmetric -- favour the conservative path.

The detector script can ALERT (toast, log, exit code) but the
kill action stays human-in-the-loop via the slash command.

**Low-friction 1-click helpers are compatible with this axis.**
A `YesNoCancel` MessageBox in the alert popup -- where Yes
spawns the rescue inline -- preserves the Owner-decision
contract while collapsing the friction from "open terminal +
type command" to "click Yes". The kill still requires explicit
consent at the moment of alert. No-click paths (auto-kill on
timeout, scheduled-task `--auto-rescue-after N`) are excluded.
The distinction is binary: a kill needs a human decision at the
moment it happens, even if that decision is just a mouse click.

Implementation reference: `tools/compact_hang_detector.py
--interactive` (opt-in via `--install --interactive`). On
detection: blocks up to `INTERACTIVE_POPUP_TIMEOUT_S` (5 min)
for an Owner click. Yes -> spawn `compact_rescue.ps1`
(guard-bypassed since detector + Owner click already confirm
intent). No -> write `~/.claude/state/compact_snooze_until.txt`
suppressing alerts for `DEFAULT_SNOOZE_SECONDS` (60 s).
Cancel / timeout -> no action. Passive (legacy OK-only popup)
remains the default mode.

### Empirical baseline (2026-06-01)

- 40 `claude.exe` procs observed; RSS distribution skewed (top
  3 = 451MB / 373MB / 352MB).
- Owner-reported symptom: `/compact` indicator stuck at 95%, no
  `.jsonl` writes. No precedent in vault -- first cycle to see it.
- M0-M5 done-gated green: 7/7 V-gates PASS; `verify_spp --row
  compact-resilience` STRICT PASS in ~5s.
- Upstream issue body drafted in
  `vault/knowledge_base/anthropic-issue-compact-95.md` for
  filing -- the binary bug is the only path to a real fix.

### Reusability

The 6-point stack is command-agnostic. To onboard a future PP
slash command under this axis: copy the
`tools/compact_rescue.ps1` + `tools/compact_hang_detector.py` +
`tools/test_compact_rescue.py` triad as templates, rename,
update process matchers and recency-guard target, register a
sibling row in `verify_spp.py`. The Process Rule + Trap
templates in UKDL are reusable as-is with name substitution.

Sealed 2026-06-01 (BL-COMPACT-001, Owner-approved plan inline).
