---
status: APPROVED 2026-10-29 (Owner: "KSR es Wii Sports Resort modificado, simplemente reconstruyamos WSR y modifiquemoslo desde ahi"; then picked base 7752caae verified, milestone rebuild + shiftable, a new private repo, D21 continues in parallel)
covers: [wsr-reconstruction, wsr-decomp, wsr-rebuild, wsr-shiftable]
extends: [recon-fabric-ksr-lane.md, recon-fabric-ksr-atlas.md]
tier: T3 (new project and repo; it becomes the substrate KobiiSports Resort is modified from)
---

# WSR reconstruction: rebuild Wii Sports Resort (RZTP01) from source, then modify it

## Objective
Build a project that links a byte-identical WSR `main.dol` from split objects, so the game can be modified at the
source level. KobiiSports Resort then moves from Kamek patches onto that source. C replaces asm one function or one TU
at a time. Matching is not a prerequisite for modding.

## Premises (measured 2026-10-29)
- **The base is verified.** The Redump-named dump `Wii Sports Resort (Europe) (En,Fr,De,Es,It) (Rev 1).wbfs`:
  - its sha1 is 1f16a04d975c01786c0decefe2c71e5857539147;
  - wit reports it as PAL, 1 partition, "well signed";
  - it holds a `main.dol` with sha1 **7752caaecc890cf6c1b6e6841ae5fe2c42c1ac44**, 7,338,240 bytes. This is byte-identical
    to the DOL that m2c_main and the KSR lane used.
- **The disc's 7 RELs are all `sys/mpls_movie/rels/d_*NP.rel`.** The game is in main.dol.
- **KSR's own builds** are this DOL plus section 17 (0xE60 bytes at 0x80001900) and 5 patched words: the Kamek loader
  and its hooks. `files/modules/main_PAL.bin` is the Kamek module ("Kame" magic), and `main_PAL.map` is that module's
  map, not a retail map. Retail WSR has no symbols.
- **No public WSR decomp exists** (searched GitHub 2026-10-29). The closest relative is doldecomp/ogws (Wii Sports,
  CC0, about 28 % decompiled), which shares EGG, nw4r and the RVL SDK.
- **Assets in hand:**
  - 8,687 KSR functions certified byte-exact (KSR lane), under flags chosen per object;
  - the ka1 atlas (757 decoded accessors, 55 class candidates).
- **GEX44 tooling:** git, ninja, Python 3.12, network, wit. MWCC and objdiff are in the KSR stage tools. There is no dtk
  and no cargo.

## Design
1. **Repo:** a new private repo `wsr-decomp` from encounter/dtk-template (Apache-2.0/MIT). It is built on GEX44 and
   mirrored to `Wii Projects/`.
   - No game data is ever committed: `orig/` is gitignored and the DOL comes from the Owner's dump.
   - Version `RZTP01`. The config pins sha1 7752caae.
2. **M1, byte-identical rebuild.** dtk analyses `main.dol`, splits it into asm objects with relocations, and links.
   - DONE = `ninja` exits 0 AND `build/RZTP01/main.dol` has sha1 7752caae.
   - A one-byte edit to a split object must make the hash check fail (the red pole).
3. **M2, shiftable.** A build with code added (or one section moved) still has every reference relocated.
   - DONE = that build boots in Dolphin to the same first screen as retail, with screenshot evidence. A diff of the
     shifted DOL against retail shows only relocated differences.
   - Bad pointer recovery in data is the known risk. dtk's analysis is fixed by symbols and splits config, never by
     patching bytes.
4. **M3, C in.** Each source enters only on objdiff 100 for its unit, inside the dtk project. Sources, in order of
   evidence:
   - ogws donors (EGG, nw4r, RVL SDK) matched by masked target bytes;
   - the KSR lane's 8,687 certified functions;
   - search and decomp-permuter on near-misses;
   - coddog to cluster duplicates.

   The KSR lane's per-object flags become per-TU flags only where the dtk splits make the TU real.
5. **M4, KSR on source.** Kamek keeps working on the retail DOL throughout. A KSR feature moves into source only after
   M2, and each move is verified in Dolphin.
6. **D21 runs in parallel** (Owner), untouched by this project.

## Acceptance
- M1: the rebuilt sha1 equals 7752caae; the red pole is driven; `orig/` is not tracked (`git ls-files orig` is empty).
- M2: a Dolphin boot screenshot of the shifted build matches the retail one at the first interactive screen.
- Each later milestone gets its own spec section before it starts.

## Out of scope (now)
- Pushing to GitHub. Repo creation and the first push are Owner-gated (ovo-push-gate).
- A matching percentage target.
- RELs (movie player only).
- Assets.

## Rollback
Delete the new repo. Nothing existing is edited.

## State
- **M1 DONE 2026-10-29.** GEX44 `~/wsr-decomp`, branch `main`, commit 7938d32. It is mirrored to
  `Wii Projects/wsr-decomp` (origin = gex44). The template remote has push disabled.
  - **Result:** `ninja` exits 0, and the rebuilt `main.dol` sha1 is 7752caae. All 11 DOL sections, bss and entry are
    identical.
  - **Analysis:** dtk v1.8.3 found 34,159 functions and wrote 877 objects.
  - **Fixes:**
    - Section 11 (0x80654880, 0x1460) is a Yaz0 blob, renamed `.rodata0`.
    - `Runtime.PPCEABI.H/__init_cpp_exceptions.cpp` got its split with `.ctors$10`, `.dtors$10` and `.dtors$15`.
      Without it, the first ctor and dtor entries were dropped and everything after them shifted 0x40.
  - **Linker:** all 9 Wii linkers give the identical DOL, so Wii/1.0 is set but not evidenced.
  - **Red pole:** one byte flipped in a linked object fails CHECK, and restoring it passes. Editing
    `build/RZTP01/asm/*.s` does not reach the link: those files are reference only.
  - **Tracking:** `orig/` tracks only `.gitkeep`.
- **M2 DONE 2026-10-29** (wsr-decomp 58ae485).
  - `src/wsr_shift.c` is linked first, only with `--non-matching`, and needs `#pragma force_active on`. Without it the
    probe is deadstripped and the "shifted" DOL is byte-identical to retail, which would make a boot test vacuous.
  - Shifted DOL e1c15139: `.text` grows 0x1A0, and 67,553 of 67,844 symbols move.
  - `tools/wsr_shiftcheck.py`:
    - 49,814 in-image data pointers are relocated;
    - 10 words stay UNRELOCATED, and none is a real pointer (9 point at odd addresses inside functions, 1 is an extab
      encoding word);
    - the 8 OTHER are the checker's own `.ctors`/`.dtors` mapping, checked against a direct dump.
  - **Dolphin (GEX44, boot, 45 s):** retail and shifted both PASS, and both reach the same title screen. The pixel
    differences (RMSE 2-6 %) are the animated background.
  - Not shown: gameplay beyond the title screen under a shifted build.
- **Next: M3 (C in).** The Owner picked option 1, the ogws donors.

## M3a -- ogws donor probe (spec section; Owner pick "1", 2026-10-29)
- **What:** compile doldecomp/ogws (CC0) C/C++ sources with ogws's own per-library compiler versions and flags, using
  the compilers dtk already downloaded. No Wii Sports DOL is needed for that.
- **Comparison:**
  - Hash every compiled function with relocated bytes masked (from the object's own relocation table).
  - Compare with every WSR function, masked the same way from the wsr-decomp split objects.
  - Size must be equal, and masked bytes must be equal.
- **Output (read-only, nothing linked into wsr-decomp):**
  - per library: matched functions out of compiled functions;
  - TUs whose every compiled function matches WSR in the same order (a candidate real TU, with the name, flags and
    compiler version ogws uses);
  - collisions where one masked hash maps to more than one WSR function.
- **Gate:**
  - A control must hit: a compiled function that ogws itself marks Matching is expected in WSR if WSR uses that
    library version.
  - The negative control must miss: the same function with one instruction changed.
  - A 0 result counts only if the positive control hits.
- **Then M3b:** link the matching TUs as C into wsr-decomp, one TU at a time, and keep sha1 7752caae on the matching
  build.
- **M3a RESULT 2026-10-29** (ogws e5a4d369; scripts and README in wsr-decomp `tools/m3a/`).
  - 458 of 459 ogws library objects compiled. HBMBase.cpp needs sjiswrap. RP game code is excluded.
  - 6,147 functions compiled; 2,563 match WSR by masked bytes, 1,197 of them uniquely. 689 of the matches are <= 8
    bytes, so they are weak evidence.
  - Controls:
    - the positive control: sampled WSR functions find themselves;
    - the negative control: 2,513 of 2,513 matches with one word flipped miss.
  - Contiguous, ordered TUs in WSR: **50** (93 functions, 9,412 bytes; RVL_SDK 32, MSL 7, nw4r 9, Runtime 1,
    RVLFaceLib 1), plus 11 made only of tiny functions. 392 TUs are not contiguous.
  - **Reading:** WSR (2009) carries newer nw4r, EGG and SDK than Wii Sports (2006). Whole-TU donation is therefore small.
    The large yield is names: 1,197 unique function matches give WSR functions their real (mangled C++) names. That
    feeds the atlas's class grouping and the Kamek headers.
  - GC/3.0a5.2-compiled ogws code matches WSR bytes, which is evidence about WSR's library compiler.
- **Next (Owner pick):** M3b-names (rename the 1,197 uniquely matched functions in symbols.txt: no byte change, and
  sha1 must stay 7752caae) and/or M3b-TUs (link the 50 contiguous TUs as C).
