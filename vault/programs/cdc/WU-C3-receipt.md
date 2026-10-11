# C3 receipt
Status: DONE

Commits: worktree 909ad75b (landed live, live HEAD 909ad75b via land_worktree, tests_after rc=0).
- PROVEN: 4 deny branches (NO_WORK, EFFECT, LEASE, DUPLICATE) each RED->GREEN with admitted controls; mutation drill disabling each predicate turns its test RED (tools/test_cognitive_admission.py, 22/22). Kill switch CPP_COG_ADMISSION=off and fail-open on bad input proven. decide() ~1.2 ms/call (< 50 ms).
- PROVEN: one writer `tools/cognitive_admission.py record`, used by the hook (detached spawn) and gsd_mission.admit_route (edge=launch).
- PROVEN (hook level, real throwaway state dir, live-installed hook file): allow row then DUPLICATE deny row in cognitive-admission.jsonl (cap rows a068eac598cb55f5).
- NOT_PROVEN: a denied spawn from a real Claude session via the deployed dispatcher. The chain entry is in repo hooks/hook-dispatcher.js, but the deployed ~/.claude/hooks/hook-dispatcher.js has no cognitive_admission entry; needs a Copy-Item of the repo dispatcher (not done: hooks-dir deploy, shared by all sessions).
- Unit binding: <state>/cognitive-unit/<sid>.json (tools/cognitive_admission.bind_unit) or env CPP_COG_ROUTE/UNIT/ROOT; nothing writes it at launch yet (arm_chain does not know the sid) -> C-next should call bind_unit from the worker launch.
- Pre-existing, untouched: test_route_admission V-RADM-SLIM-T2-ADMITTED, V-RADM-SLIM-REPO-FILE-EXISTS fail.
- Duplicate window is a TTL (120 s), no PostToolUse completion signal.
