---
title: CCFL-PDPF STOP #1 — Proposed Family (the genuine residue)
date: 2026-07-31
status: AWAITING OWNER APPROVAL — nothing below is built
scale: 1 small family (or 4 modules + 1 extension pass), not 35 datasets
---

# Proposed Family — CDP (Cognitive Decision Provenance)

## What survived, and why it is one family and not thirty-five

Of 35 candidates, 26 are owned at equal or greater maturity, 3 are extensions to existing
owners, and 4 are genuinely absent. The 4 share one root: **the estate records what
failed, what it cost, and what rule was sealed — but never records the observable decision
structure that made the failure possible.** Every one of the four gaps is downstream of
that single missing record. That shared root is what makes them one family rather than
four unrelated builds.

Proposed name: **CDP — Cognitive Decision Provenance.**
Not "immune system" (IAS-D2 holds that name and object). Not "fabric". CDP owns one
object: *the auditable provenance of an agent's decisions, and the causal record joining a
decision to the failure it enabled.*

## Boundary (binding)

**CDP OWNS**
- the decision-provenance record schema and its writer
- the persisted per-incident causal lineage object
- the historical-family kill-rate instrument
- the cycle lifecycle object and its entropy controller

**CDP CONSUMES**
- CEPS events · `never_again_log` · `root_cause_taxonomy` classes (incident material)
- ACIS E0–E7 + `epistemic_algebra` (confidence — never its own scale)
- CLAE Part XXI (lineage doctrine — never re-narrated)
- DRK-04 (counterfactual — never forked)
- `sweep_enforcer` (sibling search — never re-implemented)
- CO-12 (the single telemetry instrument — CDP feeds it, never parallels it)

**CDP MUST NOT OWN**
- cross-project immunity, exposure, quarantine, propagation → **IAS-D2**
- the ensemble level → **CPP-IAS F1/F2**
- external evidence acquisition → **Crawl OS**
- insight-to-artifact routing → **FD-03**
- rule admission and placement → **`rule_compiler`**
- completion authority → **DAIF-07 / `done_gate`**
- any claim about private chain-of-thought → **prohibited outright**

## The four units

### CDP-01 — The Decision Provenance Record (G1)

The schema the estate lacks: per decision, `claim · claim_state · evidence · evidence_class ·
provenance · confidence(ACIS level) · assumption_introduced · alternative_rejected ·
source_consulted · source_available_but_unread · verification_run · verification_omitted ·
done_claim · runtime_outcome · contradiction · revision`.

Claim states and evidence classes are **adopted verbatim from the source document**
(`UNKNOWN → HYPOTHESIZED → INFERRED → PARTIALLY_SUPPORTED → VERIFIED_LOCALLY →
VERIFIED_EXTERNALLY → VERIFIED_IN_PRODUCTION → CONTRADICTED → INVALIDATED → SUPERSEDED`),
mapped onto ACIS E0–E7 rather than competing with it. The cardinal rule is already
executable: `epistemic_algebra.fact_grade_permitted` refuses to type an inference as a fact.

Deliverable: schema + append-only writer + a CO-12 signal. Not a new store — the record
lands beside `vault/ceps/events.jsonl` under the existing event discipline.

### CDP-02 — The Incident Lineage Object (G2)

A durable record per confirmed incident linking `environmental condition → cognitive
precursor → epistemic weakness → architectural misunderstanding → implementation decision →
missing validation → latent defect → propagation → symptoms → failed diagnosis → root cause →
prevention`, with the seven link types CLAE Part XXI already distinguishes (first cause,
enabling condition, propagation cause, detection failure, diagnosis failure, recovery
failure, governance failure).

Consumes CLAE XXI's doctrine; adds only persistence and the join to CDP-01 records.
Produces raw material for IAS-D2's fingerprints — it does not compute exposure itself.

### CDP-03 — Historical Family Kill-Rate Instrument (G3)

The one supreme metric the source names that has no instrument anywhere in the estate.
Derives representative mutants from real prior incidents (offset shift, width change,
semantic field swap, base-class omission, state cleared before read, stale instance
returned, silent tool failure, truncated context before critical evidence), executes them
against the current suite, and reports verdicts `KILLED · SURVIVED · UNOBSERVABLE ·
FALSELY_ACCEPTED · NON_REPRESENTATIVE · NEEDS_REALITY_TEST`.

Composes SQI's `weakening_detectors` and `redteam_protocol` as the detection layer;
adds the mutant corpus and the rate. Reports through CO-12.

### CDP-04 — Cycle Lifecycle and Entropy Control (G4)

The MegaCycle residue, deliberately small. A cycle object with states `OBSERVED → CANDIDATE →
CORROBORATED → EXPERIMENTAL → PROVEN → STANDING → CONSTITUTIONAL → DEPRECATED → RETIRED`,
a per-cycle scorecard (detection precision, action acceptance, defects prevented,
false-block rate, cost per useful intervention), and an entropy controller with the eight
operations `merge · specialize · compose · pause · demote · retire · replace ·
constitutionalize`.

**Explicitly not built:** a metabolic engine that owns execution routing, backlog
generation, or cross-project propagation. Execution routing is `owner_queue` +
`one_shot`; propagation is IAS-D2. The prohibition in the source document holds in both
directions — MegaCycle does not absorb CDP, and CDP does not become MegaCycle.

**Promotion gate note:** the proposal's demand that recurrence alone must not
constitutionalize is *already partly satisfied* — `rule_compiler` M4's live predicate is
risk-weighted. CDP-04 adds the retirement half, which is the genuinely absent one.

### CDP-05 (extension pass, not a unit) — The Negative Fixture Corpus

The ABI-layout case from the source document, preserved verbatim as the canonical negative
fixture: one root mechanism (`INFERRED_BINARY_LAYOUT_PROMOTED_AS_FACT`) producing five
downstream symptoms (dead input, absent Plus, wrapper returning zero, edge undetected, Hub
never opening), plus its nine derived latent-defect surfaces. Lands in the merged archetype
registry (E-1) as the worked example, and in CDP-03 as the seed mutant family.

## Depth contract if the Owner approves the family form

If built as a knowledge family, CDP follows the SQI/DAIF/Crawl OS convention already
proven in this estate: `.txt`, `PART I — TITLE` plain caps, numbered subsections, dense
prose, no headings/bullets/tables/fences inside the artifact, `PART N FINAL LAW` closing
every Part, floor 1,200 words per Part, a `DATASET_NN_CONTRACT.md` written *before* Part I,
and a hermetic V-gate suite (`tools/test_cdp.py`) extended per sealed dataset.

**Realistic scale: 4 datasets × 20–25 Parts, or ~90 Parts.** Alternatively — and this is
the recommendation — **CDP-01 through CDP-04 ship as executable modules with one doctrine
index**, following the FIOS precedent, because the delta here is code and a schema, not
prose. Writing 90 Parts describing four schemas that do not yet run would be the Scaffold
Illusion, and FIOS's own STOP #1 rejected 17 prose datasets for exactly this reason.

## What the Owner is actually choosing between

| Option | Scope | Cost | Risk |
|---|---|---|---|
| **A — Execution-first (recommended)** | 4 modules + 1 doctrine index + the E-1/E-2/E-3 extensions | Low | The schemas are real and testable on day one |
| **B — Family form** | 4 datasets × ~22 Parts + the extensions | High (~90 Parts, multi-session) | Prose describing components that do not run |
| **C — Extensions only** | E-1, E-2, E-3; defer CDP-01…04 | Lowest | G1–G4 stay open; the estate keeps recording *what* failed and never *why the decision was possible* |
| **D — Build the 35-dataset corpus as specified** | ~700+ Parts | Very high | Measured 83 % duplication against a discovered denominator; seventh consecutive majority-owned proposal |
