---
name: cpp-drift-registry
description: What this estate detects about drift — discovered from disk, never a maintained list. Reports detectors, the families they attribute drift to, detectors that attribute it to nothing, and families named in prose that no detector mentions.
---

# /cpp-drift-registry

Run the discovered drift registry over the current Power Pack tree.

```bash
python modules/drift_registry/registry.py              # human report
python modules/drift_registry/registry.py --json       # machine-readable
python modules/drift_registry/registry.py --singletons # one-file terms dropped
python modules/drift_registry/registry.py --expect schema config semantic
```

## What it answers

- Which files actually detect drift, and what they detect it *about*.
- **`unclassifiable_detectors`** — detects drift, attributes it to no family,
  so its coverage cannot be credited to anything.
- **`undetected_families`** — a family this repo *names* in prose and no
  detector mentions. Prose without a probe.

## What it will not answer

Whether a drift family exists that nobody here has ever named. The scan is
bounded by the repo's own vocabulary, and a module claiming otherwise would
assert a completeness it has no instrument for. Read `undetected_families`
as *named but unprobed*, never as *complete*.

## Why nothing is enumerated

A registry enrolled by hand measures what someone remembered
(`PR-COVERAGE-BY-CONSTRUCTION-001`): an undeclared component is not scored
UNKNOWN, it is absent from the denominator, and absence reads as health.
Family terms are therefore earned by **recurrence** — written in two or more
distinct files, or as a `<word>_drift` identifier — the same measured
instrument `rule_compiler` uses to detect boilerplate. One-file terms are
counted and retrievable via `--singletons`, never silently dropped.

## Origin

EGCC Rc2. The EGCC proposal measured 0 of 25 datasets owned
(`vault/plans/egcc-corpus-2026-08-06.md`); this was one of two residues that
survived. Its sibling is `hardrule_compile.py --binding` (Rc1).

Spec: `vault/specs/egcc-residue-rc1-rc2.md` · Gate:
`python tools/test_egcc_residue.py`
