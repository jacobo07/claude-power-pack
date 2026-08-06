---
title: EGCC residue — Rc1 enforcement_level + Rc2 drift-family registry
date: 2026-08-06
tier: T2
status: APPROVED — Owner selected Option A at STOP #1 (2026-08-06)
covers: [egcc, rc1, rc2, enforcement_level, drift_registry, rule_compiler, binding_point]
audit: vault/plans/egcc-corpus-2026-08-06.md
---

# Spec — the only two EGCC residues that survived the ownership audit

EGCC measured 0 of 25. These are the two sub-dataset gaps that did not.

## Rc1 — a compiled rule cannot say WHERE it binds

**Problem.** `rule_compiler/schema.py::Rule` carries `severity` but no binding point.
A documentation-grade rule and a deploy blocker are indistinguishable in `rules_db.json`,
and `digest.py` cannot route by consequence. The source's HR-GOV-003 ("enforcement must
be declared") is correct and unowned — the single one of its eighteen rules that is.

**Scope.**
1. `Binding` enum: `ADVISORY · WARN · REQUIRE_EVIDENCE · BLOCK_BUILD · BLOCK_DEPLOY ·
   BLOCK_RUNTIME_ACTION · REQUIRE_HUMAN_AUTHORIZATION · EMERGENCY_STOP`, plus two
   non-value states: `UNDECLARED` (field absent) and `UNRECOGNIZED` (field present,
   value not in the ladder).
2. `Rule.enforcement: str` + `Rule.binding` derived property.
3. Parser aliases: `ENFORCEMENT`, `ENFORCEMENT_LEVEL`, `NIVEL`, `BINDING`.
4. `binding_coverage()` — absolute counts and named id lists.
5. One bounded digest line so the binding distribution reaches the agent.

**Out of scope.** Rewriting any rule to declare a level. Changing which rules bind.

### Non-negotiable constraints (each cites the defect it avoids)

- **`UNDECLARED` is NOT a rejection `Reason`.** 143 rules bind today and declare nothing;
  a new required field would inert the entire corpus — the disarmed-kill-switch shape
  from `enforcement_scs_c92.md`. Absence is reported, never enforced.
- **`UNRECOGNIZED` ≠ `UNDECLARED`.** A value the ladder does not know must not fall back
  to "absent", or an unrecognised idiom reads as zero and zero never falls
  (`feedback_zero_cannot_fall`).
- **Report absolutes, never a ratio.** A percentage of declared rules is satisfied by
  deleting undeclared ones (`feedback_never_gate_on_a_ratio`).
- **The digest budget is 4,096 B and currently spends 2,154 B.** The added line is a
  bounded distribution (≤10 entries), never an id list — the module's own measured
  reason for enumerating classes instead of ids. Budget re-measured after the change.
- **The field needs a consumer this session** or it is the orphan-field defect the audit
  itself named (`feedback_orphan_field_dead_recovery_path`). Consumers: `binding_coverage`,
  the digest line, and the V-gate.

### Acceptance criteria
- `V-RC1-LADDER` — every ladder value round-trips; case/whitespace tolerant.
- `V-RC1-UNDECLARED-NOT-REJECTION` — a rule with no enforcement field is still `valid`.
- `V-RC1-UNRECOGNIZED-DISTINCT` — `enforcement: "banana"` → `UNRECOGNIZED`, not `UNDECLARED`.
- `V-RC1-PARSE` — all four aliases parse out of a real archive body.
- `V-RC1-COVERAGE-ABSOLUTE` — coverage returns named id lists and integer counts, no ratio.
- `V-RC1-CORPUS-UNBROKEN` — compiling the live corpus yields the same valid count as
  before the change. **This is the regression gate**: a schema edit that silently changes
  which rules bind is the worst failure available here.
- `V-RC1-DIGEST-BUDGET` — digest ≤ 4,096 B after the change, measured.

## Rc2 — seven-plus drift detectors, no registry

**Problem.** `setup_os/drift_detector.py`, `sqi/baseline_guardian.py`,
`sqi/weakening_detectors.py`, `osr/compare.py`, `cpc_os/topology_reconcile.py`,
`liveness/`, `session_delta`, `sweep_enforcer` each detect drift and each work. No
artifact enumerates them, so coverage cannot be stated and a missing family is invisible.

**Scope.** One module that DISCOVERS detectors from disk and reports what it can witness.

### The epistemic constraint that shapes the design

A registry of drift *families* enrolled by hand measures memory, not reality
(`feedback_hand_curated_audit_measures_memory`, `PR-COVERAGE-BY-CONSTRUCTION-001`) — and
the EGCC source itself rejects its own 160-class list as bureaucracy that goes stale.

So this module **must not** claim to compute "uncovered families". A discovered sweep can
witness which detectors exist and which families they name; it cannot witness a family
nobody implemented. The module therefore reports three sets and says plainly that the
third is unknowable from discovery alone:

1. `detectors` — discovered from disk, authoritative.
2. `families` — the vocabulary the discovered detectors themselves use, authoritative.
3. `unclassifiable` — detectors naming no recognisable family. **This is the finding**,
   and it is falsifiable.

`uncovered families` is explicitly NOT emitted. A curated expectation list may be passed
in optionally and is labelled `CURATED — measures memory` in the output.

**Out of scope.** Building any new detector. Modifying any existing one. Any verdict that
a family is missing.

### Acceptance criteria
- `V-RC2-DISCOVERED` — detector set derived from a filesystem walk, no literal list.
- `V-RC2-FINDS-KNOWN` — the walk finds `setup_os/drift_detector.py` and
  `sqi/weakening_detectors.py` by discovery, not by name.
- `V-RC2-NO-UNCOVERED-CLAIM` — the report contains no "uncovered family" verdict.
- `V-RC2-CURATED-LABELLED` — an optional expectation list is labelled as curated.
- `V-RC2-EMPTY-IS-A-VERDICT` — a walk finding nothing reports `NO_DETECTORS_FOUND`,
  never an empty pass.

## Done-gate
`python tools/test_egcc_residue.py` → exit 0, every V-gate above asserted in both
directions, run 3× hermetic (same output each run — no global writes, no time window).
Plus `python -m modules.rule_compiler.compiler`-path corpus count unchanged.

## Rollback
Both changes are additive. Rc1: revert the three files; `enforcement` is an unused field
until the digest line reads it. Rc2: delete `modules/drift_registry/` — nothing imports it
but its own test and CLI.
