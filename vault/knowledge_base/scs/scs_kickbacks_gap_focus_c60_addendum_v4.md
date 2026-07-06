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

---

# SCS C60 addendum v5 -- focus DISPROVEN; render-staleness is the true earning gate

**Sealed:** 2026-07-06 (same day, follow-up)
**Supersedes the ROOT CAUSE of v4** (INV-FOCUS demoted to secondary net; code kept).

## Correction

v4 named window focus the primary cause. The Owner checked the dashboard: **Window focus
100% green, gap happened WITH Cursor focused.** Focus disproven.

## True root cause (elimination)

During the gap the extension had `hasAd:true` throughout (not timer-billing) and focus was
green (not focus-gated) -- every local signal green. The only remaining gate is the ad
actually RENDERING. The CLI ad is drawn by the statusline, which Claude Code re-invokes only
on activity; idle panes (even focused) stop rendering -> ad stops -> impressions pause.

**Proof:** `gsd-statusline.js` rewrites `%TEMP%/claude-ctx-<sid>.json` per render. Newest
mtime across live sessions:

```
15:42  renders=11   (Cursor resume burst)
15:45  renders=1    <- last dense render == dashboard Activity Ledger last row (15:45)
15:57  renders=1    <- then sparse: 12/16/10-min gaps == the reported gap
16:13  renders=1
16:46  renders=8    (session active again)
```

Render activity == billing activity. Gaps are CC-idle windows, orthogonal to focus.

## Shipped (KickbacksGuard v5)

- **INV-RENDER [authoritative]** -- newest UUID-named `claude-ctx-*.json` mtime; stale >=
  `RenderStaleMinutes` (10) while Cursor runs -> advisory + flag "ejecuta un prompt para
  reanudar el billing". Fail-open: no bridge -> silence. Verified 3/3.
- INV-FOCUS demoted to secondary explainer (kept, not authoritative).

## HARD ETHICAL LINE

PP MUST NEVER auto-invoke the statusline to fake a render -- that manufactures ad impressions
for an advertiser = **fraud**. The only honest lever is VISIBILITY so the Owner resumes by
actually using Claude Code. This is why INV-RENDER only advises; it never renders.

---

# SCS C60 addendum v6 -- render-staleness DISPROVEN; INV-RENDER RETRACTED

**Sealed:** 2026-07-06 (same day, second follow-up)
**Retracts the v5 detector.**

## Correction

v5 shipped INV-RENDER on `%TEMP%/claude-ctx-<sid>.json` bridge staleness. The Owner reported he
was actively prompting Claude 15:45-16:27 -- continuous renders -- yet the bridge mtimes were
sparse (10-16 min gaps). Impossible if the bridge tracked renders.

## Why the bridge is not a render/impression proxy (live probe)

The bridge is written by `gsd-statusline.js` (HUD chained below the ad) ONLY when the CC
statusline payload has `context_window.remaining_percentage`:

| probe payload | ad prints? | bridge written? |
|---|---|---|
| with `remaining_percentage` | yes | yes |
| WITHOUT it (null ctx) | **yes** | **no** |

So a null-context render displays the ad (impression) but leaves no bridge. Wild proof: active
session `029d13b9` (InfinityOps) ran with zero bridges ever. Bridge-staleness is a measurement
artifact of the `remaining!=null` gate -> a detector on it false-alarms during active use.

## State after this turn

- INV-RENDER retracted to an inert note (params retained, unused). Guard parse OK, ASCII-clean.
- INV-FOCUS kept as a secondary net; fixed a TZ bug (UTC read) that made its age go negative.
- INV-AUTHSTREAK / INV-VSIX / INV-CANARY unchanged.

## Honest standing conclusion

Config is global + uniform; the ad was almost certainly rendering during the gap. The ad render
leaves NO local trace, so there is NO reliable local impression proxy today -- impression
accounting is extension-internal (closed). Focus, render-staleness, auth, vsix, canary are ALL
disproven for this gap. The only ground-truth instrument left is an ungated per-invocation log
at the top of `gsd-statusline.js` (Owner-gated, hot path, deferred). Meta-lesson (Rule 12): stop
shipping detectors on unvalidated proxies -- instrument for ground truth first.
