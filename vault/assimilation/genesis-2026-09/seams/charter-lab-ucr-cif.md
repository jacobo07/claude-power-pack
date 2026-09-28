# Seam: genesis-charter-lab -> UCR-CIF promotion (T9 item 33) — PLANNED, not built on purpose

**Decision (2026-09-28): no CPP-side Charter Lab engine.** Building one would create a second
promotion authority beside the two that exist, which is the duplication HR-NOVELTY-001 exists to
stop. What Charter Lab contributes is recorded here as requirements for its canonical owner.

## Who owns promotion today (measured)

| surface | where | state |
|---|---|---|
| UCR-CIF disposition ledger, requirement corpus, reach calibration | branch `ucr-cif/construction` (`C:\Users\User\Apps\pp-ucr-cif`, `de07a5c`) | 77 commits NOT merged into `feature/knowledge-acquisition`; idle since 2026-09-23; untouched by this mission (Owner decision 1a) |
| Constitutive Baseline Ratchet (`modules/tower/ratchet.py`, generations + anti-downgrade) | live branch; CLI `tools/family_baseline.py` | `promote` requires reason + authority only — no evidence of frozen gates or held-out proof |
| UKDL candidate queue (`modules/fable_distillation/ukdl_queue.py`) | live branch; CLI | promotion requires the rule to exist in the archive; no evidence requirement |
| Preregistered paired evidence (`tools/paired_experiment.py`, item 31) | live branch | LIVE: frozen registration, holdout case required, blinded grades bound to output bytes |

## What Charter Lab adds (vendored `genesis-charter-lab`, MIT), as requirements for the owner

1. A candidate is **staged and hashed** against the active baseline before any evidence exists.
2. Promotion needs **≥ 3 train receipts and ≥ 1 distinct holdout**, **zero regressions**, and a
   preregistered **minimum relative gain** on a declared metric (`quality` or `tokens`).
3. Evidence is accepted only through an **independent verifier** bound to an evidence digest.
4. **Rollback** to a prior promoted version or the baseline, always with a reason, history retained.

Rule 2 is the one CPP lacks. The paired-experiment wrap (item 31) already produces the evidence
shape it needs, so the join is: *tower `promote` (or the UCR-CIF disposition that precedes it)
requires a committed `vault/experiments/<id>/analysis.json` whose registration names the candidate
and whose targets are met with `regressions == []`.*

## First real case it would have decided

exp-successor-packet-002 is exactly a worker-charter change (the successor card with a packet
reference). Under rule 2 it would be **refused**: 2 cases (1 train, 1 holdout), quality equal, token
target not met. The decision record reached the same conclusion by hand (`REPORT.md`): the packet
reference ships as an opt-in aid, not as a new default charter.

## Why the vendored module is not wrapped as-is

Its `verifyEvidence` is a JavaScript callback; the one-shot JSON bridge
(`modules/external_assimilation/node_bridge.py`) cannot carry a function, so wrapping it would mean
a CPP-side verifier and state store: the second authority this note declines to build.

**Reopen when:** `ucr-cif/construction` merges into the live branch, or the Owner names `tower`
as the promotion owner for charters. Then implement rule 2 as a precondition in that owner, with a
red drill whose subject is exp-successor-packet-002.
