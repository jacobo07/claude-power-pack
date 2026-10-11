# WU-E3 receipt (written by the coordinator; both E3 workers ended without one)
Status: DONE
- Commit: bc3f1199 "feat(ewc): E3 pre-stop unresolved-obligation gate + anti-livelock" (wt_ewc, branch ewc/closure).
- Workers: m-defd6cd03ac2 (861K tokens, no receipt), m-6e6382f12f90 (2.26M tokens, no receipt). Chain finalized E3 "sealed" at 14:58.
- PROVEN (coordinator, 2026-10-11 ~16:40): `python tools/test_ewc.py` EWC_PASS=31/31, exit 0 -- including the incident
  CONTINUE, the complete/human-only controls, STALLED after 3 no-progress continuations, BUDGET, RAM floor, no ping-pong
  with closer-guard, goal-bound CONTINUE without writing a binding. Caveat: measured on a tree that also carried E4's
  uncommitted edits to gsd_stop_continuation.js / ewc_gate.js.
- CLAIMED, not re-measured: 11 node tests (hooks/tests/test-ewc-stop-gate.js) and both mutation drills (CONTINUE,
  STOP_UNKNOWN) killed -- from the commit message only.
- NOT_PROVEN: the critical-lane latency budget (step 5, n=5 before/after medians). No measurement on disk. E5 or E6 must
  measure it before the merge.
- Re-gate note (22:15): the chain's 16:55 refusal was a 30 s subprocess timeout inside test_ewc.py, not a failed
  assertion. Re-run at 22:00: 39/39 rc 0. Host then: bare `node -e 0` 2.5-4.1 s, 31 claude.exe, 101 node, 2.9 GB free.
  Latency (n=3, real 2.7 MB transcript, shadow): OLD hook 6055/4029/3452 ms, NEW 4598/3326/4668 ms -- the added cost is
  below the host's node-startup noise; a clean +300 ms proof still needs a quiet host (E5 step 7).
- Modes shipped: CPP_EWC_GATE=shadow|enforce|off; interactive default shadow; armed missions and goal-bound sessions enforce.
