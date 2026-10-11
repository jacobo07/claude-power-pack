# REA-DISPOSITION (WU-W4) -- 2026-10-11

**Disposition line: REJECT (native PPC evidence). REA unusable on this host and, by static read, has no PPC/DOL lane. Zero GEX44 jobs.**

## Evidence (with limits)
- Install: `rea-agents@6.3.0` via pnpm (global npm corrupt, `evidence/rea/npm-install-fail.log`) into `C:\Users\User\Apps\rea-6.3.0`; scripts skipped; nothing global.
- Step 2 not obtainable: `scripts/rea.mjs --help` hangs >45 s, empty output (`evidence/rea/o*.txt`, `e*.txt`, `help.*` all 0 B). Bisect: `import dist/cli.js` hangs; `import dist/identity.js` prints `ok` (`o3.txt`); plain node starts in ~1 s. Hang is in cli.js's import graph, before any target resolution. Root cause not found (time-boxed; two attempts). JDK 21 not applied (never reached the provider). Ghidra 12.1.2 acceptance unrecorded.
- Static fallback (weaker than the tool's own output): `dist/` mentions powerpc/ppc only in Mach-O fat/lipo parsing (5 hits, 2 files); no ELF e_machine handling, no DOL parser. Consistent with upstream docs (x86/x86-64 PE, MIPS ELF).

| Capability | Disposition |
|---|---|
| DOL / ELF32-PPC target resolution | REJECT now; EXTEND_UPSTREAM if wanted |
| function list / pseudocode / xrefs | NO_WORK (keep DTK + m2c + existing Ghidra); comparison not run |
| Hopper / IDA | not installed |

## Pinning
morluto/rea MIT, rea-agents 6.3.0 (HEAD 9515d2fcd398). Providers exercised: none. Update strategy: revisit only if upstream adds PPC BE/DOL lane.

## Draft upstream issue (NOT filed)
Title: PowerPC big-endian (Gekko/Broadway) lane: GameCube/Wii DOL and ELF32 EM_PPC
Body: Targets are Nintendo `.dol` (custom header, no ELF) and ELF32 PPC relocatables from decomp-toolkit splits. Ask: a named-constraint refusal today, and a Ghidra-provider lane (PowerPC:BE:32) plus DOL loader. Separate bug: on Windows 11 / Node 24.15, `rea --help` hangs silently while importing `dist/cli.js` (`dist/identity.js` imports fine).

## Receipt
REJECT; evidence `vault/programs/tennis-rf/evidence/rea/`; install dir removed (unused).

## Owner note 2026-10-11
REJECT = capability gap with a certification path (backlog D27), not REA discarded. Re-probe on the current upstream release before any patch.
