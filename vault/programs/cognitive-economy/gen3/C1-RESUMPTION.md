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

Next 3 actions:
1. Zero-model: write recon-reforecast/build_c1_dossier.py on the pattern of build_p7g0_dossier.py and
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
