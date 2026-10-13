# C10 receipt
Status: DONE

Commits: worktree "cdc C10: holdouts, canary, admission non-spawn fix" (feat/cdc); live landing eb78a98c (land_worktree ok, tests_after rc=0).
- PROVEN (replay): 28 holdout traces (Live QA x11, Clock A x2, intent/order x1, DWS x14; 4 dws-p2-baseline stubs excluded) via tools/cdc_holdout.py (7/7 incl. mutant). Avoidable share under CDC rules: Live QA 7.1 %, Clock A 15.1 %, intent/order 17.0 %, DWS 20.2 %; breaker-trip share 1.4 / 0.5 / 0.9 / 5.9 %. Report evidence/holdouts.md.
- UNKNOWN (not 0): admission denials in history. NOT_PROVEN: any realised saving (traces were ungoverned); deny-at-25 correctness per call.
- PROVEN: cross-domain canary in TUA-X (read-only, claude -p): run 2 completed correctly, 4 turns, ~326k processed tokens, 0 denials, no breaker trip. Guards were wired by --settings, so inheritance stays NOT_PROVEN (C9: deployed dispatcher lacks them).
- BUG found+fixed: cognitive_admission.js denied every non-spawn tool as DUPLICATE (empty-prompt hash) when wired on `*`; run 1 blocked (4 false denials, 0.34 USD). Test C10-NONSPAWN + mutant, 24/24; KV vault/lessons/cognitive-admission-empty-prompt-duplicate.md.
Next unit must know: the Owner deploy of hooks/hook-dispatcher.js is still pending; C11 gates on holdouts must treat avoidable shares as replay estimates. Calls used: ~30.
