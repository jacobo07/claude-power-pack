# TENNIS-TOOLCHAIN -- compiler fingerprint for SportsPackEP.dol (W3 step 2, PLAN mode, 2026-10-11)

## Premise correction
The binary is NOT 2006 Wii Sports code. SportsPackEP.dol (Sports Pack, EU) embeds SDK build strings `RVL_SDK - <lib> release build: ... (0x4302_145)`
dated **Dec 11 2009** (KPAD, WPAD, GX, OS, VI, AI, AX, DSP, DVD, EXI, NAND, SC, SI), HBM May 19 2010 (0x4302_145), RFL Jan 29 2010 (0x4302_162),
NWC24 Jun 9 2009 (0x4199_60831). Resort (R0 relink of the factory split, same extraction as the pins) carries the same SDK build id **0x4302_145**
with dates Feb-Mar 2009 (KPAD/WPAD Mar 25 2009), HBM 0x4201_142, RFL/NWC24 Nov 2008 / 0x4199_60831.
Command: regex `<< RVL_SDK - (\w+) release build: <date> (<id>)` over both DOLs (scratch wst_tennis/w3, script w3_f/w3_g).

## Evidence for the same compiler family
- Same SDK build id 0x4302_145 on 13 of 16 libs; Tennis SDK is a ~9-month-later point release of the same line. Metrowerks CW runtime strings present.
- Step0 shape comparison (instruction text with symbols masked): 408 of 1,797 Tennis functions have an EXACT Resort shape (11,935 of 18,820 whole DOL).
  Shape equality across two independently linked games is only possible with identical code generation for those bodies. Loose matches add 166 more
  (Tennis candidate) -- same idioms, different constants.
- Control for the claim: 179 of the 408 exact matches have a donor already SRC PROVEN in the factory (mwcceppc f54d5644...). All are 1-2 insn bodies
  (blr stubs and trivial accessors), so this proves the compiler emits the same bytes for trivial bodies; it does NOT discriminate between two nearby
  mwcc builds.

## Candidate
- Compiler: the Resort pin, `mwcceppc.exe` sha256 f54d5644d14609f385e8fefd3eb11e50a689b888a0d06dfc0a30cf0fc5a204d7 (TOOLS.json), with the Resort flag set
  from pins.json. **Confidence: MEDIUM-LOW (60%)** -- same SDK line and 408 exact shapes, but the exact-shape set is dominated by trivial/SDK-shared bodies.
- Flags: UNKNOWN for Tennis-specific code (no evidence beyond the Resort set). Unit-level flag differences (-O4,p vs -O4,s, inline settings) are
  untested: the discriminating test is a non-trivial exact-shape function (>= 20 insns); none exists with a PROVEN donor (max donor size 2).
- Known community facts: not cited (no external lookup made).

## Falsifier / what W5 must route around
Tennis A/A on a 1-2 insn body cannot falsify a compiler mismatch. If the A/A passes, claim only "oracle reproduces trivial Tennis objects".
A real discriminator needs an exact-shape Tennis function of >= 20 insns whose Resort donor gets SRC proven (14 such exact-shape sample rows exist
in the sample, none donor-proven).