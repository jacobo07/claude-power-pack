# C6 receipt
Status: DONE

Commits: worktree "cdc C6: derivation store, research reuse hook..." ; live landing sha 230933f55677 (land_worktree, tests after rebase rc=0).
Files: tools/derivation_store.py, hooks/research_reuse.js, tools/test_derivation_store.py, dispatcher chains PreToolUse-Web-default / PostToolUse-Web-default, evidence/C6-proof.jsonl.

- PROVEN: store hit / miss / stale dep -> miss / TTL / singleflight / abandoned lock recovery (30 min) / key parity py<->js / kill switch / fail-open / negative knowledge advisory (fixture) -- 24 tests green.
- PROVEN: mutation drill (bound-deny, in-flight subscribe, kill switch disabled in copies -> behaviour flips).
- PROVEN: two-session proof, evidence/C6-proof.jsonl: sess-A asks and stores, sess-B (bound) is denied with the stored answer path.
- NOT_PROVEN: live effect. settings.json registration of --event=PreToolUse-Web-default / PostToolUse-Web-default on matcher WebSearch|WebFetch is an Owner step (like the Agent lane); no live WebSearch call observed.
- NOT_PROVEN: FIOS lookup (negative knowledge scans CLAE_TRAPS + UKDL only; FIOS_INDEX not wired).

Next unit must know: hook lock window is 300 s (CPP_RESEARCH_LOCK_S), shorter than store's 30 min, because Post never fires on failed calls. Bound = cognitive-unit file or goal binding. Calls used: ~20.
