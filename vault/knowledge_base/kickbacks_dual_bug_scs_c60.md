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

---

## C60 addendum (2026-06-30) — global scope confirmed + context-% hypothesis disproven

Follow-up EXECUTION on two Owner questions. **No code change** — both resolved by
verification + documentation.

### 1. Guard is system-global (confirmed)

The INV-CANARY/CHAIN/SETTINGS/AUTH guard covers **all** Cursor windows, not just the
one with the PP repo open:
- Kickbacks keeps a SINGLE per-user `~/.vibe-ads/` for every window (`boot.canary`,
  `cli-ad.json`, `cli-prev-statusline.json` are per-user, not per-workspace) → reaping
  those paths heals every window at once.
- `PP-KickbacksGuard` is a USER-level scheduled task (verified
  `schtasks /query /tn PP-KickbacksGuard /v`: Estado=Listo, trigger at-logon + 2-min,
  run-as User), invoking `powershell -File "…\tools\kickbacks_guard.ps1"` regardless of
  what is open. Honest coupling: the script FILE must exist on disk (PP repo dir), but
  the repo need not be OPEN. UKDL `T-KICKBACKS-GUARD-GLOBAL-001`.

### 2. Context-% ↔ ad compatibility (hypothesis DISPROVEN)

Owner hypothesis: a context-% read failure hides the whole statusline including the
ad. **False, with code + empirical evidence.** The line is one invocation
(`vibe-ads-statusline.mjs`) that prints the ad FIRST (synchronous `writeSync`), THEN
spawns the PP HUD (`gsd-statusline.js`) isolated (5s timeout, never-throws). The HUD
omits the % segment via optional chaining + `if (remaining != null)` when context is
absent; a HUD that throws drops only its own line. Real-chain test, 4 payloads — ad
present in ALL: normal (ad+46%), no `context_window` (ad), `context_window:null` (ad),
garbage stdin → HUD `JSON.parse` throws (ad). No defect → no fix (constraint honored).
The green `$X today` bar is a separate Cursor `StatusBarItem` (boot-canary path, fixed
in b9148de), not this terminal chain. UKDL `T-STATUSLINE-CHAIN-ISOLATED-001`.

### Verify (addendum)

- `schtasks /query /tn PP-KickbacksGuard /v` → Estado=Listo, logon+interval, run-as User.
- Chain isolation: pipe garbage stdin through `vibe-ads-statusline.mjs` → ad line still
  prints (HUD segment absent). Repeated across 3 distinct `current_dir` values → render
  is per-user-state, not per-repo.
