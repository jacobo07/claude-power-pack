# W7 — Consumption Reach Calibration & Activation Quality

**Decision: KEEP THE CURRENT POLICY. All five widening candidates REJECTED.**
Measured 2026-09-21 on branch `ucr-cif/construction`, base `d610518`.

W5 proved the corpus can be consumed. W6 proved a second real decision boundary
consumes the same authority. W7 asked how often that boundary opens when opening it
would help, and the answer is that it opens rarely, is **perfectly precise when it
does**, and cannot be widened without destroying that precision.

---

## 1. The shape of the question changed once it was measured

The handoff framed the gap as *"`sdd_tier` returns None unless `action ==
create_spec`"*. True, and one level too shallow. The measurement gives the mechanism:

> **Activation is decided by a property of the WORKING DIRECTORY (does it already
> hold a spec). The VALUE of activation is a property of the PROPOSAL (does the
> corpus hold adjudicated authority about it). These two are independent.**

`PR-W7-L4` drives that live: one proposal, two repositories, opposite outcomes.

A second scoping fact sharpens it. All **40** authoritative owners are Power-Pack
internal paths (`modules/*`, `agents/*`, `hooks/*`, `tools/*`). The corpus's capital
is about the Power Pack — and **every Power Pack checkout on this host has the door
shut**, because all three hold `vault/specs/*.md` and `vault/plans/*.md`.

---

## 2. Repo-side ceiling — measured before any prompt was read

The activation condition is a per-repository constant, so it bounds the whole study
and was measured first, with no prompt population at all.

| unit | door OPEN | door SHUT | denominator |
|---|---|---|---|
| distinct repository | 63 | 14 | 77 |
| working directory | 73 | 108 | 181 |
| working dir, active ≤ 30 d | 52 | 57 | 109 |
| working dir, active ≤ 90 d | 55 | 104 | 159 |

Population floor 20 **MET**. Zero sweep errors, zero absent roots. One split-verdict
group (`KobiiCraft Core Files`: two worktrees sit at refs without `vault/plans/`), so
the repository-level collapse is the conservative direction.

Shut by glob: `vault/plans/*.md` ×101 · `vault/specs/*.md` ×30 · `PRD.md` ×2.

**The two units disagree by design and the disagreement is the finding.** The door is
shut in 18 % of *repositories* but ~65 % of *recently-worked directories*, because the
14 shut repositories are the high-traffic estates, fanned across dozens of worktrees.
**Reach is anti-correlated with traffic.**

---

## 3. Prompt-side funnel — the real `UserPromptSubmit` history

400 sessions sampled reproducibly from this host's own transcript store, replayed
through the **live** `classify_tier` / `check_spec_gate` / `sdd_tier.evaluate`. No
synthetic prompts. No prompt text persisted.

```
prompt events read        3520
unique prompts            2473      (dedup across resumes)
slash commands excluded    123
engineering population    2350
reached Tier >= 2         1143/2350 = 48.6 %
judgeable at the door     1141/1143 = 99.8 %
owners COMPUTED           1057/1141 = 92.6 %
owners RENDERED            228/1141 = 20.0 %
owners computed, SILENT    829/1141 = 72.7 %
```

Miss layers, each named because each implies a different repair:

| layer | n | what it means |
|---|---|---|
| `tier_below_2` | 1207 | ordinary small work — **correct silence** |
| `owners_routed_signal_silent` | 829 | adjudicated owners computed and shown to nobody |
| `none` | 228 | an owner reached the agent |
| `spec_present_door_shut` | 60 | door shut and the corpus had nothing anyway |
| `door_open_no_owner` | 24 | door open, corpus silent — **correct silence** |
| `cwd_unreadable` | 2 | unjudgeable; never counted as a negative |

Gate actions on the Tier ≥ 2 stream: `read_spec` 833 · `create_spec` 267 ·
`knowledge_first_required` **143**. That third action is a suppression path the
handoff never named: DFP pre-empts the spec question on 11.5 % of Tier ≥ 2 prompts and
those owners are discarded too.

---

## 4. Activation quality against an INDEPENDENT oracle

Recall is not computed against "did the trigger fire" — that would make the system
correct by construction. The oracle is the engineer's own later commits: for a prompt
in repository R at time T, which paths did R's commits touch within 24 h. Its source
references no part of the chain it grades (`V-W7-ORACLE-IS-INDEPENDENT-OF-THE-TRIGGER`).

```
UNLABELLED_BY_DOMAIN   1024     cwd is not a Power Pack checkout
NOT_RELEVANT             88
RELEVANT                 27
UNLABELLED_NO_COMMITS     2     absence of a commit is NOT a negative
labelled population     115/1141 = 10.1 %

TP 8    FP 0    FN 19    TN 88
activation precision    8/8  = 100.0 %   (8/8 routed the CORRECT owner)
activation recall       8/27 =  29.6 %
miss rate              19/27 =  70.4 %
false activation rate   0/88 =   0.0 %
```

The labelled population is a tenth of the judgeable one. That is stated, not hidden:
the oracle's domain is Power Pack checkouts, because that is where the owners live.
The 1 026 unlabelled cases sit **outside** the confusion matrix, which sums exactly to
the labelled population (`PR-W7-C7`).

**POST-HOC.** These labels use evidence created after the prompt. They may never be
read as "the agent could have known this at mission start".

---

## 5. Shadow candidates — five policies, none Pareto-improving

Each candidate was written as a mechanism *before* any confusion matrix was computed,
and scored on a holdout split by **session** digest (a case split would leak, since two
prompts of one session share a repository, a moment and usually an intent).

Holdout half (572 judgeable prompts), never used to choose anything:

| policy | precision | recall | FAR | signals | owner slots |
|---|---|---|---|---|---|
| **P0 control — `create_spec`** | **100.0 %** | 25.0 % | **0.0 %** | 111 | 508 |
| P1 any owner | 23.5 % | 100.0 % | 86.7 % | 526 | 2462 |
| P2 construction intent | 33.3 % | 16.7 % | 8.9 % | 80 | 376 |
| P3 Tier 3 only | 22.2 % | 50.0 % | 46.7 % | 272 | 1355 |
| P4 strong evidence (≥10 units) | 24.0 % | 100.0 % | 84.4 % | 491 | 2393 |
| P5 construction ∧ strong | 33.3 % | 16.7 % | 8.9 % | 75 | 366 |

Calibration and holdout agree, so this is not an overfit.

- **P1 / P4** buy full recall at an **85–90 % false-activation rate** and 4.8× the owner
  slots. That is the system this programme explicitly must not become: one that shouts
  institutional advice everywhere.
- **P3** halves precision for a 47 % false-activation rate.
- **P2 / P5** are **strictly dominated** — lower precision *and lower recall* than doing
  nothing. Narrowing by intent loses on both axes (`PR-W7-S3`).

**No candidate raises recall without losing precision** (`PR-W7-S2`). Under the brief's
own rule — Pareto improvement or keep — the decision is KEEP.

---

## 6. Why widening fails, and where the real bottleneck moved

The reason is not the door. It is **applicability precision**, and it is independent of
the trigger:

| prompt length | n | routes ≥1 owner | mean owners (cap 5) |
|---|---|---|---|
| xs | 12 | 0.0 % | — |
| s | 24 | 4.2 % | 1.00 |
| m | 72 | 45.8 % | 2.73 |
| l | 74 | 89.2 % | 4.18 |
| **xl (>5 000 chars)** | **1061** | **99.4 %** | **4.74** |

85 % of real Tier ≥ 2 prompts are `xl`. The DISTINCTIVE-shared-term clause was proven on
**short synthetic proposals** (W5/W6 fixtures) and does not discriminate at the length
the estate actually writes. The most-routed owners are the three largest by unit count —
`governance-overlay` 1128, `knowledge_acquisition` 1123, `deep-research` 1087 — which is
the vocabulary-volume bias W3 measured (`spearman = +0.756`) surviving at real length.

> **The control's 100 % precision is produced by the `create_spec` filter, not by the
> selector.** The door is doing the selector's job.

Pinned as a characterization, `PR-W7-X1-SELECTOR-SATURATION-ON-LONG-PROMPTS`, which is
**expected to go red** when applicability is repaired and must then be inverted in
place, never deleted.

Per the brief, the selector was **not** touched: this is a separate causal claim and
belongs in its own wave with its own evidence.

---

## 7. Cost

Measured live, fresh subprocess, real repositories:

- one owner-naming signal = **534 B advisory + 518 B actionable = 1 052 B**
- widening to P1 on the holdout stream: +415 signals ≈ **+437 kB**, i.e. **≈ +764 B on
  every Tier ≥ 2 prompt**, at 23.5 % precision
- **zero additional selector calls and zero additional latency.** The gate already
  computes `routing` on every branch, so the entire cost of widening is context and
  attention — which is exactly the resource the brief calls scarce
- in-process, re-measured today: warm applicable L **12.73 ms**, warm no-match L
  **12.06 ms**, non-applicable S/M **0.00 ms**, marginal **+10.4 ms** paired

**Absolute hook wall-clock stays UNMEASURED.** The host ran between 351 MB and 1 230 MB
free of 32 061 MB (1.1–3.8 %) throughout, with 41 `claude` and 23 `node` processes. A
reading under that contention is not a measurement.

---

## 8. Historical manual sweeps — they belong to the FIRST door

W5 recorded that the discovered-ownership sweep had been run manually, at real audit
cost, before six consecutive mega-corpus proposals (AISHF · RE Baseline's 3 families ·
KSF's 22 · the UKR Compendium's 8-step escalation · the IIG pass's 30 candidates).

All six are *mega-system* proposals, which is the **novelty gate's** population — the
first door, closed by W5. They happened inside the Power Pack repo, where the second
door is shut, so widening the second door would not have retired one of them. The
avoidable-intervention class W7 could remove is a different one, and on this evidence it
is small: 27 labelled-relevant prompts in 400 sessions, of which 8 already receive the
owner.

**No human-rediscovery saving is claimed beyond that.** Counterfactual, not observed.

---

## 9. What would reopen this decision

- applicability precision is repaired, so that owners routed on long prompts mean
  something — then re-run `tools/ucr_cif_shadow.py`; `P1` becomes viable exactly when its
  precision on the holdout stops collapsing
- the estate's repositories stop carrying `vault/plans/*.md` (the glob shutting 101 of
  108 doors), or that clause is narrowed — the ceiling moves without any policy change
- the oracle's domain widens beyond Power Pack checkouts, raising the labelled
  population above 10 %
- a second corpus whose owners are not Power-Pack-internal

## 10. Evidence

| artifact | what it holds |
|---|---|
| `vault/audits/ucr_cif/w7_reach_control.json` | full control measurement, 2 350 derived cases, no prompt text |
| `vault/audits/ucr_cif/w7_shadow.json` | six policies × calibration / holdout / whole |
| `tools/test_ucr_cif_reach.py` | V-W7-* instrument gates, both poles |
| `tools/test_ucr_cif_reach_reality.py` | PR-W7-* production reality + the characterization pin |
| `vault/governance/mutation_plans/ucr_cif_w7.json` | 10 directed mutations |
