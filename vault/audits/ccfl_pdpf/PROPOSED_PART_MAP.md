---
title: CCFL-PDPF STOP #1 — Proposed Part Map
date: 2026-07-31
status: contingent on Owner selecting option A or B in PROPOSED_DATASET_FAMILY.md
---

# Proposed Part Map

Two maps, because the Owner is choosing between an execution-first shape and a family
shape. Neither is built. Both cover the same four gaps.

## Option A — execution-first (recommended) · 4 modules + 1 doctrine index

Precedent: FIOS, whose STOP #1 rejected 17 prose datasets on the grounds that
*"writing prose that describes an execution layer would re-narrate doctrine"* and shipped
4 engines plus one index instead.

| Unit | Artifact | Contract | Gate |
|---|---|---|---|
| CDP-01 | `modules/cdp/provenance_record.py` | the 16-field decision record; append-only writer; ACIS-mapped claim states; feeds CO-12 via `record_signal` | `V-CDP-RECORD-SCHEMA`, `V-CDP-ACIS-MAPPED`, `V-CDP-NO-PARALLEL-ACCOUNTANT`, `V-CDP-FAILOPEN` |
| CDP-02 | `modules/cdp/lineage.py` | the incident lineage object; 7 link types from CLAE XXI; joins CDP-01 records to a CEPS incident | `V-CDP-LINEAGE-LINK-TYPES`, `V-CDP-LINEAGE-JOINS-CEPS`, `V-CDP-NO-RENARRATE-CLAE` |
| CDP-03 | `modules/cdp/kill_rate.py` | mutant corpus derived from real incidents; 6 verdicts; composes SQI detectors; reports a rate to CO-12 | `V-CDP-MUTANT-FROM-REAL-INCIDENT`, `V-CDP-SIX-VERDICTS`, `V-CDP-COMPOSES-SQI`, `V-CDP-RATE-NUMERIC` |
| CDP-04 | `modules/cdp/cycle.py` | 9-state cycle lifecycle; scorecard; 8-operation entropy controller; proposes, never applies | `V-CDP-NINE-STATES`, `V-CDP-RETIREMENT-REACHABLE`, `V-CDP-PROPOSE-NEVER-APPLY`, `V-CDP-NO-EXECUTION-ROUTING` |
| index | `vault/knowledge_base/cdp/CDP_INDEX.md` | boundary, consumed owners, honest residuals | `V-CDP-BOUNDARY-DECLARED` |
| suite | `tools/test_cdp.py` | hermetic ×3, plus `V-BASELINE` (SQI, DRK, Crawl OS, D2A suites still green) | exit 0 |
| reach | `modules/liveness/reachability.py` | every CDP module REACHABLE or honestly declared | exit 0 |

Extensions E-1/E-2/E-3 ship as pathspec-scoped edits to `root_cause_taxonomy.md`,
`sweep_enforcer/rule_sweep.py`, and `backlog_autopilot/` respectively, each with its own
V-gate row.

## Option B — family form · 4 datasets, 88 Parts

Convention: SQI/DAIF/Crawl OS `.txt`, `PART I — TITLE`, ≥1,200 words/Part,
`PART N FINAL LAW` closing every Part, `DATASET_NN_CONTRACT.md` before Part I.

### CDP-01 — Observable Decision Provenance · Parts I–XXII

I purpose and the observable-exhaust boundary · II why aggregate telemetry cannot answer
"why was this possible" · III ontology and glossary · IV the decision record schema ·
V claim states and their transitions · VI evidence classes and their non-equivalence ·
VII provenance and the assumption register · VIII confidence, and why it is ACIS's scale
and not ours · IX the unread-source signal · X the omitted-verification signal ·
XI the DONE claim as a first-class object · XII runtime outcome reconciliation ·
XIII contradiction and revision · XIV the writer, append-only discipline, fail-open ·
XV the CO-12 interface and the no-parallel-accountant law · XVI storage, retention,
redaction · XVII query shapes · XVIII failure modes · XIX adversarial cases and record
gaming · XX metrics with anti-Goodhart countermetrics · XXI maturity levels ·
XXII worked example on the ABI-layout incident, and done criteria

### CDP-02 — Incident Causal Lineage · Parts I–XXII

I purpose · II symptom versus mechanism · III ontology · IV the lineage schema ·
V the seven link types · VI first cause versus enabling condition · VII propagation ·
VIII detection failure · IX diagnosis failure · X recovery failure · XI governance failure ·
XII joining lineage to the decision record · XIII joining lineage to a CEPS incident ·
XIV the five realities and their reconciliation · XV what CLAE Part XXI owns and this does
not · XVI what IAS-D2 owns and this does not · XVII lineage confidence and false links ·
XVIII failure modes · XIX adversarial cases · XX metrics · XXI maturity ·
XXII worked example and done criteria

### CDP-03 — Failure-Family Kill Rate · Parts I–XXII

I purpose and why coverage is the wrong metric · II mutants derived from incidents, never
invented · III ontology · IV the mutant corpus and its provenance · V structural mutants ·
VI semantic mutants · VII temporal mutants · VIII lifecycle mutants · IX environment and
build mutants · X agent-behaviour mutants · XI oracle mutants · XII the six verdicts ·
XIII adjudicating UNOBSERVABLE and NEEDS_REALITY_TEST · XIV composing SQI detectors ·
XV the rate, its denominator, and why a ratio is never the gate · XVI cost governance ·
XVII failure modes · XVIII adversarial cases and mutant gaming · XIX metrics ·
XX maturity · XXI interfaces to `done_gate` and CLAE XXV · XXII worked example and done criteria

### CDP-04 — Cycle Lifecycle and Entropy · Parts I–XXII

I purpose and the ranker-without-lifecycle gap · II why recurrence alone must not promote,
and what is already risk-weighted · III ontology · IV the cycle object · V the nine states ·
VI sensor, investigation and intervention classes · VII the constitutionalization gate ·
VIII the scorecard · IX demotion · X retirement, and retirement declared at creation ·
XI the entropy controller and its eight operations · XII composite cycles · XIII the
opportunity graph interface · XIV autonomy levels and what may never be automatic ·
XV failure policy by criticality · XVI what `owner_queue` owns and this does not ·
XVII what IAS-D2 owns and this does not · XVIII failure modes · XIX adversarial cases ·
XX metrics · XXI maturity · XXII worked example and done criteria

## Recorded as research, not built

**Open-model interpretability note.** Jacobian Lens and open-weight surrogates may, in
principle, be used to study internal correlates of premature convergence or assumption
promotion. This requires model weights, activations and a backward pass, and therefore
cannot attach to Claude Code. It is recorded here as a research direction with no
component, no interface, and no claim. Any artifact asserting access to Claude's private
reasoning is refused at write time.
