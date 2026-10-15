# C11 receipt
Status: DONE

Commits: worktree 07aec7d8 (feat/cdc); live landing 07aec7d8 (land_worktree ok, cognitive_ci GREEN, tests_after rc=0 `python tools/test_cdc_gate.py`).
- PROVEN: tools/cdc_gate.py evaluates 24 gates from receipts/evidence files/jsonl rows/deployed dispatcher; UNKNOWN never PASS. tools/test_cdc_gate.py: planted missing artifact flips gates 3/8/12/14/19 to FAIL, non-DONE receipt FAIL, missing marker UNKNOWN, kill-switch/lesson/handoff mutants FAIL; --selftest ok.
- PROVEN: gate run stored evidence/cdc-gate.json: PASS 17, FAIL 1, UNKNOWN 3 (gates 9, 17, 22), EXTERNAL_LIMITATION 3 (2, 4, 5). FAIL in scope: none. FAIL out of scope: gate 16 (deployed ~/.claude dispatcher lacks cognitive_admission + semantic_breaker; Copy-Item is an Owner act). No continuation unit inserted before C12 (decision in C11-gates.md).
- DEVIATION recorded: the brief's own 24-gate numbering is not stored in the repo; gates 2/4/5/18/19/22 keep plan numbers, the rest are defined in cdc_gate.py (map: vault/programs/cdc/C11-gates.md).
- DONE: 5 new KV lessons (vault/lessons/cdc-*.md) + the existing C10 one; UKDL promotions only for proven items (C7 regression refusal, C9 retirement rule, serial-proof rule, 2 traps); the other C9 candidates stay candidates.
- DONE: HANDOFF.md rendered by tools/cdc_handoff.py (deterministic, stamped; gate 24 rejects a hand-written one).
- NOT_PROVEN: FIOS wiring (FIOS_INDEX is Owner-gated; 6 failure classes proposed in C11-gates.md); gate 22 self-hosting (no per-unit ledger of CDC transcripts).
Next unit must know: C12 must not claim gates 9/16/17/22; the gate file must be re-run after any Owner dispatcher deploy (`python tools/cdc_gate.py && python tools/cdc_handoff.py`). Calls used: ~25.
