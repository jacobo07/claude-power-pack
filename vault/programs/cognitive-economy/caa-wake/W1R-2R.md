# caa-wake W1R-2R -- residual of W1R-2: mutation proof, canonical W1 receipt, arm W2

Goal `caa-wake-t3` (cap 2,200,000; Owner 2026-10-09, after the t2 over-attribution incident in
`vault/plans/caa-wake-incident-2026-10-08-t2-overcharge.md`). Worktree `C:\Users\User\Apps\pp-caa-wake-t3`, branch
`ce/caa-wake-t3`, cut from ce/caa-wake-t2 at 6de3e888. Slim worker, no Agent spawns. Use PowerShell with absolute
git and python paths. Never cd outside this worktree.

W1R-2 (m-3f3c48d7404d) halted on the stall breaker: it backgrounded the whole drill and polled it, so tokens were
spent while the work tree did not change. One suite run takes 98-172 s (about 196 git spawns at about 0.48 s each),
and each mutant costs two runs.

Read ONLY:
- this file;
- `vault/programs/cognitive-economy/caa-wake/W1R-1-receipt.md`;
- the "Mutants" list in `W1-packet.md`;
- `tools/caa_w1r2_drill.py` (the six mutant specs, already written; it resolves its own repo root);
- `tools/test_mission_wait.py`, only the gate a mutant must turn red.

## Rules (from the incident)
- Never `run_in_background` and never poll. Each long step is ONE foreground call with timeout 600000.
- After each mutant, append its verdict line verbatim to `vault/programs/cognitive-economy/caa-wake/W1R-2-mutants.md`
  and commit that file by pathspec in the same call, so the work tree changes between calls.

## Do
1. Commit the uncommitted ZEROMODEL port first: `tools/test_mission_wait.py` (+16, V-WAIT-ZEROMODEL) and
   `tools/caa_w1r2_drill.py`. Run `tools/test_mission_wait.py` once in the foreground and require WAIT_PASS=14/14.
   Then run the wake-consumer suite and require 8/8. Put both gate lines in the commit message.
2. Run the six mutants one per call, `python tools/caa_w1r2_drill.py <name>` (isolated copy, never the live
   file), names: `edge-triggered`, `no-CAS`, `skipped-invalidator`, `worktree-read`, `UNKNOWN-as-satisfied`,
   `contains-ignored`. Each mutant must turn a NAMED V-WAIT gate red.
   A survivor means you add the missing assertion and rerun that mutant once (two-strike).
3. Port the waiting assertions from `git show ce/gen2-completion:tools/test_ce_t1_waiting.py` that apply to
   mission_wait and are not already ported. Keep both suites green.
4. Write the canonical `vault/programs/cognitive-economy/caa-wake/W1-receipt.md`:
   decision / effect / proof (both suites' gate lines and every mutant line, verbatim) / unknowns / commits / spend.
   It says `status: DONE` only if every gate is green and every mutant was killed. Commit it by pathspec, with
   `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`.
5. Close: arm W2 with the three-call recipe, in this worktree:
   - `arm --no-launch --cwd C:\Users\User\Apps\pp-caa-wake-t3 --command "Read vault/programs/cognitive-economy/caa-wake/W2.md and execute it." --rollover-protocol capsule-v2 --max-cycles 3 --max-hours 6`;
   - `envelope --token-estimate 900000 --model sonnet --wu-packet <abs W2.md>`;
   - `admit --route <abs route-W2.json>`.
   Record the mission id and verdict in W1-receipt.md. End the turn with `HANDOFF NOTE:`. Never ask a person to run
   anything.
