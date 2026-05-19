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
