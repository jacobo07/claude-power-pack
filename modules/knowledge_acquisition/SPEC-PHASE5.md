---
spec: SPEC-KACQ-005
title: Question-conditioned assessment and source-boundary honesty
tier: 3
status: APPROVED
supersedes: none
extends: SPEC-KACQ-001
covers:
  - knowledge-acquisition-phase5
  - answer-quality-classification
  - epistemic-classification
  - source-capability-profile
  - source-boundary-ledger
  - question-conditioned-evaluation
  - context-bleed-provenance
  - single-source-interrogation
  - expert-routing-gap
  - eva-classification
---

# SPEC-KACQ-005 — Assessment at acquisition time

Extends SPEC-KACQ-001 (durable acquisition). That spec guaranteed an answer is
never lost. This one decides what an answer is *worth*, at the moment it lands,
without ever putting the raw capture at risk.

## 1. Why this exists, measured

Eight answers were captured live from EVA on 2026-08-26 and read in full before
this spec was written. Four facts came out of that reading, and every contract
below traces to one of them.

**F1 — the source disclaims access and then quantifies the same cohort.**
SF30-022: *"en Consultoria.io no tenemos acceso a los datos financieros
detallados de otros clientes."* SF30-024, two prompts later: *"el 100% de los
casos... corresponden a operadores con experiencia"*, plus a probability table
(2k -> 0%, 25k -> 1-5%, 50k -> 5-15%). SF30-021 does both **inside one answer**:
*"No tengo un número exacto"* followed by *"el 100% de los casos que alcanzan
100.000 EUR/$ en los primeros 30 días corresponden a nuevas tiendas de
operadores con experiencia"*.

A per-answer GOOD/BAD verdict cannot express this. The refusal and the
unsourced statistic are both true of the same text.

**F2 — personalization is subject substitution, not framing.** 8/8 answers open
"Jacobo," and retarget to Fitthouse.com. SF30-020 asked about **CW Ops** and the
answer begins *"para que Fitthouse.com (CW Ops)..."* — the subject of the
question was silently replaced. Promoting a claim from this corpus without its
context boundary yields advice about a different business.

**F3 — context bleed crosses sessions, not just prompts.** SF30-024 refers to
*"la micro-validación de problema que te propuse"* — advice never given in this
run. The account carries memory the client cannot clear. `ISOLATED` mode cannot
deliver isolation; that guarantee is not ours to make.

**F4 — the revenue/profit defect does not exist here.** EVA volunteers
contribution profit over vanity revenue, margin bands, ROAS-vs-breakeven and
CAC ceilings unprompted. No detector is built for a defect the source does not
exhibit.

## 2. Ownership — what is reused, verbatim

Measured before designing. ~85% of this capability already exists.

| Capability | Owner | Use |
|---|---|---|
| Epistemic levels, rank, degrade-only default | `research_engines.py:684-706` | imported |
| `cap_epistemic` deterministic caps | `research_engines.py:835-889` | called unmodified |
| `has_measurable_datum` | `research_engines.py` | imported |
| Coverage verdict vocabulary | `research_engines.py:586-615` | supplied, not forked |
| Unrated-never-silently-passes | `research_quality.py:377-392` | pattern adopted |
| No-Autopromotion invariant | `epistemic_ladder.py:88-117` | respected at deposit |

`craif/authority.py` is a name collision — repair authority, not source
authority. Not an owner.

## 3. The one genuinely new axis

Engine 3's caps key off a **landscape of many sources per claim**. This corpus
has exactly one source, always the same one, and it sells the programme it
cites. Run the existing contract unchanged and `landscape_verdict` returns
`VENDOR_ONLY` for every answer, which caps all 2,200 at `REJECTED` — technically
defensible, operationally useless, and it would discard F1 rather than describe
it.

In single-source interrogation there is no second source to corroborate
against, but there is a signal nobody was using: **the source's own declared
boundaries**. A quantified claim about a population the same source said it
cannot see is unsourced by the source's own admission — and detecting it costs
no second source.

That is the whole of what is built here.

## 4. Contracts

### 4.1 Expected evidence (question-conditioned)

Derived from the prompt's text and family; never hand-authored per prompt. A
methodology answer to a methodology question is excellent; the same answer to a
case-data question is a gap. Grading all answers on one scale is prohibited.

### 4.2 Source boundary ledger

Append-only, per interface. Distinguishes two kinds that must never be
conflated:

- **ACCESS** — the source states it does not have the data
  (*"no tenemos acceso a los datos financieros de otros clientes"*).
  Scope-bearing, load-bearing.
- **VARIABILITY** — the source declines to generalise
  (*"no hay un número mágico universal, depende del producto"*).
  A hedge, not a gap. Records nothing about capability.

Collapsing these would classify SF30-025's honest hedge as a capability gap and
route a perfectly answerable question to a human expert.

### 4.3 Coverage substitution, not a fork

`cap_epistemic` is called unmodified. What changes is the coverage value handed
to it:

- baseline for a single unverifiable expert source -> `UNCLASSIFIED`
  (caps at DERIVED: provenance cannot be established, but the work is kept)
- a claim crossing a recorded ACCESS boundary -> `VENDOR_ONLY`
  (-> REJECTED: unsourced by the source's own admission)

`VERIFIED` is unreachable by construction: supporting_sources is always 1.

### 4.4 Context boundary preserved in provenance

Detected personalization is recorded on the assessment, never stripped and
never scored away. A claim conditioned on the operator's own business cannot be
promoted as universal doctrine. Hard constraint, not a weight.

### 4.5 Disposition, not a grade

Classification resolves to a workflow action: extractable / deepen /
source-limited / unverifiable-claim / low-value / human. Follow-up candidates
are generated and stored; **none are auto-executed**.

### 4.6 Raw sovereignty

Assessment runs after the raw artifact and its row are durable. It is derived,
versioned by classifier version, and reproducible from raw. An assessment
failure is recorded as unrated and can never fail a capture, mutate raw, or
change a job's state.

## 5. Acceptance — falsifiable before it runs

Stated against answers already measured, so the gate cannot be tuned to pass.

| Case | Required outcome |
|---|---|
| SF30-022 (refuses + teaches) | NOT low-value; ACCESS boundary recorded; source-limited |
| SF30-024 (cohort statistics) | NOT high-confidence; boundary-crossing flagged; REJECTED epistemic |
| SF30-021 (both in one answer) | boundary recorded AND crossing flagged from the same text |
| SF30-020 (wrong subject) | context-bound, with the substitution preserved |
| SF30-025 (honest hedge) | VARIABILITY only; **against an empty ledger** it must NOT be SOURCE_LIMITED |
| SF30-025 against the filled ledger | SOURCE_LIMITED — a real prior ACCESS declaration governs a new case-data question |
| SF30-018/019 | separate on measurable-datum presence |
| All 8 | context_bound = true |

## 6. Non-goals

Per-claim extraction; standing contradiction detection; automatic frontier
recursion; promotion into institutional truth; marginal-information-gain beyond
a counter; any dashboard; a revenue/profit detector (F4); multi-source
orchestration.

## 7. Done

53 pre-existing tests still green; new unit and adversarial tests green; all
seven acceptance rows satisfied on real stored answers; a live capture observed
end-to-end with assessment attached; raw durability, resume and retry
unaffected.
