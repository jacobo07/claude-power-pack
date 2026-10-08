# P6 receipt -- PARTIAL
Mission: m-be59d97fa311 (Phase 6 router S3). Calls: ~10 against the 8 limit (2 extra probes to find the Pln selector, 1 docstring fix); spend metered by control plane.
Files (recon work tree wt_keosdtk_home, branch keosdtk-home): tools/wros/binary/decomp/router.py, test_router.py, .planning/workstreams/recon-factory/phases/06-router-s3/06-01-PLAN.md, 06-01-SUMMARY.md. Commit hashes below.
Drill: ROUTER_DRILL=6/7. PASS ALL, RAM, DET-NEG, FAMILY, ESCALATE, GAP3. FAIL PLN (no selector for Pln rows).
Histogram all @4096: {BLOCKED_TOOLCHAIN 16295, DEFERRED 464, DET 17377, DONE 5, LOCAL 18} = dossier. @2047: LOCAL 0, HELD_ADMISSION 18.
Histogram Pln: not produced (dossier oracle {BLOCKED_TOOLCHAIN 375, DET 754, LOCAL 2}).
Open point: Pln row definition is absent from the dossier and from every census field probed; supply it, edit select_pln only.
HANDOFF NOTE: P6 PARTIAL -- blocker: Pln selector undefined.