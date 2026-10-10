# WU-W4 -- REA disposition canary (zero GEX44 jobs)

Common brief: `PROGRAMME.md`. Plan sections 1 (REA row), 4. Small unit: stop at the first conclusive answer.

Facts read 2026-10-11 from upstream morluto/rea (MIT, release rea-agents-6.3.0 2026-10-09, HEAD 9515d2fcd398):
Windows native lane = x86/x86-64 PE with Ghidra 12.1.x + JDK 21+; ELF lanes are per architecture (MIPS documented);
no doc read mentions PowerPC. Upstream refuses unsupported targets with a named constraint.
1. Install `rea-agents@6.3.0` into an isolated npm prefix under `C:\Users\User\Apps\rea-6.3.0` (never global, never
   latest). Node is v24.15.0 (supported). Do not register its MCP server or skills globally.
2. One target-resolution / capability call on SportsPackEP.dol and one on a DTK split `.o` (ELF32 PPC) with the
   Ghidra provider pointed at `C:\Users\User\Apps\ghidra_12.1.2_PUBLIC` (REA verified 12.1.4; record if 12.1.2 is
   refused). Save the raw output under `vault/programs/tennis-rf/evidence/rea/`.
3. Write `REA-DISPOSITION.md`: per capability USE_DIRECTLY / ADAPT / WRAP / EXTEND_UPSTREAM / OVERLAY_CPP / NO_WORK /
   REJECT, with the tool's own output as evidence; pinning record (repo, version, providers, limits, update strategy).
   If PPC is refused: disposition REJECT for native evidence, and draft (do not file) an upstream issue text for a
   PowerPC big-endian / DOL lane in the same file. If it is admitted: run 3 representative queries (function list,
   one pseudocode, xrefs of one KPAD getter from step3) and compare with DTK/m2c on evidence quality and size.
4. Do not install Hopper or IDA. Do not upgrade Ghidra.
Receipt: the disposition line, evidence paths, install path (or removal if REJECT and unused).
