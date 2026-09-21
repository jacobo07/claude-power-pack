---
covers: [ucr_cif, structural_projection, ownership_evidence, disposition_consumer,
         structural_evidence, attribution, orthogonal_evidence, W9,
         evidence_family, saturation, projection, freshness]
tier: T2
opened: 2026-09-22
---

# Spec: UCR-CIF W9 — a structural ownership evidence family

Supersedes nothing. Extends the single selector sealed by W5 (`bc260cb`),
consumed by two doors since W6 (`aace845`), and measured to its lexical
ceiling by W8 (`822e93e`). Acts on the frontier action recorded at W8 close in
`vault/audits/ucr_cif/06_W8_PRECISION.md` and in §4.1 of the resumption.

## 1. Why a threshold cannot fix this

W8 tightened the lexical clause and reported the result honestly: on the
identical 683 xl cases of a paired re-derivation, routing fell 99.6 % ->
93.9 %, mean owners 4.76 -> 3.98, owner slots -20.3 %, zero true positives
lost — and holdout precision did **not** move, 20.0 % -> 20.0 %. Sweeping the
bar showed routing cliffing 42 % -> 5 % between 3 and 4, against a corpus
whose median distinctive supply *is* 3. Headroom above the shipped setting is
zero, and that is a property of the evidence family rather than of the
threshold.

So this wave adds an orthogonal family. It does not tune anything W8 shipped.

## 2. The family that was measured and REJECTED first

The obvious candidate is "does the candidate owner structurally hold this
unit's evidence terms?", reusing `ownership_evidence.evidence_for`.

Measured over all 996 authoritative units: **996 / 996 = 100.0 %**.

That is not a strong signal, it is a **projection of W3's adjudication**.
`ownership_evidence.adjudicate` promotes a candidate to VERIFY exactly when
`attributing and distinctive_terms` holds, so every unit that reached
authoritative status carries the property by construction. It is constant over
the admitted population and therefore carries zero discrimination. The
non-authoritative rows sit at 14.9 %, which confirms the mechanism rather than
rescuing it.

Recorded here because it would have shipped as "100 % structural coverage".
Source and projection are not two confirmations.

## 3. The granularity that is not a projection

A prompt matches a **subset** of a unit's terms, and the adjudication never
saw the prompt. So the question that can still discriminate is per-term:

> for a term `t` that a prompt matched against a unit owned by `O`, does `O`
> structurally hold `t` — define a symbol named for it, carry a file or
> directory named for it, or register it as a key?

Measured over the 7,785 (unit, term) pairs of the authoritative corpus:

| | |
|---|---|
| owner structurally holds the term | **1,634 / 7,785 = 21.0 %** |
| restricted to corpus-distinctive pairs (what the selector ranks on) | **561 / 3,119 = 18.0 %** |
| pairs where NO ledger owner holds the term (pure prose) | 2,776 = 35.7 % |
| evidence terms held by some ledger owner | 674 of 1,498 = 45 % |

The two channels disagree on 82 % of the pairs the selector ranks by, so they
are orthogonal in fact and not only in name. Corpus-distinctiveness counts how
many owners' *documents mention* a term; structural holding asks whether an
owner *builds* it. A 20,000-character prompt supplies the first by
coincidence; it cannot fabricate the second.

The top structurally-unheld terms name the residual defect directly:
`failure` (143), `capability` (102), `institutional` (96), `evidence` (85),
`before`, `future`, `rather`, `human`, `architecture`. Corpus-distinctive
prose that passes W8's bar and contributes to `strength` while attributing to
nobody.

The error frontier agrees: `governance-overlay` holds **13.7 %** of its
term-pairs and `liveness` 13.0 %, against `capability_runtime` **43.2 %** and
`cdicf` 36.4 %. The volume owner W3 measured as a false-ownership generator is
the structurally weakest.

## 4. What may not change

- **`DISTINCTIVE_MAX_HOLDERS` (3) and `MAX_DISTINCTIVE_REQUIRED` (3) are
  frozen.** Both are pinned to measured distributions, the second against the
  live ledger by `V-W8-BAR-NEVER-EXCEEDS-MEASURED-SUPPLY`.
- **`create_spec` untouched**, no third consumption boundary, corpus frozen at
  2,376 / 996 / 659 / 503 / 218.
- **`PR-W7-X1` stays green and is NOT inverted.** It asserts `rate > 0.90`
  against 93.9 %. Inverting a characterization that has not turned destroys
  the evidence of a live defect.
- **One authority, one selector.** Both doors read the same `select_for`.
- `spec_depth_selection` stays an honest UNKNOWN.

## 5. Mechanisms

Stated before any confusion matrix was recomputed.

**M1 — a compiled structural projection.** `build_structural_index` costs
45,525 ms cold and 10,080 ms warm over 1,364 files, which is exactly the
common-path repository archaeology this architecture forbids. It is compiled
offline into `term -> [ledger owners that structurally hold it]`, restricted
to the evidence-term universe and the 40 ledger owners: measured at **674
terms / 50,036 bytes / 0.73 ms to parse**. It is classified a PROJECTION —
never an authority — and carries its source fingerprint.

**M2 — structural strength as the primary rank key.** An owner's
`structural_strength` is the **same inverse-holder sum W8 already computes**,
evaluated over the subset of its matched distinctive terms that it
structurally holds. No new weight is invented, so §LXIII's magic-number
prohibition is satisfied by construction. It is a strict sub-sum of
`strength`, which gives the properties that matter:

- monotone up: adding a structural relation can only raise it;
- monotone down: removing one can only lower it;
- **true positives are protected by construction** — an owner with no
  structural attribution scores 0 and falls back to W8's ordering among its
  peers, it is never excluded;
- a projection of an existing source contributes nothing extra, because the
  term is already counted once.

**M3 — an admission clause, as a measured candidate and not a default.** An
owner routed only on terms it does not structurally hold is the coincidence
W8 could not refuse. Requiring at least one structurally attributed
distinctive term is the natural clause, and it is the one that can cost
recall. It ships only if the paired measurement supports it, and it is
evaluated as a separate arm. Default OFF.

## 6. The claim this wave can and cannot make

**A ranking-only change cannot move `P1-ANY-OWNER` precision at all.** That
metric asks whether at least one owner is routed; re-ordering the owners
inside a firing selection leaves it byte-identical. Stating this before
measuring, because reporting an unchanged headline as a failure of the
mechanism would be as wrong as reporting noise as a success.

So the headline for M2 is **rank quality** — whether the correct owner moves
toward the top, and whether false owners lose slots — and the headline for M3
is admission. Both are reported with the oracle's resolution beside them: the
labelled population is ~128 shared cases with ~31 positives, so one case is
~0.8 points and anything under ~3 points is **UNRESOLVED**, never "improved".

## 7. Freshness, and a deliberately bounded blast radius

Two tiers, because they cost different amounts:

- **Binding check, every load, ~0 ms.** The projection records the ledger's
  `compiled_corpus_id` and the ledger's size/mtime identity. A regenerated
  ledger means a stale term universe, and the projection degrades to
  *no structural contribution* — UNKNOWN, never refutation.
- **Source check, explicit.** A repo fingerprint over the scanned files is
  recorded at build time and verified by `--verify` and by a gate, not on the
  hook path.

This is safe *because* M2 is ranking-only: a stale projection can reorder, it
can never refuse. If M3 ships, the source check becomes load-bearing and the
spec is amended in the same commit that ships it.

## 8. Acceptance

- Structural supply and its distribution are measured and recorded before any
  policy constant is chosen. **Done, §3.**
- The 100 % projection result is recorded as a falsification, not buried.
- Control and treatment are re-derived **in one session on the shared cases**
  via `tools/ucr_cif_reach.py --funnel`. No stored figure is a control.
  `tools/ucr_cif_shadow.py` is not an oracle: it replays a persisted report
  and never calls `select_for`.
- The treatment runner proves the selector executed — an invocation counter,
  not a plausible number.
- True-positive retention floor: TP 12 must hold. Precision reached by routing
  nothing fails however high it goes.
- False-owner removal is shown disproportionate to true-owner removal. Fewer
  owner slots alone is not a result.
- Warm selection stays bounded; the projection parse is reported beside it.
- Absence of structural evidence never becomes refutation, and instrument
  failure is distinguishable from absence.
- Directed mutations sever the RELATION with both endpoints intact, and the
  existing 53 stay ALL_CAUGHT.
- Suites green: selection 22/22, consumption 19/19 (+PR 7/7), spec boundary
  22/22, reach 27/27, W8 applicability 17/17.

## 9. Out of scope

Test ownership, command/hook ownership and git history as evidence families.
§LXII orders current authority ahead of historical correlation, and the
measured supply (21 % / 18 %) is already sufficient to test the hypothesis.
Building a second family before the first is evaluated is gold-plating an
untested mechanism. Also out: the 503 ABSTAIN, the 218 UNRESOLVED, corpus
growth, FIOS deployment, `CLAUDE.md`, and the other writer's tree.
