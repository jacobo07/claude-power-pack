---
title: SEIP Sprint 2 — the 8 EXTEND items, owners verified against HEAD
date: 2026-08-06
status: STOP #1 -- BLOCKING, presented inline, awaiting Owner selection
predecessor: vault/plans/seip-corpus-2026-08-04.md
head_at_verification: 9359b27
---

# SEIP Sprint 2 — STOP #1

The Sprint 2 instruction was: *"Verificar el owner real leyendo el modulo correspondiente."*
That verification is the whole finding. **Four of the eight EXTEND rows name an owner that
is a sealed prose dataset, not code.** One is already built. Only three are wiring tasks.

This is a softer relative of `T-FICTIONAL-OWNER-001`. In the SEIP source, ten named owners
did not exist at all. Here every owner exists — but four of them are *paragraphs*, and
"add a field set to X" is not a wiring task when X is a definition in a sealed `.txt`.
Executing those four as written would produce more prose describing capability, which is
the exact artifact class the audit series has struck twelve times.

## Verification table

| # | EXTEND | Owner as named | Verified at HEAD `9359b27` | Actionable |
|---|---|---|---|---|
| D3 | Predictive Defect Intelligence — P0–P3 ladder | `cascade_prevention/engine.py` | **CODE.** `CascadeHit` frozen dataclass (4 fields); `CascadeSeverity` C1–C5 IntEnum + `should_warn`/`should_block`. A severity ladder already exists. | ⚠️ Owner real; the *proposed* ladder is a duplicate of `CascadeSeverity` |
| D4 | Predictive Calibration Ledger — producer | `decision_review/accountability.py` | **ALREADY BUILT** by the concurrent pane, commit `e4e341b`: `modules/decision_review/outcome_recorder.py`, 351 lines | ❌ CLOSED — rebuilding would duplicate |
| E5 | Saturation, Closure & Reopening | crawl_os DS03 | **PROSE.** `vault/knowledge_base/crawl_os/crawl_os_03_*.txt`. No `modules/crawl_os` exists. | ⚠️ no code owner; and see below |
| G2 | Difficulty Vector — 12 fields | `BenchmarkScenario` | **PROSE.** `vault/knowledge_base/sqi/CANONICAL_ONTOLOGY.md` §1.9, 6 fields. **Zero code implements it** — grep over `modules/` returns nothing. | ⚠️ entity nothing produces |
| G4 | Benchmark Metascience | SQI §5 | **PROSE.** metrics contract | ⚠️ no code owner |
| G6 | Pareto Evolution | SQI §5 + `sqi_scs_c93` | **PROSE** + `tools/run_sqi.py` | ⚠️ thin |
| H3 | Governance Minimality | `hard_rules/residual.py` | **CODE.** `audit_corpus()`, `gate_new_rule()`, `classify_empty_class()`, `compile_residual()` | ✅ actionable |
| M2 | Epistemic Acceleration | FD-04 + ACIS | **CODE** `fd_04_contrast.py` + `fd_04_prover.py`; ACIS is scattered prose across 10 files | ✅ partially actionable |

## Findings that change the sprint

### 1. D4 is already done — by the other pane, this morning

`e4e341b feat(decision-review): DecisionRecord producer -- G4` shipped
`outcome_recorder.py` (351 lines). The producer gap that made
`accountability.py::calibrate` dead by starvation is closed. Sprint 2 must not touch it.

### 2. E5's residue was consumed by Sprint 1

E5 asks for "saturation, closure and reopening". `modules/sqi/ratchet.py` shipped a
saturation predicate on 2026-08-04 with a five-conjunct closure test and an explicit
reopen path (`NOT_SATURATED` → the bar still discriminates). The generic mechanism is
now owned by code. E5 as written would restate it in prose.

### 3. G2 names an entity that nothing implements

`BenchmarkScenario` is defined in the SQI ontology as the **evaluative asset** in the
four-asset chain every failure must yield. Nothing in `modules/` produces one, stores
one, or reads one. The audit proposes adding *twelve more fields* to it.

A six-field entity that nothing produces does not become more real with eighteen fields.
The Liveness Standard already names this: prose that nothing reaches is decoration. The
honest options are to make it executable or to leave it alone — not to enrich it.

### 4. A second STOP #1 transition producer now exists

Both panes independently built one, from the same sealed pattern, hours apart:

| | mine — `modules/owner_queue/stop_ledger.py` (`38b464b`) | sibling — `modules/backlog_autopilot/stop1_queue.py` (`7b47266`) |
|---|---|---|
| posture | **read-only, derived** | **writes the transition** |
| plans | never edited; `V-STOP-NEVER-EDITS-PLANS` hashes before/after | `resolve()` edits one front-matter key, Owner-authored |
| verdicts | OPEN / CONTRADICTED / RESOLVED, witness-based | RESOLVED / ARCHIVED / SUPERSEDED |
| count measured | 19 STOP-bearing plans, OPEN 7 | 15 open STOP #1 |
| stated rationale | rewriting a sealed artifact destroys the record of what was believed when | a resolver that rewrites the plan it resolves would destroy that evidence |

They cite **the same doctrine to justify opposite postures on whether a plan may be
edited**, and they report **different numbers for the same question**. This is a genuine
architectural conflict, not redundancy to be merged silently. It is the highest-value
item surfaced this sprint and it is not on the EXTEND list at all.

## Proposed Sprint 2, honestly scoped

**Build (3 commits):**

- **H3** — `residual.py` has `audit_corpus()` proving 156 prohibitions / 0 mandates, but
  nothing gates on minimality. Add a minimality probe: a rule that forbids no move the
  corpus does not already forbid is *redundant*, and `gate_new_rule()` should say so.
  Observable: a redundant rule is named as such where today it is admitted silently.
- **D3** — not a second ladder. `CascadeHit` carries severity but no *predictive*
  dimension: no lead time, no prior probability drawn from CEPS co-occurrence history.
  Add the predictive field(s) that `CascadeSeverity` provably does not encode.
- **M2** — FD-04 has `fd_04_contrast.py` + `fd_04_prover.py`. Wire an acceleration
  measurement over what already runs, rather than a new doctrine.

**Reconcile (1 commit):** the two STOP producers — one authority, or an explicit
documented split (derived read model vs. Owner-authored writer) with the conflicting
counts reconciled.

**Decline, with the reason recorded:** E5 (consumed by `ratchet.py`), G2 / G4 / G6
(prose owners; the change as written adds definition, not capability). D4 (already built).

## Why this is not scope reduction

The instruction was explicit: *"Si el repositorio no tiene 55 gaps genuinos, el resultado
correcto es N < 55. Honrar eso."* The same standard applied to Sprint 2's own list yields
**3 buildable of 8**. Building the other four would mean writing prose into sealed
datasets to satisfy a count — the failure mode this entire audit series exists to stop.
