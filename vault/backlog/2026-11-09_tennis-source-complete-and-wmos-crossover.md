# Backlog — Tennis to 1797, Wii Sports into KobiiSports Resort, WMOS crossover (2026-11-09)

Source: session 978a21cc. The Owner said "go ahead, añade todo al backlog": keep the Tennis 1797 goal, because the end goal is
to port all of Wii Sports into KobiiSports Resort, all sports together and 100% customisable.
Status of every row is as measured on 2026-11-09 ~14:00 UTC; re-check before acting. Related: `vault/plans/deferred-backlog.md`
D21 and `vault/plans/d11-tennis-step0.md`.

## State at entry

- Tennis frontier 1198/1797 certified exact (66.7%). The 599 left: 158 COMPILES_NO_MATCH, 441 NO_COMPILE (S21 census).
- 1797 is the Tennis candidate set, an upper bound, inside `SportsPackEP.dol` (14,885 functions = all of Wii Sports, no RELs).
  63% of that DOL's functions have an exact shape match in the Resort factory split; Tennis's candidate only 23% (D21 step 0).
- S17-S21 yield +40, +1, +1, 0, 0. Model levers on the residue are spent. S21 R2 (class-level owner fix) moved 0 -> 6 COMPILES
  with 0 model tokens; it is the only lever still moving state.
- S22 m-4a5a719551ae RUNNING on GEX44 (8M, 4 cycles / 8 h), W0 done (t1 cb9cc24c). Private repo synced to t1 2ca2530f /
  gen3 671a2c86.

## To do, in order

### 1. Judge S22 at its checkpoint (running now)
Re-run its gates on GEX44, judge closeout.md, land promotions, ff the private repo. If W1-W3 moved 0 functions, the stop rule
says recommend closing exact-match Tennis — read item 3 first: it is the new mechanism the stop rule allows for.

### 2. WMOS function crossover: Table Tennis (P4) and Tennis (P5)
For each game: the motion-path functions WMOS must hook or replace (KPAD/CoreController read, MotionPlus, swing/stroke
detection, racket/paddle and ball response) x their reconstruction state (certified / compiles / blocked / not decompiled).
Table Tennis status comes from the reconstructed WSR source (ADR-010); Tennis status from t1 on GEX44 (frontier projection).
Output answers: does the missing Tennis residue block WMOS P5 or not. Draft in progress:
`<scratchpad>/wmos_crossover.md` (session 978a21cc); promote it into the KSR repo when judged.

### 3. S23 "Source-complete Tennis" — proposal, Owner approval required, NOT armed
Redefine the product target from "1797 byte-exact" to "1797 in modifiable source that relinks into a booting DOL":
- Tier A exact (objdiff 100%, certify.py / cert_cxx) — unchanged, still counted.
- Tier B equivalent: compiles, relinks, and passes a behavioural differential against retail in Dolphin on GEX44 (same game
  state frame by frame over recorded inputs). Not a certificate; reported separately.
- Tier C retail object: hookable only.
Gates to design before arming: differential COVERAGE per function (a differential that never executes a branch cannot see a
wrong one), a mutant that the differential must catch, hybrid DOL boots in Dolphin, then on hardware.
Tools that exist: `relink.py`, `lcf2ld.py` (decomp core). Cost: unmeasured; pilot on the 6 R2 COMPILES fns first.

### 4. Wii Sports -> KobiiSports Resort port (programme, after 3 proves the hybrid route)
Scope is 14,885 functions, not 1797. Step 0 for the rest of Wii Sports (Baseball, Bowling, Golf, Boxing): split per sport,
shape overlap with the Resort split (the 63% shared engine/library), census COMPILES/NO_COMPILE. Decide engine strategy:
Wii Sports code against its own EGG/NW4R versions vs rebased onto the WSR engine KSR uses. Owner decision, not yet asked.

## Owner decisions pending
- Approve S23 (budget, envelope) after S22 closes.
- Programme order for item 4 (which sport after Tennis).
