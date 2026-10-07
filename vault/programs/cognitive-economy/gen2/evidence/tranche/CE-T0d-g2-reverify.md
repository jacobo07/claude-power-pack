# CE-T0d -- G2 deterministic re-verification (zero model, read-only, no deploy)

When: 2026-10-07, run from laptop pane 71ccfa86 over ssh. Plane: GEX44 `~/missions/grammar/.claude/worktrees/wu-g2`,
HEAD 97412541 (branch worktree-wu-g2), `git status --porcelain` empty. Python 3 on GEX44.

| command | exit | summary line |
|---|---|---|
| `python3 tools/test_grammar_default.py` | 0 | GRAMMAR_PASS=41/41 threshold=41/41 |
| `python3 tools/test_grammar_compile.py` | 0 | GRAMMAR_COMPILE_PASS=62/62 threshold=62/62 |
| `python3 tools/test_gsd_mission_envelope.py` | 0 | ENVELOPE_PASS=39/39 threshold=39/39 |
| `python3 tools/test_gsd_mission.py` | 1 | MC_PASS=224/225; the red is V-MC-PLAN-FACTS-REFUSES-OVERLAP (pre-existing baseline red at 4053b006) |

Meaning: the WU-G2b done-gate passes and no new red appeared against the recorded baseline. This is a Proof of
Non-Work input for Macro-Goal B: re-running these gates is NOT an open obligation unless 97412541 moves.
NOT covered here (still open for Macro-Goal B): an independent review of the F1/F2 and law 5/6 code (a gate written by
the same worker cannot judge its own blind spots); the live supervisor still judges by GSD phases (mission
m-9d00610493fc BLOCKED "GSD NO_PHASES" despite a passing packet gate) because G1's packet-gate law is not deployed on
live daf90d00; stall breaker still blind to worktrees; G1 record m-604666a514a3 stale RUNNING+hold; deploy is Owner-only.
WU-G2b metered spend 9,757,948 vs 10M estimate (mission_spend.processed_tokens on the record).
