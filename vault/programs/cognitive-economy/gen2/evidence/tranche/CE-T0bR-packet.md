done_gate: python tools/test_cep_gen2_obligations.py

# CE-T0bR -- finish declaring the Master Done-Gate obligations (continuation of CE-T0b)

Contract: `vault/programs/cognitive-economy/gen2/COMPLETION-PLAN.md` -- read ONLY its "Master Done-Gate" section.
Fresh worker, no parent transcript. Do NOT spawn agents. Do NOT re-read files you do not edit.

## State you start from (do not rediscover)
- The previous worker (23501b2c) hit its cap before writing a receipt. Its partial work is commit f19838dd on this
  branch: `tools/cep_gen2.py` assesses an obligation that carries a `check` key (runs it; non-zero or missing tool ->
  not passing), and `tools/test_cep_gen2_obligations.py` was adjusted. It is UNVERIFIED. `cep_gen2.py` is the owner;
  `tools/test_cognitive_economy_program.py --generation 2` consumes it (prints `CEP2_OBLIGATIONS=...`). Do not move
  the logic elsewhere.
- `gen2/ledger.json` still has `obligations_declared: false` and `obligations: []`.

## Do
1. `git show f19838dd --stat` then read only the changed hunks. Run `python tools/test_cep_gen2_obligations.py`;
   fix what is red.
2. Declare C1-C14 in `gen2/ledger.json` (load; set `obligations_declared: true`, `obligations`; dump indent=1; no
   other key). Each: id, one-line clause, owner tranche (T0-T9 from the card), `check` argv or null. Use the schema
   cep_gen2 already reads; a null check = OPEN = not passing. UNKNOWN never passes.
3. Selftest/test cases, both poles: all-pass control; one OPEN; one check exit 1; one check whose tool is missing.
   Mutation: copy cep_gen2.py, make OPEN count as passing, import the copy, assert red.
4. Run `python tools/test_cognitive_economy_program.py --generation 2 --final` once: it must FAIL and name obligations.

## Receipt
`vault/programs/cognitive-economy/gen2/evidence/tranche/CE-T0b-receipt.md`: the 14 obligations table (id / tranche /
check or OPEN), test pass line, mutation result, `--final` summary lines, `COMMITS: <hash ...>` (include f19838dd
only if you kept its code). Pathspec commits only. Never push. Write the receipt BEFORE your last 2 calls.
