done_gate: python tools/test_tranche_driver.py

# CE-T1f -- tranche_driver measurement: split spend, stop on launch failure, name receipt-less work, measured caps

Owner instruction (2026-10-07): "improve the systems that measure these things for them to optimize better and
assign more accurate budgets and control the spending better". Fresh worker, no parent transcript. Do NOT spawn
agents. Do NOT re-read files you do not edit. Owner file: `tools/tranche_driver.py` (148 lines); tests
`tools/test_tranche_driver.py` (V-DRIVER-*, 21/21 today). Do not create a second driver or meter.

## Evidence that motivates each change (measured, do not re-derive)
- E1 one cap, two payers: `drive()` sums coordinator spend + step spend against `--cap`. T1 run2: coordinator
  3.71M + workers 3.02M = 6.73M -> T1d REFUSED_OVER_CAP although workers were at 38% of the 8M tranche. The T0 log
  accounted worker spend vs tranche cap and the dispatch pane separately. The two numbers must never be one.
- E2 launch failure kept spending: T1 run1, account weekly limit -> all 5 workers launch_rc=1 in 14-46 s; the
  driver launched all 5 (one admission + one launch each) instead of stopping at the first.
- E3 receipt-less work reads as no work: T0b (945k) and T1a (989k) both committed real work but hit the cap before
  the receipt -> verdict FAIL with commits=False, indistinguishable from a worker that did nothing.
- E4 caps are guessed: every step is 1.4M; measured worker spend over 7 steps: 1,024,112 / 945,219 / 1,134,541 /
  989,449 / 888,613 / 1,142,163 (+ T0b partial). Steps that end near 1.0-1.15M of 1.4M either waste headroom or,
  when the receipt is last, run out.

## Do (keep signatures backward compatible; existing V-DRIVER-* stay green)
1. Split spend (E1): `--coordinator-cap N` (default None = old behaviour). When given, `--cap` bounds WORKER spend
   only and the coordinator is bounded by `--coordinator-cap`; refusal verdicts name which one tripped
   (`REFUSED_OVER_CAP` with `payer: worker|coordinator`). `res` always records `worker_spend` and `coordinator_spend`
   as separate fields (null when unmeasurable, never 0).
2. Launch failure stops (E2): `launch_rc` non-zero AND measured spend None or < one per-call floor -> verdict
   `LAUNCH_FAILED`, `break`. A non-zero rc with real spend keeps the old FAIL path.
3. Receipt-less work (E3): receipt absent but commits exist in ROOT since the step started (record HEAD before
   launch; `git rev-list <head0>..HEAD`) -> verdict `WORK_NO_RECEIPT` with the commit list; still not PASS.
4. Measured caps (E4): packet `"cap": "auto"` -> cap = ceil(p90 of PASS/WORK_NO_RECEIPT spends in `res` and any
   `--history` results files * 1.25), floored at 600k, capped at `--step-max`; fewer than 3 samples -> refuse
   (`CAP_UNMEASURED`), never guess. Record `cap_source: auto|packet` per step.
5. Tests, both poles each, with mutants (copy the module, break the behaviour, import, assert red): split vs legacy
   cap; launch failure stops vs real-spend failure continues; WORK_NO_RECEIPT vs no-commit FAIL; auto cap from 3+
   samples vs CAP_UNMEASURED from 2.

## Receipt
`vault/programs/cognitive-economy/gen2/evidence/tranche/CE-T1f-receipt.md`: change table (E1-E4 -> function), the
V-DRIVER pass line (old + new count), each mutant killed, and the auto cap it computes over the T0+T1 results files
`CE-T0-results.json CE-T0bR-results.json` (in your tree) plus the E4 numbers above as a worked example. `COMMITS: <hash ...>`. Pathspec
commits only. Never push. Write the receipt FIRST (a stub with the COMMITS line you will amend in place), then
implement, so a cap hit cannot erase it.
