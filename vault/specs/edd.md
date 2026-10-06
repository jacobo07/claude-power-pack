---
title: Expectation-Driven Development (EDD) on GSD X
covers: [edd, expectation-driven-development, semantic-conservation, self-evolution-debt, decision-frontier, reference-frontier]
tier: 3
status: PROPOSED (Phase 1 output; no operator code exists yet)
parent: .planning/workstreams/edd/ROADMAP.md
evidence: .planning/workstreams/edd/OWNERSHIP_MATRIX.md
---

# EDD: Expectation-Driven Development

## Why
DONE must mean evidence-backed convergence between intent, expected reality and observed reality, not "tasks complete".
The ownership matrix (81 concepts) shows most of the closure machinery already exists in `modules/gsd_x`; what is missing is
the generator of unstated expectations and the closure-blocking classes that stop a defect closing as merely "fixed".
EDD extends GSD X. It adds no parallel Goal engine, obligation runtime, baseline system or verifier.

## PRD: what EDD adds (measured against the matrix)
| Addition | Matrix basis | Owner it extends |
|---|---|---|
| Semantic-conservation operators (purpose, authority, ownership, projection, temporal boundary, termination, restoration, cardinality) | C-09..C-11 DATASET_ONLY; the 4 operators DO-1..DO-4 are not state-shaped (`obligation.py:392-397`) | `modules/gsd_x/mission/obligation.py` operator pipeline |
| Mission-to-goal bridge for derived obligations | derived obligations and goal closure are disjoint pipelines (research A7; `store.save` refuses goal-bound roots, `convergence.py:accept_obligation` is manual-only) | new additive file `modules/gsd_x/goal/derived_bridge.py` |
| Self-Evolution Debt: product + factory obligation per defect, Earliest Preventable Point | C-39 PARTIAL, C-34 DATASET_ONLY; `FAILURE_DISPOSITIONS` has no factory disposition; `record_failure` has no production caller | `convergence.py` failure plane, as obligations (no `closure.py` edit) |
| Defect-triggered STALE propagation | C-33 PARTIAL: only fact-disappearance invalidates (`obligation.py:511`) | `invalidate_if_parent_gone` caller path |
| Decision Frontier: persisted blocking Decision Packets | C-48 PARTIAL: DRK registry exists, ESCALATE packet is runtime only | `modules/decision_review/decision_record.py` via a sidecar module, not a new registry |
| Reference Frontier dispositions | C-26 UNKNOWN: D2A is the candidate owner, callers untraced | `modules/duplicate_to_advantage` (to be traced in Phase 5 first) |
| Gold sets, sealed holdouts, V-EDD-BENCH | C-42, C-44, C-46, C-57 DATASET_ONLY | `tools/bench_gsd_x_reconstruction.py` pattern |

Nothing in the matrix is NEW: every concept resolved to an owner, a documented-only doctrine, or a dataset-only gap, which
matches the repo's base rate (HR-NOVELTY-001: 0 genuinely new in 22-30 prior proposals).
Rows the matrix could not settle (28, listed in `canary/RECEIPT.json` `unknown_rows`) are UNKNOWN, not passes.

## Architecture
1. Producer: new operators in a NEW file under `modules/gsd_x/mission/` emit `Obligation` (consequence, parents, operator,
   closure_condition) through `derive_from_facts` and `judge` (`obligation.py:454,478`). Identifiers must not collide with `DO-1..DO-4`.
2. Bridge: `derived_bridge.py` registers each ACCEPTED derived obligation as a `GoalObligation` with a plane and a pinned gate, so
   `goal_closure` (`convergence.py:323`) blocks on it. Single most important fact: today no code path joins the two pipelines.
3. Consumer: closure refuses on ACCEPTED/STALE/CANDIDATE obligations (`closure.py:228`); new debt classes ride as obligations.
4. Hazard: adding gating facts to `_READS` enlarges `required_facts` (`coverage.py`), so existing `FACTS.json` files that omit the
   new names become UNPRODUCED and BLOCK closure. Phase 3 must add facts as enriching, or ship a FACTS migration with a test.
5. Latent defect: `contract.py:205` reads `o.id` but the field is `identifier`; dormant until an operator sets `proof`. First dogfood
   item for Phase 4 and the Knowledge Vault.
6. Per-root mission completion effect (`capabilities/cpp-gsd-x-mission/capability.json:64`) is off by default and Windows-path bound:
   on GEX44 the goal path is the effective one; the ship:pre path is LAPTOP-ONLY.
7. Corpus partition: SkyParty post-incident material is the answer side; derivation code never reads it; holdouts hashed before Phase 3.

## Acceptance (V-EDD-* ids are PLANNED by phase; none passes today)
| Id | Phase | Criterion |
|---|---|---|
| V-EDD-BENCH | 2 | runner reports material recall, critical recall, precision, false-obligation rate, Founder-escalation precision; BEFORE baseline recorded |
| V-EDD-HOLDOUT-SEALED | 2 | holdout file hashes committed before the first Phase 3 commit |
| V-EDD-OPERATORS | 3 | each operator emits an `Obligation` with consequence and provenance; unproven ACCEPTED derived obligation makes closure REFUSE, passing Verdict closes it |
| V-EDD-BRIDGE | 3 | derived obligation appears in `goal_closure` blocking list |
| V-EDD-MUTATION | 3 | disabling an operator turns its benchmark subset red, restoring turns it green (`tools/mutation_drill.py`) |
| V-EDD-LIVENESS | 3-5 | `python modules/liveness/reachability.py` offender set is a subset of the recorded baseline |
| V-EDD-DEBT | 4 | defect yields product + factory obligation with Earliest Preventable Point; NEVER_CONSIDERED is not terminal |
| V-EDD-STALE | 4 | only causally affected SATISFIED obligations go STALE; an unaffected one stays SATISFIED |
| V-EDD-FRONTIER | 5 | blocking open Decision Packet refuses closure; answer recompiles and invalidates stale certificates; evidence-answerable unknown never reaches the Founder |
| V-EDD-REFERENCE | 5 | NOT_CONSIDERED on a material advantage refuses closure; SURPASSED needs a named oracle |
| V-EDD-INHERIT | 6 | a goal created after promotion inherits operators that passed 3 non-Minecraft holdouts without being told |
| V-EDD-DONE | 7 | each MISSION_PROMPT closure has a verdict with command and evidence; Production Reality for the KobiiCraft live server stays LAPTOP-ONLY, never PASS |

Phase 1 own gate: `python3 tools/edd_canary_gate.py` G2-G6, G9.

## Rollback
All EDD code lands in new files plus small additive edits, each its own pathspec micro-commit on `mission/edd`. Rollback is
`git revert` of that commit; operators are disabled by removing them from the operator tuple, and the `_READS` change is reverted
together with its FACTS migration. Peer-owned `tools/gsd_mission.py` and the Ralph supervisor are never edited. Universal promotion
(D-02) is written as a PROPOSED Decision Packet only and is never applied, so it needs no rollback.

## Decision provenance (Phase 1 criterion 4)
D-01 (execute on GEX44) and D-02 (promotion scope: GSD X default, universal waits for explicit y) are Founder decisions. The scan
found DRK (`modules/decision_review/decision_record.py:28`, 1 row today) as the canonical owner; `owner_override` is serialized but
never read. NOT YET WRITTEN in this unit: recording both as `DecisionRecord`s (idempotent by fingerprint) is an open item for the
next Phase 1 unit, so criterion 4 is not met by this packet.

## Conflicts observed
1. Mission says build EDD systems; HR-NOVELTY-001 (CLAUDE.md) requires 13-question proof and defaults to EXTEND. Resolved: zero NEW rows.
2. CLAUDE.md router and the capability manifest assume Windows paths and the laptop install; the mission executes on GEX44 and forbids
   touching the live install. The ship:pre gate is therefore unexecutable here (matrix C-75).
3. Global rule "plan-first / `/ultra` for multi-file builds" vs the mission's compiled-execution canary and the roadmap's execution
   mode; resolved by this spec being the written plan and Mode Selection (PR-MODE-SELECTION-001) choosing EXECUTION.
4. The mandatory iteration standard (`source/iteracion-avanzada-universal.txt`) was NOT read in this unit; conflicts with it are UNKNOWN.
   UKDL beyond the cited ids was not read either.
