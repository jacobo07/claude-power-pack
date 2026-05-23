# Plan: Code Review Skill (PP Quality Triangle Closer)

Sealed: 2026-05-23.
Spec: `vault/specs/code-review-skill.md`.
Sister: `vault/plans/auto-testing-skill-2026-05-23.md`,
`vault/plans/arch-decision-skill-2026-05-23.md`.

## Scope

5 components / 15 micro-commits / 10 V-tests / approximately 800 LOC.
No new hook (extends `auto_test.py --gate` script). Re-uses
`vault/.arch-index/` for DEEP-mode lesson citations.

## Sequencing graph

```
P1 spec ----+
            v
P2 plan --> P3 code_reviewer.py (FAST core: diff parser, doctrine,
                                  security, complexity)
                                  |
                                  v
                          P4 external linter integration (ruff/eslint/mix)
                                  |
                +-----------------+-----------------+
                v                 v                 v
        P5 V-BLOCK x2     P6 V-WARN x3      P7 V-PASS + V-SKIP-MVN
                                  |                 |
                                  v                 v
                          P8 V-TIMING (10 FAST runs)
                                  |
                                  v
P9 auto_test.py --gate extension (concurrent.futures, combined verdict)
                                  |
                                  v
                          P10 empirical: synthetic git commit -> verdict=block
                                  |
                                  v
P11 commands/code-review.md (DEEP mode + report)
                                  |
                                  v
                          P12 V-DEEP empirical
                                  |
                                  v
P13 closed-loop (patterns.jsonl + UKDL-CR-NN rows)
                                  |
                                  v
                          P14 V-CLOSED-LOOP
                                  |
                                  v
P15 apex section + session_lessons entry + verify_spp + verify_full_install + push
```

## Plan (clickable, micro-commit per paso)

- [x] **P1** -- Write spec `vault/specs/code-review-skill.md`.
      Done-gate: 15 sections, contract for STDIN + verdict shapes + SKIP-honest.
      Micro-commit: `feat(code-review): spec for Code Review Axis (PP triangle)`

- [ ] **P2** -- Write this plan file.
      Done-gate: 15 pasos + V-block + Reality Contract.
      Micro-commit: `feat(code-review): plan + sequencing graph`

- [ ] **P3** -- `modules/code-review/code_reviewer.py` core (approx 400 LOC).
      Components:
      - Unified-diff parser (no external dep; handles `git diff --staged` shape + `+++ a/path` + hunk headers + leading `+`).
      - PP-doctrine detector (9 compiled regex patterns from session_lessons).
      - Security detector (AWS/JWT/OpenAI/Anthropic keys; password literals; eval/exec/shell=True).
      - Complexity heuristics (function length via regex per-language; nesting depth).
      - JSON output with `verdict`, `findings[]`, `summary`, `source_classes[]`, `timing_ms`, `timing_partial`.
      Done-gate: empty diff input returns `{"verdict":"pass","findings":[],"timing_ms":<1000}`. Imports clean.
      Micro-commit: `feat(code-review): code_reviewer.py FAST core (doctrine+security+complexity)`

- [ ] **P4** -- External linter dispatch (approx 150 LOC added).
      Per-language detection from project signals (`pyproject.toml` with `[tool.ruff]` → ruff; `tsconfig.json` + `node_modules/.bin/eslint` → eslint; `mix.exs` → mix; `pom.xml` without mvn → SKIP honest). Parallel sub-processes via `concurrent.futures`; 8 s per-language sub-budget. Results merged into `findings[]`.
      Done-gate: ruff invocation on a synthetic Python diff produces ≥1 finding when the file has a flagged rule; missing-tool case produces `{"category":"skip-tool","tool":"<name>","fix":"<install hint>"}` finding.
      Micro-commit: `feat(code-review): external linter dispatch (ruff/eslint/mix; SKIP-honest)`

- [ ] **P5** -- V-BLOCK-SECRET + V-BLOCK-EVAL.
      Synthetic diffs:
      - V-BLOCK-SECRET: line `+ AWS_KEY = "AKIAIOSFODNN7EXAMPLE"` → verdict=block, finding cites AWS pattern.
      - V-BLOCK-EVAL: line `+ result = eval(request.GET['expr'])` → verdict=block, finding cites eval-on-user-input.
      Done-gate: both return `verdict=block`; at least one finding per test with `severity=BLOCK`.
      Micro-commit: `test(code-review): V-BLOCK secret + eval`

- [ ] **P6** -- V-WARN-LENGTH + V-WARN-DOCTRINE-1/2.
      Synthetic diffs:
      - V-WARN-LENGTH: function added with 90 lines of body.
      - V-WARN-DOCTRINE-1: `execSync('python', ['script.py'])` in JS file.
      - V-WARN-DOCTRINE-2: `cd C:/repo && git status` in PowerShell file.
      Done-gate: all three return `verdict=warn`; doctrine findings cite the lesson source.
      Micro-commit: `test(code-review): V-WARN length + doctrine`

- [ ] **P7** -- V-PASS + V-SKIP-MVN.
      - V-PASS: synthetic clean diff with 1 helper function (10 lines) → verdict=pass.
      - V-SKIP-MVN: synthetic `.java` diff in a cwd with `pom.xml` but mvn NOT on PATH → finding `category=skip-tool tool=checkstyle`; verdict=pass (skip is not a fail).
      Done-gate: V-PASS verdict=pass with zero findings; V-SKIP-MVN verdict=pass with skip-tool finding.
      Micro-commit: `test(code-review): V-PASS + V-SKIP-MVN`

- [ ] **P8** -- V-TIMING.
      10 FAST runs on a real-shape diff (e.g. the current arch-check skill diff). Persist timings to `vault/reviews/_timings.json`.
      Done-gate: p05 < 2 s; p95 < 30 s.
      Micro-commit: `test(code-review): V-TIMING (p05=X p95=Y)`

- [ ] **P9** -- Extend `modules/auto-testing/auto_test.py --gate` (approx 80 LOC added).
      Inside the gate path:
      - If `CLAUDEPP_CODEREVIEW_DISABLED=1`: skip reviewer entirely.
      - Else: spawn `code_reviewer.py --fast` via `concurrent.futures.ThreadPoolExecutor` in parallel with the existing auto-test logic. Budget split: auto-test 22 s, reviewer 6 s.
      - Combine verdicts: BLOCK if either side BLOCKs; warn if reviewer WARNs without auto-test fail; pass if both pass.
      - Emit a SINGLE JSON object on stdout (auto-test-gate.js contract unchanged).
      Done-gate: synthetic git-commit-shape PreToolUse JSON piped to `auto-test-gate.js` produces exit 2 when the diff has a BLOCK pattern; exit 0 when clean.
      Micro-commit: `feat(code-review): auto_test.py --gate calls code_reviewer in parallel (no new hook)`

- [ ] **P10** -- Empirical: synthetic git commit triggers combined verdict.
      Stage a real-shape diff in a scratch repo: ONE deliberately-broken Python test (pytest fails) AND a hardcoded AWS key. Run `auto_test.py --gate --cwd <scratch>`.
      Done-gate: stdout JSON has `verdict=block` AND `source_classes=["auto-test","code-review"]`.
      Micro-commit: `test(code-review): combined gate empirical (block from both sides)`

- [ ] **P11** -- `commands/code-review.md` (approx 80 LOC of skill prompt).
      `/code-review [--staged | --branch X]` invokes `code_reviewer.py --deep` (60 s budget; allows LLM call to generate refactor suggestions). Reads top 3 vault lessons from `vault/.arch-index/` matching the diff entities. Writes 4-section report:
      1. Executive summary (≤100 words)
      2. Findings table (severity / file:line / message / suggested-fix)
      3. Top 3 refactor suggestions (LLM-generated code samples)
      4. Lessons cited (from arch-check index)
      Output path: `vault/reviews/[ts]_[slug].md`.
      Done-gate: command file registered; the skill body documents 7 explicit agent steps.
      Micro-commit: `feat(code-review): /code-review DEEP-mode report generator`

- [ ] **P12** -- V-DEEP empirical.
      Run `/code-review --staged` (manually executing the 7 protocol steps) on this PP repo with the current Code Review skill diff. Verify the report file exists with 4 sections, ≥1 lesson cited from arch-check index, no fabricated source paths.
      Done-gate: `vault/reviews/[ts]_code-review-skill-self.md` present, 4 sections, every cited path exists.
      Micro-commit: `test(code-review): V-DEEP empirical (self-review of this skill)`

- [ ] **P13** -- Closed-loop via patterns.jsonl + UKDL.
      Add `code_reviewer.py` write to `vault/reviews/patterns.jsonl` on DEEP-mode runs when verdict != PASS. UKDL hub gets `UKDL-CR-NN` row per DEEP review.
      Done-gate: a synthetic DEEP run on a WARN diff appends one row to `patterns.jsonl`; UKDL row visible in `ukdl-universal.md`.
      Micro-commit: `feat(code-review): closed-loop patterns.jsonl + UKDL-CR-NN rows`

- [ ] **P14** -- V-CLOSED-LOOP.
      Two DEEP runs on the same WARN category, second run should surface the first run's pattern as "in this codebase, this category is typically fixed as: [example]" in its summary section.
      Done-gate: second report cites the first fix; pattern category match verified empirically.
      Micro-commit: `test(code-review): V-CLOSED-LOOP cross-run pattern citation`

- [ ] **P15** -- Apex section + session_lessons + verifiers + push.
      - Append "Code Review Axis (sealed 2026-05-23)" section to `knowledge_vault/core/apex-completion-standard.md` (PP source + live mirror, sha256-identical).
      - Append a 2026-05-23 lesson row to `vault/knowledge_base/session_lessons.md` summarising iteration findings.
      - Append UKDL-CR-01..05 rows to `vault/knowledge_base/ukdl-universal.md`.
      - Run `python tools/verify_spp.py` exit 0; `python tools/verify_full_install.py` exit 0.
      - Commit snowball; push origin/main; REMOTE_DELTA=0.
      Done-gate: all of the above.
      Micro-commit: `docs(apex): Code Review Axis sealed (triangle complete)`

## V-block summary

| V-test | Input | Expected verdict | Latency floor |
|---|---|---|---|
| V-BLOCK-SECRET | diff with AWS_KEY literal | BLOCK + AWS pattern cited | < 30 s |
| V-BLOCK-EVAL | diff with `eval(<dynamic>)` | BLOCK + eval cited | < 30 s |
| V-WARN-LENGTH | diff adding 90-line function | WARN + length cited | < 30 s |
| V-WARN-DOCTRINE-1 | diff with `execSync('python')` | WARN + Stop-hook PATH lesson cited | < 30 s |
| V-WARN-DOCTRINE-2 | diff with `cd <dir> && git` in PS | WARN + no-cd-prefix lesson cited | < 30 s |
| V-PASS | clean diff (helper + import) | PASS, zero findings | < 5 s |
| V-SKIP-MVN | `.java` diff, no mvn on PATH | PASS + skip-tool finding | < 5 s |
| V-TIMING | 10 FAST runs | p05 < 2 s, p95 < 30 s | per-run |
| V-DEEP | `/code-review --staged` on self | 4-section report, ≥1 lesson cited | < 60 s |
| V-CLOSED-LOOP | 2 DEEP runs same category | second cites first via patterns.jsonl | per-run |

## Reality Contract

The merge to `main` only happens at P15 after both verifiers exit 0 and
all 10 V-tests have produced empirical artifacts. "Classified FAIL" is
still a FAIL.

The reviewer NEVER decides. It informs. The commit is the Owner's.

## Cross-references

- `vault/specs/code-review-skill.md` (parent spec)
- `vault/specs/auto-testing-gate.md` (sister axis spec; shared hook)
- `vault/specs/arch-decision-skill.md` (sister axis spec; shared index)
- `hooks/auto-test-gate.js` (existing hook; NOT modified by this plan)
- `modules/auto-testing/auto_test.py` (extended at P9)
- `vault/.arch-index/index.json` (re-used in DEEP mode)
