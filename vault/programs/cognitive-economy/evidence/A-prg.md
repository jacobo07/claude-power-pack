# [A] Product reality: the baseline gate run from a fresh process

Pillar [A] baseline cognitive economics. Denominators: `anchor` (exact) and `D-W7` (within 0.5 %), both read
from the ledger's frozen object by the gate, never copied into it.

Each run below is a fresh `python.exe` process started from a PowerShell prompt in the campaign worktree,
2026-10-03 ~16:15 +02:00.

## Green (expected values untouched)

command: `python vault/programs/cognitive-economy/gates/gate_baseline.py` -> exit 0

```
  ok   anchor.calls expected 23925 observed 23925 exact
  ok   anchor.cache_read expected 6230548450 observed 6230548450 exact
  ok   anchor.subagent_calls expected 9893 observed 9893 exact
  ok   D-W7.calls expected 75969 observed 75969 drift 0.0000% (limit 0.5%)
  ok   D-W7.subagent_calls expected 27497 observed 27497 drift 0.0000% (limit 0.5%)
  ok   D-W7.input expected 268014 observed 268014 drift 0.0000% (limit 0.5%)
  ok   D-W7.cache_write expected 421893705 observed 421893705 drift 0.0000% (limit 0.5%)
  ok   D-W7.cache_read expected 21968212607 observed 21968212607 drift 0.0000% (limit 0.5%)
  ok   D-W7.output expected 56845008 observed 56845008 drift 0.0000% (limit 0.5%)
GATE_BASELINE=PASS failures=0
```

## Red drill (two expected values perturbed)

command: `python vault/programs/cognitive-economy/gates/gate_baseline.py --perturb anchor.calls=23926 --perturb D-W7.cache_read=21000000000` -> exit 1

```
  perturbed anchor.calls expected -> 23926
  perturbed D-W7.cache_read expected -> 21000000000
  FAIL anchor.calls expected 23926 observed 23925 exact
  ok   anchor.cache_read expected 6230548450 observed 6230548450 exact
  ok   anchor.subagent_calls expected 9893 observed 9893 exact
  ok   D-W7.calls expected 75969 observed 75969 drift 0.0000% (limit 0.5%)
  ok   D-W7.subagent_calls expected 27497 observed 27497 drift 0.0000% (limit 0.5%)
  ok   D-W7.input expected 268014 observed 268014 drift 0.0000% (limit 0.5%)
  ok   D-W7.cache_write expected 421893705 observed 421893705 drift 0.0000% (limit 0.5%)
  FAIL D-W7.cache_read expected 21000000000 observed 21968212607 drift 4.6105% (limit 0.5%)
  ok   D-W7.output expected 56845008 observed 56845008 drift 0.0000% (limit 0.5%)
GATE_BASELINE=FAIL failures=2
  failed: anchor.calls
  failed: D-W7.cache_read
```

Each perturbation was killed by its own line; the untouched figures stayed ok.

## Tolerance boundary control

command: `python vault/programs/cognitive-economy/gates/gate_baseline.py --perturb D-W7.calls=76197` -> exit 0

```
  ok   D-W7.calls expected 76197 observed 75969 drift 0.2992% (limit 0.5%)
GATE_BASELINE=PASS failures=0
```

A drift inside 0.5 % stays green, so the tolerant branch is a tolerance, not a disguised exact match.

## What this does not prove

The gate proves the index still reproduces the frozen BEFORE snapshot. The AFTER snapshot (same command, a window
after the campaign) is taken in phase 7 and reported beside this one, never folded into it.
