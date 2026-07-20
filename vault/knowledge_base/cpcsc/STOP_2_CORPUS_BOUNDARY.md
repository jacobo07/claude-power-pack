# STOP #2 — Corpus Boundary (content-tier verified)

> **BLOCKING GATE — awaiting Owner approval. Nothing built.**
> Inputs: CPCSC STOP #1 (20 domains, 6 content-verified) · CPP-ACI Tribunal re-run
> (12 Sciences, all content-verified) · CPP-IAS inside the denominator for the first time.
> Sealed 2026-07-20.

## 1. What the evidence produced

Two specs proposed a combined **32 domains, 238 system jurisdictions, ~500k–1M words**.
After content-tier verification of all 32, the genuine, non-duplicative delta is:

**2 new datasets · ~9 Parts or modules into existing owners · 2 Owner decisions · 0 new families.**

Every reduction is evidence-backed, and every survivor names a mechanism that provably does
not exist in the estate.

## 2. Verification record

| audit | verdicts | changed | direction |
|---|---|---|---|
| CPCSC STOP #1 | 6 content-verified of 20 | 6 | all toward less-owned |
| CPP-ACI Tribunal | 12 of 12 | 9 | **both directions** — 6 toward less-owned, 3 toward more-owned |

The Tribunal re-run moving in **both** directions is what makes this boundary trustworthy.
X and XI became ABSORB; V collapsed from "genuine white-space" to 80%-owned. A correction
that only ever found gaps would be indistinguishable from a method that rewards finding them.

**Owner-set accuracy was worse than verdict accuracy in both audits** — the Tribunal's
owner column was wrong or incomplete in 12 of 12. Root cause: it scored the *code* surface
while the mechanisms live in the *dataset* surface, and CPP-IAS was physically outside the
repository on 2026-07-12. Repatriation (`6b83358`) is what made the re-run possible.

## 3. THE BOUNDARY

### Tier A — genuine NEW datasets (2)

Each beat the anti-inflation test: a Part, a rule, an eval, and not-building.

**A1 · Cognitive Education** — 0% owned, confirmed by targeted search across
`vault/knowledge_base/`, `modules/`, `agents/`, `commands/`. Every hit was a vocabulary
collision (human onboarding, system certification, SaaS proficiency). No adjacent owner
holds even a partial. Scope: capability curriculum, apprenticeship, synthetic-experience
training, failure-simulation training, certification/recertification of capabilities, and
the model-onboarding pipeline. *Why a dataset and not a Part: there is no parent to attach
to. Attaching it anywhere would be the misattribution this audit exists to prevent.*

**A2 · Theory Generator / Law Extraction** — the generative half of meta-science.
Every existing owner *judges* a law that a human or frontier session already wrote —
falsify it, level it, retire it, route it. Nothing *proposes* one. **ACIS is a tribunal
without a legislature.** Four ledgers (FD-07 deposits, fd_04 proofs, UKDL rules, CEPS
events) are read only to compute a level; nothing mines them for a candidate law.
*Owner caveat: ACIS lists "unknown-unknown infra" under DO_NOT_BUILD. Building A2 revisits
a prior scoping decision — that is an Owner call, recorded here rather than assumed.*

### Tier B — Parts or modules into an existing owner (9)

Each has a named parent and a named gap. None justifies a dataset.

| # | remainder | attaches to | form |
|---|---|---|---|
| B1 | unknown-unknown generation | FIOS (already carries it as 🟡 EXTEND — not built) | dataset Part |
| B2 | epistemic algebra unification — one join across DRK-00 evidence types, DAIF-01 statuses, ACIS ladder | new registry + Part | registry |
| B3 | reasoning execution axis — live-trace ingestion, decompiler, VM, unified pre-execution entry gate | CO-03 + one_shot (estate already ruled `DEFERRED (EXTEND CO-03 + one_shot)`) | wiring |
| B4 | corpus→executable transduction — the foundry step | seam: DFP FREEZE → IAS-C1 FUNDED | module |
| B5 | undeclared side-effect ledger | daif_04 PART VII | Part + module |
| B6 | mission constitution — per-mission normative envelope | ias_a1 PART VII | **one Part** |
| B7 | adversarial pathogen class + 4 detectors | ias_d2 (taxonomy is closed at 6 self-inflicted classes) | Part |
| B8 | semantic memory abstraction ladder + cross-layer consistency | daif_08 | Part |
| B9 | DR simulator · model-exit simulator · SPOF/maturity/debt register | ias_f3 | Parts |

### Tier C — Owner decisions before any build (2)

**C1 · World Model Federation** — 10% owned; IAS-F1's thesis is the *opposite* (impose one
ontology). Genuinely absent, but holding plural competing world models is a large
architectural commitment, not an obvious win. **Decide whether it is wanted before scoping it.**

**C2 · Cognitive Diplomacy** — 5% owned, and IAS-F1 §3.4 *constitutionally excludes* the
external world: "the ensemble… does not include the external world, the model provider, or
the host machine." This needs a **boundary amendment**, not an extension. Constitutional
change precedes build.

### Tier D — already proposed, still unresolved (not new work)

The open CPP-ACI STOP #1 already proposes **Tier 0 Foundations (F1 glossary, F2 object
registry, F3 provenance standard)** and **M1 Meta-Institutional Control Plane**. This audit
independently confirms both as real gaps: three rival `CANONICAL_ONTOLOGY.md` files exist
today, and no single federation governs the 70+ modules. **These are not new — they are the
existing gate's proposal, now corroborated.** Rule on that gate rather than re-proposing.

## 4. Build order (dependency)

```
D (Tier 0 foundations)  ─┐   glossary + object registry must precede anything that
                         │   defines a term, or B2 has nothing to unify against
                         ▼
B2 epistemic unification ─┴─► A2 theory generator   (needs one evidence algebra to induce over)
B1 unknown-unknowns      ────► A2                   (a generator needs the unmapped surface)
A1 Cognitive Education   ────  independent — no upstream dependency, can start immediately
B4..B9                   ────  independent Parts, parallel, each gated by its parent's owner
B3                       ────  wiring; last, depends on nothing but touches the most
C1, C2                   ────  blocked on Owner decision
```

**A1 is the only Tier-A item with no upstream dependency.** If a single unit of work is
authorized, it is that one.

## 5. Honest limitations of this boundary

**The D2A engine did not corroborate this.** The 15 merged candidates were run through the
fixed `run_family`; it returned 15/15 KEEP, but **most at exactly 45% — the plausibility
cap.** `run_family` reads "coverage < 50" as *"genuinely new, no sealed parent"* when the
capped value actually means *"could not confidently name a parent."* **DEFER is being
reported as KEEP.** This is a defect introduced by the plausibility floor in `314ad9a`, now
recorded: `run_family` needs a third verdict distinct from KEEP. Until then its output on
pre-filtered remainders is not evidence, and this boundary rests on the content-tier
verification alone.

**Coverage percentages are judgments, not measurements.** They are defensible and each is
backed by a verbatim quote plus a named absence, but they are not instrument readings.

**Two Sciences were spot-checked, not fully audited** (X, XI) — both moved toward ABSORB,
so the risk of that shallower pass is over-building, and both landed at "no material
remainder", which is the safe direction.

## 6. What this replaces

| proposed | verified |
|---|---|
| CPCSF: 45 systems, 12 sibling corpora | — |
| CPCSC: 238 jurisdictions, 12 substrates, 12 civilizations | — |
| CPP-ACI: 12 sciences, 15 strata, 36 systems, 25 engines | — |
| **combined ~500k–1M words** | **2 datasets + 9 Parts + 2 decisions** |

`T-CPCSC-SPEC-NOT-MANDATE-001` confirmed empirically: a 238-jurisdiction specification is a
high-value architectural hypothesis, not an implementation mandate. Of 32 domains verified
at content tier, **2 justified a dataset.**
