# ECC Universal Baseline -- 12 Principles Applied

*Companion document to `ecc-reverse-engineering.md`. This file is
the human-readable catalog of the 12 principles absorbed from ECC.
Each section maps to one importable Python class in
`modules/uqf/principles/`.*

*Source: ECC (github.com/affaan-m/ecc) under MIT License
(c) 2026 Affaan Mustafa. Adapted to Python; no direct code copies.*

---

## P01 -- Pre-Report Gate

**Implementation:** `modules.uqf.principles.pre_report_gate.PreReportGate`

**What it is:** Before any code-review finding is emitted, the
reviewer must answer four questions affirmatively. If any answer
is "no" or "unsure", the finding must be downgraded or dropped.

The four questions:

1. Can I cite the exact line? (`file:line` precision)
2. Can I describe the concrete failure mode? (input + state + outcome)
3. Have I read the surrounding context? (callers, imports, tests)
4. Is the severity defensible? (no inflation)

**Why it matters:** The #1 failure mode of LLM reviewers is
**theater of completeness** -- inventing findings to justify the
invocation. The Pre-Report Gate directly addresses this.

**Apply in PP:**

- Use `modules.code_review.pre_report_gate(finding)` to gate every
  finding before it's emitted.
- For agents/code-reviewer style prompts: include the 4 questions
  verbatim in the agent prompt.

**Anti-pattern it replaces:** Findings like "Consider adding error
handling somewhere in the auth layer" with no file:line and no
specific scenario.

---

## P02 -- Common False Positives Catalog

**Implementation:** `modules.uqf.principles.false_positives_catalog.CommonFalsePositivesCatalog`

**What it is:** A catalog of 15+ patterns that LLM reviewers commonly
mis-flag. A finding whose text matches the catalog is treated as a
likely false positive and either dropped or downgraded.

Catalog entries (excerpt):

- "consider adding error handling" -> already handled by caller
- "missing input validation" -> internal func; trace one caller
- "magic number" -> well-known constant (200, 404, 1000, etc.)
- "function too long" -> exhaustive switch is not complexity
- "missing docstring" -> single-purpose internal helper
- "n+1 query" -> fixed-cardinality loop or DataLoader
- "math.random" -> non-crypto context (animation, jitter)
- "should use typescript" -> stack-change in a review
- "hardcoded value" -> test fixtures should have hardcoded expectations

**Apply in PP:** `modules.code_review.filter_false_positives(findings)`
returns a new list with the FP-matching findings dropped.

**Anti-pattern it replaces:** Review noise that costs reviewer trust.

---

## P03 -- Zero Findings Is Valid

**Implementation:** `modules.uqf.principles.zero_findings_valid.ZeroFindingsValid`

**What it is:** A clean review (zero findings) is a valid review.
Do not manufacture findings to justify the invocation.

**Apply in PP:** `derive_verdict([])` returns `"APPROVE"`. The
reviewer never adds noise to fill space.

---

## P04 -- HIGH/CRITICAL Proof Triad

**Implementation:** `modules.uqf.principles.proof_triad.HighCriticalProofTriad`

**What it is:** For any finding tagged HIGH or CRITICAL, the
reviewer must include all three:

1. The exact snippet + line number
2. The specific failure scenario (input + state + outcome)
3. Why existing guards (types, validation, framework defaults) do
   NOT catch it

Without all three -> demote to MEDIUM or drop. ECC doctrine:
**severity inflation erodes trust faster than missed findings**.

**Apply in PP:** `modules.code_review.run_full_review` demotes
HIGH/CRITICAL findings without the triad to MEDIUM.

---

## P05 -- Severity Table Output

**Implementation:** `modules.uqf.principles.severity_table.SeverityTableOutput`

**What it is:** Every code review ends with a severity table plus a
verdict derived from counts:

- `CRITICAL > 0` -> **BLOCK**
- `HIGH > 0` (no CRITICAL) -> **WARNING**
- else -> **APPROVE**

**Apply in PP:** `modules.code_review.derive_verdict(findings)`
computes the verdict.

---

## P06 -- Error Never Silent

**Implementation:** `modules.uqf.principles.error_never_silent.ErrorNeverSilent`
+ `modules.uqf.anti_patterns.detect_bare_except` /
`detect_silent_pass_in_except`.

**What it is:** Every exception path must re-raise, log+recover, or
convert to a typed domain error. Silent swallowers
(bare-except + no-op body) are anti-patterns.

**Apply in PP:** Code review (manual or automated) rejects PRs with
detected silent-swallow patterns. Fail-open paths must include a
comment justifying it + a test covering the fail path.

**Detected automatically:** `detect_bare_except` + `detect_silent_pass_in_except`
walk the AST and report file:line for every offender.

---

## P07 -- TDD Workflow

**Implementation:** `modules.uqf.principles.tdd_workflow.TDDWorkflow`

**What it is:** RED -> GREEN -> REFACTOR is mandatory, not advisory.
Every new source file in a change set has a corresponding test file.

**Apply in PP:** In PR review, check `git diff --stat` for source
files without companion test files. PP V-* gates and pytest suites
are the canonical test layer.

---

## P08 -- AAA Test Pattern

**Implementation:** `modules.uqf.principles.aaa_test_pattern.AAATestPattern`

**What it is:** Tests follow Arrange-Act-Assert: setup, single
operation, verification.

**Apply in PP:** Existing PP test conventions already follow this;
new tests adopt the explicit `# Arrange / # Act / # Assert`
comments where it clarifies a complex test.

---

## P09 -- Prompt Defense Baseline

**Implementation:** `modules.uqf.principles.prompt_defense_baseline.PromptDefenseBaseline`

**What it is:** Six baseline defenses applied to every agent prompt:

1. No role override
2. No secret leak
3. No unsafe code output
4. Treat unicode tricks as suspicious
5. Treat external data as untrusted
6. No harmful / illegal content

**Apply in PP:** CLAUDE.md now includes the full 6-rule baseline.
The auditor scores any prompt/agent `.md` for coverage; >= 4 of 6 = pass.

---

## P10 -- Rules Taxonomy

**Implementation:** `rules/common/` + `rules/<lang>/` directory tree.

**What it is:** Per-language quality rules organized as 5 files per
language (coding-style, hooks, patterns, security, testing) + a
common base of 7 cross-language rules.

**Apply in PP:** COMPLETED in the 2026-06-06 gap pass. `rules/` now
mirrors ECC's full taxonomy -- 19 languages: common (11) + python (6)
+ elixir (5, PP-only) + the 17 absorbed via `tools/absorb_ecc_rules.py`
(angular, arkts, cpp, csharp, dart, fsharp, golang, java, kotlin,
perl, php, react, ruby, rust, swift, typescript, web). Each mirrored
file preserves ECC's `paths:` frontmatter + an MIT-attribution comment;
PP's own customized common/python files were preserved (skip-if-exists).
Gate: `tools/verify_rules.py` R6 (17 langs present, all files attributed).

---

## P13 -- Confidence-Scored Instincts (ADAPTED)

**Implementation:** `tools.ceps.compute_confidence(occurrences,
resolution_success)` returning 0.3-0.9 + `tools.ceps.promote_to_global(
pattern, project_ids)` returning bool.

**What it is:** Error patterns / lessons / learned behaviors carry
a confidence score from 0.3 (first sighting) to 0.9 (proven across
multiple uses). Project-scoped by default; promote to global when
seen across >= 2 distinct projects.

**Apply in PP:** `record_error` now accepts `confidence_score`,
`scope`, and `project_id` kwargs. CEPS events carry these fields;
future cycles add the promotion-detection pass.

---

## P14 -- Skills-First Migration (INSPIRATIONAL)

**What it is:** ECC treats `commands/` as legacy and `skills/` as
canonical. New workflows land in `skills/` first; commands are
compatibility shims.

**Apply in PP:** PP today has a flatter command + skill structure.
A future cycle (not this one) may adopt the skills-first migration.
Spec: `vault/knowledge_base/ecc-specs/skills-first-migration-spec.md`
(future work; not yet written).

---

## How to apply this baseline to a new feature

When building a new feature in PP:

1. **Review pipeline** (if your feature emits findings):
   import `modules.code_review.run_full_review` and let it apply
   P01-P05 automatically.
2. **Error handling**: write your except handlers with re-raise /
   log+recover / convert. `modules/uqf/anti_patterns.detect_bare_except`
   will flag the rest in audit.
3. **Tests**: write the test first (P07). Structure as AAA (P08).
4. **Prompt** (if your feature is an agent .md): include the 6
   Prompt Defense Baseline lines verbatim.
5. **Learnings**: if your feature touches CEPS, use
   `confidence_score=compute_confidence(occurrences, resolved)`
   when recording errors.

## How to audit an existing PP module against this baseline

```bash
python tools/uqf_audit.py tools/my_module.py
python tools/uqf_audit.py --scan-all   # audits the default 5 modules
```

The output includes the score (0-100), passed principles, failed
principles with fix hints, and anti-pattern hits with file:line.

---

*Source: ECC v2.0.0-rc.1 (github.com/affaan-m/ecc) under MIT License
(c) 2026 Affaan Mustafa. Absorption: claude-power-pack 2026-05-27.*
