done_gate: C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe tools/test_route_admission.py
work_tree: C:\Users\User\Apps\pp-cost-collapse

# WU-E4 -- land T1, T2, E1-E3C on the live branch and ratchet (expected-completion E4)

Spec (binding): `vault/specs/expected-completion-admission.md` unit E4 + Rollback. Plan:
`vault/plans/expected-completion-E3R-plan.md`. Inputs: RECEIPT-E3.json, -E3G.json, -E3C.json. Fresh worker; no Agents.

## 1. Land (local, never push)
Target: `C:\Users\User\.claude\skills\claude-power-pack`, branch feature/knowledge-acquisition. It is a SHARED tree with
other live writers: load the `concurrent-writers-shared-tree` skill first; pathspec only, never stage unrelated dirty
files, never stash. Tag a rollback point first. The live hooks/session_budget_guard.js differs from this worktree's
copy (different sha256): diff it, merge the live-only hunks with E3G's, never overwrite. Cherry-pick T1, T2, E1-E3C
(list from `git log` of cost-collapse/main since dae9ff40). Smoke: re-run the seven suites + test_dependent_admission +
test_session_budget_guard from the LIVE tree. D3 becomes ACTIVE only after that smoke is green.

## 2. Ratchet
- Knowledge Vault + UKDL (`vault/knowledge_base/ukdl-universal.md`), deduplicate first by grep: CANONICAL_RECEIPT_BLOCKED_AT_BREAKER
  (packet path vs guard regex), HARD_BREAKER_AS_STEERING (calls had no checkpoint tier), CONFIGURED_FORECAST_NOT_RUNTIME
  (EAC inert: no usage at the only call site), AUTHORITATIVE_FLIP_BEFORE_CERTIFICATION, NEXT_UNIT_INHERITS_STALE_FORECAST.
  Hard Rule candidates only where an irreversible loss is possible; the rest are Process Rules / Traps.
- CBR / presence registration for the guarantees E3G and E3C proved; liveness: `python modules/liveness/reachability.py`.
- Cognitive CI: lower-bound-only admission check (spec E4).
Canary 12: this unit runs WATCHED under the live challenger.

## 3. Close
RECEIPT-E4.json. Then the program continues per the spec: T2 reconciliation (deterministic), then T3a/T3b admitted
from the recalibrated table -- write their packets, admit with --depends-on this mission, arm the first. Stop.

## Budget
Set by route-E4.json, computed by WU-E3C from the recalibrated table. On checkpoint: write the receipt and stop.
End with `HANDOFF NOTE:` and one line.
