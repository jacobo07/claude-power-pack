# Fable Advantage Distillation Reinforcement Suite — Master Index (FD-00…FD-07)

> Where the **Cognitive OS** (CO-00…CO-12) governs the *cost* of a session, the **Parallel Mesh**
> (PM-01…PM-05) governs the *coordination* of many panes, and the **Graphify Kernel** (GK-00…GK-12)
> governs *how knowledge is located*, the **Fable Advantage Distillation Suite** (FD-00…FD-07)
> governs one thing none of them does: **converting the delta a frontier model produces — the
> capability it demonstrates *above* what the PP can already do — into permanent, portable,
> model-independent advantage.**
>
> **The thesis, operationalized (borrowed from the CWOPS Unfair Advantage Engine):** *the loop is
> the moat.* CWOPS proved that in 2026 the durable advantage is not a feature but the **valid ·
> closed · <30-day** feedback flywheel a system's own execution deposits. FD applies the identical
> structure one level up: the durable advantage of using Fable is not the answer Fable gives — it
> is the **delta the FD loop extracts, classifies, and writes back into the stack** every session.
> An answer consumed is a `log file`; a delta distilled, triaged, transmuted, written back, and
> proven to survive a model downgrade is a **moat that compounds and reduces future dependence on
> the very model that produced it.**
>
> **Root law (FD-00):** *Spend frontier tokens only on the delta.* If the PP can already produce a
> result (via CO-03 routing, CO-05 assets, GK navigation, a deterministic rung, or a cached
> answer), the frontier model is not invoked. The FD suite is the classifier and the accountant of
> that decision. **Sealed as `PR-FABLE-DELTA-ONLY-001`.**
>
> **Central metric (inherited, never re-invented):** frontier-dependence reduction = **CO-12's
> model-demotion / Opus-avoided count + cognitive-compression ratio** (adopting-cohort WU/MTok ÷
> non-adopting). FD *feeds* this metric new routing rules; it does not stand up a parallel
> accounting layer (SCS C41: do not build what already exists).
>
> **Honesty rule (inherited from CO-10 / CO-12):** every FD guarantee is classified by the level it
> can actually enforce (Prompt → Hook → Wrapper → Cursor-ext → Host-limited), and no advantage is
> *claimed* without a `(metric, source, value)` triple — else it is a **hypothesis**, never a
> sealed result (CO-12 Telemetry-Before-Claims Contract).
>
> Scope approved by Owner 2026-07-09 (STOP #1, two rounds): **8 datasets — 5 NEW · 3 EXTEND**, out
> of **26 named candidates** (5 NEW · 9 EXTEND · 2 MERGE · 10 DO_NOT_BUILD ⇒ **~81 % already covered
> or thin-extension**, reported before building per the anti-bloat gate). Depth: **>2500 real
> words/Part at CommonWealth density** (differential, never volumetric). To seal as **SCS C82**.

---

## Family tree

```
Cognitive OS (CO-00..CO-12) + Parallel Mesh (PM-01..PM-05) + Graphify (GK-00..GK-12)   ← PARENT SUBSTRATE (consumed, never rebuilt)
│
└── Fable Advantage Distillation Suite (FD-00..FD-07)                                   ← this family (the Advantage axis)
    │
    ├── DOCTRINE
    │   └── FD-00  Fable Advantage Doctrine & Session Operating Protocol   NEW    (sibling of CO-00; absorbs S-PROTOCOL)
    │
    ├── EXTRACTION — the irreducible spine
    │   ├── FD-01  Fable Delta Extraction Engine (S-DELTA)                 NEW    (parent PM-03 Findings Bus)
    │   └── FD-02  High-Leverage Question Compiler (S-QUESTION)            NEW    (parent one_shot Q&A + CO-03)
    │
    ├── ROUTING TO THE STACK
    │   └── FD-03  Insight Triage & Transmutation (S-TRIAGE ⊕ S-TRANSMUTE) EXTEND (compound-learnings decision tree + UKDL)
    │
    ├── PORTABILITY PROOF
    │   └── FD-04  Intelligence Decay & Transfer-Proof Detector (S-DECAY)  NEW*   (parent CO-12 + CDIO-05; HIGH-RISK-gated)
    │
    ├── DEPENDENCE REDUCTION
    │   ├── FD-05  Anti-Dependence Arbitrage                               EXTEND (CO-03 + CO-05 + CO-12)
    │   └── FD-06  Permanent Advantage Writeback                           EXTEND (GK-08 + UKDL)
    │
    └── ORCHESTRATION
        └── FD-07  Fable Learning Flywheel (S-FLYWHEEL)                    NEW    (rides GK-08 + learning-sentinel; composes FD-01..06)
```

## Dependency graph (consumer → provider)

- **FD-00** governs all; consumes CO-00 (its sibling budget law) + CO-12 (the dependence metric it
  declares as the family's scorecard). Provides the Delta-Only root law + the per-session operating
  protocol to every other FD dataset.
- **FD-01** consumes PM-03 (the findings transport) + CO-05 (what the PP *can already do*, the
  baseline the delta is measured against) + CO-03 (was a cheaper rung available?). Provides the
  classified delta (`NEW / STRONGER / DUP / DISCARD`) to FD-03, FD-04, FD-06, and the routing signal
  to FD-05.
- **FD-02** consumes one_shot Q&A (the fixed 6-question scaffold it generalizes) + CO-03 (route the
  question to the cheapest sufficient model) + FD-04 (what capabilities are known-weak → ask there).
  Provides leverage-ranked *inputs* to the Fable session; it is the only FD dataset that acts
  *before* the model responds.
- **FD-03** consumes FD-01 (the delta to route) + compound-learnings' decision tree (the
  insight→destination classifier) + UKDL (the rule ledger). Provides the destination decision
  (Hard Rule / Process Rule / Trap / dataset Part / benchmark / prompt fragment / discard) and the
  transmuted *form* to FD-06.
- **FD-04** consumes CO-12 (cost/adoption baseline) + CDIO-05 (the six-lens review pipeline pattern)
  + FD-06's gold-standard references. Provides the portability verdict (does the distilled
  capability survive on Opus/Sonnet/deterministic?) to FD-05 and FD-07.
- **FD-05** consumes CO-03 (router), CO-05 (Zero-Token asset registry), CO-12 (Gap Radar signal),
  FD-01 (delta class), FD-04 (portability verdict). Provides new routing rules back into CO-03 and
  new deterministic/asset candidates into CO-05 — the mechanism that *reduces* future frontier calls.
- **FD-06** consumes FD-03 (the transmuted form + destination) + GK-08 (the writeback transport) +
  UKDL (rule ledger) + PM-03 (bus publish). Provides the permanent write into the correct stack
  location and the graph node (`type: fd_dataset`) to GK.
- **FD-07** consumes FD-01…FD-06 + GK-08 (Stop-hook writeback) + learning-sentinel (accrual trigger).
  Provides the closed operating loop `question → delta → novelty → triage → transmute → writeback →
  eval → benchmark → transfer-test → registry → prompt-improvement` and the leading-indicator
  readiness signal to CO-12.

## EXTEND vs NEW vs MERGE vs DO_NOT_BUILD — the full 26-candidate map

| Candidate | Verdict | PP parent / reuse | Genuine delta (why it survives) |
|---|---|---|---|
| **FD-00** Fable Advantage Doctrine + Session Protocol (S-PROTOCOL) | **NEW** | sibling CO-00; metric = CO-12 | No per-model-session operating manual exists; session-handoff-protocol is generic closure. |
| **FD-01** Delta Extraction Engine (S-DELTA) | **NEW** | PM-03 (transport only) | The irreducible spine: nothing compares a frontier output vs the PP baseline to isolate + classify the delta. |
| **FD-02** High-Leverage Question Compiler (S-QUESTION) | **NEW** | one_shot Q&A (fixed 6) + CO-03 | Compiles leverage-ranked *inputs*; CDIO critiques outputs, one_shot's Q&A is fixed, neither optimizes the question. |
| **FD-03** Insight Triage & Transmutation (S-TRIAGE ⊕ S-TRANSMUTE) | **EXTEND** | compound-learnings decision tree + UKDL | Destination-routing exists for *session learnings*; FD-03 extends it to *frontier deltas* + adds the form-transmutation. |
| **FD-04** Intelligence Decay & Transfer-Proof (S-DECAY) | **NEW (HIGH-RISK)** | CO-12 + CDIO-05 | Neither CO-12 (cost) nor PP tests (function) measure whether a distilled capability's *quality* survives a model downgrade. Absorbs Output-Comparator + Benchmark-Transfer-Harness. |
| **FD-05** Anti-Dependence Arbitrage | **EXTEND** | CO-03 + CO-05 + CO-12 | Absorbs Cognitive-Arbitrage-Router + Frontier-to-Deterministic + Gap-Radar as one section-set feeding CO-03/CO-05. |
| **FD-06** Permanent Advantage Writeback | **EXTEND** | GK-08 + UKDL | Absorbs Cross-System-Reinforcement + Permanent-Advantage-Writeback + Dataset-Mutation into GK-08's writeback protocol. |
| **FD-07** Fable Learning Flywheel (S-FLYWHEEL) | **NEW** | GK-08 + learning-sentinel | The composed valid·closed·<30-day loop does not exist as an operating protocol; rides the infra but is not reducible to it. |
| S-TRANSMUTE (Model→System) | **MERGE → FD-03** | — | "What form" = "what destination": one decision, not two systems. |
| Permanent Advantage Writeback (standalone) | **MERGE → FD-06** | — | Same GK-08 writeback surface as Cross-System-Reinforcement. |
| Context Minimality Compiler | **REFERENCE** | GK-06 Minimal Context Pack | GK-06 already ships the minimal-context-pack; FD references, does not rebuild. |
| Cognitive Arbitrage Router | folded → **FD-05** | CO-03 | — |
| Capability Gap Radar | folded → **FD-05** | CO-12 | — |
| Frontier-to-Deterministic Conversion | folded → **FD-05** | CO-05 | — |
| Cross-System Reinforcement Layer | folded → **FD-06** | GK-08 | — |
| Dataset Mutation Engine | folded → **FD-06** | UKDL | — |
| Fable-Grade Output Comparator | folded → **FD-04** | CO-12 | — |
| Model Benchmark Transfer Harness | folded → **FD-04** | CO-12 | — |
| **DO_NOT_BUILD (10):** model routing/demotion/Opus-avoided/2×3×4× ladder → CO-12/CO-03 · Zero-Token & deterministic replacement → CO-05 · Dynamic Router → CO-03 · Findings Bus & RedundancyTax → PM-03 · Session Writeback → GK-08 · Global cross-repo store → GK-10 · waste/anti-pattern detection → Leak Taxonomy C70 · critic swarm / design review → CDIO · Hard Rules / Process Rules / Traps → UKDL · Honest Guarantee Levels → CO-10 | **❌** | fully covered | Building any of these duplicates a sealed family (GK-00 "one system, no parallels"). |

**Tally:** 5 NEW · 3 EXTEND (built) · 2 MERGE · 1 REFERENCE · 10 DO_NOT_BUILD. **~81 % of the
named surface is covered or thin-extension** — the differential, delta-only discipline the thesis
demands, reported before a single dataset was written.

## Integration map with the existing stack

| FD dataset | reads from | writes to |
|---|---|---|
| FD-00 | CO-00 (budget), CO-12 (metric) | the whole FD family (root law + protocol) |
| FD-01 | PM-03, CO-05 (baseline), CO-03 | FD-03/04/06 (delta), CO-03 (routing signal via FD-05) |
| FD-02 | one_shot, CO-03, FD-04 | the Fable session (leverage-ranked inputs) |
| FD-03 | FD-01, compound-learnings, UKDL | FD-06 (destination + form) |
| FD-04 | CO-12, CDIO-05, FD-06 gold standards | FD-05, FD-07 (portability verdict) |
| FD-05 | CO-03, CO-05, CO-12, FD-01, FD-04 | **CO-03 new routing rules**, **CO-05 new det/asset candidates** |
| FD-06 | FD-03, GK-08, UKDL, PM-03 | **the correct stack location** + GK node `type: fd_dataset` |
| FD-07 | FD-01…06, GK-08, learning-sentinel | CO-12 (readiness signal), the operating loop |

The **Graphify Knowledge Graph indexes every FD dataset as a node of `type: fd_dataset`** with
edges to its CO/PM/GK parents (GK-04 typed edges), so a future session navigates to the delta
protocol instead of re-deriving it.

## Build order (by dependency)

1. **FD-00** — doctrine + protocol (the root law everything inherits) ← *this is the current turn's next deliverable*
2. **FD-01** — Delta Extraction (the classifier every downstream dataset needs)
3. **FD-02** — Question Compiler (the input side)
4. **FD-03** — Triage & Transmutation (routes FD-01's output)
5. **FD-04** — Decay & Transfer-Proof (tests the distilled asset)
6. **FD-05** + **FD-06** — the two EXTEND consumers (arbitrage + writeback)
7. **FD-07** — the Flywheel that composes FD-01…06 (built last)

## V-gates (FASE 4 done-gate) — scorecard (SEALED, verified ×3 hermetic 2026-07-09)

| Gate | Status | Evidence |
|---|---|---|
| V-FD-DELTA-NOT-GENERIC (extracts the specific delta, not generic intelligence) | ✅ PASS | FD-01 `NEW/STRONGER/DUP/DISCARD` taxonomy vs the CO-05 baseline; thesis-term density 88–219/dataset |
| V-FD-EXTENDS-NOT-DUPLICATES (no dataset duplicates CO/PM/GK) | ✅ PASS | this verdict table + every dataset's explicit "What it does NOT duplicate" section (`notDup=True` ×8) |
| V-FD-WRITEBACK-HAS-DESTINATION (every insight has an exact stack destination) | ✅ PASS | FD-03 destination taxonomy (8 homes, distinct triggers) + FD-06 write-execution + reinforcement |
| V-FD-DECAY-DETECTABLE (quality degradation measurable with defined criteria) | ✅ PASS | FD-04 six-lens transfer test vs gold standards; 97 anti-test-theater/gold-standard refs (no auto-tests, SCS C41) |
| V-FD-DEPTH (>2500 real words/Part) | ✅ PASS | all 24 Parts ≥2500 words (range 2502–3976); measured ×3 hermetic |
| V-FD-NO-CODE (zero code in datasets) | ✅ PASS | 0 fenced code blocks across FD-00…FD-07 (measured) |
| V-FD-REDUCES-DEPENDENCE (frontier-dependence reduction is a real metric) | ✅ PASS | metric = CO-12 model-demotion/Opus-avoided + cognitive-compression, reused not re-invented; fed by FD-05 arbitrage |
| V-BASELINE (pytest no regression) | ✅ PASS (vacuous) | zero code changed — only `.md` datasets added; no regression surface |

**Done-gate CLEARED:** all V-gates PASS ×3 hermetic (`DATASET_FAMILY_VERDICT=PASS`, 3/3);
sealed as **SCS C82** (`fable_distillation_scs_c82.md`); `PR-FABLE-DELTA-ONLY-001` appended to
`ukdl-universal.md`; `REMOTE_DELTA = 0 0` on push.

## The fundamental property of the whole system

> **Distill the delta, not the answer.** Spend frontier tokens only on what the stack cannot already
> produce; classify that delta; route it to its exact home; prove it survives without the model that
> made it; write it back permanently; and close the loop so the next session starts from a higher
> floor. The advantage is not the model — it is the compounding delta the loop deposits. Every
> guarantee is honest about its level; every advantage claim carries its `(metric, source, value)`
> triple or is labelled a hypothesis. All of it is files on disk, queried before exploration — no
> live brain claimed, no magic promised.
