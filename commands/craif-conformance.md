---
name: craif-conformance
description: "Verify every seam in CRAIF's reinforcement catalogue declares the contract the catalogue itself specifies, and names an Owner that still exists on disk."
allowed-tools:
  - Read
  - Bash
argument-hint: "[--list]     — optional: list the discovered seams and exit 0"
---

# CRAIF Adapter Conformance — /craif-conformance

`vault/knowledge_base/craif/CRAIF_D2A_REINFORCEMENT_PACKAGES.md` catalogues one
reinforcement package per real owner CRAIF's STOP #1 audit found already governing a
slice of the surface. The catalogue is honest about what is missing — but nothing
verified that a package actually declares the schema the catalogue states, and nothing
would notice when a package's named Owner moved or was deleted.

## Run

!`python ~/.claude/skills/claude-power-pack/modules/craif/adapter_conformance.py $ARGUMENTS`

## What it checks

Both the package set and the field set are **discovered from the document itself** —
the `## N.` headings and the `Schema per package:` sentence. Neither is a list inside
the checker, so a package added tomorrow is scored on the next run rather than being
absent from the denominator (`PR-COVERAGE-BY-CONSTRUCTION-001`).

Per seam, four defect classes:

- a field the catalogue's own schema requires is **absent**
- a field is **declared but empty**
- the Owner names a repo path that is **not on disk** (the seam points at a corpse)
- the Owner names **no repo path at all**, so nothing in the seam is machine-verifiable

That last one matters most. Without it a prose-only Owner scores CONFORMING on the
strength of having no checkable content — the gate's vocabulary would not reach it, and
a zero it cannot see can never fall.

## Exit codes

- `0` — every discovered seam conforms.
- `1` — at least one seam is NONCONFORMING; each is printed with its reasons.
- `2` — the catalogue is missing, declares no schema, or contains zero packages. This
  is deliberately an error rather than a clean run: a checker with an empty vocabulary
  would find zero violations in any possible document.

## Reading the output

The tail line is `CRAIF_ADAPTER_CONFORMANCE=<conforming>/<discovered> seams conforming`.
Report the ratio and name every `[FAIL]` seam with its reason — a conformance run
summarised as "mostly fine" is not a verdict.

The catalogue's header states a package is a proposal artifact whose changes go through
the owner's own amendment process. Do **not** edit the catalogue to turn this gate
green: that is the checker grading itself. Record the finding and let the Owner amend.

Gates: `tools/test_adapter_conformance.py` (`CRAIF_ADAPTER_PASS=11/11`).
