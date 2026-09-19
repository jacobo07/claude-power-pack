# Knowledge Goes Wrong by Omission, and Contradiction Detection Cannot See It

**Measured 2026-09-19**, GSD X wave N3, `claude-power-pack`.

A claims ledger of 69 rows sat 27 commits behind the repository it described. Its gate
returned `6/6, threshold 6/6, exit 0`.

Every clause was honest. Fields present. Vocabulary closed. Each state carrying its
falsifiable companion. Cross-references resolving. No inline code. And an honesty clause
requiring the corpus to admit at least one thing it got wrong and one it had not earned —
satisfied, by 4 contradicted and 9 unproven rows.

The corpus was still wrong, and nothing in it was false.

## Why every gate was blind

The six gates all ask variants of one question: *is what is written here internally
sound?* None asks: *is anything missing?*

That gap is not a coverage oversight. It is structural, and the measurement that proves
it is the most useful thing this wave produced:

> Every claim whose own text named an existing repo path was extracted — **21 of 69**,
> giving **12 distinct surfaces**. Each surface's blob hash was compared at the last
> reconciliation commit and at HEAD.
>
> **Zero of twelve had moved.**

So a dependency-staleness detector — the obvious mechanism, and the one the plan
originally specified — reports CURRENT for all 21 claims, and is **correct** to. Those
claims really were still true. Nothing rotted.

The corpus was stale because knowledge had failed to **grow**. Twenty-seven commits had
landed, and every one of them touched a surface no existing claim named. New capability,
new measurements, a first-ever confirmed resume — none of it contradicted anything,
because none of it was *about* anything already asserted.

**A gate that detects contradiction is measuring the claims it has. The failure was in
the claims it did not have.**

## The inversion this forces

The first design scoped the coverage sweep to *commits touching a claimed surface*. On
this corpus that sweep returns **empty** — a clean bill over a stale ledger, which is the
original defect rebuilt inside its own detector.

Coverage must be scoped to the **complement**: material evidence on surfaces the corpus
does not yet speak about. Claimed surfaces remain the input to dependency staleness,
which is a different verdict answering a different question.

    STALE_DEPENDENCY    what I claimed has moved        -> the claimed surfaces
    UNCOVERED_EVIDENCE  what happened, I never claimed  -> everything else

Both are needed. Neither substitutes for the other, and the second is the one nobody
builds, because the first is the one that sounds like freshness.

## Materiality is not claim-worthiness

The uncovered set was **pre-registered before the producer existed**, so the predicate
could not be tuned until it selected an answer already known. The prediction named 10
events; the predicate found **21**, including all 10 — full recall, and roughly a
two-fold over-count.

The mismatch was not a defect in either. The prediction was answering *which events
deserve a claim*; the predicate answers *which events are material*. A commit is a unit
of work and a claim is a unit of knowledge, and the two do not correspond — thirteen
claims ultimately covered twenty-one events, because Phase 1's five commits are one piece
of knowledge.

Keep the layers apart. Deterministic detection produces candidates; deciding which
deserves a claim is semantic and belongs to a human or a model. A tool that decides both
has started inventing knowledge.

## Traps this wave paid for

- **A reconciler is one step behind itself.** Reconciling produces commits that are
  themselves uncovered, so the count can never reach zero. Excluding the tool's own
  commits would be a blind spot; the resolution is that a commit touching *only the
  ledger* is bookkeeping rather than evidence, while the tool's own source commits get a
  claim like anything else.
- **A ratchet frozen on day one has no shrink pressure** unless something can add the
  missing field. Freezing 69 of 69 rows and then forbidding the producer from writing
  the ledger makes the inventory a permanent exemption list. Backfill first, then freeze
  what remains.
- **A gate needing the real repo cannot judge a synthetic corpus.** The drill redirects
  the subject to a temp file with no history; running repo-backed gates there sweeps real
  history while judging fabricated claims, and the verdict becomes a function of
  whichever pane commits next. They must skip — and the drill must assert *how many*
  skipped, or the skip silently becomes permanent. Without that skip the ratchet fires on
  the synthetic rows, the intact corpus is rejected, every mutation then also returns 1
  and scores as caught: a 10/10 drill measuring nothing.
- **A drill scoring exit 1 as "caught" rewards a gate that crashes.** Once a gate shells
  out to a subprocess, an uncaught exception is likely, and exit 1 reads as a successful
  detection. Three outcomes, never two.

## Rule candidates — PROMOTION_PENDING_CONCURRENT_WRITER

The canonical UKDL (`vault/knowledge_base/ukdl-universal.md`) carries **1,057
uncommitted rows** from a producer outside this session, last written 24 seconds before
this file. It is not touched. These are recorded here with their intended level and are
**not promoted**:

| intended | rule |
|---|---|
| HARD RULE | New material evidence with no claim covering it is a knowledge-freshness failure. Freshness that means "no contradictions found" is not freshness. |
| HARD RULE | A current claim requires current evidence *dependencies*, not a recent timestamp. Time is not semantic staleness. |
| PROCESS RULE | Audit the semantic contract — inputs, outputs, state semantics, failure semantics, persistence, consumers, Production Reality boundary — before reusing a similarly named capability. Name overlap does not prove contract equivalence. |
| TRAP | Pre-registering a prediction tests the layer you wrote it at. A prediction about claim-worthiness cannot grade a predicate about materiality. |
| TRAP | Scoping a coverage sweep to the surfaces already claimed rebuilds the staleness defect inside the detector meant to catch it. |

## Evidence

`a38e12c` · `88bc38f` (pre-registration) · `da7aea1` (reconciler) · `d0299b5` (21 claims
pinned) · `3c82c68` (four gates) · `ada05e2` (ledger reconciled, 69 to 84).

Gate 10/10 exit 0, drill 10/10 both poles, GSDX suite 14/14, reconciler 0 findings.
Production Reality boundary: **ACTUAL REPO EVIDENCE RECONCILED** — the producer ran
against the real 27-commit delta, not a fixture, and no commit hash or message is
hardcoded in the predicate.
