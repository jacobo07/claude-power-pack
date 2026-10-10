# WU-C11 -- Done-gate evaluator + knowledge entries + rendered handoff

Common brief: `vault/programs/cdc/PROGRAMME.md`. Plan section: 6.

Goal: the 24 Master Done-Gates are evaluated by code.
1. `tools/cdc_gate.py`: one check per gate reading evidence files/receipts/jsonl rows (PASS / FAIL / UNKNOWN /
   EXTERNAL_LIMITATION with reason; UNKNOWN never counts as PASS). Self-test with a planted missing artifact.
2. Run it; store `vault/programs/cdc/evidence/cdc-gate.json`. Any FAIL that is in scope -> insert a continuation unit
   for it before C12 (PROGRAMME step 4) instead of proceeding.
3. Knowledge Vault entries for every bug met in C0-C10; FIOS classes; UKDL hard rules (only proven), process rule,
   traps (dedup against existing).
4. `vault/programs/cdc/HANDOFF.md` rendered from state by a script (no free-form generation).
Land via land_worktree.
