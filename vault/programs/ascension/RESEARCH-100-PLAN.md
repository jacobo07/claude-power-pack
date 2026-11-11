# Ascension to 100%: research programme -- DRAFT PLAN (2026-11-11, pane fa41bae9)

Status: DRAFT. Nothing is armed and no authority is requested by this file. The Owner asked for it after the
measured forecast ("y", 2026-11-11), which concluded that the autopilot cannot reach 100% on either lane.

## Why the autopilot cannot get there (forecast, 2026-11-11, GEX44 frontier counters + S17-S27 checkpoints)
| Lane | Functions | Certified | Share | Left |
|---|---|---|---|---|
| KSR | 30,388 | 9,269 (8,687 + 582 S26C) | 30.5% | 21,119 |
| Tennis | 1,797 | 1,198 | 66.7% | 599 |

KSR remainder by class: COMPILES_NO_MATCH 9,941; NO_COMPILE 5,453; FLAGS_SPLIT 3,447; NO_TARGET 2,276 (2,858 - 582);
XF_ERROR 2. Sum = 21,119.
History: ~200M processed over ~10 generations since S17, one productive generation (S26C, 582 KSR at ~24K tokens per
certificate, from a structural finding: the reference package omitted 573 of 877 objects). Tennis: 0 new in S23-S27.
The autopilot loops generations over the levers already known (~350 KSR candidates, none for Tennis), so it ends at about
31-32% KSR and ~67% Tennis. Reaching 100% is a research problem: each failure class needs a method that does not exist yet.

## Principle: research by failure class, not by generation
Each class gets a characterisation, then one pre-registered pilot on a frozen sample (dev + held-out, drawn and committed
before any attempt), then a go/no-go. Only a passing lever is scaled, and its scale-out authority is computed from its
own measured cost per certificate. No class is scaled on hope.

## Phase 0 -- characterise (read-only, <= 5M processed, 0 fresh)
For each class, sample 50 functions and record WHY they fail (missing type, wrong compiler flag, register allocation,
instruction order, missing object, toolchain version). Read S26C's checkpoint first for why the other 2,255
capsule-omitted units did not certify. Output: `evidence/ascension/r100/phase0.md`, one failure-cause histogram per class.
Decision rule (pre-registered): a class goes to Phase 1 only if one cause covers >= 30% of its sample.

## Phase 1 -- pilots (<= 10M processed each, at most 6 pilots, <= 60M total)
| Pilot | Class | Size | Known starting point | Hypothesis to test |
|---|---|---|---|---|
| R1 | KSR FLAGS_SPLIT | 3,447 | 117 BINARY_EXACT in arm auto_03_801639EC (S25) | per-unit flag recovery generalises beyond that arm |
| R2 | KSR NO_TARGET | 2,276 | S26C re-staging stage | the rest are recoverable by the same staging, or need a different target source |
| R3 | KSR NO_COMPILE | 5,453 | `?` type repair: 87 exact (experimental) | type recovery as a capability, not a per-function fix |
| R4 | KSR COMPILES_NO_MATCH | 9,941 | S23 O8: 2 exact of 300 at 70-90% | a systematic search over codegen-equivalent source variants beats one-shot rewriting |
| T1 | Tennis NO_COMPILE | ~494 | T2 typelift: dev 14 compile / 0 exact | Tennis needs its own type corpus, not KSR's transfer |
| T2 | Tennis COMPILES_NO_MATCH | 164 | attacked 1-4 times, 0 | same search as R4 on a small, fully known set |
Go rule (pre-registered per pilot): >= 5% of the held-out sample certified by the UNCHANGED certifier (an override match
or BINARY_EXACT in an arm does not count), AND measured cost per certificate <= 200K processed tokens.
Kill rule: < 1% held-out, or the certifier rejects what the pilot calls exact. A killed pilot goes to negative.jsonl.

## Phase 2 -- scale-out (new authority, per lever)
Authority requested = pilot cost per certificate x class size x 1.5, one lever at a time, with the pilot's numbers
attached. If every class needed S26C's best rate (~24K/cert), 21,119 KSR functions would cost ~500M; the realistic
total is unknown until Phase 1 measures it, and >1B is plausible. That number is not requested here.

## How it runs (recommended)
Phase 0 and Phase 1 fit inside the autopilot's remaining ~200M: give this file to the planner as its brief, so each
generation is a pilot instead of another pass over known levers. The 3-blank stop then means "3 pilots killed".
Phase 2 is a separate Owner authorization per lever.

## Constraints (unchanged)
No certifier rule edits, no canonical ctx/header writes, no push, no counter merge. A new certification profile only
under all S26C conditions. R2-gated items and the 582 headline merge stay Owner calls.

## Owner decisions needed
1. Feed this plan to the autopilot planner as its brief (Phase 0-1 inside the existing 400M, no new authority)?
2. Accept the go/kill thresholds (>= 5% held-out, <= 200K tokens/cert; < 1% kills)?
3. Phase 2 authority: decided later, per lever, from pilot numbers.
