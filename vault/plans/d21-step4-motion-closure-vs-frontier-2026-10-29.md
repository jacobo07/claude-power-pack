# D21 step 4 -- motion closure against the certified frontier (zero-model, 2026-10-29)

Question (Owner "go ahead", 2026-10-29): how much of Tennis's motion code is already certified, and can D21 Scope A
start without waiting for Tennis ALL-MATCH or recon-factory CP50?

## Instruments
- Motion set: `wst_tennis/step3/probe_step3.py` re-run untruncated (the committed report cuts the lists at 25).
  Copy with `[:25]` removed, output to the session scratchpad. Result: c = 50 getter callers, d = 20 field readers
  (d is a subset of c), the same counts as step 3, so the re-run reproduces it.
- Frontier: GEX44 `~/missions/t1-campaign/evidence/frontier/frontier.jsonl`, read-only over ssh. Clone HEAD 281b9881,
  `counters.json`: CERTIFIED 519, COMPILES_NO_MATCH 540, NO_COMPILE 738, UNKNOWN 0. Working tree has U2's uncommitted
  operator edits; they do not touch the frontier files.
- All 50 motion functions were found in the frontier (0 ABSENT), so a 0 below is a real 0, not a failed look.

## Results (measured)
| set | n | CERTIFIED | COMPILES_NO_MATCH | NO_COMPILE |
|---|---|---|---|---|
| getter callers (c) | 50 | **0** | 4 (pct 24.6, 44.7, 74.0, 84.0) | 46 |
| field readers (d) | 20 | **0** | 0 | 20 |

- NO_COMPILE first errors in the motion set: 10149 x25, 10377 x5, 10499 x4, 10140 x4, 10393 x4, 10209 x3, 10121 x1.
  10149 is also the largest NO_COMPILE family overall (265 of 738).
- Size: motion median 138 insns, rest of Tennis median 23, CERTIFIED median 3.

Frontier state by function size:
| insns | n | CERTIFIED | CNM | NO_COMPILE |
|---|---|---|---|---|
| 1-4 | 390 | 318 | 56 | 16 |
| 5-19 | 389 | 144 | 106 | 139 |
| 20-49 | 404 | 54 | 211 | 139 |
| 50-137 | 425 | 3 | 137 | 285 |
| 138+ | 189 | 0 | 30 | 159 |

Largest certified function: 68 insns.

## Reading
- The 519 certified functions are almost all small: 462 of them have fewer than 20 instructions. Above 50 instructions,
  3 of 614 are certified. The motion code sits in exactly that band. So the ALL-MATCH count says nothing about how
  close D21 is: the frontier can keep rising without reaching one motion function.
- What blocks the motion code is NO_COMPILE, and its largest family is 10149. A fix for the 10149 family is the single
  lever that touches the most motion functions (25 of 50). The meaning of MWCC error 10149 is not recorded in the
  vault; this note does not guess it.
- D21 Scope A admission (reforecast 2026-10-12) stays **NOT ADMITTED**:
  - a >=20-insn match exists (57 certified at >=20 insns), which is evidence for the compiler/flags condition;
  - but 0 motion functions are verified, the certified population is unrepresentative of the closure, and the
    Tennis A/A and the family curve were not checked here (UNKNOWN).
- The step-3 caveats still hold: the closure is a floor (no argument propagation, no virtual calls). The true closure
  is larger, not smaller.

## Step 4b -- the 10149 family on the motion set (Owner "go ahead" = option 1, 2026-10-29)
All compiles ran in throwaway temp dirs on GEX44 (`~/missions/t1-campaign` @ 281b9881, no recon_fabric peer running).
Nothing was written to the clone, its cache or its evidence. Sources = champion v5 (`repair.transform_v5`).
- **What 10149 is:** MWCC `(10149) not a struct/union/class`, i.e. `.unkN`/`->unkN` on something with no struct type.
- **Census of every 10149 error** (265 functions; counts are lower bounds, because MWCC aborts):
  - A, a call returning `void *` dereferenced (`fn_X(...)->unkN`): 72 errors. 40 of them are the controller getter
    `fn_800B7AD4`, and all 40 are inside the motion set.
  - B, an extern declared scalar used as a struct (`lbl_X.unkN`): 740 errors. Top globals lbl_803CDE58 x117,
    lbl_804F96D8 x73, lbl_804F97F4 x55, lbl_804FB048 x20 (19 of those are in motion code).
  - C, other (pointer chains such as `p->unk0->unkAC(...)`, untyped locals): 570 errors.
  - Motion set: 25 functions, errors A 44 / B 27 / C 35. 16 of the 25 show only A/B errors.
- **Experimental transform** (not committed anywhere): for each A callee and B global actually dereferenced, it
  synthesises a padded struct with the observed offsets (width = gap to the next offset, capped at 4) and retypes the
  prototype or extern.
  - Motion 10149: **0 -> 9 of 25 compile**. pct 84.4, 84.2, 3.9, 87.7, 84.9, 89.6, 84.5, 76.0, 85.6. 0 MATCH.
  - Still failing: 10149 x7 (shape C), 10499 x7, 10140 x1, 10377 x1.
  - All 265: 0 -> 64 compile, 0 MATCH. No regression check was run on the other 1,532 functions.
- **Reading:** typing the controller object is the unlock, as expected from steps 2-3, but it moves NO_COMPILE to
  COMPILES_NO_MATCH, not to MATCH. The field widths are guesses (the getter's struct gets s32 by default), and that
  probably explains part of the ~85 % plateau.
  - Next, in order:
    1. Take field widths from the target asm (lbz/lhz/lwz/lfs at each offset) rather than the gap rule.
    2. Land it as a v6 repair lane. Then a full 1,797 sweep with 0 regressions vs v5, the search lane on the new
       COMPILES_NO_MATCH, and certify.
    3. Attack 10499, the next motion blocker (7).
  - Collision: U2's uncommitted operator edits sit in the same clone, so step 2 must wait for U2 to commit or be
    discarded.

## Step 4c -- the plateau is the compiler flags, not the field widths (Owner "y, sigue hasta terminar", 2026-10-29)
All measurements below ran in temp dirs on GEX44 with `cv1.FLAGS` overridden only inside the measuring process. The
clone's flags, cache and evidence are unchanged.
- **Asm field widths (step 1): negative.** Types were read from the target's load/store opcodes (lbz/lha/lhz/lwz/lfs,
  with extsb giving s8): 431 fields typed from asm vs 158 by the gap rule.
  - Motion: the same 9 compile at the same pcts.
  - The 265: mean pct of the compiled ones 53.7 -> 56.5, 0 MATCH.
- **Diff of fn_80209FC8** (objdiff, instruction by instruction):
  - The target addresses `lbl_805133B8` and `lbl_80512348` as `@sda21`. Ours uses `lis` + `@l`, which costs 2 extra
    instructions and a different register allocation, so it can never reach 100.
  - The rest of the gap is one v5 struct field: the target loads it with `lha` (s16) and v5 types it f32.
- **Cause:** the campaign compiles with `-sdata 0 -sdata2 0` (cv1.FLAGS). The census already names this as
  FLAGS_BLOCKED_SDA, and D9 left it "untested, not refuted".
- **`-sdata 8 -sdata2 8`, champion v5 sources, all 1,797:**
  - 502/502 cert1+ledger functions stay at 100.
  - The 17 search-certified sources (materialized from their receipts' paths) stay at 100.
  - **58 COMPILES_NO_MATCH become 100.**
  - All 58 come from `-sdata` alone: (8, 0) gives 58, (0, 8) gives 0, (4, 4) gives 58.
  - 0 regressions.
- **sd8 + the step-4b struct transform:**
  - The 10149 family (265) gives **5 MATCH** (0 at sdata 0) and 10 at >= 95 %.
  - Motion: still 9 compile, now 82-99 % (fn_8020A1A4 99.2, fn_8021C99C 95.9); fn_8020AAF0 stays at 7.5.
- **10499 (step 3) census, motion NO_COMPILE 46.**
  - One shape dominates: `(arg0->unk20 + (i * 0x18))->unkN`, an array of 0x18-byte records reached through a field
    typed s32.
  - Fix shape: type the field as a pointer to a 0x18-byte element struct and rewrite to `arg0->unk20[i].unkN`.
  - Errors across the 46: 10149 x163, 10141 x56, 10121 x32, 10209 x27, 10377 x23, 10499 x22.
- **U2 closed in the same session:** tam-ds-10 certified 35 by `cond-retest@1`, so the frontier went 519 -> 554
  (receipt `WU-U2-receipt.md`, GEX44 78d625bf).

### Reading
The 0-of-50 motion result was mostly an instrument fault. The campaign's pinned flags cannot reproduce any function that
touches a small global, and motion code is almost all such functions. Struct typing helps only once the flags are right.

### Proposed next unit (needs Owner go: it re-bases frozen evidence)
Re-base the toolchain flags to `-sdata 8 -sdata2 8` as an explicit, versioned input. Today cv1.FLAGS is frozen, and
V-RF-SR1-FROZEN pins cv1/fastmatch/repair/m1/cert1 at base 9ae2ed9e.
1. Make the flags part of the pinned toolchain identity (cache keys already carry them). Re-sweep v5 under sd8 as a new
   lane evidence dir, leaving the old sweeps untouched.
2. Re-certify through the existing certify path. The forecast is about 577 = 554 + 58 (the 58 is measured at objdiff
   level, not yet certified). Re-pin FR1 and SR1-FROZEN deliberately.
3. Then land the struct transform (10149) and the 0x18-stride array rule (10499) as a v6 repair lane under sd8.
4. Re-run `campaign next`.

## Step 4d -- the re-base, landed as a toolchain lane (Owner "go ahead", 2026-10-29)
Commits on GEX44 `t1/campaign`, unpushed:
- e61df767 feat TC1
- 4fdbedb8 evidence TC1
- 14c4e6c2 feat TC2
- ded1d1e8 evidence TC2
- dc01ea78 next packet 005

**Design.** `modules/recon_fabric/toolchain_sd.py` is additive.
- It sets `cv1.FLAGS` to `-sdata 8 -sdata2 8` inside its own process only. cv1, fastmatch, repair, m1 and
  evidence/cert1 stay frozen.
- It reuses CERT1's rule as is: controls before and after, a fresh-cache replay to the lane's bytes at 100, the extent
  check, and an A2 negative.
- Flags are recorded in every sweep row's key, in the summary and in each receipt.
- The champion stays v5. Projection adds `certified_by: toolchain`. A toolchain receipt lapses when the lane sweep,
  the champion sweep or the champion key moves, or when its lane row stops matching.

**Generations** (`TC_LANES`; a swept generation is frozen history):

| generation | source | compiles | MATCH |
|---|---|---|---|
| v5-sd8 | v5 | 1,059 | 560 (v5 at sdata 0: 502) |
| v5r-sd8 | v5 + `retype` (the 10149 shapes A/B) | 1,123 | 565 |

`retype` is a proven no-op on compiling sources: all 1,059 keep their key (V-RF-TC1-RETYPE-NO-OP).

**Frontier: 554 -> 612 (TC1) -> 617/1797 (TC2)** = 12 ledger + 490 cert1 + 52 search + 63 toolchain.
- 0 regressed, 0 invalidated; NO_COMPILE 738 -> 733.
- With U2, the frontier rose **519 -> 617** today.

**Gates:**
- V-RF-TC1-* 8/8. Five source mutants of the projection branch each turn it red.
- FP1, CERT1 and RR1 now count toolchain certifications beside search ones. FP1 lets toolchain rows leave NO_COMPILE,
  while search stays restricted to near-miss rows; narrowing that turns FP1 red.
- All suites green: TC1 8/8, FR1 15/15, FP1 25/25, CERT1 16/16, RR1 19/19, CP1 16/16 and --live 17/17, NEXT 24/24,
  SR1 --live 26/26.

**Motion closure now.**
- Frontier: still 0 of 50 certified.
- Lane v5r-sd8: 13 compile (was 0 at sdata 0), 3 at >= 95 % (fn_80251168 99.5, fn_8020A1A4 99.2, fn_8021C99C 95.9).
- First blockers: 10499 x11, 10149 x7, 10377 x6.

**10499 rule, measured and not landed.** It casts an integer sum `(e)->unkN` to a one-field struct pointer, with the
width taken from the target asm. 0 MATCH means it would add no certification today.
- Motion: 7/12 compile, at 46-96 %.
- All 80 functions with 10499: 19 compile, 3 at >= 95 %.

**Next unit (not started).** Run the search lane under the toolchain flags, over the toolchain lane's sources.
- search_c and the campaign still compile at sdata 0, so every near-miss in the lane (including the 3 motion functions
  at >= 95 %) is out of the search's reach.
- This changes the search's identity (root keys, stores, pins), which needs its own spec.
- Packet 005 (WIDEN 367) is the current `next`, and it is still computed at sdata 0.

## Step 4e -- TC3: search under the toolchain flags (spec `vault/specs/recon-fabric-tc-search.md`, Owner "go ahead")
Feature commit f617112f on GEX44 `t1/campaign` (unpushed). Run `v5r-sd8-sl-a6656c20d1b1-d3-p95`: the SR1 engine with
`cv1.FLAGS` switched to -sdata 8, rooted at the v5r-sd8 lane source.
- **Cohort:** 118 lane near-misses (compiles, no match, pct >= 95, not certified). Budget: 400 evals, depth 3, seed 7.
- **Outcome:** 92 EXHAUSTED, 24 BUDGET_EVALS, **2 SOLVED**, 14,503 fresh evals.
  - fn_8020A1A4 (motion, 58 insns), 99.2 -> 100 by `decl-swap@1`. It was NO_COMPILE in the frontier (10149).
  - fn_80219968, 96.5 -> 100 by `arg-passthru@1`. It was COMPILES_NO_MATCH.
- **certify-solved:** 2 candidates, 2 CERTIFIED (batch 8264f9eb9e92c001).
  - Controls were OK before and after, and the fresh-cache replay hit 100.
  - The A2 negative: n 2, 0 matches, 0 excluded.
  - Receipts are of kind `search` in `evidence/cert1-sd8/receipts.jsonl`.
- **Frontier 617 -> 619/1797** = 12 ledger + 490 cert1 + 52 search + 65 toolchain.
  - CNM 447 -> 446, NO_COMPILE 733 -> 732.
  - 0 regressed, 0 invalidated, FRONTIER_CHECK OK. FR1 re-pinned.
- **Motion closure: 0 -> 1 of 50 certified** (fn_8020A1A4). This is the first certified motion function.
  - The other two motion functions at >= 95 % did not close. fn_80251168 (99.5) EXHAUSTED its depth-3 neighbourhood.
    fn_8021C99C (95.9) ran out of evals.
- Evidence commit: GEX44 `t1/campaign` 2dbbf392 (unpushed). Suites: TC1 11/11, FR1 15/15, FP1 25/25, CERT1 16/16,
  RR1 19/19, CP1 16/16 and --live 17/17, NEXT 24/24, SR1 --live 26/26.

### KSR at -sdata 8 (read-only probe, `/tmp/d21_k9.py` on GEX44, nothing written to any clone)
Inputs:
- Sources: KSR main m2c L1 lifts (`decomp_work/b8d1db7edd42/m2c_main`). Transform: v5 + `retype`.
- Prelude: the Tennis context typedefs.
- Flags: cv1.FLAGS with sdata 8 / sdata2 8.
- Target: the KSR main split objects (`ksrmb-20261001-101754`).

Results:
- **30,388 L1 lifts, 27,530 with a target symbol. 20,547 compile, and 9,339 are at objdiff 100 (33.9 %).**
- pct bands of the compiling ones: 100: 9,339 · >=95: 1,764 · >=80: 3,172 · <80: 6,272.
- The full sweep has no sdata 0 arm (c0/p0 were not measured), so it gives no sd0-vs-sd8 delta. The 1,522-function
  sample gave 135 raw at sd0. That sample also lacked v5+retype, so the two numbers are not one A/B.
- **A defect in a frozen module:** `repair.transform_v5` raises `KeyError` in `_render` (`node.f[off]`) on 2 KSR
  sources. Tennis never reached it.
  - The first run of the probe had no per-function guard, so this one exception killed the pool at 17,712 rows. The
    probe now records it as `xf_error`.
  - repair is frozen at base 9ae2ed9e, so the fix belongs in the KSR lane's own transform, not in repair.
- Per-TU flags matter. main:800A3120 drops to 46.7 at sd8. A single global flag set would lose functions that match
  today.

**Owner decision (2026-10-29): KSR certification goes through a KSR toolchain lane** (option 2): an additive module
like TC1, with flags chosen per TU and recorded in every key and receipt, certified through the CERT1 rule. The ksrmb
job route (needs a job cap; CP50 HOLD) was not taken. The lane needs its own T2 spec before the first edit.

**Correction from the premise check for that spec** (`vault/specs/recon-fabric-ksr-lane.md`, DRAFT):
- KSR has no real TU flags. Every preset and capsule unit is sdata 0, and the targets are 303 auto-split objects. So
  "per-TU" above means per split object, chosen by measurement.
- The t1 frontier and the KSR sweep are different populations. Only 48 symbol names are shared, and 41 of those point
  at different target bytes (54 symbols are defined in more than one object across the 21 stages).
- So 9,339 is not frontier growth, and no KSR row may be joined to a t1 row by name.

## Next options (Owner decision; none started)
1. Point the campaign's next class at NO_COMPILE 10149 restricted to the motion set (25 functions), instead of the
   COUNT_DIFFERS small-function cohort U2 is on.
2. Drop exact match for the motion closure: Scope A only needs source that compiles and behaves the same, relinked
   against retail objects. That would need a behavioural-equivalence gate instead of objdiff 100 %. It changes what
   counts as done, so it is an Owner call.
3. Leave D21 parked; ALL-MATCH continues on small functions.
</content>
</invoke>
