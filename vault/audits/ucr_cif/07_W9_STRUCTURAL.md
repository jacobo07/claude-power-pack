# W9 — Structural ownership evidence: built, measured, NOT promoted

**Verdict: the family is real, orthogonal and does not improve owner
selection at this oracle's resolution. It ships computed, reported and
switched OFF.**

W8 ended with lexical precision at a measured supply ceiling and named a
structural family as the only remaining lever. W9 built it. The mechanism
works — it reorders 78.5 % of routed selections — and against the only
independent oracle this estate has, it could not be shown to help, with two
measured ways of hurting. That is the result, and it is recorded as a result
rather than softened into one.

## 1. The family that was rejected before it was built

The obvious candidate: *does the candidate owner structurally hold this
unit's evidence terms?*, reusing `ownership_evidence.evidence_for`.

**996 / 996 = 100.0 %** of authoritative units satisfy it.

Not a signal — a **projection of W3's adjudication**, which promotes a
candidate to VERIFY exactly when `attributing and distinctive_terms` holds.
Constant over the admitted population, therefore zero discrimination.
Non-authoritative rows sit at 14.9 %, which confirms the mechanism rather
than rescuing it. Pinned by `V-W9-UNIT-LEVEL-IS-A-PROJECTION` so it cannot
be re-proposed as coverage.

## 2. The granularity that is not a projection

A prompt matches a *subset* of a unit's terms and the adjudication never saw
the prompt. Per (unit, term) pair over the authoritative corpus:

| | |
|---|---|
| owner structurally holds the term | **1,634 / 7,785 = 21.0 %** |
| corpus-distinctive pairs only (what the selector ranks on) | **561 / 3,119 = 18.0 %** |
| pairs no ledger owner holds (pure prose) | 2,776 = 35.7 % |
| evidence terms held by some ledger owner | 674 of 1,498 = 45 % |

The channels disagree on 82 % of the pairs the selector ranks by. The
structurally-unheld terms are prose: `failure` (143), `capability` (102),
`institutional` (96), `evidence` (85), `architecture` (49).

## 3. Cost

`build_structural_index` measured **45,525 ms cold / 10,080 ms warm** over
1,364 files. Compiled offline into 674 terms / 65,834 bytes / **0.73 ms** to
parse.

Two defects found by measuring my own read path rather than assuming it:

* `load()` re-parsed the 1.9 MB ledger through `_ledger_binding` — **70.8 ms**
  per process, against a projection that parses in 0.73 ms. Passing the
  already-parsed corpus id: **70.8 → 2.71 ms**.
* the binding compared `mtime_ns`, which no clone or checkout preserves. It
  would have reported every fresh working tree as stale and silently disabled
  structural evidence where nobody would look.

## 4. The paired measurement

Both arms derived in one session, five minutes apart, 400 sessions each,
control with `UCR_CIF_STRUCTURAL_DISABLE=1`. Keyed on `prompt_sha`:
**2,098 of 2,098 cases shared, zero drift** — a cleaner pairing than W8's,
which shared 1,792 of 2,306.

| | control | treatment |
|---|---|---|
| routed ≥ 1 owner | 922 | 922 |
| owner slots | 3,677 | 3,677 |
| activation precision | 9/9 = 100 % | 9/9 = 100 % |
| false-activation rate | 0/96 = 0 % | 0/97 = 0 % |
| selector consulted | 1,056 | 1,056 |

Identical, **by construction**: a ranking-only change cannot move a
fire/no-fire metric. This was stated in the spec before the run, so that an
unchanged headline could not later be read as a failure of the mechanism.

**The mechanism is anything but inert:**

* order changed on **724 / 922 = 78.5 %** of routed selections
* top-1 changed on **544 / 922 = 59.0 %**
* `governance-overlay` net **−473** top-1 slots (gained 7, lost 480)
* `knowledge_acquisition` +324, `deep-research` +93, `sqi` +30

## 5. Against the independent oracle, it does not help

The oracle is behavioural, not lexical: it credits an owner when commits
landing in a window *after* the prompt touch its files, with shared/global
paths excluded. It is independent of both evidence channels.

Of the 30 labelled cases whose true owner was routed:

| | |
|---|---|
| rank improved | 6 |
| rank worsened | 12 |
| unchanged | 12 |
| **net** | **−6 of 30**, two-sided binomial **p = 0.238** |

**UNRESOLVED.** The point estimate is directional and the sample cannot carry
it. Reporting −6/30 as harm would overclaim exactly as reporting +6 would.

Two measured reasons not to promote on that evidence:

**(a) Owners whose artifact is PROSE are systematically under-credited.**
`governance-overlay` holds 13.7 % of its term-pairs structurally, because a
policy module's capability lives in Markdown, not in symbols, filenames or
registry keys. W3 read its routing volume as vocabulary bias — but the
behavioural oracle credits it on 21.1 % of labelled hits against a 23.7 %
routing share, i.e. roughly in proportion. It is a real owner. Five of the
twelve worsened cases have `governance-overlay` as ground truth, demoted from
rank 0. The structural family does not distinguish "not the owner" from
"owns this in prose".

**(b) The cap turns a reorder into a loss.** I claimed ranking could not lose
a true positive by construction. That is true only *before* `[:MAX_OWNERS]`.
Two labelled cases had the true owner at index 4 — the last visible slot —
and the reorder pushed it out of the selection entirely (rank 4 → absent).
My gate had passed because the fixture carried three owners against a cap of
five: a fixture structurally unable to observe the property. Now pinned by
`V-W9-CAP-CAN-EVICT-AN-OWNER` on a fixture that exceeds the cap.

The oracle is **not** merely a mirror of routing volume, which was the first
thing checked before accepting it: `duplicate_to_advantage` is routed 3.4 %
and credited 21.1 %.

## 6. What ships

* the compiled projection, its freshness contract and its four degradation
  states;
* `structural_strength` and `attributed` computed and reported on every
  owner, and rendered by `--explain` as *BUILDS …*;
* `structural_status` on every selection, so no-contribution and
  could-not-look are never the same observable;
* **`STRUCTURAL_RANKING_ENABLED = False`** — the default order is W8's,
  byte for byte. `UCR_CIF_STRUCTURAL_RANK=1` re-enables for measurement.
* `REQUIRE_STRUCTURAL_ATTRIBUTION = False` — the admission clause exists,
  refuses lexical-only owners when enabled, and is not shipped on.

Promoting a change that reorders 59 % of top-1 slots on a statistical wash
would be substituting a prior for a measurement. The prior in question —
"`governance-overlay` is a false owner" — is the one the oracle contradicts.

## 7. Reopening conditions

1. **The labelled oracle reaches ~3-point resolution.** At 30 labelled cases
   with a routed true owner, one case is 3.3 points. This is frontier action
   3 and it now blocks W9 as well as any future precision wave.
2. **Prose-form ownership gets a signal.** A family that reads Markdown
   headings, governance rule ids or doc front-matter as structural
   declarations would credit policy modules. Untested.
3. **The cap interaction is separated from the ranking question.** Ranking
   below the cap and eviction at the cap are two effects; the measurement
   cannot currently tell how much of the −6 is each.

## 8. Proof

* `tools/test_w9_structural_evidence.py` **29/29**, both poles, positive
  controls on every negative assertion.
* `vault/governance/mutation_plans/ucr_cif_w9.json` **7/7 ALL_CAUGHT**.
* Whole family re-verified: W4 14/14, W5 23/23, W7 10/10, W8 6/6, W9 7/7 =
  **60 directed mutations**, restore verified at source and runtime.
* Suites: selection 22/22, consumption 19/19 + PR 7/7, spec boundary 22/22,
  reach 27/27, W8 applicability 17/17, adversarial 18/18.
* `PR-W7-X1` untouched and green. `DISTINCTIVE_MAX_HOLDERS`,
  `MAX_DISTINCTIVE_REQUIRED`, `create_spec` and the corpus all untouched.

### Instrument failures, mine

1. **W46 SURVIVED.** The stale-ledger case rewrote the ledger with a longer
   generation string, so the SIZE check caught it and the `corpus_id` channel
   was never exercised — an assertion passing for a reason unrelated to the
   clause it named. Fixed with a same-length id swap at an identical 46,364
   bytes, plus a HARNESS branch that fails loudly if the swap ever changes the
   length again.
2. **Two W8 anchors rotted by my own edit**, then **W36 survived its first
   repair** — I repointed it at `_rank_key`, which W9 then made the
   non-shipped branch. Mutating a function the default path never calls
   changes nothing. An anchor must follow the code that ships, not the code
   that shares its name.
3. **The cap fixture first routed nothing.** Giving four filler owners the
   same two terms pushed them past `DISTINCTIVE_MAX_HOLDERS`, so every match
   became generic and the selector correctly refused everything. Adding owners
   to a term destroys its distinctiveness; a fixture has to respect the clause
   rather than fight it.
