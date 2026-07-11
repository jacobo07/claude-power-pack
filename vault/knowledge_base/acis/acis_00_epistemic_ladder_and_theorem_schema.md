# ACIS-00 — Epistemic Ladder & Cognitive Infrastructure Theorem Schema

> **Family:** Autopoietic Cognitive Infrastructure System (ACIS). **Verdict:** EXTEND of
> FD-00/01/02 + FIOS harvester + fd_04_prover. **Parent substrate consumed, never rebuilt:**
> the Fable Advantage Distillation Suite (FD-00…FD-07), the Frontier Intelligence OS (FIOS),
> the Cognitive OS (CO-00…CO-12), Duplicate-to-Advantage (D2A), and the UKDL rule ledger.
> **Sealed thesis (ACIS root):** the Power Pack must not memorize a frontier model's best
> ideas — it must use the frontier model to found a self-evolving science that converts
> *reasoning* into *infrastructure*, checks whether that infrastructure improves real
> software, and replaces its own laws when it finds better ones. This dataset supplies the
> one thing no sealed family supplies: **an explicit epistemic level on every claim, and the
> falsifier discipline that governs promotion past hypothesis.**

---

## Part I — The Epistemic Ladder E0–E7 (a naming of the pipeline that already exists)

The single most important property of this ladder: **it invents no new stage.** Every rung
names a state a claim already occupies somewhere in the sealed pipeline. ACIS's contribution
is to make the level *explicit and citable* — today a deposit knows whether it is
`portability_proven`, but nothing states "this claim is at E2 and cannot be called a law." The
ladder closes that gap by mapping level onto the existing substrate one-to-one:

| Level | Name | Where it already lives in the sealed pipeline | Producer (existing) |
|---|---|---|---|
| **E0** | Intuition | an unstructured session note / a PM-03 finding before evidence is attached | the session itself |
| **E1** | Observation | a captured finding carrying a `(metric, source, value)` triple | PM-03 bus + CO-12 telemetry-before-claims contract |
| **E2** | Hypothesis with mechanism | an **FD-07 deposit** — `portability_proven: False`, honest by construction (fd_07_flywheel.py:178) | `run_flywheel` → deposits ledger |
| **E3** | Repeated / transferred evidence | a deposit **probe-PROVEN** (`method="probes"`) or **attested on a second substrate** (`method="attestation"`) | `fd_04_prover.prove()` / `.attest()` |
| **E4** | Operational rule | an **Owner-promoted UKDL rule** (`PR-*` / `T-*`) covering the claim | Owner promotes a UKDL candidate (never auto) |
| **E5** | Portable law | an E4 rule whose proof carries a cross-model `achieved_target` (mid-model / small-model), i.e. it survives a downgrade | `fd_04_prover` with a non-deterministic target + independent-model attestation |
| **E6** | Constitutional invariant | a **Hard Rule** (`HR-*`) — a sealed production kill-switch with TRIGGER/STOP/ORIGEN | Owner seals via the Bug→Hard-Rule protocol |
| **E7** | Meta-generative law | the law that *generates* laws — the K-Router 4-trigger contract, the Bug→Hard-Rule protocol itself | the governance router (fixed) |

The ladder is therefore a **read-only projection** over the deposits ledger, the fd04 proofs
ledger, the UKDL corpus, and the Hard-Rule archive. A derived function (`acis_00`'s companion
code, `epistemic_ladder.py`) computes a claim's level by joining those four existing sources —
it writes nothing, stores nothing, and signals nothing new. This is the same discipline FD
holds toward CO-12: *feed the accountant, never fork it* (SCS C41). ACIS holds the identical
discipline toward the promotion chain: **name the level, never invent a new promotion path.**

### I.1 The strict monotonicity of evidence

Each rung demands strictly more than the one below, and the demand is the *kind* of evidence,
not its quantity:

- **E0 → E1** requires an observation with a source. An intuition with no `(metric, source,
  value)` triple stays E0 — this is CO-12's telemetry-before-claims contract, inherited whole.
- **E1 → E2** requires a *mechanism*: a causal story for *why* the observation holds, not just
  that it was seen. A deposit without a claimed mechanism is a log line, not a hypothesis.
- **E2 → E3** requires the claim to survive **independent re-derivation** — either a
  deterministic probe re-runs and passes (`prove`), or a different substrate re-produces the
  capability (`attest`). This is the FD-04 gate: *a delta that only works with the model that
  produced it has not been distilled; it is a hypothesis until the downgrade is proven.*
- **E3 → E4** requires an **Owner decision**. No automated process promotes a claim into an
  operational rule. This is the propose-never-apply invariant, inherited from evolution_engine
  and HR-SECRET-003's recommend-and-wait discipline.
- **E4 → E5** requires the rule's proof to name a **cross-model target** — the capability
  works on Opus/Sonnet/deterministic, not only on Fable. An E4 rule proven only on the
  frontier substrate is operationally real but not yet *portable*; it stays E4.
- **E5 → E6** requires the Owner to seal a **Hard Rule** — a kill-switch with an empirical
  ORIGEN (a real production bug). A portable law becomes constitutional only when its violation
  has been shown to cause harm and a STOP ritual is defined.
- **E6 → E7** is not a promotion a session performs; E7 is the small fixed set of laws that
  generate the others (the router, the Bug→HR protocol). A session may *propose* an E7
  candidate, but E7 membership is a constitutional act reserved to the Owner alone.

### I.2 The No-Autopromotion Invariant (the load-bearing rule of ACIS-00)

> **A claim may never occupy a level its evidence does not license, and the *producer* of the
> claim may never certify the level.** Concretely: a Fable session (or any single model) may
> author E0–E3 claims; it may not declare any claim E4 or higher. E4+ requires an artifact
> authored by a *different* actor — the Owner (E4/E6/E7) or a *different model* re-deriving the
> capability (the cross-model half of E5). Outputs of one model are not independent validation
> of that model's outputs (see `T-ACIS-MODEL-CONSENSUS-001`).

The derived function enforces this mechanically by construction: `epistemic_level(fp)` **caps
at E3** whenever no UKDL rule and no Hard Rule references the fingerprint, *regardless of how
confident the deposit is or how many probes passed*. Confidence is not level. A deposit at
confidence 1.0 with five passing probes is E3, not E4 — because E4 is defined by the existence
of an Owner-authored rule, and that artifact either exists on disk or it does not. The function
reads the disk; it does not reason. A prover that fails open to "proven" is a lie (fd_04
doctrine); by the same token, a ladder that fails open to "operational" is a lie, so it fails
**closed** at E3.

---

## Part II — The Cognitive Infrastructure Theorem Schema

A **theorem** in ACIS is the structured record of a candidate law: a falsifiable claim about
how reasoning becomes durable infrastructure, carried at a declared epistemic level with the
evidence and the destruction attempts that justify it. The schema is a *content convention* —
a shape that acis_01's law records and every future UKDL candidate follow — **not a code
registry.** No new database, no new state machine. A theorem lives as a section in a KB dataset
and, when promoted, as a UKDL entry; its level is *derived* from the pipeline, never stored as
a self-asserted field.

### II.1 The schema fields (every ACIS theorem carries all of them)

| Field | Meaning | Why it is mandatory |
|---|---|---|
| `id` | stable slug (e.g. `ACIS-LAW-WRITEBACK-01`) | genealogy: a claim that cannot be cited cannot be retired |
| `name` | one-line human title | navigation |
| `version` | integer, incremented on any claim change | a mutated law is a new version, not a silent overwrite (UKDL append-only inheritance) |
| `domain` | the axis it governs (compression / transfer / debt / saturation / writeback / evidence / determinization / repeatability) | routes the law to its diagnostic |
| `provenance` | the session + question_ref that produced it | per-question ROI; the deposit that paid for it |
| `epistemic_level` | **derived, never asserted** — computed by `epistemic_level()` from the ledgers | the No-Autopromotion Invariant; a stored level is a self-certification and is forbidden |
| `claim` | the precise falsifiable statement | a claim you cannot state precisely you cannot test |
| `causal_mechanism` | *why* the claim holds — the mechanism, not the correlation | E1→E2 demands it; a law without a mechanism is an observation |
| `application_conditions` | when the law applies | a law that claims universality is usually false |
| `failure_conditions` | when the law does **not** apply | the boundary is half the law |
| `predictions` | what the law forbids from happening | a law that forbids nothing predicts nothing |
| `falsifiers` | the concrete observation that would refute it | **the load-bearing field** — no falsifier, no theorem |
| `counterexamples` | known cases at or near the boundary | honesty about where it strains |
| `evidence` | the `(metric, source, value)` triples supporting it | CO-12 telemetry-before-claims |
| `derivations` | rules/traps/assets derived from it | the Production Impact Chain start |
| `implementations` | the concrete code/hook/gate that enacts it, if any | where theory touches the disk |
| `production_impact_chain` | theory → derivation → rule → Claude-Code decision → change → test → production → evidence → revision | the only path by which a law earns E4+ |
| `confidence` | float — subjective, and *decoupled from level* | confidence is not evidence; the ladder ignores it for promotion |
| `retirement_conditions` | what observation retires or supersedes the law | a law with no retirement condition is dogma, not science |

### II.2 The falsifier is the gate

The schema has exactly one field whose absence voids the record: `falsifiers`. A theorem
without a concrete, observable refutation condition is not a weak theorem — it is *not a
theorem at all*, and the V-gate `V-THEOREM-SCHEMA-COMPLETE` fails the build if any law record
lacks one. This is Popper's line drawn through the pipeline: the claims worth spending frontier
tokens to found are exactly the ones that stick their necks out far enough to be wrong. A law
that "explains everything" — that no observation could contradict — explains nothing and is
discarded at authoring time, not promoted and quietly ignored.

The falsifier must be *operational*: an observation the pipeline can actually make. "The law is
false if reasoning doesn't compress" is not a falsifier. "The law is false if a deposit's
`fd_portability_proven` flips true while the CO-12 cognitive-compression ratio stays flat over
the deposit's Reuse Horizon" is a falsifier — it names a measurement, a signal, and a window.
Every acis_01 law is held to that standard.

### II.3 Retirement is a first-class transition, not a failure

The ACIS thesis includes *"replace its own laws when it finds better ones."* The
`retirement_conditions` field makes retirement a designed operation rather than an embarrassment
to be avoided. A law is retired when its falsifier fires, when a strictly stronger law
subsumes it (D2A `REPLACE` / `RETIRE` operations), or when the domain it governed is
determinized away (the class no longer reaches the frontier). Retirement preserves genealogy:
the retired law's `id` and `version` remain in the UKDL append-only ledger with a pointer to
its successor. Nothing is deleted; a law is superseded the way a deposit is superseded — later
lines win, earlier lines remain auditable. This is the inheritance from UKDL's append-only
discipline and fd_04's append-only proofs ledger, applied to laws.

---

## Part III — Causal Effect-Separation Doctrine & Anti-Goodhart Genealogy

### III.1 Six effects, never conflated

The ACIS thesis demands checking whether infrastructure *"improves real software"* — a claim
that is worthless unless the improvement can be attributed. A capability that appears to work
may owe its success to any of six separable effects, and ACIS forbids collapsing them into a
single "it worked":

1. **Model effect** — the capability owes its result to the frontier model's raw strength. This
   is the effect FD-04 exists to *subtract*: if the capability dies on a downgrade, the model
   was doing the work, and nothing was distilled.
2. **Prompt effect** — the result owes to how the question was posed (FD-02 leverage axes). A
   capability that only works with one exact prompt phrasing is a prompt artifact, not
   infrastructure.
3. **Context effect** — the result owes to what was loaded (GK-06 minimal context pack). A
   capability that needs 40 KB of ambient context has not been compressed.
4. **Planning effect** — the result owes to the plan structure (the ULTRA/ONESHOT scaffold),
   not the model or the rule.
5. **Repository effect** — the result owes to something already on disk (a CO-05 asset, an
   existing rule). This is the DUP that FD-01 must reject at the earliest point.
6. **Time effect** — the result owes to *when* it ran (a fresh baseline, a state that has since
   drifted). Baseline drift is the diagnostic (FD-00 III.1).

A theorem's `causal_mechanism` field must name *which* effect it attributes the capability to,
and its falsifier must be able to distinguish that effect from the other five. A law that
cannot separate the model effect from the repository effect cannot claim to have distilled
anything — it may be re-describing what CO-05 already stores.

### III.2 Anti-Goodhart is inherited, not re-derived

Every ACIS metric is a proxy, and a proxy optimized directly diverges from the target it
proxies. This is not a new insight ACIS contributes — it is **already sealed** in the parent
substrate, and ACIS's contribution is to *point at it*, not restate it:

- FD-00 §III.1 carries the **metric-decoupling (Goodhart)** failure mode and the
  **deposit-count Goodharting** anti-pattern in full.
- FD-07:393 names the CO-12 cognitive-compression ratio as *"the master signal all others are
  subordinate to"* — the single ground truth against which every proxy is checked.
- The CWOPS §4.6 degenerate-feedback trap (training on your own ranked output) is the origin
  cited there.

`T-ACIS-GOODHART-001` is therefore authored as a **genealogy pointer trap**: it records that
ACIS's PCCR proxies (Cognitive IRR, Frontier Dependence Index, Portability Score, Compression
Loss, Reuse Horizon, Production Impact Confidence, Infrastructure Delta, Theory Maturity) are
each anchored to an existing accountant, and that the master check remains the CO-12 ratio —
*not* a new anti-Goodhart mechanism. Re-deriving the anti-Goodhart doctrine here would itself
be the duplication D2A forbids (`DO_NOT_BUILD`). The trap exists to stop a future session from
optimizing a PCCR number while the dependence curve stays flat — the exact volume-theater
failure FD already catalogs.

### III.3 What ACIS-00 deliberately does not build

Honesty gate, stated before the gates check it: the theorem schema is a **content convention**,
so no theorem *registry* code is built; the epistemic level is **derived**, so no level *store*
is built; PCCR metrics **ride CO-12**, so no accountant is forked; the safety constitution is
**the 30+ Hard Rules already sealed**, so no new constitution document is authored — only two
UKDL candidates (no-autopromotion, model-consensus) are proposed for the Owner to promote. The
Knowledge-to-Production Compiler that ACIS's third proposed organism describes is a
**REFERENCE**, not a build: FD-03 already routes every insight to its exact destination (Hard
Rule / Process Rule / Trap / dataset Part / benchmark / prompt fragment / discard) and transmutes
its form — ACIS points at it, it does not rebuild it. The only new code in the entire ACIS
family is one derived function that reads four ledgers and returns a level. Everything else is a
naming, a schema, and a set of falsifiable laws — the E0–E3 work that is exactly what a frontier
session is *for*.
