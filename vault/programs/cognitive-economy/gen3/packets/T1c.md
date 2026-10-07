# cep-gen3 T1c -- fixed auto-budget rule (EXECUTION, small)

Supersedes T1b (m-3e4f27d678a1: 7,594k processed, 0 code; session guard at 55 calls). Owner 2026-10-07 pane 0f9b771b
picked "retire + option (b)": ONE fixed rule, no calibration, no route math. Do not read transcripts. Envelope 1.5M
(breaker trips at 3M); plan <= 11 tool calls (admission floor 110,835/call). Do not explore: the anchors below are verified at HEAD 8224e6a6.

Repo C:\Users\User\.claude\skills\claude-power-pack (live copy, shared with other panes). Commit only your paths
(`git commit -F <msgfile> -- <paths>`), verify `git log -1 --format=%s`, never push/reset/stash/checkout.
git = & 'C:\Program Files\Git\cmd\git.exe'; python = & 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'.

## The rule (tools/gsd_mission.py)
New `_auto_budget(rec, now, measure=None) -> dict`, called in `supervise()` right BEFORE the `_cost_breaker` line
(~2508): `if not dry_run and rec.get("token_estimate") is None and not rec.get("owner_hold"): rec = _auto_budget(rec, now)`.
- spent = `(measure or mission_spend.processed_tokens)(rec)`; an exception -> spent None (never 0).
- H = `headroom_tokens` from new vault/config/mission-budget-defaults.json (`{"headroom_tokens": 15000000}`; file
  missing/unreadable -> 15,000,000, say so in basis).
- ratio = `rec.get("token_trip_ratio")` or the default the breaker uses (read it from mission_spend.judge; do not guess).
- estimate = ceil(((spent or 0) + H) / ratio). Basis string names spent (or "spend unmeasured"), H, ratio.
- Write with ONE `transition(..., event="envelope_auto_assigned", token_estimate=est, token_estimate_src="auto",
  token_estimate_basis=basis, reason=basis)`. Any exception -> ledger row `envelope_auto_unassigned`, return rec.
- Never touches a record whose token_estimate is set, a held record, or a terminal one (supervise already filters).

## Tests (tools/test_gsd_mission_envelope.py, same style as the file)
1. spent=4,000,000, H=15M, ratio 2 -> estimate 9,500,000, src "auto", ledger row present.
2. measure raises -> estimate = ceil(H/ratio), basis contains "unmeasured".
3. operator estimate 1,500,000 already set -> unchanged after a supervise pass.
4. owner_hold set -> unchanged.
Run that suite; record the exit code and counts.

## Receipt
vault/programs/cognitive-economy/gen3/T1c-receipt.md (<= 20 lines): commit hash, test counts, exit code, this
mission's measured spend. Add a spend row to vault/plans/cep-gen3-universal-economy-2026-10-07.md. Do NOT release T2,
do NOT arm anything. End the turn with `HANDOFF NOTE: T1c done` (or the blocker).
