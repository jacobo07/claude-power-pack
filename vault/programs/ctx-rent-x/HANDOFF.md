# ctx-rent-x HANDOFF (2026-10-31, GEX44 epoch 7, after Owner D1/D2)

STATUS: Phase 8 institutionalisation DONE; mission NOT fully done (done_gate exits 1: CR-29 UNKNOWN, CR-30 UNKNOWN, plus UNKNOWNs listed below).
LIVE: CCR_MAIN_CANARY default-on, release 0.1.0-265d3d55, source_commit e8d29ffb; unset->enforce, =0->off; rollback to b15bfc3d verified (LAPTOP_RESULTS.md L8).
MEASURED: L5 call-1 -22.3%; L6 processed -27.8%, 6/6 correct, 0 page faults/repairs/rereads; L8 smoke call-1 -25.6% (n=1, indicative). Replay X->X' 18.3% is an ESTIMATE.
INSTITUTIONALISED: UKDL PR-NO-RUNNABLE-UNIT-STOPS-THE-EPOCH-001, PR-TEST-THAT-NEVER-LOADED-IS-NOT-GREEN-001, T-DEFAULT-FLIP-NEEDS-LIVE-PANE-RECEIPT-001, T-LAPTOP-TEMP-WORKTREE-FILES-VANISH-001 (observed once); 3 baseline_ledger rows (repo:ctx-rent-x); no Hard Rule promoted (no production recurrence).
SECTION 8 COMMANDS (GEX44): test_ctx_rent 20/20, test_ccr_release 24/24, test_floor_regression_gate 71/71, test_rollover 57/57, test_gsd_mission 234/234 rc=0. NOT green: test_gsd_mission_capsule_v2 72/73 (V-MV2-L1-WITHIN-BACKOFF-HELD-SILENT; owner tools unmodified here, pre-existing); modules/liveness/reachability.py exit 1 on standing offenders outside this mission. `claude plugin test` ran on the laptop only (28/0).
NOT DONE (need live panes, laptop-plane): Phase 4 successor smoke + fresh-start cost (CR-11,14,15,16,29), Phase 5 Safe-to-Forget (CR-09,10,13), Phase 8 dogfood comparison, CR-07 (provider-cache vs logical-rent receipt field), CR-22 (no KSR-style session).
OPEN DEBT: runner check in gsd_mission that refuses a new epoch after N "no runnable unit" epochs (IMMUNITY.md, proposal; owner tool outside this mission).
OWNER NOTE (single): to finish, run Phase 4 smoke (/clear -> /kresume, CPP_ROLLOVER_STATE_DIR empty) and Phase 5 on the laptop; GEX44 has nothing further runnable.
