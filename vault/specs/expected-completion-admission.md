---
status: PROPOSED (pane 5d6a315c, 2026-10-08) -- awaiting Owner approval in chat; this file backs the plan, it is not the approval surface
covers: [expected-completion-admission, route-admission, forecast-classes, warn-control-point, progress-spend, dependent-admission, packet-chain-completion, context-rent-trigger, cost-collapse-T3-plus]
extends: tools/route_admission.py (owner: admission verdict), tools/mission_spend.py (owner: meter, judge, forecast, autopsy), tools/gsd_mission.py (owner: sweep, envelope, arm), vault/specs/goal-budget-admission.md (owner: goal ledger, leases, pre-call reservation), vault/specs/cost-collapse.md (parent program)
novelty: EXTEND_EXISTING_OWNER (HR-NOVELTY-001) -- no new module
depends_on: ctx/rent (S0 spec only, nothing built), ce/lifecycle-v (rotation WU-1 in flight) -- consumed, never duplicated
---

# Expected-completion admission -- the lower bound stops certifying affordability

## Verified reality (2026-10-08, deterministic: transcript usage fields + mission records + git)
- route_admission.py: need = sum(calls x (profile floor + packet)) x 1.2 (DEFAULT_GROWTH_MARGIN, "a chosen value, not a
  measured one" -- its own docstring). It is a lower bound with an unmeasured fudge and is the sole affordability test.
- T1 m-1a51d97b4a15: planned 48 calls, need 6,447,456, target 8M. Actual 11,135,030 / 65 calls / mean 171.3k / max 206k.
  actual/need = 1.73 = calls x1.35 * per-call x1.28 (171.3k vs 134.3k planned incl. margin). +39% over target.
- T2 m-b76843b319af: planned 36 calls, need 4,821,336, target 5M. Actual 4,090,547 / 27 calls / first 119,788 /
  mean 150.5k / p50 150.6k / p90 172.2k / max 174.8k. actual/need = 0.85 = calls x0.75 * per-call x1.13. Under target.
  Context grew ~linearly: (174,754 - 119,788) / 26 = 2,114 tokens per call. Gates: AUTOPSY 42/42, ENVELOPE 55/55,
  GRAMMAR 56/56 (2b5b0ea5). Receipt self-reports "~20 calls"; meter says 27 -> measured wins.
- Pattern across both: per-call error is one-sided (+28%, +13%: the 1.2 margin under-covers growth); call-count
  error is two-sided (+35%, -25%). Cost inside one process is n*F + g*n^2/2 -- quadratic in calls.
- Progress/spend tripwire ALREADY EXISTS: mission_spend.judge trips when processed since the work tree last changed
  > 0.5 x estimate; hard trip at 2.0 x estimate (DEFAULT_TRIP_RATIO) -> owner hold. Warn is declared (ms.declare,
  gsd_mission.py:1622) but has no behaviour of its own.
- CHAIN DEFECT (fired twice): each packet worker ends, the sweep tries a turn_continuation, "host started a COPY
  instead of continuing", the record sticks in LAUNCHING + hold, and the worker's own arm of the next tranche is
  refused by singleflight (T1 -> T2 needed a manual supersede; T2 -> T3 is in that state now). Hypothesis to verify:
  the sweep runs LIVE code (feature/knowledge-acquisition), which lacks T1's packet-gate-completes-continue fix.
- gsdx-pcc m-53847a002b65: held; autopsy 187.4M vs spec's 162.2M at 19:30Z; last transcript write 19:53Z 10-07.
  Whether the delta is post-hold spend or attribution is UNVERIFIED.
- Owners: ce/goal-admission (goal ledger, leases, pre-call) LIVE; fix/mission-cost-breaker LIVE; ce/presence LIVE;
  ctx/rent spec only; ce/lifecycle-v rotation WU in flight; ce/gen2-completion 15 ahead, gen3 t1/t3 unlanded.

## Four numbers, never one
LOWER_BOUND = existing need without margin (diagnostic; still refuses impossible routes; ESCALATE on absent floor).
EXPECTED = n*F + g*n(n-1)/2 + proof reserve + repair reserve, per worker, F and g from the Work-Class profile.
SAFETY = EXPECTED at the call-count band's high edge (n x (1 + calls_err)). HARD = stop (airbag, 2 x target).
Each carries basis (measured:<source>/estimated/unmeasured), n (samples) and confidence = weakest input.
Absent g or calls_err is UNKNOWN, never 0: verdict ESCALATE, not ADMISSIBLE.

## Verdicts
ADMISSIBLE: EXPECTED <= target and SAFETY <= warn. WATCHED: EXPECTED <= target, SAFETY <= stop -> reforecast
checkpoints armed at planned-calls exhaustion and at warn. RECOMPILE: EXPECTED > target (split or thin; the
report names max calls per process). ESCALATE: unmeasured input or SAFETY > stop.
While confidence is LOW (n < 5 completed units of the class) SAFETY drives WATCH, never refusal (anti-Goodhart:
on T2 the challenger would have asked to thin 36 -> 34 calls; on T1 it gives EXPECTED 7.76M, SAFETY 11.67M vs
actual 11.14M -> WATCHED, with the reforecast firing at call 48).

## Running control (warn is a control point)
At warn (session guard, pre-call) the worker gets one injected instruction: write a progress receipt, reforecast.
The sweep then computes EAC = spent + r x (ctx_now + g x r/2), r = remaining calls from the band, and decides:
CONTINUE if EAC <= target x (1 + class tolerance) and the progress fingerprint moved since the last mark;
CHECKPOINT (owner hold + recompile packet for the remainder) otherwise. Stall trip (existing) unchanged.
Context Rent: rotate when (ctx_now - F) x r > F + rehydration -- the successor is cheaper; the rotation itself is
ce-lifecycle's (kclear -> SAFE_TO_FORGET -> clear -> kresume), consumed, not rebuilt. Autocompact stays the fallback.
Checkpoint reserve: the last 2 x ctx_now before stop is receipt-only. Stop stays the airbag; a WU that reaches it
has failed regardless of its gate.

## Dependent admission (T3 cannot inherit a bad model)
A dependent unit arms only when the predecessor is terminal AND its receipt carries METERED economics (spend,
calls, first/mean/p90 ctx, g, forecast error) AND the error is inside the class tolerance or explained.
FREEZE otherwise. Arming moves from the worker (singleflight-refused by construction) to the deterministic sweep.

## Work units (fresh Sonnet packet workers; each estimate computed with the challenger itself)
E1 estimator + calibration: three tiers in route_admission, profiles gain g/calls_err with provenance, calibrated
   from mission_spend autopsy over T1, T2 and gsdx-pcc sessions; shadow verdict recorded beside the champion's.
   Canaries 1, 3, 4. Gate: V-ADMIT-EXPECTED-* + mutation drills (growth term removed, unknown-as-zero, lower bound
   labelled expected) all go red. ~30 calls, EXPECTED ~4.4M, target 5M.
E2 running control: warn instruction, EAC reforecast in judge, CONTINUE/CHECKPOINT, rotation trigger handed to
   ce-lifecycle. Canaries 5, 6, 7, 10, 11 on isolated fixtures. ~30 calls, target 5M.
E3 chain + dependent gate: verify and fix the stuck-LAUNCHING completion; sweep-side dependent admission with
   metered receipts. Canaries 8, 9. ~25 calls, target 4M.
E4 land + ratchet: cherry-pick T1, T2, E1-E3 onto feature/knowledge-acquisition (local, never push, rollback tag,
   smoke), Cognitive CI check for lower-bound-only admission, KV + UKDL entries, CBR/presence registration.
   Canary 12 = E4 itself runs WATCHED under the live challenger. ~20 calls, target 3M.
Then T2 reconciliation (deterministic) -> T3 under the new baseline. Expected recompile: one 15M process would
need ~80 calls and pass 250k context; split T3a (gsd_compile) / T3b (mission_wait + default) at ~40 calls each,
EXPECTED ~6.25M each. T4-T7 continue per cost-collapse.md.

## Program budget
Spent: T1 11.14M + T2 4.09M + T0 and this pane (unmeasured here). E1-E4 add ~17M. Original 60M cap cannot hold
T3-T7 (~40M) after that; decision D1.

## Rollback
Champion stays authoritative until E4 promotion; revert = drop the challenger verdict field (shadow only) or
revert the E4 cherry-picks at the rollback tag. CPP_ROUTE_ADMISSION=off remains the existing kill switch.
