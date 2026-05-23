

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
