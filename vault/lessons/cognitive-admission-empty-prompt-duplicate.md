# cognitive_admission denies every non-spawn tool as DUPLICATE when wired on `*` (CDC C10)
- Symptom: `claude -p` read-only task, Read/Grep denied "COGNITIVE ADMISSION -- DUPLICATE e3b0c44298fc1c14"; model gave up after 4 denials.
- Trigger: hook registered on matcher `*` (not the dispatcher's Agent|Task route). Read/Grep have no `prompt`, so phash('') is constant.
- Root cause: decide() hashed `prompt||description` for any tool and applied the 120 s duplicate window; no tool_name or empty-prompt guard.
- Fix: non-Agent/Task tool_name or empty prompt -> allow (hooks/cognitive_admission.js).
- Prevention: a guard written for one edge must check the edge's tool_name itself; test it wired on `*`.
- Regression proof: tools/test_cognitive_admission.py C10-NONSPAWN + mutant NONSPAWN (24/24); canary run 2 in vault/programs/cdc/evidence/holdouts.md.
