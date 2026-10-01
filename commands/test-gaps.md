---
name: test-gaps
description: Find the changed lines of a Python project that no test would notice breaking -- uncovered lines, and mutants that survive the tests that run them -- then write or strengthen tests until the ones that matter are killed. Spec vault/specs/test-gaps.md (Gap 3 v1).
---

# /test-gaps -- mutation-guided testing on the code you just changed

## What it does

Runs `tools/test_gaps.py` on the current project (Python + pytest). For every non-test `.py` line
changed since `--base` (default `HEAD`, plus untracked files) it reports:

- `UNCOVERED file:lines` -- no test executes them.
- `SURVIVED file:line <mutation> ran by: <tests>` -- a test runs the line, but breaking it
  (`<` -> `>=`, `and` -> `or`, `True` -> `False`, `n` -> `n+1`) fails nothing. The named tests are
  the ones to strengthen.

All of it runs in a temp copy; the project is never written to. Mutants re-run only the tests
coverage saw executing that line.

## Usage

```
/test-gaps                     # lines changed since HEAD
/test-gaps --base main         # lines changed since main
/test-gaps --files pkg/x.py    # every line of named files
```

Run:

```
python ~/.claude/skills/claude-power-pack/tools/test_gaps.py --repo . [--base <rev>] [--files ...]
```

## Then

1. For each `SURVIVED` row, add or tighten an assertion in one of the named tests so that the
   mutation would fail it. Assert the value, not a bound: a survivor usually means the test checks
   `>= 0` where the code computes `5`.
2. For each `UNCOVERED` range, write a test that reaches it, or say why it is unreachable.
3. Re-run until the survivors you care about are gone. Not every survivor is a bug (an equivalent
   mutant cannot be killed); say which ones you are leaving and why.

## Verdicts

`MEASURED` (exit 0) · `NO_CHANGES` (exit 0) · `UNMEASURABLE` (exit 2): the clean suite is red in
the copy, pytest-cov is missing from the project's Python, or the project moved during the run.
An UNMEASURABLE run proves nothing either way.

## Limits (v1)

Python and pytest only. A sampled run (`sampled N of M`) is not exhaustive. Killing a mutant shows
a test is sensitive to the line, not that its expected value is right.
