# RESUMPTION -- CP50 lease C1 (build bench.py + per-cohort packet + drill)

Identity. Recon worktree C:\Users\User\Apps\recon_work\wt_keosdtk_home (branch keosdtk-home). PP repo
C:\Users\User\.claude\skills\claude-power-pack (branch feature/knowledge-acquisition). Plan:
vault/plans/cp50-run-plan-2026-10-09.md (APPROVED, Owner "y" to D1-D5). Thesis: no CP50 budget until one cost per
function has been measured. C1 builds the instrument; C2 measures it.

State (2026-10-09 ~16:30):
- Sealed: GAP-1 runner A/A PASS; L1+L3 lifecycle live (PP 37a5f3c0); RF Phase 7 cap 4 (recon 0d400fd, RF_CURRENT_PHASE
  still 2); ROADMAP Phase 7 decisions D1-D5 (recon 6dbf919).
- Pending: C1. bench.py does not exist (STATE.md:83). Arm A = "decomp Phase 5 free baseline" (01-AUDIT.md:42, PLAN line
  125), and its frozen n=165 baseline exists. decomp_factory\baseline\ is empty.
- Coherence anchor: G0 draw sha 0f2ecb37..., holdout sha 7bf4c5f5... (phases/07-g0-freeze/07-01-SUMMARY.md:21-22).

Decisions in force: arms A and B only; "50" = attempted per arm; cohorts of ~10 functions, one fresh process each
(Context Rent); amendment (d) record fields; GAP-3 (bench.py builds capsules only via capsule_build/custody/repatriate);
GAP-4 (arm A is re-measured on the GEX44 plane); GAP-7/9/10/12. C1 sends NOTHING to GEX44.

Action 1 DONE 2026-10-09 (uncommitted): build_c1_dossier.py -> C1-DOSSIER.md, 63,172 chars (~15.8k tokens), exit 0,
unknown=[]; draw anchor 0f2ecb37 MATCH ($.draw.ids n=300), holdout 7bf4c5f5 MATCH (n=60). The 9 arm-A runner names that
05-04 Task 1 planned for baseline.py (build_candidates, run_slice, summarise, best_of, wilson, ...) are ABSENT on disk:
arm A has a design (05-04 Task 1, quoted in the dossier) but no runner, so bench.py's arm A must build it or reuse
transaction.attempt directly. Size that into the C1 packet.

Action 2 DONE 2026-10-09 (uncommitted): packets/C1.md + packets/route-C1.json (envelope target 0.85M | warn 0.925M |
stop 1.0M, 11 calls; worker 9 calls, packet 16k). Scope decision in the packet: the REAL arm-A executor (candidates ->
cohort capsule -> GEX44 -> records) is C2's first deliverable; bench.py refuses ARM_EXECUTOR_ABSENT for a real arm.
Goal cp50-c1 declared: cap 1,500,000, root c:\users\user\apps\recon_work\wt_keosdtk_home, lease_calls 5 (default),
since 2026-10-09T14:49:08, remaining 1,500,000.

Action 3 DONE 2026-10-09: mission m-4c2ceda008e1 ARMED (PREPARED, no launch; sweep launches it). arm --no-launch
--workstream recon-factory --max-cycles 2 --max-hours 2 --rollover-protocol capsule-v2 --add-dir <PP repo>, superseding
P2a m-f501c31d6523 (held by its cost breaker; P2a DONE, variance explained in P2a-receipt.md) -> P2a now HALTED, hold kept.
Envelope: token_estimate 500k (breaker at 2x = 1.0M = stop), model sonnet, wu_packet packets/C1.md. Admission: first
route (9 calls) RECOMPILE need 1,369,818 > 850k; cut to 6 worker calls (C2 template written by the main pane, no
SUMMARY, no spare call) -> need 913,212; envelope now target 0.92M | warn 0.96M | stop 1.0M -> ROUTE ADMISSIBLE.
C1 RUN 1 REFUSED 2026-10-09 15:16-15:17 (worker sid c021de1c, 2 calls, 215,716 processed, nothing written, mission
HALTED): goal cp50-c1 ledger used 7,684,629 > cap 1.5M. Cause = retroactive attribution: the lifecycle steward settled
4 already-finished recon-factory sessions into cp50-c1 (seq 2-4 m-6d6bb4cef637 1,412,234 | m-789229da3a6f 2,353,284 |
m-be59d97fa311 1,372,775, at declare+2 min; seq 5 P2a m-f501c31d6523 2,396,336, when the C1 arm superseded it). Goal
root now rebound to _retired_cp50-c1. Owner decision pending: new goal id (and whether to fix the steward first).
NEXT (after the Owner decides): when the receipt gen3/C1-receipt.md lands, read it, meter the worker transcript (dedupe by message.id) against
the 1.0M stop, then size C2 from the measured per-call figure; C2's first deliverable = the arm-A executor.

Next 3 actions (historical):
1. (DONE) Zero-model: write recon-reforecast/build_c1_dossier.py on the pattern of build_p7g0_dossier.py and
   build_p2a_dossier.py. It extracts verbatim (AST, with line numbers) the arm-A pipeline entry points of decomp Phase 5,
   the capsule_build/custody/repatriate APIs, the G0_FREEZE.json schema (keys only), ROADMAP Phase 7, and the
   P7G0-DOSSIER policy text. Run it -> C1-DOSSIER.md. Any piece not found is printed as UNKNOWN.
2. Write packets/C1.md plus route-C1.json in the P2a format. Lease target 1.5M; stop 1.0M (ceiling - 0.65M); calls from
   the measured 125-147k/call. Deliverables: decomp/bench.py (draw order, cohort slicing, per-function record (d),
   threshold-from-A-before-B lock), test_bench.py drill with red controls (fake 3-function draw; B unreadable before the
   A threshold is frozen), and the per-cohort packet template for C2. A goal `cp50-c1` declared via mission_spend
   goal-declare (cap 1.5M, root = recon worktree).
3. Arm with the live gsd_mission.py (arm --no-launch, envelope --wu-packet, admit --route; or arm-chain). The sweep
   launches it. Coordinator: never Set-Location into a goal root.

Start: read only this file and the plan, then action 1.
