# AutoResearch Upgrade Log

Upgrade of the CPP Research OS from a one-shot pipeline to a four-engine one.
Module: `modules/deep-research/`. Version `0.2.0` → `0.3.0`, sealed 2026-08-18.

---

## P0 — what already existed

Read before writing anything, per the standing rule that a dataset describing an
architecture is a hypothesis about the repo, never a statement about it.

| Engine | State found in CPP | Verdict |
|---|---|---|
| E1 Problem decomposition | `generate_serp_queries` + `is_natural_question` already produced natural-language questions with a `researchGoal`. No typed axes. | **EXTEND** |
| E2 Landscape coverage | Absent. Top-5 DuckDuckGo organics, unclassified. `filter_by_relevance` judged operator-actionability, which is a different axis from source quality. | **NEW** |
| E3 Capability + reality | `LEARNINGS_PROMPT` read *"extract what a founder or operator should LEARN"* — the exact string the upgrade brief quoted. Learnings were bare `list[str]`: no capability, no epistemic label, no provenance. | **EXTEND** |
| E4 Contradiction detection | Absent entirely. Conflicts were resolved by whichever learning was extracted last. | **NEW** |

Two findings that prevented duplication:

- `modules/autoresearch/` is a **different system** — an RSS/YouTube signal
  firehose (score → enrich → digest). Untouched.
- `modules/fable_distillation/epistemic_ladder.py` already derives an E0–E7
  level, but for *internally deposited claims* judged against PP's own ledgers.
  Different axis, different corpus. Its **doctrine** was reused (degrade
  downward, never inflate; no self-certification); its code was not.

The referenced dataset file was not present in the workspace. The engine
descriptions in the brief were treated as the spec.

---

## What shipped

| File | Role |
|---|---|
| `modules/deep-research/research_engines.py` | **NEW.** All four engines: prompts, schemas, deterministic gates. Pure — no network, no LLM, no disk. |
| `modules/deep-research/test_research_engines.py` | **NEW.** 41 V-gates, offline. Fixtures are the observed bug, not synthetic analogues. |
| `modules/deep-research/deep_research.py` | Wired. v0.3.0. All four engines on the live path. |
| `modules/deep-research/research_quality.py` | Two prompts marked SUPERSEDED; its deterministic gates still run underneath the engines. |
| `commands/cpp-deep-research.md` | Documents the engines, the families, and the epistemic ladder. |

The engines are **wired, not merely shipped**: `deep_research.py` imports
`research_engines` on the module path exercised by `--version`, and the command
plus the `research-intent-detector.js` Stop hook both reach it. A module nothing
invokes is an orphan, and an orphan passes its own tests forever.

---

## The core design decision

The upgrade does not make learnings longer. It makes them carry **how much to
bet on them**.

Every stored learning now leads with its labels:

```
[VERIFIED][HIGH] <insight> — Capacidad: <the decision this changes> — Evidencia: <why the label>
```

The label leads because a label at the end arrives after the reader has already
formed a view.

And the extractor **cannot certify its own claim**. It proposes a level;
deterministic gates dispose:

| Cap | Fires when | Result |
|---|---|---|
| landscape | every source is a recognised conversion surface | `REJECTED`, dropped, logged |
| provenance | no source resolved to a known family | capped at `DERIVED` |
| corroboration | `VERIFIED` on < 2 supporting sources | demoted |
| measurement | `OBSERVED` with no quantity a regex can find | → `DERIVED` |
| arithmetic | claimed `supporting_sources` > documents fetched | clamped |

Every cap **only degrades**. An unknown label, a malformed field, an unreadable
value costs confidence and can never buy it.

---

## WS5 — the same query, re-run

Query, verbatim from the original conversation:

> *how do content teams know when a topic cluster is saturated and adding more
> articles stops helping*

### Run 1 — 2026-08-18 13:57Z · `--depth 1 --breadth 3`

**Result: 0 learnings, 0 sources, 68 s.** The run exposed a real calibration
defect in Engine 2, which is why it is recorded here rather than deleted.

| Engine | Observed |
|---|---|
| E1 | 3/5 axes searched — EVIDENCE, MECHANISM, COUNTEREXAMPLE. Worked as designed. |
| E2 | 13 pages fetched. **1 classified `D_VENDOR`, 12 classified `UNKNOWN`.** All three questions returned `VENDOR_ONLY` → all three extractions skipped. |
| E3 | Never reached. |
| E4 | `skipped-too-few-learnings`. |

**Root cause — two defects, both mine:**

1. **The classifier's vocabulary was software-engineering-only.** The
   practitioner markers were `latency`, `throughput`, `our architecture`. A
   content-strategy domain matches none of them, scores zero, and a zero is
   indistinguishable from a bad page. This is the trap already sealed in memory
   as *"a gate is bounded by its vocabulary; unrecognised idioms read as 0, and
   0 never falls"* — walked into while building the gate that was supposed to
   prevent it.
2. **`UNKNOWN` was treated as family D.** The Owner's rule refuses a claim built
   on **family D alone**. A page the classifier could not identify is not
   family D — it is unidentified. Collapsing the two turned the coverage gate
   into a silent kill switch for every field it had not been taught.

**Fix:**

- New verdict `UNCLASSIFIED`, distinct from `VENDOR_ONLY`. Refusal stays
  reserved for pages positively recognised as marketing; unidentified
  provenance costs confidence (capped at `DERIVED`) instead of erasing the work.
- Practitioner vocabulary broadened to the **shape** of first-hand reporting
  (`in our experience`, `lessons learned`, `what worked`, `en nuestra
  experiencia`, `lo que aprendimos`…) rather than one industry's nouns.
- Guard against the obvious side effect: broadening could have laundered every
  vendor blog into a load-bearing family, since marketing pages say "in our
  experience" constantly. Family C now requires **either** a recognised
  practitioner host **or** first-hand prose **on a page that is not a conversion
  surface**. Gated by `V-LANDSCAPE-NO-LAUNDERING`.

Four V-gates were added so the regression cannot recur silently:
`V-LANDSCAPE-UNKNOWN-IS-NOT-VENDOR`, `V-LANDSCAPE-MIXED-UNKNOWN`,
`V-LANDSCAPE-NO-LAUNDERING`, `V-LANDSCAPE-DOMAIN-AGNOSTIC`,
plus `V-EPISTEMIC-CAP-UNCLASSIFIED`.

### Run 2 — 2026-08-18 14:15Z · `--depth 1 --breadth 4`, corrected gate

**Result: 9 learnings, 14 sources, 803.9 s, exit 0.** All four engines fired on
live data.

| Engine | Observed |
|---|---|
| E1 | **4/5 axes searched** — EVIDENCE, MECHANISM, BOUNDARY, COUNTEREXAMPLE. Zero questions rejected as keyword soup. |
| E2 | 19 pages classified: `A_MEASURED×2`, `B_ACADEMIC×2`, `D_VENDOR×1`, `UNKNOWN×14`. Per question: `THIN/HIGH`, `UNCLASSIFIED/LOW`, `UNCLASSIFIED/LOW`, `THIN/HIGH`. **0 refused as vendor-only** — the gate now distinguishes unidentified from marketing. |
| E3 | `OBSERVED 1 · VERIFIED 3 · DERIVED 5`. **3 labels demoted by the evidence gates** — two `OBSERVED→DERIVED` and one `VERIFIED→DERIVED`, all under the provenance cap on the two `UNCLASSIFIED` questions. |
| E4 | **6 unresolved conflicts**, detector `checked`. |

The demotions are the system working, and they are visible in the error log by
name: a claim extracted from an `UNCLASSIFIED` landscape asked for `OBSERVED`
and was refused it. Nothing was deleted; the confidence was corrected.

**Sample output, verbatim:**

> `[OBSERVED][HIGH]` A blog post that earns zero Google Search Console
> impressions in its first 72 hours after indexing has an 84% chance of never
> exceeding 50 monthly sessions, while posts that earn at least one impression
> in that window hit their traffic peak 3.2× faster […]

> `[VERIFIED][HIGH]` The most common modern failure mode is traffic and
> conversions falling while average position barely moves — a page can hold
> position ~3.1 for its head term while clicks drop 30–40% over six months […]
> Rank-tracking alerts watch head terms and therefore stay silent.

**A contradiction it surfaced instead of resolving:**

> **CONTRADICCIÓN** — Fuente [3]: post-expansion decline is dominantly keyword
> cannibalization; the remedy is merging overlapping pages. · Fuente [4]: pages
> in the same keyword space coexist fine when each serves a distinct intent, so
> the filter is intent-differentiation, not page-count consolidation.
> *El conflicto NO está resuelto.* Explicación probable: METHODOLOGY.
> *Para el operador:* as stated they prescribe opposite first moves — check
> whether the overlapping pages differ by intent before consolidating.

The original conversation produced no such section. It picked one framing and
presented it with a single voice. The two claims above are both in the field;
an operator who only saw one of them would consolidate pages that should have
been kept, or keep pages that should have been merged.

### Verdict

`delta_quality: **mejor**`

Reason: the same query now returns 9 learnings whose confidence is individually
legible (1 `OBSERVED`, 3 `VERIFIED`, 5 `DERIVED`), carries concrete figures
(84%, 3.2×, 30–40%, position 3.1), names the capability each one confers, and
ends with 6 named conflicts the pipeline refused to settle. The original
returned confident prose founded on one vendor blog with no label at all.

Honest limits of this measurement:

- One run per configuration, no repeat. `delta_quality` is a judgement over
  observed artifacts, not a statistic.
- 14 of 19 sources still classify `UNKNOWN`. The classifier is calibrated for
  refusal-correctness first (a vendor page must never launder into a
  load-bearing family), so recall is deliberately the weaker side. The system
  reports this honestly — those questions are stamped `UNCLASSIFIED/LOW` and
  their learnings are capped — rather than guessing a family.
- One `extract_learnings` call failed on a `claude.exe` subprocess error and was
  skipped; the run continued and logged it, as designed.

---

## Delta vs the original conversation output

| Dimension | Original | Upgraded |
|---|---|---|
| Question generation | one framing of the topic | decomposed across 5 axes, gated at ≥3 |
| Source handling | top-5 organics, unweighted | classified into 4 families, load-bearing read first, marketing-only refused |
| Learning shape | unlabelled prose | capability + epistemic level + evidence + source quality |
| Confidence | implied by tone | stated per claim, capped by deterministic gates |
| Conflicts | resolved silently, last-writer-wins | reported unresolved, with an axis and operator guidance |
| Empty result | "insufficient data" | names *which* layer ran out, including a vendor-only landscape |

---

## Meta

The learning extracted in the original conversation was good but fragile: one
vendor blog, no epistemic label. An operator acting on it could not tell it from
a measured result, so they would bet the same amount on both.

A correct Research OS does not produce longer learnings. It produces learnings
whose confidence is legible. One `[OBSERVED][HIGH]` sentence is worth more than
five `[HYPOTHESIS][LOW]` paragraphs — and the label is the part that lets the
reader know which one they are holding.

Run 1 is the proof that this applies to the system itself: a gate that refused
everything looked, from the outside, exactly like a gate working correctly. Only
the per-question landscape breakdown in the footer made the difference visible.
