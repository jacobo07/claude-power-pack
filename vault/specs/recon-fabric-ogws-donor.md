---
status: OG1 DONE 2026-10-29 (Owner "go ahead"). OG2 DONE 2026-10-29 (Owner "construyelo"): the names design was measured and falsified, and vtype was built from that measurement.
covers: [recon-fabric-ogws-donor, ogws-donor, og1, og2, tennis-ogws]
extends: [recon-fabric-tc-search.md, wsr-reconstruction.md]
tier: T2 (certification authority, persisted evidence, projection change)
---

# OG1/OG2: doldecomp/ogws as a donor for Tennis (SportsPackEP.dol)

## Premises (measured 2026-10-29, GEX44; probe outputs `~/tennis_twin/`)
- Tennis frontier 619/1797 (t1/campaign 2dbbf392). The Tennis DOL is Wii Sports (SportsPackEP.dol of SP2P01); ogws
  (CC0, e5a4d369) is a Wii Sports decomp. ogws has no Tennis source: `RPTnsScene` is one `_unsplit.o`.
- Matching every compiled ogws function (RP included) against the Sports DOL by size + relocation-masked bytes:
  357 Tennis functions match; 30 are uncertified. Negative control 3383/3387 (4 mutated matches still hit).
- objdiff on those 30 (probe `og_probe.py`): **6 have exactly one ogws donor and reach 100** once the donor's own
  symbol AND its relocation targets carry the Tennis target's names (`RPSysScene::init/exit/calc/reinit/
  incoming_childDestroy`, `main`), with 0 relocation offsets disagreeing. Renaming only the own symbol gives ~98.
  The other 24 are generic tiny shapes matched by 2-350 ogws functions: the bytes agree, the source is unknowable.
- RP objects need `SportsPack.mch`. It builds only when MWCC runs inside the output directory with the bare name
  `-precompile SportsPack.mch`; any path with a slash crashes wibo (`FormatMessageA`). 67/69 RP objects then compile.
- The champion lane's `retype` (toolchain_sd v5r-sd8) already gives synthetic struct types to the two 10149 shapes.

## OG1 design (build now)
1. `modules/recon_fabric/ogws_donor.py`, GEX44 clone only. Pin `OGWS_PIN = e5a4d369`; refuse when `~/ogws` HEAD
   differs or `src/`/`include/` are dirty.
   - `compile`: every completed ogws object with its own compiler version and flags, the PCH built by the bare-name
     rule. Objects and manifest go under `.local/ogws-donor/` (git-ignored, disc-free but not committed).
   - `match`: one masker for both sides (zero every word a relocation touches), donor objects vs the Tennis target
     objects of `cv1.target_index`. A candidate is a Tennis function, not CERTIFIED in the frontier, whose masked key
     equals exactly ONE ogws function. Ambiguous keys are listed with their donor count, never candidates.
     Evidence: `evidence/og1/{candidates.jsonl, ambiguous.jsonl, summary.json}`.
   - `certify` (the CERT1 rule, adapted):
     - controls: `m1.run_controls` before and after;
     - callee map: donor and target relocations must sit at the same offsets with the same types, and map each donor
       symbol to one target symbol (section-local targets on both sides are left alone). Else REFUSED `RELOC_DISAGREES`;
     - judge: the donor object with the map applied (strtab appended, the section header repointed) must get objdiff
       100 for the Tennis name. Else `NOT_100`;
     - replay: the donor source recompiled in a fresh temp dir must give the same function bytes and relocations, and
       objdiff 100 again. Else `REPLAY_DIFFERS` / `REPLAY_NOT_100`;
     - extent: `certify.disputed_extents`. Else `EXTENT_DISPUTED`;
     - A2 negative: the donor renamed onto its `cv1.neg_partners_a2` partner, judged against the partner's target,
       must not reach 100. The batch is healthy only by `certify.batch_ok`. Else every row is `INSTRUMENT`.
   - Receipts: `evidence/cert1-ogws/receipts.jsonl`. Fields: `kind: "ogws"`, verdict, reason, `ogws_commit`, the
     donor (lib, src, sym, mw, cflags sha256), donor function sha256, target object sha256, callee map, pct, replay
     pct, negative partner and its outcome, batch.
2. `projection.py`: an optional `ogws_cert` input. A receipt certifies (`certified_by: "ogws"`) only when it is
   CERTIFIED, names `ogws_commit == OGWS_PIN`, and no earlier authority (ledger, cert1, search, toolchain) holds the
   function. An unknown verdict is a hard red. Absent input = the pre-OG1 projection byte for byte.
   `fingerprint.built_frontier` leaves `ogws_cert` out, as it does the other post-view lanes.

## OG1 acceptance (each driven red -> green)
- V-RF-OG1-RENAME: renamed symbols read back. Every other symbol and every section is byte-identical.
- V-RF-OG1-CALLEE-MAP: a consistent map is built. A moved offset, a changed type and a two-way mapping are each refused.
- V-RF-OG1-UNIQUE: only single-donor keys become candidates.
- V-RF-OG1-DECIDE: the rule order, with each refusal reachable.
- V-RF-OG1-PROJECTION: certifies; a refusal, a wrong pin and an earlier authority do not; an unknown verdict is red.
- V-RF-OG1-ABSENT: no input = no `ogws` counter or input.
- A real `certify` run with healthy controls. Expected about 6 by the probe; whatever is measured is the result.
- Every existing suite stays green: TC1, FR1, FP1, CERT1, RR1, CP1, NEXT. `projection check` OK after `build`.

## OG1 result (2026-10-29, GEX44 t1/campaign a66c1c21, unpushed)
- `compile` 525/528 objects (RP 67/69, PCH built by the module). `match`: 356 Tennis functions keyed to ogws, 327 of
  them already certified, **6 candidates**, 23 ambiguous.
- `certify` batch aecfd741913cf084: **6/6 CERTIFIED**, controls OK/OK, A2 negative 6 pairs 0 match.
- Frontier **619 -> 625/1797** (`certified_by.ogws: 6`), 0 invalidated, 0 regressed, FRONTIER_CHECK OK.
- Suites: OG1 7/7 (the projection pin check mutation-drilled red, 4/5 reds caught with the check removed), TC1 11/11,
  FR1 15/15, FP1 25/25, CERT1 16/16, RR1 19/19, CP1 16/16, NEXT 25/25. FR1/FP1/CERT1/RR1 now name the new authority
  beside search and toolchain.

## OG2 result (Owner "construyelo", 2026-10-29; GEX44 t1/campaign 612e7493, unpushed)
- **The names design was falsified before any build.** The MWCC error line of each of the 169 lane 10149 functions
  (`~/tennis_twin/og2_diag.jsonl`): **0** are rooted at an ogws-named callee. The 12 that mention one
  (`fn_8004D010`) fail on an untyped local passed to it (`temp_rN->unk100`), and a callee's name does not type that.
- **The shape the measurement found instead:** shape D, `(*X)->unkN(..)` (96 virtual calls) and `(*X)->unkN`
  (7 reads). All 148 roots are declared `void **`, and no compiling lane source contains the shape. The rest:
  C local chains 30, B globals 25, global+offset 6, A 2, other 3.
- **Built:** `toolchain_sd.vtype` (lane generation v5d-sd8 = v5 + retype + vtype) casts a `void **` root to a
  synthetic vtable struct (a function pointer for a call, an s32 for a read). It needs no ogws input.
  - Sweep: compiles 1123 -> 1208, matches 565 -> 572, 0 no-op violations.
  - `certify` 70/70 (63 re-judged + 7 new); TC3's 2 search rows re-judged by `certify-solved`.
  - Frontier **625 -> 632/1797**.
  - Gates: V-RF-TC1-VTYPE (mutation-drilled red) and V-RF-TC1-VTYPE-NO-OP. Every suite green, SR1 included.
- **TC3 search on the v5d near-misses (ended 2026-10-29 23:03, GEX44):** run `v5d-sd8-sl-a6656c20d1b1-d3-p95`, cohort
  152 at >= 95 %: **0 solved**, 128 EXHAUSTED, 24 BUDGET_EVALS; `solved.jsonl` is empty. Nothing to certify, so the
  frontier stays 632/1797. The same search solved 2 on the previous lane, so it can return a solve.

## OG3 probe (Owner "haz ambas", 2026-10-30; read-only, GEX44 `~/og3_diag.py`, `~/og3_probe.py`, own cache dirs)
- v5d lane, 1165 uncertified, 588 NO_COMPILE. First errors: 10209 x116, none x92, 10377 x75, **10149 x72** (was 169 before
  vtype), 10499 x66, 10140 x65. Root declarations of the 72: `void **` with `X->unkN` (shape E) 18, global+offset /
  array index 9, `extern u8 lbl[]` used as `lbl.unkN` (B2) 5, typed struct params whose field is itself untyped ~20.
- Probe: shape E cast at the use site `((O_X *)X)->unkN` (a declaration retype would rescale `X + 0xA04`), the chained
  `X->unk0->unkM(..)` given a function-pointer vtable, and B2 cast as `((A_lbl *)lbl)->unkN`. Field type s32.
  - Changes 47 functions; **21 now compile, 0 match**; 3 at >= 95 % (fn_8024DE84 97.8, fn_8027AFD0 96.6, fn_802293D0 96.0).
  - `void *` fields: 5 compile, 0 match (s32 strictly better).
  - First error after the cast: 10209 x10, 10140 x5, 10149 x3. The type error was the first of several.
- **Not built as a lane generation:** it certifies nothing directly. Its only route to the frontier is a TC3 search on 3
  near-misses, and that search just went 0/152 on the v5d near-misses. Next lever by count: 10209 (116 first errors).

## OG2 original draft (superseded by the result above): real names and types for the NO_COMPILE families
- **Measured 2026-10-29 on the toolchain lane (v5r-sd8, after retype):** 1172 uncertified; 673 NO_COMPILE in the
  lane; first errors 10149 x169, 10209 x112, 10377 x73, 10499 x64, 10140 x64. Of the 169, **38 call an ogws-named
  callee**, and 7 call `fn_800B7AD4`, which ogws does not name. Of all 673 NO_COMPILE, 160 call a named callee.
  Calling a named callee does not make it the cause of the error, so 38 is a ceiling for the 10149 family, not a
  forecast.
- Input: the 127 callees of uncertified Tennis functions that get a unique ogws name (probe, masked bytes), and
  ogws's headers for their classes.
- Measure first, under the lane that matters: the 10149 count in the toolchain lane sweep (v5r-sd8, after retype),
  not the champion's 259. Then measure how many of those functions call a named callee. If the overlap is small,
  stop there.
- Design: a typed-prototype layer for named callees (return types, `this` classes) composed before the lane source,
  for functions that call them; swept as a new lane generation and certified by the existing lane rule.
- Known limit: the controller getter `fn_800B7AD4` (40 of the 10149 errors) gets no ogws name.

## Out of scope
The 24 ambiguous shapes, names in `symbols`/views, pushing.

## Rollback
Revert the commits. OG1 evidence lives in new paths only; with `evidence/cert1-ogws/` removed the projection is the
pre-OG1 one.
