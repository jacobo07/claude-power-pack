# Cognitive OS — CO-01 — Operating Economics & Cognitive Capital

> The unified cost model of the kernel. CO-00 sets the ceiling; CO-01 defines **what a
> thing costs** and **what a thing is worth**, so every other dataset can reason in one
> currency. Central metric, instantiated here: **verifiable work finished per unit of
> compute cost** — operationalized as **Work Units per Million Tokens (WU/MTok)**.
>
> EXTEND, not NEW: builds directly on `tools/token_ground_truth.py` (real per-turn usage
> from transcripts) and `modules/wrapper/cost_gate.py` (daily/weekly burn). Reuses the
> **Production Reality Gate** (PP done-gates / Reality Contract) as the *sole* definition
> of "verified work" — CO-01 never builds a parallel verification system.

---

## Part I — The Unified Cost Ledger

### I.1 Why "tokens used" is the wrong unit

The PP already measures tokens accurately. `token_ground_truth.py` reads the real
`input_tokens`, `output_tokens`, `cache_creation_input_tokens`, and
`cache_read_input_tokens` straight from the transcripts and computes a lifetime cache
ratio (~96.6% measured). But tokens are an *input*, not an outcome. A session that burns
2M tokens and ships a verified, tested feature is cheap; a session that burns 2M tokens
re-deriving context across four parallel panes and ships nothing is ruinous — and the
token counter cannot tell them apart. The 48h/49.2M-token forensic is exactly this
failure of unit: the number was large, but the number alone did not say whether the
spend bought work. CO-01 exists to make the *denominator* (cost) richer and the
*numerator* (verified work) real, so the kernel optimizes the ratio, not the raw spend.

### I.2 The seven cost dimensions

CO-01 models cost as a vector, not a scalar. A unified ledger records, per operation and
per session, seven dimensions — each already partly observable in the PP today:

1. **Token cost** — input + output + cache-creation, priced per model. The cache-read
   tokens are tracked but priced near-zero (the 96.6% cache ratio is *why* the PP is
   affordable; CO-01 makes that explicit rather than implicit). Source:
   `token_ground_truth`.
2. **Context cost** — the effective-context growth an operation causes (CO-00's
   projection input). Context is a *consumable*: every percentage point spent toward the
   60% ceiling has an opportunity cost (it is a point unavailable to later work in the
   session). CO-01 prices context growth as a first-class cost, not a side effect.
3. **Latency cost** — wall-clock. A 5-second tool call and a 5-minute subagent swarm
   differ in a dimension tokens cannot capture. Source: existing prelaunch/agent timing.
4. **RAM / continuity cost** — proximity to the `ram_guard` WARN/CRIT bands; an operation
   run at 26GB claude.exe RAM carries an OOM-continuity risk premium an identical
   operation at 8GB does not.
5. **Parallelism cost** — the multiplier from concurrent hot sessions/subagents. The 48h
   burn proved this is super-linear: two panes re-deriving the same context cost far more
   than 2× a single pane's useful output. CO-08 governs the cap; CO-01 prices the
   multiplier.
6. **Risk cost** — the expected cost of an operation's failure modes: a `/loop` that may
   not converge, a deploy without tests (HR-CASCADE-001), an operation projected near the
   ceiling. Risk is priced as expected recovery cost × probability.
7. **Recovery cost** — what it would cost to get back if this operation corrupts state:
   the price of a `/kclear` + re-bring-up, or a hibernation restore (CO-07). Operations
   that raise recovery cost are charged for it.

The ledger does not require all seven to be precisely measurable; CO-00's honesty rule
applies — an unmeasurable dimension is recorded as *unknown* and surfaced, never silently
zeroed. The value of the vector is that it lets the kernel compare operations the token
counter renders identical.

### I.3 The ledger as an EXTENSION, not a rebuild

CO-01 is explicitly an extension of two live systems. `token_ground_truth.analyze()`
already produces lifetime/month/today aggregates and per-session cache ratios; CO-01
adds the other six dimensions alongside the token dimension it already owns, keyed by the
same transcript-derived session identity. `cost_gate.py` already projects daily and
weekly burn and consults `classify_tier` for a model hint; CO-01 supplies it the richer
cost vector so its projection is no longer token-only. Nothing in CO-01 replaces these;
the anti-pattern (explicitly forbidden) is to stand up a second token tracker or a second
verification system parallel to the Reality Gate.

---

## Part II — Cognitive Capital: the Work-Unit Metric

### II.1 Defining a verifiable Work Unit (the numerator)

A Work Unit is the kernel's atom of *verified* output. The defining constraint, and the
reason CO-01 does not drift into vanity metrics: **a Work Unit only counts when the
Production Reality Gate confirms it.** The PP already has the gate — done-gates, the
Reality Contract (zero placeholders/mocks/stubs), V-gate suites, observed test PASS, the
`is_done()` OQS contracts. CO-01 does not redefine "done"; it *counts* the things the
existing gate has already certified as done.

Concretely, a Work Unit is credited when an operation produces an artifact that passes
its applicable gate: a code change with an observed test PASS; a dataset that passes its
V-gates; a deploy that passes its healthcheck (the rollback-skill Reality Contract); a
review that completes the Pre-Report Gate. An operation that produces an artifact which
*fails* or *skips* its gate earns **zero** Work Units regardless of token spend — this is
what makes WU/MTok honest. The scaffold illusion (Mistake #16) earns nothing; a "done"
claim with absent artifacts (HR-CONTEXT-001) earns nothing. The numerator is deliberately
hard to inflate, because the whole point is to make wasted spend visible.

### II.2 Work Units per Million Tokens (WU/MTok) — the ratio

The kernel's headline efficiency number is WU/MTok: verified Work Units produced per
million tokens of true cost (output + cache-creation weighted; cache-read near-free).
The ratio is computed from the same transcripts `token_ground_truth` already reads,
joined to the gate outcomes the PP already records. WU/MTok makes the 48h burn legible
*as a ratio collapse*: the tokens spiked while verified work did not, so WU/MTok cratered
— a signal the raw token counter could never give.

WU/MTok is not a single global number; it is sliced by the dimensions that matter:
per-model (does Opus on a NANO task tank the ratio? — HR-COST-001), per-operation-class
(do parallel same-repo panes have a worse ratio than sequential? — the forensic says
yes), per-session, per-day. The slices are what turn the metric from a scoreboard into a
control signal: a low WU/MTok slice for "Opus on rename" is an instruction to route
cheaper (CO-03); a low slice for "parallel same-repo panes" is an instruction to cap
(CO-08).

### II.3 Cognitive ROI and the (folded) Futures Market

The Reality Scan flagged "Context Futures Market" and "Cognitive ROI Scoring" as
standalone systems but rated them SKIP-LOW-ROI until a real cost ledger exists. CO-01
folds them in as *sections* rather than separate datasets, honestly scoped:

- **Cognitive ROI score** — for a *planned* operation, the ratio of projected Work
  Units to projected cost vector. A pre-flight ROI score lets CO-03 and CO-09 prefer the
  operation that buys the most verified work per unit of compute. It is an *estimate*
  (confidence-bounded), used to rank, never asserted as fact.
- **Context futures (honest framing)** — not a market with prices and trading, which
  would be speculative theater, but a simple forward reservation: an operation that will
  need a large context block later can *reserve* budget now so the kernel does not admit
  intervening operations that would starve it. This is a scheduling primitive (consumed
  by CO-00's admission and CO-08's scheduler), not an economic simulation. CO-01 states
  plainly that the elaborate "market" framing is deferred until the basic ledger and
  reservation primitive have proven themselves — building the market first would be the
  anti-pattern of pricing a currency nobody yet earns.

---

## Part III — Calibration, Failure Modes, Rollback, Integration

### III.1 Feeding CO-00's projection (the calibration loop)

CO-01's most important *service* to the kernel is calibration. CO-00 admits operations by
projecting their context cost; that projection is only as good as the historical
relationship between operation class and observed growth. CO-01 owns that history: every
completed operation contributes (operation class, projected cost vector, *actual*
realized cost vector, Work Units earned) to a calibration ledger. When CO-00 breaches
(Part III of CO-00), the RCA reads CO-01's ledger to determine whether the projection
*under-estimated* (calibration gap → re-fit) or was *skipped* (wiring gap → fix the
gate). The calibration loop is what makes the ceiling sharpen over time instead of drifting.

### III.2 Observability

CO-01 exposes: the current session's running cost vector and WU/MTok; the day's and
week's WU/MTok with trend; the worst-ratio slices (the operations bleeding compute for
little verified work); and the calibration accuracy (projected vs actual cost spread).
These surface through the statusline HUD's economy segment, the wrapper pre-launch
advisory (which can now say "this class of operation has historically returned 0.2
WU/MTok — consider CO-03 routing"), and CO-10's ledger. Honesty rule (SCS C53 lineage):
all numbers come from transcripts + gate outcomes, never optimistic estimates; an
unmeasured dimension reads *unknown*.

### III.3 Failure modes and detection

- **Numerator gaming.** Crediting Work Units for ungated output would corrupt the whole
  metric. Detection/prevention: a Work Unit *requires* a gate-pass record; no record, no
  credit. The metric is intentionally hard to inflate.
- **Denominator blind spots.** A cost dimension is unmeasurable (e.g. latency on a host
  that didn't record it) → recorded *unknown*, the WU/MTok for that slice is flagged
  low-confidence rather than silently computed on a partial denominator.
- **Calibration overfit.** Re-fitting projection to a small recent window could chase
  noise. Detection: calibration changes are bounded per cycle and reverted if breach
  rate rises after a re-fit (ties to CO-00 rollback).
- **Reality-Gate coupling risk.** If the done-gate definition changes, the Work-Unit
  count shifts. This is *correct* (CO-01 follows the gate, by design) but must be visible:
  a gate-definition change is logged as a metric discontinuity so trend breaks are
  explained, not mysterious.

### III.4 Rollback protocol

CO-01 is a *measurement and pricing* layer; it never blocks work directly (CO-00 and
CO-02 do the blocking, using CO-01's numbers). Therefore its rollback is low-risk: (1)
if the cost vector or WU/MTok proves mis-calibrated, the kernel reverts to **token-only**
costing (the pre-CO-01 `cost_gate`/`token_ground_truth` baseline) — CO-00 and CO-02 then
fall back to their token-only projections (wider margins, more conservative); (2) the
calibration ledger reverts to last-good parameters; (3) the Work-Unit crediting can be
disabled, leaving the raw token visibility (SCS C53) intact. At no point does rolling back
CO-01 remove the underlying token truth, because that truth is `token_ground_truth`,
which predates and outlives CO-01.

### III.5 Integration contract

- **CO-00** — CO-01 supplies the cost vector and calibration the ceiling's projection
  consumes; every breach RCA reads CO-01's ledger.
- **CO-02** — the governor enforces budgets denominated in CO-01's cost vector and WU/MTok.
- **CO-03** — the router ranks resolutions by Cognitive ROI (CO-01 estimate).
- **CO-09** — loop/subagent budgets are priced and their realized WU/MTok scored, so an
  unproductive loop is *measurably* unproductive.
- **`/loop` `/compact` `/kclear` `/clear`** — each is a costed event in the ledger: a
  `/compact` has a recovery cost and resets the context-cost baseline; a `/kclear` costs
  more; a `/clear` is a budget reset. The ledger prices them so the kernel can reason
  about *when* recovery is worth its cost.
- **Cursor / parallel sessions** — per-session ledgers aggregate to the global envelope
  CO-08's scheduler consults; the parallelism multiplier (I.2 dim 5) is computed here.
- **Knowledge Vault** — worst-ratio slices and calibration insights are CO-05 assets, so
  the kernel learns its own inefficiencies once and routes around them thereafter.

### III.6 Anti-patterns (forbidden)

- **Optimizing tokens instead of WU/MTok.** Cutting spend by cutting *work* improves the
  wrong number. The ratio, not the denominator, is the target.
- **A parallel verification system.** Defining "done" anywhere but the Production Reality
  Gate. CO-01 counts the gate's verdicts; it never re-judges them.
- **Crediting ungated output.** Any Work Unit without a gate-pass record.
- **Building the Futures Market before the ledger earns trust.** Pricing a currency the
  kernel does not yet reliably produce.
- **Silently zeroing an unmeasured cost dimension.** Unknown is unknown (CO-00 honesty).

---

### CO-01 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Reports a 7-dimension cost vector per operation/session, EXTENDING token_ground_truth | Always; unmeasurable dims = unknown | Precise values for dims the host did not record |
| Credits a Work Unit only when the Production Reality Gate certifies the artifact | Always | It never re-defines "done" — it counts the gate's verdicts |
| WU/MTok sliced by model/class/session/day as a control signal | Always | A single global number that hides the slices |
| Supplies CO-00 the calibration that sharpens the ceiling projection | Per completed operation | That every operation is projectable (un-projectable = flagged, not blocked) |
| Rollback reverts to token-only costing without losing token truth | On mis-calibration | — |

**Guarantee level (honest):** CO-01 is a *measurement + pricing* layer (rung-2 class) —
it informs and ranks; the *blocking* belongs to CO-00/CO-02/CO-08 which consume its
numbers. It makes wasted compute **visible and comparable**; it does not, by itself, stop
it. *Sealed under SCS C61.*
