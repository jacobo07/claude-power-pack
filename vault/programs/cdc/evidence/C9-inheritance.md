# C9 fresh-repo inheritance (2026-10-13)
Scratch: %TEMP%\cdc-c9-scratch-075050 (git init, no opt-in flags). `claude -p` asked for one Agent spawn (no prior work), --max-turns 3.
Observed: the Agent spawned and replied "ok". ~/.claude/state/cognitive-admission.jsonl stayed 12084 bytes: NO admission row, no deny.
Cause (verified): deployed ~/.claude/hooks/hook-dispatcher.js has 0 matches for cognitive_admission / semantic_breaker; the repo dispatcher has them. Also the session was unbound (no unit), so decide() would be inert.
Verdict: INHERITANCE NOT_PROVEN (observed FALSE for the deployed estate). Fix = Copy-Item repo hooks/hook-dispatcher.js to ~/.claude/hooks/ (all-session activation; Owner act, hooks-dir deploy), then re-run this probe and expect an allow row.
