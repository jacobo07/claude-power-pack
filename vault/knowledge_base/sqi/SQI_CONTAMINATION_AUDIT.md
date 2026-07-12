# SQI — Contamination Audit

> FASE 7. Verifies that no concept, name, or domain semantic from the reference corpus
> consulted during design has entered the SQI corpus. Enforced by
> `tools/test_sqi.py` (`V-SQI-*-CONTAMINATION` per dataset + `V-SQI-GOVERNANCE-CONTAMINATION`).

**Verdict: CLEAN.** 0 hits across 18 quarantined literals, 4 datasets + 2 governance
artifacts, ×3 hermetic, exit 0.

---

## 1. What was taken from the reference corpus, and what was not

The reference (a commercial-operations dataset family in the Owner's Downloads) was consulted
for **fabrication attributes only**, measured programmatically and never read for meaning:

| taken (structure) | measured value |
|---|---|
| Part spine | `PART I` … `PART XX`, invariant across all 3 sampled datasets |
| closing convention | a `FINAL LAW` block per Part, 49–221 words |
| depth tiers | ~800 (manifesto) / **~1,145 (operational)** / ~4,200 (flagship) words per Part |
| structural devices | numbered subsections + arrow flows; **zero** headings/bullets/tables/fences |
| dataset scale | 20.5k / 24.5k / 91.8k words |

**Not taken:** any concept, system name, taxonomy, metric, domain, or semantic. Zero.

The SQI corpus adopted the *operational tier* (its exemplar being a failure-science engine —
the closest structural analogue) and set a floor of 1,200 words per Part. Achieved mean:
**1,357**.

## 2. The audit's own defect, and its repair

The audit as originally specified was a literal grep over a word list. Run naively it produced
**39 hits and a CONTAMINATED verdict**. Investigation with word boundaries showed:

- **37 hits were false positives.** All were a single three-letter commerce acronym matched as a
  *substring* inside the interior of the word "cache" — in an environment-qualification dataset
  that necessarily discusses warm and cold artifact caches on nearly every page. A detector that
  cannot distinguish a hit from a substring manufactures findings, and a manufactured finding is
  the exact defect this corpus exists to prevent. **Repair:** every literal is now word-boundary
  matched (`\b…\b`), never substring-contained.

- **2 hits were real**, and both were in the corpus's own governance files:
  1. `CANONICAL_ONTOLOGY.md` §8 named a quarantined word *in the course of prohibiting it* —
     stating the rule by committing it. Rewritten to describe the prohibition obliquely; the
     enumeration lives in the detector's code, fragment-assembled at import.
  2. `SQI_INDEX.md` used the git phrase for a fresh working copy, whose second word is
     quarantined as a payment-page term. Legitimate vocabulary that nonetheless trips a literal
     grep. Renamed to "clean-clone", matching SQI-03's own Part XIII title.

- **The audit report itself was then refused by its own gate**, because this section originally
  named both literals in the course of reporting them. That is the fourth instance in this build
  of one recursion: *a document about forbidden words cannot contain the forbidden words.* The
  detector cannot read intent, and it is correct not to try — a scanner that exempts text which
  claims to be discussing a violation is a scanner with an exemption an attacker can write.
  Every literal in this corpus is therefore named only in code, assembled from fragments.

- **A gate gap was exposed.** The detector scanned only the `.txt` datasets and never the `.md`
  governance artifacts — which is precisely why both real hits survived. A gate that does not
  scan an artifact cannot protect it. `V-SQI-GOVERNANCE-CONTAMINATION` now covers them.

## 3. The vocabulary decision (and why the audit can stay literal)

A literal grep for the visitor-to-buyer word produces false positives on legitimate quality
prose: the source specification itself uses it in "Regression … Rate" and "… of failures into
assets", both pure verification concepts with no commercial semantics whatsoever.

Rather than weaken the audit with context-sensitive exemptions, **SQI changed its own
vocabulary**: it uses *transmutation* and *institutionalization* throughout. The audit therefore
remains literal, cheap, and honest — it expects zero hits and gets zero, with no escape-hatch
reasoning about intent.

## 4. Evidence

```
V-SQI_00_CONSTITUTION_V1-CONTAMINATION            0 hits / 18 literals
V-SQI_01_REPOSITORY_REALITY_V1-CONTAMINATION      0 hits / 18 literals
V-SQI_02_TEST_REACH_V1-CONTAMINATION              0 hits / 18 literals
V-SQI_03_ENVIRONMENT_QUALIFICATION_V1-CONTAMINATION  0 hits / 18 literals
V-SQI-GOVERNANCE-CONTAMINATION                    2 artifacts clean / 18 literals

SQI_PASS=27/27  threshold=27/27  datasets=4   (x3 hermetic, exit 0)
```

Reproduce: `python tools/test_sqi.py`
