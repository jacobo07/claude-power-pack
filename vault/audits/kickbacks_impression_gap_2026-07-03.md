# Kickbacks Impression Gap — Forensic Audit (2026-07-03)

**Verdict: HYPOTHESIS DISCARDED.** The "orphan boot.canary → freeze → reporting cut"
theory is NOT supported for today's 12:08 (local) impression gap. No PP-side defect;
the earning path is demonstrably healthy. Recommendation: report the dashboard
contradiction to Kickbacks; the gap is best explained by low active-Claude-Code time
+ heavy session churn, not a freeze.

## Symptom (as reported)
- Dashboard `kickbacks.ai/me` "Ad mode mix" widget: *"No ad impressions in last 24 hours"*.
- Same dashboard event history: **142 impressions today**, last at **12:08 local** (= 10:08 UTC), none since.
- Today's revenue **$0.828** vs **$40.24 / 7 days** (~$5.75/day avg) → today is a low outlier.

## Investigation (evidence-first)
Environment: Windows, Brave profile, `~/.vibe-ads/` CLI. Log = `~/.vibe-ads/debug.log`
(UTC, `Z`). NOW at analysis = 2026-07-03T13:27 local / 11:27Z. Log is live (last line ≈ now).

### What the log's real event vocabulary is
`activate`, `session.state {signedIn,authHealthy,injectionOn,killed,hasAd,ccVersion}`,
`boot.cycle.start/done`, `preflight`, `auth.loadCached`, `auth.refresh {ok,rotated}`,
`activate.fatal {Canceled}`, `cli.spinnerVerbs`, `selfupdate.*`.

### Hypothesis terms vs reality
- `canary` / `suspendServing` / `servingVerdict` / `freeze` → **0 occurrences** in the entire debug.log.
- **Correction (honest):** those are *internal function names inside Kickbacks `dist/extension.js`*
  (bootCanary, SETTLE_MS=5000, CANARY_STALE_MS≈90s), documented in `tools/kickbacks_guard.ps1`
  lines 170–180. The extension does **not** log those state transitions, so "0 occurrences"
  does not by itself disprove the mechanism — it had to be tested via observable proxies.

### Observable-proxy tests (the actual evidence)
1. **`boot.canary` absent now** (checked 13:24 local) → no active orphan-freeze at this instant.
2. **PP-KickbacksGuard**: `Habilitado` / `Listo`, last result `0`, runs every ~2 min. Log window
   11:22/11:24/11:26Z all `healed=[] warns=[] notes=[]` → no canary reaped, no signed-out,
   no chain break for the whole period. INV-CANARY mitigation is operational.
3. **Ad pipeline healthy after the 12:08 cutoff**: `signedIn:true, authHealthy:ok,
   injectionOn:true, killed:false, hasAd:true` reached repeatedly 10:44–11:03Z
   (= 12:44–13:03 local). A frozen/suspended server would not keep reaching `hasAd:true`.
4. **Guard self-test NOW**: `selftest bar=True ad=True` → the ad + earnings-bar statusline
   chain renders end-to-end at 13:27 local.
5. **`cli-ad.json` age = 0.3 min** → the ad is actively refreshing (guard's earning proxy = OK).
6. **auth healthy**: `auth.refresh {ok:true,rotated:true}` repeatedly today; INV-AUTH not flagging.

### The 12:08 cutoff, correlated
At 10:08Z (12:08 local) the CLI was **idle** — the only surrounding events are `auth.refresh`
+ `selfupdate.failed` housekeeping; **no `activate` / no injection** between 10:08Z and 10:44Z
(12:08–12:44 local). Impressions accrue only while an **active Claude Code session renders the
ad statusline**. The cutoff coincides with an idle window, **not** a canary/freeze event
(there is none at that timestamp; the only `boot.cycle.done reason:"already patched; no pristine
backup"` events are 06-29/06-30, not 07-03).

## Root cause (best-supported)
1. **Low active-Claude-Code statusline time + heavy session churn today.** The log shows
   idle gaps plus rapid `activate → activate.fatal{Canceled} → re-activate` cycles (Cursor
   reloads / `/restart` tooling tearing sessions down inside the settle window). Fewer steady
   statusline-minutes ⇒ fewer impressions ⇒ lower revenue. $0.828 is consistent with a
   low-usage / high-churn day, not an outage.
2. **Dashboard widget contradiction is on Kickbacks' side.** "Ad mode mix: no impressions in
   24h" contradicts the same dashboard's 142-event history → at least one is stale/mislabeled.
   Not reproducible/fixable from the PP.

## Standing (non-today) issue noted
`selfupdate.failed {reason:"vsix-url-blocked"}` is chronic (stuck on 0.3.177, cannot fetch
0.3.178) for days (since ≥06-30), `consecutiveFails` climbing. Not the cause of today's dip,
but worth watching — an outdated client could eventually diverge from server expectations.

## Recommendations
- **No PP build.** The guard is correct and operational for the canary case it covers; nothing to fix here.
- To raise impressions: keep **steady, long-running Claude Code sessions** (avoid rapid reloads/
  restarts that cancel activation inside the 5s settle window).
- If the "no impressions 24h" widget persists while the event history shows credits, **report to
  Kickbacks** with both screenshots — it is a dashboard/reporting discrepancy on their side.

## Done-gate
- [x] Logs analyzed, correlated to 12:08 (idle window, no freeze event).
- [x] `boot.canary` state verified now (absent).
- [x] PP-KickbacksGuard verified (active, healthy, 2-min cadence, self-test bar+ad = True).
- [x] Forensic verdict emitted: **hypothesis discarded**, cause external to PP.
- [x] No code built (correct outcome for a discarded hypothesis).
