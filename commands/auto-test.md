---
name: auto-test
description: Auto-Testing Skill — PP Quality Gate. Detects the project type (Python/Node/Java/Mixed/Unknown) of the current cwd, generates relevant tests for the staged diff via claude.exe, runs them, and reports a verdict. Two activation modes — automatic (PreToolUse hook intercepts every `git commit` invocation, fast 30 s budget, 1 LLM call) and manual deep mode (`/auto-test`, depth=2, edge cases, no hard budget cap). Output lands in vault/test-results/.
---

# /auto-test — Auto-Testing Quality Gate (deep mode)

## What it does

Generates relevant tests for the **staged** diff in the current
working directory, runs them with the project's framework
(pytest / vitest / jest / mvn / gradle), and reports the verdict
to stdout + `vault/test-results/`.

The same module is also invoked transparently by the PreToolUse hook
on every `git commit` — fast mode, 30 s budget, 1 LLM call. The
`/auto-test` skill is the manual **deep mode**: more tests, edge
cases, longer budget, no commit-side coupling.

## Args

| Arg | Default | Meaning |
|---|---|---|
| `--cwd PATH` | `.` | Project working directory |
| `--mode` | `deep` | `fast` or `deep` — deep generates more tests with edge cases |
| `--depth N` | `2` | 1 = happy path only; 2 = happy + 1 edge; 3 = happy + 2 edges |
| `--budget SEC` | `120` | Wall-clock cap in seconds (deep mode) |
| `--diff PATH` | (staged) | Read diff from file instead of `git diff --cached` |
| `--gate` | off | Machine-readable JSON output (matches hook contract) |

## Output

For every run that reaches the test runner:

1. **`vault/test-results/<ts>_<verdict>_<slug>.md`** — verdict report
   with frontmatter (ts, project, verdict, reason) + test output.
2. **`vault/test-results/.auto-spawned.log`** — newline-delimited
   JSON, one row per gate fire (rotated above 100 KB).
3. On `verdict=fail`:
   **`vault/test-failures/<project>/<ts>_<slug>.md`** + `index.json`
   row — the closed-loop ledger consumed by future runs to build the
   AVOID clause (F1).

## Activation

**Manual (deep mode)**: type `/auto-test` in any pane. Reads the
current cwd's staged diff and produces a multi-test verdict.

**Automatic (gate mode)**: the PreToolUse hook
`hooks/auto-test-gate.js` intercepts every `git commit` invocation.
On verdict=fail it exits 2 and the commit is BLOCKED with a visible
reason. On any other verdict (pass / ceiling / timeout / skip) it
exits 0 and the commit proceeds.

## Verdicts (binary, no classifications)

| Verdict | Hook exit | Meaning |
|---|---|---|
| `pass`    | 0 | Generated test ran + passed |
| `fail`    | 2 | Generated test ran + failed -> commit BLOCKED |
| `ceiling` | 0 | Project has no executable test framework, OR the LLM could not generate a real test, OR the diff exceeds 8 KB |
| `timeout` | 0 | Hook-side 28 s budget guard fired, or test runner exceeded its budget |
| `skip`    | 0 | No staged diff, opt-out, or recursion guard fired |

The gate never blocks for reasons it cannot verify — a gate that
blocks on ceiling would be worse than no gate.

## Constraints

- **30 s fast-gate budget**: PreToolUse must return in <30 s
  total, including LLM + test runner. The hook-side timer kills
  the child at 28 s with WARN-TIMEOUT.
- **1 LLM call per fast-gate run**: budget allows ~17-30 s for
  the call empirically; one is the limit.
- **Generator output is real test code**: must contain the
  required idioms (`def test_` + `assert` for Python;
  `describe + it + expect` for Node; `@Test + assertEquals` for
  Java). Missing any -> ok=False -> ceiling.
- **CEILING-honest for Java**: the KobiCraft repo on this
  development machine has 136 .java files and zero pom.xml /
  build.gradle. The gate returns CEILING and ALLOWS the commit.
  Generating a JUnit class that could not be executed would be
  theater, not testing.

## Opt-out

| Var | Effect |
|---|---|
| `CLAUDEPP_AUTOTEST_DISABLE`        | `1` to skip the PreToolUse gate entirely |
| `CLAUDEPP_AUTOTEST_RUNNING`        | `1` is set by the runner when spawning claude.exe; the hook respects it and exits 0 silently. Sister vaccine to the deep-research recursion guard. |
| `CLAUDEPP_AUTOTEST_FAKE_SLEEP_SEC` | `N` to sleep N s before any real work (used by D2 done-gate to prove the 28 s budget guard kills slow runners). |
| `CLAUDEPP_PY_EXE`                  | Override the python executable used by the hook |

## Activation step (Owner-pasted, Mirror-Sync-Direction)

```powershell
python ~\.claude\skills\claude-power-pack\tools\settings_merger.py register-auto-test-gate
```

Idempotent. Reuses the existing `settings_merger.py` pattern (also
used by `register-mark-live-session`, `register-deep-research`,
`register-session-safety`).

## Examples

```
/auto-test                  # deep run on cwd's staged diff
/auto-test --mode fast      # equivalent to the gate run
/auto-test --depth 3        # 3 tests: happy + 2 edge cases
/auto-test --diff /tmp/d    # use a saved diff file
```

## Empirical verification (V1 + V2, 2026-05-23)

- A1 detector: 5/5 cwds correctly classified (KobiCraft->ceiling,
  InfinityOps/UI->node_vitest, TUA-X->python, PP->python by
  convention, TEMP->unknown).
- A2 LLM bridge: HELLO returns in 16.1 s, recursion-guard env
  propagates correctly.
- B1 Python generator: real pytest scaffold in 15.4 s on a 30-line
  calc.py diff (`def test_add(); assert calc.add(2,3)==5`).
- B2 Node generator: real vitest scaffold in 20.2 s with
  `describe + it + expect` for all 3 TS functions; framework
  correctly inferred from InfinityOps UI deps.
- B3 Java generator: KobiCraft -> CEILING; synthetic Maven ->
  `@Test assertEquals(5, calculator.add(2,3))` in 16.1 s.
- C1 runner: 5 s pytest pass + infinite-loop killed at exactly 5 s
  timeout.
- D1 hook: 9/9 positive + 9/9 negative regex matrix; integration
  150 ms on no-diff cwd (verdict=skip).
- D2 budget guard: 35 s fake-sleep killed at exactly 28 s,
  verdict=timeout, exit 0.

## Cross-references

- Spec: `vault/specs/auto-testing-gate.md`
- Plan: `vault/plans/auto-testing-skill-2026-05-23.md`
- Module: `modules/auto-testing/auto_test.py`
- Generators: `modules/auto-testing/generators/{python,node,java}_gen.py`
- Hook: `hooks/auto-test-gate.js`
- Vault IO: `modules/auto-testing/vault_io.py`
- Consolidator: `tools/settings_merger.py register-auto-test-gate`
- Sister axes: Research (`cpp-deep-research`),
  Session-Safety (`SESSION_SAFETY_CONTRACT.md`),
  Concurrency (Intent-Lock).
