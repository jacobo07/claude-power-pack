---
status: DRAFT 2026-10-29 (route chosen by Owner, "KSR toolchain lane"; this design needs an Owner go before the first edit)
covers: [recon-fabric-ksr-lane, ksr-lane, ksr-toolchain-lane, ksr-certification]
extends: [recon-fabric-tc-search.md, d21-step4-motion-closure-vs-frontier-2026-10-29.md]
tier: T2 (certification authority, new persisted population, gate changes)
---

# KSR lane: certify KSR main functions under a flag set measured per object

## Objective
Certify KSR main functions (the m2c_main L1 lifts) through the CERT1 rule. The flag set is chosen per target object
by measurement. The result is a separate population with its own frontier, and is never merged into the t1 frontier by
symbol name.

## Premises (measured 2026-10-29 on GEX44, `~/missions/t1-campaign` @ 2dbbf392)
- **Population.** `decomp_work/b8d1db7edd42/m2c_main/results.tsv`: 30,388 L1, 2,522 M2C_ERROR, 1,249 M2C_FAILED.
  Against stage `ksrmb-20261001-101754`, 27,530 of the L1 lifts have a target symbol.
- **Sd8 result** (v5 + retype, Tennis-context typedef prelude): 20,547 compile and 9,339 reach objdiff 100. There was
  no sd0 arm on the full set.
- **No real TU flags exist.** The capsule's 5 presets and all 298 units carry `-sdata 0 -sdata2 0` (296 O4p, 2 O2).
  Targets are 303 auto-split objects (`auto_03_<addr>_text.o`), not translation units. So per-object flags must be
  measured; nothing can be read from a source of record.
- **A bare symbol is not an identity.**
  - Across the 21 `ksrmb-*` stages there are 313 object basenames, and 54 symbols are defined in more than one object.
  - `cv1.target_index()` keeps the latest basename per symbol.
  - Of the 48 symbol names shared by the t1 frontier and the KSR sweep, only 7 have identical target bytes, and only 6
    resolve to the same object basename.
  - 1,745 of the 1,797 t1 functions are ABSENT from m2c_main. The t1 population is mostly code outside main.dol.
- **Arm conflicts are rare but real.** In the 1,522-function sample (v5 + retype): 445 match on both arms, 58 only at
  sd8, 1 only at sd0 (fn_800A3120: 100 at sd0, 46.7 at sd8).
  - One object of 245 (`auto_03_80007EE0_text.o`) holds both an sd0-only and an sd8-only match.
- **Frozen-module defect.** `repair.transform_v5` raises `KeyError` in `_render` (`node.f[off]`) on 2 KSR sources.
  repair is frozen at base 9ae2ed9e (V-RF-SR1-FROZEN).
- **Tennis-bound pieces of CERT1:**
  - `m1.run_controls` takes its reference pool from the t1 compile log.
  - `certify.disputed_extents` reads the t1 ledger.
  - The rest is generic: `cv1.judge`, `cv1.neg_partners_a2`, `certify.batch_ok`, `certify.neg_outcome` and the
    objdiff call.

## Design
1. **Identity.** A KSR row is keyed by entity id `main:<ADDR>` plus the stage id, the target object path and that
   object's sha256. The symbol is a field, never a key. A row whose symbol resolves to a different object under
   `cv1.target_index()` is still judged against its own pinned object. It is never compared with a t1 row.
2. **Inputs are pinned.** Each run records:
   - the m2c_main `results.tsv` sha256;
   - the stage id;
   - the prelude header sha256;
   - the transform generation;
   - each arm's flags.

   A moved input refuses to resume.
3. **Transform.** `ksr-v5r` = `toolchain_sd.retype(repair.transform_v5(src))`, called through a guard. An exception
   yields a row `XF_ERROR:<ExceptionName>` and never stops the sweep. repair is not edited. The 2 KeyError sources stay
   XF_ERROR until a lane-local fix lands with its own gate.
4. **Two arms, then a choice per object.**
   - Every function is measured at sd0 and at sd8.
   - Each target object then gets one flag set: the arm with the most matches, provided the other arm has no match the
     chosen arm loses.
   - When both arms hold exclusive matches, the object is `FLAGS_SPLIT`. Nothing in it certifies, and it is reported
     by name. An auto-split object may join two real TUs.
   - A flag choice per function is refused. A TU compiles with one flag set, so a choice per function would overfit to
     objdiff.
5. **Certification, using the CERT1 rule on KSR inputs.**
   - **Controls before and after:** a KSR pool of positive controls, the capsule units of kind `sealed` and `donor`,
     each compiled with its own preset and expected to hit its `local_object_sha256`. Negative controls are the A2
     partner swap.
   - **Replay:** a fresh-cache replay under the object's chosen flags must give the swept object bytes at 100.
   - **Extent check:** the compiled function size equals the size of the target symbol in the pinned object. This
     replaces `disputed_extents`, which is t1-ledger-bound.
   - **A2 negative:** `cv1.neg_partners_a2` over the KSR pool.
   - **Batch health:** `certify.batch_ok` as is.
6. **Evidence (new paths only):**
   - `evidence/ksr-lane/<gen>/{run.json, sweep.jsonl, objects.jsonl}`;
   - `evidence/cert1-ksr/{receipts.jsonl, summary.json, controls-log.jsonl}`;
   - `evidence/ksr-frontier/{frontier.jsonl, counters.json}`.

   The t1 frontier, FR1's pins and every frozen file are untouched.
7. **Code.** A new module `modules/recon_fabric/ksr_lane.py` in the t1-campaign clone.
   - CLI: `sweep | choose | certify | project | check`.
   - It is additive. cv1, fastmatch, repair, m1, toolchain_sd and evidence/cert1 are not edited.

## Acceptance (each driven red -> green)
- A1 V-RF-KSR-IDENTITY: a real colliding symbol (fn_80203C0C) is judged against its own pinned object. A lane copy
  keyed by bare symbol turns the gate red.
- A2 V-RF-KSR-XF-GUARD: a source that makes the transform raise yields `XF_ERROR`, and the sweep goes on. Removing the
  guard turns the gate red on the real KeyError source.
- A3 V-RF-KSR-FLAG-RULE: on fixtures, exclusive matches on both arms give `FLAGS_SPLIT`, and a one-sided object takes
  its winning arm. A per-function choice is refused. The real `auto_03_80007EE0_text.o` is FLAGS_SPLIT.
- A4 V-RF-KSR-CONTROLS: real capsule units pass as positive controls, and a unit with one flipped byte fails.
- A5 V-RF-KSR-REAL: a real run certifies >= 0 functions with healthy controls. 0 is a valid measured result.
- A6: every existing suite stays green: TC1, FR1, FP1, CERT1, RR1, CP1 (and --live), NEXT, SR1 --live. The t1
  frontier `rows_sha256` is unchanged.

## Out of scope
- Merging KSR rows into the t1 frontier. A later unit would need an identity map by target bytes, not by name.
- A search lane on KSR near-misses.
- The ksrmb job route.
- Fixing repair.
- Pushing.

## Rollback
Revert the commits. Evidence lives in new paths only.
