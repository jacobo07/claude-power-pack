# CE-T1b receipt -- C2 transcript-deletion + handoff-destruction tests

Done-gate: `python tools/test_ce_t1_state.py` exit 0. Real seal / resume_flow / certify_flow / gate, temp state_dir + temp git repo; live ~/.claude/state/rollover fingerprinted unchanged.

| gate | pole | result |
|---|---|---|
| V-CE-T1-STATE-NO-TRANSCRIPT | green | PASS -- deleted=['transcript'] resume=0 certify=0 verdict=RESUME_CERTIFIED |
|  | red (control) |  --  |
| V-CE-T1-STATE-NO-HANDOFF | green | PASS -- deleted=['handoff'] resume=0 certify=0 verdict=RESUME_CERTIFIED |
|  | red (control) |  --  |
| V-CE-T1-STATE-NO-BOTH | green | PASS -- deleted=['transcript', 'handoff'] resume=0 certify=0 verdict=RESUME_CERTIFIED |
|  | red (control) |  --  |
|  | red (control) |  --  |
|  | red (control) |  --  |
|  | red (control) |  --  |
|  | green (pole) |  --  |
|  | green (pole) |  --  |

`CE_T1_STATE_PASS=11/11`

Controls observed red: deleted goal file -> certify_flow exit 9 (CE-T1a forget_safe), capsule kept unretired; capsule bytes edited after seal -> gate() REFUSED ('capsule on disk is not the bytes that were sealed'), against an untouched-capsule control of SAFE_TO_FORGET.

Ledger: C2 status CHECKED, check [tools/test_ce_t1_state.py]; tools/test_cep_gen2_obligations.py exit 0.

Note: CE-T1a-receipt.md was not present in the tree; CE-T1a state taken from commit d465eaef and rollover.forget_safe.

COMMITS: a5e8385f
