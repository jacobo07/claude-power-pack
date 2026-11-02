---
status: APPROVED 2026-11-02 (Owner "y" on the W3 plan, GPF coordinator pane)
covers: [gpf, global-prefix-floor, resident-admission, resident-budget, floor-budget, w3, cr-33, cr-34, cr-35, cr-36]
owner: GPF (plan vault/plans/global-prefix-floor-2026-11-02.md, W3 + Gates)
---

# GPF W3 -- Resident Context Admission (absolute budgets for the resident doctrine)

## Problem (measured 2026-11-02)
`tools/floor_regression_gate.py --check` flags only a RISE against a committed reference. That reference
(`vault/programs/incremental-cognition/floor/reference.json`) was written 2026-10-05, before the GPF diet:
memory_global 39,809 chars, rules 63,625. The live session floor now is memory_global 7,871, rules 8,239
(sessions bcf0a0bc and 07f7d1bd, measured with `measure()`). So the doctrine can re-inflate by ~32K + ~55K chars
and the gate still reads WITHIN_BOUND: the diet's -6,444 tokens/call-1 is protected by nothing.

## Decision
1. A third mode, `--budget PATH`, in `floor_regression_gate.py`: ABSOLUTE char ceilings per layer, read from what
   the session actually loaded (the startup window), never from a hand-kept file list. A new resident file is
   counted the day it appears (PR-COVERAGE-BY-CONSTRUCTION-001).
2. A committed budget file per plane: `vault/programs/global-prefix-floor/resident_budget.json`
   (schema `resident-budget/1`). Raising a ceiling is a reviewable diff of that file; that IS the admission.
3. Refresh `reference.json` to a post-diet session (`--write-reference --replace`), so the existing 3 % rule
   bites at the new level too.
4. `vault/programs/ctx-rent-x/done_gate.py` gains CR-33..36, each read from an existing receipt.

## Contract: `--budget`
`floor_regression_gate.py --budget BUDGET.json (--transcript T | --project-dir D | --session SID | --probe) [--json]`

Budget file: `{"schema": "resident-budget/1", "plane": str, "install_home": str,
"budgets": [{"layer": str, "max_chars": int > 0, "cwd": str (optional), "basis": str}]}`.
A layer's measured value = the sum of `chars` of every component of that layer, all scopes.
An entry with `cwd` applies only when the transcript's cwd equals it (normalised); otherwise it is reported
`BUDGET_NA` and not enforced. An entry without `cwd` applies everywhere on that plane.

| condition | verdict | exit |
|---|---|---|
| budget file unreadable / wrong schema / bad entry | UNMEASURABLE budget_invalid | 2 |
| plane or install_home differ from the transcript's | UNMEASURABLE not_comparable | 2 |
| no entry applies to this transcript | UNMEASURABLE no_applicable_budget | 2 |
| an applicable layer has no component at all | UNMEASURABLE layer_absent:<layer> | 2 |
| window degraded (dispatcher abandoned SessionStart) | UNMEASURABLE window_degraded | 2 |
| any applicable layer > max_chars | OVER_BUDGET over_budget | 1 |
| every applicable layer <= max_chars | WITHIN_BUDGET within_budget | 0 |

Window health `unknown` does not downgrade a budget green: the budgeted layers are instruction files the harness
loads, not hook output, so an abandoned hub cannot shrink them. The health is still printed.

## done_gate rows (plan section Gates)
- CR-33 W0 floor decomposition record exists and names the CLAUDE.md chain and rules shares.
- CR-34 W1 delta: n=4/arm, spread < 1 %, delta > 0 (receipt `gpf-l2-laptop.json`).
- CR-35 quality non-inferior: 6/6 correct (receipt `gpf-l2-quality.json`).
- CR-36 budget pinned: the budget file validates AND `--budget` on the newest receipt session exits 0.
A missing or unreadable receipt is UNKNOWN, never PASS.

## Acceptance
- `tools/test_floor_regression_gate.py`: new V-FLOOR-BUDGET-* gates, each driven at both poles (within / over,
  boundary max == now green and max == now-1 red, absent layer exit 2, cwd-scoped entry NA, invalid file exit 2,
  no applicable entry exit 2), CLI and in-process. Whole suite green (was 71/71).
- `tools/test_done_gate.py` stays green with the new rows; each new row drilled PASS and not-PASS.
- Live: `--budget` on this session's transcript exits 0; the same file with a ceiling 1 char under the measured
  value exits 1.

## Never
- Never derive the measured value from files on disk: the session window is the truth of what was resident.
- Never let an unmeasured layer read as zero (absent is not zero).
- Never write the real `~/.claude` from a test.

## Rollback
Delete the `--budget` branch (one mode in `build_parser`, one function, the render branch), the budget file and
the CR-33..36 rows; restore `reference.json` from git. Nothing else consumes them.
