# C4 receipt
Status: DONE

Commits: 3339f7d6 (C4 breaker), 4c9ea6f4 (C3 run() gap); landed live via land_worktree, live HEAD f424dd4b, tests_after rc=0 (`python tools/test_semantic_breaker.py`, 30 passed, 0 failed).

Delivered:
- hooks/semantic_breaker.js: PostToolUse fold + trip, Pre refusal with recompile message, bound sessions only, kill switch CPP_SEM_BREAKER=off, fail open. Trip writes token-incidents/<ts>-<sid>.json (class TOKEN_INCIDENT), role autopsy when transcript_path exists, deny budget via session_budget_guard envelope (keeps an existing Owner envelope). Context growth not counted (needs transcript usage; recorded null, never guessed).
- Threshold from data (tools/semantic_breaker.py calibrate): 11 historical worker transcripts, 127 gaps, p50 0, p95 10, max 20. trip_calls = max(p95, 25) = 25 (p95 would false-trip legit exploration). Recorded in vault/config/semantic-breaker.json.
- Tests: trip at 30/25 no-progress calls, commits/edits/red->green/head-moved reset, kill switch, unbound inert, fail open, incident shape, deny budget, mutation drill (10 mutants all RED).

C3 gap (own commit 4c9ea6f4): hooks/cognitive_admission.js had no run(); added. tools/test_cognitive_admission_dispatch.py drives the real hook-dispatcher CLI on PreToolUse-Agent-default: first spawn admitted, duplicate denied, kill switch admits (4 passed). test_cognitive_admission.py still 22 passed.

Live canary: landed hooks copied to a temp layout, real dispatcher CLI, throwaway bound sid c4-canary-throwaway looping Grep. Tripped at call 25, next PreToolUse denied "TOKEN_INCIDENT (semantic breaker)". Incident: C:\Users\User\.claude\state\token-incidents\2026-10-12T21-27-34-071Z-c4-canary-throwaway.json (counters calls_since_progress 25, last_tools Grep x12, deny_budget written).

NOT_PROVEN / notes:
- The canary was a synthetic loop through the dispatcher, not a full armed mission. Autopsy was "unavailable" because the synthetic event carries no transcript_path.
- The deployed ~/.claude/hooks/hook-dispatcher.js mirror does not yet list semantic_breaker (0 matches); the repo dispatcher does. Mirror sync (Copy-Item) is left to the Owner, since it activates the breaker in every bound session.
