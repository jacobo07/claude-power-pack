# EVO — Strategy evolution in the real Ascension autopilot (DRAFT, awaiting Owner "y")

Owner brief 2026-11-12 (laptop pane ddf4990e): integrate Open-Ended Scientific Evolution into the existing GSD X
autopilot (`/home/kobii/agora/ascension-autopilot`). The aim is for the autopilot to evolve its methods verifiably
instead of parking after N generations without certificates. No parallel autopilot.

## Reality scan (measured 2026-11-12 ~08:35Z)
- Lanes: KSR PARKED. INFO_PARK=2 fired: S30K INFORMATION, then S32K INFORMATION with H-A2 SUPPORTED. TENNIS STOPPED:
  the planner found "no admissible lever", because the brief admits only B1-T, which S31T ran and which ended
  INSTRUMENT_FAIL. Both missions sit in a checkpoint hold with no live worker, so nothing has to be stopped.
- Progress classes in `autopilot.py classify_progress`: CERT > CAPABILITY > INFORMATION > NONE. **INSTRUMENT_FAIL
  falls into NONE** and counts toward BLANK_STOP=3 (STOP) and NO_CONVERSION_PARK=3, so a broken instrument is
  scored like a negative result.
- Stagnation handling is the park itself: `_park` -> owner_queue. There is no diagnosis, no alternative selection and
  no research mode. The planner receives the brief's prose ranking and stops when the brief's list is exhausted.
- Continuity defects seen today:
  - A lane parked on FROZEN stayed parked after the Owner released the tranche, so a coordinator had to un-park it by
    hand.
  - S31T's checkpoint lived on branch `worktree-s31t` and the judge reads the product HEAD, which gave INCONCLUSIVE
    until a coordinator fast-forwarded it.
- Reusable pieces (verified on GEX44):
  - `recon-general modules/reconstruction_factory/method_graph.py` (MethodGraph: learn(cls, path, solved), prior,
    macros) and `genome.py` (Strategy Genome: strategy-as-data, seeded mutation). Both work at OPERATOR level today.
  - t1 `negative.jsonl` rows with reopen conditions in S26/S26E/S28K/S30K/S30T/S31T/S32K.
  - S26 method cards (`method_card*.json`), `s26_portfolio.decide` (pre-registered champion/challenger rule).
  - CPP side (inventory 2026-11-12):
    - **Mission Runtime already has method pivoting, live.** `tools/gsd_mission.py`:
      - failure class METHOD_PLATEAU (:3268);
      - `pivot_decision` (:3310-3361), with an authority-first rule;
      - early stop when one method class gives zero evidence delta twice;
      - past 3 pivots, only with distinct method classes, each with an evidence delta, and >= 3M authority left;
      - `pivot_gate` is called from `supervise` (:6293);
      - kill switch `CPP_PIVOT_AUTONOMY=off`; gate `test_mission_pivot.py` (PIVOT_PASS).
      It works inside one mission; the autopilot works across generations.
    - **Constitutive Baseline Ratchet:** `modules/tower/ratchet.py promote()` (:164-183) checks fields, reason and
      authority only. It has NO evidence, negative-control or reuse requirement and NO caller. `verify_chain` is the
      anti-downgrade guard; `family_baseline.py judge/rule/verify` is the CLI. Prompt injection of family baselines is
      live (hook-dispatcher -> gsd_x family_block).
    - **UKDL "three levels"** in this programme = hard rule / process rule / trap (`ukdl-candidates.md:3`), in the
      single `ukdl-universal.md`.
    - PP Eval measures PP's own layers (scheduled), not research methods: not used here.
    - Cognitive OS = token/context/resources: not a method selector. Not used beyond today's budget path.
    - No strategy selector exists anywhere (no "stagnat*" in code). S26 stage D (meta-challenger) was planned, never
      built.
- Real cases:
  - **H-A2 SUPPORTED** (S32K): the 16 S30K exacts were refused because (i) the A2 partner pool was built from the wrong
    set (fixed in diagnosis, control 15/15) and (ii) the ids are absent from the s25stage target oracle
    (TARGET_UNPROVEN). That is a concrete conversion path.
  - **TU-boundary instrument** (S32K T2): recall 0.613 vs 0.80; the amended set had n=0. The UKDL candidate (c) gives
    an unexamined signal: sbss/bss references.
  - **Tennis controls** (S31T): the frozen rule yields n=2 against 22 needed. The proposed widened rule draws controls
    from any lane at its own flags, with the pool proven >= 22 at freeze time and thresholds unchanged.

## Design (inside the existing autopilot; deterministic code, model only in judge/planner as today)
1. **Outcome taxonomy (4 + 1).** CERT, CAPABILITY, INFORMATION, NONE (= no new certificates and no verified
   knowledge), and **INSTRUMENT_FAIL** as its own class.
   - The source is the judge's JSON plus the generation's negative rows with verdict INSTRUMENT_FAIL.
   - INSTRUMENT_FAIL never increments `blank`/`no_conversion` and is never a negative result. It opens INSTRUMENT
     REPAIR for that instrument: at most 2 repair attempts; a third failure parks with the instrument named.
2. **Stagnation -> research transition**, reusing the Mission Runtime pivot rules at generation level instead of
   inventing new ones:
   - the trigger is METHOD_PLATEAU;
   - "a method class with zero evidence delta twice" retires the class;
   - more than 3 consecutive pivots are allowed only with distinct classes, each with a delta, and >= 3M authority
     left; otherwise park.
   - The exact reuse (import of `pivot_decision` vs. sharing its constants and taxonomy) is decided in E2 after reading
     its signature (premise check).
   The 3-without-conversion and 2-INFORMATION rules stay as triggers.
   - The first trigger in a lane switches it to RESEARCH mode instead of parking. Research mode carries its own budget
     (cap per research generation, research total per lane) and its own progress proof (INFORMATION or CAPABILITY,
     verified as today).
   - Stop condition: 2 consecutive research generations without verified INFORMATION/CAPABILITY park the lane (the
     protection stays).
   - A CERT anywhere returns the lane to EXPLOIT and resets the counters.
3. **Lever ledger reusing MethodGraph.** The autopilot records each generation in MethodGraph at lever level:
   cls = blocker class, path = levers applied, solved = verified CERT/CAPABILITY. It reads back a prior.
   - Lever registry `levers.json`: id, mechanism family, blocker classes, preconditions, retire/reopen pointer to a
     negative row.
   - Policy `evolve.select()`:
     - diagnose: the blocker class and the stalled lever from the checkpoint and negative rows;
     - candidates: levers whose blocker class matches, not retired (or reopen condition met, cited), and whose
       **mechanism family differs** from the stalled one (materially different);
     - rank: MethodGraph prior, then cost.
   - The planner prompt gets the selected lever and must pre-register a **discriminating test**: two rival
     hypotheses with different predicted outcomes, a positive control, and a decision rule frozen in a commit.
   - The policy filter refuses research packets without these.
4. **Continuity repairs.**
   - (a) A lane parked on a budget reason re-checks `budget_admits` each tick and resumes when admitted. It only
     re-reads an Owner release and never changes authority.
   - (b) Checkpoint discovery across branches: when the hold's evidence is not in the product HEAD, look at the mission
     binding / worktree branch. Fast-forward only, and only when product HEAD is an ancestor and the product tree is
     clean on the touched paths. Otherwise park `CHECKPOINT_ON_BRANCH <branch>`. Never a merge commit, never a second
     worker.
5. **Gates.** `test_autopilot.py` gains V-EVO-* checks with planted mutants:
   - INSTRUMENT_FAIL counted as NONE;
   - same-family alternative accepted;
   - research without a discriminating test admitted;
   - budget park never resumes / resumes without admission;
   - non-ff checkpoint merged;
   - research loop never stops.

## Phases (budget from the existing autopilot tranche: 405,261,779 total, ~130M free, 80M/day; no new authority)
| Phase | What | Cap | Gate / evidence |
|---|---|---|---|
| E0 | Reconcile: lanes, missions m-a402d24328de / m-774ba9b21e19 (checkpoint holds, no worker), ledger, gate baseline 121/121 | 0.3M | snapshot in laptop EVO dir |
| E1 | Outcome taxonomy + INSTRUMENT_REPAIR + continuity repairs (a)(b) | 2M | V-EVO taxonomy/continuity + mutants; laptop micro-commits per step |
| E2 | Lever ledger on MethodGraph + levers.json + evolve.select + research mode + planner/policy hooks | 3M | V-EVO selection/research + mutants; dry-tick on real state |
| E3 | Cycle 1 KSR (real): stalled = fwidth certification refused (S30K) and TU2 (S32K) -> diagnosis H-A2 -> alternative = target-oracle coverage from original DOL bytes + corrected A2 pool (additive; if it needs a profile change, a NEW additive profile with all six S26C conditions) -> experiment = certify the 16 through the unchanged certify.decide -> independent result (judge + coordinator DOL re-check) -> decision recorded in MethodGraph | <= 12M (one generation) | receipts in a separate file; judge AGREE; indep check |
| E4 | Cycle 2 Tennis (instrument repair): INSTRUMENT_FAIL -> repair: widened control rule pre-registered, pool proven >= 22 at freeze, thresholds unchanged -> B1-T re-run | <= 8M | S31T gate red mutants still red; verdict SUPPORTED/REFUTED or INSTRUMENT_FAIL again (2nd attempt) |
| E5 | Reuse: the next KSR generation picks the learned path for the 45 fallback exacts by the policy, without a human | <= 12M | the selection row cites the MethodGraph edge learned in E3 |
| E6 | Promotion. Production Reality Gate: live ticks and ledger rows, not dry. Constitutive Baseline Ratchet: wire an evidence gate in front of `ratchet.promote` (laptop CPP, additive). It requires (1) a real-execution improvement pointer, (2) red negative controls, (3) a reuse pointer. Without them it refuses, and it gets its own gate with mutants. Then promote the EVO policy into family `binary_reconstruction`. UKDL in three levels: hard rule (an instrument failure is never a negative result), process rule (stagnation goes to research with its own budget and stop), traps (budget park never resumes; checkpoint on another branch). No GEX44 CPP deploy (an Owner gate). | 2.5M | ratchet gate + mutants; family_baseline verify; gate_ukdl_candidates |
| | **Total** | **<= 40M** | |

Stop rules:
- E1/E2 gates must be green before any live tick runs the new code (rollback = bak dir).
- E3 is stopped by: 0 certified with controls clean, which is recorded as a negative row with a reopen condition, the
  lever is retired and the policy picks the next one; or any control violation.
- E4: a 2nd INSTRUMENT_FAIL parks Tennis with the instrument named.
- No push, no certifier/receipt/frontier edits, no authority change; the 100% target stays a direction, not a promise.

## Promotion to baseline (all three or no promotion)
1. Improved a real execution: a lane that would have parked instead produced verified CERT/INFORMATION through the
   policy.
2. Negative controls: the mutants above red, and a dry-tick on a planted stalled lane chooses a different-family lever.
3. Reuse: a later generation (E5) used the learned edge without a coordinator act.

## Rollback
autopilot bak-* dirs (GEX44) + laptop git; kill switch `OFF`; t1 micro-commits revertable; receipts untouched.
