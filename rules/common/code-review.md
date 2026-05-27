# Code Review Standards (common, all languages)

## Purpose

Code review ensures quality, security, and maintainability before any
change is merged. This rule defines when and how the review runs in
the Power Pack.

## When to Review

MANDATORY triggers:

- After writing or modifying production code
- Before any commit to shared branches
- When security-sensitive code is changed (auth, secrets, RLS, sandbox)
- When architectural decisions are encoded (new module, new contract)
- Before merging pull requests

Pre-review requirements:

- Automated checks (CI/CD, V-tests, verify_spp) passing
- Merge conflicts resolved
- Branch up to date with origin/main

## Pre-Report Gate (4 questions, before ANY finding)

Before emitting a finding, the reviewer must answer affirmatively:

1. Can I cite the exact line? `file:line` precision.
2. Can I describe the concrete failure mode? Input + state + outcome.
3. Have I read the surrounding context? Callers, imports, tests.
4. Is the severity defensible? No inflation.

If any answer is "no" or "unsure" -> downgrade or drop the finding.

This gate is enforced by `modules.uqf.principles.pre_report_gate.PreReportGate`.

## Common False Positives -- Skip These

LLM reviewers commonly mis-flag these patterns. Skip unless you have
codebase-specific evidence:

- "Consider adding error handling" on a call whose error path is
  already covered by a caller or framework
- "Missing input validation" on internal functions whose callers
  already validate (trace at least one caller before flagging)
- "Magic number" for well-known constants (200, 404, 1000 ms, 60, 24,
  array index 0 / -1, HTTP status codes)
- "Function too long" for exhaustive switch, config object, or test
  table -- length is not complexity
- "Missing docstring" on single-purpose internal helpers whose name
  and signature are self-describing
- "Possible null dereference" when type-narrowed upstream
- "N+1 query" on fixed-cardinality loops or DataLoader-batched paths
- "Missing await" on fire-and-forget calls (logging, metrics, queues)
- "Should use TypeScript" or "Should have types" in a JS-only file --
  don't propose stack changes in a review
- "Hardcoded value" for test fixtures or example code
- Security theater: flagging `Math.random` in a non-crypto context;
  flagging `eval` in a plugin system that is explicitly a code-loading
  surface

When tempted to flag one of the above, ask: "Would a senior engineer
on this team actually change this in review?" If no -- skip.

Codified in `modules.uqf.principles.false_positives_catalog`.

## HIGH/CRITICAL Require Proof Triad

For any finding tagged HIGH or CRITICAL, include all three:

1. The exact snippet + line number
2. The specific failure scenario (input, state, outcome)
3. Why existing guards (types, validation, framework defaults) do
   NOT catch it

Without all three -- demote to MEDIUM or drop. ECC doctrine:
**severity inflation erodes trust faster than missed findings**.

Codified in `modules.uqf.principles.proof_triad`.

## Zero Findings Is Valid

A clean review is a valid review. Do NOT manufacture findings to
justify the invocation. If the diff is small, well-typed, tested,
and follows the project's patterns -> the correct output is a
summary with zero rows and verdict APPROVE.

Manufactured findings, filler nits, speculative "consider using X",
and hypothetical edge cases without a trigger are the primary failure
mode of LLM reviewers.

Codified in `modules.uqf.principles.zero_findings_valid`.

## Output Format (Severity Table)

Every review ends with:

```
## Review Summary

| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | 0     | pass   |
| HIGH     | 0     | pass   |
| MEDIUM   | 0     | info   |
| LOW      | 0     | note   |

Verdict: APPROVE
```

Verdict mapping (auto-derived from counts):

- `CRITICAL > 0` -> **BLOCK**
- `HIGH > 0` (no critical) -> **WARNING**
- otherwise -> **APPROVE**

Codified in `modules.uqf.principles.severity_table_output`.

## Approval Criteria

- **Approve**: No CRITICAL or HIGH issues (including zero findings)
- **Warning**: HIGH issues only (merge with caution)
- **Block**: CRITICAL issues present -- must fix before merge

Do not withhold approval to appear rigorous.

## Integration with Other Rules

- [testing.md](testing.md) -- 80% coverage + AAA pattern
- [security.md](security.md) -- security checklist
- [error-handling.md](error-handling.md) -- never silently swallow
- [git-workflow.md](git-workflow.md) -- commit format + push hygiene

---

*Portions adapted from ECC (github.com/affaan-m/ecc) under MIT License
(c) 2026 Affaan Mustafa.*
