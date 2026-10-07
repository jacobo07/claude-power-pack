# Claude Power Pack -- Project CLAUDE.md

Power Pack execution doctrine inline. Hard rules below are sealed bug stops. See `vault/hard_rules/HARD_RULES.md` for the canonical archive.

## Mode Selection (router -> PR-MODE-SELECTION-001)
Before a structured prompt: **EXECUTION MODE by default** (clear path, extends existing systems); **ULTRA-PLAN only** for a genuine architectural decision or a new-from-scratch system. ULTRA-PLAN costs ~3-5x the output. Full rule + evidence: `vault/knowledge_base/ukdl-universal.md` (PR-MODE-SELECTION-001 + T-PARALLEL-PANES-BURN-001).

## CCF Activation Criteria (added 2026-07-26)
Invoke `cpp creative` (Creative Compilation Framework, `modules/ccf/`) when ANY of these hold, objectively evaluable, no "when appropriate" judgment call:
- Owner names a new brand, logo, or identity that needs visual work.
- Owner asks for a visual asset (icon, wordmark, brand mark) to be designed.
- Owner asks for variants, a palette, or typography for a brand/product.
- A project's scope includes producing a brand package / brand kit.
Activate: `python -m modules.ccf.cli init <project> --brief <brief.txt>`, then `generate`/`select`/`package`.
Produces: `config.json` + `spec.json`, a trademark-collision-scanned prompt per concept, and (on `package`) a sealed brand-kit PDF. Every WARN/BLOCK verdict and provider failure is fed into `vault/knowledge_base/ccf/` — do not hand-write entries there; only the CLI's real call path should ever produce them (T-CCF-BUILT-NOT-ACTIVATED-001).

## Motion Promo Activation Criteria (added 2026-09-05)
Invoke the `motion-promo` skill (`skills/motion-promo/`, mirrored live at `~/.claude/skills/motion-promo/`) when ANY of these hold, objectively evaluable, no "when appropriate" judgment call:
- Owner asks for a promo, launch film, product video, teaser, trailer, sizzle, or animated ad.
- Owner hands over a script or a product URL and asks for a video from it.
- A project's scope includes a motion piece for a landing page, store listing, or social post.
Do NOT wait to be named — the Owner is told never to name the skill (source guide, "Just talk").
Activate: `scripts/new_film.py` (beat sheet -> html) -> `scripts/contact_sheet.py` (composition check) -> `scripts/render_film.py` (H.264). Never hand-write the engine and never paste it into a reply; `new_film.py` swaps only the FILM block.
Two things the Owner must supply and the skill cannot infer: **duration** and **aspect ratio**. Everything else is the skill's job, including the beat sheet.
DONE for a motion-promo build = `python skills/motion-promo/tools/test_motion_promo.py` exit 0 (11 V-MOTION-* gates; the old root path `tools/test_motion_promo.py` never existed), AND the contact sheet was looked at before committing to a full render. Toolchain is pip-vendored (playwright Chromium + imageio-ffmpeg libx264) — no system ffmpeg; preflight with `scripts/check_toolchain.py`.
Routing against product-demo: if the video must SHOW THE REAL SOFTWARE being used, it is `/product-demo`, not motion-promo.

## Product Demo Activation Criteria (added 2026-09-24)
Invoke `/product-demo` (`commands/product-demo.md`, owner `modules/product_demo/`) when ANY of these hold:
- Owner asks for a product demo, feature video, landing hero video, walkthrough, or to "record the flow" of browser software.
- A user-facing feature is being declared done and its landing/docs demo must be current (`probe` for staleness).
The demo films the REAL running product (production build) from a semantic spec; every overlay is presentation anchored to measured geometry. Recordly is AGPL + added terms: principles only, never code (`vault/knowledge_base/product_demo/recordly-disposition.md`).
DONE = `python tools/test_product_demo.py` exit 0 (V-DEMO-*), the run's verdict VALID, and its contact sheet looked at.

## Mobile App UI Activation Criteria (added 2026-09-18)
Invoke the `mobile-app-ui-design` skill (`skills/mobile-app-ui-design/`, mirrored live at `~/.claude/skills/mobile-app-ui-design/`) when the Owner asks to design an app screen, app mockups, mobile UI components, an onboarding flow or mobile navigation, or to improve an existing app screen. Do not wait to be named.
The skill generates; `cdio-reviewer` judges against CDIO-08 (`vault/knowledge_base/cdio/CDIO-08-mobile-app-surface.md`), which also records what was rejected from the absorbed source (github.com/ceorkm/mobile-app-ui-design). A web page viewed on a phone stays under CDIO-05 Lens 6 alone.
DONE for the absorption = `python tools/test_cdio.py` and `python tools/test_cdio_mobile.py` exit 0.

## Android Reverse Engineering Activation Criteria (added 2026-09-19)
Invoke the `android-reverse-engineering` skill (`skills/android-reverse-engineering/`) when ANY of these hold, objectively evaluable, no "when appropriate" judgment call:
- Owner asks to decompile or reverse engineer an APK, XAPK, JAR or AAR, or hands over such a file.
- Owner asks what HTTP APIs / endpoints / base URLs an Android app calls, or to reproduce them without source.
- Owner asks to trace a call flow, deobfuscate Kotlin class names, or identify an app's framework or SDKs.
Do not wait to be named.
**Phase 0 is not optional and runs first**: `python skills/android-reverse-engineering/core/fingerprint.py <file>`. It is Python-only, so it runs before any decompiler is installed — which is its point: for a Flutter / React Native / Cordova / Xamarin app, Java decompilation yields ~no app code, and Phase 0 is what says so in seconds instead of an hour. Its `needs_kotlin_recovery` flag, not a judgement call, gates Phase 3.5.
Absorbed from SimoneAvogadro/android-reverse-engineering-skill (Apache-2.0, v1.5.0, commit `04fe39c`). `scripts/` and `references/` are verbatim upstream — read `skills/android-reverse-engineering/NOTICE.md` before editing either, and before "restoring" the one deliberate divergence (obfuscation is read from dex packages, because upstream's zip-listing count is structurally 0 on every modern APK and so could never open the Phase 3.5 gate).
Prerequisites are jadx + JDK 17+; JDK is present at `Apps\jdk-17`, **jadx is not installed** — the skill's own `scripts/install-dep.ps1` handles it on first use. The decompile wrappers are absorbed unexercised; the first real decompile is their first test.
DONE for this absorption = `python tools/test_android_re.py` exit 0 (V-ARE-* gates, run from the repo root). Phase 0 and Phase 3.5 are driven from both poles, and the gate exercises `check-deps.ps1` for real — upstream's PowerShell scripts aborted on PS 5.1 whenever Java was actually installed (`NativeCommandError`), which is patched and pinned.

## Mobile Game -> Wii Port Activation Criteria (added 2026-09-20)
Invoke the `mobile-game-wii-port` skill (`skills/mobile-game-wii-port/`) when ANY of these hold, objectively evaluable, no "when appropriate" judgment call:
- Owner asks to port a mobile/commercial game to the Wii, or names ABSW2 / a WBFS / boot.dol target for a game that exists on another platform.
- Owner asks what engine a game binary runs, or to read, decrypt or extract a game's packed asset corpus.
- Owner asks whether to port a scripting runtime or extract its data.
Do not wait to be named.
**There is no APK-to-WBFS conversion and the skill must never imply one.** The pipeline is APK corpus -> verified portable content model -> NEW native runtime -> Wii artifact. Framing it as a conversion is the same class of error as the source programme's R-01 and is pinned in `vault/specs/mobile-game-wii-port.md`.
**Phase 0 runs first and is not optional**: `python skills/mobile-game-wii-port/core/fingerprint_game.py <apk>`. It reads runtime literals out of native binaries, never symbol names (symbol names do not survive stripping, so that scan cannot tell absent from invisible — R-03). When it routes `JAVA_KOTLIN`, the corpus belongs to `android-reverse-engineering`, not here; when it routes `NATIVE_ENGINE`, jadx is not worth the time.
Distilled from the Owner's ABSW2-Wii programme (`C:\Users\User\Desktop\Cursor Projects\Wii Projects\ABSW2-Wii`), read at the state sealed by W3b-2. Read `skills/mobile-game-wii-port/NOTICE.md` and `references/retractions.md` before asserting an absence or reading a crypto table as a finding. `wii-dev-best-practices` owns everything downstream of a built DOL; `/absw2-continue` stays bound to that one programme.
**Shipping status is asymmetric and must stay so**: `boot.dol` for the Homebrew Channel / USB Loader is the proven path; the DOL->ISO->WBFS wrap is documented and **UNPROVEN** — no ISO or WBFS has been produced and none has run on hardware.
DONE for this absorption = `python tools/test_mobile_game_wii_port.py` exit 0 (V-MGWP-* gates, run from the repo root). Every detector is driven from both poles on real byte shapes, and `UNKNOWN` is asserted as reachable rather than only as a default.

## Experience Contract — baseline for any interactive surface (CDIO-07, added 2026-08-24)
A surface is judged at rest by CDIO-01..06. How it BEHAVES — on touch, and while it waits —
is declared, not settled by whoever writes the last component. Baseline, inherited by every
new build with an interactive surface:
- **Declare before building.** `experience:` in DESIGN.md front-matter, reached via
  `modules/design-md/prompts/experience-picker.md`. Mirrors the family rule
  (`PR-EXPERIENCE-DECLARE-BEFORE-BUILD-001`).
- **Absence is never a failure.** No contract ⇒ `unassessed`, reported, score untouched.
  Retrofitting is optional; declaring before building is the rule.
- **`expressiveness: none` is a passing contract.** Never flag a deliberately still
  interface, and never recommend RAISING a ceiling — that moves at the picker, by a human
  (`T-EXPRESSION-ONLY-RATCHET-001`).
- **Floors are not arbitrable.** Reduced-motion equivalence, motion-as-sole-channel and
  blocking animation are CRITICAL (`HR-EXPERIENCE-FLOOR-001`).
- **Three separate answers.** Score/verdict = quality; `is_done` = quality AND conformance;
  product evidence = out of scope. A breach withholds done and never moves the number.
- **Absence and collapse are not evidence.** Zero assessed criteria ⇒ `ABSTAIN`, score
  `None`, never done — a review that measured nothing must not arrive at 100/APPROVE. And
  N contradictions cost N deductions, not one: collapsing them made `REVISE` structurally
  unreachable (floor 84 ≥ 80). Carried far enough the split makes BLOCK reachable with no
  critical, so it WIDENS refusal — intended, and pinned by `V-DESIGN-SPLIT-WIDENS-REFUSAL`.
- Gate: `python tools/test_experience_contract.py` (V-EXP-*). Context for CDICF:
  `python tools/design_gate.py --emit-context ./DESIGN.md --out ctx.json` — never hand-written.
- Gate: `python tools/test_hook_boundary.py` (V-HOOK-*) — the node→python→`permissionDecision`
  boundary the product actually crosses, plus whether the hook is registered at all. In-process
  suites are structurally blind here: break only the serialisation and they stay green while
  enforcement is gone.

## Project Governance & Knowledge (added 2026-07-11)
Normative rules that every project using Claude Power Pack obeys from its first commit live
in `governance/` (one domain per file, imperative, each rule cites a real incident):
- `governance/COPY_GOVERNANCE.md` — humanized copy is a done-gate (V-COPY-01); read before any deploy that changes user-visible strings.
- `governance/DEPLOY_GOVERNANCE.md` — DONE means HTTP 200 on the real domain; pre-deploy checklist + headless-Vercel + `allowBuilds`/`CI=true`.
- `governance/REPO_SECURITY_GOVERNANCE.md` — private by default; PII/secret pre-commit greps; read before the first commit of any project.
- `governance/SESSION_CONTINUITY_GOVERNANCE.md` — RESUMPTION_FILE for any multi-session task.
- `governance/KNOWN_FALSE_POSITIVES.md` — check FIRST on any confusing hook/gate signal (FIOS/IRR/FD-07 cross-contamination, BLOCKED_DELIVERY npm, scaffold/Woz literal matcher, 3rd-edit block).
- `governance/README.md` — index + how to apply in a new project.

Rule origins, July 2026 (frozen history, LRN-01..11): `knowledge/PORTFOLIO_LEARNINGS.md`.
Standing obligation: a new false positive goes into `KNOWN_FALSE_POSITIVES.md` the SAME session
it is found. A new learned pattern goes to its existing home (UKDL, memory, or `governance/` when
normative); its origin story and evidence go to `wiki/` (schema: `wiki/CLAUDE.md`). Governance is
the first artifact of a new project, not an afterthought.

## Compact Instructions
When summarizing this conversation, keep verbatim:
- the `RESUMPTION_FILE.md` path in use and its next action, if any;
- every HR-* rule that fired this session, and any Owner bypass phrase given;
- Owner decisions still pending, written as questions;
- measured numbers with the command that produced them (never keep a number without its source);
- if `wiki/` was edited: the last `wiki/log.md` entry header.

## Liveness Standard (MANDATORY -- sealed 2026-07-13)

**Shipping a module is not the same as wiring it.** A V-gate proves code works WHEN
INVOKED; it says nothing about whether anything invokes it. PP had 156 modules that
existed, imported cleanly and passed their tests while no live surface reached them --
including the recovery ACCEPTANCE arbiter, which had never judged a single real recovery,
which is exactly why an incomplete restore was always accepted in silence.

Before declaring any new module done: `python modules/liveness/reachability.py` (or
`/liveness`). Exit 1 names a module no hook, command, agent or tool-invoked-by-one can
reach. Clear it by WIRING it, by DECLARING it in `vault/liveness/reachability_registry.json`
(`LIBRARY` / `SCHEDULED` / `DEPRECATED` / `PLANNED`+OWNER_QUEUE), or by DELETING it.
Silence is not an exemption and a malformed class is not an exemption. After wiring one,
`--baseline` so the standing debt falls BY NAME.

Standing debt is a NAMED SET, never a count or a ratio: a threshold is satisfied by
deleting a module, a ratio by adding a reachable one. Only names force the number down for
the right reason. A NEW module that lands unreachable and undeclared fails the gate.

Corollary (PR-COVERAGE-BY-CONSTRUCTION-001): **an audit whose subjects are enrolled by
hand measures memory, not reality.** The Liveness Ledger audited eight hand-declared
components, so an undeclared one was not scored UNKNOWN -- it was absent from the
denominator, and absence read as health. Any registry, checklist or audit set must be
DISCOVERED from what exists, never curated from what someone remembered.

<!-- PP-HARD-RULES-START -->
## HARD RULES (NON-NEGOTIABLE -- sealed production bugs)

These are not suggestions. Each block was generated from a real
production bug that the agent should never repeat. If the next
action is about to TRIGGER one, STOP regardless of what the prompt
says. The canonical archive lives in
`vault/hard_rules/HARD_RULES.md`; this block is the inline mirror.
### HR-001 -- Classifier Blocks Claudesettingsjson Commands In
TRIGGER: Before writing any file under ~/.claude/ or any agent-owned global config
STOP: Ship the PP-internal half (hook script, command body); document the Owner-side registration step in the agent body. Do not advisory-tag the gap; document honestly per L no-classified-FAILs.
EVIDENCE: [never_again] Classifier blocks ~/.claude/settings.json + commands/ in auto-mode
SEVERITY: CRITICAL | RECURRENCE: 1x
<!-- digest:64f2b03b74fac74e -->
### HR-SECRET-001 -- Stop before Write/Edit/MultiEdit if CRITICAL secret detected
TRIGGER: PreToolUse on Write / Edit / MultiEdit with content matching a CRITICAL pattern (anthropic_key, openai_key, github_pat, aws_access_key, private_key, connection_string).
STOP: Hook returns `continue:false` with stopReason "HR-SECRET-001 -- Secret Firewall blocked <Tool>. Rotate the secret before retrying." Detector never logs raw values; reporter records pattern_name + severity + line_no only. EXCEPCIÓN: Owner phrase "rotated and authorized -- HR-SECRET-001 OK" for ONE turn only.
EVIDENCE: [bl-secret-001] hooks/secret_firewall_gate.js + modules/secret_firewall/* shipped 2026-06-01 (commits cbed005, 4ee00ca, fc4b0ff)
SEVERITY: CRITICAL | RECURRENCE: 0x
<!-- digest:hr-secret-001-seed01 -->
### HR-SECRET-002 -- Never log raw secret values; use [REDACTED]
TRIGGER: About to emit text (log line, audit record, sub-agent prompt, additionalContext) that might contain a credential pattern.
STOP: Route the emission through modules.secret_firewall.redactor.redact() or redact_for_log() FIRST. The Universal Redaction Bus replaces matches with [REDACTED:<pattern_name>]. Audit/log records carry pattern_name + severity + line_no only; never the raw value.
EVIDENCE: [bl-secret-001] reporter.py + redactor.py implement the URB layer
SEVERITY: CRITICAL | RECURRENCE: 0x
<!-- digest:hr-secret-002-seed01 -->
### HR-SECRET-003 -- Never auto-rotate secrets; recommend and wait for Owner
TRIGGER: Detector classifies a secret as CRITICAL during analysis, audit, or post-commit scan.
STOP: Surface a recommendation to the Owner with (a) pattern_name, (b) file:line, (c) suggested rotation provider. NEVER call provider rotation APIs autonomously. NEVER write a new credential to disk autonomously. Owner approval required for every rotation action (per OD1, sealed 2026-06-01).
EVIDENCE: [bl-secret-001] OD1 = "secret rotation = Owner-decide (no auto)"
SEVERITY: CRITICAL | RECURRENCE: 0x
<!-- digest:hr-secret-003-seed01 -->
### HR-SECRET-004 -- Never git-add .env-class files without verifying .gitignore
TRIGGER: About to stage a file named `.env*`, `*.pem`, `*.key`, `id_rsa*`, or any path under known-secret directories (e.g. `vault/secrets/`, `_secrets/`).
STOP: Verify .gitignore (or .git/info/exclude) excludes the path BEFORE staging. If the path was already tracked and is about to land in a commit, abort the commit, `git rm --cached <path>`, append to .gitignore, then redo. Owner confirmation required if the file was already pushed.
EVIDENCE: [bl-secret-001] reinforces existing deploy doctrine (HR-005)
SEVERITY: CRITICAL | RECURRENCE: 0x
<!-- digest:hr-secret-004-seed01 -->
### HR-SECRET-005 -- Never hardcode real credentials in test fixtures
TRIGGER: Writing test code under tests/, _logs/, fixtures/, or any tracked path that includes a credential-like literal.
STOP: Use synthetic test values that ARE CLEARLY FAKE: `sk-ant-` + repeating literal (e.g. 'A'*50), `sk-fake-...`. Real-format synthetic keys (e.g. `sk-ant-` + 50 alphanumerics) ARE intentionally detectable -- they SHOULD trigger the firewall in CI to prove the firewall fires. NEVER paste a real provider key into a test.
EVIDENCE: [bl-secret-001] M1 done-gate uses `sk-ant-` + ('A' * 50) explicitly to prove detection on a clearly-fake but real-shape input
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-secret-005-seed01 -->
### HR-SECRET-006 -- Never send raw secrets in additionalContext or sub-agent prompts
TRIGGER: Building additionalContext (JIT cards, gatekeeper-semantic injection, learning sentinels), hook stdout, or sub-agent prompt that may include file content or tool_input transcripts.
STOP: All such text MUST pass through redact_for_log() FIRST. Hooks emitting context (Stop-event injectors, JIT loaders, learning-sentinel summaries) must wrap user-text before serialization. Sub-agent prompts must redact tool_input transcripts before composing the Agent call.
EVIDENCE: [bl-secret-001] URB designed as the universal sieve for all egress
SEVERITY: CRITICAL | RECURRENCE: 0x
<!-- digest:hr-secret-006-seed01 -->
### HR-SECRET-007 -- Post-commit secret detection: rotate FIRST, scrub after
TRIGGER: Post-commit audit (GitHub Push Protection alert, `vault/secret_firewall/audit.jsonl` entry, dependabot scan) flags a secret that already landed in commit history.
STOP: STOP all other work. Steps in order: (1) ROTATE at the provider FIRST (Owner-authorized), (2) revoke the leaked credential at the provider, (3) THEN optionally rewrite history. Force-push only after explicit Owner go-ahead. NEVER assume rotation can wait until "after this PR". Doctrine: scrubbed history with un-rotated credentials is still a leak.
EVIDENCE: [bl-secret-001] industry-standard rotate-first-scrub-second + OD1 alignment
SEVERITY: CRITICAL | RECURRENCE: 0x
<!-- digest:hr-secret-007-seed01 -->
### HR-CASCADE-001 -- STOP before deploy if tests_passed=False
TRIGGER: Bash / PowerShell command matching `(deploy|kubectl apply|helm install|fly deploy)` without explicit verification that the relevant tests passed in this session.
STOP: Refuse to dispatch. Surface the missing-test condition with the exact command to run tests first. EXCEPCIÓN: Owner phrase "deploy without tests authorized" for ONE turn only.
EVIDENCE: [bl-cascade-001] modules/cascade_prevention/engine.py _detect_deploy -> C4 (block)
SEVERITY: CRITICAL | RECURRENCE: 0x
<!-- digest:hr-cascade-001-seed01 -->
### HR-CASCADE-002 -- STOP before rm -rf or Remove-Item -Recurse -Force without backup
TRIGGER: Bash `rm -rf <path>` (path NOT under /tmp) OR PowerShell `Remove-Item ... -Recurse ... -Force` without an explicit backup precondition.
STOP: Refuse. Require an explicit `cp -r` / `Copy-Item -Recurse` backup OR Owner override. The dangerous_cmds.py registry (M11 GAP-2) is the source of truth for the pattern set.
EVIDENCE: [bl-cascade-001] modules/cascade_prevention/dangerous_cmds.py + _detect_bash
SEVERITY: CRITICAL | RECURRENCE: 0x
<!-- digest:hr-cascade-002-seed01 -->
### HR-CASCADE-003 -- STOP before commit without verification
TRIGGER: About to invoke `git commit` without a prior successful test / lint run in the current session.
STOP: Pause. Run the verification step OR escalate to Owner with the explicit gap. Sister of HR-CASCADE-001 for the commit surface.
EVIDENCE: [bl-cascade-001] _detect_commit -> C3 when verified=False
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-cascade-003-seed01 -->
### HR-CASCADE-004 -- STOP if a CRITICAL secret appears in any emission mid-turn
TRIGGER: Any text the agent emits (response, tool output it reads, sub-agent prompt) contains a CRITICAL Secret Firewall match.
STOP: Halt. Route through redact_for_log() BEFORE further emission. Sister of HR-SECRET-002 / HR-SECRET-006; integrates the Secret Firewall (M1) + URB into the cascade engine.
EVIDENCE: [bl-cascade-001] integrates Secret Firewall + URB on the cascade surface
SEVERITY: CRITICAL | RECURRENCE: 0x
<!-- digest:hr-cascade-004-seed01 -->
### HR-CASCADE-005 -- WARN at context >= 85% / BLOCK at context >= 95%
TRIGGER: Context-usage proxy (input_tokens / max_context_tokens) crosses the threshold.
STOP: 85-94% -> surface a /compact recommendation in the closing emission (advisory, do not block). 95%+ -> refuse to start new sub-agent dispatches; finish current state in-place and request Owner-driven /compact.
EVIDENCE: [bl-cascade-001] _detect_context CONTEXT_WARN_PCT=85 / CONTEXT_BLOCK_PCT=95
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-cascade-005-seed01 -->
### HR-OUTPUT-001 -- STOP declaring DONE if output has slop tokens
TRIGGER: About to claim "done" / "ready" / "shipped" with a deliverable whose content matches an OQS slop pattern.
STOP: Refuse the DONE claim. Surface the slop hit + surrounding context so the Owner sees the gap. Aligns with the Wozniak slop-veto already enforced via PreToolUse Write hook.
EVIDENCE: [bl-output-001] modules/output_contracts/validator.py + hooks/output_contract_stop.js (advisory)
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-output-001-seed01 -->
### HR-OUTPUT-002 -- STOP declaring DONE if tests_passed=False
TRIGGER: About to claim "done" / "ship" for a code output where the relevant test suite has not been empirically observed to pass (tests_passed=False or unmeasured).
STOP: Run the test and observe a real PASS, OR demote the claim to "draft, tests pending". DONE without observed PASS violates the Reality Contract (kernel vMAX-NULL-ERROR).
EVIDENCE: [bl-output-001] OQS validator passes_test check on `tests` field
SEVERITY: CRITICAL | RECURRENCE: 0x
<!-- digest:hr-output-002-seed01 -->
### HR-OUTPUT-003 -- STOP shipping code if OQS < 70
TRIGGER: is_done(contract='code', ctx) returns (False, score) with score < OQS_DONE_THRESHOLD (70).
STOP: Block the ship. Surface the OQS score + the failing checks (missing file_path / failed syntax / failed tests / slop in content) so the Owner sees the exact gap.
EVIDENCE: [bl-output-001] OQS scorer + 4 contracts (code/docs/deploy/test)
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-output-003-seed01 -->
### HR-ONESHOT-001 -- Compile contract before any L/XL task
TRIGGER: About to start a task whose pre-estimated size is L (>$30) or XL (>$100).
STOP: Pause. Run `compile_contract(description, size)` first. Inspect scope / out_of_scope / done_gate / budget. Confirm with Owner if estimate exceeds the OD3 cap for the chosen size.
EVIDENCE: [bl-oneshot-001] modules/one_shot/compiler.py + OD3 budget table
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-oneshot-001-seed01 -->
### HR-ONESHOT-002 -- STOP if execution deviates > 40% from scope
TRIGGER: Mid-execution check: is_deviated(contract, files_touched) is True (fewer than SCOPE_DEVIATION_THRESHOLD=0.40 of touched files match scope tokens).
STOP: Pause. Surface the touched-vs-scope diff to Owner. Either extend the contract (re-compile) OR revert the out-of-scope changes.
EVIDENCE: [bl-oneshot-001] modules/one_shot/lock.py fidelity_score + is_deviated
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-oneshot-002-seed01 -->
### HR-ONESHOT-003 -- After 3 consecutive fails, STOP -- Owner decision
TRIGGER: should_stop(fail_count) is True (fail_count >= STOP_AT=3).
STOP: Stop autonomous retries. Escalate to Owner with the failing-attempt log. Companion of anti-antipatterns Rule 12 (2-consecutive-failures pivot).
EVIDENCE: [bl-oneshot-001] modules/one_shot/escalation.py + OD7 ladder
SEVERITY: CRITICAL | RECURRENCE: 0x
<!-- digest:hr-oneshot-003-seed01 -->
### HR-COST-001 -- NEVER use Opus for format/lint/rename tasks
TRIGGER: About to dispatch a task that route(description).route_class == NANO with a model other than claude-haiku-4-5.
STOP: Refuse. Re-dispatch on Haiku. Opus tokens on a rename is a self-inflicted budget hole; cost discipline is non-negotiable.
EVIDENCE: [bl-cost-001] modules/cost_collapse/router.py NANO_KEYWORDS
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-cost-001-seed01 -->
### HR-COST-002 -- STOP if estimated cost > 2x task budget
TRIGGER: Mid-task: running cost estimate (input + output token spend) exceeds 2x the contract's budget_usd.
STOP: Pause. Surface the over-budget condition. Either Owner extends the budget (re-compile_contract at a higher size class) OR collapse the task scope to fit.
EVIDENCE: [bl-cost-001] OD3 ceilings (NANO $1 / MICRO $15 / MACRO $30 / ULTRA $100)
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-cost-002-seed01 -->
### HR-COST-003 -- Route trivial tasks to Haiku by default
TRIGGER: About to start a task whose description has no MACRO/ULTRA keyword AND no specific reason to prefer Sonnet/Opus.
STOP: Apply `route(description)`; respect the routed RouteClass. Default MICRO (Sonnet) for unspecified-but-non-trivial; NANO (Haiku) for keyword-matched trivial.
EVIDENCE: [bl-cost-001] modules/cost_collapse/router.py default path
SEVERITY: MEDIUM | RECURRENCE: 0x
<!-- digest:hr-cost-003-seed01 -->
### HR-BACKLOG-001 -- Run /what-now before starting new session work
TRIGGER: SessionStart on a project with a backlog file present, about to start NEW work rather than continue prior.
STOP: Invoke /what-now (or `modules.backlog_autopilot.what_now` programmatically). Picking a P2 over an actionable P0 is a process bug.
EVIDENCE: [bl-backlog-001] modules/backlog_autopilot/engine.py + commands/what-now.md
SEVERITY: MEDIUM | RECURRENCE: 0x
<!-- digest:hr-backlog-001-seed01 -->
### HR-BACKLOG-002 -- NEVER start L/XL task without backlog check
TRIGGER: About to start a task whose size class is L (>$30) or XL (>$100) without consulting the project's backlog.
STOP: Refuse. Run /what-now first. Confirm the task is the recommended item OR Owner-explicitly-authorized despite the recommendation.
EVIDENCE: [bl-backlog-001] enforces the spirit of OD3 budget discipline
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-backlog-002-seed01 -->
### HR-BACKLOG-003 -- STOP if new task would block a P0 item
TRIGGER: About to start new BacklogItem when the backlog has at least one P0 item that is currently actionable (not done, not blocked).
STOP: Refuse the lower-priority work. Surface the P0 contention. Either Owner explicitly defers the P0 OR you flip the queue.
EVIDENCE: [bl-backlog-001] what_now() filtering + priority scoring
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-backlog-003-seed01 -->
### HR-PREMISE-001 -- Verify file/function premises before executing a plan
TRIGGER: About to act on a plan that names specific file paths, module functions, classes, or APIs that have NOT been verified to exist in THIS repo.
STOP: Run modules.error_prevention.assert_premises([...]) (or python modules/error_prevention/premise_verifier.py --premises -) FIRST. A failing premise returns the REAL public API as the correction. Never write code against an assumed signature. EXCEPCION: Owner phrase "premises verified -- HR-PREMISE-001 OK" for ONE turn. ORIGEN: a plan asserted a 4-param compile_contract that does not exist (real signature is 2-param, description+size).
EVIDENCE: [bl-premise-001] modules/error_prevention/premise_verifier.py + verify_spp premise-verifier row
SEVERITY: HIGH | RECURRENCE: 1x
<!-- digest:hr-premise-001-seed01 -->
### HR-SPEC-001 -- L/XL task requires a spec gate check before coding
TRIGGER: About to start coding an L (>$30) or XL (>$100) task without checking whether a spec exists in the repo.
STOP: Run modules.spec_gate.check_spec_gate(desc, cwd, "L"|"XL"). gate_passed=False (action=create_spec) means establish a spec FIRST -- the auto-injected One-Shot contract (scope+done-gate) or the karimo PRD parser. S/M tasks are exempt. EXCEPCION: Owner phrase "spec gate waived -- HR-SPEC-001 OK" for ONE turn.
EVIDENCE: [bl-spec-gate-001] modules/spec_gate/gate.py + one_shot compiler advisory + skill_router spec domain
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-spec-001-seed01 -->
### HR-CONTEXT-001 -- Verify a plan's output files exist before declaring complete
TRIGGER: About to declare a multi-file plan "complete"/"done"/"shipped" when the plan's promised output files have NOT been verified to exist on disk.
STOP: Check every planned output -- assert_premises([{"type":"file_exists","path":p} for p in planned_outputs]). A "done" claim whose artifacts are absent is the Scaffold Illusion (Mistake #16). DONE = files exist AND a V-gate observed them working.
EVIDENCE: [bl-premise-001] premise_verifier.verify_file_exists + Reality Contract (kernel vMAX-NULL-ERROR)
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-context-001-seed01 -->
### HR-STALLED-SESSION-ADVISORY-001 -- Stalled/unbounded session is advisory only; never auto-kill
TRIGGER: The Process Hibernation governor (modules/cognitive_os/process_governor.py loop_advisory) flags a pane STALLED (no output >30min AND session >1h total) or UNBOUNDED (active >2h without a /compact reset).
STOP: Surface a VISIBLE advisory to the Owner ONLY. NEVER change the hibernate/keep verdict and NEVER auto-kill a process -- a long-running pane may be real continuous work; the Owner decides /kclear or close. Fail-open: unmeasurable session age -> silence (never a false positive). EXCEPCION: none -- no phrase authorizes auto-killing on a stall/unbounded signal.
EVIDENCE: [kickbacks] a session hung ~10h undetected caused the Kickbacks suspension (2026-07-04); loop-boundedness added to the governor as a VISIBILITY net, never an autonomous kill. Sealed SCS C75; UKDL T-UNBOUNDED-SESSION-001.
SEVERITY: HIGH | RECURRENCE: 1x
<!-- digest:c442a805144bbe7b -->
### HR-PANE-MAP-FRESHNESS-001 -- The pane_map is the only post-crash recovery mechanism; freshness is a production requirement
TRIGGER: Relying on ~/.claude/state/pane_map.md/.json for pane recovery, OR classifying a pane as LIVE.
STOP: (1) Freshness: the pane_map MUST be regenerated on a bounded cadence (PP-PaneMapUpdate scheduled task, every 5 min + onlogon). If it is stale > 5 min during active sessions the recovery net has already failed -- regenerate before trusting it. (2) Liveness: NEVER classify LIVE by file mtime -- a batch sweep (heartbeat merger, backup, git checkout, AV) rewrites transcript mtimes en masse and forges false-LIVE. Classify by the transcript's INTERNAL last-message timestamp OR the snapshot live-registry only. EXCEPCION: none.
EVIDENCE: [rca 2026-07-06] Cursor crash -> pane_map 8 days stale (no scheduled task registered, only the Cursor extension regenerated it). Regen showed 30 "LIVE"; internal-timestamp forensics proved only 1 genuinely live (this session) + 35 files sharing one mtime spike ~11 min old while their real last turn was 14h-7d old. Fix: build_pane_map.ps1 Get-LastInternalAgeMin + PP-PaneMapUpdate task. UKDL T-PANE-MAP-STALENESS-ROOT-CAUSE-001 + T-PANE-MAP-FALSE-LIVE-MTIME-001. Sealed SCS C79.
SEVERITY: HIGH | RECURRENCE: 1x
<!-- digest:pane-map-freshness-001 -->
### HR-REVIVAL-LIVENESS-IS-PROCESS-001 -- A pane is open only when a process proves it; never by recency or registry membership
TRIGGER: Deciding whether a pane is OPEN -- classifying a tier in build_pane_map.ps1, filtering panes in vscode_autorun.generate_from_snapshot, or writing any .vscode/tasks.json folderOpen entry.
STOP: Prove openness with a RUNNING process: a kclaude beacon in %TEMP% whose pid still blocks on WaitForSingleObject(h, 0) == WAIT_TIMEOUT. OpenProcess succeeding is NOT liveness -- the handle-table entry outlives the process, so a corpse reads as alive. Snapshot membership is not liveness either; snapshot._LIVE_STATUSES includes "stale". Idle time is not liveness: a pane idle for days may be open and one active a minute ago may be gone. Fail-open: zero measurable beacons means "cannot measure" -> filter nothing. EXCEPCION: none.
EVIDENCE: [rca] A 120-minute idle ceiling was measured against the live host before shipping and would have dropped three genuinely-open panes idle 2, 6 and 8 days -- the Owner contract is that a pane lives as long as Cursor does. A same-moment cross-check of the two liveness implementations returned 14 sids vs 12; the two extras were exited processes admitted by OpenProcess alone.
SEVERITY: CRITICAL | RECURRENCE: 1x
<!-- digest:revival-liveness-is-process-001 -->
### HR-REVIVAL-BEACON-COVERS-NEW-SESSIONS-001 -- Never gate panes on a signal that structurally cannot cover new sessions
TRIGGER: Adding or tightening any filter that drops panes from tasks.json based on a liveness beacon, or narrowing a writer's tier set toward beacon-only.
STOP: Verify the signal covers sessions created FRESH, not only resumed ones. kclaude.ps1 can beacon only a session whose id it knows at launch (--resume); a new session has no id until Claude Code mints one. The SessionStart hub closes this via modules/cpc_os/beacon.py, which walks to the ancestor claude.exe -- if that path is removed or fails, beacon-only filtering silently deletes exactly the panes worth keeping. Keep the content-age tiers as the compensating fail-open until coverage is PROVEN for both session origins. EXCEPCION: none.
EVIDENCE: [measured] 23 folderOpen tasks existed against 5 beacons; the session the Owner was typing in had no beacon of its own and a beacon-only gate dropped it in dry-run -- shipping it would have reproduced the reported bug. V-BEACON-NEW-SESSION pins writer/reader parity.
SEVERITY: CRITICAL | RECURRENCE: 1x
<!-- digest:revival-beacon-covers-new-001 -->
### HR-REVIVAL-STALE-TASK-IS-A-PUMP-001 -- Never fix a stale folderOpen task by deleting it
TRIGGER: A .vscode/tasks.json holds a folderOpen task for a session that is dead, wrong, or duplicated, and the intended fix is to delete the task or hand-edit the file.
STOP: Deleting it fixes nothing -- the next writer cycle regenerates it. Acting on the record RE-CREATES the record: resuming a dead session re-registers it as a fresh pane, which re-classifies it OPEN-NOW, which rewrites the task. Fix the CLASSIFIER that admitted it, then let the writer converge. A hand-edit is undone within one scheduled cycle and reads as "the fix did not hold". EXCEPCION: none.
EVIDENCE: [rca] A session confirmed clean_exit five days earlier kept relaunching its own terminal tab on every folder open; the scheduled writer restored the task minutes after each manual deletion, which is why several prior fix attempts appeared to fail at random.
SEVERITY: HIGH | RECURRENCE: 1x
<!-- digest:revival-stale-task-is-a-pump-001 -->
### HR-REVIVAL-GHOST-BUFFER-NOT-RESUME-001 -- Restored scrollback is not a restored session; never accept it as evidence revival works
TRIGGER: Judging whether session revival works, from a terminal that shows prior conversation history after a Cursor restart.
STOP: Confirm the PROCESS, not the pixels. terminal.integrated.persistentSessionReviveProcess repaints the old scrollback and launches a BRAND-NEW shell underneath it, so correct history above an empty session is the expected output of that setting, not a partial success. Require the setting at "never" and require the folderOpen task to have run kclaude --resume with a real session id. Also: terminal.integrated.restoreTerminals is not a real Cursor setting and is inert -- never add it and never read it as proof restore is off. EXCEPCION: none.
EVIDENCE: [owner report] The reported symptom was verbatim "revivia el historial correcto pero me mandaba a escribir a una sesion nueva y vacia"; the inert restoreTerminals key made terminal restore look disabled while it was fully active, misdirecting three prior fix attempts.
SEVERITY: HIGH | RECURRENCE: 1x
<!-- digest:revival-ghost-buffer-not-resume-001 -->
### HR-REVIVAL-VERIFY-AFTER-CURSOR-UPDATE-001 -- After a Cursor update, verify the revival settings before diagnosing anything
TRIGGER: Cursor has updated, or its settings UI was used, and revival is being investigated or declared healthy.
STOP: Run tools/test_session_revival.py and require REVIVAL_PASS at full count BEFORE forming any hypothesis. An update can reset task.allowAutomaticTasks to "off", which kills every folderOpen task silently -- no error, no log, and the only symptom is that revival became flaky again. Restore the exact key V-SETTINGS-REQUIRED names rather than re-deriving the pipeline. EXCEPCION: none.
EVIDENCE: [incident] An allowAutomaticTasks reset cost a full diagnosis cycle before the reset itself was found; the gate now pins allowAutomaticTasks, persistentSessionReviveProcess, enablePersistentSessions and restoreWindows as a tripwire.
SEVERITY: HIGH | RECURRENCE: 1x
<!-- digest:revival-verify-after-cursor-update-001 -->
### HR-NOVELTY-001 -- Require the 13-question novelty proof before admitting a new institutional mega-system
TRIGGER: A proposal to build a new "fabric", "compendium", institutional operating system, kernel, civilization, governance layer, or intelligence platform (`modules/spec_gate/gate.py::check_novelty_gate`).
STOP: Refuse GENUINELY_NEW_DATASET status until all 13 questions (problem owner gap, new outcome, real consumer, extension insufficiency, new primitive, new decisions, new evidence, failure class prevented, interfaces with existing owners, value measurement, complexity introduced, retirement condition, why-not-rhetorical-layer) are answered with cited file:line evidence from a DISCOVERED sweep of the repo -- never from the proposal's own curated list of what it assumes doesn't exist. Missing evidence on any question -> classify as EXTEND_EXISTING_OWNER, NEW_MODULE, NEW_VIEW, NEW_POLICY_PACK, NEW_SCANNER_OR_GATE, or REJECT instead. EXCEPCION: Owner phrase "novelty proof waived -- HR-NOVELTY-001 OK" for ONE turn.
EVIDENCE: [iig-compendium-2026-07-30] 6 consecutive mega-corpus proposals for this repo (AISHF, RE Baseline's 3 NEW families -> 1 (CLAE), KSF's 22 -> 4-deferred, the UKR Compendium's 8-step escalation -> 0, this IIG pass's 30 candidates A-AD -> 0) measured as majority-or-fully owned once checked against a discovered denominator instead of the proposal's own list. `vault/plans/iig-compendium-2026-07-30.md`.
SEVERITY: HIGH | RECURRENCE: 6x
<!-- digest:novelty-proof-required-001 -->
<!-- PP-HARD-RULES-END -->
