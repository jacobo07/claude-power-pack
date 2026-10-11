# WU-E2 receipt (commit 25f83975, wt_ewc)
Status: DONE
(Status line added by the coordinator 2026-10-11 after re-running test_ewc_obligations.py 56/56 and test_ewc.py 2/5 at 25f83975; the worker omitted it, so the chain read UNREADABLE.)

- M1 fields + SESSION scope: PROVEN (tools/test_ewc_obligations.py 56/56). Ledger: `<goals_root>/<repo-id>/session-<sid>/NNNNNN.json`, one atomic event per file (obligation.accepted / obligation.satisfied), modules/gsd_x/goal/session_scope.py.
- M3 classify_obligation / human_gate_ready: PROVEN (same suite, both poles + 3 near-miss phrases).
- M4 compiler: PROVEN. modules/daif/turn_obligations.py; patterns JSON: modules/autonomy_gate/obligation_patterns.json (6 patterns, compiles in Node). Incident >=5 NOW + 1 HUMAN_PREF, complete 0, human-only 1 APPROVAL.
- CLI: PROVEN. `python -m modules.autonomy_gate obligations add|close|list|compile --session <sid>`; bare verdict refused, needs '<gate>: <result>'.
- tools/test_ewc.py: 2/5 (Stop-level assertions red until E3, as expected).
- Liveness: reachability_registry.json updated; test_reachability 14/14, rc 0.
- Untracked vault/specs/salvage/ left uncommitted (not E2 scope).
