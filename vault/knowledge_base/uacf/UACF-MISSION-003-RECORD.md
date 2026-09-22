# UACF Mission 003 — Cross-Artifact Baseline Inheritance

**Session:** 2026-09-22 · **Branch:** `feature/knowledge-acquisition`
**Started at:** `20725e8` · **Mission commits:** `1157d22`, `dee4efd`, `565d4f3`

Every load-bearing claim below carries an evidence class, because a handoff that
cannot be falsified quickly is a handoff the next session has to re-derive:

| class | meaning |
|---|---|
| **MEASURED** | established from repository or runtime evidence in this session |
| **DERIVED** | concluded from several measured facts |
| **NEGATIVE** | a specific search or inspection failed to find it |
| **HISTORICAL** | true in an earlier session, not revalidated at this HEAD |
| **UNVERIFIED** | carried for continuity, not independently checked |

---

## 1. Result

**Artifact genericity: DEMONSTRATED for two real artifact kinds.** `MEASURED`

A second real construction artifact (`design_md`) participates in the same
inheritance boundary. `modules/capability_runtime/enrichment.py` and
`contract.py` were **not edited** — asserted in code by
`V-INHERIT-BOUNDARY-CLEAN`, which reads an AST rather than grepping, and driven
red by its own control and by mutants M1 and M2.

**Claim the rung and no higher:** inherited across two real artifact kinds, with
a real consumer, adversarially mutation-verified. **Not** production-exercised —
no live PreToolUse hook invocation was observed, and no user-authored DESIGN.md
exists in this estate to have been reviewed. `MEASURED`

## 2. Predeclared falsifiers — none fired

| | falsifier | outcome |
|---|---|---|
| F1 | boundary gains design/capability knowledge | did not occur `MEASURED` |
| F2 | candidate selection branches on artifact | did not occur `MEASURED` |
| F3 | generic layer imports the design gate | did not occur `MEASURED` |
| F4 | design adapter is `prd_adapter` re-pointed | did not occur — it reads DESIGN.md's own prose and UX findings, and populates **fewer** context fields `MEASURED` |
| F5 | gate sees obligations only via test injection | did not occur — the real CLI on the real template shows it `MEASURED` |
| F6 | contract schema must change | **did not occur, and this was the live risk** — see §3 |

## 3. The architectural finding the handoff did not contain

**A `CapabilityContract` holds ONE `adapter` field, not one per input.**
`MEASURED` (`modules/capability_runtime/contract.py:137`)

`surface_architecture` already declared `inputs: ["measured product
constraints", "prd_baseline"]` against a single adapter. Appending `design_md`
to that list would have routed DESIGN.md artifacts into the **PRD adapter**.

Three ways out, and only one avoids falsifying genericity:

- branch inside the adapter on artifact shape → hides the join, F4;
- make `adapter` a per-input mapping → a change to the generic contract model
  made purely to admit a second artifact, **F6 by construction**;
- **a derivative contract** using the schema's existing `parent` genealogy
  field → no schema change, no boundary change. Chosen. `DERIVED`

Killing the derivative does not kill the parent; they are separate files.

## 4. What the mutation drill found that the tests did not

**M3 (sever the design adapter) left `V-INHERIT-DESIGN-REAL` GREEN.** `MEASURED`

An unreachable capability still produces an `InvocationRecord`, and a record
still has a key in the decisions dict. The gate asserted membership, so it
passed. Worse, the consumer's `capability_state` had three values and an
`else: inherited`, so a **broken** capability was reported with the word for a
**working** one — the unknown-as-yes defect, in code written an hour earlier,
invisible to every ordinary test because every ordinary test had a working
adapter.

Both repaired: a fourth state `unresolved`, rendered loudly and separately, and
the gate now asserts `status == "invoked"`. M3 reds it. `MEASURED`

> **Presence is not invocation.** A record proves a capability was *considered*,
> never that it was *entered*.

## 5. Instrument failures in this session, and what they cost

- **`ls -d` returned a path on GEX44 and I nearly recorded "GEX44 has a Power
  Pack checkout".** It is not a git repo and contains **none** of the subject
  files. `MEASURED`. Presence is not identity, at directory granularity.
  GEX44 (61 GB free, 20 cores, py3.12) is therefore **not** a usable verification
  host without a repo-transport path that does not exist. `NEGATIVE`
- **The mutation harness's restore was byte-different from its original.** v1
  read `utf-8-sig` and wrote `utf-8`, translating LF→CRLF. The SHA-256 check
  refused it and the drill **stopped**, which is the kill-switch working. The fix
  is not a cleverer comparison — it is to stop decoding: read bytes, splice
  bytes, write bytes. `MEASURED`
- **Two PowerShell→ssh quoting failures of the same shape.** Regla 12 pivot to
  the doctrine's temp-file route resolved it; re-tweaking the quoting a third
  time would not have. `MEASURED`

## 6. Handoff claims from Mission 002, adjudicated

| claim | verdict |
|---|---|
| HEAD is `db8e34f` | **CORRECTED** — HEAD was `20725e8` `MEASURED` |
| the boundary is generic | **CONFIRMED** `MEASURED` |
| `design-md` is the strongest second subject | **CONFIRMED** `MEASURED` |
| host ~3.8 GB after reaping | **SUPERSEDED** — 4.65 GB at session start `MEASURED` |
| `baseline_guardian` is a false owner | `HISTORICAL` — not re-inspected; nothing in this mission depended on it |
| `modules/sqi` holds no construction-obligation owner | `HISTORICAL` `NEGATIVE` — not re-swept |

## 7. Concurrency

`vault/knowledge_base/ukdl-universal.md` had **566 uncommitted added lines and a
12:47 mtime**, i.e. a writer live *during* this session. `MEASURED`

This record is therefore a **new file**, not an append to the shared corpus — a
pathspec-scoped commit of that file would have carried 566 lines of someone
else's work under this mission's message. The UKDL promotions in §8 are stated
here and deliberately **not** written into the shared corpus by this session.

`modules/design-md/*` is dirty but eight days stale — not a live writer, and
untouched. `MEASURED`

## 8. Lessons proposed for UKDL promotion — NOT yet written to the corpus

Deliberately unpromoted: the corpus has a live writer (§7). A future session
should merge these against existing doctrine rather than append duplicates.

- **T-PRESENCE-IS-NOT-INVOCATION** — asserting a capability appears in a
  decisions dict passes under a severed adapter. Assert the status.
- **T-ONE-ADAPTER-PER-CONTRACT** — a capability serving a second artifact kind
  needs a derivative contract, not a branching adapter and not a schema change.
- **T-RESTORE-THAT-RE-ENCODES** — a mutation harness that decodes and re-encodes
  rewrites the files it measures. Binary splice only.
- **PR-TWO-GENERICITY-AXES** — capability genericity and artifact genericity are
  orthogonal. Never report either as "generic" unqualified.
- **PR-DIRECTORY-PRESENCE-IS-NOT-IDENTITY** — extends the existing
  presence-is-not-identity rule to remote path probes.

## 9. Evidence

```
INHERITANCE_PASS=29/29   (was 20/20)   bracket STABLE
CON_PASS=11/11 · DESIGN_PASS=15/15 · EXPERIENCE_PASS=19/19 · KARIMO exit=0
MUTATION_CAUGHT=5/5      post_restore_exit=0    all restores SHA-256 verified
```

Real CLI, real template, real gate:

```
design_gate: APPROVE  (score=100)
  capability: surface_architecture_design_md -> invoked
              (DESIGN.md names an entry surface: ['onboarding'])
```

**Oracles were narrow and bracketed on the dirty-path SET.** `test_sqi` was
**not** run: it is wide, it starved the host in Mission 002, and it collects
another writer's untracked file, so it could not have produced an attributable
verdict. Estate-wide health is therefore **unmeasured**, and that is a gap, not
a pass. `MEASURED`

## 10. Open

- No production PreToolUse-hook invocation observed. `NEGATIVE`
- No user-authored DESIGN.md exists; the applicable subject is the canonical
  template and the declining subjects are authored fixtures. `MEASURED`
- A third artifact kind would test whether the derivative-contract idiom scales
  or whether per-input adapters eventually become the right model. `UNVERIFIED`
- GEX44 as a verification lane is unbuilt. `NEGATIVE`
