

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
