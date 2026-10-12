# E -- Long rollover canary (/clear + policy recycle), GEX44 plane (2026-10-12)

Owner direction: measure the rollover path (`/clear` rotation), not `/compact`. Same plane and fixture as D (Linux,
2.1.296 Bun/JSC, isolated config, stub API, 20 KB Bash result per turn, zero provider tokens). Clone at 6f886d2d
(= 410f3495, receipts report `private_mb: null` off Windows). Hook in observe mode; the driver obeys its receipt.
150 turns, `/clear` every 10. Raw rows: GEX44 `~/prr-bench/runs/rollover-{long,nowrap}.{jsonl,receipts.jsonl}`.

## Two runs, one variable
| run | parent of claude | hook decision after each /clear | processes | epochs |
|---|---|---|---|---|
| rollover-long | `kclaude-bench` (argv0, as in D) | RECYCLE x14 at turns 11, 21 ... 141 | 15 | 15 |
| rollover-nowrap | plain python driver | KEEP x140, reason `no kclaude resume loop` | 1 | 1 |

The control is the same /clear cadence with the restart withheld by the hook's own wrapper check, so it is also a
drive of the KEEP branch on a real process: with no resume loop to relaunch into, the hook does not recycle.

## Memory (RssAnon MB, main process; tree_n = 1)
| run | t1 | t50 | t100 | t140 | HWM t150 | slope (all samples) |
|---|---|---|---|---|---|---|
| rollover-long | 110 | 142 | 142 | 143 | 324 | 9.9 MB/100 turns |
| rollover-nowrap | 113 | 183 | 202 | 224 | 377 | **53.3 MB/100 turns** |

- **Epoch start after each resume (rollover-long, n=14): 123, 123, 124, 123, 123, 123, 123, 124, 123, 123, 123, 123,
  124, 124. Drift +0.04 MB/epoch.** The rollover path has no measurable generation-over-generation growth.
- /clear alone does not return memory: the control grows ~53 MB per 100 turns in one process. The recycle is what
  bounds it.
- Resume 0.35-0.38 s every time; one sid across all 15 processes; 14 MARK + 14 RECYCLE receipts, zero null receipts,
  no loop (every resumed process says KEEP until its own boundary).
- The rollover-long slope (9.9) mixes in-epoch growth (110 -> ~142 within ten turns) with the last sample (161 at
  t150, inside epoch 15 with no recycle after it); the epoch-start series is the generational answer.

## What this settles and what it does not
- Settles D28 unit 2 for the rollover path: D's +4.5 MB/epoch was a compact-path, n=3 reading. Compact drift stays
  unmeasured beyond n=3 and is no longer on the Owner's path.
- Not a Windows result, and the act path (`CPP_PRR_RECYCLE=act` -> `restart-claude.ps1`) is still unexercised.

## Instrument defects found running this
- With `exec -a kclaude-bench`, `sys.executable` is `""`, so the driver's default hook command had no interpreter and
  the hook never ran (an aborted run, kept as `rollover-long-aborted.*`, 109/109 null receipts). `longrun.py` now
  refuses that case (`default_hook_cmd`, tested); pass `--hook-cmd` with an absolute python.
- `bash -c "exec -a ... ; trailer"` never runs the trailer (exec replaces the shell): the stub had to be stopped by
  hand and t1 taken from the output file's mtime.
