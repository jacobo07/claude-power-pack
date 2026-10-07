done_gate: python tools/test_cep_gen2_obligations.py

# CE-T1a -- spend-clause DEBT + Forget-Safety check in certify

Contract: `vault/programs/cognitive-economy/gen2/COMPLETION-PLAN.md` -- read ONLY its "Execution log" (DEBT line) and
"Master Done-Gate" C3. Fresh worker, no parent transcript. Do NOT spawn agents. Do NOT re-read files you do not edit.

## State you start from (do not rediscover)
- `tools/cep_gen2.py` lines ~75-79: `spent_measured` is now a dict `{value, sources, unknown}` but the clause only
  type-guards it, so a dict is reported "not comparable" and a real overrun is never judged.
- `tools/rollover.py`: `certify()` (~l.984) judges exam answers only; `certify_flow()` (~l.1299) retires the capsule.
  `completeness()` (~l.380) and `safe_to_forget()` (~l.481) already exist. Nothing checks, at certify time, that the
  MACHINE continuation (capsule fields: goal pointer, obligations, branch/head) suffices WITHOUT the handoff prose file
  (`handoff_facts`, ~l.329).

## Do
1. cep_gen2: accept `spent_measured` as int OR `{value:int, unknown:bool|list}`. Compare `value` vs
   `authorization_boundary`. `unknown` truthy, value missing/non-int -> fail "UNKNOWN never passes". Over boundary
   without `owner_extension` -> fail. Tests in `tools/test_cep_gen2_obligations.py`, both poles: dict under (pass),
   dict over (fail), dict unknown (fail), int under (pass). Mutant: copy cep_gen2.py, make unknown pass, import, red.
2. rollover: add `forget_safe(capsule) -> {verdict: FORGET_SAFE|FORGET_UNSAFE, missing:[...]}` = the capsule alone
   names a readable goal file, >=1 obligation, branch and head; handoff prose is NOT consulted. `certify_flow` refuses
   to retire (new exit 9, ledger row `certify_forget_unsafe`) when FORGET_UNSAFE; existing exits unchanged. Tests in
   `tools/test_rollover.py` (extend; reuse its sandbox state_dir helpers): both poles, plus "handoff file deleted ->
   still FORGET_SAFE" and "goal pointer missing -> exit 9, capsule NOT retired".
3. Run `python tools/test_rollover.py`, `python tools/test_rollover_capsule_v2.py`,
   `python tools/test_cep_gen2_obligations.py`. All green.

## Receipt
`vault/programs/cognitive-economy/gen2/evidence/tranche/CE-T1a-receipt.md`: what changed (file:function), test pass
lines, mutant result, `COMMITS: <hash ...>`. Pathspec commits only. Never push. Write the receipt BEFORE your last 2 calls.
