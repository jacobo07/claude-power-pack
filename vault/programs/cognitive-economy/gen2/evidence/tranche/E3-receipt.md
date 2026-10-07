# E3 receipt -- HARD RULES single authority (closed by T0, deterministic)

VERDICT: PASS
- Work by worker 513bf490 (budget breaker stopped it before committing); closed by T0 with no model worker.
- Inventory: archive 9 ids, mirror 30 -> 36/36 after merge; HR-NOVELTY-001 differed, archive kept (both traced to 48e1a502).
- Classifier: mechanical 12, judgmental 24, 0 stub/test/obsolete.
- Proof: test_hard_rules_mirror -> HRM_PASS=11/11  threshold=11/11 (rc 0); test_hard_rules -> HARDRULES_PASS=14/14  threshold=14/14 (rc 0); drift mutation recorded by the worker (9/11 red, restored 11/11).
- test_faitp_debts: failing gates at base 86843dc1 = [V-MEMORY-POINTERS,V-MEMORY-SIZE]; with E3 = [V-MEMORY-POINTERS,V-MEMORY-SIZE] -> PRE-EXISTING (MEMORY.md size/pointer debt, unrelated to E3). Only a PASS line changed (real-rule corpus 156 -> 183, expected from the merge).
- T0 instrument defect, recorded: a first comparison matched the substring FAIL inside PASS lines (FAILCLOSED) and reported a false 'introduced'; rerun compared failing gate names only.
- Debt: project CLAUDE.md 40,410 chars after mirroring 6 archive-only rules (over the 40k warning).
- Physical model calls by T0: 0 (deterministic). BOUNDARIES: 1 (pre-existing vs introduced).

COMMITS: 7e9ad97f
