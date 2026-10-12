# 03-06 SUMMARY -- PARTIAL

Status: partial. Phase 3 is NOT verified; `03-VERIFICATION.md` was not written.

## Done
- Liveness: `frontier` declared PLANNED in `vault/liveness/reachability_registry.json` (same entrance as the rest of the
  goal engine). `python modules/liveness/reachability.py` exit 0, gate offenders 0.
- Engine identity (G17): new `frontier.py` changes the engine term; now `engine:b650bc5355d1...`. engine_identity 14/14 and
  every suite that pins keys passed (`03-06-regress.log`). The before-value was not captured.
- Mutation drills: m1 (`decide_frontier` always base) KILLED by V-FRONTIER-GLOBAL-WAIT; m2 (`epoch.begin` skips independence)
  KILLED by V-FRONTIER-UNSAFE-WRITES. `03-06-drill.log`.
- Regression: 19 pre-existing goal suites, all at baseline except one (below). Replay 28/28. Mutation suite 58/58.

## Not done
- Drills m3-m8: UNRUN. The harness killed the m2/m3 command for low system memory; m3 had no verdict, m4-m8 never started.
  Not restarted (the kill note forbids restarting on my own). UNRUN is not PASS.
- `test_gsd_x_goal_pcc_semantics.py` reads 47/48: `V-PCC-ADDITIVE-ONLY` pins the legacy goal files' hashes and allows
  only `proof.py` as a new module. Phase 3 edits `epoch.py`, `reconcile.py`, `sweep.py` and adds `frontier.py`.
  The plans did not foresee it. Not touched; recorded as OWNER DECISION NEEDED in STATE.md with options and my pick.
- DENOMINATOR rows not moved: the drill and Phase 2 regression gates are not satisfied.
