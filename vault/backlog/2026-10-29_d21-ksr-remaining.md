# D21 / recon fabric: everything still open after TC3 and the KSR lane (2026-10-29)

Source of truth for the results: `vault/plans/d21-step4-motion-closure-vs-frontier-2026-10-29.md` (steps 4 to 4f) and the
specs `vault/specs/recon-fabric-tc-search.md` and `vault/specs/recon-fabric-ksr-lane.md`.

## State at write time
- PP HEAD 91638070 on `feature/knowledge-acquisition`.
- GEX44 clone `~/missions/t1-campaign`, branch `t1/campaign` at 252a2652. **Every commit of the day is unpushed:**
  - e61df767, 4fdbedb8: TC1 feat and evidence;
  - 14c4e6c2, ded1d1e8: TC2 feat and evidence;
  - dc01ea78: next packet 005;
  - f617112f, 2dbbf392: TC3 feat and evidence;
  - ae6b70d7, 252a2652: KSR lane feat and evidence;
  - 5b851691, 1c00a895: KSR atlas ka1 feat and evidence (added after write time, item 12). The branch is now at 1c00a895.
- t1 frontier: **619/1797** certified (12 ledger + 490 cert1 + 52 search + 65 toolchain).
- D21 motion closure: **1 of 50** certified (fn_8020A1A4). Scope A is still **NOT ADMITTED**.
- KSR frontier (its own population): **8,687 certified** of 30,388 L1 lifts.

Before acting on any item, re-read the evidence on GEX44. Nothing below has been started.

## Items, in rough order of leverage

1. **Re-split the 6 FLAGS_SPLIT KSR objects.** They hold 3,447 functions and 652 matches. 202 of those matches are
   exclusive to one arm, so per-object flags cannot certify them.
   - The objects: `auto_03_80007EE0` (3,928 functions in the stage), `auto_03_800C4EE4` (1,381), `auto_03_8024B5E8`,
     `auto_03_8024EC64`, `auto_03_80288810` and `auto_03_8039ECA0`.
   - Idea: split each one at the address boundary between its sd0-exclusive and sd8-exclusive runs, then re-choose.
     It needs a spec. A split is a claim about real TU boundaries, so it must be evidenced, never fitted to objdiff.
2. **A KSR search lane** (the TC3 analogue) on the 9,941 KSR COMPILES_NO_MATCH rows. In the sd8 probe, 1,764 KSR
   functions sat at >= 95 %. It needs its own spec, because search identity (root keys, stores) would now be keyed by
   entity and object, not by symbol.
3. **Deeper search on the two t1 motion near-misses that did not close:**
   - fn_80251168 (99.5 %) EXHAUSTED its depth-3 neighbourhood;
   - fn_8021C99C (95.9 %) ran out of evals at 400.

   Re-run TC3 on these two with depth 4-5 and a larger budget, or add a mutation operator aimed at their diff.
4. **Land the 10499 rule and the v6 repair lane under sd8** (step 4c "next unit" points 3 and 4b).
   - The struct transform for 10149 is measured; 10499 is a 0x18-stride array, `arg0->unk20[i].unkN`.
   - 10499 was measured and not landed: 7 of 12 motion functions compile, at 46-96 %. Across all 80 functions with
     10499, 19 compile and 3 reach >= 95 %. 0 MATCH, so it gives search roots, not certifications.
5. **Point the campaign at the toolchain flags.** `campaign next` still computes at -sdata 0: packet 005 (WIDEN 367)
   predates TC1-TC3. Changing the campaign's SL and pins was out of scope for TC3 and needs its own unit.
6. **Lane-local fix for the 2 KSR XF_ERROR sources** (main:8055C704, main:80563754). `repair.transform_v5` raises
   `KeyError` in `_render` at `node.f[off]`. repair is frozen (V-RF-SR1-FROZEN), so the fix belongs in a KSR transform
   generation with its own gate.
7. **2,858 KSR NO_TARGET lifts.** These L1 lifts have no symbol in the pinned stage `ksrmb-20261001-101754`. Check
   whether other stages, or a different symbol naming, hold them before calling them absent.
8. **The m2c_main lifts outside the lane:** 2,522 M2C_ERROR and 1,249 M2C_FAILED. The lane covers L1 only.
9. **Identity map between KSR and t1 by target bytes.** This was out of scope for the KSR lane. 7 of the 48 shared
   names have identical target bytes, so a merged count must join on bytes, never on names.
10. **D21 Scope A, an Owner decision** (still open from step 4):
    - aim the campaign's next class at the motion set;
    - drop exact match for a behavioural-equivalence gate;
    - or park D21.
11. **KSR certify speed.** `ksr_lane certify` still uses a thread pool, which is GIL-bound on objdiff's JSON: 710 s
    for 8,687 candidates. Move it to the sweep's process pool before any larger run.
12. **KSR class-layout atlas, narrowed** (Owner pick 2026-10-29; spec `vault/specs/recon-fabric-ksr-atlas.md`).
    - Population: 778 certified KSR accessors with receiver `arg0` (237 getters, 326 setters, 215 initialisers).
    - Field offset and width come from the target asm. 216 getters start with lwz, 20 with lbz, 1 with lhz.
    - Class grouping was weaker than proposed:
      - Only 17 initialisers store a vtable at +0 (16 distinct), and 0 accessors are vtable slots.
      - Grouping by co-receiver call sites gives 73 candidate classes (220 accessors, largest 10, 35 with an
        initialiser). The other 558 stay UNGROUPED.
    - Out of scope: emitting Kamek headers, and the t1 10149 retype, which needs item 9 first.
    - **DONE as ka1** (D21 plan step 4g; GEX44 5b851691 + 1c00a895, unpushed):
      - 757 OK and 21 ASM_DISAGREE;
      - 55 CANDIDATE classes holding 136 accessors, 0 CONFLICT;
      - 621 UNGROUPED, 16 vtable anchors;
      - V-RF-KA 8/8, mutants 7/7.

      Prototypes were excluded from the call sites, which shrank the probe's 220/73. Open: a ka2 that tracks
      `mr rX, r3` receiver copies, to recover the 21.

## Debt
- **Push and hand-back of the GEX44 commits** (list above). Push needs the Owner: `ovo-push-gate` blocks pushes from
  inside ssh. The laptop can `git fetch ssh://gex44/home/kobii/missions/t1-campaign t1/campaign`.
- **Evidence size.** The KSR lane commit adds about 30 MB (sweep 19 MB, cert1-ksr 6.9 MB, frontier 3.7 MB). Decide
  before pushing whether it stays in history or moves to a compressed or ignored location.
- ~~**`campaign --help` runs a default pin**~~ **FIXED** in GEX44 0a809dc8 (unpushed).
  - Precisely: `campaign <sub> --help` ran the subcommand on tam-ds-1, so `run --help` launched a run.
  - Gate V-NEXT-HELP-RUNS-NOTHING, RED -> GREEN. NEXT 25/25, CP1 16/16, CP1 --live 17/17.
  - With it, the branch is at 0a809dc8, and 13 commits are unpushed.
- **Throwaway probe scripts in GEX44 `/tmp`** (`d21_*.py`, `ksr_*.py`, `atlas_probe*.py`, `/tmp/d21_ksr_full_sd8.jsonl`). The KSR lane
  sweep supersedes them. Delete them once the evidence above is pushed.
