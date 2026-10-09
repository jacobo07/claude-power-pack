# P2b receipt

Authority: Owner "fund it" 2026-10-09 (one A/A job, from the main pane, no worker). No ceiling was named. The main pane
set its own ceiling of 1.0M without projecting it from the measured per-call floor; see Spend.
Status: BLOCKED. The first job FAILED in custody before any compile. The fix is committed and drilled. The resend would
use the root's LAST cap slot, so it waits for the Owner.

## Job 1 -- ksrmb-20261009-072932 (build reproduce-20261008T211412Z)
- Pre-checks, read immediately before the send:
  - pins: PINS=OK, and the pins sha256 equals the build record (41ad9cee...).
  - slot_ledger --status: PASS, events=23, violations=0, lease=none.
  - GEX44: idle (current_job_id null, queue_depth 0), boots 0/6.
  - send's own route preflight with --require-return: ROUTABLE.
- Send: one jobs_ledger row in the RF root (seq 1, phase 2, cap 1 of 2). Uploads were task.json and payload.tar; the
  runner files were already staged with equal sha256. Result QUEUED_NOT_RUNNING at 180 s, which was GEX44 boot latency.
  wait reported COLLECTED, and repatriate reported REPATRIATE=OK, tree 3e3f16b4....
- GEX44 verdict: FAIL INVALID_CUSTODY. "unit main_802B87E8.s21 entity 'main:802B87E8.s21'". On arrival, capsule 119/119,
  payload, task, runner and tools all verified. Nothing was compiled, and the return holds no run/units.
- Cause: runner_lib.ENTITY_RE (`^[A-Za-z0-9_.-]{1,32}:[0-9A-Fa-f]{1,16}$`) admits only a hex address after the colon.
  P2a's reproduce.build_units put the seq into the entity, and the P2a drill never ran the runner's own unit check.

## Fix -- recon 1c2b89f (runner_lib unchanged, so the judge revision is unchanged)
- reproduce.py: an AA unit sends the plain entity. Its seq and mutant mark travel in unit_id (main_X.s21, .s110.mut).
  Non-AA tasks are byte-identical to before.
- oracle_parity.aa_returned reads the seq and the mutant mark from unit_id when the entity is plain.
- test_p2a.py gains V-P2A-RUNNER-ACCEPTS: runner_lib._check_reproduce_unit on every built unit, plus a control that the
  old entity shape is refused. BUILD asserts that the jobs ledger does not grow. P2A_DRILL=8/8.
- Differential on the real tasks: old 211412Z is refused 41/41 with the GEX44 message. New
  reproduce-20261009T074333Z is refused 0/41, and its admission block is accepted. Its payload sha256 is the same
  (34cc3993...); only task.json changes (c7f9fa66...).

## Spend (main pane ce1c3a41, usage deduplicated by message.id)
- P2b to date: 49 model calls, 12,177,177 processed, 26,349 out. That is 12x the self-set 1.0M ceiling. A main-pane
  call here costs ~250k of cache reads, so 1.0M was ~4 calls.
- The same session BEFORE "fund it" (P2a close, P2a meter, P2b point 1, D11 step 1): 64 calls, 10,812,318. It was not
  in the tranche ledger, which counts worker transcripts only.

## Open (Owner)
1. Resend: send reproduce-20261009T074333Z only. It takes the RF root's 2nd and last phase-2 slot, which AA_GATE had
   assigned to "one parity capsule".
2. Budget: the resend costs ~6 to 10 main-pane calls (pre-checks, send, wait, repatriate, judge, receipt), i.e.
   1.5M to 2.5M at ~250k per call, or less from a fresh pane.
3. Do not send 211354Z, 211412Z or 215900Z: they are custody-invalid.
