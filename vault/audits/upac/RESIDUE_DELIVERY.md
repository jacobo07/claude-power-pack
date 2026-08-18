---
title: UPAC — residue delivery record (Option A)
date: 2026-08-19
status: DELIVERED — W1 + R1 + R2 + R3 built, wired, verified
audit: vault/audits/upac/SYSTEM_OWNERSHIP_OVERLAP_MAP.md
owner_decision: "1 + 2 + encuentra más sistemas ... como debe hacer siempre el sistema D2A"
covers: [upac, residue_delivery, w1, r1, r2, r3, dependency_sovereignty,
         architecture_horizon, cognitive_load, effect_harness_wiring]
---

# UPAC — Residue Delivery

The ownership map is a sealed record of what was measured on 2026-08-18 and is not
rewritten here. This is the separate record of what was built against its residue, per
the estate's rule that a plan or audit is never edited to match a later verdict.

## What was delivered

| id | Residue | Artifact | Commit |
|---|---|---|---|
| **W1** | rule-effect harness reached no live surface | `verify_spp` row `rule-effects` | `9b339d3` |
| **R1** | no owner for dependency sovereignty | `modules/dependency_sovereignty/` + `/dependency-sovereignty` | `f77e10c` |
| **R2** | no architecture-scale counterfactual | `modules/architecture_horizon/` + `/architecture-horizon` | `10e6844` |
| **R3** | no cognitive-load-on-engineer lens | `modules/cognitive_load/` + `/cognitive-load` | `6951874` |

Each ships a module, a V-gate suite, a command (the live surface reachability actually
seeds from — `tools/` is not a seed), and standing `verify_spp` rows.

## Compounding Test — the three PARTIAL answers

The map recorded 9 of 12 passing, with 5, 11 and 12 all failing on one defect: the
effect harness was built, correct, exported, and invoked only by its own test.

| # | Question | Was | Now | Evidence |
|---|---|---|---|---|
| 5 | a wrong constitutional rule can be refuted | PARTIAL | **YES** | `verify_spp --row rule-effects`, rc=0, `RULE_EFFECTS IMPROVED=1 REGRESSED=0` |
| 11 | learning from outcomes, not documentation | PARTIAL | **YES** | same row; `RULE_COUNTERFACTUALS WOULD_BLOCK=3` |
| 12 | the Constitution improves with experience | PARTIAL | **YES** | same row, standing in the umbrella |

One of the three counterfactuals is `HR-NOVELTY-001` replayed against
`uceimr-corpus-2026-08-04` — the same proposal class this audit measured. The rule
governing mega-corpus proposals now demonstrably fires against a recorded one.

Question 9 ("depth produces quality, not bureaucracy") remains CONTESTED and is not
claimed closed: 20 STOP #1 records across 129 plans, 8 open. That is a throughput
observation, not something a module closes.

## Findings the residue produced

Building the three views measured things nothing in the estate had measured:

1. **An eleven-unit mutually-dependent core** — `cdio`, `cognitive_os`, `dataset_first`,
   `decision_review`, `duplicate_to_advantage`, `fable_distillation`,
   `frontier_intelligence`, `liveness`, `parallel_mesh`, `spec_gate`, `wrapper`. Every
   member transitively reaches every other, so a dozen units tie at 27–29 transitive
   dependents and **nothing inside the group invalidates first**.
2. **`decision_review` carries the highest cognitive load** — cost 90: 8 own files plus
   9 upstream units exporting 82 public symbols.
3. **25 units declare no entry point** — no package docstring, no `__all__`. The cheapest
   cognitive-load defect in the estate, now named rather than counted.
4. **Two load-bearing dependencies** — `anthropic` and `httpx`, 6 observed call sites
   each in `sleepless_qa`; a breaking change edits six files.

## Two defects found in this pass, in my own work

Recorded because a delivery record that lists only successes is an advertisement.

- **`INTERNALIZE` was emitted and withdrawn.** On real data it recommended internalizing
  Pillow, PyYAML and Playwright. Deciding to absorb an upstream needs reimplementation
  cost, which no pin string or import count carries. It is now a declared unreachable
  rung, printed with its reason.
- **`architecture_horizon --root` was silently inert.** `_unit_of` read a module-level
  constant instead of the passed base, so every file under another root raised
  `ValueError`, `build_graph` swallowed it as a skip, and an empty graph was reported as
  a real one. It passed against the real repo only because that path uses the default
  root. Four synthetic V-gates failed on their first run and named it.

## Verification observed

Full umbrella, 53 rows, 402.58s: **all six new rows OK**.

```
rule-effects                  rc=0   RULE_COUNTERFACTUALS WOULD_BLOCK=3
dependency-sovereignty        rc=0   DEPENDENCY_SOVEREIGNTY REVIEW=14  WRAP=2
dependency-sovereignty-gates  rc=0   DSSE_PASS=10/10
architecture-horizon          rc=0   baseline UNSEALED -- reporting only
architecture-horizon-gates    rc=0   AH_PASS=9/9
cognitive-load                rc=0   COGNITIVE_LOAD units=84 undeclared=25 max_cost=90
cognitive-load-gates          rc=0   CL_PASS=7/7
```

Reachability: modules 356 → 360, REACHABLE 233 → 239, ORPHAN 123 → 121, gate offenders
5 → 3. Standing debt fell **by name**, not by threshold.

### Six pre-existing umbrella failures, not inherited silently

`mirror-parity` · `drift-report` · `paths+secrets` · `hooks-registration` ·
`dataset-build` · `benchmarks-ok`.

Causation excluded by construction: no commit in this pass touched the hooks
registration script, `settings.json`, any mirror file, the drift PAIRS config, the
secret allowlist, the dataset-build path, or a benchmark target. `hooks-registration`
was checked directly — it fails on `idempotency-mod`, a marker-set drift between the
registration script (11 markers) and live `settings.json` (5); none of the markers is
`d2a_gate`. These are named here because a failing gate is a defect regardless of whose
it is, and "pre-existing" is not a promotion.
