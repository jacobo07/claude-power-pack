---
title: EGCC C1 — reconcile the enforced corpus against the compiled corpus
date: 2026-08-07
tier: T2
status: APPROVED — Owner selected "Solo C1" at STOP #1 (2026-08-07)
covers: [egcc, c1, reconcile, rule_compiler, hard_rules, verify_hard_rules, h7, mirror, archive]
audit: vault/plans/egcc-expansion-2026-08-07.md
denominator: EGCC_EXPANSION_DENOMINATOR.md
---

# Spec — C1

## Disposition of the STOP it closes

`vault/plans/egcc-expansion-2026-08-07.md` — **STOP #1 RESOLVED 2026-08-07.**
The Owner selected "Solo C1"; C1 is built and shipped. C2 (the `severity`
capture defect), C3 (a rule's retirement condition) and C4 (the liveness
scanner's four blind packages) were presented and **not** selected, so they
remain unbuilt and unclaimed.

The plan file itself is left exactly as written. A plan is a sealed record of
what was believed when, and rewriting it to match a later verdict destroys the
only evidence of what the decision looked like before it was made.

## Problem, measured

`parser.load_corpus()` reads exactly two files. The rules this estate actually
enforces are largely in neither.

| Measurement | Value |
|---|---|
| distinct `HR-` ids named across 3,066 files | 418 |
| of those, compiled | 16 |
| named but never compiled | 402 |
| ...named in ≥2 distinct files | 68 |
| ids in `CLAUDE.md`'s sentinel block | 36 |
| ids in `vault/hard_rules/HARD_RULES.md`'s block | 15 |
| **ids in both** | **9** |
| only in the mirror | 27 |
| only in the archive | 6 |

The divergence is **bidirectional**, so it is not a lag. `HR-SECRET-001`,
`HR-CASCADE-001`, `HR-PREMISE-001`, `HR-COST-001` and `HR-OUTPUT-001` are each
enforced by a live hook and absent from the compiled corpus — verified by direct
search, returning zero occurrences in the archive.

## Why the existing gate cannot see it

`tools/verify_hard_rules.py` check H7 iterates `(CLAUDE.md, archive)`, sets
`has_block = True` on the first file containing both sentinel markers, and
`break`s. Two independent reasons it cannot witness this defect:

1. The `break` means the archive is never opened once the mirror matches.
2. **Even without the break it would pass**: both files *do* carry the markers.
   H7 asserts marker presence, never block agreement. A conjunction would not
   have helped.

## Scope

### 1. `modules/rule_compiler/reconcile.py` — new

Two reconciliations, deliberately kept apart because they answer different
questions and share no threshold.

**R-A — mirror vs archive.** Parse the `### HR-…` headings inside each file's
sentinel block. Emit `both`, `mirror_only`, `archive_only` as **named id lists**.

**R-B — enforced vs compiled.** Discover every `HR-` id named under
`modules/ tools/ commands/ governance/ hooks/ agents/`, recording the files that
name each. Classify:

- `hook_enforced` — named in at least one file under `hooks/`. A hook is the live
  enforcement surface, so this is a rule that *fires*, not one that is discussed.
- `referenced` — named elsewhere only.

Apply the estate's measured recurrence gate: an id named in **≥2 distinct files**
is real; a one-file id is a `singleton`, retained and retrievable, never silently
dropped. This is the same instrument `find_boilerplate_stops` and
`drift_registry` already use, reused rather than reinvented.

Diff against the compiled ids to produce `enforced_not_compiled` and
`compiled_not_referenced`.

### 2. `tools/hardrule_compile.py --reconcile` — the live surface

Mirrors the `--binding` pattern shipped as Rc1. This is what clears the liveness
gate; a module no surface reaches is an orphan.

### 3. `tools/verify_hard_rules.py` H7 — message only

Remove the `break` so both files are inspected, and report which carry the block
(`both` / `claude-only` / `archive-only` / `neither`). **Pass semantics are
unchanged** and the check count stays at **7**.

## Non-negotiable constraints

Each cites the defect it exists to avoid.

| # | Constraint | Defect avoided |
|---|---|---|
| 1 | Report **named id lists and integers, never a ratio** | A ratio is satisfied by shrinking its denominator (`feedback_never_gate_on_a_ratio`) |
| 2 | A scan finding **zero** ids returns `NO_IDS_FOUND`, never `NO_DIVERGENCE` | An instrument bounded by its vocabulary reads the unrecognised as 0, and 0 never falls (`feedback_zero_cannot_fall`) |
| 3 | The id set is **discovered by walking disk**, never a maintained list | A registry enrolled by hand measures memory; an undeclared subject is absent from the denominator, and absence reads as health (`PR-COVERAGE-BY-CONSTRUCTION-001`) |
| 4 | Exit 1 **only** on `enforced_not_compiled ∧ hook_enforced` | A gate that cries wolf on valid work is uninstalled by the third false alarm. Everything else is advisory |
| 5 | H7 must keep passing and stay at 7 checks | Turning a live gate into a hard conjunction inerts it — the disarmed-kill-switch shape already on this estate's record |
| 6 | `compiled_not_referenced` is reported and **attributed to `effect_harness.py:166`**, not reinterpreted | That module already measured this half; re-deriving it would create a second, drifting source of truth |
| 7 | The report states in prose that it **cannot witness a rule nobody named** | The scan is bounded by the estate's own vocabulary; claiming completeness would assert an instrument it does not have |
| 8 | Singletons counted and retrievable via a flag, never dropped | Silent truncation reads as "covered everything" (`no-silent-caps`) |

## Acceptance criteria

| Gate | Asserts |
|---|---|
| `V-C1-DISCOVERED` | The id set comes from disk: injecting a fixture id into a temp tree makes it appear; removing it makes it disappear |
| `V-C1-RECURRENCE` | A one-file id is a singleton, a two-file id is real — asserted in both directions |
| `V-C1-NO-RATIO` | No key in the JSON output is a float or named `*_ratio`/`*_pct` |
| `V-C1-ZERO-DISTINCT` | An empty tree yields `NO_IDS_FOUND`, not a clean-divergence verdict |
| `V-C1-BIDIRECTIONAL` | Mirror-only and archive-only are reported separately, never merged into one "divergent" bag |
| `V-C1-HOOK-CLASS` | An id named only in `hooks/` classifies `hook_enforced`; one named only in `commands/` does not |
| `V-C1-EXIT-DISCIPLINE` | Exit 1 with a hook-enforced uncompiled id; exit 0 when the only divergence is prose-only |
| `V-C1-LIVE-CORPUS` | Against the real repo, `mirror_only` contains `HR-SECRET-001` and `both` has fewer members than either block |
| `V-C1-H7-UNCHANGED` | `verify_hard_rules.py` still prints `HARDRULES_PROBE=7/7` and exits 0 |
| `V-C1-HERMETIC` | Three consecutive runs produce byte-identical output |

## Done-gate

All ten gates pass, three consecutive identical runs, `test_egcc_residue.py` and
`test_enforcement_systems.py` unchanged, `liveness` offenders not increased,
pathspec-scoped commit, `REMOTE_DELTA = 0 0`.

## Rollback

Delete `modules/rule_compiler/reconcile.py`, revert the `--reconcile` flag and
the H7 message. Nothing else is touched; no existing behaviour changes, so
rollback cannot strand a consumer.

## Explicitly out of scope

Migrating the 27 mirror-only rules into the archive. That changes what the router
enforces at every trigger point and is the Owner's decision, not a side effect of
building the instrument that found them.
