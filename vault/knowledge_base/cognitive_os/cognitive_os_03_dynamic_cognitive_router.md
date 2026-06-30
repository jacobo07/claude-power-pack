# Cognitive OS — CO-03 — Dynamic Cognitive Router

> The kernel's decision about **how to spend** before it spends. Before any model is
> invoked, the router evaluates a cascade of progressively more expensive resolutions and
> stops at the first that satisfies the task. The expensive model is the *last* resort, not
> the default.
>
> EXTEND, not NEW: unifies the three disjoint routers that exist today —
> `modules/spec_gate/gate.py::classify_tier` (Tier 0–3 / S-M-L-XL), `modules/cost_collapse/
> router.py::route` (NANO/MICRO/MACRO/ULTRA → model + budget), and `cost_gate.py`'s model
> hint — into one cascade. It does **not** replace them; it sequences them and adds the two
> rungs they lack (Vault and reusable-asset resolution).

---

## Part I — The Resolution Cascade

### I.1 The ordered cascade (cheapest-first)

The router evaluates, in strict order, and stops at the first rung that can satisfy the
task to its done-gate:

1. **Knowledge Vault** — has this exact question already been answered and stored? If a
   CO-05 asset (a decision, a mapping, a schema, a prior RCA) resolves the task, the answer
   costs *zero new model tokens*. This is the cheapest possible resolution and therefore
   first.
2. **Reusable asset (Zero Token Layer)** — is there a CO-05 template, rule, or pattern that
   can be *applied* deterministically to produce the answer without reasoning it afresh?
   Applying a stored pattern is near-zero cost.
3. **Deterministic / rules / template / cache** — can the task be resolved by code, a rule,
   a template substitution, or a cache hit (e.g. `audit_cache` hash-match → cached summary)
   rather than a model call at all? The PP already does this in places (audit cache,
   premise verifier); CO-03 makes "is this deterministically resolvable?" an explicit rung.
4. **Haiku** — the task genuinely needs a model, but is mechanical/bounded (format, lint,
   rename, extract, classify, a NANO-class job per `cost_collapse`). Haiku, not Opus.
5. **Sonnet** — standard reasoning/execution: the MICRO/MACRO default. Most real work lands
   here.
6. **Opus** — last resort, justified only by genuine architectural decision, hard multi-step
   reasoning, or iteration-on-error (the ULTRA class). Never the default.

The cascade's discipline is the whole point: the PP's HR-COST-001 already forbids Opus on a
rename, but enforcement is scattered. CO-03 makes the cascade the *single* path every
model-using operation flows through, so "did we check whether a cheaper rung resolves this?"
is answered structurally, not by hoping the model self-selects.

### I.2 Unifying the three existing routers (the EXTEND)

The three routers each hold a piece of the cascade and must stop disagreeing:

- `classify_tier` contributes the **task-shape** read (S/M/L/XL, requires-spec/PRD,
  strategic vs micro). This determines *how far down the cascade* a task is allowed to stop
  — an XL strategic task cannot be resolved at the Haiku rung even if a keyword matched.
- `cost_collapse.route` contributes the **keyword→model+budget** mapping (NANO/MICRO/MACRO/
  ULTRA → model id + $ ceiling). This is the model-selection core of rungs 4–6.
- `cost_gate`'s hint contributes the **budget-pressure** read (when the week is in RED,
  bias the cascade to stop earlier/cheaper).

CO-03's unification is a single decision that consults all three: task-shape bounds the
floor (how cheap is *allowed*), keyword routing picks the model within that bound, and
budget pressure (CO-02) and Cognitive ROI (CO-01) break ties toward cheaper. The
anti-pattern — three routers making three independent keyword decisions that can contradict
— is eliminated by making them inputs to one cascade rather than three exits.

### I.3 Why "Vault and asset first" is the highest-leverage rung

The two rungs CO-03 *adds* (Vault, reusable asset) are where the largest savings live,
because they cost *zero new model tokens*. The PP already reasons about many things
repeatedly across sessions — the same Windows-bash-bridge pivot, the same git-path gap, the
same false-positive catalog. Every one of those, once stored as a CO-05 asset, should be
*retrieved* (rung 1–2), not *re-reasoned* (rung 4–6). CO-03's placement of Vault/asset
resolution *before* any model rung is what operationalizes the Zero Token Layer's promise
(CO-05): the system never pays a model to re-derive what it has already verified and stored.

---

## Part II — The Resolution Gate: "Can this be answered without a model?"

### II.1 The gate question, asked every time

Before rungs 4–6 (any model), CO-03 forces an explicit gate: *can this task be satisfied,
to its done-gate, without invoking a model?* This is not rhetorical — it has concrete
checks: a Vault lookup (semantic match against stored answers), an asset-applicability
check (does a stored template/rule fit), and a determinism check (is the task a
transformation code can do). Only when all three say "no" does the cascade proceed to a
model. The gate is the structural embodiment of "the system never reasons the same thing
twice" (CO-05).

### II.2 Confidence and the false-cheap-resolution risk

The danger of a cheapest-first cascade is a *false* cheap resolution — a Vault answer that
is stale, an asset applied where it does not quite fit, a Haiku output that is wrong because
the task actually needed Sonnet. CO-03 guards this with **confidence thresholds and
done-gate verification**: a cheap-rung resolution is only accepted if (a) its confidence
clears a rung-specific threshold and (b) it passes the task's done-gate. A Vault match below
threshold falls through to the next rung; a Haiku output that fails its gate triggers
escalation (II.3). The cascade optimizes WU/MTok (CO-01), and a wrong cheap answer earns
*zero* Work Units while still costing tokens — so the metric itself punishes false-cheap
resolutions, keeping the cascade honest rather than merely thrifty.

### II.3 Escalation and re-grade (the upward path)

The cascade is cheapest-first, but it is not one-shot. When a rung's resolution fails its
done-gate or its confidence is too low, CO-03 **escalates** to the next rung — Haiku→Sonnet,
Sonnet→Opus — with the failure context attached so the higher rung does not repeat the
miss. Escalation is bounded by the task-shape floor and the budget envelope: a task may
escalate to Opus only if its shape (classify_tier) and budget (CO-02) permit. The escalation
ladder is the honest counterpart to cheapest-first: the kernel starts cheap but is *willing
to pay more when the cheap rung provably failed*, never stubbornly retrying a too-weak rung
(which would violate the 2-consecutive-failures law). Repeated escalation on a task class is
a signal CO-01 records: if "X always escalates to Sonnet", the cascade learns to *start* X at
Sonnet, saving the wasted Haiku attempt.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **False-cheap resolution.** A stale Vault hit or mis-applied asset produces a wrong
  answer. Detection: the done-gate fails, or (worse) passes but the artifact is later
  corrected → the Vault entry is flagged stale and demoted (CO-05 freshness). The WU/MTok for
  that resolution is zero/negative, surfacing the rung as unreliable for that task class.
- **Over-escalation (cost creep).** Tasks escalating to Opus that did not need it. Detection:
  Opus resolutions with low post-hoc difficulty (the Sonnet rung *would* have passed) → the
  escalation threshold for that class is too eager → re-tune.
- **Under-escalation (quality loss).** Tasks stopping at Haiku that needed Sonnet, shipping
  weak work. Detection: low WU/MTok + downstream corrections on a class → raise that class's
  floor. This is the same signal CO-02 watches for harmful downgrades — the two share the
  guardrail that *quality loss shows up as a worse ratio, not a better one*.
- **Router disagreement residue.** If the three unified inputs still produce contradictory
  signals on some task, CO-03 resolves conservatively (respect the *highest* floor any input
  demands) and logs the disagreement for tuning, rather than silently picking one.

### III.2 Rollback protocol

CO-03 sits in front of every model call, so its rollback must be safe: (1) disable the two
*added* rungs (Vault/asset resolution) first — the cascade reverts to the three existing
routers' behavior (model-only routing), which is exactly today's baseline, losing the
zero-token savings but nothing else; (2) if the unification itself misbehaves, fall back to
`cost_collapse.route` alone as the model selector (its current standalone behavior); (3)
confidence thresholds and escalation tuning revert to last-good. At no point does rolling
back CO-03 *raise* cost — the worst case is it stops *saving*, returning to pre-kernel
routing.

### III.3 Integration contract

- **CO-00** — every model rung has a context cost the ceiling projects; the router prefers
  resolutions that grow context least, all else equal (a Vault hit grows context far less
  than an Opus turn).
- **CO-01 / CO-02** — the router ranks rungs by Cognitive ROI (CO-01) and respects the budget
  envelope/downgrade verdicts (CO-02). A CO-02 DOWNGRADE is *executed* by CO-03 choosing a
  cheaper rung.
- **CO-04 / CO-05** — rungs 1–2 *are* CO-05 (assets) and CO-04 (which memory tier holds the
  answer); the router is CO-05's primary consumer.
- **`/loop`** — each iteration routes through the cascade; a loop whose iterations keep
  escalating to Opus is a CO-09 budget alarm.
- **Subagents** — each subagent's model is chosen by the cascade per its task shape (an
  exploration/test/doc subagent routes to Haiku/Sonnet, never Opus — the existing TCO rule).
- **`/compact` `/kclear`** — recovery operations are deterministic (rung 3), never model-
  routed.
- **Knowledge Vault / Cursor** — the Vault rung reads CO-05; routing decisions and their
  realized ROI are themselves stored back as CO-05 assets so the cascade self-tunes.

### III.4 Anti-patterns (forbidden)

- **Opus by default.** Reaching for the most expensive rung without descending the cascade.
  The cascade exists precisely to make this impossible structurally.
- **Three routers, three decisions.** Letting classify_tier, cost_collapse, and cost_gate
  exit independently. They are *inputs* to one cascade.
- **Accepting a cheap resolution without its done-gate.** Thrift that ships wrong answers.
  A cheap rung must clear confidence *and* the gate.
- **Stubborn non-escalation.** Retrying a too-weak rung (2-consecutive-failures violation)
  instead of escalating with context.
- **Re-reasoning a stored answer.** Skipping the Vault/asset rungs and paying a model to
  re-derive what CO-05 already holds.

---

### CO-03 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Evaluates Vault→asset→deterministic→Haiku→Sonnet→Opus in order, stops at first that passes the done-gate | Every model-using operation routed through CO-03 | Coverage of a model call made outside the cascade (flagged by CO-10) |
| Unifies classify_tier + cost_collapse + cost_gate into one decision (no contradictory exits) | Always | — |
| A cheap resolution is accepted only above confidence AND past its done-gate | Always | That a cheap rung is always right — failure escalates with context |
| Escalates on gate-failure with context; never stubbornly retries a weak rung | Always | Escalation past the task-shape floor / budget envelope |
| Rollback can only stop savings, never raise cost | On misbehavior | — |

**Guarantee level (honest):** CO-03 is a pre-spend decision layer (rung-2/3 class) — it
governs model *selection* deterministically where it owns the call path; it cannot govern a
model call issued outside the cascade (CO-10 flags that gap). It makes the expensive model
the **last** resort by construction. *Sealed under SCS C61.*
