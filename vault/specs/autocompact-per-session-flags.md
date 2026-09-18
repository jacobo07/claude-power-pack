---
covers: [auto-compact-trigger, auto-compact-sendkeys-daemon, per-session-flag, cpp-gsd-long-concurrent]
date: 2026-09-18
tier: T2
---

# Auto-compact Enter dispatch: one flag per session

## Problem (measured)
`context-watchdog.py` wrote ONE global `~/.claude/hooks/auto-compact-trigger.flag`.
The SendKeys daemon sent Enter into whatever Cursor window was focused, and when a
pending flag already existed it DISCARDED the new trigger
(`auto-compact-sendkeys-daemon.ps1:121`). With two `/cpp-gsd-long` runs, a second
concurrent compaction lost its Enter and that run stalled.

## Change
1. Watchdog writes `auto-compact-trigger-<session_id>.flag` (payload unchanged:
   ts, session_id, used_pct, cwd).
2. Daemon globs `auto-compact-trigger*.flag` / `auto-compact-pending*.flag`
   (legacy names included). Nothing is discarded; demotion is per file.
3. Routing, when Cursor is foreground (window title `<root> - Cursor`):
   - flag whose cwd leaf == foreground root -> send (oldest first);
   - flag whose cwd leaf is the root of ANOTHER open Cursor window -> wait;
   - flag whose project has no open Cursor window -> send (legacy behaviour);
   - at most one Enter per window until focus leaves that window and returns.
4. Launcher and SessionStart cleanup use the same globs; stale age 10 -> 30 min
   so a flag legitimately waiting for focus is not reaped by another session.
5. Test seam: `AC_DAEMON_DRYRUN=1` logs `WOULD-SEND` instead of SendKeys;
   `AC_DAEMON_DIR`, `AC_DAEMON_FAKE_FG`, `AC_DAEMON_FAKE_WINDOWS`, `AC_DAEMON_TTL`
   override inputs. Production never sets them.

## Acceptance
- two trigger flags never collapse into one; both are eventually dispatched;
- a flag for project B is not sent while project A's window is focused and B has
  its own window;
- a single flag with no matching window is sent as before (no regression);
- a second Enter into the same window requires a focus change in between.
Gate: `tools/test_autocompact_per_session.py`.

## Not solved
Two runs inside ONE Cursor window (two terminal tabs) are indistinguishable from
Win32; the focus-change rule limits misfire but cannot route by tab.

## Rollback
Restore the three .ps1 from `~/.claude/hooks/_bak_autocompact_20260918/` and revert
the watchdog hunk.
