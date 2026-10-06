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

## TOK-18 TRANCHE APPROVED (Owner 'y' 2026-10-06, pane c77978f6) - START HERE
Read ONLY `vault/plans/tok18-tranche-context-runtime-2026-10-06.md`. 6M hard cap re-authorizes post-E1 Phase 2+3.
Next: WU1 floor gate wired (fresh pane; read Pillar K plan first, hand off if K claims it). Then WU2, WU3, WU4.

## POST-E1 APPROVED (Owner 'y' 2026-10-06, wake via scheduled task INCLUDED) - superseded by the tranche above
Read ONLY `vault/plans/post-e1-meta-work-2026-10-06.md`; it supersedes every "Next" list above.
Next: Phase 0 ownership check (Mission Compiler / GSD X / Context Compiler / ledger writer / scheduled-task carrier),
then Phase 1 E1 closeout: author B1 in cep_gen2, run D1-D8 as ONE driver call with 0 model calls between steps.
One fresh pane per phase; meter with stage0/self_spend.py; pre-live model-bound hard recompile 4.5M.

## Goal-governed mission control (Owner ULTRA-PLAN 'y' 2026-10-06, pane e0a08ce5) - STOPPED AT BUDGET
Spec `vault/specs/goal-governed-mission-control.md`. LIVE: C1-C3 924bdad6 (renewal carries route; unbounded
renewal shadow/enforce via CPP_MISSION_BOUNDED_RENEWAL; epoch-0 never renews -- fired in prod 12:37:10Z on
m-8c64d4f52fc9), 9d7d980f (mission_spend measures launch-cwd plane: KME read None -> 3,353,877), C4 f71fbdd1
(goal hold + singleflight + `arm --supersedes --authority`, also on renewal). KME: Owner-ratified v3 rearm
(dac2c3bb) supersedes Gen2.1 "never rearm"; m-e935055d072d token_estimate 1.75M (trip 3.5M), hold released;
rotation = its 17:42Z budget renewal (carries estimate + note). Stopped: 23.07M processed since approval vs 15M cap.
Next (fresh pane, <=4M): C5 write-on-change sleep (launch_held / provider_held); C6 `status --surface`;
flip CPP_MISSION_BOUNDED_RENEWAL to enforce after shadow rows; deploy C1-C4 to GEX44 live install BEFORE
2026-10-07T05:00Z (m-eaf2843afb16 launches unbounded then) -- Owner call; UKDL/Vault entries.

## C5 DONE (pane ef0d3f77, 2026-10-06) -- 063ff456
Holds sleep and write only on change (`tools/mission_sleep.py`; quota/provider, gate lineage + preflight,
cwd launch hold). test_gsd_mission_sleep 6/6 + drill 3/3; MC 225/225; G23 32/32 via new `--amend` (the
documented `--capture --force` re-pin was unexecutable since T6; C2's s_budget_halt_renew red was re-pinned
with it). Pre-existing reds on clean HEAD, untouched: V-MV2-HALT-NONE-FIRST-WORKER (C3 vs an old pin),
V-ROUTE-REAL-LEDGER (historical contractId). Debt: relay_held still writes per pass. Scratch worktree gone.
Next: C6 `status --surface` (reads `sleep.wake` for HOT/WARM/COLD + Owner-only = wake.kind owner);
GEX44 deploy of C1-C5 still needs the Owner's go before 2026-10-07T05:00Z.

## GEX44 DEPLOYED (Owner 'yes' 2026-10-06; ~17:40Z)
Live install /home/kobii/.claude/skills/claude-power-pack fast-forwarded 4856b50d -> 4db97ab0 (= live head +
cherry-picks of 924bdad6, 9d7d980f, f71fbdd1, 063ff456 ONLY; branch deploy/ggmc-c1-c5 in the bare repo).
One hand resolution: test_mission_spend.py launch-cwd checks without `sessions=` (live predates attribution).
Smoke on laptop plane at 4db97ab0: 13 suites green (MC 225/225, G23 32/32, cwd-align 16/16). On GEX44: sleep 6/6,
goal-control 27/27, mspend 22/22, LG 20/20, PFP 28/28, owner-hold 12/12; 17:44:25Z agora sweep clean, 0 error rows.
Rollback: `git -C <live> reset --keep 4856b50d` (point logged in ~/.claude/state/ggmc-deploy-rollback.log).
Still true: m-eaf2843afb16 PREPARED epoch 0, token_estimate None; C2 is SHADOW, so it still launches unbounded
at 05:00Z unless the Owner bounds or holds it.

## C6 DONE (pane ef0d3f77) -- 1d25b4ae, laptop only (GEX44 still at 4db97ab0, C1-C5)
`gsd_mission.py status --surface`: HOT/WARM/COLD + owner_only + KPIs (`tools/mission_surface.py`, sleep judged
before plan). test_gsd_mission_surface 6/6 + drill 3/3; MC 225/225. Laptop estate: 7 live, HOT 2 / WARM 1 /
COLD 4 (owner_only 4: holds m-608c8d8d761f, m-a128e03c7419; blocked-on-prompt m-8bbdf725cd52, m-b65977d380b3).
SPEND: pane ef0d3f77 = 29,364,576 processed / 132 calls, 0 subagents (stage0/self_spend.py under this sid)
vs <=4M budget: OVER ~7x (~222k context per call). HR-COST-002 STOP: nothing further starts without the Owner.
Open, all Owner calls: (1) bound or hold m-eaf2843afb16 before 05:00Z; (2) deploy C6 to GEX44; (3) flip
CPP_MISSION_BOUNDED_RENEWAL to enforce; UKDL/Vault entries remain.

## m-eaf2843afb16 Cognitive Economy envelope (Owner 2026-10-06 "make it use CE at full potential")
Orca X closure workstream (/home/kobii/closure-wt, GEX44). Lineage measured (live meter == transcript scan):
839,560,807 processed; P1 109.4M, P2 114.8M, P3 280.7M, P8 310.6M, P4 discuss 24.1M; 85% subagents
(executor 33%, planner 23%, reviewer+fixer 25%, main 15%, verifier/checker/gp 4%). Remaining: P4 plan+exec, P5,
P6, P7, P9. Set via GEX44 transition (no envelope CLI there): token_estimate 135M (trip 270M -> Owner hold),
autocompact 160k, continue_max_tokens 160k; directive #3 = CE rules (review at phase tip only, one planner pass,
fresh executors, no gp agents, keep verifier + combined-tree gate). Backup .json.bak-ce-20261006.
Estimate to finish: no-CE 990M (550M-1.5B); with CE 664M central (369M-1.0B; 937M if directives ignored);
program total ~1.50B. Budget halt 2026-10-07T18:12Z; breaker likely trips ~9 h into the run.

## Post-E1 Phase 0 DONE (2026-10-06, pane e0332e3a, read-only, HEAD a5a5e91)
- Mission Compiler: no code. Only `modules/crawl_os/mission_compiler.py`, PLANNED for crawl intent (another domain). Not an owner.
- Context Compiler: ABSENT, as recorded in `vault/programs/skill-capability/ledger.json` row L (deferred to cognitive-economy).
- GSD X: `modules/gsd_x/goal/brief.py::compile_brief` is deterministic, but it builds epoch briefs from the GOAL LOG. It does
  not build planner packets from the git tree, so it does not own B3. B3 stays EXTEND `tools/source_packet.py` (build/build_context/persist).
- gen2 ledger writer: none in code. `tools/cep_gen2.py` (LEDGER_REL) only reads and checks it (not_before, obligations);
  the ledger is edited by commits. B1 adds the receipt check to cep_gen2 `check`; D1-D7 writes go in the driver, not a new owner.
- Wake carrier: no wait/wake evaluator exists (`not_before` only in cep_gen2). Zero-model daily tasks: PP-LivenessCheck 09:00
  (liveness_ledger.py --report; mixes concerns), PP-Tower-Capsules 03:45, PP-Vault-Summarize 02:00, PP-SessionTitles 04:00.
  Not PP-SelfEval: pp_eval night spends model quota, which would break the wait test. Phase 2 picks one of these (recommend
  a `wake` mode in cep_gen2 invoked by an existing zero-model task's command line); still no new task.
- Spend: this pane 2,178,039 processed / 15 calls (main thread, 0 subagents), measured with stage0/self_spend.py run under this session id.
  self_spend.py hard-codes sid 87601e81; run it under a substituted id rather than editing the sealed script.
- Next: Phase 1 (fresh pane): B1 receipt path in cep_gen2, then D1-D8 as ONE driver call.

## Post-E1 Phase 1 DONE (2026-10-06, driver vault/programs/cognitive-economy/gen2/evidence/e1_closeout/e1_closeout.py)
- B1 42a984fb: cep_gen2 fails a closed experiment without a receipt and re-derives its arithmetic (23/23 mutants).
- D1-D7 a051c761..1b93539b: gen1 state.B saving 8,477/call (upper_bound); forecast 12,515 (the 12.5k) superseded, -32.3%; plan's 10.8k/22% came from 41,353 B typo (real 37,353 B, net est 9,422); pointer tax ESTIMATED 3,093-4,038/call; payback PAID_BACK (8,784/1,083 laptop main calls, lower bound); gen2 W3 closed with receipt.
- Evidence: vault/programs/cognitive-economy/gen2/evidence/e1_closeout/README.md. Semantic (UKDL/KV/CBR candidates) not written here.
- Spend: pane 7f13d6e2 = 8,157,384 processed / 47 calls, 0 subagents (stage0/self_spend.py under this sid). Phase 1 budget
  was 0.7M central / 1.2M recompile: OVER ~7x, and over the plan's 4.5M pre-live hard recompile on its own. HR-COST-002:
  Phase 2 does not start until the Owner re-authorizes the envelope (cause: ~170k context per call x 47 calls).
- Next: Phase 2 (fresh pane, after Owner re-authorization): wake mode in cep_gen2 on a zero-model scheduled task (W1, W2).

## m-eaf2843afb16 directive delivery (pane ef0d3f77, 2026-10-06; peer report gap 2)
Handoff vault/handoffs/bug-gsd-mission-effective-workdir-2026-10-06.md. An epoch-1 fresh launch with note "" gets
NO card (session_start `epoch <= 1 and not note`; launch_worker renders a card only with note/card/capsule), so
the CE directive would never reach the 05:00Z worker. Set a factual note via transition (GEX44 seq 7); the
rendered epoch-1 card is 4,839 chars with CE directive (1)-(6) intact. Peer confirms m-ce41dd79ddd7 stays under
Owner hold (its replacement m-6f7451aefe40 uses the same worktree).
OPEN code fixes for a fresh pane (re-read HEAD; gsd_mission.py has other writers): (a) render the card at
epoch 1 when directives exist; (b) effective_workdir follows a no-workstream predecessor only into a worktree
holding .planning/ROADMAP.md (RED-first test + M6 positive control).

## ORCA P4 COMPILED-EXECUTION CANARY -- APPROVED (Owner "y" 2026-10-06) -- START HERE
Spec: vault/specs/orca-p4-compiled-execution-canary.md (1c416a50). Authority in the "y": S0 hold, S1 GEX44 deploy,
canary total cap 75M (over -> hold). S0 DONE: m-eaf2843afb16 owner_hold (GEX44 seq 9; plan_next at 05:01Z = none).
Next, each in a fresh short-lived context, no Opus parent pane, metered with stage0/self_spend.py under its sid:
1. S1: find the laptop commits behind spec mission-envelope-and-compiled-wu (c2 set_envelope CLI, c3 wu_packet in
   launch_prompt) + their test; cherry-pick onto GEX44 live 4db97ab0 in a scratch worktree, run
   test_gsd_mission_envelope + the GGMC suites there, push to the bare repo, ff the live install, smoke on GEX44.
2. S2: compile P4 from closure .planning/workstreams/closure/phases/04-continuity-closure-wave-d/04-CONTEXT.md (at
   closure HEAD 963c53977): obligations + non-work receipts + packets (follow D-08 split) + per-packet token and
   call budgets; write tools/orca_p4_canary_gate.py FIRST and see it red. Sonnet, cap 7M.
3. S4: envelope --wu-packet <packet> --token-estimate 40M, token_trip_ratio 1.5, then `release` the hold.
