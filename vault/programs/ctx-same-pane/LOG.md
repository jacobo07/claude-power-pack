# ctx-same-pane LOG (confirmed facts, append-only)

## Phase 1 / Plan 01 (S0 ctx-rent S2 repair), 2026-10-10
- S0 patch: `git apply --check -v vault/programs/ctx-same-pane/S0-ctx-rent-s2-halfedit.patch` rc=0 (evidence s0/apply-check.txt), `git apply` rc=0: APPLIED, not hand-ported. Touched tools/rollover.py (_economics accepts PROTOCOL prefix) and tools/rollover_replay.py.
- The patch was a half edit: `certs.add(...)` / `return ... certs` used an undefined name. H1 finished in `_tool_message_ids`: (a) tool_result `elif _is_certified_result(...)` adds to `certified`; (b) `cert_uses[b.get("id")] = msg.get("id")`; (c) `certs = {mid for tid, mid in cert_uses.items() if tid in certified}`.
- Predicate (grounded in rollover.py prints at lines 1329/1362/1364): counted only when the non-error result text has `RESUME_CERTIFIED -- ` or `RESUME_CERTIFIED (already) -- authority restored` and lacks `NOT restored`. The bare token is never the decision.
- fresh-cost CLI prints calls_to_certify, protocol_overhead, no_certify_call. replay() untouched. No gate constant (MIN_GROWTH_TOKENS, ADVISORY_PCT) touched.
- Existing replay suite after the edit: ROLLOVER_REPLAY_PASS=33/33 (s0/suite-tracer-replay.txt).
- Real ledger run (read only; `prior --write` NOT run, nothing written under ~/.claude): `rollover_replay.py fresh-cost --json` -> s0/fresh-cost-real.json. certified 301, samples 300, missing_transcript ['drill-successor-A'], torn_rows 6, no_mutation 6.
  - protocol_overhead n=298: p10 353,401 p50 387,598 p90 593,098. calls_to_certify n=298: p10 3 p50 3 p90 5.
  - carried_before_first_mutation (old UPPER_BOUND basis) n=294: p10 784,323 p50 1,801,735 p90 4,172,439.
  - no_certify_call = 2. Secret grep (sk-, ghp_, BEGIN) on the JSON: 0 hits.
- Env note: coreutils `timeout` in the Git Bash tool scrubbed HOME/USERPROFILE and made rollover.py fail at import (Path.home); run python directly (no `timeout` wrapper).
- Commit A 018230b9 (tools/rollover.py, rollover_replay.py, test_rollover_replay.py, test_rollover_decide_evidence.py), committed from the PP main pane per the budget-stop receipt.
- Suites re-run at commit: test_rollover_replay 41/41, test_rollover_decide_evidence 13/13, test_rollover 57/57 (worker's final run also: active_path 46/46, economic 19/19, horizon_wiring 11/11).
- Drills, all MUTANT KILLED: V-RR-CERTIFY-DETECT[refused], V-RR-PROTOCOL-NOT-WORK, V-RR-NO-CERTIFY-NOT-ZERO, V-ROLLOVER-PROTOCOL-BASIS (s0/drill-*.txt).
- Budget: goal ctx-same-pane hit its 16M hard stop during S0 (worker 5.6M + subagents 11.7M: gsd-executor 7.2M, gsd-planner 4.3M). Mission on owner hold. Re-arm = S1 + S4 only, no GSD plan-phase (Owner option 1, 2026-10-10).
