# RESUMPTION -- TOK-18 Gen2.1 Economic Kill-Shot (Owner decision 2026-10-05)

**Owner of the work:** Cognitive Economy generation 2 (`vault/programs/cognitive-economy/gen2/`, card `MISSION.md`,
state `ledger.json`). Add Gen2.1 there; build no new programme. The 124M U1-U11 plan is SUPERSEDED; keep it as provenance only.
Stage 0 is SEALED: `gen2/evidence/stage0/README.md` (numbers, hashes, scripts). Do not redo it.

## Owner decision (2026-10-05, binding)
- **Scope now (no live model experiments before 2026-10-11T18:00Z):**
  P0 park/renewal guard -> A0 zero-model floor attribution -> B deterministic call-elimination ceiling ->
  budget-unit reconciliation -> minimal economic readout. Then STOP and report.
- **No A1 probes now.** After the reset, run an ADAPTIVE A1 only if A0 leaves a decision-relevant ambiguity
  (repeated baseline for noise, minimal envelope, split only still-ambiguous blocks, stop when VoI ~ 0).
  Rules/instructions belong to gen2 W3/E1 (resident-rule ablation); skill/agent listings belong to the
  skill-capability gen2 owner: hand them evidence, do not re-experiment.
- **Budget, processed tokens, counted from the anchor below:** target 6-10M, warn 10M, HARD CAP 15M.
  Report both incremental spend and total campaign spend (Stage 0 = 19.2M sunk, incl. 7.84M owner-map agent).
- **Agents: default 0.** Spawn only for an independent uncertainty whose value clearly exceeds its cost.
- **Do not productise yet:** replay stays a reproducible analysis artifact (exact KSR control 273,912,110);
  the bottom-up budget rule is followed procedurally, not built. Only the rearm/park guard is built now (small, red/green test).
- **Canary naming:** InfinityOps / odr-device-trust Phase 4 (`C:\Users\User\Apps\io-device-trust`, branch
  feat/odr-device-trust, HEAD b01fb3ac, 52 dirty paths not ours). Not TUA-X. No mutation there in Gen2.1.
  Its future canary is compiled from paid semantic state (D-01..D-04, 04-RESEARCH, 04-UI-SPEC) into Work Packets,
  not planner->researcher->plans. Canary stop rule is progress-adjusted, ceiling well below the old ~70M.
- **Priority order:** P0 park guard; P1 hard/soft floor residual (A0); P2 meta-work calls that can disappear
  (planner/researcher/verifier); P3 compile Phase 4 into Work Packets OFFLINE (zero-model where possible);
  P4 compare marginal ROI of floor reduction vs meta-work elimination; P5 build only winners (later, own authorization).
- **New metrics:** Resident Prefix Tax and Meta-Work Tax (planning/research/review/verify/status/handoff share of processed).
- Never rearm KME/KSR; never unblock m-a128e03c7419, m-608c8d8d761f; never re-enable PP-ReconFactory-Rearm-20261011.

## Spend anchor
Pane 87601e81 = 19,196,694 processed at 2026-10-05T11:13:02Z (script `gen2/evidence/stage0/self_spend.py`).
A successor pane counts its own session from zero; Gen2.1 spend = successor total (+ this pane after the anchor).

## Facts to verify, not trust
- Mission m-608c8d8d761f (InfinityOps) BLOCKED, worker dfc0acda pid 24976 not running, heartbeat 2026-10-04T23:46Z.
- "A BLOCKED mission can renew itself into the old architecture" comes from an Owner-relayed scan: reproduce the path
  in `modules/gsd_x` / `tools/gsd_mission*` before writing the guard.
- Floor split 35K tools / 45K instructions / 13K agents / 12K skills / 9K hooks and role split planner 14.6M /
  researcher 8.9M / verifier 7.4M / executor 1.6M are UNVERIFIED (not on disk). A0 measures them from transcripts.
- gen2 `ledger.json` `budget_tokens` has no unit field; prose labels it processed; derivation of 40/78/150M not on disk.

## Done since the anchor (pane tua-x-96, session 242ae047 -- verify, do not redo)
- **P0 DONE, c25622e8.** Path reproduced: `plan_next` halts a BLOCKED mission on budget and `renewal_refusal` renews a
  budget halt (m-4df3ebcb89ff -> m-608c8d8d761f was exactly that). Guard = `gsd_mission.py hold|release` (owner_hold;
  plan_next none, renewal refused), spec `vault/specs/mission-owner-hold.md`, `tools/test_gsd_mission_owner_hold.py`
  12/12 + 2-mutant drill, test_gsd_mission 220/220. APPLIED to m-608c8d8d761f; on the live record at budget time
  (created+24h+60s): plan none, renewal refused; unheld control: halt, renews. Release is Owner-only.
- **A0 InfinityOps DONE, 85adcbcf** (`gen2/evidence/stage0/infinityops/`): the floor split and role split in "Facts to
  verify" are now MEASURED (main floor 129k, soft ~80k; planner 14.6M/run, researcher 8.9M, verifier 7.4M, executor
  1.6M total). Corrections: prompt_snapshot is a host record, not context; hook success text IS context (~7-13%).
  This pane's spend was not separately metered (long interactive session; count it as UNKNOWN, not zero).

## Next 3 actions
1. A0 for KSR + KME: the same zero-model floor/role split (reuse `infinityops/io_*.py`, which take a worker list).
2. B pass 1: exact-match mechanical calls; extend to pass 2 only if pass 1 lands near the 10% threshold.
3. Units fix (ledger budget_tokens unit field) + minimal economic readout with Resident Prefix Tax and Meta-Work Tax; STOP and report.

## Gen3 T1 DONE (Owner 'y' 2026-10-05; 288c5a28, 414b7dc8; evidence gen2/evidence/gen3_t1/README.md)
- Spend: T1 worker ~5.1M (Sonnet, metered) + parent orchestration; cap 8M respected. K3 not built: hook_success is not context.
- Floor after E1: n=1 session (124,464 vs same-project median 128,760); instructions attachment -28,020 chars (~9.0k tok). Median effect UNKNOWN until n>=3.
- Factorial ceilings (k4_out.txt, KSR control exact): floor -1.5..-3.7%, hook_additional_context -1.6..-2.2%, meta-work -18..-23% at c=0 (KSR break-even c~4.1M/removed run), bounded workers -22..-44%, combined N=20/S=10k -34..-56%.
- InfinityOps Phase 4 Original Obligation Set: gen3_t1/OBLIGATIONS-io-phase4.md (6 rows + D-01..D-05; extractor floor, prose obligations not captured -> review before T2).

## Next (needs Owner, not before 2026-10-11T18:00Z)
1. T2: compile Phase 4 into packets from the reviewed Obligation Set; canary measures c (inline compile cost per removed planner/researcher/checker run) -- the number that decides the meta-work lever.
2. Re-measure the E1 floor once >=3 post-12:34Z sessions exist per project (zero-model, g3_k1_floor.py).
3. Optional, small: compact advisory hook text (tower-baseline, ExecutionOS tier, woz, Graph-First); ceiling 1.6-2.2%.


## T2-0 (Gen3, 2026-10-05) - zero-model instruments A-I + D3 (worker T2ZERO-WORKER-7Q4)
State: DONE, all controls pass. Evidence: vault/programs/cognitive-economy/gen2/evidence/gen3_t2/ (README.md readout, manifest.json sha256 + controls, out_*.json, PROGRESS.md). Code: gen3_t2/t2_extract.py + t2_instruments.py + t2_c_sensitivity.py; tools/cep_gen2.py (check_obligations) + tools/test_cep_gen2_obligations.py; ledger has obligations_declared=false only. No savings realized; all numbers are measurements or ceilings.
Headlines: SDD 0.25/0.26/0.38 (KSR/InfinityOps/KME); control-loop 36-45% of processed; REPAIR 3.5-5%; join tax 0.06-0.12% of base (not a lever); lifetime grid with rehydration best N=10,S=5-10k, defensible ceiling -33..-41% (T1 (d) was -43% at its best, so T1's combined -34..-56% loses a few points; (e) not recomputed); D: meta-run output 2% overlap with its paid inputs, c lower bound 67k/121k vs break-even 4.1M/8.5M per run (SURVIVE as lower bound only, not proven); recurrence 75-77% of DELTA episodes (+13-20 pp over null); irreducible new-cognition floor 6.3/7.0/9.8% of processed.
Open for the Owner: human judgment of gen3_t2/t2_unclassified_sample_60.json (OTHER is 15-34% of calls strict); decide whether lever (c) is worth a measured compile pilot given the break-even in floor-sized calls (~34 KSR / ~66 InfinityOps).
Do not build: join-tax mitigation, copy-based packet compiler, more hook-text compaction, N=1 or S>=60k handoffs.
Next 3 actions: (1) Owner reads gen3_t2/README.md "What this changes"; (2) decide canary scope (InfinityOps Phase 4 not contradicted); (3) if (d) proceeds, test N=10,S=5-10k on a real worker with a measured handoff quality check before any realized-saving label.

## T2-0.5 APPROVED (Owner 'y' 2026-10-05) - START HERE
Read ONLY `vault/programs/cognitive-economy/gen2/evidence/gen3_t2/T2-0.5-PACKET.md`; it supersedes the "Next" lists above.
T2-0 true cost: worker 3,383,129 measured + pane a5fafaa2 orchestration ~2.5-3.5M estimated (that pane ran ~385k/call) -> ~5.9-6.9M.
State at approval: HEAD 64406cfc; holds on KSR m-a128e03c7419, InfinityOps m-608c8d8d761f, E1 m-f011d7fdebc9 (GEX44); KME HALTED.
Online breakers already exist (ccd134e6 mission_spend session scope, edcb4ad7 session_budget_guard): connect, do not rebuild.
Next 3 actions: (1) `mission_spend.py session-declare` for the orchestrating session (stop 4.5M); (2) dispatch W-a then W-b, one at a time, each with the packet only; (3) verify their controls yourself, write T2-0.5-README.md, report the T2-1 budget for the Owner's go after 2026-10-11T18:00Z.

## T2-0.5 (2026-10-05)
- Done: a (eeb1e94c), g/j (9187e329), h (31e09b81: E1 state.B IMPLEMENTED_AND_VERIFIED, --final PASS), e/b/c/d/f (readout gen3_t2/T2-0.5-README.md); i UNKNOWN (sessions after 2026-10-05T12:34Z: KSR 0, InfinityOps 0, KME 3).
- Revised combined CEILING -53..-70% (workers x packets x transaction), -56..-76% with recurrence; workers alone -39% is the defensible one; not a saving.
- T2-1 for the Owner's go after 2026-10-11T18:00Z: 4 decision points + 1 fresh review; budget 5.73M / 10.68M / 18.46M, call breaker 90, run as a supervised mission (guard cannot cap subagents).
- Spend: W-a 3,374,974; W-a2 1,718,594; final worker in README; orchestrator pane not separately metered (~0.4M/call).
- Not done: haircut variant of the transaction lever; item i; a real-session pilot of any lever.

## T2-1 APPROVED (Owner 'y' 2026-10-05) - do not start before 2026-10-11T18:00Z
Canary InfinityOps odr-device-trust Phase 4 as a SUPERVISED gsd_mission with token_estimate (central 10.68M) and the
mission token breaker; stop at 90 calls or 13.35M processed (gen3_t2/T2-0.5-README.md). One fresh worker per decision
point D-01..D-04 + one fresh-context independent review on the founder-authority seam. Before launch: resolve the missing
D-05 in gen3_t1/OBLIGATIONS-io-phase4.md, declare obligations (cep_gen2 obligations_declared=true for this canary), then
the Owner-only release of hold m-608c8d8d761f is covered by this 'y' only at launch time. KSR/KME stay held.
## Gen3 T2 DONE (Owner 'carry on' + cap 42M; evidence gen2/evidence/gen3_t2/README.md)
- 44.25M measured (2.25M over cap). Canary branch canary/odr-p4-packets in C:\Users\User\Apps\io-odr-p4-canary, HEAD 312e0db5, not pushed. Review APPROVE + 1 LOW open.
- Next (Owner): merge/deploy decision for InfinityOps Phase 4 (OWNER-GATED), the LOW fix, and whether to build an external spend breaker for agents before any further canary.
