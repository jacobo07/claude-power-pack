---
title: CPP-APIR — Dataset Architecture Plan
date: 2026-08-03
status: STOP #1 — BLOCKING. No dataset or module content is written until the Owner selects an option.
verdict: MAJORITY_OWNED (~80 %) — 0 of 6 proposed owners genuinely new; residue is one capability layer
---

# Dataset Architecture Plan

## 1. Verdict

| | |
|---|---|
| Datasets proposed | **25** |
| Owned at equal or greater maturity | **19** |
| Require extension of a named incumbent | **4** |
| Genuinely new, thin, contingent | **2** |
| Proposed owners genuinely new | **0 of 6** |
| Measured duplication | **≈ 80 %** |
| Source's own estimate of incumbent coverage | 55–65 % (**understated by 15–25 points**) |

**The 25-dataset corpus is refused.** Building it as written produces roughly 400k–600k words
re-narrating SQI, ACIS, CLAE, FD, D2A, CEPS, `crawl_os`, `sdd_os`, `liveness`, `cost_collapse` and
`rule_compiler` — the identical outcome CPP-ACI measured on 2026-07-12 and stopped for.

## 2. The residue, stated as one sentence

> Every registry in this estate is module-, skill-, or model-level. **None is capability-level**, and
> nothing specializes a capability per project beyond substituting nouns.

Three objects, one lifecycle, four consumers. By this estate's own bar — *a distinct object no
incumbent owns, more than one mechanism, more than one consumer, its own lifecycle, admission on a
measured sweep* — that is **a module family, not a dataset family**.

## 3. The four options

### Option A — Execution-first (RECOMMENDED)

Build the capability layer as code, and nothing else.

```
modules/capability_runtime/
├── contract.py       Capability Contract schema (DS03)
│                     triggers · anti-triggers · required evidence · consumers
│                     · activation cost · failure-risk-if-omitted · maturity
├── applicability.py  the multi-factor score + 8 verdicts (DS05)
│                     MANDATORY / RECOMMENDED / AVAILABLE_ON_TRIGGER /
│                     NOT_APPLICABLE / CAPABILITY_INSUFFICIENT /
│                     BLOCKED_BY_MISSING_EVIDENCE / BLOCKED_BY_UNRESOLVED_OWNER /
│                     REJECTED_AS_DUPLICATE
└── derivatives.py    parent · specialization delta · inherited vs overridden
                      contracts · upgrade path · staleness (DS07)

EXTENSIONS (no new owner)
├── setup_os/scanner.py            + graph emitters (DS02)
├── universal-meta-systems         + 6-component specialization map (DS06)
└── hooks/hook-dispatcher.js       + capability registration (DS08 wiring)

REGISTRATIONS
├── vault/liveness/reachability_registry.json   one entry per new module
├── vault/hard_rules/                            HR-APA-016 / -017 enforcement surface
└── NON_DUPLICATION_LEDGER.md                    routes all 19 owned rows to their owners
```

**Cost:** 3 modules + 3 extensions + 3 registrations. ~1 session.
**Doctrine:** ~1 index document, not 25 datasets.
**Precedent:** FIOS's STOP #1 refused 17 prose datasets describing engines that did not run; CCFL-PDPF
chose the same shape. The delta here is a schema and three executables.

### Option B — Execution-first plus a thin doctrine tier

Option A, plus **2 datasets** (~25k–30k words): the Capability Contract ontology and the applicability
decision doctrine. Justified only if the Owner wants the reasoning authored ahead of the code.
Everything else routes to the non-duplication ledger.

### Option C — Defer, and resolve CPP-ACI first

Build nothing. **CPP-ACI has stood at STOP #1 since 2026-07-12** with an approved architecture
(Foundations tier + Circulatory Fabric + Control Plane) and remains unbuilt. CPP-APIR's residue partly
depends on CPP-ACI's Tier-0 object registry. Two open STOP #1s on overlapping ground is itself a
governance defect. This option closes one before opening another.

### Option D — Full 25-dataset compendium

Explicit Owner override of the non-duplication finding, accepting ~80 % measured overlap as a
deliberate teaching corpus distinct from the runtime. ~500k–600k words, 8–15 sessions. The
non-duplication ledger becomes a traceability map rather than a do-not-build list.
**Not recommended** — nine consecutive precedents cut in the opposite direction.

## 4. If Option A or B is approved — build order

1. `NON_DUPLICATION_LEDGER.md` — the verdict on disk, before any code (SQI/DFP/USIRC model).
2. Settle the **DS13 / CDP provenance collision** (Ownership audit §3). One ledger, not two.
3. `contract.py` — the schema everything else consumes.
4. `applicability.py` — with the counterfactual and overlap-penalty terms.
5. `derivatives.py` — only after 3 and 4 have a real consumer.
6. `setup_os` graph emitters → `universal-meta-systems` specialization map → dispatcher wiring.
7. Liveness registration + `HR-APA-016`/`-017` enforcement surface.

**Done-gate:** `python modules/liveness/reachability.py` exits 0 with every new module reachable by a
named live surface. Not file existence — a V-gate with observed output. A module that lands
unreachable and undeclared fails the gate.

## 5. The single question for the Owner

The A–J re-verification of **2026-08-03 — today, this corpus** — already ruled on this residue:

> *"no capability-level (as distinct from module-level) registry exists — **low ROI, no failure
> attributable to it**."*

CPP-APIR supplies the missing half of that sentence: the KADOS fork session, in which the Owner
personally performed capability applicability and specialization reasoning across 22 candidates
because no PP surface performs either. That converts *no failure attributable* into **one failure
attributable**.

**Does one observed incident of the Owner acting as capability router justify building the capability
layer?**

That is the whole of STOP #1. This plan does not answer it, because answering it silently is how a
low-ROI verdict gets overturned without anyone noticing.

## 6. Blocking condition

No dataset content, no module content, and no registry entry is written until the Owner selects
**A**, **B**, **C** or **D**. Phase C (Constitutional and Registry Foundations) does not begin before
that selection.
