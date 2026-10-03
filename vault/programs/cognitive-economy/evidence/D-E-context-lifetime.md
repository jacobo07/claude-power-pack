# [D] [E] Context lifetime and fresh-epoch economics -- measurement

Denominator: `D-W7` = 2026-09-26T00:00:00Z .. 2026-10-03T00:00:00Z, weighted 3,325,101,725 (frozen:
input 1, cache_read 0.1, cache_write 2, output 5). Every call counted below lies inside D-W7, so numerator and
denominator are drawn from the same calls.

command: `python vault/programs/cognitive-economy/measure/context_lifetime.py --json vault/programs/cognitive-economy/evidence/context_lifetime.json`
(zero model calls; reads the rollover ledger, the autorun ledger, `tools/gsd_epoch.py` epochs() by import, the
session transcripts and, read-only, the usage index). Run twice: result_sha256
`672ad45dd2b922a8c30ef227c97ccae676f04f1b763892006a3af7f3a2087225` both times. Raw stdout:
`evidence/context_lifetime.stdout.txt`; per-pair rows: `evidence/context_lifetime.json`.

## Definitions

- **crossing**: interactive = a non-drill `successor_claimed` row (predecessor -> successor); mission = an epoch
  whose start_cause is CONTEXT_ROTATION. Route of an interactive crossing = the `rollover_kclear_asked` route of
  its predecessor (economic / self / terminal-inbox / orca-exact / manual).
- **ctx_before / ctx_after**: context of the predecessor's last call / the successor's first call.
- **rehydration** (displaced work, MEASURED): weighted cost of the successor's calls up to and including its first
  Edit/Write.
- **carry_saved**: (ctx_before - ctx_after) x 0.1 x successor calls in the window. It assumes the predecessor would
  have carried its full context for every one of those calls. The real alternative at the wall was compaction or
  ending the session; neither was measured. So this is an UPPER bound and never a saving.

## Results

| Population | Pairs (measured) | median ctx before -> after | Rehydration % D-W7 | carry_saved UB % D-W7 | Net interval % D-W7 |
|---|---|---|---|---|---|
| Interactive, all | 127 (126) | 458,194 -> 127,988 | 2.1287 | 19.2924 | [-2.1287, 17.1637] |
| Interactive, economic trigger | 3 (3) | 382,280 -> 133,771 | 0.0475 | 0.2346 | [-0.0475, 0.1871] |
| Interactive, wall / other routes | 124 (123) | 458,375 -> 127,876 | 2.0812 | 19.0578 | [-2.0812, 16.9766] |
| Mission CONTEXT_ROTATION | 52 (49) | 400,617 -> 153,720 | 0.9063 | 3.3177 | [-0.9063, 2.4113] |

Unresolved pairs (a transcript missing) are counted and excluded: 1 interactive, 3 mission.

## [D] What the live economic trigger realized

The economic trigger (approved 2026-10-02) produced 5 `rollover_kclear_asked route=economic` asks in D-W7, and
3 of them led to a claimed successor. Those 3 crossings paid 0.0475 % of D-W7 in rehydration. Against that they
saved at most 0.2346 % in carried context. Net: **[-0.05 %, +0.19 %] of D-W7**, an interval, because the
counterfactual (compaction or session end) is unmeasured. Nearly all crossing activity (124 of 127) came through
the 45 % wall route, not the economic one.

## [D] KSR dead-carriage comparison (success criterion 2)

KSR measured dead carriage <= 6.34 % (UPPER BOUND, on the KSR corpus's own D-decision denominator, not D-W7). The
live economic trigger reclaimed at most 0.23 % of D-W7 in this window. **The remaining up-to-6.11 % stays an
upper bound, not a saving.** The two figures sit on different denominators, so the subtraction only orders
magnitudes; it is not a computed residual.

## [E] Is any rotation-threshold change worth >= 3 % of D-W7?

Ceilings over the 97 mission worker sessions with epochs started in D-W7 (540 epochs; 48 without a transcript:
45 named sessions with **0 indexed calls** in D-W7, plus 3 with no session, so they sit outside both numerator and
denominator):

- Rent paid above each session's own first-call context (gross): 3.4871 %.
- **Rotating earlier**, net of one rehydration per extra rotation priced at the CHEAPEST measured rotation
  (280,066 weighted): <= **2.7839 %**. That is an upper bound. Real rehydrations are larger (median of the
  measured rotations about 0.6 M weighted), and a second extra rotation costs again.
- **Rotating later** can save at most the rehydration the window's rotations paid: <= **0.9063 %**.

Both ceilings are below 3 %, so by the frozen rule no threshold change is proposed to the owner.

## Controls (success criterion 4)

- Positive: the first interactive pair the ledger records (b56ffff2 -> 4bb2abf7) is found, with
  ctx_before > ctx_after: `found_with_drop: true`.
- Negative: session 00343cb8 (>200 KB transcript, active in the window, never typed /clear or /kclear, in no
  ledger row) yields 0 crossings: `ok: true`.
- The script exits 1 unless both controls hold; it exited 0.

## Saving labels

- Economic trigger: upper_bound, net <= 0.19 % D-W7, displacement unknown. Rehydration is measured, but the
  counterfactual alternative's cost is not.
- All crossings: upper_bound <= 17.16 % net D-W7, displacement unknown (same reason). This is the rent the boundary
  avoided relative to never crossing. It is NOT a saving relative to the compaction it replaced.
