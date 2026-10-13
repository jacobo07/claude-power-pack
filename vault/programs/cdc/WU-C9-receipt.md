# C9 receipt
Status: DONE

Commits: worktree "cdc C9: retirements, registration test, UKDL candidates, inheritance probe"; live landing 0d64b4af (land_worktree ok, tests_after rc=0).
- PROVEN: R1 rule retirement. CLAUDE.md "Bash is not the default" bullet -> one-line pointer, -213 chars (19502 -> 19289). Guard test hooks/_tests/test-bash-bridge-guard-v15.js 31/31. Backup ~/.claude/backups/cdc-20261013-074826/CLAUDE.md; revert command in evidence/C9-retirements.md. Other bullets NOT retired (guard absent/untested).
- PROVEN (policy level): R2 role retirement, green-path reviewer, via tier_routing.review_policy (C5, 15/15). NOT_PROVEN: that the landing flow calls it every time.
- PROVEN: tools/test_cdc_registration.py: C3/C4/C6 hooks chained in repo dispatcher and files exist; 2 mutants flagged; C7 cognitive_ci.py present. Matcher liveness 3/3 and hookreg 15/15 still green. C7 is a land-time gate, not a hook.
- DONE: UKDL candidates (6, marked not promoted, no duplicates existed) appended to vault/knowledge_base/ukdl-universal.md.
- NOT_PROVEN (observed FALSE): fresh-repo inheritance. Scratch git repo, `claude -p` Agent spawn succeeded; no row added to cognitive-admission.jsonl (12084 bytes before/after). Deployed ~/.claude/hooks/hook-dispatcher.js lacks cognitive_admission and semantic_breaker. Evidence: evidence/C9-inheritance.md.
Next unit must know: Owner act pending: Copy-Item repo hooks/hook-dispatcher.js to ~/.claude/hooks/ (activates C3/C4/C6 in every session), then re-run the probe and expect an allow row. Calls used: ~22.