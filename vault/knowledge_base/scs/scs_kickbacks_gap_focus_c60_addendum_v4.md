# SCS C60 addendum v4 -- KickbacksGuard: window-focus gap detection

**Sealed:** 2026-07-06
**Component:** `tools/kickbacks_guard.ps1`
**Cross-ref:** UKDL `T-KICKBACKS-GAP-PATTERN-001`, `T-KICKBACKS-UI-DEATH-NO-DISK-SIGNAL-001`

## Root cause finally identified

Periodic Kickbacks billing gaps (impressions stop while the extension is visually
active) are **window-focus-gated billing behaving as designed** -- not a local fault.
Dashboard label: "100% billed while focused". `vibe-ads-statusline.mjs` is a pure
renderer (no impression report), so accounting is entirely inside the closed extension
+ backend, which bills only while Cursor is the foreground window.

Why prior forensics missed it: every local signal is GREEN during a real gap.
2026-07-06 evidence (gap 13:43-14:13Z): auth.refresh 6/6 ok, vsix consecutiveFails=3,
session.state signedIn:true killed:false hasAd:true, canary absent. The debug.log
records NO focus / impression / billing / serving events -- there was no local signal
to find, so canary/auth/vsix audits (all local) always came back clean.

## What shipped (KickbacksGuard v4)

Two new fail-open, advisory-only invariants (never auto-act; HR-STALLED-SESSION-ADVISORY-001):

- **INV-FOCUS** -- Win32 `GetForegroundWindow` -> process name. When Cursor is running
  but not foreground for >= `FocusLossMinutes` (5), raise a toast + durable flag
  (`kickbacks_focus_lost.flag`) and clear it on regain. Anchored on a known-focused
  sample so the first unfocused sample can't fire; throttled 30 min; **indeterminate
  foreground (HWND 0 / unresolvable pid) -> SILENCE**, so it can never false-alarm.
- **INV-AUTHSTREAK** -- trailing `auth.refresh` ok:false streak >= `AuthFailStreak` (5)
  with the last outcome still a failure -> warn before the session drops. Dormant when
  the last auth.refresh is ok (today: streak 0).

Guard runs `LogonType=InteractiveToken`, so the foreground query is valid.

## Verification (4/4, foreground observed)

| Scenario | Expected | Observed |
|---|---|---|
| plain run | billing-eligible, no flag | `FOCUS: Cursor foreground -- billing eligible`, flag absent |
| `-SimulateUnfocused` | toast + flag written | `toast=True, flag written` (fg=Brave) |
| plain run again | flag cleared on regain | `FOCUS: regained -> flag cleared`, flag absent |
| `-SimulateAuthStreak` | warn | `WARN: Kickbacks auth.refresh fallando (99 seguidos)` |

## Honest limitation

PP cannot force window focus, re-authenticate, or fix the backend. The only mitigation
is DETECT + visible advisory. If the Owner legitimately works in another app, the focus
advisory is expected (not a bug) -- it exists to make an otherwise-invisible billing
suppression visible, so the Owner can choose to return focus to Cursor.
