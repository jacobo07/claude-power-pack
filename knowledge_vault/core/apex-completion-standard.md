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
