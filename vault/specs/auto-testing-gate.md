---
title: Auto-Testing Skill — PP Quality Gate (specification)
date: 2026-05-23
status: ACCEPTED — execution authorized 2026-05-23
branch: feat/rtk-compressor-fusion
plan: vault/plans/auto-testing-skill-2026-05-23.md
forbidden_runtimes: n8n (per feedback_no_n8n_ever)
budget_fast_gate_sec: 30
llm_call_budget_per_gate: 1
diff_scope: staged-only (git diff --cached)
---

# Auto-Testing Skill — PP Quality Gate

## 1. Purpose

A skill that detects the project type (Java / Python / Node / Mixed / Unknown)
from the current working directory, generates relevant tests for the
**staged** diff (`git diff --cached`), runs them inside a 30-second hard
wall-clock budget, and **blocks the commit** if any generated test fails.

The skill is invoked transparently by a PreToolUse hook that matches any
Bash or PowerShell `git commit` invocation. It is also runnable explicitly
via the `/auto-test` skill (deep mode, depth=2, edge cases, coverage).

Cross-project: empirically validated against four real repositories on
this host (see §2 of the plan for the PASO-0 floor table).

## 2. Reality contract (the hard floor)

A test exists on disk or it does not. `vault/test-results/` carries
real timestamps or it carries none. A commit blocked by the gate is
evidence; a commit allowed by the gate against passing tests is
evidence. Anything else is incomplete — not a feature, not a "should
work", not a future iteration. The gate must:

- generate real test code (callable, executable) — never an inert shell
  that only resembles a test;
- run real subprocess invocations of pytest / vitest / jest / mvn;
- write atomic vault artifacts via `.tmp+rename`;
- emit honest CEILING reasons when a project has no executable framework
  and ALLOW the commit anyway (a gate that blocks for reasons it cannot
  verify is worse than no gate).

## 3. Architecture

```
modules/auto-testing/
  detectors.py            # detect_project_type(cwd) → enum + reason
  llm_bridge.py           # call_llm(...) via claude.exe -p + STDIN
  auto_test.py            # orchestrator: detect → generate → run → report
  generators/python_gen.py
  generators/node_gen.py
  generators/java_gen.py
  vault_io.py             # atomic writers + JSONL index

hooks/auto-test-gate.js    # PreToolUse (Bash + PowerShell), matcher
                           # git\s+commit (excludes `git commit -h`)

commands/auto-test.md      # /auto-test deep mode

vault/test-results/        # gate output (committable .md)
vault/test-failures/       # closed-loop ledger
```

## 4. Project-type detection (detectors.py)

Ranked, first match wins:

1. `pom.xml`            → Java (Maven)
2. `build.gradle*`      → Java (Gradle)
3. `pyproject.toml` OR `setup.py` OR `setup.cfg` OR `requirements*.txt`
                        → Python
4. `package.json`       → Node (variant determined by presence of
                          `vitest`, `jest`, `mocha` in devDependencies
                          OR the package's `scripts.test` text)
5. None of the above    → Unknown (CEILING with reason
                          "no build manifest found at cwd or up 3
                          ancestors")

Multiple matches return `Mixed(types=[...])` and the gate generates
tests for the language whose extension matches the staged diff.

A framework binary missing on PATH (e.g. `mvn` not callable) is a
secondary CEILING: detected type is Java but `mvn -v` fails → returns
`Ceiling("java toolchain missing")`. The gate then ALLOWS the commit.

## 5. Diff scope

The fast gate reads only `git diff --cached` (staged-only). This
matches the actual content about to enter the commit and avoids
reacting to unstaged scratch files. Diffs larger than 8 KB return
`Ceiling("diff exceeds fast-gate bound; run /auto-test for deep
sweep")` and ALLOW the commit — the fast gate cannot honestly
evaluate a diff that big in 30 seconds.

## 6. LLM bridge (llm_bridge.py)

Subprocess-invocation of `claude.exe -p` with the user message passed
via STDIN (per the WinError 206 vaccine sealed
2026-05-23 in `vault/lessons/windows-argv-limit-stdin-fix.md`). The
system prompt rides in `--append-system-prompt` (small, fits argv).

Recursion guard: `CLAUDEPP_AUTOTEST_RUNNING=1` is set in the
subprocess env. The hook checks this sentinel as the first
statement of `main()` and exits 0 silently when the flag is set
— this prevents `claude.exe -p` from re-firing the gate from
inside its own Stop-hook chain (vaccine inherited from
`vault/lessons/stop-hook-subprocess-recursion.md`).

Per-call timeout: 25 seconds. On timeout, the runner returns
`Ceiling("LLM timeout")` and ALLOWS the commit.

## 7. Generators

Each generator reads up to 3 existing test files from the project to
infer style (assertion library, import path, naming convention) and
emits one happy-path test for each function modified in the staged
diff. The fast gate's prompt asks for ONE test (smallest unit that
demonstrates the function is callable and returns a non-error result
under typical input). Deep mode asks for HAPPY + EDGE (null / empty /
boundary) + REGRESSION (last failure for this project, if any).

The output file is written to:

  `<project>/tests/auto-generated/<ts>_<slug>.test.<ext>`

This path is added to the project's `.gitignore` by D3's consolidator
(when first installed). Manual promotion to a permanent test is a
deliberate Owner step.

## 8. Runner (auto_test.py + run_tests)

| Project type | Command                                     | Cwd          |
|--------------|---------------------------------------------|--------------|
| Python       | `python -m pytest <file> -v --no-header`    | project root |
| Node (vitest)| `npx vitest run <file> --no-coverage`       | project root |
| Node (jest)  | `npx jest <file> --no-coverage`             | project root |
| Java (Maven) | `mvn test -pl <module> -Dtest=<Class>`      | project root |
| Java (Gradle)| `gradle test --tests <Class>`               | project root |

Subprocess hard-kill at 30 seconds. TIMEOUT verdict is distinct from
FAIL — TIMEOUT returns WARN (commit proceeds, log entry written).
FAIL returns BLOCK (exit 2 from the hook, commit aborted, reason
visible).

## 9. Pre-commit gate hook (auto-test-gate.js)

- PreToolUse matcher: `^(?:git|.*\\\\git\\.exe)\\s+commit(?!\\s*-h)`
- Reads stdin JSON from the harness, extracts `tool_input.command`.
- Resolves repo root via `git rev-parse --show-toplevel`.
- Calls `python modules/auto-testing/auto_test.py --gate --cwd <root>`.
- Exit 2 + reason on FAIL; exit 0 on PASS, CEILING, TIMEOUT, or any
  internal error (fail-OPEN: a broken gate must never deny commits).
- Total budget: 30 seconds. At 28 seconds the hook prints a WARN-
  TIMEOUT line and exits 0 even if the child has not returned.

## 10. Vault IO (vault_io.py)

- Atomic write: write to `<path>.tmp.<pid>` then `os.replace` to
  final path.
- `index.json` is append-only JSON-lines (each line is one JSON
  object). Concurrent writes serialize via per-file `.lock` mkdir
  semantics (sister to the deep-research lock pattern).
- Logs over 100 KB rotate to `<name>.1.log`; keep last 3 rotations.

## 11. Closed-loop learning

Each FAIL writes one row to
  `vault/test-failures/<project>/index.json`
  `vault/test-failures/<project>/<ts>_<slug>.md`

with: project, file changed, generated test text, failure output,
plus a "Do not regenerate this pattern" line. On the next
generation, the generator reads the last 20 entries for the same
project and computes a token-Jaccard similarity against the current
diff; if ≥0.30, the prompt is augmented with "AVOID this prior
failure pattern" + the offending test text.

## 12. DONE-gate (binary, no classifications)

The skill is DONE when, on this host, with no manual proxy:

1. A real `git commit` in the PP repo on a deliberately-broken
   staged .py file is BLOCKED with a visible reason and a vault
   artifact recording the failure.
2. A real `git commit` in the PP repo on a passing staged .py file
   ALLOWS the commit and writes a vault artifact recording the pass.
3. A real `git commit` in the KobiCraft cwd on a staged .java file
   returns CEILING("no build system") and ALLOWS the commit, with a
   warn-line in the auto-spawn log.
4. A real `git commit` in the InfinityOps/UI cwd on a staged .ts
   file returns SOFT-CEILING("no test script in package.json") and
   ALLOWS the commit, with a warn-line in the log.
5. 10 consecutive gate runs measured: 95th-pct ≤30s wall-clock; 5th-
   pct ≤5s (empty diff fast path).

There is no "doctrine-by-design" or "budget-tight" classification.
A row that fails any of the above is a defect, not a category.
(Sister rule to `feedback_no_classified_fails_at_done_gate`.)

## 13. Opt-out

Set `CLAUDEPP_AUTOTEST_DISABLE=1` in the env. The hook then logs a
single line to `vault/test-results/.auto-spawned.log` recording the
would-have-fired pattern and exits 0 immediately. Same posture as the
deep-research opt-out.

## 14. Mirror-Sync-Direction

The hook source of truth is `claude-power-pack/hooks/auto-test-gate.js`.
The installer's `register-auto-test-gate` consolidator prints a
PowerShell paste-block; the Owner pastes to register, never the
installer writing into `~/.claude/hooks/` directly. (Per
`feedback_mirror_sync_direction_and_hooks_dir_deny`.)

## 15. Cross-references

- Plan: `vault/plans/auto-testing-skill-2026-05-23.md`
- Sister axes already sealed: Research (deep-research), Concurrency
  (Intent-Lock), Async-Audit (oneshot-architect-auditor)
- Apex completion standard will gain a "Testing Gate Axis" section
  at POST-1.
