---
title: RE Baseline Compendium — Closure Report
date: 2026-07-29
status: CLOSED. One family built, three struck, residue shipped.
charter: vault/knowledge_base/COMPENDIUM_CHARTER.md (sealed 2026-07-26, NOT amended — see below)
ruling: Owner, 2026-07-29 — A then B then C; D (build E1–E5 as chartered) discarded
---

# RE Baseline Compendium — Closure Report

## Outcome

| | |
|---|---|
| Families chartered | **4** — CLAE, CRPF, IGEF, and the E1–E5 pass set |
| Families built | **1** — CLAE, Parts I–XXVI, sealed 26/26 |
| Families struck on audit | **3** — CRPF, IGEF, E1–E5 |
| Parts chartered | ~90–110 |
| Parts written | **26** |
| Struck by | a boundary audit against a discovered denominator, every time |

The charter allocated CRPF 22 Parts, IGEF 20, and E1–E5 approximately 24. **None was
written, and none should have been.** Each family was measured, before construction,
against what the estate already owned, and each failed that measurement.

## Why each family closed the way it did

**CLAE — COMPLETE (26/26).** Admitted by a *measured zero-hit sweep* of its vocabulary
(`reference-delta`, `quality distance`, `anti-underbuild`, `human oracle`,
`observability-capable`, `phase zero`, `deviation ledger`). It is the only family whose
admission criterion was evidence rather than assertion, and the only one that survived.
That correlation is the whole lesson of this compendium.

**CRPF — STRUCK (2026-07-27).** ~80 % owned by `cognitive_os` (CO-00…CO-12, 12 datasets
+ 11 modules), DAIF-08 Context Runtime and Parallel Mesh PM-04/05. Four of the charter's
five stated absences were false and the fifth partial. Root cause: the charter's CRPF
boundary enumerated `cost_collapse`, `graphify` GK-06 and `memory-engine` as non-owners
and never named `cognitive_os` — the family that actually held the territory.
Residue shipped as **CO-13** (Observed Residency) and **CO-14** (Residency Jurisdiction),
plus an Option-A wiring pass: 171 → 180 REACHABLE, JIT trigger 85 → 22 firings.

**IGEF — STRUCK (2026-07-29).** Zero of four mechanisms justified a family, and two
founding premises were refuted: the `Rule` dataclass carries no retirement field, so
G9's complaint was vacuous, and M4's live predicate (`CRITICAL or recurrence >= 3`) was
already risk-weighted. Residue shipped as alert escalation on unresolved repeat, a
discovery producer for mirror pairs (9 → 28 pairs, 2 → 7 real drifts visible), and a
rule-effect harness. The escalation pass also uncovered a defect the audit had not
seen: `MIRROR_PAIRS` was comparing two *different documents*, so all 333 handoffs were
a permanent false positive.

**E1–E5 — STRUCK (2026-07-29).** 1,371 files / 154 families swept; **15 of 17
mechanisms already owned**. Two founding claims false: E1's premise that FD "never makes
the student do the work" (FD-04's Step 2 re-executes the capability on the target
substrate and grades the output across six lenses), and E5's premise that the acceptance
arbiter was unwired — `tools/recovery_epoch_gate.py` wired it on **2026-07-14**, twelve
days *before* the charter was sealed, and names the charter's gap verbatim in its own
docstring.

## The sealed pattern

`PR-COVERAGE-BY-CONSTRUCTION-001`, **ninth measured instance**: an audit set enrolled by
hand measures memory, not reality. A component absent from the denominator cannot be
scored as overlap, and its absence reads as a gap.

Five consecutive corpus proposals measured as majority-owned:

| Proposal | Measured | Outcome |
|---|---|---|
| AISHF | 75–80 % owned | became CRAIF |
| RE Baseline (literal A–J) | 55–60 % owned | became 3 NEW + 5 EXTEND |
| KSF | 70–80 % owned | reduced to a 4-family residue |
| CRPF | ~80 % owned | struck |
| IGEF | 0 of 4 mechanisms | struck |
| E1–E5 | 15 of 17 mechanisms | struck |

**The failure is never the pillar.** Each source analyzed itself correctly — Colibrì's
own Duplicate-to-Advantage map scored context hygiene and memory hierarchy as EXTEND,
and said outright that renaming an existing capability does not make it new. The failure
is a boundary column filled in from memory instead of swept.

## Lesson, already active

**Run the overlap audit against a complete, discovered denominator BEFORE any
construction.** This is not a recommendation in this file; it is a standing obligation
in `RE_BASELINE_RESUMPTION.md` block 3, sealed by Owner ruling 2026-07-29, and it is the
gate that struck three families before they cost ~66–80 Parts of writing.

Corollary the audits kept paying for: **count the thing, not a proxy for it.** Three
measurement slips this session — a CLAE 26-vs-29 near-miss, an "eight seams" catalogue
reported as nine, and a false "the kill switch is INERT" claim carried from memory —
were each caught by re-measuring rather than by reasoning. Two of the three would have
shipped as findings.

## Residue shipped (the compendium's actual product)

| From | Artifact | Commit |
|---|---|---|
| CRPF | `cognitive_os_13_observed_residency.md`, `cognitive_os_14_residency_jurisdiction.md` | `3c41824` |
| CRPF | wiring pass — scheduled-task discovery, 13-module disposition, JIT trigger | `a91328c`, `5f88210`, `7bff31c` |
| IGEF | alert escalation on unresolved repeat | `0087c1c` |
| IGEF | mirror-pair discovery producer (replaces two hand-written lists) | `a8e7662` |
| IGEF | rule-effect harness | `9df175b` |
| E1–E5 | `epistemic_algebra` wired into its two contract-named consumers | `37ad01c` |
| E1–E5 | CRAIF adapter conformance checker + `/craif-conformance` | `59d1888`, `a334135` |

Seven shipped repairs, all of them removals of duplication or closures of a wiring gap.
Not one new family.

## What is deliberately NOT claimed

The `COMPENDIUM_CHARTER.md` is **not amended**. It was sealed while concurrent panes
were reading it, and rewriting a sealed artifact to match a later verdict would destroy
the record of what was believed when. Where the charter and this report disagree, this
report and `RE_BASELINE_RESUMPTION.md` block 2 win — reconcile from the filesystem,
never from either narrative.

`epistemic_algebra` did **not** reach REACHABLE. The whole `decision_review` package is
PLANNED and no live surface consumes ACIS levels, so there was no real flow to join;
reaching REACHABLE would have meant inventing a consumer, which is manufacturing the
measurement. It is declared LIBRARY, which is the honest class, and that declaration
became true only when the sibling importers landed.

CRAIF's catalogue is at **7/8 conforming**, exit 1. Seam 8's Owner is prose and names no
verifiable path. It is recorded in `OWNER_QUEUE.md`, not silently fixed — editing the
catalogue to turn the gate green would be the checker grading itself.

Four `session_resilience` modules remain ORPHAN and `modules/daemon/` holds zero `.py`
files while the charter names `daemon` an E5 target. Both are documented in
`OWNER_QUEUE.md` with a proposed owner and a recommended action, per module, by name.
