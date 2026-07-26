---
title: RE Baseline Compendium — Charter
date: 2026-07-26
status: APPROVED (Owner selected 3 NEW + 5 EXTEND at STOP #1)
supersedes: the literal A–J ten-family specification
audit: vault/plans/re-baseline-compendium-2026-07-26.md
corpus_sha256: CFBDAB0C48709730551DC0C979A6089B5430C1D4B9A9088AA1596654B88321C4
---

# RE Baseline Compendium — Charter

## Purpose

Convert a nine-round reverse-engineering corpus (FounderOS, OpenMontage, Colibrì,
OSA Claude Code, HY-WorldPlay, Ghidra, Claude Institution, Fable Succession, LAAS)
into institutional infrastructure for Claude Power Pack — **without re-authoring
capability the stack already owns.**

## Non-goals

- No second knowledge graph, rule compiler, artifact gate, distillation pipeline,
  event bus, model router, or recovery engine. Each already has a canonical owner.
- No frontend, dashboard, or connector architecture. PP has no such surface; the
  FounderOS pillar contributes its *principle* (a declared capability must be
  reachable from a real surface), which `liveness/reachability.py` already generalizes.
- No executable code inside dataset artifacts. Pseudoflows are natural language.
- No CommonWealth Ops vocabulary. The CW corpus is a depth benchmark, named only in
  planning files, never in a dataset artifact.

## Founding constraint (the reason this charter exists)

Phase 0 measured PP at 71 modules / 24 dataset families / 62 commands / 38 hooks /
322 tools / 1,101 graph coordinates. The corpus assumed roughly a dozen systems and
states in every round that it could not inspect this workspace. Approximately 55–60 %
of its proposed mechanisms are already owned at equal or greater maturity.

Therefore the compendium is organized **by verified gap**, not by source pillar.
A pillar contributes to whichever family owns the gap it exposes; several pillars
contribute to one family, and one pillar (Ghidra) contributes only extend material.

## The three NEW families

### CLAE — Closed-Loop Autonomous Engineering Laboratory
**Gaps closed:** G1 reference-delta engineering · G2 quality distance accounting ·
G3 anti-underbuild floors · G4 human oracle boundary · G5 observability-capable Phase Zero.
**Primary pillars:** LAAS (R-009), FounderOS (R-001, principle only).
**Thesis:** every PP gate today is binary and self-referential. It answers "did this pass
my own criteria?" and never "how far is this from an external bar, and what remains after
the pass?" CLAE supplies distance where the stack has only compliance.
**Boundary:** CLAE owns *measurement against an external reference and the loop that
closes on it*. It does not own scoring rubrics for a specific domain — `cdio` owns design,
`uqf` owns code quality, `sqi` owns its own index. CLAE generalizes their shared shape.
**Parts:** I–XXVI.

### CRPF — Cognitive Residency & Pressure Fabric
**Gap closed:** G6 cognitive residency physics.
**Primary pillar:** Colibrì (R-003).
**Thesis:** `executionos-lite` tiers the *task*; nothing tiers the *assets*. There is no
heat model, no promotion/demotion policy, no prefetch discipline, no admission control
contract, and no declared degradation order under pressure.
**Boundary:** CRPF owns *where a cognitive asset resides and what degrades first when
resources bind*. It does not own model routing (`cost_collapse`), context packs
(`graphify` GK-06), or hot/cold memory splitting (`memory-engine`) — it supplies the
physics those three consume.
**Parts:** I–XXII.

### IGEF — Institutional Governance Evolution Fabric
**Gaps closed:** G7 governance regression harness · G8 source-vs-deployed drift detection ·
G9 rule retirement engine.
**Primary pillar:** Claude Institution (R-007), gaps only.
**Thesis:** `rule_compiler` decides whether a rule is *admissible*. Nothing decides whether
a rule change was an *improvement*, whether the deployed copy still matches the source, or
whether a rule has outlived the incident that produced it. A corpus of 156 rules that can
only grow is a corpus that will eventually be ignored.
**Boundary:** IGEF explicitly does **not** contain a rule placement compiler.
`rule_compiler/schema.py` owns placement and admission. IGEF owns *evolution*: effect
measurement, deployment fidelity, and retirement.
**Parts:** I–XX.

## The five EXTEND passes

Parts appended to existing sealed families. No new family is created; each pass names its
target family's index and registers there.

| Pass | Target | Pillar | Adds |
|---|---|---|---|
| **E1** | `fable_distillation` | R-008 Fable Succession | G10: student *execution* trials, negative-transfer detection, model succession registry, retirement eligibility. FD proves portability of judgment; it never makes the student do the work. |
| **E2** | `session_resilience` + `session-continuity` | R-005 HY-WorldPlay | Reconstituted operational context, remote-anchor registry, bounded-horizon execution, drift measured at every handoff. |
| **E3** | `graphify` + `d2a_fabric` + `crawl_os` | R-006 Ghidra | Resource-adapter conformance, evidence-overlay layering (source fact / inference / annotation / conclusion), confidence propagation, dependent-conclusion invalidation. |
| **E4** | `contract_fabric` + `one_shot` + `karimo-harness` | R-002 OpenMontage | Unified mission manifest, inter-stage artifact contracts, append-only decision genealogy with explicit supersession. |
| **E5** | `daemon` + `zero-crash` + `session_resilience` | R-004 OSA | Semantic recovery contract (supervision is not recovery); wiring of the acceptance arbiter that `reachability.py` documents as unreached. |

## Reference-only ledger (analyzed, deliberately not built)

FounderOS operator dashboard and connector honesty · Ghidra decompiler and p-code format ·
HY-WorldPlay visual world model and RL post-training · Colibrì MoE disk-streaming runtime ·
OSA reverse-engineered request signing and the full Claude Code port. Each is recorded with
the reason for rejection in its contributing family's Evidence and Provenance Index.

## Per-family required structure

Every family ships: Charter · Master Index · Part files (one Part per file) · Systems
Derived Catalog · Hard Rules Registry · Process Rules Registry · Traps Registry · Eval and
Benchmark Registry · Production Reality Gate Registry · Ontology and Glossary ·
Cross-Dataset Integration Map · Evidence and Provenance Index · Open Questions and Research
Frontier · Version and Evolution Ledger · Dataset Completion Report.

## Per-Part depth floor

A Part carries unique intellectual responsibility. Depth is achieved through mechanism
density, not restatement. A Part is rejected and rewritten when it exhibits: generic
consultancy prose · rhetorical repetition · lists without mechanisms · an engine with no
inputs, outputs, lifecycle or evals · cosmetic taxonomy · circular definition ·
architecture without contracts · rules without enforcement · depth simulated through
synonym substitution · CommonWealth Ops contamination.

Scoring per Part (compared against the depth of the read quality references): conceptual
depth · mechanism density · architectural specificity · evidence grounding · failure
coverage · evaluation coverage · production realism · interoperability · ownership clarity ·
non-redundancy · system-derived value · institutional compounding · usability by agents ·
usability by engineers · long-term durability.

## Construction order (dependency-derived)

1. **CLAE** — first. It supplies the measurement discipline (reference, delta, distance,
   floor, oracle) that the remaining families and every extend pass are scored against.
   Building it last would mean the rest were built without an external bar, which is the
   exact defect CLAE exists to fix.
2. **CRPF** — second. Its residency model is consumed by E2's reconstituted context and by
   E3's overlay layering.
3. **IGEF** — third. Its regression harness needs CLAE's distance accounting to answer
   "was this rule change an improvement?" with a number rather than an opinion.
4. **E1 → E5** — after the three families, in that order. E5 is last because wiring the
   acceptance arbiter is a runtime change and must be gated by IGEF's deployment-fidelity
   check.
5. **Integration spine · UKDL registration · eval suite · adversarial review · repair ·
   final verification · institutional writeback.**

## Approximate scale

CLAE 26 Parts · CRPF 22 Parts · IGEF 20 Parts · E1–E5 approximately 24 Parts combined.
Order of 90–110 Parts. Multi-session by construction; continuity is governed by
`RE_BASELINE_RESUMPTION.md`, updated after every sealed Part.

## Completion definition

The compendium is complete when every family holds its full required structure, every Part
clears the depth floor, the contamination gate returns zero hits, UKDL carries the full
rule lineage, adversarial review findings are repaired, `RE_BASELINE_COMPENDIUM_SEAL_REPORT.md`
exists with observed counts, and no dataset artifact contains executable code.
