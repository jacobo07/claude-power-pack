# A1-U1 receipt

Commits (all pathspec, prefix `a1-u1:`, not pushed):
- 6f11a3c5 ledger: `budget_tokens.coordination_spend`, `a1` block, obligations C15/C16 (OPEN, check argv bound). `spent_measured` untouched.
- 5eed05c9 `tools/cep_gen2.py`: `check_receipt` accepts `kind: measurement` (cost + `decision_value`); optional `horizon_days`/`confidence`/`retirement_criterion` validated for every kind; unknown kind errors. Selftest gained 6 red mutants + 2 positive-pole cases.
- test_ce_a1 commit: `tools/test_ce_a1.py` (12/12, incl. null-as-zero mutant killed).

done_gate: exit 0 (all five commands). Tails: `CE_A1_PASS=12/12`, `OBL_TEST=PASS`, `CEP2_CLI_TEST=PASS (2 positive, 1 mutant)`, `CEP2_TRANCHE_TEST_PASS=9/9`, `CEP2_SELFTEST=PASS`.

Expected-RED evidence, real ledger:
`python3 tools/test_ce_a1.py --obligation C16` -> `C16 a1.spent None is UNKNOWN: unmeasured never passes` / `C16=FAIL`, exit 1.

Files touched: vault/programs/cognitive-economy/gen2/ledger.json, tools/cep_gen2.py, tools/test_ce_a1.py, this receipt.

UNKNOWN / left open:
- C15 on the real ledger exits 0 vacuously: `completion_plan.tranches` values are bare integers (budgets), so no tranche counts as started. I defined "started" as an object entry with `started: true` plus `receipt`; nothing was migrated to that shape (packet said keep keys). T0/T1 have md receipts, not JSON receipts, so they are not yet judged.
- C15/C16 are status OPEN with a bound check, as the packet says; the existing gate reports an OPEN-with-check obligation as a failure ("OPEN yet carries a check"), so `--final` stays red on them until they are flipped to CHECKED.
- Family `tranches` lists are not in the ledger (packet gave only `strikes`); a family at the strike limit with no declared tranches fails C15.
- `a1.spent` and `coordination_spend` stay null: the A1-2 meter is not built.
