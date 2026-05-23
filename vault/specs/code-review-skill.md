# Spec: Code Review Skill (PP Quality Triangle Closer)

Sealed: 2026-05-23.
Cross-references: `vault/specs/auto-testing-gate.md` (corrección axis),
`vault/specs/arch-decision-skill.md` (diseño axis).

## 1. Purpose

Close the third side of the PP quality triangle: code review for
calidad / seguridad / mantenibilidad before a commit lands on main.

The triangle:
- **Auto-Testing Gate**: does the code do what it should?
- **Arch-Check**: is the decision consistent with the vault?
- **Code Review** (this skill): is the code well-written, secure,
  maintainable?

No commit reaches main without passing all three.

## 2. Reality Contract

- BLOCK that does not block = the gate is decorative.
- BLOCK on clean code = the gate is an obstacle.
- SKIP-honest on projects without tooling = correct behaviour.

The line between BLOCK and WARN is **not subjective**:

- BLOCK = secrets hardcoded, dangerous eval/exec, SQL injection.
- WARN = function length, naming, nesting depth, missing error handling.
- INFO = style suggestions.

Owner is the final arbiter. The reviewer informs; the commit is the
Owner's decision.

## 3. Architecture

### 3.1 Components

| # | File | Role |
|---|---|---|
| C1 | `modules/code-review/code_reviewer.py` | Verdict engine: PP-doctrine + security + complexity + per-language linter dispatch. Both FAST and DEEP modes. |
| C2 | `modules/auto-testing/auto_test.py` (extension) | Already the gate runner. Extended to call `code_reviewer.py --fast` in parallel via `concurrent.futures`; combined verdict in the same JSON shape `auto-test-gate.js` already reads. NO new hook. |
| C3 | `commands/code-review.md` | Manual `/code-review [--staged \| --branch X]` skill; produces a 4-section report at `vault/reviews/[ts]_[slug].md`. |
| C4 | `vault/reviews/patterns.jsonl` | Append-only learning log; DEEP mode reads recent rows to surface prior fix patterns to the LLM. |
| C5 | `vault/.arch-index/index.json` (re-use) | Existing Arch-Check index. The DEEP-mode "Lessons cited" section consumes this — same closed-loop infrastructure. |

### 3.2 PP-doctrine patterns detected in FAST mode

Derived from `vault/knowledge_base/session_lessons.md` empirically-observed
incidents:

| Pattern | Source lesson | Severity |
|---|---|---|
| Bare `python` / `python3` in execSync/spawn/Popen first arg | 2026-05-14 Stop-hook PATH | WARN |
| Bare `git` in PowerShell native-call shape | 2026-05-21 PowerShell git PATH gap | WARN |
| `cd <path> && git ...` shell composition | feedback_no_cd_prefix_on_git | WARN |
| `read_text(encoding='utf-8')` (instead of `utf-8-sig`) | feedback_python_utf8_bom | WARN |
| `os.open(... os.O_WRONLY)` without `os.O_BINARY` | feedback_windows_text_mode_compounding | WARN |
| `fs.writeFileSync` on shared-state JSON without atomic_write | 2026-05-10 BL-0073 #2 | WARN |
| Stop hook returning `hookSpecificOutput` (only PreToolUse supports it) | 2026-05-14 Stop-hook schema | WARN |
| Hardcoded secrets: AWS key, JWT, password-literal, OpenAI key, Anthropic key | universal | **BLOCK** |
| `eval(...)` / `exec(...)` / `subprocess(... shell=True ...)` on dynamic input | universal | **BLOCK** |

The detector parses the diff's `+` lines (additions only — never blames
existing code) and matches against compiled regexes. Each match emits a
finding with file/line/snippet/severity/lesson-cited.

### 3.3 Per-language external linter dispatch (SKIP-honest)

| Project signal | Tool | Invocation | Fallback |
|---|---|---|---|
| `pyproject.toml` with `[tool.ruff]` | `ruff` | `ruff check --output-format=json --select E,F,W,B,S -` | SKIP with `"ruff not installed: pip install ruff"` |
| `tsconfig.json` + `node_modules/.bin/eslint` | `eslint` | `eslint --format json --stdin --stdin-filename <file>` per file | SKIP with `"eslint not installed in node_modules"` |
| `mix.exs` | `mix format --check-formatted` | as-is, scoped to staged files | SKIP with `"mix not in PATH"` |
| `pom.xml` (no `mvn` on PATH) | n/a | — | SKIP with `"mvn not in PATH; add maven to enable Java review"` |

External linters get an 8 s per-language sub-budget; over budget = partial
results + `timing_partial: true` flag. Never installs.

### 3.4 Complexity heuristics (custom, fast)

- Function length > 80 lines → WARN.
- Nesting depth > 5 (paren/brace counting for non-Python; AST `ast.NodeVisitor`
  for Python) → WARN.
- File added with 0 tests when an existing test directory is present → INFO.

## 4. Per-mode latency budgets

| Mode | Budget | Behaviour on overshoot |
|---|---|---|
| `--fast` (default; called by gate) | 30 s total. Internal: doctrine+security <1 s, complexity <2 s, external linters 8 s each parallelised. | Partial verdict; `timing_partial: true`; never BLOCKs from timeout alone. |
| `--deep` (manual via `/code-review`) | 60 s total (allows LLM-mediated report). | Report written with sections marked `[partial]` if LLM step times out. |

## 5. STDIN contract

`code_reviewer.py --fast` reads from STDIN. Three accepted shapes:

1. A unified diff (preferred; matches `git diff --staged` output).
2. A JSON object `{"diff": "<unified-diff>", "cwd": "<path>"}` (used by
   the auto_test.py extension to pass already-parsed diff).
3. Empty stdin + `--cwd <path>` arg → reviewer runs `git diff --staged`
   internally.

Output: JSON `{verdict, findings[], summary, source_classes[], timing_ms, timing_partial}`. Exit codes: 0 success (any verdict), 1 bad invocation, 2 reserved for the hook to translate BLOCK into commit-blocking exit.

## 6. Threshold of activation

This skill ALWAYS runs in FAST mode when the existing `auto_test.py --gate`
is invoked (which itself triggers only on `git commit` per the existing
`auto-test-gate.js`). No additional threshold layer needed.

DEEP mode is Owner-invoked via `/code-review`.

## 7. Verdict mapping (to existing auto-test-gate.js exit codes)

The hook script `auto-test-gate.js` already maps `verdict` from
`auto_test.py` stdout:

- `verdict=pass` → exit 0 (commit allowed)
- `verdict=fail` → exit 2 (commit BLOCKED) — auto-test failure
- `verdict=ceiling` / `timeout` / `skip` → exit 0 with log entry

This skill adds two combined-verdict values that map cleanly:

- `verdict=block` → exit 2 (BLOCKED — code-review BLOCK finding OR auto-test fail)
- `verdict=warn` → exit 0 (commit allowed) + WARN-line in `.auto-spawned.log`

Combined-verdict logic inside `auto_test.py --gate` after both
sub-verdicts complete:

```
if either side says block-equivalent (auto-test fail OR code-review BLOCK):
    verdict = "block"   (exit 2)
elif either side says warn (code-review WARN findings present):
    verdict = "warn"    (exit 0 + log)
elif both pass:
    verdict = "pass"
else (skip/ceiling on both):
    verdict = "skip"
```

## 8. Failure modes (fail-open)

| Failure | Behaviour |
|---|---|
| Reviewer crash | Gate falls back to auto-test-only verdict. Commit NOT blocked solely by reviewer crash. |
| Timeout > 30 s | Partial verdict (whatever finished). `timing_partial: true`. Never BLOCK from timeout. |
| Ruff/eslint missing | SKIP-honest with install hint. PP-doctrine + security checks still run. |
| Diff parse failure | SKIP entirely. Logged; commit not blocked. |
| Recursion guard hit | CLEAR exit immediately. |

Opt-out: `CLAUDEPP_CODEREVIEW_DISABLED=1` env. Recursion guard: `CLAUDEPP_CODEREVIEW_RUNNING=1`.

## 9. Closed loop

When Owner fixes a finding then commits → `vault/reviews/patterns.jsonl`
appended with:

```json
{"ts":"2026-...","category":"bare-python-execSync","file":"hooks/foo.js","diff_before":"+ execSync('python ...","diff_after":"+ execSync(getPythonCommand(), ['...","project_type":"node"}
```

`code_reviewer.py --deep` reads the last 30 days of patterns.jsonl,
filters by `project_type` matching the current cwd, and supplies the top
3 corrective examples to the LLM as `"in this codebase, this category is
typically fixed as: [example]"`. FAST mode never uses patterns.jsonl
(no LLM in FAST).

UKDL hub: each non-PASS DEEP review appends a UKDL-CR-NN row referencing
the report file.

## 10. Mirror-Sync-Direction

This skill ships PP-only files. The existing `auto-test-gate.js` hook is
NOT modified (zero new hook fanout per `vault/lessons/hook-fanout-systemic-cost.md`).
The `auto_test.py --gate` SCRIPT is extended; the JSON contract with the
hook stays identical (one verdict object on stdout).

## 11. Recursion guard

`CLAUDEPP_CODEREVIEW_RUNNING=1` set by the auto_test.py extension when
spawning code_reviewer.py. If the LLM in DEEP mode shells out to claude.exe
and that triggers a hook chain, the recursion guard short-circuits.
Sister to `CLAUDEPP_AUTOTEST_RUNNING`, `CLAUDEPP_ARCHCHECK_RUNNING`,
`CLAUDEPP_DEEPRESEARCH_RUNNING`.

## 12. DONE-gate (binary, no classifications)

A PP install is Apex-complete on the Code Review Axis iff:

1. `vault/specs/code-review-skill.md` (this file) and
   `vault/plans/code-review-skill-2026-05-23.md` exist.
2. `modules/code-review/code_reviewer.py` exists; `--fast` on a no-op
   diff returns valid JSON with `verdict=pass` and `timing_ms < 1000`.
3. `python modules/code-review/test_v_block.py` exits 0: all 7
   functional V-tests pass (V-BLOCK-SECRET, V-BLOCK-EVAL, V-WARN-LENGTH,
   V-WARN-DOCTRINE-1, V-WARN-DOCTRINE-2, V-PASS, V-SKIP-MVN);
   V-TIMING p05 < 2 s, p95 < 30 s over 10 FAST runs.
4. `auto_test.py --gate` empirical: a synthetic diff with both a
   test-breaking change AND a doctrine violation returns combined
   verdict `block` (auto-test-gate.js translates to exit 2).
5. `commands/code-review.md` registered (visible in available-skills
   list after `/restart`).
6. A real `/code-review --staged` produces a 4-section report at
   `vault/reviews/[ts]_[slug].md` with at least one lesson cited
   from `vault/.arch-index/`.
7. V-CLOSED-LOOP: a synthetic WARN-fix sequence writes a row to
   `vault/reviews/patterns.jsonl`; the next DEEP run on the same
   category mentions the prior fix.

Missing any of 1-7 = NOT Apex-complete on the Code Review Axis.

## 13. Opt-out

`CLAUDEPP_CODEREVIEW_DISABLED=1` disables only the reviewer path inside
`auto_test.py --gate`; auto-test runs normally. Honest, documented.

## 14. Cross-references

- `knowledge_vault/core/apex-completion-standard.md` (target axis seal)
- `vault/specs/auto-testing-gate.md` (sister axis spec)
- `vault/specs/arch-decision-skill.md` (sister axis spec; index re-used)
- `vault/lessons/hook-fanout-systemic-cost.md` (why no new hook)
- `vault/lessons/windows-argv-limit-stdin-fix.md` (STDIN vaccine)
- `hooks/auto-test-gate.js` (existing hook; NOT modified)
- `modules/auto-testing/auto_test.py` (extended in C2)

## 15. Future extensions (NOT in this cycle)

- Bytecode-less Java static analysis (BCEL parsing) when mvn is missing —
  out of scope; SKIP-honest is the contract for now.
- Per-project doctrine extensions via `<repo>/.code-review/doctrine.yml`
  — out of scope; PP-doctrine is the universal set.
- Auto-fix mode (`/code-review --fix`) — out of scope; the reviewer
  reports, never modifies code (per Reality Contract section 2).
- semgrep / detect-secrets integration when binaries become available
  — handled by the SKIP-honest path; no special code path required.

These are explicit scope cuts. Adding them later does not change the
DONE-gate above.
