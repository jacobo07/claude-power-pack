# Pre-registration — what the uncovered-evidence sweep should find

**Written 2026-09-19, before `tools/gsd_x_claim_reconcile.py` exists.** Committed ahead
of the producer so the predicate cannot be tuned until it selects an answer already
known. A mismatch **in either direction** — a predicted event the sweep misses, or an
event the sweep flags that is not predicted here — is the finding, not a defect in this
file to be edited away afterwards.

Subject: `vault/datasets/gsd_x/claims.jsonl` (69 claims), last reconciled at `fd87e39`
(2026-09-18). Delta under test: `fd87e39..HEAD`, 27 commits at time of writing.

## The measurement that forced this design

Before predicting, one thing was measured. Every claim whose own text names an existing
repo path was extracted — **21 of 69** — yielding **12 distinct claimed surfaces**. The
blob SHA of each was compared at `fd87e39` and at `HEAD`:

    0 of 12 claimed surfaces moved.

So a dependency-staleness detector, even with the claimed-surface set fully populated
from the claims' own evidence, reports **CURRENT for all 21** — and is **correct** to.
Those claims really are still true.

Yet the corpus is 27 commits stale. Therefore:

> **Dependency staleness cannot detect this failure.** The knowledge did not rot; it
> failed to grow. Every unreconciled commit touched a surface that no existing claim
> names, which is precisely why no existing claim was contradicted and why the gate
> returned `6/6 exit 0`.

This inverts the predicate drafted earlier. A sweep scoped to *commits touching a
claimed surface* would return **empty** here — a clean bill over a stale corpus, which
is the original defect reproduced inside its own detector. Coverage must be scoped to
the **complement**: material evidence on surfaces the corpus does **not** yet speak
about. Claimed surfaces remain the input to `STALE_DEPENDENCY`, a different verdict.

## Prediction

**MUST be flagged uncovered** — material evidence, no current claim covers it:

| commit | why it is material |
|---|---|
| `547e4ae` | session-scoped autocompact thresholds landed; a shipped capability with no claim |
| `64ec155` | the fix distinguishing a resume from a re-sent `/compact`; `GSDX-C03` decided the rule, nothing records it shipped |
| `f2462ee` | resume-confirmation aperture fix — the reason a confirmation became observable at all |
| `c5f82c0` | the two-pane drill tool exists; `GSDX-C09` is UNPROVEN about two panes |
| `62da863` | prompt-chain startup measured at 42 ms; bears directly on `GSDX-C06`'s timeout diagnosis |
| `d0477b8` | marker reap by session clock, and the roadmap's premise measured false (0 of 9 reapable) |
| **`9c30713`** | **the first confirmed resume this estate has recorded.** `GSDX-C08` is UNPROVEN only for `via=orca-exact`; the terminal-inbox leg of `GSDX-C04` succeeded and no claim says so. This is the single event whose absence proves the thesis — if the sweep misses this one, the sweep is wrong. |
| `3e56322` | refusal half of two-pane exactness proven live; bears on `GSDX-C09` |
| `3c49f86` | context-watchdog overlay guards fix; bears on the `GSDX-I11` watchdog baseline |
| `1b2d6f4` + `b788b25` | HR-CONT / PR-CONT / T-CONT promoted into the UKDL; a governance surface no claim tracks |

**MUST NOT be flagged** — immaterial, or a record of work rather than evidence of it:

| commit | why not |
|---|---|
| `9c2882e` | **touches zero files.** A deliberate empty commit. Any sweep that flags it is counting commits, not evidence — and any sweep that crashes on it has an unhandled shape. |
| `72fc059` | auto-generated planning context |
| `396477d`, `8138d50`, `1fdd3cc`, `265c12c` | resumption-file narration; restates state rather than establishing it |
| `50837ed` | already the reconciliation boundary's neighbour and pointer-only |

**Expected count: 10 flagged, 7 explicitly not.** Remaining commits are unclassified
here on purpose — if the sweep flags one of those, that is new information and must be
read, not suppressed.

## What would falsify the whole approach

- The sweep flags `9c2882e` → it is counting commits.
- The sweep misses `9c30713` → it cannot see the one event this wave exists for.
- The sweep flags every commit → no materiality filter; a detector that accuses
  everything has the same information content as one that accuses nothing.
- The sweep returns an empty set → the claimed-surface inversion above was not applied,
  and the vacuous-pass defect has been rebuilt.

## Floor and positive control

Per `tools/gsd_x_ups_sweep.py:63-67`, a sweep that silently stops matching must not
read as a clean bill. This sweep therefore carries a minimum population and a named
positive control — `9c30713` must be reachable by the predicate — and returns
**exit 2 (INSTRUMENT_FAILED)**, never 0, when the population falls below the floor.
Three outcomes, never two.
