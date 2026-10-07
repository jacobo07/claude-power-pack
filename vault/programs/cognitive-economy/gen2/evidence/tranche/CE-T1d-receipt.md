# CE-T1d receipt -- C3 part 2: WAITING with zero hot sessions via WAKE_FLAG; stale-pane lease revalidation

Done-gate: `python tools/test_ce_t1_waiting.py` exit 0. It drives the real owners: `wake_check.consume`, `rollover.claim` / `_holder_dead` and `modules.lease.LeaseStore`. `PP_WAKE_FLAG`, `PP_WAKE_RECEIPTS` and `CPP_CLAUDE_SESSIONS_DIR` point at a temp dir. The real WAKE_FLAG.json and wake_receipts/ are fingerprinted before and after.

| gate | result | evidence |
|---|---|---|
| V-CE-T1-WAIT-RECORDER-LIVE | PASS | positive control: the launcher recorder caught `['claude', '--probe']` |
| V-CE-T1-WAIT-NO-FLAG | PASS | outcome=NO_FLAG events=1/1, no receipt, 0 launches |
| V-CE-T1-WAIT-ZERO-HOT | PASS | no_hot=True outcome=MOVED wakes=1 receipt=wake-...-MOVED.json launches=0 |
| V-CE-T1-WAIT-IDEMPOTENT | PASS | second=NO_FLAG (flag retired), replayed bytes=DUPLICATE, wakes=1, launches=0 |
| V-CE-T1-WAIT-PROJECT | PASS | gc.project reads the goal with the wake event |
| V-CE-T1-WAIT-DEAD-HOLDER-TAKEABLE | PASS | _holder_dead=True; claim taken over gen 2, reason 'holder process is gone' |
| V-CE-T1-WAIT-LIVE-HOLDER-REFUSED | PASS | _holder_dead=None (alive, unknown proc_start); claim refused, holder pane-A |
| V-CE-T1-WAIT-CLAIM-LEASE-EXPIRED | PASS | live holder but lease_until passed -> taken over, 'lease expired 1s ago' |
| V-CE-T1-WAIT-EXPIRED-NOT-ACTIVE | PASS | check before=True; after TTL check=False/not_live, renew=not_live, state=EXPIRED, next acquire ok |
| V-CE-T1-WAIT-LIVE-UNTOUCHED | PASS | real WAKE_FLAG.json + wake_receipts/ unchanged |

`CE_T1_WAIT_PASS=10/10`

"Zero model calls": during every consume(), the recorder replaces `subprocess.run/Popen/call/check_call/check_output` and `os.system`. Any launch would be recorded and refused. The recorder saw 0 calls. "Parked WAITING": a declared gsd_x goal with no session (empty sessions dir) and no claim record. gsd_x has no separate WAITING event, and I did not invent one.

## Wiring and regression
- `tools/test_ce_t1_lifecycle.py` now runs `test_ce_t1_waiting.py` as the subprocess gate V-CE-T1-LIFE-WAITING: `exit=0 CE_T1_WAIT_PASS=10/10`, `CE_T1_LIFE_PASS=12/12`, exit 0.
- Ledger C3: `status: CHECKED`, `check: ["tools/test_ce_t1_lifecycle.py"]`. I edited only that object; dump indent=1 with ensure_ascii False and a trailing newline (the byte round-trip was checked first).
- `test_cep_gen2_obligations.py` exit 0. Its live-ledger row still reports `status FAIL, declared=True` because other obligations are open. That is the programme verdict, not a red gate.
- `test_wake_flag_consumer.py` WAKE_CONSUMER_PASS=8/8, exit 0. `test_lease.py` LEASE_PASS=21/21, exit 0.

## Owner changes: NONE
Every behaviour asked for was already provided by the owners, so no signature or code changed.

COMMITS: 697bc611
