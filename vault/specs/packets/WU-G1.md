done_gate: python3 tools/test_grammar_default.py

# WU-G1 -- launch-boundary admission + packet completion in tools/gsd_mission.py

Spec (binding, read first and in full): `vault/specs/compiled-grammar-default.md`. You build laws 1-4 and 7 (G1).
Fresh worker, no parent transcript. This file is your scope, budget and done-gate. Do NOT run GSD commands, do NOT
spawn agents. Work tree: `/home/kobii/missions/grammar` (branch `grammar/default`). Pathspec commits. Never push.
Never touch `/home/kobii/.claude/skills/claude-power-pack` (the live install) or any other mission directory.

## Orientation (cheap, deterministic -- do this instead of reading the 3k-line file)
1. `python3 - <<'PY'` with `ast` to list every top-level def/class of tools/gsd_mission.py with line numbers.
2. Find the launch boundary: the function every worker start goes through (it builds the `claude --bg` command;
   callers: arm, the supervise/sweep path, turn continuation, context rotation, renewal). `git grep -n` for
   `launch_worker`, `RENEWAL_CARRIED_ENVELOPE`, `_cost_breaker`, `turn_continued`, `ALL_COMPLETE`, `def envelope`.
3. Read only the functions you will change (offset/limit). Page more only when a test fails.
4. Floors: `vault/config/route-floors.json` (read its schema; tools/route_admission.py `load_floors` already parses it
   -- reuse it, do not write a second parser).

## Build (smallest change that satisfies the spec)
- Laws 1-2: admission inside the launch boundary; `arm` gains `--unbounded` + reuses `--authority`; stored on the record.
- Law 3: window check shared by `envelope` and the launch boundary.
- Law 4: parse `done_gate:` from the packet; run it (cwd = the record's work tree, bounded timeout, output tail kept)
  before continue / rotate / renew; COMPLETED on exit 0, ledger row `packet_gate_passed`; timeout != pass.
- Law 7: `CPP_MISSION_GRAMMAR=legacy` bypass, ledgered.
- `tools/test_grammar_default.py`: V-GRAMMAR-* cases from the spec's Acceptance, each driven from both poles (a
  refused case AND an admitted control), plus two mutation checks (copy the module to a temp dir, remove the check,
  import the copy, assert the matching case goes red). Follow the style of tools/test_gsd_mission_envelope.py
  (read its first 80 lines for the harness/fixtures; reuse them).

## Budget
At most 45 model calls. Token estimate 8M; the breaker parks you at 16M; commit after each law lands (a stall of 4M
without a tree change parks you). Redirect test output to a log; read only the summary + failing lines.

## Done
1. `python3 tools/test_grammar_default.py` exits 0.
2. `python3 tools/test_gsd_mission.py > /tmp/mc.log 2>&1; tail -5 /tmp/mc.log` and the same for
   `tools/test_gsd_mission_envelope.py`: record pass lines; any NEW red is yours to fix. Existing tests that assumed
   "no envelope launches" must be updated to set an envelope or `--unbounded`, never deleted.
3. Write `vault/specs/compiled-grammar-default.RECEIPT-G1.json`:
   `{"mission_id": "...", "commits": [...], "tests": {"grammar": "<pass line>", "mc": "<pass line>", "envelope": "<pass line>"}, "changed_functions": ["..."], "boundaries": [{"n": 1, "reason": "PAGE|AMBIGUITY|PROOF_FAILURE|RECOVERY|NOVELTY", "purpose": "<=12 words"}]}`
4. Commit, end with `HANDOFF NOTE:` and one line with the three test lines. Do not wait for anything.
