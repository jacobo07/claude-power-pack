---
covers: [prr, physical-resource-runtime, prws, memory-census, session-hibernation, physical-epoch-recycling]
status: APPROVED
date: 2026-10-12
author_session: ce64704d
---
# PRR: Physical Runtime Working Set (Master Plan, first response)

Backup of the inline plan given in chat. The chat message is the approval surface.

## Owner decision (2026-10-12, pane ce64704d): "1 prr, 2 yes, 3 GEX44"
1. New goal `prr`, cap 18,000,000, root `C:\Users\User\Apps\pp-prr` (branch `prr/main` off 983cca18). Linked to
   `ccr` (owner pane c13cda65) by reference only; no writes to CCR-owned files.
2. Process-destructive actions (hibernate, recycle, orphan reap with identity proof) are authorized for
   **canaries on panes/processes this programme starts**, until the two-shape canary passes. Fleet-wide action
   on the Owner's existing panes is NOT covered and needs a fresh Owner word.
3. Laptop sessions are left untouched (no trimmer). Laptop work is read-only Windows census only (no new
   claude.exe). Canaries, long-run benchmarks, engine identification and recycling drills run on **GEX44**
   (64 GB, 57 GB available, Claude Code 2.1.296 native ELF, measured 14:41).
   Plane rule: every number names the plane that produced it. A GEX44 (Linux) result is not a Windows result;
   Windows transfer stays UNPROVEN until one laptop canary runs at >= 4 GB Available.

## Phase order
A0 laptop read-only census instrument (Windows truth, no spawn) -> A1 GEX44 engine identification + Mods capability
probe -> B hard floor + long-run fixture on GEX44 -> E contract -> O recycling canary on GEX44 -> laptop transfer canary.

## Reality Delta (measured 2026-10-12 ~14:22, host laptop, Claude Code 2.1.296 native `~/.local/bin/claude.exe`)
- Host: 32,061 MB RAM, **1,096 MB free**, commit 73.7 / 93.1 GB. The host is starved right now.
- 38 `claude.exe`: private 28.2 GB, working set 9.4 GB (about two thirds of private bytes are paged out or standby).
- 33 main processes (>300 MB private): mean 854 MB private. Cross-section age vs private bytes: Pearson r = 0.18,
  slope 1.26 MB/h. Across the fleet, age barely predicts RAM. Sealed June evidence: one session grew 5.9 to 25 GB, driven by context.
- Process model: a main `claude.exe` plus child `claude.exe` helpers of ~125-150 MB private (parent = claude.exe,
  python.exe or cmd.exe). Not yet classified: bg/subagent/headless.
- node.exe: 104 total, 78 with a dead parent; 62 are `.planning/config.json` one-liner probes (~4 MB private,
  0 working set each). Orphan count is real; orphan RAM is about 0.3 GB of commit.
- Mods surface in use: fs, env, plugin.root, session.{id,repo,version,messages,compact}, ui.status, tool.register.
  Sealed limits: `$.session.compact()` refused headless; a mixed handle/rebuilt kept-set is a silent no-op.
  No heap, process or MCP lifecycle surface has been observed in use.
- Existing owners: `modules/cognitive_os/process_governor.py` + `hibernate_runner.py` (FASE A: store, then flag, then kill;
  the kclaude wrapper parks and resumes), `tools/ram_guard.py` + `hooks/ram-guard-stop.js`, `tools/ram_trimmer.ps1`,
  `modules/zero-crash/hooks/ram-watchdog.js`, `tools/lazarus_orphan_purge.py` (disk only). CCR goal `ccr` is owned by
  **live pane c13cda65** (transcript written 14:24).
- Unverified premise: whether claude.exe 2.1.296 is a V8 (Node SEA) or JSC (Bun) runtime. Phase A decides.

## Workstreams, owner, mode
| ID | Workstream | Owner map | Mode |
|---|---|---|---|
| A | Runtime + Mods capability matrix | IMPLEMENT (probe mod, read-only) | EXECUTION |
| B | Memory Census (per-tree private/WS/commit, children, MCP, agents) | EXTEND ram_guard.py | EXECUTION |
| C/D | PRWS + hard resident floor, live vs allocated | IMPLEMENT (measurement) | PLAN |
| E | Logical session vs physical epoch vs PID | EXTEND kclaude park/resume + Lazarus + ContextImage | ULTRA-PLAN (only open contract) |
| F/G | Memory Liveness + Admission Firewall | EXTEND process_governor + Agent necessity | PLAN |
| H | Agent Memory Governor | CONNECT (measure helper claude.exe) | EXECUTION |
| I | MCP lifecycle | HOST_LIMITATION likely; measure, govern via config | EXECUTION |
| J | Process Liveness / Orphan Reaper (node probes) | EXTEND ram_trimmer identity checks | EXECUTION |
| K | Cache/artifact lifecycle | ALREADY_DONE for pixels (CCR M2); NO_WORK for text (M3) | NO_WORK |
| L | Memory Pressure Controller | MERGE ram_guard + ram-watchdog (two owners today) | PLAN |
| M | Hibernation | EXTEND FASE A (exists, not hot path) | PLAN |
| N | UTVM continuity | CONNECT (transcript is the backing store already) | EXECUTION |
| O | Physical epoch recycling | EXTEND hibernate_runner + `--resume <sid>` (not `--continue`) | PLAN |
| P/Q | Long-run benchmark + elasticity CI | IMPLEMENT (synthetic `-p` fixture, no model spend where possible) | EXECUTION |
| R | Resource PGO | IMPLEMENT (append-only profile ledger) | EXECUTION |
| S/T | Self-host + 2-shape global canary | CONNECT | EXECUTION |
| U | Knowledge/UKDL/CBR | EXTEND | EXECUTION |

## Root-cause matrix (first pass)
SESSION_AGE_RAM_GROWTH PARTIAL (fleet r=0.18; within-session growth is context-driven) · TRANSCRIPT_MEMORY_GROWTH PARTIAL
(June 5.9 to 25 GB) · V8_HEAP_RETENTION UNKNOWN (runtime unverified) · NATIVE_EXTERNAL_MEMORY UNKNOWN · AGENT_RAM PARTIAL
(helpers about 130 MB each) · MCP_RAM PARTIAL (notion via bunx, small) · TOOL_RESULT_RAM UNKNOWN · MULTIMODAL_RAM UNKNOWN (token
share 9-17 %, bytes unmeasured) · PLUGIN_RAM UNKNOWN · CACHE_RAM UNKNOWN · ORPHAN_PROCESS_RAM PARTIAL (78 dead-parent node,
about 0.3 GB) · HARD_RESIDENT_FLOOR PARTIAL (helper ~125 MB; fresh main process not yet measured).
Dominant estate cause measured: **population** (33 live main sessions x ~0.85 GB), not age.

## Budget
Tokens: lower bound 1.5M · P50 6M · P80 9M · P95 14M · hard authority 18M (confidence medium; floor 100-215K/call).
Split (P50): A 0.5M, B 0.6M, C/D 0.6M, E 0.8M, F/G 0.6M, H/I/J 0.6M, L/M 0.6M, O 0.8M, P/Q 0.5M, R 0.2M,
S/T 0.4M, U 0.3M, recovery reserve 0.8M (meta-optimization tax included in each).
Physical: start canaries only at >= 4 GB Available (AvailableMBytes counter); at most 2 extra claude.exe at once;
Blender/Ghidra/GEX44 excluded; 3 GB safety reserve; abort a canary below 2 GB Available.
