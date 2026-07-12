# DFP — Completion Report (honest state)

> Sealed 2026-07-12. Combines the contamination audit, the dependency graph, the governance
> contract, and an honest statement of what this family is and is not.

---

## 1. What shipped

| unit | evidence |
|---|---|
| **3 datasets** (DFP-00 · DFP-02 · DFP-05) | 30 Parts, 40,086 words, every Part ≥ 800w, every dataset in the measured 8k–15k band |
| **5 modules** (`modules/dataset_first/`) | `classifier` · `knowledge_sufficiency` · `necessity_record` · `manifest` · `calibrator` |
| **1 DRK amendment** | `BUILD-KNOWLEDGE-FIRST` — the 11th verdict, wired as a live provider (Stage 7b) |
| **1 D2A extension** | `FAMILY_REGISTRY` 19 → 27 families |
| **1 D1 Liveness row** | `dfp-necessity-ledger` — probe earns LIVE from a real record, never declares it |
| **1 necessity record** | `DFP-0001` — the founding self-exemption, with its falsifiable prediction |
| **17 V-gates** | `tools/test_dataset_first_protocol.py` — 17/17 hermetic ×3 |

**Four proposed datasets were NOT built** (DFP-01 · 03 · 04 · 06). They were routed through
D2A and became one enum member, two modules, and a set of cross-references. Ratio: **4
proposed datasets → 0 new datasets.** See `DFP_D2A_VERDICTS.md`.

---

## 2. Contamination audit — PASS (zero hits)

Pattern scanned across the whole corpus + governance artifacts:
`commonwealth | tua-?x | unfair advantage | first win | capital ladder | pre-capital | ecommerce`

**0 hits.** Gate: `V-DFP-CONTAMINATION`, run hermetically ×3.

The approved references (Human Resonance OS, Operator Essence Intelligence System,
CommonWealth Unfair Advantage Engine) were used **only** to extract fabrication attributes —
words per dataset, words per Part, artifact shape — by measurement. Their measured band
(8,000–15,000 words/dataset; 800–1,500 words/Part) is the standard this corpus obeys. **Zero
concepts, terminology, entities, ecosystems, or commercial domain content were imported.**

---

## 3. Dependency graph

```
spec_gate (HR-SPEC-001)  ──tier──────────┐
D2A (functional precision) ──overlap─────┤
ACIS (epistemic_ladder) ──E0..E6─────────┼──> knowledge_sufficiency.evaluate()
DRK-02 (reversibility, passed IN) ───────┘         │
                                                   ├──> classifier.classify()
                                                   │         │
                                                   │         └──> necessity_record (ledger)
                                                   │                     │
                                                   │                     └──> calibrator (DFP-05)
                                                   │                              │
                                                   └──> DRK kernel Stage 7b ──────┘
                                                          (provider "dfp")
                                                                │
                                                                └──> Verdict.BUILD_KNOWLEDGE_FIRST
```

**Direction is one-way.** DFP reads its providers; no provider reads DFP except DRK's kernel,
which calls it as one advisor among seven. There is no cycle, and DFP holds no block authority
of its own — the one block it cares about is exercised through DRK's existing gate, under
DRK's existing override protocol. Its authority is entirely borrowed, on purpose (DFP-00 VIII).

---

## 4. Governance contract

- **Naming.** Datasets `dfp_<NN>_<slug>_v1.txt` (prose only — no markdown, no code fences).
  Governance artifacts are markdown. Code lives in `modules/dataset_first/`.
- **Numbering.** The gaps at 01, 03, 04, 06 are preserved deliberately. They are the
  DO-NOT-BUILD verdicts, and the holes are the evidence. A reader who asks "where is DFP-03?"
  is answered by `DFP_D2A_VERDICTS.md`.
- **Versioning.** A sealed dataset is amended, never silently edited. An amendment names what
  changed and why.
- **Ownership.** DFP owns the knowledge-necessity axis and nothing else. Every capability in
  `CANONICAL_ONTOLOGY.md` §0.2 belongs to a sibling and is cross-referenced, never re-narrated
  (gate: `V-DFP-CROSS-REF-NOT-RENARRATE`).
- **Deprecation.** This family is built to be retired. `calibrator.retirement_signal` is
  reachable and a gate proves it. If the evidence says the discipline does not pay for itself,
  the honest response is deletion, not a threshold tweak.
- **Conflict resolution.** DFP never overrides a sibling. Where DFP and a provider disagree,
  the disagreement is recorded (as it was, twice, in `DFP_D2A_VERDICTS.md`) and the provider
  is not tuned until it agrees.

---

## 5. Honest state — what this family is NOT

**The family is at maturity level ONE of five** (DFP-00 X.8), and this is the single most
important fact in this report.

- Level 1 = the corpus exists, the gates are green, the modules import. **This is where we are.**
- Level 3 = enough records exist to compute the two error rates.
- Level 5 = the protocol has correctly recommended *against itself* at least once.

**Every gate in this family currently proves the corpus is well-formed. Not one proves it is
right.** The necessity ledger holds exactly **one** record — this family's own founding — and
that record's prediction has not been graded. Until DFP-05 has real records to grade, every
claim in DFP-00, including its central thesis, is a hypothesis with good formatting.

### What would falsify the whole thing

After twenty recorded necessity decisions: if implementations that followed a certified corpus
show no measurable advantage over those that went direct — no lower rework, no fewer
regressions, no higher reuse — then the discipline does not pay for itself. The honest response
is **not** a threshold adjustment. It is to retire the protocol, delete the modules, keep the
three datasets as a well-conducted negative result, and seal the trap that stops the next agent
from proposing it again (DFP-00 X.10). `calibrator.py` will emit that recommendation on its
own, and `V-DFP-RETIREMENT-REACHABLE` proves it can.

### The founding exemption, restated so it cannot be lost

DFP's own `CORPUS_OPEN` signal returned **DEFER** on DFP (SQI was open with zero sealed Parts),
and the source science for the thesis did not exist on disk. Both were surfaced to the Owner
*before* any corpus was written. The Owner overrode the DEFER and directed a parallel,
scope-collapsed build. That override is `DFP-0001`, it carries the prediction that would prove
it wrong, and it is the family's first calibration datum.

Notably, the **sufficiency engine itself returned HYBRID** — which is what was built. The class
was never overridden; only the open-corpus signal was. The author had *assumed* the engine would
return knowledge-first (the dramatic result) and wrote that into the first draft of the
constitution without running it. The engine disproved him. That correction is recorded in
DFP-00 IX.3a rather than buried, because a constitution that states what its own instrument
returns without asking the instrument is doing the exact thing this family exists to forbid.

---

## 6. The standing obligation

The next agent to touch this family must do two things before anything else:

1. **Read `DFP_D2A_VERDICTS.md` §2.** Two of D2A's four verdicts disagreed with the
   architectural reading and were left standing rather than tuned away. If you tune the
   detector until it agrees with your prior, you have overfitted it to one case — the case its
   own author wrote.
2. **Run `calibrate()` before trusting any threshold.** The thresholds in
   `knowledge_sufficiency.py` are hypotheses seeded from thin evidence. A threshold that has
   not moved after twenty records is unmeasured, never perfect.
