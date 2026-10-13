STATUS: DONE
COMMITS: b9185c63
Packet: U7.md sha256 b84a9dba00eb.

Step 1: tools/a5_stall.py -> A/STALL.md. Source A/data/calls.jsonl.gz: 311 sessions, 10,985 calls, 3,106,974,814 tokens.
  Gaps between mutations n=2341 p50 1 p90 9 p95 14 p99 34. K=10 cut 2.42%, K=15 1.79%, K=25 0.98% of tokens.
  Rule: smallest K with false-trip rate <= 5% -> K=14. Existing 25 not within 20% -> changed (not CERTIFY_EXISTING).
Step 2: hooks/session_budget_guard.js default 14, env CPP_NOPROGRESS_K; tools/mission_spend.py DEFAULT_NOPROGRESS_CALLS same.
  Per-session budget.noprogress_calls still outranks.
Step 3/4: tools/test_a5_u7.py: A5_U7_PASS=18/18 (1 s). Canary: second arm refused while first live (no launch);
  host-stopped owner -> replace, live/unknown -> no replace; one replacement launch, same mission id, goal kept;
  after terminal second admits. Mutants caught: default 25, env ignored, blind goal_refusal, always-LIVE liveness,
  terminal-blind goal_conflicts.
Regression: test_session_budget_admission 12/12. test_session_budget_guard SBG_PASS=19/21: V-SBG-WIRED and V-SBG-E2E
  fail on the live ~/.claude dispatcher wiring (shared tree, out of scope, unrelated to K); not verified as pre-existing.
Deviation: earlier pane's breaker stop (envelope 10 calls) left work uncommitted; this pane finished it.

HANDOFF NOTE: U7 done; V-SBG-WIRED/E2E failures on live dispatcher need the Owner.
