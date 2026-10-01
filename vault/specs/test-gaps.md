---
covers: [test-gaps, test_gaps, gap-3, se-gap-3, d7, mutation-guided-testing, user-code-testing]
tier: T2
status: SPEC (nothing below is implemented unless marked LIVE)
owner_decisions: 2026-10-01 ("3": build gap 3 next)
---

# Test gaps on the user's code (Gap 3, v1)

Source: `vault/audits/se-capability-gaps-2026-09-30.md` row 3, backlog D7.

## Problem (verified 2026-10-01)

PP's mutation machinery only ever points at PP. `tools/mutation_probe.py` has a working AST
mutator, but it rewrites the **live** file in place, runs suites as `python <suite>` (PP's V-gate
style) with `cwd` fixed to the PP repo, and samples the whole module. Nothing measures whether the
tests of the project the agent is working in would notice a defect in the lines it just changed.
`hypothesis`, `coverage`, `pytest` and `pytest-cov` are installed and unused for user code.

The strongest evidence in the audit is for **mutation-guided test generation** (Meta: 73% of
generated tests accepted). The agent already writes tests; what it lacks is a precise statement of
which changed lines no test observes.

## Scope (v1)

`tools/test_gaps.py`: for a Python project tested with pytest, report two things about the lines
changed since a base revision:

1. **Uncovered changed lines.** No test executes them.
2. **Surviving mutants on covered changed lines.** A test executes the line, but breaking it
   (`<`->`>=`, `and`->`or`, `True`->`False`, `n`->`n+1`) fails no test. Each survivor names the
   tests that ran the line, so the agent knows which test to strengthen.

The mutator is imported from `tools/mutation_probe.py` unchanged (one engine, not two).

| capability | status |
|---|---|
| changed lines from `git diff -U0 <base>` plus untracked `.py` files | LIVE |
| coverage with per-test contexts (`pytest --cov --cov-context=test`) | LIVE |
| mutants restricted to changed and covered lines, each re-running only the tests that ran that line | LIVE |
| lines run inside a subprocess a test spawns (`coverage [run] patch = subprocess`), their mutants judged by the whole suite | LIVE |
| all work in an isolated copy; the project's own files hashed before and after | LIVE |
| property-based tests (hypothesis), fuzzing, flaky-test detection | ABSENT (not v1) |
| non-Python projects | ABSENT (not v1) |

Measured 2026-10-01 (coverage 7.13.4, pytest 9.0.3, pytest-cov): per-line contexts come back as
pytest node ids with a phase suffix, e.g. `tests/test_calc.py::test_low|run`; import-time
execution is the empty context `""`. Node ids are passed straight back to pytest.

## Behaviour contract

1. **Never touches the project.** The tree is copied to a temp dir (skipping `.git`, virtualenvs,
   `node_modules`, caches, build output) and everything runs there. The project's changed files
   are hashed before and after; a mismatch is reported as a harness failure.
2. **A failing baseline makes nothing measurable.** If the clean suite does not pass in the copy,
   the verdict is `UNMEASURABLE` with pytest's tail, and no mutant is judged: a red run would prove
   nothing about a mutant.
3. **Test files are not mutation targets.** Paths named `test_*.py`, `*_test.py`, or under a
   `tests/` directory are excluded from mutation and from the uncovered report.
4. **Outcomes, never collapsed:** a mutant is `KILLED` (pytest exit 1 or 2: a failure or a
   collection error the mutant caused), `SURVIVED` (exit 0), `TIMEOUT`, or `ERROR` (exit 3-5, or
   unparseable). Only KILLED and SURVIVED are verdicts.
5. **No stale bytecode.** `PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider` on every run, the
   same trap `mutation_probe.py` documents.
6. **Bounded.** `--max-mutants` (default 20, evenly sampled and reported as sampled when capped).
   The coverage baseline gets `--timeout` (default 600 s); each mutant run gets
   `max(120 s, 3 x measured baseline)`. A fixed 120 s baseline timed out on a real CLI project.
7. **Subprocesses are measured.** Coverage runs with `patch = subprocess` and the per-process data
   is combined before reading. A line that ran with no test context (in a child process, or at
   import) has no single test to credit, so its mutant is judged by the **whole suite** and
   reported as such, never skipped. Found on a real project (2026-10-01): its CLI tests drive
   `python -m pkg` in a subprocess, and without this every CLI line they exercise read UNCOVERED
   and produced no mutant at all.
8. **Exit codes:** 0 = measured (gaps or not), 2 = unmeasurable or harness failure. Gaps are
   information for the agent to act on, not a build break.

## Wiring

Slash command `commands/test-gaps.md` (`/test-gaps [--base <rev>]`): run the tool on the current
project, then write or strengthen tests for each survivor and uncovered line, and re-run until the
survivors that matter are killed.

## Acceptance

`python tools/test_test_gaps.py` exit 0 (V-TG-* gates) on a fixture project created in a temp dir:

- a changed line that no test runs is reported uncovered;
- `if x > hi` with a test asserting only `>= 0` leaves the `>`->`<=` mutant SURVIVED, naming the
  test that ran the line;
- the same fixture with a strong test kills it (control, so a tool that never reports a survivor
  cannot pass);
- a mutant on a line covered by one test re-runs only that test;
- a red baseline gives `UNMEASURABLE` and no mutant verdicts;
- test files are never mutated;
- the project's files are byte-identical after the run.

Mutation drill: with the per-line restriction removed, or the SURVIVED/KILLED mapping inverted,
the suite goes red.

## Evidence (2026-10-01)

- `python tools/test_test_gaps.py`: 14/14 locally (839 s, RAM-starved Windows host).
- GEX44 (Linux, throwaway venv `~/drills/tg-venv`, coverage 7.16.2): control 14/14; isolated drill
  6/6 KILLED (per-line restriction removed, kill/survive mapping corrupted, whole suite per
  mutant, mutant written to the project, subprocess patch removed, context-less lines skipped);
  source unchanged.
- Real project `gsd-long-smoke` worktree, **before** the subprocess fix: MEASURED in 115 s,
  2 changed files, 0 mutant candidates. Diagnosis: `test_reverse.py` only checks the import
  (true gap), and `test_cli.py` drives `python -m smoketext` in subprocesses (the blind spot that
  produced item 7 above).
- Real project **after** the fix: a laptop run was stopped by Claude Code for host memory pressure
  before printing anything; re-run on GEX44 (Owner: "on GEX44 now") with `--files
  smoketext/cli.py smoketext/reverse.py` (every line of both, no git history there), same tool
  bytes as dc7f781. MEASURED: uncovered `cli.py` shrank from
  `49,93,107-109,127,129-130,145-150` to `108`; 25 candidates, 13 sampled, **11 KILLED, 2
  SURVIVED**. Both survivors are genuine gaps, read against the source: `reverse.py:23`
  `or`->`and` (no test reverses spacing/enclosing/class-0 marks, the case the `or` exists for)
  and `reverse.py:66` `<`->`>=` (no test starts with a mark; line 67 uncovered agrees).

## Rollback

Delete the tool, its test and the command file. No state is persisted.
