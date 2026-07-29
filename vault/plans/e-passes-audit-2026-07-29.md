---
title: E1-E5 — boundary audit against a discovered denominator (blocking, pre-construction)
date: 2026-07-29
status: STOP — verdicts delivered inline. No E-pass Part authored. No E-pass artifact exists.
scope: the five EXTEND passes of COMPENDIUM_CHARTER.md, approximately 24 Parts allocated
precedent: CRPF struck (vault/plans/crpf-2026-07-27.md) · IGEF struck (vault/plans/igef-2026-07-29.md)
obligation: RE_BASELINE_RESUMPTION.md block 3 — audit every E-pass boundary before building it
---

# E1-E5 — the boundary audit the charter never ran

## Denominator

**Discovered, not recalled.** Every `.py/.md/.txt/.js/.json/.ps1` under `modules/`,
`tools/`, `hooks/`, `commands/`, `agents/`, `vault/knowledge_base/`, `vault/hard_rules/`,
`governance/` and `rules/` — **1,371 files across 154 distinct families and packages**.
The same construction the IGEF audit used (1,364 / 152, grown by this week's commits).

Seventeen mechanisms were swept, one per capability the charter's E-pass table claims each
pass *adds*. Every hit was then verified by reading. **A hit is a lead, never an owner**,
and a high count is more often a noisy token than an owner — `manifest` returned 144 files
and owns nothing on its own.

## Verdicts

| Pass | Mechanism | Hits | Real owner (verified by reading) | Verdict |
|---|---|---|---|---|
| **E1** | student *execution* trials | 1 file (the charter quoting itself) | **FD-04 II.2 Step 2** — "re-execute the capability on the claimed target substrate", graded on Correctness/Robustness/Determinism of the *output* | **DO_NOT_BUILD** |
| E1 | negative-transfer detection | 2 | FD-04's **DEGRADED** verdict + `failed_lenses` + `highest_passing_substrate` — quality regression under downgrade, named per lens | **DO_NOT_BUILD** |
| E1 | model succession registry | 17 / 9 fams | FD-04 `highest_passing_substrate` · CO-03 routing · CO-12 dependence credit · `cost_collapse/router.py` | **EXTEND** — one record, not a Part-set |
| E1 | retirement eligibility | 3 | FD-05 anti-dependence arbitrage retires the frontier call; FD-04 supplies the evidence, FD-05 the policy | **EXTEND** — one predicate |
| **E2** | reconstituted operational context | 54 / 16 fams | DAIF-07, DAIF-08 Context Runtime, `cognitive_os/rehydration.py`, hibernation SCS C67, `SESSION_CONTINUITY_GOVERNANCE.md` | **DO_NOT_BUILD** |
| E2 | remote-anchor registry | 12 / 9 fams | `session_resilience/epoch.py` — pins the last topology recorded *while the session was alive*, idempotent across N panes | **DO_NOT_BUILD** |
| E2 | bounded-horizon execution | 63 (token noise) | CO-00 60 % ceiling · `one_shot/escalation.py` STOP_AT=3 · `process_governor.loop_advisory` (HR-STALLED-SESSION-ADVISORY-001) · Regla 12 | **DO_NOT_BUILD** |
| E2 | drift measured at every handoff | 6 / 5 fams | `modules/alert_escalation/policy.py` + `background_verifier_run.check_mirror_parity` — **shipped 2026-07-29 as IGEF Option A**, by this same effort, three days ago | **DO_NOT_BUILD** |
| **E3** | resource-adapter conformance | 3 | `CRAIF_D2A_REINFORCEMENT_PACKAGES.md` names **nine** missing adapters; no standing conformance check exists | **CREATE_MISSING** — small, one checker |
| E3 | evidence-overlay layering | 3 (2 are the charter) | **DAIF-01 Part VIII** — a ten-status Confidence lattice mapped onto ACIS E0-E7, carrying the cardinal rule *"an inference may never be typed as a fact"* | **DO_NOT_BUILD** |
| E3 | confidence propagation | 19 / 9 fams | `decision_review/epistemic_algebra.py` — `acis_max` (DRK-03 strongest-support join) / `acis_min` (weakest-link meet over a conjunctive evidence set); `graphify_11` route governor propagates the weakest link | **REPAIR_WIRING** — see below |
| E3 | dependent-conclusion invalidation | 65 / 23 fams | `daif_21_reality_sync` (128 occurrences), `graphify_06` stale-node handling | **DO_NOT_BUILD** |
| **E4** | unified mission manifest | 144 / 42 fams | `one_shot/compiler.py::OneShotContract` — frozen `scope · out_of_scope · done_gate · budget_usd · task_id` | **DO_NOT_BUILD** |
| E4 | inter-stage artifact contract | 6 / 5 fams | `done_gate/artifact_done_gate.py::ArtifactContract` — a stage NAMES its artifact and SHAPE; `verify()` reads real disk; MISSING is reported `NEVER_OBSERVED_TO_WORK` | **DO_NOT_BUILD** |
| E4 | decision genealogy + supersession | 105 / 39 fams | `crawl_os_10` Parts IX-X — change-history chains, one link per supersession, append-only, superseded objects never deleted; plus DAIF-01, FD-06, DRK-05 | **DO_NOT_BUILD** |
| **E5** | semantic recovery contract | 5 | `session_resilience/acceptance.py` (G4) — `AcceptanceCriteria · score_recovery · equivalence_verdict · classify → RECOVERED/PARTIAL/FAILED · acceptance_gate` blocking the "complete" claim, fail-safe to hold | **DO_NOT_BUILD** |
| E5 | acceptance-arbiter wiring | 26 / 17 fams | `tools/recovery_epoch_gate.py`, **2026-07-14**, wired at `hooks/session_start_hub.js:85` | **DO_NOT_BUILD — already shipped** |

**Fifteen of seventeen mechanisms are owned. Zero of five passes justifies its Part
allocation.** Two of the five founding claims are outright false, below.

## E1's founding claim is false

The charter states, as E1's whole reason to exist: *"FD proves portability of judgment;
it never makes the student do the work."*

FD-04's operating contract is a five-step transfer test whose **Step 2 is
"re-execute the capability on the claimed target substrate"**, capturing the raw output as
the candidate, then grading that output across six lenses — Correctness ("right answer,
right transformation, right constraint satisfied"), Robustness, Completeness, Fidelity,
Efficiency, Determinism-across-three-re-runs. The worked example runs a summarization
capability on Sonnet and on Haiku over five held-out transcripts and reports 4/5 root
causes correct on the smaller model.

That is the student doing the work, graded on the work. E1's premise describes FD-04 as it
was *not* built.

## E5 was closed twelve days before the charter was sealed

E5's second mechanism is, verbatim: *"wiring of the acceptance arbiter that
`reachability.py` documents as unreached."*

`tools/recovery_epoch_gate.py` was authored **2026-07-14**. Its own module docstring:

> *"`power_beacon.classify_startup`, `epoch` and `reentry` were reachable by no hook,
> command or task — so no interruption was ever detected and no restore was ever judged,
> which is precisely why an incomplete one was accepted in silence."*

That is the charter's gap, named in the repair's own words, and the repair is wired at
`hooks/session_start_hub.js:85`. `reachability.py` today reports
`session_resilience/acceptance` as **REACHABLE**; it is not in the unreachable set.

The charter was sealed **2026-07-26**. It chartered a pass to wire something the repo had
already wired twelve days earlier, and its Phase 0 did not see it.

## Root cause, unchanged across five audits

The charter's per-pass "Adds" column was written from a pillar's proposal, not from a sweep
of the target family. This is `PR-COVERAGE-BY-CONSTRUCTION-001` again — **the ninth measured
instance**, and the fifth consecutive corpus proposal to measure as majority-owned:

| Proposal | Measured overlap |
|---|---|
| AISHF | 75-80 % → became CRAIF |
| RE Baseline (literal A-J) | 55-60 % → became 3 NEW + 5 EXTEND |
| KSF | 70-80 % → 4-family residue |
| CRPF | ~80 % → struck |
| IGEF | 0 of 4 mechanisms → struck |
| **E1-E5** | **15 of 17 mechanisms → this file** |

The failure is never the pillar. Each pillar analyzed itself correctly; Colibrì's own D2A
map scored its context work EXTEND. The failure is a boundary column filled in from memory.

## The genuine residue

Small, and none of it is a Part-set.

- **R1 — `decision_review/epistemic_algebra` is ORPHAN.** The confidence arithmetic E3
  proposes to build already exists, decision-agnostic and fail-open, and **nothing can
  reach it**. Its own docstring records why it was written: three owners each held a piece
  of "how sure are we", a fourth site regex-parsed `E0..E7` to an int independently, and
  none held the arithmetic. Building E3's propagation Part would make that four sites.
  This is CRPF's G6 shape exactly — a wiring gap wearing a capability gap's clothes.
- **R2 — adapter conformance has no checker.** `CRAIF_D2A_REINFORCEMENT_PACKAGES.md`
  names nine distinct missing adapter/contract seams (liveness has no Repair Intent, SQI's
  replay is scoped to repository-state claims, DAIF-21's drift detection has no standing
  consumer, and six more). The catalogue is honest; nothing verifies conformance against it.
- **R3 — four `session_resilience` modules are ORPHAN**: `integration`, `multi_window`,
  `resume_identity`, `ui_state`. E2's and E5's target family carries unreachable code while
  the charter proposed appending Parts to it.
- **R4 — `modules/daemon/` holds zero `.py` files.** E5 names `daemon` as a target family.

## Recommendation

Not a decision. The decision is the Owner's.

- **A — Wire R1, audit R3/R4.** Smallest unit, and it removes the only mechanism in the
  seventeen whose *capability* is genuinely absent from the live surface.
- **B — Ship R2 as one conformance checker** inside CRAIF, which already owns the catalogue.
- **C — Strike E1-E5 as chartered** and close the RE Baseline compendium at CLAE 26/26 —
  the only family of the three that survived its own audit.
- **D — Build the passes as chartered.** Available, and it would author ~24 Parts over
  fifteen owned mechanisms and two false premises. Recorded, not recommended.

## Gates on this file

`V-NOCODE-01` — zero code fences. `V-CONTAM-01` — no CommonWealth Ops vocabulary; this is a
planning file and no E-pass dataset artifact exists. Every count is reproducible from the
paths named beside it. The sealed `COMPENDIUM_CHARTER.md` is **not** amended here.
