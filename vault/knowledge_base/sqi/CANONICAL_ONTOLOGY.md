# SQI — Canonical Ontology & Shared Schemas

> **Sovereign Quality Intelligence — the Verification axis of Claude Power Pack.**
> Founded 2026-07-12. Architecture approved at STOP #1
> (`vault/plans/sqi-uqios-architecture-2026-07-12.md`).
>
> This file is the **spine**. Every SQI dataset binds to the terms, objects, scales, and
> prohibitions defined here. A dataset that invents a term incompatible with this ontology
> is rejected and rewritten — no exceptions, no local dialects.

---

## 0. What SQI governs, and what it must never re-govern

SQI answers exactly one question that no other PP system answers:

> **Is the executable reality actually verified — and what evidence licenses that claim?**

It is the *ex-post* verification axis. It is **not** a decision kernel, **not** an epistemic
ladder, **not** a knowledge graph, and **not** an insight router. Those exist. SQI composes
them.

### 0.1 The Parent Substrate (composed, never re-narrated)

| Capability | Canonical owner | SQI's relationship |
|---|---|---|
| Evidence / confidence ladder (E0–E7) | **ACIS** `acis_00_epistemic_ladder_and_theorem_schema.md` | **cross-reference only** |
| Falsifier discipline, No-Autopromotion | **ACIS** | cross-reference only |
| Quality-law / theorem registry | **ACIS-01** candidate laws | SQI proposes E2 records *into* it |
| Decision correctness, verdict authority, blast radius | **DRK** (DRK-00…07) | cross-reference; SQI supplies verification evidence *to* DRK |
| Evidence burden by reversibility | **DRK-03** | cross-reference only |
| Insight → Hard Rule / Trap / dataset Part / benchmark routing | **FD-03** | **DO NOT BUILD.** SQI routes *through* FD-03 |
| Knowledge / coordinate graph | **graphify** GK-00…12 | **never fork a second graph** |
| Bug → Invariant / Hard Rule compilation | `modules/hard_rules` (`bug_to_hardrule`) | cross-reference only |
| Premise / assumption kill gate | `modules/error_prevention/premise_verifier.py` + HR-PREMISE-001 | cross-reference only |
| Done-gate scoring (OQS) | `modules/output_contracts` + HR-OUTPUT-001/002/003 | **EXTEND**, never shadow |
| F1–F8 failure taxonomy | `vault/knowledge_base/testing/testing_failure_taxonomy.md` (SCS C81) | **EXTEND** — F1–F8 is the spine |
| V-gates ×3 hermetic standard | `testing_universal_standards.md` (SCS C81) | **EXTEND** |
| Error recurrence counting | `modules/cascade_prevention` (CEPS) | cross-reference; SQI supplies the R-ladder |
| Autonomous QA execution + visual verdict | `modules/sleepless_qa` | **EXTEND** |
| Test generation | `modules/auto-testing` | **EXTEND** |
| Test-quality linting (AAA, Proof Triad, false positives) | `modules/uqf` | **EXTEND** |

**Sealed as `T-SQI-PARALLEL-SYSTEM-001`.** A capability in the table above is a
cross-reference, not a build. Forking one is a defect, not a feature.

---

## 1. Canonical objects

Nine objects. Every SQI dataset that produces, consumes, or transforms state does so
through one of these. Field names are normative.

### 1.1 `FailureRecord` — the universal failure unit

Every observed failure produces exactly one. It is the atom the whole compounding
pipeline is built on.

```
FailureRecord
  failure_id            stable identifier, append-only
  repository            repo the failure was observed in
  commit                exact commit at observation
  component             the unit that failed (file:symbol where knowable)
  environment           EnvironmentRecord reference
  trigger               what initiated the failing path
  expected_behaviour    the contract that was supposed to hold
  observed_behaviour    what actually happened (verbatim, not paraphrased)
  production_consequence what a user/operator loses if this ships
  failure_class         F1..F8 (+ subclass) — the SEALED C81 taxonomy
  origin_axis           product | test | fixture | environment | config |
                        toolchain | data | dependency | ci | hardware | observability
  behaviour_axis        deterministic | flaky | order-dependent | time-dependent |
                        state-dependent | host-polluting | resource-sensitive |
                        concurrency-sensitive | network-sensitive
  detectability_axis    visible | silent | misleading-green | false-negative |
                        false-positive | unverified
  root_cause            demonstrated, not hypothesized
  contributing_causes   list
  why_controls_failed   the governance answer, not the code answer
  reproduction          the minimal command/state that reproduces
  evidence              EvidenceRecord references
  regression            RegressionRecord reference (mandatory to close)
  invariant             InvariantRecord reference (where one is derivable)
  cross_repo_exposure   repos plausibly carrying the same pattern
  epistemic_level       ACIS E0..E7 — NEVER a locally-invented scale
  recurrence_level      R0..R4
  residual_risk         what remains unknown after the fix
```

**Contract.** A `FailureRecord` whose `root_cause` is populated but whose
`epistemic_level` is below E3 is a *hypothesis wearing a root-cause label*. The field
must be demoted, not the level inflated.

### 1.2 `QualityClaim` — any assertion about verified state

```
QualityClaim
  claim_id
  statement           the exact assertion ("suite X passes", "surface Y is protected")
  scope               what the claim does NOT cover, stated explicitly
  verdict             one of the 12 states (§2)
  evidence            EvidenceRecord references
  epistemic_level     ACIS E0..E7 — the ceiling is set by the weakest evidence
  owner               the agent or human that made the claim
  counterevidence     what was actively sought to refute it
  dissent             unresolved objections, preserved verbatim
  expiry              the condition under which this claim stops being true
  verification_status
```

**Contract.** No `QualityClaim` may carry a verdict stronger than its weakest
`EvidenceRecord` admits. This is the **Limiting Evidence Law** (§6).

### 1.3 `EvidenceRecord` — what makes a claim admissible

```
EvidenceRecord
  evidence_id
  admissibility     STRONG | MEDIUM | WEAK (§3)
  kind              runner-output | artifact | hash | observation | replay |
                    hardware-capture | static-analysis | reasoning
  command           the exact command executed (never a description of it)
  output            the observed output (never a summary that replaces it)
  artifacts         paths + content hashes
  environment       EnvironmentRecord reference
  timestamp
  agent             who produced it
  chain_of_custody  every transformation applied between capture and citation
  supports          QualityClaim / FailureRecord references
  independence      whether a different actor/substrate produced it
```

**Contract.** `kind: reasoning` is **always** WEAK, regardless of how convincing the
reasoning is. Agent reasoning is not evidence about executable reality — it is a
hypothesis about it.

### 1.4 `EnvironmentRecord` — qualification state

```
EnvironmentRecord
  environment_id
  qualification   QUALIFIED | PARTIALLY-QUALIFIED | BLOCKED |
                  HARDWARE-REQUIRED | UNSUPPORTED | UNKNOWN
  language_versions / runtime_versions / toolchain
  lockfile_state  present-and-current | present-and-stale | absent
  services        required external services and their provisioning contract
  host            os, arch, cpu
  blockers        what prevents qualification, verbatim
```

**Contract.** A test result produced in a non-`QUALIFIED` environment cannot yield a
verdict stronger than `ENVIRONMENT-INVALID` or `UNVERIFIED`. It can never yield `FAILED`
attributed to the product — that is the canonical fault-attribution error.

### 1.5 `RegressionRecord`

```
RegressionRecord
  regression_id
  failure_id           the failure this permanently prevents
  test_path            where the preventing test lives
  failed_before        observed RED against the unfixed code — MANDATORY
  passes_after         observed GREEN against the fixed code
  regression_class     the family it guards, not just the instance
  hermetic_replay      observed identical across ×3 runs
  in_canonical_invocation  whether the default runner actually reaches it
```

**Contract.** `failed_before` unobserved means the test proves nothing. A regression test
that was never seen to fail may be asserting a tautology. This is RED-before-GREEN as a
data field, not a suggestion.

`in_canonical_invocation: false` means the regression **protects nothing** — see the
Execution Reality Law (§6).

### 1.6 `InvariantRecord`

```
InvariantRecord
  invariant_id
  statement          the property that must always hold
  derived_from       FailureRecord references
  enforcement        the gate/detector that makes it structural (or: NONE)
  scope              repos / domains where it applies
  falsifier          what observation would disprove it — MANDATORY (ACIS discipline)
  epistemic_level    ACIS E0..E7
```

**Contract.** An invariant with `enforcement: NONE` is documentation, not governance
(§6, Executable Governance Law). An invariant with no `falsifier` is not a weak invariant
— it is a **non-invariant** (inherited from ACIS).

### 1.7 `CertificationRecord`

```
CertificationRecord
  certification_id
  subject            repo / component / change
  commit
  environment        EnvironmentRecord reference
  verdict            one of the 12 states (§2)
  confidence_vector  per-dimension, NEVER a single averaged number (§5)
  baselines          the counts/surfaces this certification asserts
  risks_covered / risks_open
  evidence           EvidenceRecord references
  scope              stated exclusions
  expiry_conditions  what revokes this automatically
  issued_by          MUST differ from the producer of the change (No-Autopromotion)
```

**Contract.** Every certification is **scoped and expirable**. A certification without an
expiry condition is a claim of permanence that no evidence can license.

### 1.8 `PolicyRecord`

```
PolicyRecord
  policy_id
  statement / motivation
  enforcement        the executable check that makes it real
  applicable_repos
  exceptions         WaiverRecords, each with an expiry
  metric / countermetric   (anti-Goodhart: never a metric alone — §5)
  failure_cases      what it was born from
  version
```

### 1.9 `BenchmarkScenario`

```
BenchmarkScenario
  scenario_id
  family             the trap class it embodies
  seeded_defect      the deliberate flaw the pipeline must detect
  expected_detection what a correct SQI pass must report
  false_positive_trap what a naive detector would wrongly flag
  derived_from       FailureRecord reference (real origin, never invented)
```

**Contract.** A `BenchmarkScenario` with no `derived_from` is a synthetic exercise, not a
regression guard against real history. Both are allowed; only the first is evidence.

### 1.10 `HypothesisRecord`

```
HypothesisRecord
  hypothesis_id
  statement
  evidence_for / evidence_against
  prediction              what must be observed if true
  discriminating_experiment  the SMALLEST test that separates it from rivals
  cost / risk
  status              live | eliminated | confirmed
```

**Contract.** Hypotheses live in a tournament (SQI-08). A single surviving hypothesis
that was never contested is not a root cause — it is the first plausible story.

---

## 2. Verdict ontology — the twelve states

`PASS` **does not exist** as a general simplification. It collapses "verified" with
"not observed to fail", and that collapse is the origin of the misleading-green class.

| verdict | meaning |
|---|---|
| `PROVEN` | reproducible evidence, canonical invocation, hermetic replay observed |
| `CONDITIONALLY-PROVEN` | proven within an explicitly stated, narrower scope |
| `PARTIALLY-VERIFIED` | some surfaces verified, others explicitly not |
| `UNVERIFIED` | not executed, not reached, or evidence never produced |
| `BLOCKED` | could not be executed — environment, toolchain, or dependency |
| `INCONCLUSIVE` | executed, but the result does not discriminate |
| `FAILED` | reproducibly fails, attributed to the product |
| `REGRESSED` | previously proven, now failing |
| `ENVIRONMENT-INVALID` | the failure belongs to the environment, not the product |
| `EVIDENCE-REJECTED` | evidence was offered and found inadmissible |
| `N/A` | the surface genuinely does not exist (e.g. no executable code) |
| `WAIVED-WITH-LIABILITY` | consciously accepted, with owner + expiry + compensating control |

**Contract.** Absence of a failure signal maps to `UNVERIFIED`, never to `PROVEN`. This
is the single most-violated rule in the audited history and the reason the state list
exists at all.

---

## 3. Evidence admissibility

Three tiers. The tier is a property of the **method**, not of the confidence of the
person citing it.

**STRONG** — deterministic reproduction · complete runner output · signed/hashed
artifacts · independent observation by a different actor or substrate · before/after
comparison · real-hardware capture where the surface requires it.

**MEDIUM** — a directed test · partial logs · a valid simulation · static analysis.

**WEAK** — agent reasoning · code read but not executed · absence of an error message ·
a summarized output that replaces the output · the producer's own assertion.

**Binding rule.** Admissibility caps the epistemic level, and the epistemic level is
**ACIS's E0–E7 ladder** — SQI does not define a competing confidence scale. WEAK evidence
cannot license an E3+ claim no matter how much of it is accumulated. Volume of weak
evidence is not strength; it is repetition.

---

## 4. The ladders

### 4.1 Risk ladder — Q0…Q5 (what process a change must pass)

| level | surface | requirement |
|---|---|---|
| **Q0** | no functional impact (text, comments, formatting) | scope check only |
| **Q1** | local, reversible | directed test · component suite · baseline intact |
| **Q2** | ordinary functional change | predicted impact · directed + integration · regression · affected full suite |
| **Q3** | data · permissions · money · auth · deploy · persistence · recovery · external contracts | separation of powers · adversarial pass · proven rollback · reproducible evidence · independent audit |
| **Q4** | irreversible deletion · credentials · payments · destructive migration · core infra · hardware · agent control | full adjudication · two independent verifications · blast-radius analysis · fault injection · real rollback · quarantine where applicable |
| **Q5** | changes to SQI itself (gates, policies, evidence criteria, risk models) | highest standard. **An agent may not modify the rules that evaluate it within the same task.** |

Q3+ composes **DRK** for the reversibility/blast-radius computation. SQI does not
recompute it.

### 4.2 Maturity ladder — L1…L7 (what the QA capability itself can do)

L1 Inventory · L2 Execution · L3 Diagnosis · L4 Risk Intelligence ·
L5 Autonomous Remediation · L6 Cross-Repo Learning · L7 Self-Evolving Quality Science.

A repo's level is **observed**, never declared. A repo with a green suite that has never
been reconciled against its authored surface is L2 at most, regardless of test count.

### 4.3 Recurrence liability — R0…R4 (a repeat is a learning failure)

| level | condition | what it indicts |
|---|---|---|
| **R0** | first observation | nothing — this is how learning starts |
| **R1** | recurs, no gate was ever built | institutionalization failure |
| **R2** | recurs despite an existing gate | enforcement failure |
| **R3** | recurs *and was masked by a green signal* | governance failure |
| **R4** | recurs in critical production | constitutional failure |

**Contract.** A recurrence is never scored as an independent incident. It is scored as
evidence that the prior learning was insufficient. Severity escalates with R-level even
when the technical impact is identical.

Recurrence *counting* is supplied by CEPS (`modules/cascade_prevention`). SQI supplies
the **liability interpretation**, not a second counter.

---

## 5. Metrics — and the anti-Goodhart contract

**No metric ships alone.** Every metric is paired with a countermetric that becomes
adversarial under gaming. This is inherited from FD-00 §III.1 and is not re-derived here.

| metric | mandatory countermetric |
|---|---|
| test count | risk-weighted coverage |
| coverage % | mutation adequacy |
| pass rate | executed surface (authored-vs-executed reach) |
| suite speed | evidence completeness |
| fewer incidents | detection sensitivity |

Two supreme measures for the family:

- **IFI — Institutionalized Failure Intelligence** = failures institutionalized ÷ failures
  observed. A system with few failures and a low IFI is learning nothing.
- **HQR — Honest Quality Ratio** = claims supported by admissible evidence ÷ total quality
  claims. The target is not more successes; it is that every claim is true, scoped, and
  reproducible.

---

## 6. The Quality Laws (SQI's binding invariants)

Each is falsifiable, each cites the observation that produced it. These are proposed into
the **ACIS** law registry as E2 records — SQI does not maintain a rival registry.

**L1 — Execution Reality Law.** A test that is not executed protects exactly what a
non-existent test protects: nothing.
*Falsifier:* an unexecuted test demonstrably preventing a defect.
*Origin:* PP — 70 of 76 test files outside the canonical invocation; TUA-X — 390 tests
orphaned by `testpaths` (SCS C81).

**L2 — Limiting Evidence Law.** The strength of a conclusion can never exceed the strength
of its weakest supporting evidence.
*Falsifier:* a `PROVEN` verdict whose only support is WEAK evidence, holding under
independent re-verification.

**L3 — Recurrence Law.** A repeated failure is primarily a learning failure, not an
implementation failure.
*Falsifier:* a recurrence with a fully-enforced gate, correct taxonomy, and cross-repo
scan already in place.

**L4 — Hidden Surface Law.** Aggregate figures conceal unprotected regions. A high total
with an unexamined distribution is a claim about volume, not about protection.
*Origin:* KobiiCraft — 1,596 green assertions, `EconomyService` with zero test references
(`T-MINECRAFT-TESTING-CONCENTRATION-001`).

**L5 — Expirable Certification Law.** Every certification is bound to a specific
environment and surface and can lose validity without any code changing.

**L6 — Executable Governance Law.** A policy without enforcement is documentation. An
invariant without a detector is a wish.

**L7 — Attribution Law.** A failure observed in an unqualified environment may not be
attributed to the product.
*Origin:* GEO-audit — a test polluting the host drive root broke a sibling suite; the
product logic was correct (SCS C81).

**L8 — No-Autopromotion (inherited, ACIS).** The producer of a claim never certifies it.
Consensus among agents of the same model is not independent evidence
(`T-ACIS-MODEL-CONSENSUS-001`).

---

## 7. The compounding pipeline (`PR-SQI-COMPOUND-INTELLIGENCE-001`)

Every failure must be able to yield **at least four** permanent assets. Each SQI dataset
must define its own slice of this chain explicitly; a dataset that does not is incomplete
by definition.

```
Failure
  → FailureRecord              (causal asset)
  → RegressionRecord           (preventive asset)
  → InvariantRecord            (structural asset)
  → training example: negative + positive   (learning asset)
  → BenchmarkScenario          (evaluative asset)
  → gate candidate
  → PolicyRecord candidate
  → cross-repo exposure scan
  → quality-law hypothesis  → proposed into ACIS at E2
```

**The routing itself is FD-03's job.** SQI produces the records; FD-03 transmutes an
insight into its destination form (Hard Rule / Process Rule / Trap / dataset Part /
benchmark / prompt fragment / discard). SQI **must not** implement a second router.

An incident is not closed when it is fixed. It is closed when its **class** is harder to
repeat in every repo — or when a documented reason says otherwise.

---

## 8. Vocabulary discipline

The SQI corpus is a quality/verification system. It carries **no** commercial-operations
semantics — none of the vocabulary of trade, retail, promotion, or demand research, either as
subject matter or as system identity. The reference corpus consulted during design contributed
**fabrication attributes only** (Part depth, structural density, the FINAL LAW convention);
zero concepts, names, or domain semantics were imported.

(This paragraph is deliberately written around its subject rather than through it. An earlier
revision named one of the quarantined words in order to prohibit it — stating the rule by
committing it — and the gate, once taught to scan governance files, found it here in the very
section that forbids it. The enumeration lives in the detector; see §8.2.)

Two consequences, both binding:

1. **Approved substitutes.** Where a commerce-adjacent word would be the natural English
   choice for a purely internal transformation, SQI uses **transmutation** and
   **institutionalization**. This keeps the contamination audit literal and cheap: it can
   grep for banned literals and legitimately expect zero hits, with no escape-hatch
   reasoning about context.

2. **The banned register lives in code, not prose.** The enumerated literal list is held
   by the audit tool and assembled at runtime. It is deliberately not spelled out in this
   file: a vault document that enumerates forbidden literals trips PP's own content gate,
   which cannot distinguish a detector's vocabulary from a violation
   (`feedback_kb_prose_naming_slop_tokens_trips_write_gate.md`).

Neutral mentions of a *repository type* are permitted where a domain profile genuinely
requires one; such a mention may never become part of SQI's identity, mission, or
subject matter.

---

## 9. Naming and file conventions

- Datasets: `vault/knowledge_base/sqi/sqi_NN_<snake_name>_v1.txt`
- Structure: `PART I` … `PART XX`, each closed by `PART N FINAL LAW`
- Prose density: dense continuous prose, numbered subsections, arrow flows. No markdown
  headings, no bullet lists, no tables, no code fences inside a dataset `.txt`.
- Depth: **1,200–1,500 words per Part** (operational tier). Flagship Parts may exceed it
  where complexity genuinely sustains the depth. **Padding to reach a count is a rejection
  condition, not a strategy.**
- Governance artifacts (this file, the index, the audits) are markdown and exempt from the
  dataset structure rules.

---

## 10. Status

This ontology is **binding as of its first commit**. Amendments are Q5 changes: they
require the highest standard, and no agent may amend it inside the same task in which it
is being evaluated against it.
