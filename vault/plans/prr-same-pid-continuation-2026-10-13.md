# PRR continuation: same-PID working set. Reality Delta + Master Continuation Plan (2026-10-13)

Status: APPROVED WITH AMENDMENTS (Owner, 2026-10-13). Capital: +50M (OCA `prr-l3-successor-50m-2026-10-13`, programme 88M, lease L3 46M + 2M closeout + 2M recovery). Scope NOT narrowed: the "accept the re-scope" decision below was REJECTED; claude.exe same-PID reclaim is HOST_LIMITATION / CURRENTLY UNREACHABLE with a research frontier, and the programme covers A (CPP-owned), B (inputs to the host) and C (host frontier). Integration was done as a proven causal closure (16 commits), not by count. Priority order and done criteria: `vault/programs/prr/RESUMPTION_FILE.md`.
Superseded finding: the "~887 MB vs 107-160 MB" gap compared Windows commit charge with Linux anonymous RSS (evidence F).

Original status: PROPOSED. Blocked on the Owner. Goal `prr` lease L2 is spent: the guard measured 19,954,002 of 20,000,000 used, and it refused this pane's next call.

## Reality Delta (measured 2026-10-13)
- **Repo.** `prr/main` @ `e71564ad` in worktree `Apps/pp-prr`, tracks `origin/prr/main`, **not merged**. `886be474` and `e71564ad` are absent from main (`908b5430`). main is an ancestor of prr/main, which is **1,320 commits ahead**. Merging it would land ~1,300 commits from other programmes, so the merge is REJECTED. Reconcile by cherry-picking the 17 PRR commits (`7ed66817..e71564ad`) onto a fresh branch off main. Only untracked file in the worktree: `.pp-capabilities`. The shared checkout (`feature/knowledge-acquisition`) holds dirty files from another pane; do not touch them.
- **Machine (laptop).** 32,061 MB total. 304 MB free and ~1,059 MB available. Commit charge 80.5 of 101 GB. 33 claude main processes hold 29,258 MB private (~887 MB each). Other groups: js_other n=22 at 2,733 MB, mcp n=15 at 602 MB, claude_helper n=5 at 2,900 MB. 87 orphan candidates. The laptop stays read-only, because the standing rule needs at least 4 GB available.
- **Falsifier of the mission's main premise (A1/B/C, GEX44).** claude 2.1.296 runs on Bun/JSC. The Mods sandbox has no heap stats, no GC and no agent or MCP stop. CPP code does not live in the claude.exe heap. The one exception is the cpp-cognitive-runtime Mod's host-held `$.store`/`$.state`. /compact and /clear do not free RAM (+12 MB/100 turns). A completed agent stays resident at about 1 MB each. Large tool output is already spilled to disk by the host. The only bounded mechanism measured so far is compaction or /clear followed by a recycle (+0.27 MB/100 turns, history elasticity ~0).
  **Therefore:** same-PID reclamation of claude.exe is a HOST_LIMITATION today. It is not a CPP implementation task. The same-PID programme applies to CPP-owned long-lived processes (MCP servers, js_other, daemons, the Mod's state) and to what CPP feeds the host (images, agents, tool output).

## Root-cause matrix
| Root cause | Verdict |
|---|---|
| PRR_RECYCLING_PROVEN_BUT_SAME_PID_RECLAMATION_UNPROVEN | CONFIRMED (host-limited for claude.exe) |
| FRESH_FLOOR_UNDECOMPOSED | CONFIRMED on Windows (~887 MB vs 107-160 MB on Linux, a 5-8x gap that is **the top unknown**) |
| CPP_DYNAMIC_RESIDENCY_UNATTRIBUTED / UNKNOWN_RESIDENCY | CONFIRMED (js_other 2.7 GB unowned) |
| AGENT_HISTORY_RETENTION | CONFIRMED (host-owned) |
| LARGE_TOOL_OUTPUT_LONG_LIVED | REJECTED (the host spills it, C) |
| HISTORY_MEMORY_ELASTICITY_UNPROVEN | REJECTED after a boundary plus recycle (C); CONFIRMED within one PID |
| ARTIFACT_DECODE_RESIDENCY (images) | CONFIRMED: drives peak (1.2 GB HWM) |
| SAME_PID_DRIFT_UNPROVEN / DEEP_IDLE_SAME_PID_UNPROVEN | CONFIRMED for CPP-owned processes; host-limited for claude.exe |
| LISTENER / WATCHER / ASYNC retention | UNKNOWN (scope: long-lived CPP node/python processes only; hooks are per-call) |
| PEAK_OVERLAP_UNGOVERNED / AGGREGATE_GOAL_RAM_UNGOVERNED | CONFIRMED (laptop at 1 GB available) |
| RAM_FORECAST_UNCALIBRATED | PARTIAL (5 GEX44 profiles, none on Windows) |
| SHARED_STATE_DUPLICATION_UNMEASURED | UNKNOWN |

## Workstreams (mode · token P50/P80)
- W0 Reconcile: cherry-pick the 17 PRR commits onto `prr/v2` off main; run tests; re-baseline reachability. EXECUTION · 0.4M/0.7M
- W1 Windows floor decomposition: one controlled pane, VMMap-class region split (image, heap, mapped, private), with and without hooks and MCP. PLAN (needs at least 4 GB available) · 1.5M/2.5M
- W2 Census attribution: classify js_other, claude_helper and MCP by command line and owner; rank UNKNOWN by bytes. Read-only. EXECUTION · 0.6M/1M
- W3 Orphan candidates (87): only through the existing reaper authority, re-judging each one. EXECUTION · 0.3M/0.5M
- W4 Same-PID marathon for CPP-owned long-lived processes (MCP servers, the Mod's state) on GEX44: drift slope, handles, timers. EXECUTION · 1.5M/2.5M
- W5 Residency Contract and Liveness extension for CPP long-lived processes and the Mod's `$.store`. EXECUTION · 0.8M/1.2M
- W6 Input non-residency: image and agent admission (epoch length bounds peak; agents cost ~1 MB of parent RAM each); RAM-aware Agent admission in the existing economic runtime. EXECUTION · 1M/1.5M
- W7 Windows recycle act-path canary (the only bounded lever for claude.exe), demoted to fallback after W1/W4 evidence. EXECUTION (needs at least 4 GB) · 0.6M/1M
- W8 Upstream primitives (`$.session.memory`, `agent.stop`, `mcp.disconnect`, `session.recycle`): documented ask, NO_WORK locally.
- W9 Knowledge: UKDL HR/PR/traps, FIOS, CBR (Residency Contract for CPP long-lived processes). EXECUTION · 0.6M/1M
- Rejected or evidence-gated: semantic GC or object VM inside claude.exe (unreachable); shared resident services (W2 duplication evidence first); forced GC, working-set trim and V8 flags (wrong engine, no surface).

## Budgets
- Tokens: semantic lower bound 3M · P50 7.3M · P80 12M · P95 17M. Proposed successor lease: 12M plus a 2M closeout reserve.
- RAM: zero local benchmarks and zero local Agents while available is under 4 GB. At most one benchmark process at a time, on GEX44. Stop-loss: local available under 1 GB means stop launching anything.

## Owner decisions (genuine authority)
1. Successor lease for goal `prr`. Proposed 12M plus 2M reserve.
2. Accept the re-scope: same-PID for claude.exe is HOST_LIMITATION; the programme targets CPP-owned processes, inputs, and the recycle fallback.
3. Reconcile by cherry-pick onto a branch off main (recommended) rather than by merging prr/main.
