---
id: PLAN-CEP-GEN3-REFORECAST
date: 2026-10-07
status: PROPOSED (Owner "recost stages 4 to 10", pane 0f9b771b). Nothing funded by this file.
parents: [vault/plans/cep-gen3-universal-economy-2026-10-07.md]
---

# cep-gen3 reforecast: stages 4-10

Stage text is from the Owner's source prompt (pane c77978f6, transcript line 826). Costs are FORECASTS built
from the measured inputs below; every one is a hypothesis until a receipt replaces it.

## Measured inputs (gen3, 2026-10-07)
| input | value | source |
|---|---|---|
| worker processed per call | 103k (T1c) to 138k (T1b); admission floor 110,835 | mission_spend, route admission |
| coordinator pane per call | ~153k (this pane: 10,075,093 / 66) | mission_spend.session_tokens |
| product tranche, foreign repo | T3 10.27M = worker 7.26M + pane 3.17M, 0.62x champion, delivered first try | T3-receipt |
| self-edit tranches, PP repo | T1 4.56M + T1b 7.59M + T1c 1.75M: 0 code from workers; finished by the pane (+10.08M) | T1c-receipt |
| PP-repo worker first-try success | 0/3 (live checkout refused edits; EnterWorktree failed) | T1c transcript |
| gen3 total | ~37.2M vs 31M cap (breached by ~6.2M) | plan spend table |
| closed levers (do not reopen) | reread 1.88, dead tool output 2.67, proof reuse 0.50, schema paging 0.002, dead context 0.19, fresh-epoch 2.78 (%) | gen3 plan |

Cost model: central = calls x 125k; high = calls x 140k; expected = central / p(first-try success).
Coordinator budget per tranche: hard 1.5M via `mission_spend session-declare` (the measured 3.2-18.4M coordinator
spend is the largest controllable renter, and is what broke the gen3 cap).

## Prerequisite P0: PP-repo workers can write (not a stage, blocks every stage below that edits this repo)
Diagnose why a background worker's edits to the live ~/.claude/skills checkout are refused, and give PP-repo
missions a sanctioned worktree outside ~/.claude that the arming step creates and a gate merges. 12 calls:
central 1.5M, high 1.7M, p 0.8 -> expected 1.9M. Without it, PP-repo stages cost the T1/T1b pattern: spend, no code.

## Stages
| stage | already owned by | smallest unit worth funding | central | high | p | expected | payback evidence | verdict |
|---|---|---|---|---|---|---|---|---|
| 4 Model-boundary elimination | tranche_driver.py (17/17), source_packet, gsd_mission admission | make tranche_driver the coordinator: arm, admit, read receipt, gate with zero model calls; agent-spawn admission on the same envelope | 5.0M (40 calls) | 5.6M | 0.6 | 8.3M | coordinator measured 3.2-18.4M per tranche; removing ~70% saves 2-13M per tranche, pays back in 1-2 tranches | FUND FIRST |
| 5 Proof compilation | test suites, mutation_drill, cep_gen2 gates | affected-proof closure | 4-6M | 7M | 0.6 | ~8M | proof reuse measured 0.50%: closed lever | PARK until new evidence |
| 6 Profile-guided optimization | usage_index, FIOS, model routing table | MEASURE only: repeated tool sequences + Opus share of spend from existing transcripts | 1.5M (12 calls) | 1.7M | 0.8 | 1.9M | context-profile levers closed (0.19 / 1.88%); mining and routing unmeasured | FUND measurement; build only if >5% addressable |
| 7 Institutional compilation | bug_to_hardrule, CEPS, UKDL, CBR | MEASURE only: count repeated Owner decisions / questions across sessions | 1.5M | 1.7M | 0.8 | 1.9M | unmeasured; build 6-10M later only on data | DEFER build |
| 8 Cross-domain universalization | GGMC, gsd_dossier, packets | one non-software canary (research or writing) on real queued work, compiled vs its own baseline | ~1M overhead per canary (work itself is real) | 2M | 0.7 | 1.4M each | software canary done: T3 0.62x | FUND when real non-software work is queued |
| 9 Estate enforcement | mission_spend session-declare, T1c auto-envelope (03e1b0c3), CBR | CBR entry "no mission without an envelope" with a live ledger row; per-tranche coordinator lease; retire superseded prose | 3.0M (24 calls) | 3.4M | 0.7 | 4.3M | closes the cause of the 1.18B recon lineage | FUND after P0 |
| 10 Self-hosting / deflation | stage 4 + 9 outputs | one repeat optimization tranche under the stage-4 driver, compared with gen3's ~37M | 3.0M | 3.4M | 0.7 | 4.3M | is the claim itself | AFTER 4 and 9 |

## Totals
- Fund now (P0 + 4 + 9): central 9.5M, expected 14.5M. Proposed hard cap 15M (gen4), coordinator <= 1.5M per tranche.
- Measurement only (6, 7): central 3.0M, expected 3.8M.
- Conditional (5, 7 build, 8 per canary, 10): ~16-20M central, only if the measurements or Owner work justify it.
- All of 4-10 built: ~35-40M central, ~50-55M expected. Not recommended as one approval.

## Order
P0 -> 4 -> 9 -> (6, 7 measurements) -> 10 -> 8 per real workload. 5 stays parked.
Each tranche: packet + route admission + receipt + `cep_gen2 --tranche` gate; next tranche only on a passed gate.
