# Apex Completion Standard — JIT Aggressive Activation Law

> Sealed BL-0069 (2026-05-16). Permanent, mandatory. Version-controlled
> source of truth: `<power-pack>/knowledge_vault/core/apex-completion-standard.md`.
> Global mirror: `~/.claude/knowledge_vault/core/apex-completion-standard.md`
> (byte-identical; drift is a hard gate failure via `verify_global_mirrors.py`).

Every skill or specialist knowledge module added to the Power Pack from
BL-0069 onward MUST be **latent-by-default, JIT-full-depth-on-trigger**.
Always-on injection of heavy reference material is a Reality-Contract
violation: it taxes every unrelated turn for context the turn does not use.
The five sections below are the unyielding blueprint. A feature that does
not pre-wire all five is **incomplete by definition** (plan-time-audited,
not a runtime hook).

## 1. UserPromptSubmit interception contract

The activation hook runs on the `UserPromptSubmit` event. Its emitted JSON
places injected text at **top-level `additionalContext`**, NOT nested under
`hookSpecificOutput`. This is empirically fixed by the in-process merge
switch in `~/.claude/hooks/hook-dispatcher.js` (lines ~156-166): only
`PreToolUse` nests `additionalContext` inside `hookSpecificOutput`; every
other event — `UserPromptSubmit`, `SessionStart` via the merged path,
`Stop` — uses top-level `additionalContext`. Emitting the wrong shape =
silently dropped injection that *looks* like success (Mistake #16). The
hook MUST be fail-open: any internal error returns `{"continue": true}`
and never blocks the prompt; a diagnostic line is logged (Ley 24). A
bounded stdin watchdog (≤3 s) guarantees a response even if stdin never
closes. Reference implementation: `tools/jit_skill_loader.py`.

## 2. Selective module parsing (trigger matrix)

Activation is tiered-aggressive: inject the FULL reference of ONLY the
module(s) whose trigger directly matches this prompt/cwd — never the whole
catalog. The trigger matrix maps file extensions, dependency manifests,
and prompt-intent regexes to specific modules with a priority rank. The
cheap signals run first (prompt text + `package.json` dependency keys);
the filesystem walk is the fallback, is depth-bounded (≤4), skip-dir'd,
hard-capped at 2000 dirent stats, and early-exits on the first matching
file. Non-matched modules stay as their latent ~80-token discovery card
(served by the SessionStart sentinel) — they are NOT escalated.

## 3. Context-budget validation (40 KB circuit breaker, BL-0068)

Total force-injected bytes per activation MUST NOT exceed the BL-0068
circuit breaker of 40,000 bytes (≈10 k tokens). When multiple modules
match, fill by ascending priority rank until the budget would be exceeded,
then defer the remainder (they degrade to their latent cards and a
one-line "deferred" note is appended). The breaker is a hard guard, never
disabled. Token Austerity (DNA-3000) is not optional: a feature that can
blow the context window on a common path is not done.

## 4. Session-dedupe (inject-once, resident-after)

A module is force-injected at full depth at most ONCE per session. State
lives in `~/.claude/state/jit-injected-<sid>.json`, written atomically
(temp + `os.replace`). `<sid>` = the harness `session_id`; when absent,
fall back to `cwd-<sha1(cwd)[:12]>`. Every entry carries a timestamp;
entries older than a 2 h TTL are ignored so a stale id can never
permanently suppress a module across sessions. State read/parse failure
is treated as "not yet injected" (fail toward injecting). Under a
concurrent-prompt race the worst case is one extra bounded injection —
acceptable; a missed injection or a crash is not.

## 5. Mandatory rule for all future skills

Every new Power Pack skill/module MUST ship: (a) a latent ≤80-token
discovery card warmed by the SessionStart sentinel, AND (b) a JIT
full-depth path keyed into the `UserPromptSubmit` trigger matrix, AND
(c) a deterministic verification criterion in the relevant gate that
proves real injection (parsed `additionalContext`, ≥95 % of the
reference's bytes literally present — not a summary). Always-on heavy
injection, a card with no JIT escalation, or a JIT path with no
empirical gate each fail this standard. Registration is via
`python tools/settings_merger.py register-userprompt` (absolute
interpreter preflight, append-only bounded settings merge, timestamped
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
