done_gate: python tools/test_ce_t1_state.py

# CE-T1b -- C2: transcript-deletion + handoff-destruction tests

Contract: `vault/programs/cognitive-economy/gen2/COMPLETION-PLAN.md` -- read ONLY "Master Done-Gate" C2.
Fresh worker, no parent transcript. Do NOT spawn agents. Do NOT re-read files you do not edit.

## State you start from (do not rediscover)
- CE-T1a (previous step, same branch) added `rollover.forget_safe()` and a certify refusal (exit 9) when the capsule
  alone cannot carry the continuation. Read its receipt `CE-T1a-receipt.md` first (one file).
- `tools/rollover.py`: `compile_capsule`, `seal`, `gate`, `resume_flow`, `certify_flow` take a `state_dir`; the
  existing tests (`tools/test_rollover.py`, `tools/test_rollover_capsule_v2.py`) show the sandbox pattern -- copy it,
  never touch the real `~/.claude/state`.
- Obligation C2 in `vault/programs/cognitive-economy/gen2/ledger.json` is `status: OPEN, check: null`.

## Do
1. New `tools/test_ce_t1_state.py` (V-CE-T1-STATE-* gates, `print("CE_T1_STATE_PASS=n/n")`, exit 0 only if all pass),
   driving the REAL functions in a temp state_dir + a temp git repo:
   a. seal -> delete the session transcript -> resume_flow + certify_flow still reach RESUME_CERTIFIED (model-free).
   b. seal -> delete the handoff prose file -> same result.
   c. both deleted -> same result.
   d. control (must go red): delete the goal file -> certify refuses (exit 9 from CE-T1a), capsule not retired.
   e. control: capsule bytes edited after seal -> `gate()` REFUSED.
2. Set C2 in ledger.json: `status: CHECKED`, `check: ["tools/test_ce_t1_state.py"]` (load / edit that one object /
   dump indent=1; no other key). Run `python tools/test_cep_gen2_obligations.py` -- green.

## Receipt
`vault/programs/cognitive-economy/gen2/evidence/tranche/CE-T1b-receipt.md`: gate table (id / pole / result), the
CE_T1_STATE_PASS line, both controls observed red, `COMMITS: <hash ...>`. Pathspec commits only. Never push. Write the
receipt BEFORE your last 2 calls.
