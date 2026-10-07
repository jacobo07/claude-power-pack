done_gate: python tools/test_cognitive_economy_program.py --generation 2 --selftest

# CE-T0b -- declare the Master Done-Gate obligations (gen2 completion, tranche T0, EXECUTION)

Contract: `vault/programs/cognitive-economy/gen2/COMPLETION-PLAN.md` -- read ONLY its "Master Done-Gate" section
(obligations C1-C14). Fresh worker, no parent transcript. Do NOT spawn agents. One Write per new file.

## Do
1. Read how `tools/test_cognitive_economy_program.py --generation 2` assesses obligations today (it prints
   `CEP2_OBLIGATIONS=UNASSESSED` because `gen2/ledger.json` has `obligations_declared: false`, `obligations: []`), and
   what schema an obligation must have to be judged. Extend that existing mechanism; do not write a second gate.
2. Declare C1-C14 in `gen2/ledger.json` (load, set `obligations_declared: true` and `obligations`, dump indent=1; touch
   no other key). Each obligation: id, the clause text compressed to one line, the work unit/tranche that owns it
   (T0-T9 per the card), and an executable `check` (argv) that will prove it. Where the check's tool does not exist
   yet, the obligation's status is OPEN with `check: null` and the gate must report it as not passing -- never skipped,
   never green. UNKNOWN never passes.
3. The `--final` verdict must FAIL while any obligation is OPEN or its check exits non-zero, and PASS only when all
   checks exit 0 and all work units have terminals. Add selftest cases for both poles (all-pass control; one OPEN; one
   check exiting 1; one check missing its tool) to the existing `--selftest`, plus a mutation check (copy the module,
   make an OPEN obligation count as passing, assert the selftest goes red).
4. Run `--generation 2 --final` once and paste its summary lines in the receipt: it must FAIL, now naming obligations.

## Receipt
`vault/programs/cognitive-economy/gen2/evidence/tranche/CE-T0b-receipt.md`: schema used, the 14 obligations as a table
(id / owner tranche / check or OPEN), selftest pass line, mutation result, `--final` summary, `COMMITS: <hash ...>`.
Pathspec commits only. Never push.
