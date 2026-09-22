---
id: UACF-MISSION-002-RECORD
name: Mission 002 -- runtime dispatch, consumption, and what was not closed
type: mission-record
domain: uacf
status: PARTIAL
date: 2026-09-22
branch: feature/knowledge-acquisition
commits: [9e3b186, 7a99782, 2314257]
---

# Mission 002 -- record, seeds, and handoff

## 1. DS08 -- final disposition: SURVIVES, NOT REOPENED, and it was never what the handoff said

The mission brief stated that DS08 "reserved dispatch to `hook-dispatcher.js`"
and asked whether that reservation should be reopened. It was read, at
`vault/audits/apir/NON_DUPLICATION_LEDGER.md:22`:

> `hook-dispatcher.js` capability registration | DS08 | Wiring only

Three things follow, none of which match the brief:

1. The row is in the **permitted-extension** table, not the DO-NOT-BUILD table
   below it. DS08 is a classification that capability *registration* in the hook
   dispatcher is ordinary wiring rather than a novel system.
2. Its subject is **registration**, not invocation. It says nothing whatsoever
   about who may CALL a capability.
3. So there was nothing to reopen. The reservation stands, untouched, and the
   architecture built this mission is consistent with it: applicability stays
   hook-side (that IS the wiring DS08 covers) and invocation moved to the caller
   that holds the capability's input.

**The brief's version of DS08 was paraphrase drift** -- a boundary restated in
better-sounding words until it asserted something its source did not. That is
`PR-INHERIT-VERBATIM-NEVER-PARAPHRASE-001` (seed S5, from Mission 001) recurring
at the HANDOFF boundary rather than at a contract boundary. Had the reopen been
performed on the brief's wording, the session would have spent itself relitigating
a decision the ledger never made.

## 2. What the measurement changed about the architecture

The decisive evidence was not doctrinal. `SurfaceContext` carries eighteen typed
product-constraint fields (`context.py:63-101`); a `UserPromptSubmit` payload is
a prompt string. **The hook cannot build the input**, so it cannot be the
invoker -- not because a rule forbids it, but because the input contract makes it
impossible. Reinforced by failure-domain doctrine: that chain is already measured
at 15,173 ms against a 15,000 ms ceiling with total stdout loss, and
`gsd_x_tier.js` runs at `timeoutMs: 8000`.

The consumer was then chosen the same way -- by asking which stage HOLDS product
constraints. Exactly one does: KARIMO's PRD baseline. Both of its renderers are
pure functions of that baseline and one of them is what the live sentinel emits,
so consumption reaches the running system rather than a CLI nobody invokes.

## 3. Universal iteration protocol -- applied, not cited

`iteracion-avanzada-universal.txt` was read (6,862 bytes) and run against the two
non-trivial defects of this session.

### Defect A -- KARIMO G2 DETERMINISM broke

* **FASE 1 REALITY CHECK.** Source read: `enrichment.decisions_for_artifact`.
  Exact error: `[FAIL] G2 DETERMINISM: CHECK FAIL: non-deterministic parse`.
  False premise detected: **yes** -- "an added key is inert". It was not; the
  entry carried `at`, a microsecond UTC stamp, so two parses of one PRD differed.
* **FASE 2 CLASE 2** (plan assumed a repo state that was false). The parser's own
  docstring says `blueprint_from_baseline()` is a PURE function of S4 output and
  its CLI ships `--check` for determinism. The contract was written down in the
  file I had already read; I did not carry it into the change.
* **FASE 3 FIX** -- in the core, not the surface: the volatile field was removed
  from the persisted entry rather than the gate being relaxed. Three lines.
* **FASE 3 DONE-GATE, real output:**
  `[PASS] G2 DETERMINISM: CHECK OK: deterministic + pure-blueprint + jsonschema OK (sha=0f5473a4caeb)`
  followed by `=== ALL GATES PASS ===`, exit 0. Removing the field is also what
  proves causation.
* **FASE 5 CROSS-PROJECT: yes.** Any content-addressed or determinism-checked
  artifact in any repo.

### Defect B -- the call counter measured the wrong module

* **FASE 1.** Exact symptom: `FAIL V-INV-FOUR-OUTCOMES: RECOMMEND: capability not
  entered`, on a record simultaneously reporting `status=INVOKED` with the
  correct outcome. Source read: `resolve_entrypoint`. False premise: **yes** --
  "the script and the imported module are the same module".
* **FASE 2 CLASE 4** (instrument failed silently). It is an INSTRUMENT failure,
  and the classification matters: read naively it says the seam never calls
  anything, which is precisely the defect the gate exists to detect.
* **FASE 3 FIX** -- bind both module names to one list object.
* **FASE 3 DONE-GATE, real output:** `INV_PASS=13/13 threshold=13/13`, exit 0.

### Defect C -- a gate denied me twice, and the second denial was the signal

`HR-SECRET-001` denied two Edits: *"detector timed out (host likely starved) ...
an unenforced secret gate must not become permission"*. Host measured at 8.1 %
free. First denial: retried once, succeeded. Second denial, same shape: **pivoted
tool path** rather than retrying, per the two-consecutive-failures law. No UKDL
seed -- host starvation is already recorded in this estate's memory, and the gate
behaved exactly as designed.

## 4. FASE 4 -- seeds from this mission

Destination is this project vault, not `ukdl-universal.md`, for the reason given
in `UACF-UKDL-ADJUDICATION.md` section 0: a live writer is inside that file. The
iteration protocol explicitly permits the active project's vault.

### T-ENRICHED-ARTIFACT-MUST-STAY-A-PURE-FUNCTION-001 -- trap

**Trap:** attaching a decision to a derived artifact silently makes it
non-deterministic, because the natural thing to attach carries a timestamp. The
record of a RUN and the record of a DECISION look alike and are not: `at` and
`elapsed_ms` are facts about the run.
**Fix:** an artifact derived from an input must be a pure function OF that input.
Run-facts stay on the in-memory record where a log can have them, and out of
anything content-addressed or determinism-checked. Attach after the hash is
computed, so an artifact that gains nothing stays byte-identical.
**Corollary:** do NOT re-pin determinism in the new gate -- KARIMO G2 already owns
it and is stricter, and a looser duplicate can disarm a stricter drill while every
suite stays green.
**Evidence:** commit `2314257`; caught by the consumed stage's own done-gate.
**Cross-project:** yes.

### T-SCRIPT-AND-IMPORT-ARE-TWO-MODULES-001 -- trap

**Trap:** a test whose entrypoints point back at itself holds two module objects
-- `__main__` and the dotted import -- with two copies of every global. A call
counter then reports "never entered" for a call that demonstrably happened.
**Fix:** bind both names to one object before asserting, or keep the sentinel in
a module that is only ever imported. More generally: when a counter and a status
field disagree, suspect the counter's IDENTITY before the subject's behaviour.
**Sibling:** S7 in the adjudication (`sys.modules` registration for
`spec_from_file_location`). Same family -- a module loaded under two names is two
modules.
**Evidence:** commit `7a99782`.
**Cross-project:** yes.

### PR-VERIFY-THE-LEDGER-ROW-NOT-THE-HANDOFF-001 -- process rule

**Rule:** a handoff's description of a prior decision is a paraphrase until the
row is read. Before reopening, honouring or overriding a recorded decision, read
its ORIGINAL row and quote it.
**Evidence:** this mission was briefed to reopen DS08 as a reservation of
dispatch to `hook-dispatcher.js`. The row says "capability registration --
Wiring only", in the permitted-extension table, and is not about invocation at
all. Acting on the paraphrase would have relitigated a decision that was never
made.
**Relation:** this is `PR-INHERIT-VERBATIM-NEVER-PARAPHRASE-001` at the handoff
boundary rather than the contract boundary; promote as a sibling, not a duplicate.
**Cross-project:** yes.

## 5. Evidence rungs actually reached -- and NOT reached

| claim | status | evidence |
|---|---|---|
| DISCOVERABLE | held | contract in the registry, pre-existing |
| **CALLABLE** | **PROVEN** | V-INV 13/13; real on-disk contract -> real resolver, `outcome=UNDETERMINED exit=22`; mutation to 10/11, SHA-verified restore |
| **CONSUMED** | **PROVEN** | V-CON 11/11; decision reaches `constraints_block` (the live sentinel's own output) AND `BLUEPRINT.md`; mutation to 5/11 |
| applicability / non-pollution | PROVEN | batch PRD -> `not_callable`, reason recorded, no vocabulary leaked |
| INHERITED | **NOT REACHED** | one artifact kind is wired; `baseline_guardian` still has no automatic invoker |
| PRODUCT-EXERCISED | **NOT REACHED** | no real product build has consumed a decision |
| PRODUCTION-REALITY | **NOT REACHED** | no production environment exists for this |

The ladder is not projected upward. CONSUMED in a live code path is not
PRODUCT-EXERCISED, and this record does not let the two collapse.

## 6. What was NOT done, and why

* **Slice 4, baseline inheritance.** Not started. The canonical owner is
  identified and is better than the brief assumed:
  `tools/test_baseline_inheritance.py` already walks PRESENT -> REACHABLE ->
  ACTIVATED -> **EFFECTIVE** and pins the inheritance CHAIN. `baseline_guardian`
  is reachable only from `tools/run_sqi.py` and its tests -- no hook -- so
  inheritance still depends on someone remembering a CLI. **Extend that gate; do
  not build a second one.**
* **Slice 5, PRG evidence monotonicity.** Not started.
  `PR-SKIPPED-INSTRUMENT-MUST-DROP-THE-RUNG-001` is adjudicated and awaiting the
  canonical write.
* **Slice 6, adversarial matrix.** Partially done -- outcome classes, authority,
  kill switch, failure isolation, applicability and both renderers are driven.
  Not driven: duplicate invocation, replay, stale contract, stale specialization
  map, mixed-version peers.
* **Canonical UKDL write.** `DEFERRED-BY-CONCURRENCY`, measured twice.
* **A latent portability defect, found and NOT fixed** (out of scope, recorded
  so it is not lost): `prd_parser._validate` falls back to a required-keys-only
  structural check on `ImportError`, which enforces neither
  `additionalProperties:false` nor the `schema_version` const. On a host without
  `jsonschema` the same baseline validates differently. This host HAS jsonschema
  4.26.0, so the strictness relied on above is real here and conditional
  elsewhere.

## 7. Next task -- exactly one

Extend `tools/test_baseline_inheritance.py` so that UACF applicability is one of
the obligations it walks to EFFECTIVE, and give `baseline_guardian` an automatic
invoker at the same boundary the PRD stage now uses. Drive the red branch by
deleting the obligation and requiring the gate to fail.

**Start from:** `modules/capability_runtime/enrichment.py` (the generic boundary
-- a second artifact kind needs no new mechanism), `tools/test_baseline_inheritance.py`
(the four-rung ladder), and `modules/sqi/baseline_guardian.py` (the orphan).
