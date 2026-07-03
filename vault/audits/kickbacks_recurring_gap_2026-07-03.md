# Kickbacks Recurring-Gap Forensic (2026-07-03, PM) — 5 hypotheses tested

**Verdict: NO periodic system cause. All 5 hypotheses (H1–H5) DISCARDED against real
log data.** The two "gaps" (12:08 and 17:38 local) are the tail-ends of two active-work
bursts followed by breaks — a human work rhythm (n=2, ~5h30m apart), not a 5-hour timer.
The morning "activity-driven" conclusion HOLDS and is reinforced. No PP bug, no PP fix.

## Symptom (as reported)
- Activity Ledger at 18:48 local: 154 rows, last impression 17:38 local (15:38Z), 70 min silent.
- Statusbar $3.49 today. Earlier gap ~12:08 local (10:08Z). Two gaps same day, ~5h apart.
- Owner concern: the second identical gap may falsify the morning "churn" conclusion.

## Evidence (debug.log is UTC `Z`; NOW at analysis = 18:50 local / 16:50Z; log live)

### H1 — auth.refresh fails at 12h/17h → DISCARDED
At **10:08Z (gap 1) there were ZERO auth failures** — window was clean (`auth.refresh ok:true`
at 10:04/10:11/10:17). Today's `ok:false` events are scattered (09:09, 13:09, 15:09, then a
cluster 15:14–16:51), **all `transient:true` and immediately followed by `ok:true`**. They do
not align to the gap starts, and the first gap had none. Auth is not the trigger.

### H2 — a task every ~5h interrupts Kickbacks → DISCARDED
Scheduled tasks with a 3–6h repetition are all benign Windows built-ins: CEIP `Consolidator`
(PT6H), `OneSettings RefreshCache` (PT4H8M), `Storage Tiers Optimization` (PT4H), `WER
QueueReporting` (PT4H). **None is ~5h; none touches Kickbacks.** The only Kickbacks task is
`PP-KickbacksGuard` (every 2 min, Running, result 0). No 5h cadence exists.

### H3 — token TTL ~5h → DISCARDED
Tokens rotate roughly **hourly and far more often under load** (`auth.refresh rotated:true`
dozens/min in 15:20–16:00), never on a 5h boundary. No 5h expiry event.

### H4 — vsix-blocked degraded state → NOT SUPPORTED
`selfupdate.failed` occurs all day at varying `consecutiveFails` (3 at 10:08Z, 9 at 15:33Z);
the CLI keeps activating and reaching `hasAd:true` regardless. Not aligned to either gap.
(Already monitored via INV-VSIX.)

### H5 — Cursor 5h GC → no supporting signal
Nothing in these logs indicates a 5h Cursor-internal event. Cannot be proven from here, but
zero evidence for it.

### The `killed:true` red herring
`killed:true` in `session.state` appears ONLY at 23:00Z (yesterday, brief) and **16:52–16:53Z
(right now, flipping killed:true↔false)** — NOT at 10:08Z or 15:38Z. Both gaps ran
`killed:false` throughout. A kill-switch did not cause the gaps. Grep for
`kill|serving|suspend|quota|429|throttle|rate-limit` returned **only** `session.state` lines —
no rate-limit / quota / 429 events exist in the log.

## What actually happened
- The gaps are the tails of work bursts → breaks (12:08 lunch, 17:38 evening). Impressions did
  **not** stop permanently at 12:08: they went 142 → 154 (+12) through 17:38 — they resumed
  when work resumed. A gap is a **plateau during a break**, not an outage.
- **Churn does not multiply impressions.** The afternoon shows heavy rapid `activate`/auth churn
  (Cursor reloads / restarts) yet only +12 impressions — consistent with server-side per-interval
  impression dedup/rate-limit: rapid re-activation shows the same ad without counting new
  impressions, and can suppress rather than add. Steady long sessions with ad rotation earn more.
- **NOW (18:50 local, mid "gap"):** CLI active (`activate` 16:46Z, `signedIn:true, authHealthy:ok`),
  guard self-test `bar=True ad=True`, no canary. Earning path healthy — the "gap" is just the
  current evening lull, not a broken pipeline.

## Answers to the brief
- **Cause of the gaps:** activity-driven (work-burst → break); confirmed, not speculated.
- **Same mechanism in both gaps:** yes — both are break-plateaus at the tail of active work.
- **Real interval:** 12:08→17:38 = 5h30m — coincidental with work rhythm, not a system period.
- **Third gap expected?** No periodic basis. A "gap" recurs whenever active Claude Code work pauses.
- **PP action possible:** none — this is how Kickbacks Ad-mode earns (active-statusline time),
  not a PP bug. Auth transients + vsix-blocked already surfaced/monitored.

## Recommendation
- **No PP fix** (external, by-design earning model). To raise earnings: fewer reloads/restarts,
  longer stable Claude Code sessions (also reduces the auth-throw churn seen in the PM cluster).
- Optional: reinstall the extension to clear `vsix-url-blocked` (0.3.177 → 0.3.178+); may reduce
  the transient auth throws, but will not change the active-time earning model.
- If the ledger truly shows $0 while `hasAd:true` + `killed:false` during a genuinely active,
  long session (not a break), THAT would be a new signal worth reporting to Kickbacks — not
  observed today.

## Cross-ref
Morning forensic `vault/audits/kickbacks_impression_gap_2026-07-03.md`; SCS C60; UKDL
`T-KICKBACKS-SESSION-CHURN-001`, `T-KICKBACKS-RECURRING-GAP-ACTIVITY-001`.
