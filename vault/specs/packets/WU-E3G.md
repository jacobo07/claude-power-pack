done_gate: C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe tools/test_session_budget_guard.py
work_tree: C:\Users\User\Apps\pp-cost-collapse

# WU-E3G -- the session guard steers before the airbag, and closeout can always write the canonical receipt

Plan (binding, Owner "y" 2026-10-08): `vault/plans/expected-completion-E3R-plan.md`. Input: RECEIPT-E3.json.
Fresh worker, no parent transcript. No Agents, no GSD commands. Edit ONLY this worktree (never the live
`C:\Users\User\.claude\skills\claude-power-pack`; landing is E4). Pathspec commits with a message file; never push.

## Incident (measured, E3 worker b35651f5)
52 calls vs estimate 34 tripped `calls > 1.5 x estimate` with NO earlier call-level checkpoint (tokens have one, at warn).
The packet's receipt `vault/specs/*.json` was then unwritable: `CLOSEOUT_PATH` admits only vault/plans/*.md,
memory/handoffs/*.md, RESUMPTION_FILE.md. A fallback .md receipt was written instead.

## 1. Call-trajectory checkpoint (hooks/session_budget_guard.js `judge`)
Past `calls_estimate` (1.0 x) and below the deny ratio: inject the same checkpoint instruction the token warn gives
(write the progress receipt, reforecast, stop the section). Earlier when `calls - progress_at` shows no durable
progress since the last mark. Deny stays at call_ratio. Advisory fires once per tier, not every call.

## 2. Packet-declared receipt survives the stop
A packet may declare `receipt: <repo-relative path>` in its header. `gsd_mission._declare_worker_envelope`
passes it to `mission_spend.declare` as `receipt_path`; the guard's closeout allowance admits Write/Edit to exactly
that resolved path (plus the existing three). Ordinary writes stay denied. Absent receipt_path: behaviour unchanged.
Reserve: closeout_calls default stays 4 unless measured need says otherwise (record why).

## 3. Gate
Extend tools/test_session_budget_guard.py (and test_session_budget_admission.py if it owns declare): both poles per
guarantee -- checkpoint fires past estimate / not before; receipt_path write allowed after deny / another .json denied;
undeclared receipt_path keeps old regex. One mutation drill per guarantee on a COPIED module (tools/mutation_drill.py
if present), each must go red. Re-run test_gsd_mission_admission, test_running_control, test_route_admission.

## 4. Chain
Write RECEIPT-E3G.json (same shape as RECEIPT-E3.json, economics included); commit; then arm WU-E3C per the plan's
Chain section with this mission as --supersedes and --depends-on. Stop.

## Budget
At most 26 model calls (route-E3G.json). On checkpoint: go to section 4.
End with `HANDOFF NOTE:` and one line.
