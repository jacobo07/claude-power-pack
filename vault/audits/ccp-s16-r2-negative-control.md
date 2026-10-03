# CCP §16.1 R2 -- historical negative-control search (2026-10-03)

Question: has any REAL boundary ever produced a CONTINUE that the remaining-work prior decided, rather
than decide's 150k growth gate? Evidence level: HISTORICAL_REAL (Owner Q6) -- real sessions, only the
information available at each commit, no live shadow.

## Method

`rollover_replay.replay` (hindsight-free boundaries, plan ccp-s16 C2-C3) over the usage index: of 878
interactive sessions, the 664 whose last call fell in the 14 days before the newest, scanned newest
first until 80 candidates (>= 1 successful commit AND max growth over floor >= MIN_GROWTH_TOKENS);
126 scanned, 0 unreadable. Every boundary judged by decide at the prior (C = 0) and with measured
rehydration C in {0, p50 of resumes certified before T}. Driver: the scratch script of this session,
re-runnable as `rollover_replay search` once R1 lands (until then this file is the record).
Wall 280.5 s.

## Result

| | count |
|---|---|
| boundaries | 471 |
| stopped by the growth gate (CONTINUE, not horizon-driven) | 169 |
| judged by the prior | 302 |
| prior WOULD_ROLLOVER / INSUFFICIENT / CONTINUE | 225 / 77 / **0** |
| rehydrated WOULD_ROLLOVER / INSUFFICIENT / CONTINUE | 112 / 190 / **0** |

**No horizon-driven CONTINUE exists in 302 judged real boundaries.** Rehydration moves 113 of the 225
WOULD verdicts to INSUFFICIENT_EVIDENCE and never produces CONTINUE.

## Reading

This confirms the plan's prediction (§16.1) and the audit's gap 3: a prior of `calls after a commit`
that is not conditioned on the session's own state cannot say "this session is near its end". Its
survival share at break-even n* stays high because most commits in the index are followed by many
calls. A ROBUST_CONTINUE therefore needs either a very large n* (which the growth gate already covers)
or a STATE-CONDITIONED prior (Stage 2: open obligations at the boundary, reconstructable without
hindsight from the goal file at the boundary commit).

Consequences:
- The negative check stays PARTIAL. A fixture can show the branch is reachable; neither history nor
  the unconditioned prior can supply a real one. Do not weaken thresholds to manufacture it.
- D1 with this prior removes the 30-call constant from live authority and makes uncertainty visible,
  but it can only REDUCE economic asks (WOULD -> UNDETERMINED), never add a CONTINUE that the old
  policy lacked. That is the honest scope of Stage 1.
- Stage 2 is the next evidence-earning step for the negative control, not a tuning of Stage 1.
