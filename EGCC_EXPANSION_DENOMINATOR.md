# EGCC Expansion — the denominator, discovered

**Measured 2026-08-07** against `HEAD 290edc2`. Every number below was read off
disk by a walk, never enumerated by hand: a curated inventory measures what
someone remembered, and an undeclared subject is not scored UNKNOWN — it is
absent from the denominator, and absence reads as health
(`PR-COVERAGE-BY-CONSTRUCTION-001`).

Scan scope: `modules/ tools/ commands/ governance/ hooks/ agents/ vault/
knowledge/` — **3,066 files** of type `.md .py .js .json`.

## 1. Executable surface

| Subject | Count | Note |
|---|---|---|
| `modules/` — Python packages | 66 | what `liveness/reachability.py` can see |
| `modules/` — **JavaScript only** | **4** | `cdicf` · `governance-overlay` · `harness` · `rtk-core` |
| `modules/` — mixed py+js | 4 | |
| `modules/` — neither | 6 | `agent-governance` `bug-hunter` `daemon` `design-md` `omniram-sentinel` `oracle` |
| `commands/` | 68 | |
| `agents/` | 12 | |
| `hooks/` in repo | 39 | |
| `~/.claude/hooks/` live | 86 | the canonical/live split is a standing drift surface |
| `tools/*.py` | 305 | of which **122** are `test_*` |
| distinct `V-` gate ids | 1,525 | across 119 files |

The **4 JS-only packages** are the measured size of gap **D-009**, which the CDICF
record named at one (`modules/cdicf`). The reachability scanner enumerates Python
packages, so all four are absent from its denominator rather than failing in it.

## 2. Knowledge substrate

| Subject | Count |
|---|---|
| `vault/knowledge_base/` families | 26 |
| `vault/` top-level directories | 67 |
| `governance/*.md` | 11 |
| `vault/plans/*.md` | 124 |
| `vault/specs/*.md` | 9 |
| `vault/audits/` directories | 5 |
| `*.jsonl` under `vault/` | 947 files |

STOP-bearing plans, from `vault/plans/STOP_LEDGER.md` regenerated this session:
**23 plans — OPEN 8 · CONTRADICTED 11 · RESOLVED 4 · UNKNOWN 0.**

## 3. The rule corpus

Read from `vault/hard_rules/compiled/rules_db.json`, not re-derived.

| Measure | Value |
|---|---|
| rules compiled | 162 (**161 unique** — `HR-BLENDING-THRESHOLD` appears twice) |
| valid / rejected | 149 / 13 |
| form: FIELDED / IMPERATIVE | 136 / 26 |
| sources | exactly **two** files |
| — `global:core/HARD-RULES.md` | 147 |
| — `pp:vault/hard_rules/HARD_RULES.md` | 15 |

Per-field occupancy:

| field | empty | of |
|---|---|---|
| `trigger` | 30 | 162 |
| `stop` | 28 | 162 |
| `evidence` | 20 | 162 |
| `exception` | 47 | 162 |
| `severity` | **147** | 162 |
| `enforcement` | **162** | 162 |

Two readings that a raw count would get wrong:

- **The 30 empty triggers are not a defect.** All 26 `IMPERATIVE` rules are
  one-line prose whose entire text *is* the rule. Restricted to the 124 valid
  `FIELDED` rules, the count of rules missing a trigger or a stop is **0**. The
  validator is doing exactly what it claims.
- **`severity` has no usable value at all** — not 15, but zero. The 147 empty
  ones are empty, and all 15 populated ones read `'CRITICAL | RECURRENCE: 1x'`
  or `'HIGH | RECURRENCE: 6x'`: the field capture runs to end-of-line and
  swallows the ` | RECURRENCE: Nx` suffix. Three distinct values exist across
  the whole corpus, and none of them is a severity.
- `enforcement` is at 0 of 162 by construction — it shipped yesterday
  (Rc1) and nothing has been classified yet. That is `UNDECLARED`, a state, not
  a failure.

There is **no retirement, expiry or sunset field** on a compiled rule. Confirmed
by key inspection, not by grep.

## 4. The governance vocabulary vs. the compiled corpus

This is the load-bearing measurement of the sweep.

| Measure | Value |
|---|---|
| distinct `HR-` ids named anywhere in the 3,066 files | **418** |
| of those, present in the compiled corpus | **16** |
| named but **never compiled** | **402** |
| ...of which named in ≥2 distinct files | **68** |

The ≥2-file gate is the same measured recurrence instrument `rule_compiler` uses
to detect boilerplate and `drift_registry` uses to earn a family name. It
separates a typo from a rule the estate actually refers to.

The 68 recurrent uncompiled ids are not obscure. The top of the list:

| id | files naming it | including |
|---|---|---|
| `HR-PREMISE-001` | 44 | `modules/dataset_first/knowledge_sufficiency.py` |
| `HR-COST-001` | 23 | `agents/graphify-librarian.md` |
| `HR-SECRET-001` | 19 | `hooks/hook-dispatcher.js` |
| `HR-SECRET-003` | 17 | `modules/fable_distillation/fd_07_flywheel.py` |
| `HR-OUTPUT-001` | 16 | `hooks/hook-dispatcher.js` |
| `HR-CASCADE-002` | 14 | `hooks/cascade_check_bash.js` |
| `HR-SPEC-001` | 12 | `vault/knowledge_base/apex_baseline_doctrine.md` |
| `HR-CASCADE-005` | 10 | `tools/jit_skill_loader.py` |

Every one of those is **enforced by a live hook** and **absent from the corpus
the compiler reads**. Verified directly rather than inferred:
`vault/hard_rules/HARD_RULES.md` contains **zero** occurrences of
`HR-SECRET-001`, `HR-CASCADE-001`, `HR-PREMISE-001`, `HR-COST-001` or
`HR-OUTPUT-001`. They live in the inline mirror in `CLAUDE.md` and in the hook
sources, and `parser.load_corpus()` reads exactly two files, neither of which is
either of those.

The two halves of this were not equally unknown:

- **Known and owned.** `modules/rule_compiler/effect_harness.py:166` already
  records that "140 of 149 compiled rules come from `global:core/HARD-RULES.md`
  and govern OTHER estates (payment secrets, landing pages, i18n mirrors,
  storefronts)". The corpus being mostly foreign is measured and documented.
- **Not owned.** Nothing measures the converse — rules this estate *enforces*
  that never reach the corpus. `effect_harness` begins from the compiled set, so
  a rule absent from that set is absent from its denominator too. This is the
  same shape as the finding it was built to avoid.

The gate that nominally covers this is `tools/verify_hard_rules.py` check **H7**,
and its own docstring states the mechanism: *"archive-or-claude — CLAUDE.md **OR**
vault/hard_rules/HARD_RULES.md has the sentinel block"*. A disjunction cannot
witness a divergence between its two operands. A rule present only in the mirror
passes H7 forever while never compiling.

## 5. Ledgers with a reader and almost no writer

Five governance ledgers hold exactly one row:

| rows | ledger |
|---|---|
| 1 | `vault/decision_registry/records.jsonl` |
| 1 | `vault/done_gate/receipts.jsonl` |
| 1 | `vault/dataset_first/necessity_ledger.jsonl` |
| 1 | `vault/ias/c2_opportunity_cost_ledger.jsonl` |
| 1 | `vault/anti_fragility/hacks.jsonl` |

One row is the signature of a writer that fires at build or test time and never
in production — the orphan-producer shape
(`feedback_orphan_field_dead_recovery_path`). It is reported here as an
observation, not a verdict: a ledger for a rare event legitimately holds one row,
and distinguishing the two requires opening each writer. That has not been done,
and this document does not claim it has.

## 6. What this denominator forecloses

An expansion pass proposing a *new* governance family must clear
`HR-NOVELTY-001` against these numbers: 80 module directories, 26 knowledge
families, 68 commands, 11 governance documents, 1,525 executable gates and 161
compiled rules. Adjacency to something in that set is the expected finding, and
adjacency is an EXTEND.
