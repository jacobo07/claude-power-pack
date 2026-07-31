---
title: USIRC STOP #1 — Boundary Contract
date: 2026-07-31
status: proposed; binding only if the Owner approves Option B or C at STOP #1
---

# Boundary Contract

Written for the residue that survived the audit, not for the proposal as submitted.
If the Owner approves construction, these boundaries bind; if the Owner approves
Option A (record and close), this file stands as the record of where the line would
have been drawn.

## 1. What the residue owns

The surviving object is provisionally named **OSR — Observed System Reconstruction**.
It is not a civilization, a fabric, an operating system or a control plane. It is
three mechanisms and one law.

| ID | Owns | Does not own |
|---|---|---|
| **OSR-1** | A typed representation of an **external, third-party, observed** product: surfaces, states, transitions, contracts, invariants, failure modes, recovery paths, and the unresolved hypotheses attached to each | The graph substrate (`graphify`), the type discipline (DAIF-01 kinds and Strength), the epistemic status of any claim about it (ACIS) |
| **OSR-2** | Comparison of a rendered build against a captured reference artifact: geometry, structure, and temporal instruments, each emitting a three-valued verdict | The oracle protocol (`modules/oracle`/OVO), the fidelity metric authority (DAIF-03 §1.7), the design-quality judgment (`cdio`), the capture mechanism (`osa/gpu_eyes.py`) |
| **OSR-3** | Alignment of two executions to locate the earliest point at which they diverge | The causal investigation that follows (`craif`), the failure-mechanism taxonomy (`root_cause_taxonomy.md` CLASE 0–5), the cascade chain (`cascade_prevention`) |
| **OSR-L1** | The ordering law: a reached terminal state does not witness the sequence of prerequisite contracts that should have produced it | The Reality Contract, CLAE Part XXV gates, `liveness` reachability — OSR-L1 is a *specialization* registered against them, never a replacement |

## 2. Boundaries stated as prohibitions

Each is a stop condition, not a preference.

1. **OSR never stands up a second graph.** `graphify` owns the semantic IR
   unconditionally (`RE_BASELINE_RESUMPTION.md` block 3). OSR-1 contributes node and
   edge **types**, indexed by the existing indexer.
2. **OSR never defines a fidelity metric.** DAIF-03 absorbed the Metric-Authority
   candidate by Owner ruling. OSR-2 emits *observations* that DAIF-03's dimensions
   consume; it never publishes a fidelity number of its own and never averages across
   dimensions — DAIF-03 §1.2 prohibits averaging by name.
3. **OSR never acquires evidence.** `crawl_os` owns acquisition, provenance,
   integrity and authorization. OSR consumes Evidence Objects; a running-application
   adapter is **crawl_os DS05**, built inside that family, on that family's schedule.
4. **OSR never authorizes a reconstruction.** crawl_os DS16 adjudicates. OSR refuses
   to start without a composite authorization verdict from it.
5. **OSR never investigates a cause.** OSR-3 hands CRAIF an aligned divergence with a
   position; CRAIF owns candidates, evidence and closure. **The source's KADOS bridge
   is deleted — KADOS does not exist in this repo.**
6. **OSR never replaces the replay harness.** New event kinds extend
   `vault/forensic/REPLAY_SCHEMA.md`; the harness keeps its verdict vocabulary.
7. **OSR never rules on whether a dataset should exist.** `dataset_first` does.
8. **OSR never promotes a finding to a rule.** FD-03 routes; `rule_compiler` admits
   and places. No successor system may contain a second placement compiler.
9. **OSR never claims a status above what its evidence supports.** ACIS owns the
   ladder; a status that rises without new evidence is epistemic laundering and is a
   refusal, per DAIF-03 §4.5.
10. **OSR is domain-blind.** No console, no game, no vendor, no project name enters
    any OSR artifact (E11; `core.md` PATH RULE). Console-specific instrumentation
    belongs to the repo that owns that console.

## 3. The two-way contract with each neighbour

| Neighbour | OSR gives it | It gives OSR | Failure if the boundary is crossed |
|---|---|---|---|
| `crawl_os` | a declared evidence need, expressed as a mission requirement | Evidence Objects with provenance, integrity and an authorization verdict | Two acquisition engines with divergent provenance schemas; DS10's chain of custody stops being the single custody record |
| `graphify` | node and edge types for observed external systems | location, routing, coordinate identity | A second graph; every "where is X" query splits and neither answer is authoritative |
| DAIF-01/02/03 | per-dimension observations from OSR-2 | the type discipline, the CIR stack, the fidelity verdict PASS / DEGRADE / REFUSE | A second fidelity number; the estate acquires two authorities that can disagree, which is precisely what §1.7 forbids |
| CLAE | a concrete reference class (a running product) and new instruments for Part XIII | reference qualification, delta extraction, distance accounting, floors, oracle routing, closure semantics | A second measurement discipline whose distances are not comparable with CLAE's |
| `craif` | an aligned divergence with a temporal position | causal candidates, evidence sufficiency, closure | Two investigation records for one incident |
| `modules/oracle` / OVO | new oracle implementations conforming to the protocol | the protocol, the verdict aggregation | A second oracle protocol; OVO stops being the single verdict path |
| `omnicapture` | nothing | runtime truth about the build under test | A second telemetry plane |
| ACIS | claims with declared provenance | the E0–E7 status of every claim | Silent promotion of a hypothesis to a fact |

## 4. What this contract deliberately refuses to own

Recorded so a future session cannot quietly widen the boundary:

- **A personal assistant product.** Category J is a product build governed by PP under
  an SDD-OS T2/T3 spec, not PP doctrine. If the Owner wants it, it gets a spec and a
  repo — not thirteen dataset families here.
- **Console or emulator instrumentation.** Category L2. Another repo's domain.
- **Legacy migration and shadow execution.** Real techniques, no consumer in PP.
- **Design archaeology.** Genuinely absent, genuinely unowned, and with no consumer —
  which under `liveness` doctrine makes it a candidate for the Owner queue, not a build.
