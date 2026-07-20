# CPCSC — D2A Reinforcement Findings

> Produced under Owner ruling D-001 (fold into CPP-ACI + D2A-reinforce).
> Per `PR-DUPLICATE-TO-ADVANTAGE-001`: no duplicate ends in bare rejection.

---

## 1. The headline finding — the duplication immune system is blind to ~68% of the estate

`run_family` was executed over all 20 CPCSC domains
(`modules/duplicate_to_advantage/d2a_engine.py --family-file`). Raw verdict: **17 FOLD / 3 KEEP**.

The D2A index carries its own warning: *"the mechanical FOLD/MERGE verdict is a bag-of-words
signal, not a semantic one — sanity-check each FOLD against the matched parent's actual index."*
Sanity-checking every row exposed a defect in the instrument, not in the proposal.

### 1.1 `FAMILY_REGISTRY` coverage, measured

`FAMILY_REGISTRY` (`d2a_engine.py:109`) holds ~32 entries. Cross-referenced against the measured
estate (1,422,209 words):

| Family | words | in registry? |
|---|---|---|
| **d2a_fabric (DAIF-00..08, 21)** | **299,397** | **ABSENT** — the single largest family |
| **CPP-IAS (ias_f1..g1, 14 datasets)** | **478,208** | **ABSENT** |
| **pp_dataset (23 Sovereign systems)** | **86,082** | **ABSENT** |
| **dataset_first (DFP)** | **44,775** | **ABSENT** |
| testing | 21,457 | ABSENT |
| setup_os | 19,223 | ABSENT |
| session_resilience | 15,550 | ABSENT |
| scs | 8,837 | ABSENT |
| sqi | 119,080 | **PARTIAL — only SQI-02 of 4 datasets** |
| decision_review | 27,368 | **PARTIAL — only DRK-01/02/03 of 7** |
| CO · PM · GK · FD · FIOS · CDIO · ACIS · CrawlOS · HR · SPEC-GATE | — | present |

**Unregistered or invisible: ~973,500 of 1,422,209 words ≈ 68% of the estate.**

### 1.2 Both error directions are live, with named instances

**FALSE FOLD** — the true owner is unregistered, so the engine matches the nearest registered
vocabulary and reports high confidence in a wrong parent:

| domain | engine verdict | why it is wrong | true owner |
|---|---|---|---|
| Reasoning Compiler | 92% → SQI-02 *Test Reach* | shares "coverage/signal/verification" tokens | **DAIF-02 CIR Fabric** (34,827 w, unregistered) |
| Cognitive Education | 89% → SQI-02 *Test Reach* | shares "certification/benchmark/coverage" | none found — this is the clean NEW domain |
| World Model Federation | 89% → PM-02 *Pane Collision Detector* | shares "collision/contradiction/model" | **ias_f1_federation_ontology** (28,613 w, unregistered) |
| Digital Twin | 92% → GK-08 *Knowledge Writeback* | shares "graph/state/registry" | **ias_f3_digital_twin** (32,802 w, unregistered) |
| Constitution · Hierarchical Memory · Scientific Gov · Diplomacy · Civilizational Gov | 80–92% → **HR** | HR is a catch-all attractor: 5 of 17 FOLDs land on it | various, mostly unregistered |

**FALSE KEEP** — the owner is unregistered, so a real duplicate is declared genuinely new:

| domain | engine verdict | reality |
|---|---|---|
| **Counterfactual Intelligence** | KEEP, coverage 13%, "genuinely new" | `decision_review/drk_04_counterfactual_simulation_horizons.md` **exists**, 4,148 w. DRK-04 is not in the registry. |

A false KEEP is the more dangerous class: a false FOLD wastes an audit cycle, a false KEEP
authorizes building something that already exists — the exact failure D2A was sealed to prevent.

---

## 2. This is the third instance of one pattern in a single session

| # | instance | denominator error |
|---|---|---|
| 1 | 2026-07-12 CPP-ACI audit measured knowledge_base at "~524,000 words" | CPP-IAS (478k) sat outside the repo boundary |
| 2 | Liveness Ledger audited 8 hand-declared components (`PR-COVERAGE-BY-CONSTRUCTION-001`) | an undeclared component was absent from the denominator, and absence read as health |
| 3 | **D2A `FAMILY_REGISTRY`, hand-curated, blind to 68% of the estate** | unregistered families cannot be matched, so duplicates read as novel |

The project's own corollary already names the law: *an audit whose subjects are enrolled by hand
measures memory, not reality.* It was written about the Liveness Ledger. It applies unchanged to
the D2A registry — which is the estate's duplication immune system, and therefore the worst
possible place for it to be true.

---

## 3. Recommended reinforcement — the D2A operation is `AUTOMATE`, not a dataset

Under the anti-inflation contract (`T-D2A-ANTIINFLATION-VIOLATION-001`: a new dataset must beat a
new Part, a new rule, a new eval, and not-building), the highest-value artifact here is **not a
CPCSC dataset**. It is:

**R1 — Derive `FAMILY_REGISTRY` from the filesystem instead of curating it by hand.**
Discover families from `vault/knowledge_base/*/` + declared external corpus roots; fail loudly on
an unregistered family rather than silently matching the nearest vocabulary. Operation:
`AUTOMATE`. Reinforces: D2A-1 Duplicate Detection Core. This converts the registry from memory
into measurement and closes all three instances above at the mechanism level.

**R2 — Add a confidence floor + parent-plausibility check.** An 89% match to a parent whose
declared jurisdiction does not intersect the proposal's domain should DEFER, not FOLD. The HR
catch-all attractor (5 of 17) is detectable: HR matched five unrelated domains at 80–92%.
Operation: `HARDEN`. Reinforces: D2A-1.

**R3 — New V-gate `V-D2A-REGISTRY-COMPLETE`.** Assert every `vault/knowledge_base/*/` domain
resolves to a registry entry. Fails today by name, on 7 domains. Operation: `EVALUATE`.

**R4 — Repatriate CPP-IAS (478,208 w) into version control** so it is inside every future
denominator. Operation: `PORT`. Independent of the corpus decision.

**R5 — Cognitive Education** remains the sole clean-NEW domain — genuinely absent, and the
engine's 89% FOLD against it is a demonstrated false positive. Build candidate, pending the
verifier's gap confirmation.

---

## 4. UKDL candidate

**`T-D2A-REGISTRY-BLIND-SPOT-001`** — a duplication detector whose parent registry is
hand-curated will report false-NEW for every family nobody remembered to enroll, and will bind
false-parents at high confidence for the rest by matching the nearest registered vocabulary.
Measured 2026-07-20: 68% of the estate unregistered; one false KEEP (Counterfactual vs DRK-04)
and four named false FOLDs. **Any registry a gate depends on must be DISCOVERED from the
filesystem, never curated.** Sibling of `PR-COVERAGE-BY-CONSTRUCTION-001`.
