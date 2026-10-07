# CE-T1c receipt -- C3 part 1: SAFE_TO_FORGET poles, kclear->clear->kresume canary, autocompact demoted

Done-gate: `python tools/test_ce_t1_lifecycle.py` exit 0. Real gate / resume_flow / certify_flow / decide; sandbox + fixtures imported from tools/test_ce_t1_state.py (STATE, make_repo, scenario, quiet, live_fingerprint), not copied.

| gate | result | evidence |
|---|---|---|
| V-CE-T1-LIFE-SAFE | PASS | verdict=SAFE_TO_FORGET reasons=[] |
| V-CE-T1-LIFE-REFUSED-UNSEALED | PASS | reasons=['the seal itself refused: not sealed: seal refused', 'the recorded receipt carries no sealed hash'] |
| V-CE-T1-LIFE-REFUSED-BYTES | PASS | reasons=['capsule on disk is not the bytes that were sealed'] |
| V-CE-T1-LIFE-REFUSED-AGED | PASS | fresh=SAFE_TO_FORGET aged reasons=['capsule sealed 1860s ago (limit 1800s): seal again before clearing'] |
| V-CE-T1-LIFE-CANARY | PASS | gate=SAFE_TO_FORGET resume=0 certify=0 verdict=RESUME_CERTIFIED certified=True |
| V-CE-T1-LIFE-SECOND-CLAIMANT | PASS | resume=5 certify=5 verdict=FENCED |
| V-CE-T1-LIFE-REFUSED-CERTIFIED | PASS | reasons=['capsule already certified and retired'] |
| V-CE-T1-LIFE-DEMOTE-CERTIFIED | PASS | forget_safe=FORGET_SAFE unknown-usage=True ok-usage=True |
| V-CE-T1-LIFE-DEMOTE-NO-CAPSULE | PASS | no capsule -> compaction fallback (usage no usage row) |
| V-CE-T1-LIFE-DEMOTE-NO-PRESSURE | PASS | below the wall an unreadable usage still never rolls (no pressure, no figures) |
| V-CE-T1-LIFE-LIVE-UNTOUCHED | PASS | live ~/.claude/state/rollover fingerprint unchanged |

`CE_T1_LIFE_PASS=11/11`

Regression: test_rollover.py ROLLOVER_PASS=64/64 exit 0; test_rollover_decide_evidence.py DECIDE_EVIDENCE_PASS=11/11 exit 0. test_ce_t1_state.py (not in this tranche's gate): first run 10/11, only V-CE-T1-STATE-LIVE-UNTOUCHED red (the live ~/.claude/state/rollover moved during the run, shared with other live sessions); rerun exit 1.

## decide() changed: YES (signature unchanged)

Before: `usage.state != OK` returned would_rollover=False first, so at the wall (used_pct >= pressure_pct) a session WITH a capsule fell through to autocompact whenever its usage row was unreadable. After: in that branch, used_pct >= pressure_pct AND capsule_bytes > 0 returns would_rollover=True (reason 'pressure ... with a capsule'); otherwise the old return is unchanged. Compaction stays the fallback only with no capsule (capsule_bytes <= 0). The capsule signal is the caller's capsule_bytes (observe() passes len(bootstrap(cap))); decide() does not itself re-judge FORGET_SAFE; the test pairs forget_safe(cap)=FORGET_SAFE with the bytes observe() would pass.

Note: CE-T1a-receipt.md is not in the tree (as CE-T1b noted). Ledger C3 not edited (CE-T1d).

COMMITS: 6ffc0566
