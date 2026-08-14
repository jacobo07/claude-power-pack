---
title: Intent-Verified Done — close the gate at the end, not only at the start
date: 2026-08-14
covers: [intent_verified, intent_verifier, done_gate, intent-fidelity, criterion-join]
tier: 2
status: PLAN — STOP #1, awaiting Owner decision
---

# Intent-Verified Done

Audit: `vault/audits/DONE_GATE_AUDIT.md`. Measured state: 0 of 58 gate
surfaces read an intent artifact at close; 41 of 64 declared criteria are
verified once by hand and never again.

## 1. Two of the three stated problems are already solved

The proposal named three problems. Checking each against the repo before
designing changed two of the answers.

**Problem A — the intent must be available at verify time.** Solved.
`vault/specs/*.md` persists it; `covers:` front matter binds it to a task;
`modules/sdd_os/spec_binding.find_bound_spec()` resolves task to spec today.
A new Intent Document schema would be a second copy of a working artifact,
and the second copy is the one that goes stale. **Do not build it.**

**Problem B — the comparison must be mechanical.** Solved in form. The
Owner's specs state criteria as V-gate ids, and a V-gate id is a falsifiable
predicate: satisfied when a test emitting it is observed to pass. What is
missing is the lookup, not the predicate.

**Problem C — intent can be partially satisfied.** The vocabulary already
exists and is sealed. CLAE Part 27 §6 defines `DONE_VERIFIED`,
`PARTIAL_VERIFIED`, `EVIDENCE_INCOMPLETE` and `BLOCKED`. Part 27 §5 defines
the admissibility rule this verifier needs: an objection is admissible only
when it names the mission's declared intent, the external reference, or a
registered trap. Everything else is inadmissible by construction. **Adopt
these names; do not mint new ones.**

So the deliverable is not a system. It is a **join and a ledger**: one module,
one gate row.

## 2. Design

### 2.1 The criterion

Discovered from the bound spec's acceptance section, never from a curated
list. A criterion is `(id, assertion, critical)`.

`critical` defaults to **true**. A criterion is nice-to-have only when its row
is explicitly marked advisory. Defaulting the other way makes a forgotten mark
fail open, which is how a criterion silently stops blocking.

### 2.2 The join, in two tiers

`resolve` (static, milliseconds) — for each criterion id, find the executable
files that emit it. Three outcomes, matching the audit: SATISFIED-REACHABLE,
UNJOINED, UNVERIFIABLE.

`observe` (dynamic, bounded) — run the owning file and parse its output for
that id's PASS. This is the only step that produces evidence rather than a
claim; `resolve` alone proves an owner exists, which is exactly the weaker
statement the audit found everywhere else.

### 2.3 The verdict

| Verdict | Condition |
|---|---|
| `DONE_VERIFIED` | every critical criterion observed passing |
| `PARTIAL_VERIFIED` | every critical criterion passes, some advisory one does not |
| `BLOCKED` | a critical criterion resolves to an observed failure |
| `EVIDENCE_INCOMPLETE` | a critical criterion is UNJOINED or UNVERIFIABLE |
| `INTENT_NOT_CAPTURED` | no spec binds this task — reported, accumulates, does not block |

`EVIDENCE_INCOMPLETE` is deliberately distinct from `BLOCKED`. "I could not
check it" and "I checked it and it failed" are different claims, and collapsing
them is how a gate teaches people to route around it.

### 2.4 Two anti-gaming constraints, from this repo's own scar tissue

**Never gate on a ratio.** The blocking condition is an absolute: the count of
critical criteria not observed passing must be 0. A percentage is satisfied by
deleting criteria.

**The criterion set is a named ratchet.** A baseline records the criterion ids
per spec. A criterion that disappears from a spec is reported as `WITHDRAWN`
by name, never silently absorbed into a smaller denominator. This mirrors
`vault/governance/mutation_ratchet.json`, which the repo already trusts.

## 3. Relation to existing systems — no overlap

| System | Its question | Why this is not it |
|---|---|---|
| `spec_gate` / `sdd_os.pre_exec_gate` | does a spec exist before coding? | opens the loop; this closes it. Same artifact, opposite end |
| `modules/done_gate` (artifact gate) | did the promised artifact land on disk? | the RIGHT artifact vs SOME artifact. Composes: run the artifact gate first |
| `output_contracts` (OQS) | is the output well-formed and slop-free? | quality of the output, not fidelity to the request |
| SQI / CDIO | is it good? | quality; this is fidelity. Disjoint |
| `one_shot.lock.fidelity_score` | did we touch out-of-scope files? | scope fidelity over FILE PATHS. This is criterion fidelity over BEHAVIOUR. The closest neighbour, and still a different oracle |
| CLAE Part 27 | doctrine of the prosecutor | this is its executable form for anchor 1 of 3 |

The nearest existing owner is `one_shot.lock`. It is not sufficient: it scores
path overlap, so a change that edits exactly the right files and implements the
wrong behaviour scores 1.0.

## 4. When intent is not formalizable

Three honest cases, each with a defined outcome rather than a silent pass:

- **No spec binds the task** — `INTENT_NOT_CAPTURED`. Visible in the report and
  counted in a standing debt file. Never blocks; a gate that blocks every
  unspecced task is disabled within a day, and a disabled gate governs nothing.
- **A spec binds but states criteria in prose** — `CRITERIA_NOT_MECHANICAL`.
  The verifier names the spec and the section. Converting prose to a V-id is a
  human act; the verifier will not invent a predicate.
- **A criterion is genuinely not machine-checkable** (a judgement, an
  aesthetic) — declared advisory in the spec, reported as epistemic debt,
  excluded from the blocking count and never from the report.

## 5. Minimum implementation

```
modules/intent_verified/
  criteria.py   parse a bound spec's acceptance section -> [Criterion]
  join.py       resolve + observe -> [CriterionResult]
  verdict.py    results -> Verdict (Part 27 vocabulary)
  ratchet.py    named-set baseline; WITHDRAWN detection
tools/intent_verify.py        CLI; exit 0 iff no critical criterion unobserved
tools/test_intent_verified.py V-gates for the above
```

One `verify_spp` row, `intent-fidelity`, running the resolve tier over every
spec plus the observe tier over the spec bound to the current task. The row is
declared in `vault/liveness/reachability_registry.json` so it cannot become
another module that imports cleanly and is never called.

The verifier's own spec is this file. Its acceptance criteria are stated as
V-ids, so it is the first subject of its own gate.

## 6. Acceptance criteria

Emitted by `tools/test_intent_verified.py`, reachable from the `intent-fidelity`
row of `verify_spp`. This spec is the first subject of its own gate.

| Gate | Asserts |
|---|---|
| `V-IV-CRITERIA-FROM-TABLE` | V-ids are read from a table acceptance section and collection stops at the next heading |
| `V-IV-CRITICAL-DEFAULT` | an unmarked criterion is critical |
| `V-IV-ADVISORY-MARK` | a row marked advisory is not critical |
| `V-IV-PROSE-NOT-INVENTED` | a prose acceptance section yields no criterion rather than a guessed one |
| `V-IV-FAIL-BEATS-PASS` | an id reported both PASS and FAIL resolves to FAIL |
| `V-IV-ID-FIRST-LAYOUT` | id-first / verdict-last rows are read; an unknown layout never reads as unobserved |
| `V-IV-ONLY-VERIFIERS-RUN` | only `test_*` / `verify_*` files are executed to collect evidence |
| `V-IV-ABSOLUTE-NOT-RATIO` | the blocking count is independent of the denominator |
| `V-IV-NO-RATIO-EMITTED` | no float value appears in an emitted verdict |
| `V-IV-NOT-CAPTURED-DOES-NOT-BLOCK` | an unbound task is visible debt, not a block |
| `V-IV-NO-CRITERIA-IS-NOT-DONE` | a bound spec naming no criterion cannot report DONE_VERIFIED |
| `V-IV-RATCHET-WITHDRAWN` | a criterion deleted from a spec is named, not absorbed |
| `V-IV-RATCHET-UNJOINED-BACK` | coverage lost on a still-declared criterion is a regression |
| `V-IV-RATCHET-REPAIR-ALLOWED` | debt falling by name is never a regression |
| `V-IV-UNVERIFIABLE-VS-UNJOINED` | no-emitter, emitter-outside-gate and emitter-in-gate are three distinct verdicts |
| `V-IV-TARGETS-FROM-SOURCE` | standing-gate targets are parsed from the real `verify_spp` row table |
| `V-IV-ABSENT-IS-NOT-PASS` | against real subprocesses, an id the owner never emitted is ABSENT |
| `V-IV-BLOCKED-ON-CRITICAL-FAIL` | an observed critical failure yields BLOCKED |
| `V-IV-EVIDENCE-INCOMPLETE-DISTINCT` | an unobserved critical criterion is EVIDENCE_INCOMPLETE, not BLOCKED |
| `V-IV-PARTIAL-ON-ADVISORY` | critical satisfied plus advisory unmet yields PARTIAL_VERIFIED |

## 7. Open decisions — STOP #1

1. **Standing scope.** Resolve-all + observe-bound-only (cheap, push-safe), or
   observe everything (accurate, adds the 41 unjoined tests to every push)?
2. **The 41 UNJOINED.** Adopt into `verify_spp` now and repair whatever fails,
   or baseline the current state as a named ratchet and ratchet it down?
3. **Tier 2+ without a spec.** `INTENT_NOT_CAPTURED` advisory, or blocking?
