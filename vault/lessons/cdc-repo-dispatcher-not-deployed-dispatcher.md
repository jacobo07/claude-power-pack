# A guard chained in the repo dispatcher is not active: the deployed ~/.claude dispatcher lacked it (CDC C3/C4/C9)
- Symptom: C9 fresh-repo probe: `claude -p` Agent spawn succeeded, cognitive-admission.jsonl unchanged (12084 bytes before/after); deployed hook-dispatcher.js has 0 matches for cognitive_admission / semantic_breaker.
- Trigger: landing through land_worktree updates the live repo checkout, not the Copy-Item'd copy under ~/.claude/hooks.
- Root cause: two dispatcher files; deploy of the hooks dir is shared by all sessions and denied to workers.
- Fix: none by a worker (Owner act: Copy-Item repo hooks/hook-dispatcher.js). cdc_gate gate 16 reads the deployed file and stays FAIL until then.
- Prevention: "guard live" claims cite a row written through the deployed dispatcher; prior art feedback_hook_dispatcher_split_brain_mirror.
- Regression proof: tools/test_cdc_registration.py (repo side) + evidence/C9-inheritance.md (deployed side, observed false) + cdc_gate gate 16.
