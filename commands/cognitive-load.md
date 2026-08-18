---
description: How much must an engineer hold in their head to change this unit? Measures the inward cost — files to read plus upstream exported surface — and names the units that never say where to start.
---

# /cognitive-load

UPAC residue R3 (`vault/audits/upac/SYSTEM_OWNERSHIP_OVERLAP_MAP.md`). `modules/cdio`
scores what an **end user** sees. `modules/cognitive_os` governs what an **agent's**
context costs. The load a codebase places on a **human who has to modify it** was
unscored.

## Run it

```
python -m modules.cognitive_load.load                # ranked view
python -m modules.cognitive_load.load --unit <name>  # what one change costs
python -m modules.cognitive_load.load --json
python -m modules.cognitive_load.load --root <path>  # any repo
```

Standing rows:

```
python tools/verify_spp.py --row cognitive-load
python tools/verify_spp.py --row cognitive-load-gates
```

## The two directions, and why both exist

| | question | owner |
|---|---|---|
| outward | if I change X, **what breaks**? | `/architecture-horizon` (R2) |
| inward | to change X, **what must I read**? | this lens (R3) |

They are complements, not variants. A unit can be cheap to break and expensive to
understand, or the reverse, and conflating them hides both.

`context_cost = files_to_read + upstream_surface` — a **stated formula, not a fitted
score**. Both terms are counts of things a person actually opens and reads. Upstream
*surface* rather than upstream *edge count*, because depending on a unit that exports
forty names costs more than depending on one that exports two, and an edge count ties
them.

## Findings on this estate (2026-08-19)

- **`decision_review` carries the highest load**: cost 90 — 8 files of its own plus 9
  upstream units exporting 82 public symbols.
- **25 units declare no entry point** — no package docstring and no `__all__`, so you
  must read the files to learn where to start. That is the cheapest cognitive-load
  defect in the estate to fix, and it is reported by name.

## Non-duplication, enforced rather than promised

`modules/uqf` owns file-local defects: bare except, silent pass, missing type hints,
magic numbers, mutable defaults, god functions, hardcoded paths. **None of them is
recomputed here** — a second opinion on an owned question is duplication.
`V-CL-NO-UQF-OVERLAP` asserts the boundary mechanically against the module's own source,
so the claim cannot rot into a comment that used to be true.

Likewise the dependency graph is **imported** from `architecture_horizon`, never rebuilt.
Two import graphs in one estate would be two sources of truth for the same fact, and the
second one to drift would be silently wrong. `V-CL-SHARED-GRAPH` asserts that too.

## What it does not measure

Setup time, feedback latency, error-message quality, debugging affordances and naming
quality are printed as **declared unmeasured**, each with its reason. They need a clean
machine, a timed edit-run-observe loop, a real runtime failure, or an engineer attempting
a real diagnosis. Naming quality in particular is left alone deliberately: a linter that
judged names without domain knowledge would produce confident nonsense.
