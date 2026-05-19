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
