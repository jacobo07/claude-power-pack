done_gate: python3 tools/test_ce_a1.py && python3 tools/test_cep_gen2_obligations.py && python3 tools/test_cep_gen2_cli.py && python3 tools/test_cep_gen2_tranche.py && python3 tools/test_cognitive_economy_program.py --generation 2 --selftest

# A1-U1 -- gen2 gate extensions for amendment A1 (G1, G2, G7, G8 receipt kind)

Authority: Owner 'y' 2026-10-07 to vault/programs/cognitive-economy/gen2/AMENDMENT-A1-2026-10-07.md (read ONLY its
sections "Phase 4 audit" and "What A1 adds"). This packet is your whole task. Budget: 8M processed tokens, at most
58 model calls (route-U1.json beside this file: ADMISSIBLE at 7.80M with margin over a measured 110,835/call floor);
the mission envelope trips the cost breaker there. Batch reads; do not reread files you have read. Never ask a
question: decide inside this scope; ending on a question is a failure. Do not run GSD commands.

Repo: this clone, branch you are on. Python: python3. Commit with `git commit -F <msgfile> -- <paths>` (pathspec only),
one commit per step below, message prefix `a1-u1:`. Do not push.

## Steps
1. `vault/programs/cognitive-economy/gen2/ledger.json` (keep every existing key; merge, never replace):
   - `budget_tokens.coordination_spend = {"value": null, "unit": "processed", "sources": [], "unknown":
     ["A1-2 meter (turns.py --attribute) not built"]}`. Do NOT touch `spent_measured`.
   - `a1 = {"cap": 20000000, "spent": null, "frozen": ["T2","T4","T5","T6","T8"], "families": {"e1-rule-moves":
     {"strikes": 0}, "ic-ao-measurement": {"strikes": 0}, "context-runtime": {"strikes": 0}, "gen3-envelopes":
     {"strikes": 0}}, "strike_limit": 2}`.
   - Append obligations C15 and C16 in the existing obligation shape, status OPEN, `check` pointing at
     `python3 tools/test_ce_a1.py --obligation C15` / `--obligation C16`.
2. `tools/cep_gen2.py` `check_receipt` (line ~205): accept `kind: "measurement"` (requires cost and a
   `decision_value` string; no per_call / payback fields) beside the existing payback kind; for every kind accept and
   validate optional `horizon_days` (positive int), `confidence` (one of low/medium/high), `retirement_criterion`
   (non-empty string). Unknown kind -> error. Keep every existing selftest green; add selftest cases for both poles
   of the new kind.
3. `tools/test_ce_a1.py` (new, V-gate style: `_ok/_fail`, prints `CE_A1_PASS=n/m`, exit 0 only if all pass):
   - `--obligation C15`: every tranche in `completion_plan.tranches` not in `a1.frozen` that has started has a receipt
     passing check_receipt; any family with `strikes >= strike_limit` must have all its tranches frozen. Exit 1
     otherwise.
   - `--obligation C16`: `a1.spent` is an int <= `a1.cap`; null/absent = UNKNOWN = exit 1 (never pass).
   - No argument: hermetic selftest on temp fixtures (tempfile; never the real ledger) driving BOTH poles of C15
     (valid receipt passes; missing receipt fails; 2 strikes with an unfrozen tranche fails) and C16 (spent under
     cap passes; over cap fails; null fails), plus one mutant: force C16 to treat null as 0 and require the
     selftest to go red, then restore.
4. Run the done_gate line above. All exit 0. On the real ledger, `--obligation C16` MUST exit 1 today (spent is
   null) -- record that output as expected-RED evidence.

## Receipt
Write `vault/programs/cognitive-economy/gen2/evidence/a1/U1-RECEIPT.md`: commits, done_gate output tail, the
expected-RED C16 line, files touched, anything left UNKNOWN. Commit it. Then stop.
