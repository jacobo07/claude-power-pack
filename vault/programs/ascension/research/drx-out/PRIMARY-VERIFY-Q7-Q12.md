# Primary-source check of DRX Q7-Q12 (2026-11-14, session 423c9c50)

DRX Q7-Q12 (commit 99ad1f0f) reached few primary sources (DuckDuckGo only). The decisive ones were fetched
directly (gh api raw / git clone, read as data) and the DRX quotes compared against the real files.

| Claim (DRX ledger) | Primary file, line | Verdict |
|---|---|---|
| SMG1 (a Wii game) links game code built with GC 3.0a3, RVL_SDK/NW4R/JSystem/MSL with GC 3.0, MetroTRK with GC 2.5; picked per library by build date, codegen trial and SDK init build strings (Q12 C1/C2) | SMGCommunity/Petari.wiki `CodeWarrior.md` L1-15 | VERBATIM |
| dtk-template sets the compiler per object: `mw_version` option, default `config.linker_version`, compiler path `compilers/$mw_version` | encounter/dtk-template `tools/project.py` L65, L98, L668, L1033 | CONFIRMED |
| Statics are allocated in reverse declaration order (Q8 C11) | PrimeDecomp/mwcc-tools `gc2/docs/matching-guide.md` L193 | VERBATIM |
| MWCC emits a literal at first use and pools equal literals within a unit (Q8 C10) | same file L213 | VERBATIM |
| Auto-inline limit counts statements; 10 at nesting level 1, 7 at level 2 (Q8 C12) | same file L121-123 (the guide is for its gc2 reference compiler; check our build) | VERBATIM |
| Residual swaps/extra instructions can come from wrong inline usage; TWW recovers inlines from a kiosk-demo debug map, each inline listed once per map (Q9 C24) | zeldaret/tww `docs/decompiling.md` L177, L183, L249 | VERBATIM |

Grade: E3 (a primary practitioner source states it). E4 only once our pinned mwcc + objdiff reproduces it.

## Experiments this licenses (ranked)
1. B-COMPILER: per-library compiler sweep (GC/2.5, GC/3.0, GC/3.0a3, Wii/1.x) over KSR CNM + NO_COMPILE functions in SDK/NW4R/MSL/MetroTRK units. Our certifier pins Wii/1.7 for everything; Petari shows that a Wii title can use GC builds per library. Look for SDK init build strings in the DOL first, since that is the cheapest signal.
2. Integrity: mutation test of reloc_oracle (change one `.sdata2` constant or one pointed-to table entry; it must reject). Q9 C16 shows code + relocation identical with different pointed-to data.
3. B-FLAGS: `.bss` reverse-order and literal-pool resets as unit-boundary signals on FLAGS_SPLIT.
4. B-CNM: split CNM into frame-only / code / structural before spending variant search (Q12 C6, decomp-triage SMS; not yet fetched).
