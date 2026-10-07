# S3 receipt -- WAKE_FLAG consumer (tranche context-runtime-3, carried from context-runtime-2)
verdict: PASS (unit scope). The consumer exists, is wired through the existing owners and the real producer -> consumer
path is green with both red poles. Not claimed: any production invocation. Nothing schedules `--consume` yet and no
production goal is bound to it; the nightly scheduler was not touched, so the 02:00 clause stays WAITING.

Owners extended (no second owner built):
- Producer and consumer share one file: `tools/wake_check.py`. `evaluate()` at :34 is unchanged. New `consume()` at :67,
  plus `--consume <repo-id> <goal-id>` in `__main__`.
- Goal state: the gsd_x goal spine `modules/gsd_x/goal/log.py` `GoalLog.read()`/`append()` (:144 / :173). The consumer
  appends ONE `wake` event (reason, gate_exit, flag_at, flag_sha256) through the log's compare-and-swap, so it
  inherits the CAS and the hash chain. It never writes event files itself. `modules/gsd_x/goal/contract.project()`
  reads a goal that carries the event (V-WAKE-PROJECT).

Path: evaluate() writes WAKE_FLAG.json -> consume() reads and validates it (wake is True) -> GoalLog.append('wake') ->
the flag is renamed to WAKE_FLAG.consumed.json -> a receipt is written to `gen2/wake_receipts/wake-<ts>-<OUTCOME>.json`
(env PP_WAKE_RECEIPTS overrides the location).
Outcomes:
- NO_FLAG: no receipt, goal untouched.
- MOVED.
- DUPLICATE: the flag's sha256 is already on the log.
- REFUSED: flag unreadable, flag not a wake report, goal log corrupt, or a lost race. A receipt carries the cause, the
  goal is untouched, and the flag is kept. CLI exit is 1.

Commands (repo root, Python312):
- `python tools/test_wake_flag_consumer.py` -> exit 0, WAKE_CONSUMER_PASS=8/8. Gates: V-WAKE-ABSENT, E2E, FLAG-RETIRED,
  PROJECT, IDEMPOTENT, REFUSE-FLAG, REFUSE-STATE (GoalLogCorrupt), CHAIN. Red poles are byte-snapshot comparisons of
  the goal dir.
- `python tools/test_wake_check.py` (existing producer gates) -> exit 0, which shows the producer was not regressed.
- `git commit -F <msg> -- tools/wake_check.py tools/test_wake_flag_consumer.py` -> exit 0, 2591bf00.

Owner items:
- Bind a real goal: which goal id should a wake move?
- Decide whether vault_summarize.py --check should call `--consume` after evaluate(). That is a scheduler-adjacent
  change and was left out on purpose.

COMMITS: 2591bf00
