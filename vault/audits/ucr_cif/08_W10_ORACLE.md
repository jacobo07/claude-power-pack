# W10 — Owner-relevance oracle: widened 3.9×, and it resolves the question W9 could not ask

**Verdict on the oracle: SUCCESS.** 30 → 116 labelled cases, an arm-independent
truth set, the rank/cap decomposition, and modality stratification.

**Verdict on ~3-point resolution: NOT REACHABLE, and now measured rather than
hoped.** It needs ≈3,100–3,700 discordant pairs; the entire available population
yields 25–37. The population is exhausted, not under-sampled.

**Verdict on the W9 treatment: KEEP DISABLED — HARM on a pre-registered
stratum.** `STRUCTURAL_RANKING_ENABLED` stays `False`.

---

## 1. The instrument W9's headline never had

A repo-wide sweep at W10 open found W9's "6 improved / 12 worsened over 30
cases, p = 0.238" in exactly two places: prose in `07_W9_STRUCTURAL.md` §5 and
a docstring at `disposition_consumer.py:338`. **No committed code computed it.**

That is not a bookkeeping complaint. The brief's §XLVI requires both arms to be
re-derived fresh rather than read from a stored report — and there was nothing
to run. The headline was unfalsifiable in both directions.

`tools/ucr_cif_oracle.py` is that instrument. `V-W10-REPRODUCES-W9-P` re-derives
p = 0.2379 from W9's own 6/12 split, so the test that produces W10's numbers is
demonstrably the one that produced the number W10 inherited.

## 2. Two defects the missing instrument concealed

### 2.1 The truth set was a function of the arm

`reach_ground_truth.label_case(case.owners_routed, touched, …)` credits an owner
only when that owner **was routed**. Correct for W7's activation question. For a
ranking question it leaks, and the leak flatters the treatment:

> A case whose true owner the treatment DROPS produces no owner hits, so it is
> re-labelled `NOT_RELEVANT` and leaves the measured population — instead of
> counting as the loss it is.

Suppressing a true owner improved the apparent score. That is exactly what
PR-W10-19 exists to forbid, and it was live in the design W9 measured through.

W10 computes truth against the full **40-owner authoritative universe**
(`modules/ucr_cif/owner_truth.py`), never against any arm's output. An owner
missing from an arm is now a named eviction. Both worlds are driven by
`V-W10-SUPPRESSION-CANNOT-FLATTER` and its `ARM-DEPENDENT-TRUTH-LOSES-THE-CASE`
reproduction.

### 2.2 Rank and cap were not merely unmeasured — they were unmeasurable

W9 said it could not apportion its −6 between ranking and cap eviction. The
reason is one line: `owners.sort(...)` computed the ranked order and
`owners[:MAX_OWNERS]` discarded everything past the cap on the next line. The
pre-cap verdict never survived the function.

`Selection.precap_owners` carries it, reporting-only, under the same contract as
W9's `structural_strength`: computed, reported, decides nothing
(`V-W10-PRECAP-DECIDES-NOTHING`, `V-W10-PRECAP-NOT-SLICED-BY-CAP`).

## 3. The population

Both arms in **one process, interleaved per prompt** — strictly better than
W9's two passes five minutes apart, because corpus, ledger, projection, working
tree and clock are identical by construction rather than by hope. Population
drift is not a caveat this instrument carries.

| | |
|---|---|
| sessions swept | **573 of 573 available** (W9 used 400) |
| unique prompts | 1,471 |
| routed cases | 1,285 |
| pre-cap order changed | **982 = 76.4 %** (W9: 78.5 %) |
| **LABELLED** | **116** (W9: 30) |
| `UNLABELLED_BY_DOMAIN` | 1,331 = 90.5 % |
| `NO_OWNER_TOUCHED` | 17 |
| `UNLABELLED_NO_COMMITS` | 7 |

The 76.4 % reorder independently reproduces W9's 78.5 % on a larger population —
and doubles as the execution proof: identical arms are reported as a HARNESS
FAILURE, never as a treatment that does nothing (`V-W10-DEAD-ARM-IS-A-FAILURE`).

**90.5 % is unlabellable BY CONSTRUCTION and no effort fixes it.** All 40
authoritative owners are Power-Pack-internal paths, so a prompt issued in any
other repository cannot produce a commit that touches one. The resumption's
suggestion to "widen by repository domain" is not cheap; it is unavailable.

## 4. The result

| | pre-cap | post-cap |
|---|---|---|
| observed (owner, case) pairs | 57 | 42 |
| improved / worsened | 16 / 21 | 9 / 10 |
| **evicted / admitted** | **0 / 0** | **4 / 2** |
| discordant | 37 | 25 |
| two-sided p | 0.5114 | 0.6900 |
| effective n (one prompt = one observation) | 45 cases, 12/15, p = 0.7011 | 33 cases, 7/11, p = 0.4807 |

**Pre-cap evicted = admitted = 0 is a structural validation, not a null.** The
ranking reorders the candidate list and never changes its membership — exactly
as W9's spec claimed before its run. Therefore **every set-level effect is
attributable to the cap**, which is the decomposition W9 owed.

### The aggregate is a wash. The strata are not.

| | improved | worsened | p |
|---|---|---|---|
| pre-cap prose | 6 | 13 | 0.1671 |
| pre-cap code | 10 | 8 | 0.8145 |
| **post-cap prose** | **3** | **12** | **0.0352** |
| post-cap code | 8 | 2 | 0.1094 |

Under Holm–Bonferroni over these four comparisons **none survives** (threshold
0.0125 for the smallest). Reported as the nominal figures they are.

## 5. The two mechanisms, named

**`modules/governance-overlay` (prose, 13.7 % structural) — 8 movements across
8 distinct prompts, 4 sessions, 3 days: 0 improved, 8 worsened, p = 0.0078.**
Demoted **from rank 0** in six of the eight. It is never once improved.

This is **not** a fishing expedition. W9 pre-registered this exact owner as its
first reason not to promote (`07_W9_STRUCTURAL.md` §5(a)), before W10 existed.
W10 tested that pre-registered hypothesis on an independent population 3.9×
larger and it held, in the same direction, more strongly.

Honest limit: 8 prompts but only **4 sessions**. Clustered at the session level
the split is 0/4, p = 0.125. The pair-level p = 0.0078 is an upper bound on the
evidence, not a measurement of it.

**`modules/duplicate_to_advantage` (prose, 17.6 %) — the cap converting a wash
into a loss.** Four true owners sat at rank 3–4, drifted to rank 5–6 under
treatment (pre-cap 2 up / 4 down, **p = 0.6875 — statistically nothing**), and
were **evicted entirely** post-cap: rank 4 → absent, four times.

> A ranking change too small to detect produced four true owners removed from
> the agent's view, because they lived at the cap boundary.

That sentence is what W9 could not say, and it is the whole value of separating
the two effects. **453 of 1,471 cases (30.8 %) rank more than 5 owners**, so the
boundary is not a corner case — it is where a third of routed traffic lives.

## 6. Why ~3 points is not reachable

Derived, not asserted (`power_block`, `required_discordant`):

| | pre-cap | post-cap |
|---|---|---|
| discordant rate | 0.649 | 0.595 |
| detectable π @ 80 % / α .05 | 0.723 | 0.767 |
| **achieved resolution** | **28.9 points** | **31.8 points** |
| discordant pairs to resolve the *observed* effect | 427 | 543 |
| discordant pairs to resolve **3 points** | **3,668** | **3,084** |
| discordant pairs available | 37 | 25 |

Roughly **100×** the entire available evidence. And the population is exhausted:
every session was swept, and 90.5 % of prompts are unlabellable for a structural
reason no labelling effort removes.

Per brief §X, the achievable resolution is reported honestly and the standard is
not quietly lowered. Per §LVII, the reason is named: **too-small finite
population and a domain restriction intrinsic to the owner set** — not
insufficient labelling effort, so more labelling is not the answer.

## 6a. The treatment removes no false owners — it substitutes (PR-W10-20)

The rank metrics follow the *true* owner and say nothing about what fills the
other slots, so a treatment could look neutral on rank while swapping correct
owners for incorrect ones. Measured on the rendered surface, over the 116
labelled cases:

| | slots | true | false | slot precision |
|---|---|---|---|---|
| control | 454 | **40** | 414 | 8.81 % |
| treatment | 454 | **38** | 416 | 8.37 % |
| delta | 0 | **−2** | **+2** | **−0.44 points** |

Slot count is identical because the cap fills the same slots in both arms,
which makes this a clean **substitution** measurement: every true owner lost is
a false owner gained.

So the claim that structural ranking improves precision by removing false
owners is not merely unsupported — it is **directly falsified**. The treatment
removes no false owners at all, and the small movement it does produce runs
against it. Derived by `slot_precision`, pinned by
`V-W10-SLOT-SUBSTITUTION-IS-VISIBLE` with an unchanged-selection control, and
driven red by mutation `W65`.

## 7. Decision against the pre-declared contract

Pre-registered in the approved plan: promotion requires MPIE ≥ 5 points **AND**
cap safety **AND** prose-modality safety — all three.

- practical effect: **not demonstrated**; aggregate is a wash at 29–32 point resolution
- cap safety: **FAILED** — 4 true-owner evictions, 0 recoveries
- prose-modality safety: **FAILED** — pre-registered owner demoted 8/8, never improved
- false-owner reduction: **FALSIFIED** — −2 true / +2 false at constant slot count,
  slot precision −0.44 points

**KEEP DISABLED — HARM.** Stronger than W9's UNRESOLVED: the aggregate remains
unresolved *and is now known to be unresolvable at rational cost*, while the
pre-registered stratum resolves against promotion.

The family is **not deleted** (§LV). It stays computed, reported and rendered by
`--explain`; only its authority over the order stays off.

### Reopening conditions

1. **Prose-form ownership gets a structural signal.** The measured mechanism is
   that a Markdown-shipped capability is credited 13.7 % where the corpus
   averages 21.0 %. This is now the frontier's first action, promoted by
   evidence rather than by intuition.
2. **The cap becomes rank-aware**, or `MAX_OWNERS` rises. 30.8 % of cases exceed
   it and eviction is where the measured harm is.
3. A materially different evidence route for owner relevance — *not* more labels
   through this one.

## 8. Proof

* `tools/test_w10_oracle.py` **38/38**, every negative assertion paired with a
  positive control.
* `vault/governance/mutation_plans/ucr_cif_w10.json` **12/12 ALL_CAUGHT**.
* Family re-verified: W4 14, W5 23, W7 10, W8 6, W9 7, W10 12 = **72 directed
  mutations**. W5's `W13` anchor rotted on this wave's edit and was repaired by
  restoring the false world, as a one-line anchor on the shipped branch.
* Suites: selection 22/22, consumption PR 7/7, spec boundary 22/22, reach 27/27,
  W8 applicability 17/17, adversarial 18/18, W9 structural 29/29.
* Frozen and untouched: `STRUCTURAL_RANKING_ENABLED`, `MAX_OWNERS`,
  `DISTINCTIVE_MAX_HOLDERS`, `MAX_DISTINCTIVE_REQUIRED`, `create_spec`, the
  corpus, the 503 ABSTAIN, the 218 UNRESOLVED.

### Positive controls that make the numbers believable

The modality instrument reproduces **both** of W9's independently recorded
values: corpus aggregate **1,634 / 7,785 = 21.0 %** and `governance-overlay`
**13.7 %**. It measures the quantity W9 measured.

### What this wave does NOT claim

* Not a repaired proxy. The oracle is still POST-HOC git behaviour with every
  caveat `reach_ground_truth` states. W10 widened it and removed the arm
  dependence; it did not make it a fact.
* Not a population-level precision estimate. The labelled set is what the oracle
  could judge, and it is 7.9 % of the swept prompts.
* Not independent of clustering. 8 prompts / 4 sessions is stated wherever the
  8 is.
* The prose finding is **one pre-registered stratum**, not a survivor of
  correction across the four.

## 9. Production Reality ledger — 21 of 22, and the one that is open

Recorded per gate rather than as a total, because a count hides which one failed.

| gate | status |
|---|---|
| PR-W10-1 W9 state / fresh control | MET — ranking off, control re-derived in the paired run |
| PR-W10-2 real case acquisition | MET — 1,471 real prompts, 573 sessions |
| PR-W10-3 independent label | MET — truth from git behaviour, independent of selector *and* of both arms |
| PR-W10-4 negative label | MET — 17 `NO_OWNER_TOUCHED`: work happened, no authoritative owner touched |
| PR-W10-5 prose owner | MET — `governance-overlay` credited despite 13.7 % structural |
| PR-W10-6 multi/no-owner | MET — truth is a set; `NO_OWNER_TOUCHED` is its own state |
| PR-W10-7 ambiguity | MET — three distinct `UNLABELLED_*` states, never coerced to negative |
| PR-W10-8 blindness | MET — `V-W10-TRUTH-IS-ARM-INDEPENDENT`, mutation `W57` |
| PR-W10-9 duplicate defence | MET — dedup by `prompt_sha`; clustering reported at case level |
| **PR-W10-10 label correction** | **OPEN — NOT EXERCISED.** No label was corrected, so the supersession path is *designed* (schema version + case-level store) and never driven. Claiming it would be claiming a green nobody has falsified. |
| PR-W10-11 population fingerprint | PARTIAL — computed and printed; not driven against a second, deliberately-drifted population |
| PR-W10-12 fresh report | MET — report recomputes from the store; verified at seal, byte-comparable |
| PR-W10-13 fresh paired run | MET — both arms, one process, interleaved |
| PR-W10-14 treatment execution | MET — 76.4 % divergence + mutation `W63` |
| PR-W10-15 control execution | MET — `V-W10-CONTROL-ARM-IS-A-CONTROL` reads the flag *inside* the production call; mutation `W64` |
| PR-W10-16 pre-cap rank effect | MET |
| PR-W10-17 post-cap cap effect | MET — 4 evictions, 2 admissions |
| PR-W10-18 prose-modality effect | MET |
| PR-W10-19 true-positive retention | MET — arm-independent truth makes suppression a scored loss |
| PR-W10-20 false-owner removal | MET — and **falsified**: −2 true / +2 false |
| PR-W10-21 practical effect | MET — compared against the pre-declared 5-point MPIE |
| PR-W10-22 decision | MET — KEEP DISABLED, HARM |

**PR-W10-P1…P7 are not applicable**: they gate a promotion, and there is none.

PR-W10-15 and PR-W10-20 were both **initially unmet and are recorded here
because closing them changed the result** — PR-W10-20 turned "no false-owner
evidence either way" into a falsification, and PR-W10-15 closed the one
contamination the divergence proof structurally cannot see: a control that is a
second treatment produces *identical* arms, which reads as a dead harness rather
than as a contaminated comparison.
