---
title: Predictive governance — defect pattern register and enforcement gap
date: 2026-08-10
tier: T3
status: STOP #1 — awaiting Owner decision
covers: [predictive_governance, defect_patterns, enforcement_gap, vacuity_gate, oracle_gate]
audit: vault/plans/memory-audit-2026-08-09.md
---

# Phase 0 — corpus mining

## Sources, and two that do not exist

| source cited | on this host | used |
|---|---|---|
| `/mnt/transcripts/` | absent (POSIX path) | 99 `.jsonl` transcripts in the project dir |
| `knowledge-vault/UKDL/universal-knowledge.md` | absent | `vault/knowledge_base/ukdl-universal.md` |
| `vault/audits/` | 104 markdown files | yes |
| corpora | `ukdl-universal.md` + `knowledge_vault/core/HARD-RULES.md` | yes |

## The measurement that reframes the brief

The brief asks which rules have text but no gate. Measured across both corpora,
with the rule set walked off disk rather than listed:

| class | count | meaning |
|---|---|---|
| ENFORCED | 34 | the id survives in executable text, comments stripped |
| MENTIONED_ONLY | 49 | named solely in a comment or docstring |
| PROSE_ONLY | 316 | no code names it at all |
| sealed total | 399 | |

**The instrument corrected itself mid-pass.** A first version counted "id appears
in a code file" and returned 83 enforced. Stripping comments and docstrings drops
that to 34: 49 of the 83 were prose inside a `.py` file. My own gate's docstring,
written yesterday, made `T-NEVER-GATE-ON-A-RATIO` read as enforced. That is
`T-PLAUSIBLE-BUT-WRONG-001` occurring inside the audit built to catalogue it.

**Direction of error, stated.** This still undercounts: a mechanism can enforce a
rule without naming it — `PR-COVERAGE-BY-CONSTRUCTION-001` is implemented in
`liveness` and `capability_runtime` yet scores MENTIONED_ONLY. So 34 is a LOWER
bound on enforcement and 316 an UPPER bound on unenforced. The ranking below does
not depend on the exact split.

## What the enforced set is made of

The 34 enforced rules are almost entirely OPERATIONAL: restart, RAM, kclaude,
Playwright, MCP health, secrets, hook drift. Every one is a failure you can watch
happen.

The EPISTEMIC failures — a mechanism reporting a plausible wrong number, a gate
that cannot fail, a denominator nobody discovered — are almost entirely
prose-only. They are also the ones that shipped with green suites, which is why
they had to be found by hand, twice.

That is the finding: enforcement covers what crashes, not what lies.

# Phase 1 — pattern register

| # | pattern | class | rules folded in | evidence | fires | enforcement today |
|---|---|---|---|---|---|---|
| P1 | a mechanism returns a plausible number nobody can falsify | plausible_but_wrong | `T-PLAUSIBLE-BUT-WRONG-001` | 7 instances tabled in-corpus, 2 sessions, several green suites | pre-done | none |
| P2 | a gate whose failing branch is unreachable | gate_defect | `T-CATCH-ALL-POINTER-...`, `T-NEVER-GATE-ON-A-RATIO`, `T-OMITTED-FACTOR-CANNOT-PENALIZE-001`, `T-SELF-MATCHING-RELEVANCE-SIGNAL-001`, `T-BORROWED-THRESHOLD-CONSTANT-VERDICT-001`, zero-cannot-fall, constant-factors | 7 rules, one mechanism | pre-build | none |
| P3 | denominator curated instead of discovered | denominator_corruption | `PR-COVERAGE-BY-CONSTRUCTION-001`, hand-curated audit, F6 name-match | liveness ledger, F6 (119 to 23) | pre-build | behavioural only, unnamed |
| P4 | a suite that exits 0 having executed nothing | silent_failure | `T-SYS-EXIT-IN-MODULE-SCOPE-001`, `T-CANON-INVOCATION-SILENT-FAIL-001`, hook sys.path outage | 340 authored, 0 run | pre-done | none |
| P5 | fail-open returns the negative verdict's shape | silent_failure | `T-D2A-FAILOPEN-MASKS-A-CRASH-001` | 2 of P1's instances | during-build | none |
| P6 | tests authored by the code's author | gate_defect | `T-SUITE-AUTHOR-BIAS-001` | A5 corpus, 4 defects found only by spec-derived cases | pre-done | none |
| P7 | plan computed before the state it reads is repaired | ordering | `T-PLAN-COMPUTED-BEFORE-STATE-REPAIR-001` | D-013 | during-build | none |
| P8 | the remedy is prose | implementation_defect | `T-PROSE-ONLY-REMEDY-001` | the 316 above, at corpus scale | pre-done | none |
| P9 | mega-corpus proposal over a curated denominator | scope_creep | `HR-NOVELTY-001` | 10 of 10 majority-owned | pre-build | ENFORCED (`jit_skill_loader`) |
| P10 | literal/environment assumption in a matcher | assumption | `T-LICENSE-FILENAME-CASE-SENSITIVITY-001`, `T-MINLENGTH-COUNTS-WHITESPACE-001`, `T-FINGERPRINT-FROM-RENDERED-MARKDOWN-001` | A5 | during-build | none |

P9 is already mechanical and must not be rebuilt.

# Proposed build, by ROI

**G1 — vacuity gate (pre-build, covers P2, 7 rules).** For every gate module, its
suite must construct at least one state that FAILS. Mechanically checkable: a
suite that never asserts a non-zero exit or a FAIL verdict is testing only the
happy path, and its gate is unfalsifiable. This is the highest-leverage item
because it is the mechanism behind the largest rule cluster, and because it is
the one defect that certifies itself.

**G2 — executed-count gate (pre-done, covers P4).** A suite reporting `N/N` where
N is 0, or exiting 0 with no assertion executed, is UNVERIFIED, never PASS. Also
detects `sys.exit` at module scope, the exact shape that silenced 340 tests.

**G3 — oracle gate (pre-done, covers P1).** Every mechanism emitting a number
must have at least one assertion against an independently-known expected value, a
literal in the test rather than a value recomputed from the mechanism. Partial by
nature: it can detect the absence of any literal-compared assertion, not the
correctness of the oracle.

**Deferred, with reason.** P6 as a convention (a `spec:` header in test files)
would be inert on the host that runs it — the failure mode already sealed as
`T-CONVENTION-INERT-ON-THE-HOST-THAT-RUNS-IT-001`. It needs a real predicate, not
a header. P7 and P10 are per-site defects with no general detector yet.

# Non-negotiable constraint on this build

No rule is sealed without an enforcement path, and every gate built here must
itself pass G1 — it must ship a constructed failing state. A vacuity gate that
cannot fail would be the funniest possible instance of P2.
