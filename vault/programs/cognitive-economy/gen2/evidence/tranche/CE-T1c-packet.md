done_gate: python tools/test_ce_t1_lifecycle.py

# CE-T1c -- C3 (part 1): SAFE_TO_FORGET both poles, kclear->clear->kresume canary, autocompact demoted

Contract: `vault/programs/cognitive-economy/gen2/COMPLETION-PLAN.md` -- read ONLY "Master Done-Gate" C3.
Fresh worker, no parent transcript. Do NOT spawn agents. Do NOT re-read files you do not edit.

## State you start from (do not rediscover)
- Read `CE-T1a-receipt.md` and `CE-T1b-receipt.md` (same dir) first: forget_safe + exit 9, and the sandbox pattern
  in `tools/test_ce_t1_state.py`. Reuse that file's helpers by import; do not copy them.
- `tools/rollover.py`: `gate()` (~l.520) is the one authority for `/clear`; `decide()` (~l.635) chooses the
  continuation at the context wall (rollover vs compaction). The `/kclear -> /clear -> /kresume` sequence is
  seal -> gate SAFE_TO_FORGET -> (clear) -> resume_flow -> certify_flow.

## Do
1. New `tools/test_ce_t1_lifecycle.py` (V-CE-T1-LIFE-* gates, `CE_T1_LIFE_PASS=n/n`, exit 0 only if all pass), real
   functions, temp state_dir + temp git repo:
   a. SAFE_TO_FORGET pole: complete sealed capsule -> gate SAFE_TO_FORGET.
   b. REFUSED poles: unsealed; bytes changed; aged past max_age_s; already certified. Each REFUSED with its reason.
   c. Canary chain: seal -> gate -> (transcript removed = the clear) -> resume_flow -> certify_flow with the exam's
      answers -> RESUME_CERTIFIED and `.certified` exists; a second claimant is refused (exit 5).
   d. Autocompact demotion: on a path whose capsule is FORGET_SAFE, `decide()` must not return compaction as the
      continuation; it may only be the fallback when no certifiable capsule exists. If `decide()` today can return
      compaction on a certified path, change `decide()` minimally (keep its signature) and say so in the receipt.
      Both poles: certified -> not compaction; no capsule -> compaction fallback allowed.
2. Run `python tools/test_rollover.py` and `python tools/test_rollover_decide_evidence.py` -- still green.
3. Do NOT edit ledger C3 (CE-T1d finishes C3).

## Receipt
`vault/programs/cognitive-economy/gen2/evidence/tranche/CE-T1c-receipt.md`: gate table, CE_T1_LIFE_PASS line, whether
`decide()` changed (diff summary), `COMMITS: <hash ...>`. Pathspec commits only. Never push. Write the receipt BEFORE
your last 2 calls.
