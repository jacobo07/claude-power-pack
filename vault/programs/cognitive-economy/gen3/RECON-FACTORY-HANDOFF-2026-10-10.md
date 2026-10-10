# HANDOFF -- Reconstruction Factory (canonical) + GSD X Reconstruction Factory (optimized), 2026-10-10

Every number has its source next to it. M = measured (ledger or transcript, deduplicated by message.id).
D = derived here by arithmetic on M figures. U = unknown.

## 0. The two systems, and how they relate

| | Canonical: recon-factory | Optimized: GSD X Reconstruction Factory (gsdx-factory) |
|---|---|---|
| What | the GSD workstream that does the work (compile, judge, promote) | the programme meant to fund and run recon-factory through P9 cheaper, without a coordinator pane |
| Tree | `C:\Users\User\Apps\recon_work\wt_keosdtk_home`, branch keosdtk-home (569+ dirty paths: never touch) | `C:\Users\User\Apps\pp-gsdx-factory-2`, branch gsdx-factory/v2 (local only) |
| Plan | `.planning/workstreams/recon-factory/ROADMAP.md` (10 phases) | `vault/plans/gsdx-factory-master-plan.md` @ 68d21301 (W0-W8) |
| Ledger | PP `vault/programs/cognitive-economy/gen3/` (receipts, TRANCHE-CP50.md) | `vault/specs/gsdx-factory.RECEIPT-*.json`, `~/.claude/state/gsdx-chain.jsonl` |
| Goals | rf-p3b, rf-p3b2, cp50-c1, cp50-c1b (+ unbound gen3 leases) | gsdx-factory (closed), gsdx-factory-2 |
| Driver | coordinator pane + gsd_mission workers (one lease each) | `tools/gsdx_chain.py tick` (Task PP-GsdxChain-Tick, 15 min) |

Key relation: gsdx's Part B (W7) was meant to run recon P2 -> P3 -> CP50 -> P8 -> P9. On 2026-10-09 17:35 its
coordinator DEFERRED every REC-* unit to the Owner's CP50/gen3 track ("gsdx does not put a second writer in
wt_keosdtk_home", chain.json `deferred.note`). Since then **every recon phase was done by the canonical track. The
optimized factory has executed no recon phase.** Its REC-P2C and REC-P3 units are now obsolete: P2 and P3 are done.

## 1. Canonical recon-factory: progress

ROADMAP (recon `ROADMAP.md:39-48`), plus what landed after it was last ticked:

| Phase | State | Evidence |
|---|---|---|
| 1 Plan audit + GEX44 lane | DONE | 01-VERIFICATION 4/4 (2026-10-03) |
| 01.1 Fork port (GAP-3) | DONE with deferred gaps | 36 files sha-pinned; test_capsule/test_propagate/test_return_path NOT-RUN |
| 2 Oracle parity | DONE | fa66cbc; 350/350 MEASURED + 51/51 INFERRED, ORACLE_PARITY_DRILL 14/14, GEX44 AA_GATE PASS (ksrmb-20261009-090602) |
| 3 Capital promotion | **DONE in fact, NOT ticked** | 3a: SEAM_DRILL 8/8 (dcd9178). 3b-1: P3B_DRILL 10/10 (4e7d8e7). 3b-2: see section 2 |
| 4 Work-unit log + tx/2 | DONE | WORKUNIT 37/37, TX2 18/18 |
| 5 Closure census | DONE | 0bb9786, CENSUS_DRILL 4/4 (Jsk/Png positive controls NOT-RUN) |
| 6 Router | DONE | 9697c9e, ROUTER_DRILL 7/7 |
| 7 G0 + CP50 | G0 DONE; CP50 C1 built, **not committed** | G0 e3b0b82 (draw 300, holdout 60 sealed); C1 BENCH_DRILL 8/8 |
| 8 CP150/300 | NOT STARTED | only if CP50 meets the preregistered criterion |
| 9 Seal | NOT STARTED | |

Count: 6 of 10 ticked (1, 01.1, 2, 4, 5, 6). Phase 3 is complete pending two tests and the tick, which makes 7 of 10.
Phase 7 is about half done (G0 yes, CP50 measurement no).

## 2. Phase 3b-2: what happened (this pane, 2026-10-09/10)

1. Goals: rf-p3b2 is bound to wt_keosdtk_home; rf-p3b points to _retired_rf-p3b.
2. Control drift: `SB.impact(load_store())` gave control_proven=5, each with drift=["match_py"]. match.py changed in recon
   ac1f1ae (2026-10-04) after the 5 rows were sealed. The drill's IMPACT gate does not catch this (it only asserts
   `src_registry` is absent). Owner "a" = accept; the bundle path re-judges the 5.
3. Pre-checks: PINS=OK tools=7; SLOT_LEDGER PASS, lease=none; GEX44 idle (queue 0, boots 0/6).
4. RF_CURRENT_PHASE 2 -> 3: recon a5d57a0.
5. Sent job 1 of 2: ksrmb-20261009-214006. WAIT=COLLECTED; REPATRIATE=OK, tree 6f7b2c9d.
   - Receipt PASS, 294 units, custody ok, runner_lib 7377ff0f, task_sha 5bd8add8 (matches the build), ended_at 21:44:51Z.
6. register_src: added=289, kept=5, refused={}. assemble: bundles=294, refused=0. 294 bundles written to
   `C:\Users\User\Apps\recon_work\decomp_factory\levels\evidence\src_bundles`.
7. The first promote was refused HOST_FLOOR_BREACHED (free 1221/1314/619 MB < 1500). It passed later at 2528 MB free:
   - promoted 294, ledger rows 34,159, ledger_sha256 0c247d0d...;
   - SRC PROVEN 5 -> 294 (+289), PROMOTED_NOT_PROVEN=0, SEALED_LOST=[], PROVEN_VIA_BUNDLE=294/294,
     POST_IMPACT_DRIFTING=0, P3B2_CHECK=PASS.
   - Scripts: `gen3/recon-reforecast/p3b2_finish.py`; log `gen3/P3b2-steps6-8.log`.
8. Commits: PP bdbe4f35, 00493bcb, 33516abe; recon a5d57a0.
9. RF Phase 3 jobs: 1 of 2 used. One is left; it is a reserve and is not owed to anything.

## 3. Canonical recon-factory: token spend

Gen3 era (2026-10-08 onward), deduplicated:

| Line | Processed | Source |
|---|---:|---|
| Tranche workers P5, P5b, P6, P7G0, P3a, P2a | 9,881,933 | M, TRANCHE-CP50.md:43-49 |
| R1 reforecast worker | 553,590 | M, R1-receipt.md:3 |
| Main pane ce1c3a41 before "fund it" (P2a close, meter, D11) | 10,812,318 | M, TRANCHE-CP50.md:65 |
| Main pane P2b (3 GEX44 jobs, OUT fix, AA gate), 98 calls | 27,600,379 | M, TRANCHE-CP50.md:63 |
| P3b-1 worker (m-1a112049e9c8) | ~1,790,000 | M, approximate, P3B-RESUMPTION.md:67 |
| rf-p3b coordinator misattribution (one Set-Location, 8 calls) | 1,316,151 | M, memory dgl-durable-goal-lease |
| C1 run 1, refused (worker c021de1c, settled into rf-p3b) | 215,716 | M, C1-RESUMPTION.md:37 |
| C1b worker (ee4121e6), bench.py | 731,961 | M, cp50-c1b journal seq 8 |
| P3b-2 (this pane), ledger `used` | 1,488,019 | M, includes an open lease of 751,885 |
| **Gen3-era total** | **~54.39M** | D, sum of the rows above |

Goal ledgers, read 2026-10-10 with `mission_spend.py goal-status`:

| Goal | cap | used | settled | open | Note |
|---|---:|---:|---:|---:|---|
| rf-p3b (retired root) | 2,400,000 | 3,318,702 | 3,148,832 | 169,870 | over cap by 918,702 because of the misattribution |
| rf-p3b2 | 2,400,000 | 1,488,019 | 736,134 | 751,885 | this pane |
| cp50-c1 (retired root) | 1,500,000 | 7,684,629 | 7,534,629 | 150,000 | **double count**: settled = P5+P3a+P6+P2a, already in the tranche row; real C1 spend here = 0 |
| cp50-c1b | 1,500,000 | 1,347,690 | 731,961 | 615,729 | the open amount is a lease marked `leak` (seq 10); real spend = 731,961 |

Do not add the goal rows to the table above: cp50-c1 duplicates the tranche row, and the leaked leases are phantoms.

Before gen3: STATE.md:44 records the lineage at "~1,180M processed / 4,274 calls" (cep-gen3 card), and Phase 4
04-01 + 04-02 at 33.2M. That is phases 1, 01.1 and 4, under the pre-economy regime. It is not comparable with the
figures above.

## 4. Optimized gsdx-factory: progress

Master plan W0-W8 (plan section 2) against its receipts:

| Unit | State | Evidence |
|---|---|---|
| W0 S1 closeout | DONE | RECEIPT-S1; commits 55ced1e8, 006c8b7b, 2a3c3bd0; STEWARD 18/18, GOAL 45/45, ADM 44/44; both drills KILLED |
| (S4 slim-t2 probe) | DONE | RECEIPT-S4: guard denied the Write at stop 5,000; whole unit 73,648 |
| W1 wait for lc3 INST2 | MET | L3 installed live PP 37a5f3c0 (TRANCHE-CP50.md:29) |
| W2 L1 (graph + dispositions) | DONE (DONE_WITH_LIMITS) | RECEIPT-L1; "GRAPH costs are not a forecast (n = rows/6)" |
| PLAN-1 planner epoch | DONE | RECEIPT-PLAN |
| DOCTRINE | DONE (DONE_WITH_LIMITS) | RECEIPT-DOCTRINE; test_wu_doctrine.py rc 0 (41 rows) |
| **W3 S2/S3 residual** | **PARTIAL, STALLED** | see below |
| W4 reforecast | NOT STARTED | after W3 |
| W5 GEX44 control-plane port | NOT STARTED | DEPLOY class; GEX44 has no admission/dossier/steward/guard |
| W6 Part A (A-G2..A-G5) | NOT STARTED | |
| W7 Part B (recon P2..P9 on GEX44) | DEFERRED to the gen3/CP50 track | chain.json `deferred`; P2 and P3 already done there |
| W8 closeout | NOT STARTED | |

W3 receipt (`RECEIPT-W3.json`): status PARTIAL; test_wu_w3.py 9/9.
- Delivered: the `calls_unit` field; a model-call counter by message.id in session_budget_guard.js and
  mission_spend.session_tokens; the breaker denies on the declared unit.
- Remaining: per-class g/r and the closeout tail; R4 reconciliation and phantom-reservation prevention; successor arming
  within the envelope; the S1 replay priced at 2.1M or more; the `--calls-unit` CLI end to end.
- **The chain is stuck.** Every 15 min since the receipt, `gsdx-chain.jsonl` logs `stopped_without_done W3 PARTIAL
  "steward / residual owns it; never re-armed by the chain"`. No residual packet exists. The programme rule
  (RESUMPTION_FILE.md:33) says this row needs a residual packet compiled and added to chain.json. Nothing does that
  automatically, so gsdx makes no progress until someone does.

## 5. Optimized gsdx-factory: token spend

| Line | Processed | Source |
|---|---:|---|
| Old goal gsdx-factory (closed): used | 13,870,691 | M, goal-status. Of this: A-G1 3,276,310; coordinator 530d9700 ~10.36M misattributed via Set-Location; 232,321 open hold (liveness UNKNOWN) |
| gsdx-factory-2: used = settled, open 0 | 6,851,452 | M, goal-status |
| **Total** | **20,722,143** | D |
| **Productive (excluding the ~10.36M misattribution)** | **~10.36M** | D |

Envelope: 40M safety, 55M hard; expected verified completion 26.6M (plan section 3). gsdx-factory-2 has spent 6.85M =
17.1% of the envelope (D), and it covered the S-block plus L1, PLAN-1 and DOCTRINE. The plan's W0-W3 lines (S1 0.5, S2
0.3, S3 0.4, L1 2.0 expected, = 3.2M) compare with 6.85M spent before W3 finished (D). That is about 2.1x the expected
cost, so the remaining forecast is not trustworthy until W4 reforecasts it.

## 6. Comparing the two (for the Owner's decision)

- The canonical track delivered phases 2 and 3 for ~47.8M (D). That is P2a worker 2.40M + main pane 10.81M (P2a close,
  meter, D11) + P2b 27.60M + P3a 2.35M + P3b-1 1.79M + the misattribution 1.32M + P3b-2 1.49M. It was driven mostly by
  a main pane: P2b alone is 58% of it.
- The optimized programme has spent 6.85M on its own control plane (steward, counters, doctrine, graph), and 0 on recon
  phases. Its thesis (a chain with no coordinator is cheaper) is untested on factory work. The one measurement is the
  2.1x overrun of its own W0-W3.
- Both tracks keep their spend in separate goals, so neither ledger shows the whole picture. This file does.

## 7. Open debt (exact)

1. **C1 bench.py is not committed.** In wt_cp50_c1 (branch cp50-c1, tip 4e7d8e7), `bench.py` and `test_bench.py` are
   staged (`A`) but not committed, although C1-receipt.md says COMPLETE. The merge into keosdtk-home cannot happen until
   they are committed. Pathspec only.
2. **ROADMAP Phase 3 is not ticked, and STATE.md is stale** (it still says "current_phase: 2"; ROADMAP:42 unticked).
   Tick it only after item 3.
3. **test_levels.py and test_levels_revalidate.py have not been run** (P3B-RESUMPTION.md:13). They need compiles. They
   are the Phase 3 done-gate.
4. **dgl W7 duplicates P3b-2** (`Apps\pp-dgl\vault\programs\dgl\chain.json:36-40`). Rewrite it as verify-only or remove
   it before `D2-owner.md` exists, or it will re-send and spend the last RF Phase 3 job.
5. **The gsdx W3 residual packet is missing**, so the chain logs the same stop forever (section 4).
6. **gsdx REC-P2C and REC-P3 are obsolete** (P2 and P3 are done). Retire them in chain.json `deferred`.
7. **The IMPACT drill gate is too weak.** test_p3b.py:176-177 should assert `drift == []` on the control, not only that
   `src_registry` is absent.
8. **Phantom holds to settle:** rf-p3b 169,870; cp50-c1 150,000; cp50-c1b 615,729 (leak); gsdx-factory 232,321;
   rf-p3b2 751,885 (this pane's live lease; it settles when the session ends).
9. **CP50 C2 is the next real work.** First deliverable: the arm-A executor (candidates -> cohort capsule -> GEX44 ->
   repatriate -> records). It is absent; bench.py refuses ARM_EXECUTOR_ABSENT (C1-receipt.md:24). C2 needs RF Phase 7
   jobs (cap 4, recon 0d400fd) and RF_CURRENT_PHASE 7 at its first send.

## 8. Next 3 actions

1. Commit bench.py and test_bench.py in wt_cp50_c1 (pathspec, `git -C`), then merge cp50-c1 into keosdtk-home (bench
   files only).
2. Make dgl W7 verify-only (it is another pane's chain: tell its owner, or have the Owner approve the edit), and write
   the gsdx W3 residual packet, or have the Owner retire W3.
3. Run test_levels.py and test_levels_revalidate.py, then tick ROADMAP Phase 3 and refresh STATE.md. Then size C2 from
   the measured C1 figure (731,961 over 6 calls, about 122k per call).

Start: read this file, then P3B-RESUMPTION.md and C1-RESUMPTION.md. Never Set-Location into a goal root.
