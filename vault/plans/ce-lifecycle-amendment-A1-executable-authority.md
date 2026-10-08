---
status: APPROVED (Owner "y", 2026-10-08 ~12:40 local; authorizes A1 + ctx-rent tranche T-S2 1,900,000)
date: 2026-10-08
amends: C:\Users\User\Apps\pp-ce-lifecycle-v\vault\plans\ce-lifecycle-vertical-slice-plan-2026-10-08.md (APPROVED "y A")
preserves: vault/plans/ctx-rent-RESUMPTION.md, vault/plans/ctx-rent-s2-recovery.md, the uncommitted S2 diff
covers: [executable-authority, admission, checkpoint-reserve, mutation-edge, ctx-rent-s2-canary]
---

# Amendment A1 -- executable authority + ctx-rent S2 as the production canary

This is NOT a new program. The lifecycle bootstrap prompt of 2026-10-08 ~12:20 asked for L1-L6, which the
approved ce-lifecycle-v plan already owns (WU-1..WU-8, WU-1 RUNNING as m-3403c155ecb8). A1 adds only the
obligations that plan lacks.

## Reality delta (MEASURED unless labelled)
- ctx-rent worktree: branch ctx/rent, HEAD 0f8713fe, dirty tools/rollover.py (+3/-1), tools/rollover_replay.py
  (+64/-11), ctx-rent-RESUMPTION.md; untracked ctx-rent-s2-recovery.md, .pp-capabilities. No live writer.
- Partial edit confirmed: rollover_replay.py `_tool_message_ids` initialises `cert_uses, certified` and never fills
  them; `certs.add(...)` and `return ..., certs` reference an undefined name (NameError on any trace with a
  certify command). The three missing changes are exactly those in ctx-rent-RESUMPTION.md section "WORKTREE IS BROKEN".
- Goal ctx-rent-s2: cap 3,000,000, settled 2,950,164, open 162,077, used 3,112,241, remaining -112,241,
  since 2026-10-08T10:00:02, root pp-ctx-rent. Parent goal ctx-rent: 6,033,002 of 6,000,000.
- Goal ce-lifecycle-v: cap 5,126,080, settled 486,517, open 307,665, remaining 4,331,898.
- route_admission.py `admit(..., remaining=None)`: the remaining-budget check (line 118) runs ONLY when the caller
  passes `--remaining`. Without it, need is compared with the route target (a nominal envelope).
- S2 plan "Envelope" section declared a 0.4M proof reserve and a 0.3M checkpoint reserve as prose. No mechanism
  held them; the guard enforces only warn/stop on the cap.
- INFERRED: the 1,332,791 already used when the S2 pane started is the R4 class (goal-wide `since` charges a pane's
  pre-binding history; the same mechanism produced 6.82M on ce-lifecycle). WU-1 fixes this.
- Host RAM at scan: ~1.0 GB free of 32 GB.

## Why S2 was admitted with insufficient authority (answer)
Three gaps stacked: (1) admission never subtracted spent + open, because `--remaining` is optional; (2) the proof and
checkpoint reserves existed only in prose; (3) pre-binding history was charged to the new goal. So 1.67M of usable
room was treated as 3.0M, and the reserve was spent on ordinary calls until the guard refused mid-edit.

## Additions to the ce-lifecycle-v Work Units
- WU-2 (+0.15M): the program envelope carries the ctx-rent lineage too, so `ctx-rent` -> `ctx-rent-s2` -> successor
  tranches sum cumulatively. This approval is recorded as a ctx-rent tranche authority event (below).
- WU-4 (+0.35M), executable authority: one function owned by mission_spend GoalLedger returns
  AUTHORIZED / SPENT / RESERVED / IN_FLIGHT_UNKNOWN / PROTECTED_PROOF / PROTECTED_REPAIR / PROTECTED_CHECKPOINT /
  AVAILABLE. Route admission derives `remaining` from it and refuses when the caller cannot name a goal (no more
  optional `--remaining`). Unknown open leases count as unavailable. Admission compares the route's expected
  verified completion (p50 work + proof + repair at p90 variance) plus the checkpoint reserve with AVAILABLE.
- WU-4, mutation edge: the guard refuses a NEW mutating tool call (Edit/Write/commit) when AVAILABLE is less than
  the measured cost to finish-or-revert + minimum verify + checkpoint; reads, tests and checkpoint writes stay allowed.
- WU-4 gates: V-LIFE-EXEC-AUTH (S2 replay: cap 3.0M, used 1.33M, need 1.8M -> NOT_ADMISSIBLE), V-LIFE-RESERVE-UNSPENDABLE
  (mutant "reserve funds work" goes red), V-LIFE-MUTATION-EDGE, V-LIFE-OPTIONAL-REMAINING (mutant restoring the
  optional flag goes red).
- WU-5: the production canary is ctx-rent S2 (below), not a synthetic goal.

## ctx-rent tranche authorized by this YES
- Tranche T-S2: 1.9M = work+proof 1.4M + repair 0.2M + checkpoint 0.3M. Basis: ~14 calls (3-line fix, 4 gates,
  4 suites, commit, replay, receipt, decision) at the measured fresh-worker floor ~95K/call; MEASURED floor, ESTIMATED count.
- The 162,077 open on ctx-rent-s2 is not reused; WU-4's sweep reconciliation settles it.
- S3-S8 are NOT authorized here. After the replay their forecast goes to the broker as ONE semantic question.

## S2 canary flow (zero Owner ops)
When WU-5 lands, the sweep's lifecycle stage finds the ctx-rent program with an approved, unconsumed tranche and
a durable frontier (this file + ctx-rent-RESUMPTION.md). It checks AVAILABLE, binds the successor prospectively
(WU-1), compiles the card and launches a fresh worker in pp-ctx-rent. The worker does the S2 frontier in order:
apply the 3 changes, add V-RR-CERTIFY-DETECT / V-RR-PROTOCOL-NOT-WORK / V-RR-NO-CERTIFY-NOT-ZERO /
V-ROLLOVER-PROTOCOL-BASIS, run the 4 rollover suites, commit, replay OLD UPPER_BOUND_P50 vs NEW PROTOCOL_P90
(+p50 sensitivity) into vault/receipts/ctx-rent-s2-replay.json, measure H3 (no_certify_call: valid exclusion /
measurement hole / alternate path / UNKNOWN), decide the 150K gate (KEEP / LOWER / REPLACE / UNKNOWN),
then checkpoint SAFE_TO_FORGET. H2 stays REJECTED unless new evidence appears.
If WU-5 slips past WU-4 by more than one WU, the WU chain worker arms the S2 packet itself (deterministic arm
with `--goal`, no Owner step).

## Rollback
Kill switches already in the plan plus `CPP_EXEC_AUTHORITY=0` (admission falls back to today's behaviour) and
`CPP_MUTATION_EDGE=0`. The S2 diff is preserved untouched until the canary worker applies the fix.
