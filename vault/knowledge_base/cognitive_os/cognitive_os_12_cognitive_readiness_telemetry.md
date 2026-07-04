# Cognitive OS — CO-12 — Cognitive Readiness Telemetry

> The **adoption axis** of the kernel's economy. CO-01 measures cost/worth (WU/MTok); the
> C68/C69/C70 audit family measures what *happened* (volume / behavior / infrastructure). None
> measures whether the machinery built to save reasoning is **actually consulted and acted on**.
> A built-but-unused system produces zero savings while looking "shipped" — PM-03 sat inert for a
> full day (SCS C70→C73) doing exactly that. CO-12 is the missing measurement: the **Cognitive
> Readiness Score**, an adoption-rate composite that turns "we built the levers" into "the levers
> are being pulled", so any 2x/3x/4x claim is evidenced, never asserted.
>
> **EXTEND, not NEW-from-scratch:** CO-12 is the **fourth audit axis**, sibling to C68 (volume) /
> C69 (behavior) / C70 (non-token leaks). It reuses the SAME `.jsonl` corpus + `~/.claude/state`
> files those tools already read; it never stands up a parallel reader. Parents: the audit family
> (data), **CO-01** WU/MTok (the efficiency ground-truth the score must explain), **GK-09**
> Navigation Observatory (the coverage/benchmark *presentation* pattern), and CO-10 (honest
> guarantee levels). It instruments CO-03 / PM-01 / PM-03 / CO-09 / GK-06 without modifying them.
>
> **ID honesty:** CO-09 (Loop & Subagent Economics) and CO-10 (Enforcement Guarantee Ledger) are
> TAKEN (SCS C61/C62). This dataset is **CO-12** — the next free CO id after CO-11 (Output Budget
> Governor, deferred). It seals under **SCS C74**.

---

## Part I — The Adoption Axis & the Readiness Score

### I.1 Why three audit axes are not enough

The PP measures cost accurately in three complementary ways. C68 reads the `.jsonl` corpus for
**volume** (cache ratio, output fat-tail, first-load) and proved the stack near-optimal on every
token lever that does not cost output quality. C69 reads the same corpus for **behavior** (self-
correction, plan→exec divergence, repeated questions) and priced ~784k output tokens of behavioral
waste. C70 opened the **non-token** axis (failing scheduled tasks, latency, cross-pane
effectiveness). All three are *retrospective*: they answer "what did the session spend, and on
what?"

None answers the question that actually governs whether the kernel's savings are real: **was the
machinery designed to prevent that spend consulted before the spend happened?** The Findings Bus
(PM-03) only saves tokens if a pane *reads its digest before re-reasoning*. The Router (CO-03) only
saves money if a task *is actually demoted to Haiku when Haiku suffices*. The Repo Brain (PM-01)
only saves context if a pane *reuses it instead of re-scanning*. A system that is shipped, tested,
and never consulted produces the same telemetry as a system that does not exist — the retrospective
axes cannot tell "unused" from "absent". PM-03's inert day is the canonical proof: fully built,
26/26 tests green, and **zero** findings published across all of history until it was deliberately
exercised. The audit family said nothing was wrong because nothing was *spent* on it — the whole
point is that nothing was *saved* either.

Adoption is therefore the missing axis: not "what did we spend" but "what fraction of the time did
we use the thing that would have spent less". CO-12 makes that fraction a first-class, corpus-
derived number.

### I.2 The Cognitive Readiness Score

The Readiness Score is a 0–100 composite of adoption-rate signals, each bound to one machinery
system and each computed from data the PP already has on disk (the `.jsonl` transcripts + the
`~/.claude/state` machinery files). It is a **weighted mean of per-lever adoption rates**, where a
lever's rate is *usages / eligible-opportunities* — not raw usage count, because a system used once
in a hundred eligible moments is not adopted. Eligibility is what makes the denominator honest: the
Bus-consult rate counts only sessions where the Bus was **non-empty** (there was something to
consult); the Brain-reuse rate counts only repos where a **valid** Brain existed. A lever with no
eligible opportunities in the window contributes *unknown*, never a spurious 0 or 100 (CO-00
honesty rule: unmeasured is surfaced, never silently scored).

The score is deliberately **not** a single global vanity number. Like WU/MTok it is sliced — per
lever, per day, per week, and (critically) per **adoption cohort**: sessions that used the machinery
vs sessions that did not. The cohort slice is what lets CO-12 prove the machinery *works*: if the
"used PM-03" cohort does not show a better WU/MTok than the "did not" cohort, the lever is not
earning its adoption and the score is Goodharting (§III.2). The composite exists to be scanned at a
glance; the slices are the control signal.

### I.3 The 2x/3x/4x ladder — readiness as leading indicator

The Owner's savings target is tiered, and each tier is gated by a specific set of levers:

- **2x readiness** — duplicate-reasoning elimination + minimum-necessary context: the Bus-consult
  rate (PM-03), the reasoning-dedup hit rate (PM-03 RedundancyTax), and the context-pack minimality
  (GK-06). If these are near zero, no 2x is being realized regardless of what is *built*.
- **3x readiness** — adds economic model routing + loop compression: the model-demotion / Opus-
  avoided counts (CO-03) and the loop-boundedness rate (CO-09).
- **4x readiness** — adds the mature shared substrate: the Brain-reuse rate (PM-01) and the asset-
  writeback rate (CO-05 / GK-08).

Readiness answers, per tier, *"are the levers for tier N actually being pulled?"* — the leading
indicator. WU/MTok (CO-01) is the lagging indicator that confirms the pull produced the saving.
CO-12 reports both side by side so a claim of "we are at 3x" must show both the 3x levers adopted
**and** the WU/MTok cohort gap that adoption produced. A tier claimed on built-not-adopted levers is
rejected by the contract in §III.1.

---

## Part II — The Metrics (each with a concrete data source)

Every metric below names **what measures it** and **whether the instrument exists today** or is a
specified EXECUTION-mode follow-up. This honesty is the point: CO-12 computes what the current
corpus supports now and marks the rest **instrument-pending** — never a faked number (§III.2).

1. **Bus-consult rate** — fraction of sessions whose transcript shows the PM-03 Findings-Bus digest
   was injected **and non-empty** at SessionStart, among sessions where the repo's bus was non-empty.
   *Source (exists today):* the `session_start_hub` Hook 13 emits the `[Findings Bus] …` block into
   `additionalContext`; its presence is greppable in the `.jsonl`, and bus non-emptiness is a stat of
   `~/.claude/state/parallel_mesh/findings_bus_<enc>.jsonl`. *Gates:* 2x.

2. **Reasoning-dedup hit rate** — RedundancyTax consult hits / (hits + misses): how often a pane
   found an existing conclusion instead of re-deriving it. *Source (instrument-pending):* PM-03's
   `consult()` has no hit/miss log today; CO-12 specifies the minimal signal — a one-line append
   per consult `{topic, hit, trust}` to a `readiness/` sidecar — as the follow-up. Until then this
   metric reads *unknown*, not 0. *Gates:* 2x.

3. **Context-pack minimality** — GK-06 Minimal Context Pack size vs the full-file baseline it
   replaced (bytes or tokens saved per navigation). *Source (partial):* GK-06 route cache +
   GK-09 observatory already record pack composition; the baseline delta needs the pre-pack size
   recorded alongside. *Gates:* 2x.

4. **Model-demotion count / Opus-avoided count** — tasks routed to Haiku/Sonnet where Opus was the
   naive default (a demotion), and specifically the count of avoided-Opus dispatches. *Source
   (instrument-pending):* CO-03's `router.py` *decides* the model but does not *log* the counterfactual
   (what the default would have been). CO-12 specifies a per-route record `{task_class, chosen,
   naive_default, demoted:bool}` written by the router's decision point. This is the headline 3x
   signal and the one most worth instrumenting. *Gates:* 3x.

5. **Loop-boundedness rate** — fraction of `/loop` invocations admitted **with** the CO-09 seven-part
   budget declared (cap/checkpoint/stop/kill/resume present) vs launched raw. *Source (partial):*
   CO-09's admission boundary is the natural write point; a loop-admission record makes this exact.
   *Gates:* 3x.

6. **Brain-reuse rate** — fraction of repo work-sessions that consulted a valid PM-01 Repo Shared
   Brain instead of re-scanning the repo. *Source (partial):* PM-01 brain-state freshness
   (`~/.claude/state/parallel_mesh/brain_<enc>.json`) joined to whether the transcript shows a broad
   repo re-read after a valid brain existed. *Gates:* 4x.

7. **Asset-writeback rate** — fraction of sessions that converted a reusable conclusion into a
   permanent asset (CO-05 registry entry or GK-08 graph writeback) vs discarding it at close.
   *Source (exists today):* CO-05 registry + GK-08 writeback both append to state the audit can diff
   against session count. *Gates:* 4x.

8. **Cognitive compression ratio** — the WU/MTok (CO-01) of the machinery-adopting cohort divided by
   the non-adopting cohort: the empirical multiplier adoption actually buys. *Source (exists today):*
   CO-01 WU/MTok joined to the per-session adoption flags above. This is the metric that turns the
   Readiness Score from a process measure into a **proof** of saving. *Gates:* all tiers (it *is* the
   realized multiplier).

The re-audit trigger mirrors the family: recompute after major PP changes or when burn shifts >20%
from the C68 baseline. A metric whose instrument is pending is reported as pending on every run until
the signal is wired — the pending list is itself a readiness signal (how instrumented is the kernel?).

---

## Part III — Contracts, Failure Modes, Rollback, Integration, Anti-patterns

### III.1 The Telemetry-Before-Claims Contract

**No dataset, seal, or sprint may claim an Nx (or any) reasoning/token saving without a readiness
metric backing it, delivered as a `(metric, data-source, value)` triple in the same emission.** An
unmeasured saving is a **hypothesis**, and must be labelled one — never sealed as a result. This
formalizes as a cross-cutting contract the discipline already proven in the audit family (C68:
"si un patrón no tiene ROI medible → ignorar"; C69: no fix below frequency ≥ 5; C70: measure-before-
build proved PM-03 inert and saved building the wrong gate). Binary gate: an emission asserting a
saving either carries the triple, or it carries the word *hypothesis*. There is no third state. A
tier claim (§I.3) additionally requires BOTH the tier's lever-adoption rates AND the WU/MTok cohort
gap — built-not-adopted levers do not substantiate a tier.

### III.2 Failure modes and detection

- **Vanity adoption (read ≠ act).** A pane *reads* the Bus digest and re-reasons anyway. Detection:
  the dedup-hit metric (§II.2) measures ACT (a consult that returned a reused conclusion), not merely
  the digest's presence; a high consult-presence with a low hit rate is the tell.
- **Goodhart (optimizing the score, not the saving).** Adoption rises but WU/MTok does not.
  Detection: the cognitive compression ratio (§II.8) is the ground truth the composite must
  correlate with; a score that climbs while the cohort WU/MTok gap does not is flagged decoupled and
  the weighting is re-examined.
- **Missing instrument faked as 0 or 100.** A metric with no data source today reported as a real
  number. Prevention: instrument-pending metrics read *unknown* and are excluded from the composite's
  denominator (CO-00 honesty), never scored.
- **Survivorship.** Measuring only sessions that used the machinery. Prevention: eligibility
  denominators (§I.2) count the *opportunities*, so non-adoption is in the denominator by
  construction.

### III.3 Rollback protocol

CO-12 is a **measurement-only** layer (like CO-01); it never blocks work — it informs claims and
ranks levers. Rollback is therefore low-risk: (1) disable the composite Readiness Score but keep the
raw per-lever adoption signals (they are just corpus reads); (2) if a specific metric proves mis-
calibrated, drop that metric to *unknown* and recompute the composite on the rest; (3) at no point
does rollback remove the underlying audit truth — C68/C69/C70 and CO-01 predate and outlive CO-12.
The one thing that must never regress: a saving claim without its triple is never re-permitted (the
contract is the durable core; the score is the convenience).

### III.4 Integration contract

- **C68 / C69 / C70** — sibling audit axes; CO-12 is the fourth (adoption). It reuses their corpus
  readers, adds no parallel `.jsonl` reader, and its V-NO-REGRESSION runs their suites in-process.
- **CO-01** — WU/MTok is the ground-truth multiplier the Readiness Score must explain; the cohort
  join (§II.8) is computed against CO-01's ledger.
- **CO-03 / PM-01 / PM-03 / CO-09 / GK-06 / CO-05 / GK-08** — the instrumented machinery. CO-12
  observes each and, where the signal is missing, *specifies* the minimal record for the EXECUTION-
  mode follow-up — it never modifies their logic.
- **CO-10** — every metric carries an honest guarantee level; instrument-pending is a first-class
  state, not a hidden zero.
- **GK-09** — CO-12 borrows the Navigation Observatory's coverage/benchmark presentation pattern
  (per-lever tiles, trend, blind-spot list) rather than inventing a new HUD.
- **`/compact` `/kclear` `/clear`** — each resets the adoption window; CO-12 reports readiness per
  session and per window so a reset does not erase the trend.

### III.5 Anti-patterns (forbidden)

- **Claiming a saving without the `(metric, source, value)` triple.** The contract's core violation.
- **Measuring READ instead of ACT.** Presence of a digest is not adoption; a reused conclusion is.
- **A composite score decoupled from WU/MTok.** A readiness number that does not track the realized
  multiplier is theater.
- **Faking a metric that has no instrument.** Instrument-pending reads *unknown*; it is never
  scored as 0 or 100 to make the dashboard look complete.
- **Optimizing the score.** The score is a proxy; the target is the cohort WU/MTok gap it explains.
- **A parallel corpus reader.** CO-12 extends the audit family's readers; it never re-implements them.

---

### CO-12 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Reports a Cognitive Readiness Score = weighted adoption rate over eligible opportunities, per lever/day/week/cohort | Always; no-opportunity levers = unknown | A single global number that hides the slices |
| Every metric names its data source and whether the instrument exists or is pending | Always | A value for a metric whose instrument is not yet wired (reads unknown) |
| The cohort cognitive-compression ratio ties readiness to CO-01 WU/MTok (proof, not proxy) | When both cohorts have data | That adoption *causes* the gap (correlation, surfaced as such) |
| No saving may be claimed without a (metric, source, value) triple; else it is labelled hypothesis | Always | It does not itself *increase* adoption — it makes non-adoption visible |
| Rollback keeps raw signals + the audit truth; the triple-contract never regresses | On mis-calibration | — |

**Guarantee level (honest):** CO-12 is a **rung-2 measurement layer** (CO-01 class) — it makes
adoption and claim-honesty *visible and enforceable at the claim boundary*; it does not by itself
pull a lever. Several metrics (dedup-hit, Opus-avoided, loop-boundedness) need a minimal logging
signal that does not exist yet; CO-12 **specifies** those as the EXECUTION-mode follow-up and reads
*unknown* for them until wired — the pending list is itself an honest readiness signal. *Sealed
under SCS C74.*
