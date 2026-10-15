---
covers: [cpp-evc, global-execution-optimization, pcc-wave-6-gate]
status: AWAITING_OWNER_APPROVAL
date: 2026-10-15
---

# CPP global execution optimization (EVC) — master plan

This file is the backup. The approval surface is the inline plan in chat (session 7c5ac907, 2026-10-15).

## 1. Measured reality (2026-10-15 15:50)
- P52d m-33f7242bd363 closed itself as COMPLETED via b98e7cf3. Wave 5.2 is closed:
  - commits a6866c4e, 0f7efbf0, 004d6ac2, e74fee93;
  - drills t1-t7 all KILLED;
  - VERIFICATION, DENOMINATOR and STATE written; STATE reads "awaiting re-plan"; liveness exit 0.
- Registry `GSDX_PCC_DONE=39/46` (exit 1):
  - 7 SINGLE_PLANE (Q08 Q11 Q12 Q14 Q22 Q37 Q45);
  - UNKNOWN 0. Nothing was edited toward PASS.
- Wave 6 gate: there is no WU-P6 file. The chain arms nothing (it is in wait_event).
- The worker economics of wave 5.2 were measured deterministically from the 7 transcripts (scratchpad autopsy52.py). The first table holds totals; the second breaks down the 334 tool calls.

| measure | value |
|---|---|
| model boundaries | 268 |
| tool calls | 334 |
| processed tokens | **41.33M** |
| fixed context floor per boundary (min, every unit) | 108-110K |
| floor × boundaries | 29.5M = **71 %** |
| task context (average 152K − floor) × boundaries | ~11.3M = 27 % |
| output | ~0.5M |

| tool-call class | calls |
|---|---|
| CONSTRUCTION | 90 |
| READ | 62 |
| PROOF_EXECUTION | 62 |
| FILE_DISCOVERY | 52 |
| REPEATED_READ | 26 |
| SHELL_READ | 15 |
| COMMIT | 15 |
| other | 12 |

- Coordinator pane 7c5ac907 on Opus, 14-15 Oct: **232 calls, 54.28M processed**, peak context 358K. It is **NOT booked** in any goal; the plan's coordinator cap was 3M.
- GEX44: 2.86M, from P51r (wave 5.1, not 5.2). It ran under GEX44's own account, which is outside the laptop transcripts the goal ledger reads.
- Full cost of 5.1 + 5.2 ≈ 49.5M (goal ledger) + 54.3M (coordinator) + 2.86M (GEX44) ≈ **106.7M**.
- RAM: 4.2 / 31.3 GB free; the tick holds below 4 GB.
- Branch `main` has 30 commits that `feature/knowledge-acquisition` lacks. Among them is **prr (Physical Resource Runtime)**: a pgo resource ledger, CPP-owned and MCP residency, and a reaper fix. The live tools run from the feature branch, so the live estate lacks prr.

## 2. Causal answers (summary)
- **Q1 (why 5.2 cost what it cost):**
  - the fixed 110K floor on each of 268 boundaries is 71 % (top-level-worker profile);
  - task context is 27 %;
  - deterministic orchestration through the model: P52d spent 35 of its 45 calls on suites, stamps, drills and commits;
  - rework is ~4-5M (P52c 1.82M with 0 edits; P52 breaker);
  - the coordinator (54.3M) is larger than all the workers together.
- **Q2 (irreducible boundaries):** about 90 CONSTRUCTION calls plus ~30 first reads, so ~36 % of tool calls (range 30-45 %). Boundary amplification ≈ 2.2-3.0×.
- **Q3 (what is deterministic):**
  - deterministic: phase close (suites, stamp, drills, registry, VERIFICATION and DENOMINATOR from the registry), the residual from the receipt, mission closure, and the coordinator's chain decisions;
  - still model work: construction of code and tests.
- **Q4 (reusable proof):** `modules/gsd_x/goal`:
  - certificate with element_premises;
  - inherit plan/apply/inherited_ids/verification_set;
  - combine_states over AND/OR/SEQ/QUORUM;
  - trust (authority, lineage, env2, plane);
  - judge VALIDATE.
  It is already a one-level proof DAG with element-level reuse; nesting and cross-claim CSE are missing.
- **Q5 (unattributed logs):** suites write logs through shell redirection, and the producer does not know the plane. The stamp is applied afterwards, so P52d had to RE-RUN 8 suites just to stamp them. A redirect `*>` with a BOM hid PASS lines.
- **Q6 (invisible breaker):** the session-budget gate blocks tools and the worker ends its turn. The host reports "blocked". supervise keeps the mission BLOCKED with replace + gsd NO_PHASES. gsdx_chain.decide reads non-terminal as "running". No breaker event reaches the ledger or the chain.
- **Q7 (residual.md):** the steward generates `<packet>.residual.md` as a copy of the packet; it is the residual unit's packet. The coordinator hand-edits it as if it were authority. That makes it overloaded: a generated projection used as state.
- **Q8 (main):** two-sided branch drift. Feature carries ~1005 commits; main carries 30 (prr). This is unlanded feature work, not stale debt.
- **Q9 (GEX44):** the ledger reads only local transcripts; a remote `claude -p` on another account cannot be seen.
- **Q10 (RAM):** a reaper exists (orphan node), and prr measures CPP-owned residency. Idle claude.exe processes only free RAM when recycled. The tick holds without polling the model; it is already a durable wait.

## 3. Owner map (no parallel subsystems)
- **Proof graph:** `modules/gsd_x/goal` (PRODUCTION, one level) → extend it.
- **Evidence gateway:** a new runner in gsd_x/goal on top of `trust.stamp` + env2 (PARTIAL) → creation-time provenance.
- **Provenance types:** levels already implicit: raw log → stamped → registry CLOSED → portability (2 planes). Make them explicit in trust (PARTIAL).
- **Events:** mission ledger (`lr.ledger_append`), chain log and chain_alert, PM-03 (PRODUCTION) → no new bus.
- **Obligations:** gsdx_pcc_done registry (questions) + plan tasks (PARTIAL). daif/obligation_extractor is another domain → do not reuse.
- **Resources:** prr on main (PARTIAL, not landed), chain_tick RAM hold (PRODUCTION), cognitive_os governor (SHADOW).
- **Economics:** mission_spend goal ledger, route_admission floors, gsdx_chain.forecast (PRODUCTION).
- **Worker floor:** slim-t2 profile (PRODUCTION, floor 13.5K vs 110.8K; 118 COMPLETED / 168 HALTED, cause unclassified).
- **CCR / UCVM / ContextImage:** CCR runtime installed for subagents (PRODUCTION for subagents, not for chain workers).
- **Work necessity:** not present as a module. The registry already decides "question CLOSED → no work" (PARTIAL).

## 4. Envelopes (M processed tokens)
| E | content | mode | SLB | Low | P50 | P80 | P95 | Hard | conf |
|---|---|---|---|---|---|---|---|---|---|
| 0 | reality delta (done in this turn) | EXEC | 0.3 | 0.5 | 1 | 1.5 | 2 | 2 | high |
| 1 | `tools/unit_autopsy.py` (the autopsy as a tool) + floor/boundary/proof/rework matrices | EXEC | 0.5 | 1 | 2 | 3 | 4 | 4 | high |
| 2 | proof graph: nesting + CSE in gsd_x/goal; evidence runner with creation-time provenance; explicit types; precheck | PLAN→EXEC | 3 | 5 | 8 | 11 | 15 | 15 | med |
| 3 | `phase_close` runner (suites + stamp + drills + registry + VERIFICATION/DENOMINATOR/STATE + commit), zero calls on the normal path | EXEC | 2 | 3 | 5 | 7 | 9 | 9 | med |
| 4 | breaker → HALTED + ledger event; residual compiled from receipt + registry + override file; multi-writer test | EXEC | 3 | 4 | 7 | 9 | 12 | 12 | med |
| 5 | merge origin/main → feature (prr); tick uses prr eviction of CPP-owned state before holding | PLAN→EXEC | 1.5 | 2.5 | 4 | 6 | 8 | 8 | low |
| 6 | minimal work necessity: pre-arm skip of units whose obligations are CLOSED; REUSE/DERIVE/WAIT/SKIP outcomes in the chain | EXEC | 1 | 2 | 3 | 5 | 7 | 7 | low |
| 7 | full cost: book coordinator (--measured) + GEX44 as external spend; per-class PGO in route-floors | EXEC | 0.5 | 1 | 2 | 3 | 4 | 4 | high |
| C | thin coordinator (this pane closes on approval) | — | 1 | 2 | 3 | 4 | 5 | 5 | med |
| 8 | wave 6 micro-canary on slim-t2 + phase_close | EXEC | 1 | 2 | 4 | 6 | 8 | 8 | med |
| 9 | reforecast of waves 6-11 by Work Class | EXEC | 0.5 | 1 | 1.5 | 2 | 3 | 3 | high |
| 10 | Vault / FIOS / UKDL / CBR / CI | EXEC | 1 | 2 | 3 | 4 | 6 | 6 | med |

Immediate request: E0-E7 + C, P80 = 49.5M, hard **55M**, on a new goal `cpp-evc` (keeps it separate from PCC). E8 is admitted afterwards by gate (≤8M). E9 and E10 are covered by the same goal, up to +9M, once the canary passes.
