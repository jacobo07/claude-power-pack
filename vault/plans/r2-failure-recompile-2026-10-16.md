---
covers: [r2-failure-causality, chain-recompile, capital-deflation, tool-admission-premise]
status: PROPOSED (awaiting Owner approval, 2026-10-16)
parent: vault/plans/recon-factory-locality-routing-2026-10-15.md
---

# R2 failure causality, capital deflation and chain recompile (tennis-rf)

## Reality (measured 2026-10-16)
- tennis-rf: programme 150,000,000; settled 142,621,706; **executable 7,378,294**. Coordinator pane 85b7c296 settled into
  L42 (`tennis-rf:coord-85b7c296:2`): 7,056,882 since L40 (transcript 41,056,859). The coordinator, not the workers,
  is the dominant spend of the last two days (L40 21.6M + L42 7.06M vs R2 0.06M).
- PP HEAD 884e61c7 + plan commits; wt_tennis_rf ee16eab. Chain: R2 HALTED, R1/P1/R3/P2 not started, pause_budget
  (forecast 15.6M).

## R2 failure causality (transcript 350c7eb2..., sweep log, gsd-autorun-ledger, Windows event logs)
| evidence | value |
|---|---|
| Read of WU-R2.md (3.6 KB) | 95 s (11:55:50 -> 11:57:25Z) |
| `git log --oneline \| head -20` | hit the 120 s Bash timeout, moved to background |
| Glob `decomp/**/*` | "Ripgrep search timed out after 20 seconds" (155-byte error) |
| Glob `*` on vault/programs/tennis-rf (small dir) | **same 20 s timeout** |
| decomp tree size | **155 files, enumerated in 17 ms** (2026-10-16) |
| last event | API request 12:01:14Z carrying both timeout errors; no response logged |
| process end | pid 24968 gone by 12:11Z; stdout 0 B, stderr 0 B (no graceful CLI exit) |
| who stopped it | nothing: pid absent from every reaper/breaker/supervisor log; breaker not tripped (0 closeout) |
| host events 13:50-14:20 local | none (System/Application level 1-2, Resource-Exhaustion 2004); no reboot since 10-14 |
| concurrency at the time | several other sessions writing (ccr-v5 worktree, costaluz, apr, ewc chains) |

Classification: **UNKNOWN abrupt termination** (no exit code captured) **during host-wide tool starvation** (HIGH
confidence on starvation: every tool, including trivial ones, timed out). The broad Glob is **INCIDENTAL** (HIGH:
155 files; an equally timed-out `*` on a tiny dir). Not TOOL_RESULT_OVERFLOW (result was a 155 B error), not breaker,
not host crash. RAM at the time: UNMEASURED (no telemetry for that window; ram-trimmer stale since 09-14).

## Premise check
The proposed Tool Execution Compiler / fanout admission targets unbounded fanout. The measured fanout was 155 files, so
this incident gives no evidence for it. It is not built now. It is recorded as unproven, to be reopened only on a measured fanout
incident. What the evidence does support: (1) the slim runner records no exit code and no host state, so causality is
unprovable; (2) workers launch into a starved host; (3) the worker spent its first calls orienting (git log, ls, glob)
because its packet gave goals, not handles.

## Recompiled chain (failure-adjusted, P(fail) 0.2 per worker unit, recovery 0.5M)
| unit | old | new | class | P50 | P80 |
|---|---|---|---|---|---|
| R2+R1min+P1 -> **PX** (merged pilot) | 3.5+3.5+3.5 | dossier for the 9 fns only (direct handles listed), permuter admission + runs, `--l0` fix, control fixture, job 4 judge, priors/negative for the 9 | Tennis OPEX | 3.4 | 4.8 |
| P2 -> **PZ** (min) | 1.6 | reprice by class + next strategy or VERDICT; KV/UKDL entries for confirmed failures only | Tennis OPEX | 0.6 | 0.9 |
| R1 rest (judge contract doc, supersede of D8v2 12) | in R1 | deferred: not needed to judge job 4 | Tennis OPEX, deferred | 0 | 0 |
| generic router classes (beyond the 9) | in R2 | deferred until the pilot shows a class worth routing | OPEX, deferred | 0 | 0 |
| R3 (strategy exhaustion, coord guard) | 3.5 | deferred | **institutional CAPEX** | 0 | 0 |
| Tool Execution Compiler / Working Set | (brief) | not built: premise refuted | CAPEX, rejected for now | 0 | 0 |
| worker exit + host-state capture, starved-host launch refusal | - | deferred as CAPEX; procedural mitigation now: coordinator measures host (free RAM, live claude.exe, a 1-dir glob latency) before arming PX and re-arms only on a calm host | CAPEX debt | 0 | 0 |
Deflation: 15.6M -> P50 4.0 / P80 5.7 (failure-adjusted P50 4.6). Reserve 1.7M. No capital request.

## Retry diff (zero-progress rule)
Changed dimensions: (1) direct handles in the packet (exact files, the 9 fns, the 3 donors, mwcc paths on GEX44) so no
orientation search; (2) merged unit (one startup instead of three); (3) launch admission on host state; (4) early
checkpoint: dossier for the 9 committed by 1.0M or the unit stops.

## Envelopes (M tokens: floor / lower / P50 / P80 / P95 / hard)
0 Reality+causality: spent (in L42). 1-3 Tool compiler / working set / admission: 0 (not built). 4 failure gate: 0 now
(CAPEX debt). 5 deflation: 0.05 (this plan). 6+7 R2 canary+retry -> PX early checkpoint + body: 2.2 / 2.8 / 3.4 / 4.8 /
5.5 / 5.0. 8 PZ: 0.4 / 0.5 / 0.6 / 0.9 / 1.1 / 1.0. 9 R3: 0. 10 KV/UKDL inside PZ. Coordinator: <= 0.4 (arm + one
check). Total hard 6.4 of 7.38.

## Approval
Spend <= 6.4M of the existing 150M. Changes: chain.json (replace R2,R1,P1,R3,P2 with PX,PZ; R3 recorded deferred),
two new packets, no PP code. GEX44: permuter install in its own venv; CPU search 20 min/fn, -j8, max 3 parallel;
job 4 (already reassigned). Back to Owner: capital, jobs 8+, capsule rebuild, irreversible actions, PZ's verdict.
