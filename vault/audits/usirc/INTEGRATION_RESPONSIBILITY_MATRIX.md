---
title: USIRC STOP #1 — Integration Responsibility Matrix
date: 2026-07-31
rule: every row names a producer, a consumer and the surface that carries the handoff.
  A row with no consumer is not an integration — it is an orphan, and this estate has
  sealed that lesson three times (orphan module, orphan field, write-without-read).
---

# Integration Responsibility Matrix

## 1. If the residue is built: who calls whom

| # | Producer | Artifact crossing the boundary | Consumer | Carrying surface | Liveness class if built |
|---|---|---|---|---|---|
| 1 | crawl_os DS16 | composite authorization verdict | OSR mission start | module call | REACHABLE via the mission entry point |
| 2 | crawl_os DS10 | Evidence Objects with provenance and integrity | OSR-1 model population | module call | REACHABLE |
| 3 | OSR-1 | node and edge types for the observed product | `graphify` indexer | `modules/graphify/indexer.py` type registration | REACHABLE only once the indexer emits them |
| 4 | OSR-1 | the reference object (a qualified external reference) | CLAE Part IV/V | doctrine citation + a reference record | REACHABLE |
| 5 | `osa/gpu_eyes.py` | captured reference and build artifacts | OSR-2 | file paths, `visual_qa_passed=None` honoured | REACHABLE |
| 6 | OSR-2 | per-dimension observations, three-valued | DAIF-03 dimension gate | structured record | REACHABLE |
| 7 | DAIF-03 | PASS / DEGRADE / REFUSE | `done_gate` + `output_contracts` | existing gate path | already REACHABLE |
| 8 | OSR-2 | oracle verdicts | `modules/oracle` OVO aggregation | OVO protocol | REACHABLE |
| 9 | `tools/replay_harness.py` | ordered execution traces | OSR-3 | REPLAY_SCHEMA, extended event kinds | REACHABLE |
| 10 | OSR-3 | divergence position (which segment, which order) | `craif` investigation | CRAIF adapter, conformance-checked | REACHABLE |
| 11 | `craif` | closed investigation | `tools/bug_to_hardrule.py` → `rule_compiler` | existing path | already REACHABLE |
| 12 | OSR-L1 | one ordering gate | CLAE Part XXV gate set | rule registration | rule, not a module |
| 13 | any OSR finding | promoted insight | FD-03 router | existing path | already REACHABLE |
| 14 | OSR module set | reachability declaration | `modules/liveness/reachability.py` | `vault/liveness/reachability_registry.json` | the gate itself |

**Row 14 is the row that decides whether this is real.** `/liveness` exits 1 on a
module no hook, command, agent or tool-invoked-by-one can reach. Every row above must
be satisfiable *at merge*, not promised. CLASE 0 — "module built but not
auto-activated" — is this estate's single most-recurring error, and a reconstruction
runtime that ships unreachable would be an unusually expensive instance of it.

## 2. Who is responsible for each integration failing

| Failure | Owner of the fix |
|---|---|
| OSR starts without an authorization verdict | OSR (refuse to start); crawl_os DS16 keeps the verdict |
| Two evidence-custody records exist | OSR — it must not persist its own; DS10 is the record |
| A second graph appears | OSR — prohibited unconditionally |
| OSR publishes its own fidelity number | OSR — DAIF-03 §1.7 owns the metric |
| OSR investigates a cause itself | OSR — hand the position to CRAIF and stop |
| A finding promotes itself to a rule | OSR — FD-03 routes, `rule_compiler` places |
| A claim's status rises without evidence | ACIS invariant; DAIF-03 §4.5 refuses |
| The module ships unreachable | `liveness` gate, at merge |

## 3. If the residue is NOT built (Option A)

The matrix still has one live row, and it is the reason Option A is not "do nothing":

| Producer | Artifact | Consumer | Surface |
|---|---|---|---|
| This audit | the measured finding that the estate has **no rendered-artifact comparison instrument**, no external-product model, and no two-execution alignment | `vault/OWNER_QUEUE.md` | an Owner-queue entry per gap, each with a proposed owner and a recommended action |
| This audit | the KADOS premise failure, and the pattern that a source's inventory of PP is a hypothesis | `vault/knowledge_base/ukdl-universal.md` | one Trap entry |
| This audit | the ninth consecutive majority-owned corpus proposal | `COMPENDIUM_CLOSURE_REPORT.md` base-rate table | one row |

An audit whose only output is a verdict has no consumer either. These three rows are
what make this audit itself pass the standard it is applying.
