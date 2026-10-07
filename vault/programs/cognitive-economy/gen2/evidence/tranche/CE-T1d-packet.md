done_gate: python tools/test_ce_t1_waiting.py

# CE-T1d -- C3 (part 2): WAITING with zero hot sessions via WAKE_FLAG; stale-pane lease revalidation

Contract: `vault/programs/cognitive-economy/gen2/COMPLETION-PLAN.md` -- read ONLY "Master Done-Gate" C3.
Fresh worker, no parent transcript. Do NOT spawn agents. Do NOT re-read files you do not edit.

## State you start from (do not rediscover)
- Read `CE-T1c-receipt.md` (same dir) first.
- WAKE_FLAG owner: `tools/wake_check.py` (`evaluate()`, `consume(goal, flag, receipts)`: flag -> one `wake` event on
  the bound goal's gsd_x GoalLog -> receipt); tests `tools/test_wake_flag_consumer.py`, `tools/test_wake_check.py`.
  `PP_WAKE_FLAG` env overrides the flag path -- use it; never touch the real WAKE_FLAG.json.
- Lease owner: `modules/lease` (ACTIVE/CONSUMED/EXPIRED, store); tests `tools/test_lease.py`.
- Claim owner: `tools/rollover.py` `claim()` / `_claim_stale()` / `_holder_dead()` (~l.739-826).

## Do
1. New `tools/test_ce_t1_waiting.py` (V-CE-T1-WAIT-* gates, `CE_T1_WAIT_PASS=n/n`, exit 0 only if all pass):
   a. WAITING zero-hot: a goal parked WAITING with no live session; writing the flag + one `consume()` produces
      exactly one `wake` event and a receipt, with zero model calls (assert no `claude` process is launched: inject
      a launcher that records calls and assert it was called 0 times). Consume twice -> still one wake (idempotent).
   b. No flag -> zero events (control).
   c. Stale-pane revalidation: a claim whose holder is dead (`_holder_dead` True via injected `alive`) is takeable;
      a live holder's claim is refused. An EXPIRED lease is not honoured as ACTIVE.
   If a gate shows the owner cannot do this, fix the owner minimally (keep signatures) and say so in the receipt.
2. Set C3 in `gen2/ledger.json`: `status: CHECKED`,
   `check: ["tools/test_ce_t1_lifecycle.py"]` plus a second obligation-level run is not supported, so make
   `tools/test_ce_t1_lifecycle.py` ALSO run `test_ce_t1_waiting.py` as a subprocess gate (V-CE-T1-LIFE-WAITING).
   Load / edit that one object / dump indent=1. Run `python tools/test_cep_gen2_obligations.py` -- green.
3. Run `python tools/test_wake_flag_consumer.py`, `python tools/test_lease.py` -- still green.

## Receipt
`vault/programs/cognitive-economy/gen2/evidence/tranche/CE-T1d-receipt.md`: gate table, CE_T1_WAIT_PASS line, owner
changes if any, `COMMITS: <hash ...>`. Pathspec commits only. Never push. Write the receipt BEFORE your last 2 calls.
