# Plan — Kickbacks dual bug (patch activation failed + status bar hidden)

**Date:** 2026-06-30 · **Mode:** EXECUTION · **Backup of inline plan.**

## Diagnosis (DUAL BUG REPORT)

- **Bug 1 cause:** boot-canary false positive. `~/.vibe-ads/boot.canary` survives a
  Cursor reload/cancel within Kickbacks' 5 s `.unref()` settle timer
  (`activate.fatal {"msg":"Canceled"}`); next activation <90 s reads it as a crash →
  `suspendServing()` → patch skipped. CONFIRMED in `dist/extension.js` bootCanary.
- **Bug 1 re-enable command:** status bar click = `kickbacks.debugMenu`; canonical
  fix = Command Palette → `Kickbacks: Restore Claude Code` (`kickbacks.restore`).
- **Bug 2 cause:** SAME root cause — `suspendServing()` freezes serving and the
  earnings `StatusBarItem` blanks; plus a transient blank each re-activation
  (`signedIn:false/hasAd:false` window). Kickbacks auto-updated 27/06 (build 06-13
  → 06-27), which is one trigger for the reload churn.
- **SessionStart guard active:** the guard runs via scheduled task `PP-KickbacksGuard`
  (every 2 min + at logon), State=Ready, LastResult=0 — strictly dominates a
  SessionStart-only hook (the register script's deliberate design). No SessionStart
  hook for statusline exists; the prompt's premise was corrected.
- **PP mitigation possible:** YES — INV-CANARY reaper in the existing guard +
  recovery doc. Partial for Bug 1's first hit (Kickbacks-internal race); full for
  recurrence + the context-bar chain.

## Blocks executed

- **A1:** timing mitigation NOT built — not reliably applicable (documented honestly).
- **A2:** `~/.claude/state/kickbacks_recovery.md` with exact re-enable commands.
- **B-root (covers A1 intent + B1/B2):** INV-CANARY reaper added to
  `tools/kickbacks_guard.ps1`; runs every 2 min, idempotent, fail-open.
- **C1:** UKDL `T-KICKBACKS-BOOT-CANCELED-001` + `PR-STATUSLINE-GUARD-ALWAYS-001`.
- **C2:** SCS **C60** (prompt's "C54" did not exist; latest was C59).
- **C3:** git commit (pathspec-scoped) + push → REMOTE_DELTA 0 0.

## Constraint honored

Kickbacks code never modified. All mitigation is PP-side file/guard only, fail-open.
