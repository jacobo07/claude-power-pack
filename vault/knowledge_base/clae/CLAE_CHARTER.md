---
title: CLAE — Closed-Loop Autonomous Engineering Laboratory · Dataset Charter
family: clae
date: 2026-07-26
status: SEALED
parts: 26
gaps_closed: [G1, G2, G3, G4, G5]
primary_pillars: [R-009 LAAS, R-001 FounderOS]
parent: vault/knowledge_base/COMPENDIUM_CHARTER.md
---

# CLAE — Dataset Charter

## Purpose

Supply Claude Power Pack with the discipline of **measured distance to an external bar**.

Every quality mechanism the stack owns today answers a binary question against a criterion
the stack itself authored: `done_gate` asks whether the named artifact exists,
`output_contracts` asks whether the score clears 70, `uqf` asks whether the file scores
above threshold, `sqi` asks whether the index fell, `cdio-reviewer` asks whether the design
score reaches 80 with zero critical findings, `sleepless_qa` asks whether the verdict is
green. Each is sound. Collectively they share one blind spot: **after a pass, none of them
reports what remains.** Compliance is recorded; distance is discarded.

CLAE supplies the missing half. It defines what an external reference is, how a delta
between an artifact and that reference is made observable, how deltas are ranked by impact
rather than by discovery order, how the residual gap survives a passing gate, what minimum
a domain must derive so that a nominally-complete feature cannot pass as finished, which
properties a machine structurally cannot verify about itself, and what instrument must
exist before autonomous work is legitimate at all.

## Scope

CLAE owns:

- The **Reference** object — what qualifies as canonical, how it is acquired, versioned and
  provenanced, and why an internally-authored bar is not one.
- The **Delta** — extraction, observability, impact ranking, top-k correction, termination.
- **Quality Distance Accounting** — the residual ledger that survives a passing gate.
- **Anti-underbuild floors** — domain-derived minima, and why imported floors fail.
- **The Human Oracle Boundary** — the declared set of properties the stack cannot verify
  about itself, and the routing that converts a human answer into durable evidence.
- **Observability-Capable Phase Zero** — the proof that a project can boot, observe,
  measure, reproduce, compare and fail legibly, established before the first feature.
- **Autonomous toolsmith behaviour** and incident-to-probe conversion.
- **Deviation governance** — constraint-bounded substitution that preserves intent.
- **Evidence-gated autonomy** — the gate structure that replaces per-step approval.

## Non-scope (explicit ownership boundaries)

| Not owned by CLAE | Canonical owner | Relationship |
|---|---|---|
| Design scoring rubric | `modules/cdio/scorer` | CLAE generalizes its *shape*; CDIO keeps its criteria |
| Code quality scoring | `modules/uqf` | consumes CLAE's residual ledger |
| Index-direction monitoring | `modules/sqi` | SQI detects decrease; CLAE supplies distance |
| Empirical verification runs | `modules/sleepless_qa` | executes; CLAE decides against what |
| Artifact existence gate | `modules/done_gate` | CLAE adds residual after its pass |
| Slop-token detection | `hooks/scaffold-auditor` | CLAE adds the shallow-but-real case it cannot see |
| Owner-facing queue | `modules/owner_queue` | CLAE supplies the admission criterion it lacks |
| Reachability of modules | `modules/liveness` | CLAE reuses its by-construction discovery discipline |

## Owner

`modules/clae/` on the executable side once Parts are implemented; this dataset is the
doctrine. Institutional owner: Claude Power Pack governance.

## Interfaces

- **Consumes:** `liveness/reachability.py` discovery pattern · `done_gate` artifact
  contracts · `cdio/scorer` as the proven single-domain instance · PM-03 findings bus.
- **Produces:** residual ledger entries · floor declarations · oracle-routed questions ·
  Phase Zero readiness verdicts · deviation records · durable probes.
- **Registers into:** UKDL (rules, process rules, traps) · the compendium integration spine.

## Evidence base

R-009 (LAAS) mechanisms: binding quality brief, reference frames, qualitative pillars,
quantitative floors, banned outcomes, phase gates, reference-delta loops, durable status
memory, rehydration protocol, verified API notes, deviation ledger, deterministic seeds,
screenshot harness, pixel sampling, GPU profiling, bug-specific probes, explicit human
judgment boundary. R-001 (FounderOS) contributes the surface-integrity principle only.

Every mechanism claim in this family is labelled OBSERVED, VERIFIED, INFERRED, HYPOTHESIS
or REJECTED against that evidence, and separately labelled where it is a PP-side finding
from the Phase 0 audit rather than from the corpus.

## Limits and honest boundaries

CLAE is doctrine derived from a *single well-documented instance* (one visual project) plus
one internal proven vertical (`cdio`). The generalization from a domain where quality is
pixel-observable to domains where it is not is the family's central hypothesis, and Parts
that depend on it say so. Where a mechanism has not been demonstrated outside the visual
domain, it is registered in Open Questions rather than asserted as a rule.

## Completion definition

All 26 Parts sealed and above the depth floor · all registries populated · integration map
resolved against the named canonical owners · contamination gate zero · evidence index
complete · Dataset Completion Report written with observed counts.
