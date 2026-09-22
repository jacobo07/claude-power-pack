---
covers: [ucr_cif, prose_ownership, representation_neutral, normative_consumer,
         declaration, provenance_class, lineage, structural_projection,
         ownership_evidence, disposition_consumer, W11, governance_overlay,
         benchmark_leakage, oracle_separation, modality]
tier: T2
opened: 2026-09-22
---

# Spec: UCR-CIF W11 — a representation-neutral declaration channel

Supersedes nothing. Extends the structural family sealed by W9 (`STRUCTURAL_RANKING_ENABLED
= False`) and measured to a KEEP DISABLED — HARM verdict by W10 over the range
`af2bef0..8c39376`. Acts on action 1 of the frontier recorded at W10 close in §4 of the
resumption.

W10's verdict is not re-litigated here and its treatment is not re-run. This wave builds an
evidence channel and reports it. Whether any treatment is ever promoted is a separate
question with a separate identity.

## 1. The mechanism, measured rather than inherited

`ownership_evidence.build_structural_index` returns four channels. Two of them can promote a
candidate; both are unreachable for an owner whose authority is written in prose.

| channel | how a code owner earns it | how a prose owner earns it |
|---|---|---|
| `defined` — term-specific, promotes | `.py` AST symbol definitions; `.js`/`.ts` via `_DECL_RX` | **nothing.** `_DECL_RX` holds `.js` and `.ts` only, and the `.md` branch does not exist |
| `inbound` — owner-level, corroborates | Python `import` edges | **nothing.** A document cannot be imported |
| `named` | path words | path words |
| `registry` | JSON keys | JSON keys, if it ships any |

`.md` is scanned — `ALL_EXT` includes it — so a prose artifact contributes `owner_terms`
(bag of words, which is what the lexical family already reads) and filename words, and then
stops. It cannot declare. This is the mechanism behind `governance-overlay` holding 13.7 % of
its term-pairs structurally against a 21.0 % corpus average, and it is a property of the
extractor rather than of the owner.

## 2. The three candidate relations the frontier named, and why two of them are dead

The W10 frontier proposed reading "governance rule ids, document headings or front-matter
`covers:` keys as DECLARATIONS". Supply was measured against the one owner with a named,
mechanism-level defect behind it — `modules/governance-overlay`, 10 files — before any policy
was chosen, as W9 did for the structural family.

| candidate | supply in `governance-overlay` | estate-wide | verdict |
|---|---|---|---|
| `covers:` front-matter | **0 of 10 files** | 40 files carry it | **dead for this stratum** |
| headed rule ids | **1** (`MC-OVO-21`, in `pre-output.md`) | 28 files; `ukdl-universal.md` alone carries 260 | **dead for this stratum** |
| document headings | **148** across 8 markdown files | 1,061 markdown files scanned | abundant, and **forbidden alone** |

Two of the three named candidates have effectively no supply in the owner they were proposed
to repair. The third has abundant supply and is exactly what the mission forbids: a heading is
not authority, and a family that read headings alone would credit every README in the estate.

Recorded here because it would otherwise have been discovered after the extractor was built.

## 3. The relation that is not Markdown-equals-authority

Neither half of the pair is authority on its own. Composed, they are the prose analogue of
what a code owner already gets for free:

> A prose artifact becomes **declaration-capable** when a consumer outside it resolves a path
> to **that specific artifact** and treats it as contract. Its declarations are then read from
> its structured surface — headings, rule ids, `covers:` keys — never from its prose body.

An imported Python module defines symbols. A consumed contract declares headings. The
predicate is the same shape in both cases and never asks what the extension is, which is what
`REPRESENTATION-NEUTRAL` has to mean if it is to mean anything.

Real instances, measured, for `governance-overlay`:

| consumer | artifact | kind |
|---|---|---|
| `tools/mistake_frequency.py` | `mistake-frequency.json` | module constant, opened at runtime |
| `tools/council_verdict.py` | `council.md` | named as the doctrine it renders |
| `tools/test_completion_authority.py` | `core.md` | policy test asserting behaviour against the document |
| `tools/test_governance_overlay.py` | `core.md`, `mistakes-registry.md` | policy test |
| `commands/ovo-audit.md`, `commands/omni-verification-oracle-audit.md` | `council.md`, `post-output.md`, `mistakes-registry.md` | command contract |
| `modules/oracle/ovo-protocol.md` | `council.md`, `post-output.md`, `mistakes-registry.md` | protocol contract |
| `modules/executionos-lite/sovereign-feature-template.md` | `pre-output.md` | template contract |

The discriminator is inside the owner, not around it: on this evidence `during-task.md` and
`zero-issue-baseline.md` are named by nobody and earn no declarations, while sitting in the
same directory, with the same extension, under the same owner. A family that credited the
directory could not produce that split.

## 4. Provenance, and the leak this family would otherwise be

Ranked by raw inbound mentions, the top referrers of `governance-overlay` are the benchmark
and the adjudication that the signal is meant to be independent of:

| referrer | mentions | class |
|---|---|---|
| `vault/ucr_cif/oracle_cases.json` | **4,734** | BENCHMARK — the W10 answer key |
| `vault/ucr_cif/disposition_ledger.json` | 452 | W3's own adjudication output |
| `vault/ucr_cif/structural_projection.json` | 37 | this signal's own projection |
| `ownership_evidence.py`, `disposition_consumer.py`, `owner_truth.py` | 2–3 each | comments recording the W9/W10 measurement of this owner |
| `vault/audits/ucr_cif/07_W9…`, `08_W10…`, `UCR_CIF_RESUMPTION.md` | 3–6 each | wave reports |

A family that counted inbound references would have scored this owner overwhelmingly, from
its own answer key, and the result would have looked like a triumph. So every edge carries a
**provenance class** and only one of them promotes:

`CONSUMER` promotes · `SOURCE` is the artifact itself · `PROJECTION` is generated from a
source and never counts beside it · `CITATION` is a mention in a message or a path in a
config · `SELF_MEASUREMENT` is this mission's own prose about this owner · `BENCHMARK` is the
oracle and the ledger.

Classification is by provenance, not by a path denylist that a future reader has to maintain.

## 5. What may not change

- `STRUCTURAL_RANKING_ENABLED` stays `False` for the whole of signal construction.
- `MAX_OWNERS`, `DISTINCTIVE_MAX_HOLDERS` (3), `MAX_DISTINCTIVE_REQUIRED` (3) frozen.
  The cap is held constant so that treatment is isolated from truncation.
- `create_spec` untouched; corpus frozen; the 503 ABSTAIN and 218 UNRESOLVED stay open.
- `spec_depth_selection` stays an honest UNKNOWN.
- W9's treatment semantics and W10's KEEP DISABLED — HARM verdict remain reproducible. Any
  W11 candidate is a **new treatment identity**, never W9's with more data.
- The three foreign working-tree items are not mine and are not touched.

## 6. Mechanisms

**M1 — a typed edge extractor.** One pass produces, for each prose artifact, the set of
consumers that resolve a path to it, each carrying a provenance class and the source line.
Owner-level, term-free, and therefore unable to rank anything by itself.

**M2 — a declaration surface, gated by M1.** For an artifact with at least one `CONSUMER`
edge, headings, rule ids and `covers:` keys are split into terms and enter the existing
`defined` channel. No new channel, no new weight, no score. It reaches ranking only through
the inverse-holder sum W9 already computes, so the magic-number prohibition is satisfied by
construction and the monotonicity properties W9 relied on are inherited unchanged.

**M3 — lifecycle.** A superseded or deprecated artifact is declaration-incapable however
strong its declarations read. Historical authority is not current authority.

The signal ships **computed and reported, with ranking off**. A treatment arm exists only if
the signal passes §9, and it runs in shadow.

## 7. The claim this wave can and cannot make

A ranking-only change cannot move `P1-ANY-OWNER` precision, for the reason W9 stated:
re-ordering owners inside a firing selection leaves it byte-identical. W10 then measured that
aggregate resolution on this oracle is economically dead — ~28.9/31.8 points of uncertainty
against a ~3-point question, needing ~100× the available discordant pairs. That question is
closed and is not reopened here.

So the headline is **stratum-level and deterministic**: whether the eight known
`governance-overlay` movements recover, measured pre-cap and post-cap separately, with
code-form and mixed-form owners held as safety strata. A local result is reported as local.

If the family does not recover those movements, **W9's causal story is falsified** and that
is the finding. The signal is not strengthened until they move.

## 8. Freshness and blast radius

The edge set is compiled at the existing `structural_projection` build boundary and inherits
its binding check, source fingerprint, staleness states and `UCR_CIF_STRUCTURAL_DISABLE` kill
switch. No markdown scan, git walk or vault traversal on the selection path. A stale
projection degrades to *no prose contribution* — UNKNOWN, never refutation. This is safe
precisely because the channel is ranking-only while the flag is off; if a treatment is ever
promoted the source check becomes load-bearing and this spec is amended in the same commit.

## 9. Acceptance

- Supply measured and recorded before any policy constant is chosen. **Done, §2.**
- The two dead frontier candidates are recorded as a falsification, not buried.
- A real canonical prose authority earns declarations through a real consumer edge.
- A real non-authoritative prose artifact with overlapping vocabulary earns none.
- Source and generated projection do not count as two supports.
- Benchmark and ledger cannot reach the signal: driving the oracle to favour an owner leaves
  the production selector byte-identical.
- Superseded authority stops contributing.
- Editing a consumed artifact invalidates the projection; editing an unrelated README does
  not perturb it.
- `PR-W10-11` closed: the population fingerprint is driven against a deliberately drifted
  population, not merely computed and printed.
- Directed mutations sever the RELATION with both endpoints intact; the existing family stays
  ALL_CAUGHT.
- Common-path warm cost bounded and reported beside the build and refresh cost.
- Suites green: W9 29/29 and W10 38/38 are the pinned baseline.

## 10. Out of scope

Git history as an evidence family; test-count signals; new labels; corpus growth; the 503
ABSTAIN and 218 UNRESOLVED; re-enabling global structural ranking; `MAX_OWNERS`; FIOS
deployment; `CLAUDE.md`; and the other writer's tree.
