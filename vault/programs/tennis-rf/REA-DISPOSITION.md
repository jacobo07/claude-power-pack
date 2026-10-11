# REA-DISPOSITION (WU-W4) -- 2026-10-11

**Disposition line: REJECT (native PPC evidence). REA unusable on this host and, by static read, has no PPC/DOL lane. Zero GEX44 jobs.**

## Evidence (tool's own output; supersedes the earlier "help hangs" note, which was a transient/unreproduced observation)
- Install: `rea-agents@6.3.0` via pnpm into `C:\Users\User\Apps\rea-6.3.0` (global npm corrupt, `evidence/rea/npm-install-fail.log`); nothing global.
- SportsPackEP.dol -> `code: target_unavailable`, "unsupported binary format" (`evidence/rea/inspdol.out`, `inspdol2.out`).
- DTK split `auto_03_800071C0_text.o` (ELF32 PPC) -> `target_unavailable`, "unsupported ELF architecture" (`evidence/rea/inspo.out`).
- Ghidra 12.1.2: REA accepted the version as compatible 12.1.x; the provider stays unavailable because JAVA_HOME is JDK 17 and REA needs 21+. Not changed (target refused before provider). `doctor*.out`, `caps.out` hold the capability matrix.
- Static corroboration: `dist/` mentions powerpc/ppc only in Mach-O fat parsing; no DOL parser.
- Function list / pseudocode / xrefs comparison not run (targets refused).

| Capability | Disposition |
|---|---|
| DOL / ELF32-PPC target resolution | REJECT now (named refusal); EXTEND_UPSTREAM if wanted |
| function list / pseudocode / xrefs | NO_WORK (keep DTK + m2c + existing Ghidra) |
| Hopper / IDA | not installed |
## Pinning
morluto/rea MIT, rea-agents 6.3.0 (HEAD 9515d2fcd398). Providers exercised: none. Update strategy: revisit only if upstream adds PPC BE/DOL lane.

## Draft upstream issue (NOT filed)
Title: PowerPC big-endian (Gekko/Broadway) lane: GameCube/Wii DOL and ELF32 EM_PPC
Body: Targets are Nintendo `.dol` (custom header, no ELF) and ELF32 PPC relocatables from decomp-toolkit splits. Ask: a named-constraint refusal today, and a Ghidra-provider lane (PowerPC:BE:32) plus DOL loader. 

## Receipt
REJECT; evidence `vault/programs/tennis-rf/evidence/rea/`; install dir `C:\Users\User\Apps\rea-6.3.0` removed (unused).

## Owner note 2026-10-11
REJECT = capability gap with a certification path (backlog D27), not REA discarded. Re-probe on the current upstream release before any patch.
