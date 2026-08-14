---
title: Done-gate audit — what oracle does each gate consult?
date: 2026-08-14
covers: [done_gate, intent_verified, intent_verifier, spec_gate, verify_spp, done-gate-audit]
tier: 2
status: FASE 0 complete — measured, awaiting Owner decision at STOP #1
---

# Done-gate audit

## Question

A done-gate is defined by the **oracle it consults**, not by its name. Four
oracles are possible: the intent that started the work, the code running, the
tests reaching a branch, the corpus lacking a duplicate. This audit asks, for
every executable gate surface in the repo, which one it actually reads.

## Method

The denominator is **discovered, never curated** (PR-COVERAGE-BY-CONSTRUCTION-001):

1. every row of `tools/verify_spp.py`, parsed out of that file's own `rows_spec`
2. every `modules/*/gate*.py`, `modules/done_gate/*`, `modules/uqf/gates.py`,
   `modules/liveness/*`, `modules/output_contracts/validator.py`
3. every `hooks/*.js` capable of emitting a blocking decision

A hand-listed set would have measured memory instead of reality — the failure
this repo already paid for in the Liveness Ledger.

## Result — 58 gate surfaces

| Class | Count | What it proves |
|---|---:|---|
| FUNCTIONAL_ONLY | 38 | the code ran, the artifact exists, rc was 0 |
| COVERAGE_ONLY | 8 | the tests reach the branches |
| NOVELTY_ONLY | 3 | nothing duplicated |
| INTENT-touching | 5 | see the correction below |
| UNCLASSIFIED | 4 | no oracle signal in the source |

### The correction that matters

The keyword pass returned 5 `INTENT_VERIFIED` surfaces. Each was checked by
hand, and **all five are false positives** for done-time intent verification:

| Surface | Keyword hit | What it actually does |
|---|---|---|
| `modules/spec_gate/gate.py` | `check_spec_gate` | asks whether a spec EXISTS, before coding |
| `modules/sdd_os/pre_exec_gate.py` | spec binding | classifies tier and WRITES a spec skeleton, before coding |
| `tools/test_sdd_os.py` | spec machinery | tests that the gate code works |
| `tools/test_spec_driven.py` | spec machinery | tests that the gate code works |
| `tools/test_governance_propagation.py` | objective | tests that governance files propagate |

So the honest count is:

> **0 of 58 gate surfaces compare a task's output against that task's declared
> intent.** Five reach an intent artifact, all of them at task START. None
> reads one at task CLOSE.

Confirmed structurally: `find_bound_spec` has exactly one non-doc caller
(`tools/sdd_os_cli.py`); `check_spec_gate` has two (`one_shot/compiler.py`,
`dataset_first/classifier.py`). All three are pre-execution. No done-gate
imports `modules.sdd_os.spec_binding`.

## The gap is a missing JOIN, not a missing artifact

The first framing — "the intent is not captured" — is wrong, and the
correction makes the fix an order of magnitude smaller.

`modules/sdd_os/pre_exec_gate.py` writes `## 7. Acceptance criteria / AC-001:`
into every Tier 2+ spec it generates. Grepping `AC-\d` finds producers and no
consumer. That is real, but it is not the whole picture: the Owner-authored
specs do not use `AC-001` bullets at all. They state criteria as a table of
**V-gate ids**:

```
| Gate                  | Asserts                                             |
| `V-LD-SERIES-EXCLUDED`| 3 same-shape uuid files are excluded as a series... |
```

A V-gate id is already a mechanical oracle: the criterion is satisfied when a
test emitting that id is observed to pass. Nothing in the repo performs that
lookup.

### Measured: 64 declared criteria across 13 specs

| Outcome | Count | Meaning |
|---|---:|---|
| SATISFIED | 9 | the id is emitted by a file `verify_spp` runs |
| UNJOINED | 41 | a test emits the id, but no standing gate reaches it |
| UNVERIFIABLE | 12 | the id appears in no executable file — prose only |
| CRITERIA_NOT_MECHANICAL | 2 specs | the acceptance section names no id |
| NO_CRITERIA_SECTION | 1 spec | the spec declares no criteria |

The 41 UNJOINED are the finding. Each was green on the day it was written, by
hand, once. `test_ledger_discovery.py` (11 criteria) and
`test_terminal_registry.py` (8 criteria) are not rows of `verify_spp` — so no
push, no commit, and no done-claim since has re-checked a single one of them.
A regression there is invisible to every one of the 58 gates above.

## Second-order finding

`modules/sdd_os/pre_exec_gate.py` is reachable only from `tools/sdd_os_cli.py`.
No hook invokes it. The tier classifier and the spec generator run when a human
runs them, which means the artifact the intent verifier would consume is
produced by hand today. Wiring the verifier without wiring its producer would
reproduce the orphan-field pattern.

## Instruments

`scratchpad/audit_done_gates.py` (classification) and
`scratchpad/intent_join.py` (criterion join). Both take the repo as their only
input and are re-runnable; the second becomes the seed of the verifier.
