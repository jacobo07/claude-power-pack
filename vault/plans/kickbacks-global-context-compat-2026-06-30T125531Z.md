# Plan — Kickbacks guard global scope + context-% compat check

**Date:** 2026-06-30 · **Mode:** EXECUTION · **Backup of inline plan.**
Follow-up to SCS C60 (commit b9148de). **No code change** — both questions resolved
by verification + documentation.

## GLOBAL SCOPE REPORT

- **Task trigger:** at-logon + 2-min interval, run-as user `User`, Estado=Listo
  (`schtasks /query /tn PP-KickbacksGuard /v`). NOT bound to any Cursor process/workspace.
- **Canary path:** `~/.vibe-ads/boot.canary` — **unique per Windows user**, shared by
  all Cursor windows (Kickbacks uses one `~/.vibe-ads/` for every window).
- **Status bar repo A / repo B:** render is driven by per-user `~/.vibe-ads/` state, not
  by the open repo — demonstrated by running the real chain across 3 distinct
  `current_dir` values (repoA/B/C); ad rendered in all.
- **Verdict:** the guard is **already global by design**. No adjustment needed (BLOQUE A1).
  Honest coupling: the script file must exist on disk (PP repo dir), but the repo need
  not be open.

## CONTEXT-PERCENT COMPAT REPORT

- **Chain order:** vibe-ads ad FIRST (synchronous `writeSync`), THEN PP HUD
  (`gsd-statusline.js`) spawned isolated (5s timeout, never-throws).
- **HUD error handling:** try/catch present; `context_window.remaining_percentage` via
  optional chaining + `if (remaining != null)` → missing/null context OMITS the % segment,
  never crashes.
- **If the HUD fails:** failure is **isolated** — only the HUD line drops; the ad is
  already on the pipe.
- **Owner hypothesis confirmed?** **NO.** Empirical (real chain, 4 payloads): ad present
  in ALL 4 — normal (ad+46%), no `context_window` (ad), `context_window:null` (ad),
  garbage stdin → HUD `JSON.parse` THROWS (ad). The green `$X today` earnings bar is a
  separate Cursor `StatusBarItem` (boot-canary path, already fixed in b9148de).

## Blocks executed

- **A1:** documented global scope in `~/.claude/state/kickbacks_recovery.md` + UKDL. No code.
- **A2:** not triggered (task already global).
- **B1:** not applicable — chain already isolated (hypothesis disproven).
- **B2:** documented honestly; no invented fix (constraint: don't fix a non-defect).
- **C1:** multi-dir render proof (3 `current_dir` values) — empirical proxy for multi-repo.
- **D1:** UKDL `T-KICKBACKS-GUARD-GLOBAL-001` + `T-STATUSLINE-CHAIN-ISOLATED-001`.
- **D2:** SCS C60 addendum (this file's seal target).
- **D3:** git commit (pathspec-scoped) + push → REMOTE_DELTA 0 0.

## Constraint honored

Kickbacks code never modified. No fix invented for a non-confirmed hypothesis. All
findings backed by code + empirical evidence, not speculation.
