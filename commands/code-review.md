---
name: code-review
description: Code Review Skill (PP Quality Triangle Closer) -- before a PR or merge, audits staged/committed code for security, PP-doctrine violations, complexity, and style. Complements auto-testing (correction) and arch-check (design). Use for "review my staged diff", "audit before commit", "review this branch vs main", or any cross-cutting quality check. DEEP mode produces a 4-section report at vault/reviews/&lt;ts&gt;_&lt;slug&gt;.md with findings + refactor suggestions + lessons cited from the local vault. FAST mode auto-fires inside the auto-test gate on every git commit (combined verdict).
---

# /code-review -- PP Quality Triangle Closer

## What it does

`/code-review [--staged | --branch X]` invokes the code reviewer in
DEEP mode (60 s budget, allows LLM-mediated report). Produces a
4-section markdown report at `vault/reviews/[ts]_[slug].md`:

1. **Executive summary** -- verdict + top 3 findings + key tradeoffs.
2. **Findings table** -- severity / file:line / message / suggested-fix.
3. **Refactor suggestions** -- top 3 with code samples (LLM-generated).
4. **Lessons cited** -- prior session_lessons / sealed-standard
   sections matching the diff's entities (from `vault/.arch-index/`).

The FAST-mode engine that drives this skill ALSO runs automatically
inside the `auto-test-gate.js` PreToolUse hook on every `git commit`
(combined verdict). Without `/code-review`, BLOCK-level findings still
fire as commit-blocking. The slash command exists to produce the
durable artifact + Owner-readable narrative.

## Usage

```
/code-review --staged
/code-review --branch feat/something
/code-review --since HEAD~5
```

If no scope arg is given, defaults to `--staged`.

## Execution protocol (agent's responsibilities)

When this command is invoked, the agent MUST execute the following
eight steps in order. The report is NOT done until step 7 writes a
file and step 8 logs a UKDL-CR row.

### Step 1 -- Resolve diff text

Based on the scope arg:

- `--staged` -> `git diff --staged` (default if no arg).
- `--branch X` -> `git diff main...X` (three-dot to limit to X's commits).
- `--since X` -> `git diff X HEAD`.

Capture the diff into a local variable. If empty, report "No diff to
review" and exit step 1.

### Step 2 -- Run the FAST engine to get the verdict + findings

```
echo "[diff]" | python modules/code-review/code_reviewer.py --fast --cwd .
```

Parse the JSON. Capture: `verdict`, `findings[]`, `source_classes[]`,
`timing_ms`, `files_reviewed[]`. Do NOT re-implement the detection.

### Step 3 -- For DEEP mode, also call code_reviewer with --deep

```
echo "[diff]" | python modules/code-review/code_reviewer.py --deep --cwd .
```

The `--deep` mode adds (a) `patterns.jsonl` history matched by category
and (b) a `lesson_candidates[]` array sourced from `vault/.arch-index/`.
Capture these into the working context.

### Step 4 -- Read the lesson candidates

For each entry in `lesson_candidates[]`, READ the cited section /
file. Do NOT paraphrase what you have not read. The "Lessons cited"
section of the report must trace every claim to text actually read
at this step.

### Step 5 -- Generate refactor suggestions

For up to 3 of the top WARN/BLOCK findings, generate a concrete
refactor suggestion with a 5-15 line code sample showing the
before / after. Every code sample MUST be syntactically valid in the
target language and reflect real runnable code -- no symbolic
shorthand markers and no abbreviated function bodies.

### Step 6 -- Compose the report

Single markdown file with EXACTLY these four sections in this order.
Real values substituted for the bracketed labels.

```
# Code Review [YYYYMMDD-HHMMSS]: [scope-slug]

Date: [ISO date]
Verdict: [pass | warn | block]
Files reviewed: [count]
Timing (FAST): [ms]

## Executive summary

[Two short paragraphs. State the verdict, top 3 findings, and key
tradeoffs the Owner should weigh. Max 100 words.]

## Findings

| Severity | Category | File:Line | Message | Suggested fix |
|---|---|---|---|---|
| BLOCK | ... | ... | ... | ... |
| WARN | ... | ... | ... | ... |
| INFO | ... | ... | ... | ... |

(Append "None." if a severity tier has no rows.)

## Refactor suggestions

For each of the top 3 findings (by severity then proximity to changed
hot paths), include a Before / After code block.

### Suggestion 1: [category]

Before:
\`\`\`language
[real code from the diff -- read; do not paraphrase]
\`\`\`

After:
\`\`\`language
[real refactored code -- syntactically valid; runs in the project]
\`\`\`

[Why: 2-3 lines on the trade-off.]

(Repeat Suggestion 2 / 3 if there are enough findings to warrant. If
no findings warrant a refactor, write "None warranted at this
verdict level.")

## Lessons cited

For each lesson candidate from step 4 that genuinely informed the
review, cite the file path + section + a one-line takeaway. Every
cited path MUST exist on disk.

- `path/to/lesson.md:Section Name` -- one-line takeaway

(If no lessons cited: write "None cited.")
```

### Step 7 -- Write the report + side artefacts

- Slug: kebab-case from the top finding's `category` if any, else
  `scope-staged` / `scope-branch-X`. Cap at 60 chars.
- Filename: `vault/reviews/[YYYY-MM-DD-HHMMSS]_[slug].md`.
- Create the directory if missing.
- Write the file (UTF-8, no BOM).

### Step 8 -- Append to patterns.jsonl + UKDL

If verdict != PASS, append one row to
`vault/reviews/patterns.jsonl`:

```json
{"ts":"<ISO>","category":"<top-finding-category>","file":"<top-finding-file>","verdict":"<verdict>","review_path":"<report-path>","project_type":"<auto-detected>"}
```

Also propose (do NOT silently apply) a UKDL row for
`vault/knowledge_base/ukdl-universal.md`:

```
| UKDL-CR-NN | vault/reviews/<filename> | <verdict> -- <one-line summary> |
```

Print the proposed UKDL row + ADR path to the Owner. Owner accepts the
UKDL row by running the appender; the agent does NOT silently mutate
the UKDL hub (per Axis B of apex: READ + PROPOSE only).

## Reality Contract (binary)

- No source path cited in the report may name a file that does not exist.
- No "Lessons cited" row may reference a file that was not read in
  step 4.
- BLOCK findings stay BLOCK -- the agent must NOT downgrade them to
  WARN or INFO regardless of how minor they look. The reviewer's
  severity decisions are authoritative.
- The Owner's decision to ignore a finding is theirs; the report
  remains durable on disk for audit.

## Closed loop

Each run produces a row in `patterns.jsonl`. Future DEEP runs read the
last 30 days of rows and filter by `project_type` + `category`,
supplying the top 3 prior corrections to the LLM as
`"in this codebase, this category is typically fixed as: [example]"`.

The loop ONLY operates in DEEP mode. FAST mode (called by the gate)
never reads patterns.jsonl -- keeps the per-commit overhead low.

## Cross-references

- `vault/specs/code-review-skill.md` -- full spec.
- `vault/plans/code-review-skill-2026-05-23.md` -- implementation plan.
- `modules/code-review/code_reviewer.py` -- engine.
- `modules/auto-testing/auto_test.py` -- gate caller (no new hook).
- `vault/.arch-index/index.json` -- reused for lesson citation.
- `hooks/auto-test-gate.js` -- existing hook; the BLOCK->exit-2
  translation already happens there for verdict=fail.
