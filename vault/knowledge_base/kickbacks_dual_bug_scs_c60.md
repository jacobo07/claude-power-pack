# SCS C60 — Kickbacks dual-bug mitigation (boot-canary false positive)

**Sealed:** 2026-06-30. Extends the statusline/Kickbacks sprint (commits 6793f42
"fix context bar under Kickbacks chain", c05486a "self-healing guard", 562eb91
"detect signed-out + toast"). That sprint was never sealed with a C-number; the
prompt's "SCS C54" did not exist (latest was C59) — sealed here as **C60** to
avoid collision. Honest correction logged per the audit-disproves-premise rule.

## What broke (two symptoms, one root cause)

1. **Patch activation failed** — on opening Cursor: *"prior activation didn't
   complete cleanly — skipping automatic patch this run. Click the status bar to
   manually re-enable…"*. Kickbacks did not patch the Claude CLI that run.
2. **Green earnings status bar hides intermittently** — the `Kickbacks $X today`
   indicator blanks now and then.

**Confirmed root cause (read from `dist/extension.js`, not speculation):** the
`bootCanary` mechanism. Kickbacks writes `~/.vibe-ads/boot.canary` at activation
start and self-deletes it 5 s later via an `.unref()`'d `setTimeout` (`SETTLE_MS
= 5000`). A Cursor reload / activation-cancel within those 5 s (logged repeatedly
as `activate.fatal {"msg":"Canceled","stack":"Canceled: Canceled"}`) drops the
unref'd timer, so the canary survives. The next activation within 90 s
(`CANARY_STALE_MS`) reads the stale canary → `canaryFromCrash=true` →
`suspendServing()` → `servingVerdict()="freeze"` → `canPatch()=false` (Bug 1:
patch skipped + warning toast) **and** the earnings `StatusBarItem` blanks
(Bug 2). Both symptoms are the SAME false positive. Trigger is rapid Cursor
window reloads / ungraceful shutdown / a Kickbacks self-update (it auto-updated
2026-06-27: build `2026-06-13` → `2026-06-27`, dir mtime 27/06).

## Mitigation (PP side only — Kickbacks code never touched)

- **INV-CANARY** added to `tools/kickbacks_guard.ps1` (the existing scheduled-task
  guard, `PP-KickbacksGuard`, every 2 min + at logon, verified running, repo copy =
  live copy). Reaps a `boot.canary` older than 15 s (past the 5 s settle window, so
  never a live in-flight activation; real boots settle <5 s). This pre-empts the
  false positive on the *next* reload and breaks the repeating notification cycle.
  Fail-open.
- **`~/.claude/state/kickbacks_recovery.md`** documents the exact owner-side
  recovery: click the status bar (`kickbacks.debugMenu`) or Command Palette →
  `Kickbacks: Restore Claude Code` (`kickbacks.restore`); last resort delete the
  stale canary + Reload Window.

## Honest limits

- The PP **cannot** pre-empt the very first occurrence in the seconds right after a
  rapid reload — that race lives entirely inside Kickbacks' 5 s settle window. The
  guard shortens any leftover-canary window to ≤2 min and stops recurrence.
- The PP **cannot** force Kickbacks' own earnings `StatusBarItem` to show; only the
  suspend trigger is removable. The transient blink during each re-activation is
  inherent to Kickbacks and is documented, not faked.
- The trigger (Cursor window reloads / ungraceful shutdown / Kickbacks self-update)
  is mostly outside PP control — `/restart` restarts `claude.exe` in-pane and does
  NOT reload the Cursor window, so it does not cause this. Hence the A1 "hub waits
  for boot.cycle" timing idea is **not reliably applicable** (the hub runs in the
  terminal after Kickbacks has already activated) and was correctly not built.

## Verify

- `powershell -File tools/kickbacks_guard.ps1 -SelfTest` → `bar=True ad=True`.
- Guard reaps a stale canary: drop a >15 s-old `~/.vibe-ads/boot.canary`, run the
  guard → `HEALED: canary(reaped stale boot.canary …)`.

Cross-ref: UKDL `T-KICKBACKS-BOOT-CANCELED-001`, `PR-STATUSLINE-GUARD-ALWAYS-001`.
