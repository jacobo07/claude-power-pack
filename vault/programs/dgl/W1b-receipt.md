# W1b receipt
Status: DONE
COMMITS: c5f22af9 (tests RED) · 1bfb30cf (ledger.py lease epochs) · d3f397ff (mission_spend.py CLI) · receipt + W2 packet in the next commit
Red -> green: tools/test_goal_lease.py GOAL_LEASE_PASS 0/10 (before ledger) -> 7/10 (ledger) -> 10/10 (CLI). 10 gates incl. V-LEASE-CLI.
Mutation kills (tools/mutation_drill.py, isolated copy, all KILLED): drop CAS -> V-LEASE-DOUBLE-RACE; ignore reserves -> V-LEASE-ENVELOPE-EXHAUSTED (a reserves-only case was added to that gate first, the original did not see it); closed-lease cap honoured by the fold -> V-LEASE-CAP-IMMUTABLE; goal-lineage via status() -> V-LINEAGE-READONLY (+V-LEASE-CLI).
Regression exit codes, base c5f22af9~1 vs now: test_goal_budget_admission 0/0 (54/54), test_session_budget_admission 0/0 (12/12), test_tranche_driver 0/0 (27/27).
Measured spend: NOT MEASURED (packet forbids transcript and ~/.claude/state reads). About 24 tool calls; W1 measured a ~112K first-call floor and 100-215K/call, which W2 is sized on.

## What landed (ledger.py, additive; no lease row => fold byte-identical, pinned on both fixtures)
- Ops: programme, lease_open (CAS on prev_lease, idempotent by succession_id), lease_close, authority_required (one row per succession id).
- Fold: g["leases"], g["programme"], g["status"]; with a lease_open row g["cap"]/g["used"] are the CURRENT lease's, g["total_used"] is the goal-wide figure.
- API: set_programme, lease_open, lease_close, lineage (read-only), programme_status (read-only), declare_cap(lease=).
- CLI: goal-lease-open [--prev-lease --proof --closeout --recovery], goal-lineage, programme-status, goal-programme [--owner needs a real console].
## Decisions the packet left open
- No programme declared => lease_open REFUSED "UNKNOWN" (unknown headroom is not free); no authority_required row, since nothing was short.
- A lease_open without --prev-lease skips the CAS; callers that race must pass it.
- Programme rule = declare_cap rule: first value and lowering admitted, raise needs Owner (a raise in the CLI needs --owner on a TTY).
## Not done / traps
- Per-lease `used` ignores `correct` lowering (clamped at 0 per settle). Owner corrections do not give a lease its tokens back.
- A closed lease's open holds still count in the programme envelope until settled; they are not attributed to the successor's `used`.
- Fixtures were copied into a temp goal dir; the live goal-budget directory was never read.
HANDOFF NOTE: W1b done
