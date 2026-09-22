# W12 — pre-registration, written and committed BEFORE either arm ran

This file exists so that the decision rule cannot be chosen after the numbers are
visible. Everything below is fixed at commit time; the run that tests it has not
been started. If a later commit in this wave changes any threshold here, that is a
p-hack and the diff will say so.

## 1. The kill condition, RECOVERED from the contract rather than paraphrased

Two committed sources say the same thing, and neither is this prompt:

`vault/specs/ucr-cif-w11-representation-neutral-ownership.md` §7 —

> So the headline is **stratum-level and deterministic**: whether the eight known
> `governance-overlay` movements recover, measured pre-cap and post-cap separately,
> with code-form and mixed-form owners held as safety strata. A local result is
> reported as local.
>
> If the family does not recover those movements, **W9's causal story is falsified**
> and that is the finding. The signal is not strengthened until they move.

`vault/knowledge_base/ucr_cif/UCR_CIF_RESUMPTION.md` §4 action 1 —

> **Pre-registered kill condition: if they do not recover, record the falsification
> of W9's causal story and stop — do not raise the signal's strength until they
> move.**

## 2. The eight, pinned by value from the committed store

Derived by the shipped instrument from the canonical case store
`vault/ucr_cif/oracle_cases.json` (control vs `w9-structural`), reproduced in
`w12_precheck_from_store.json`. Population fingerprint:

| key | value |
|---|---|
| `oracle_schema` | `ucr-cif-oracle/1` |
| `corpus_id` | `ef2b381beff512ca6919280a` |
| `ledger_rows` | 2376 |
| `owner_universe_n` / `_sha` | 40 / `ccc401bda49648c8` |
| `case_set_sha` | `1235476c90059398` |
| `cases` / `sessions_swept` | 1471 / 573 |
| `window_hours` / `max_owners` | 24 / 5 |

The pre-registered stratum, both halves, exactly as the report holds them:

    pre_cap .by_owner["modules/governance-overlay"] = {"worsened": 8}
    post_cap.by_owner["modules/governance-overlay"] = {"worsened": 8}

Eight `(owner, case)` pairs, **zero** improved, **zero** unchanged, **zero** evicted,
**zero** admitted, at both halves. That is the harm W11 hypothesised a
representation-neutral channel would repair.

## 3. Safety strata, pinned at the same moment

| stratum | W9 arm, pre-cap | W9 arm, post-cap |
|---|---|---|
| prose modality | improved 6 / worsened 13, p 0.1671 | improved 3 / worsened 12, p 0.0352 |
| code modality | improved 10 / worsened 8, p 0.8145 | improved 8 / worsened 2, p 0.1094 |
| `duplicate_to_advantage` | worsened 4, improved 2, unchanged 2 | **evicted 4**, improved 2, unchanged 2 |
| owner slots (116 labelled) | — | control true 40 / false 414; treatment true 38 / false 416 |

## 4. The decision rule

"Recover" is the contract's word and it is operationalised here, before exposure, in
the only direction the contract's own sentence allows — *they move*:

- **RECOVERED** — under `w11-prose`, `worsened` in this stratum is **strictly below 8**
  at the half being read, **and** no `evicted` verdict appears for this owner that the
  W9 arm did not already have. An improvement bought by removing the owner from view
  is not a recovery; it is the substitution W10 already measured and named.
- **FULLY RECOVERED** — `worsened` is 0.
- **NOT RECOVERED** — `worsened` is still 8 or higher, or every apparent gain is
  offset by an eviction.

Both halves are read and reported separately. Pre-cap recovery with post-cap loss is
**not** a recovery of the harm; W10 proved every set-level effect in this system is
the cap's, so the half that reaches the agent is post-cap.

Reported beside the verdict, never in place of it: the sign test over the eight.
Under the W9 arm the split is 0/8, p = 0.0078. This number is descriptive. The
decision is keyed on the contract's sentence, not on a threshold this file invented.

**On the kill:** NOT RECOVERED at post-cap terminates promotion evaluation. No
weight, relation, evidence, threshold, `MAX_OWNERS`, `DISTINCTIVE_MAX_HOLDERS` or
`MAX_DISTINCTIVE_REQUIRED` is touched afterwards. The falsification of W9's causal
story is the finding, and any further candidate is a new hypothesis with a new
treatment identity in a new wave.

**On promotion:** RECOVERED is necessary and **not sufficient**. It opens the safety
evaluation in §3 and the live gates; it does not by itself promote anything.

## 5. Run validity is decided before movement is read

In this order, and the order is the point:

1. both arms derived fresh, in this session, at this HEAD, each to its **own** store
   path — never the canonical one, whose default `--store` would otherwise overwrite
   the very control record the comparison is against;
2. `compare_fingerprints` returns `COMPARABLE` and `paired_verdict_allowed` licenses
   the pairing;
3. the execution proof shows the arms diverge — identical arms are a HARNESS FAILURE,
   never a finding that the treatment does nothing;
4. **only then** is any rank movement read.

If step 2 or 3 refuses, there is no verdict to report and the run is re-derived. That
refusal is not permitted to become more acceptable because of what step 4 would have
said.

## 6. Why the W9 arm is re-derived rather than reused

W11 records that `holders()` was left unchanged so W9's arm stays byte-reproducible.
That is an assertion about a refactor, and this wave is in no position to inherit it:
the whole reason the mutation family was re-driven at final HEAD is that a green
earned before the last commits is a claim about a tree that no longer exists. So the
W9 arm is run again, at this HEAD, and reproducing `{"worsened": 8}` is the evidence
that W11's changes did not move the reference the comparison depends on. If it does
not reproduce, that is a finding about W11 and the W12 headline waits.
