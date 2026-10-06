# RESUMPTION -- Gen3 T3 recompiled as global bounded execution (Owner-approved 2026-10-06)

Worktree `C:\Users\User\Apps\pp-gen3-t3`, branch `ce/gen3-t3-runtime`. The plan of record is
`vault/plans/global-bounded-execution-2026-10-05.md` (read it; it supersedes the old S3..S7 roadmap and the 50M cap).
Budget for everything remaining: warn 13M, HARD STOP 20M processed, summed over successor sessions from 2026-10-06.
Spend so far in the new graph: session d8d8d060 (planning + c1 + c0) -- meter it with tools/mission_spend.py
session-status --transcript <its jsonl> before declaring the next envelope.

## Sealed
- S1 80c356fb agent-solo session scope. S2 4eb924a6 tree meter + child reserve + per_child_stop + dispatch reserve
  (SBT 6/6 re-run before commit). c0 = the plan file + this file.

## Open facts (verify, do not trust)
- c2 DONE (session d64f90b2, 2026-10-06): V-SBG-LATENCY is NOT an S2 regression. Suite 5x interleaved: 646c6c86
  min 6.9 / p50 42.9 / 2 fails, HEAD min 45.6 / p50 119.1 / 4 fails (rank-sum U=19/25, not separable). In-process
  decide() A/B, 60x interleaved, 20k-row transcript: base min 10.05 p50 168.6, HEAD min 11.24 p50 159.5 -> S2 adds
  ~1 ms. Floor ~10 ms = the 20k-id state round-trip (read+parse ~4, Set ~4, stringify+write ~3; tiny state 1.8);
  tails 50-500 ms = host RAM pressure (3.8% free at session start) on both arms. Scripts: session scratchpad
  c2_latency.py / c2_bench.js / c2_parts.js. Consequence: c3 as written (skip readdir/stat over the known child set)
  saves ~1 ms; the hot path is the ids round-trip. c3 needs an Owner decision before any edit.
- Main checkout holds ANOTHER pane's uncommitted hunk in hooks/session_budget_guard.js and
  tools/test_session_budget_guard.py: land by `git diff 646c6c86..HEAD -- <paths> | git apply --3way` there, commit with
  `git apply --cached` of the same patch; never commit or overwrite the foreign hunk.
- Checkpoint misroute observed live: the 2cc507fd handoff sits in the pp-gen3-t3 project memory, its transcript in the PP
  project.

## Next 3 actions (one fresh worker per unit; at most 3 edit calls per file per unit)
0. DONE in this worktree (session bd2f5752, committed with c3): (a) ROLLACT 29/29 incl. self-seal gates + mutant red,
   (b) EXEMPT_CMD += session_checkpoint.py with V-SBG-EXEMPT covering it, (c) kclear.md step 5 ends on a trailing
   `/clear`. STILL OPEN: (d) land in the main checkout (live) by patch apply, with c5. c3 DONE too: V-SBG-LATENCY =
   min of 3 + V-SBG-LATENCY-RED-CONTROL (60 ms mutant). MARGINAL at 9% free RAM: run 1 min 155 ms FAIL, run 2 min
   45.9 PASS (mutant min 67.9) -- the cold-process floor sits near 50; Owner may want a warm-process measure.
   Original text of 0 follows for (d).
   Autonomous rotation after ANY
   /kclear. In modules/zero-crash/hooks/context-watchdog.py: `_self_sealed_step` +
   `_own_capsule` + ROLLOVER_SELF_SEAL_FLAG; called from the Stop path as `elif _rollover_active():` after the
   ROLLOVER_ASK_FLAG step 2. Root cause: step 2 (gate -> /clear dispatch -> kresume courier) was reachable only via
   ASK, set only by the context wall / econ trigger, so a manual or breaker /kclear ended as "run /clear" to the Owner.
   To do: (a) tests in tools/test_rollover_active_path.py: fresh own capsule -> rollover_clear_dispatched + courier;
   REFUSED/stale/certified/mission -> no dispatch; same seal twice -> one act (rearm clears ASK but not the self flag);
   _own_capsule == rollover.capsule_path and ROLLOVER_SELF_SEAL_MAX_AGE_S == rollover.RESET_MAX_AGE_S pinned;
   mutant (drop the self flag) must go red. (b) EXEMPT_CMD in hooks/session_budget_guard.js += session_checkpoint\.py
   (breaker blocked /kclear live). (c) commands/kclear.md step 5: on SAFE_TO_FORGET end with a trailing `/clear` line,
   never "suggest /clear". Known gap: no metrics file -> Stop returns before step 2 (same as the wall path).
   (d) land in the main checkout (live) by patch apply, with c5.
1. c3 RECOMPILED (Owner 2026-10-06: "Fix the gate, skip c3"; the 1.7M c3 allocation is dropped): make V-SBG-LATENCY in
   tools/test_session_budget_guard.py judge the MIN of 3 incremental calls (append one line before each) against 50 ms;
   keep the detail line printing all three. Red control: a mutant guard with a 60 ms busy-wait in advance() must FAIL
   it. Run the suite once, commit (~0.3M / 4 calls).
2. c4 DONE (session bd2f5752): agent-solo-guard calls decide(payload, {dispatch:true}) after the content checks and
   before the tracker entry (a denied dispatch holds no solo slot); fail-open on require/decide errors; the warn
   advisory is printed on allow. AGENT_SOLO_GUARD 25/25; pre-c4 guard exits 0 on the red case (BOM-free stdin; PS 5.1
   piping adds a BOM and fails BOTH arms open -- use cmd /c "node g.js < p.json"). pp-code-reviewer (Sonnet): APPROVE,
   0 C/H/M, 2 LOW (advisory test -- added; platform gate skips the budget check off Windows -- known gap).
   NEXT = c5. Main checkout is at 6124eecf with many foreign dirty files incl. hooks/session_budget_guard.js and
   tools/test_session_budget_guard.py; main-side commit ed172f48 touched the rollover path since 646c6c86, so use
   `git diff 646c6c86 -- <9 code paths> | git apply --3way` and inspect every conflict. Host was at 1.6% free RAM at
   c4 close: measure free RAM before the live probe.
3. c6-c7 rollover idempotency + checkpoint root; then c8 profile, R6 micro-canary, c11, c12 per the plan.

Start: read the plan file, `git -C C:\Users\User\Apps\pp-gen3-t3 log --oneline -4`, declare the session envelope
(mission_spend.py session-declare, stop <= the remaining hard stop), then action 1.
