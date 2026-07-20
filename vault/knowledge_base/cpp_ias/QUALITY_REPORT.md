# CPP-IAS — QUALITY REPORT

> Real metrics pulled from the Foundations authoring results (IAS-F1, IAS-F2) and the System
> verify verdicts (IAS-A1/A2, B1/B2, C1/C2, D1/D2, E1/E2, F3, G1). No number in this file is
> estimated — every word count and Part count below is the value reported by the verify pass
> against the actual file on disk.

## 1. Per-dataset metrics

**FINAL, post-remediation. Every number below was measured by the orchestrator directly from the
files on disk** (each Part sliced from its `PART N —` header to the next), *not* taken from any
authoring or verify agent's self-report. The first seal's numbers were wrong (see §6); these are not.

| ID | Dataset | Parts | Words | Words/Part (mean) | Min Part | Contamination | Sealed |
|---|---|---|---|---|---|---|---|
| IAS-F1 | Federation Ontology & System-of-Systems Object | 18 | 28,612 | 1,590 | 1,253 | 0 | YES |
| IAS-F2 | Institutional Advantage Algebra & Fusion Score | 20 | 31,048 | 1,552 | 1,238 | 0 | YES |
| IAS-A1 | Institutional Capability Router & Mission Composer | 22 | 34,912 | 1,587 | 1,215 | 0 | YES |
| IAS-A2 | Institutional Control Bus & Event Fabric | 20 | 32,250 | 1,613 | 1,230 | 0 | YES |
| IAS-B1 | Cognitive Multiplier & Leverage Discovery | 22 | 34,196 | 1,554 | 1,225 | 0 | YES |
| IAS-B2 | Cross-Dataset Insight Synthesis & Pattern Transfer | 22 | 35,226 | 1,601 | 1,213 | 0 | YES |
| IAS-C1 | Capability Portfolio & Cognitive-Capital Allocation | 22 | 34,894 | 1,586 | 1,208 | 0 | YES |
| IAS-C2 | Capability Demand Forecasting & Opportunity Cost | 18 | 29,192 | 1,622 | 1,206 | 0 | YES |
| IAS-D1 | Institutional System Ecology | 26 | 42,778 | 1,645 | 1,316 | 0 | YES |
| IAS-D2 | Institutional Immune System & Failure-Mutation Intelligence | 24 | 36,039 | 1,502 | 1,204 | 0 | YES |
| IAS-E1 | Institutional Observability Fabric | 22 | 35,004 | 1,591 | 1,200 | 0 | YES |
| IAS-E2 | Cognitive Reliability Engineering | 22 | 36,562 | 1,662 | 1,218 | 0 | YES |
| IAS-F3 | Institutional Digital Twin & Simulation | 24 | 32,801 | 1,367 | 1,231 | 0 | YES |
| IAS-G1 | Architecture Intelligence & Topology Optimization | 22 | 34,680 | 1,576 | 1,298 | 0 | YES |
| **TOTAL** | **14 datasets** | **304** | **478,194** | **1,573** | **1,200** | **0** | **14/14** |

The corpus grew by 7,882 words between the first seal and this one. That delta is the depth
remediation described in §6 — not new datasets.

## 2. Net Institutional Capability Gain (qualitative)

The corpus adds **14 second-order institutional systems** to the estate (7 explicitly tagged
2nd-order EXTEND against an existing estate system in `SYSTEM_STRENGTHENING_MATRIX.md`: A1, A2,
C1, D1, D2, E1, G1; 7 tagged NEW but each still required to strengthen ≥4 existing systems per
the Constitution's compounding mandate: F1, F2, B1, B2, C2, E2, F3). Zero of the 150
non-duplication candidates evaluated in `NON_DUPLICATION_LEDGER.md` were rebuilt from scratch —
every candidate was either folded into an EXTEND dataset or explicitly referenced/rejected. The
gain is compounding, not additive: `COMPOUNDING_GRAPH.md`'s four loops (circulation,
amplification, defense, foresight) each route through 4–6 of the 14 datasets, meaning every
sealed dataset raises the functional ceiling of multiple siblings rather than standing alone.
This is a qualitative claim, not a measured one — the four loops are specified and cross-
referenced in text (see `COMPOUNDING_GRAPH.md` § LOOP EVIDENCE) but not yet exercised against a
live multi-project estate; that remains EXPERIMENTAL per each dataset's own epistemic markers.

## 3. Duplicate Avoidance Rate

- Candidates evaluated (NON_DUPLICATION_LEDGER.md): **150**
- Candidates built as net-new duplicate systems: **0**
- Candidates folded into an EXTEND dataset or explicitly referenced/dispositioned: **150**
- **Duplicate Avoidance Rate: 150/150 = 100%**

This rate is a direct consequence of the Constitution's Article X (PP-repo writes must stay 0)
and the D2A doctrine (propose-never-build on architectural duplicates) — both of which are
structural gates the authoring passes had to satisfy to reach SEALED, not a self-reported score.

## 4. Domain Contamination

- Datasets audited: **14/14**
- Total contamination hits: **0** — confirmed by an independent orchestrator-side regex sweep of
  the files on disk, not accepted from the authoring agents' self-reports.
- Method: regex sweep per dataset for CommonWealth / CW Ops / InfinityOps / ecommerce / store /
  operator / supply-chain / customer-acquisition / ads / ROAS terms.

**Known false-positive classes (do NOT re-flag these on a future audit):**

1. **The audit-declaration passage.** IAS-F2's closing compliance statement *names* the forbidden
   term list in order to declare its absence, so a naive grep scores 5 hits inside a sentence whose
   whole purpose is to assert cleanliness. A detector that flags a corpus for describing its own
   forbidden-term list will flag every honest audit statement ever written.
2. **"Knowledge supply chain."** IAS-E1 uses this phrase 5 times. It is a *Claude Power Pack*
   concept — candidate Family I in `NON_DUPLICATION_LEDGER.md`, REFERENCE-routed to
   GK-01..08 / FD / CO-05 / akos_knowledge. It has nothing to do with commercial logistics.
3. **"store" as data storage.** IAS-F1's "property-record store" / "structured store" are
   storage nouns, not retail.

Every literal match found on disk fell into one of these three classes. **Real contamination: 0.**
The lesson is recorded because the naive detector produced a 10-hit false alarm that a less careful
audit would have either reported as a failure or, worse, "fixed" by damaging correct prose.

## 5. PP-repo writes

- **0** — confirmed across both the Foundations pass and the System verify pass. No dataset wrote
  production code into `modules/`, `hooks/`, `commands/`, or any other PP-repo-owned path; all
  authored content is specification-only prose under
  `CPP Institutional Advantage Systems/`, consistent with Article VIII (Reality Contract /
  science-before-implementation).

## 6. Depth-floor audit (CORRECTED — the seal pass overstated this)

**The original seal claimed "no dataset has a Part below 1,200 words". That claim was FALSE.**
An independent orchestrator-side scan of the files on disk (per-Part word counts computed from
each `PART N —` header to the next) found **23 Parts across 7 datasets below the Constitution's
Article VI hard floor of 1,200 words.** The System verify pass had self-reported
`parts_below_floor: 0`; the disk disproved it. This is recorded rather than smoothed over, per
the corpus's own "no classified FAILs at done-gate" discipline — a producer may not certify its
own claim (Constitution Art. XI; SQI Article Six).

Verified violations at first audit:

| Dataset | Parts below 1,200w (measured) |
|---|---|
| IAS-F1 | I (1,033) · II (902) · III (859) · XVI (1,190) |
| IAS-A1 | I (1,187) · IV (1,192) |
| IAS-B1 | VI (1,199) |
| IAS-B2 | I (1,162) · II (1,151) · VI (1,185) · XIII (1,195) · XIV (1,177) · XVI (1,171) |
| IAS-C1 | XIV (1,150) |
| IAS-D2 | XI (1,152) · XVII (1,190) · XXII (1,191) |
| IAS-E2 | I (1,199) · V (1,175) · VI (1,178) · VII (1,162) · X (1,195) · XI (1,179) |

Note on IAS-F1 Parts I–III: these were authored in an earlier session, before the depth contract
was fixed at 1,200–1,500 w/Part. The F1 completion agent correctly declined to alter them (they
were out of its scope) and flagged the shortfall honestly in its return — the failure was in the
seal pass accepting the dataset as clean, not in the authoring agent hiding it.

**Remediation:** a targeted expansion pass re-authored each of the 23 Parts in place to ≥1,300
words of genuine content (new subsections, worked examples, edge/adversarial cases, failure modes,
metrics with countermetrics, sibling interfaces) — never padding, with each Part's FINAL LAW
preserved. Final post-remediation counts are in §1 and `BUILD_STATUS.md`.

## 7. Not independently re-verified

Per IAS-F2's honest_notes, the geometric-mean arithmetic in its Part XVIII worked synthetic
examples was computed by hand in-line rather than run through a calculator or script. It is
marked EXPERIMENTAL in the source text and is illustrative rather than load-bearing; a reader
relying on the exact numeric outputs there should re-derive them rather than trust them blindly.
This report does not independently re-verify that arithmetic — it is passed through as reported.
