# Cognitive OS — CO-02 — Economics Governor & Budget Violation Registry

> The enforcement arm of the economy. CO-01 prices and measures; **CO-02 sets budgets and
> governs them across all sessions**, and keeps the durable record of every breach so the
> kernel never normalizes overspend. Where CO-00 governs the *context* envelope, CO-02
> governs the *compute* envelope (tokens, weekly burn, model spend, parallel multiplier).
>
> EXTEND: `modules/wrapper/cost_gate.py` (W5 daily/weekly burn, the `WEEKLY_OUTPUT_LIMIT_EST
> = 66M` advisory projection) and SCS C59 (weekly-burn awareness). CO-02 promotes those
> advisories into a governed envelope and adds the violation registry that does not exist
> today.

---

## Part I — The Governor: a Global Compute Envelope

### I.1 From advisory projection to governed envelope

Today the PP *projects* weekly burn and *warns* when the 24h rate is ≥1.5× the June
average — but it never blocks, and the projection is per-launch and stateless. CO-02
turns this into a **governed envelope**: a set of nested budgets, each with an action
band (echoing CO-00's GREEN/AMBER/RED) and each enforced at the strongest honest surface
available (the wrapper launch boundary, per CO-00's ladder).

The nesting matters because compute is spent at multiple time-scales:

- **Per-operation budget** — inherited from `cost_collapse.route` (NANO $1 / MICRO $15 /
  MACRO $30 / ULTRA $100). CO-02 makes these *live* ceilings, not just routing hints: an
  operation tracking toward >2× its class budget (HR-COST-002) is surfaced and re-graded.
- **Per-session budget** — a session's cumulative cost vector. A session is the unit the
  Owner experiences; its budget is what keeps a single window from becoming a 49.2M-token
  outlier.
- **Per-day budget** — the daily burn `cost_gate` already computes, now with a band.
- **Per-week budget** — the `WEEKLY_OUTPUT_LIMIT_EST` envelope, now governed: as the week's
  cumulative burn climbs through AMBER toward RED, the governor tightens — biasing the
  router cheaper (CO-03), lowering loop iteration caps (CO-09), and refusing low-ROI
  parallel sessions (CO-08).

The envelope is **global across sessions**: this is the property the current per-launch
advisory lacks and the property the 48h burn needed. Two panes each individually "fine"
can jointly blow the weekly envelope; only a governor that sums across live sessions sees
it. CO-02 aggregates every session's CO-01 ledger into one running total and governs
against that.

### I.2 What the governor consults and what it does

The governor reads CO-01's cost vectors (all live sessions) and WU/MTok slices, plus
CO-00's context state, and produces, at each wrapper-owned boundary, an **admission verdict**
for budget: ADMIT / ADMIT-DOWNGRADED / REFUSE. The middle verdict is the important one —
the governor rarely needs to flatly refuse; far more often it *downgrades*: admit the
operation but force a cheaper model (CO-03), a lower iteration cap (CO-09), or a sequential
rather than parallel execution (CO-08). Downgrade preserves the Owner's ability to do the
work while bending its cost back under the envelope. REFUSE is reserved for the operation
whose *minimum viable* form still breaches a hard budget — and like CO-00, the refusal has
no bypass flag; it can only be satisfied by changing the operation's inputs.

### I.3 Honest guarantee level

Per CO-10's ladder and CO-00's analysis, the governor's real enforcement is **rung 3
(wrapper, launch-boundary)** plus **rung 2 (in-turn advisory)**. It can refuse to *launch*
an over-budget loop/session/swarm; it cannot halt a running session's spend mid-turn. The
in-turn surface (a Stop/PostToolUse hook reading CO-01's running cost) can warn and stage a
checkpoint when a session crosses its per-session RED band, but the Owner/▸ must act on it
(BL-0003: no auto-fired slash commands). CO-02 states this plainly; it does not claim a
mid-turn spend halt it cannot deliver.

---

## Part II — The Budget Violation Registry

### II.1 Why a registry, and why it is non-negotiable

A budget that is exceeded and forgotten is not a budget. The PP today has no durable
record of budget overages — `cost_gate` fires an advisory line that scrolls away. CO-02
introduces the **Budget Violation Registry**: a durable, append-only ledger of every
budget breach, structured so the kernel can learn from its own overspend. This is the
economic twin of CO-00's breach RCA: where CO-00 records *context* breaches, CO-02 records
*compute* breaches, and the two cross-reference (a context breach and a budget breach in
the same operation are usually the same incident seen from two axes).

Each registry entry captures: which budget tier was breached (operation/session/day/week);
the operation class and model; the projected vs actual cost vector (the calibration miss);
the Work Units earned (was the overspend at least *productive*?); whether the governor
*downgraded* or *refused* and was overridden by an un-gated path (a bare `claude` launch
escaping the wrapper — flagged honestly, never hidden); and the RCA disposition.

### II.2 The mandatory-investigation protocol

Like CO-00, CO-02 treats a *hard*-budget breach as an incident requiring RCA, not a normal
event. The protocol distinguishes severity honestly:

- A **soft-band crossing** (entering AMBER/RED) is a governed event — the governor tightens
  and logs, no RCA required; this is the system working.
- A **hard-budget breach** (week envelope exceeded, or a session past 2× its class budget
  with low WU/MTok) is an incident: it must produce an RCA answering *why the governor did
  not prevent it*. The usual answers: the spend happened in-turn after admission (the
  honest residual the wrapper cannot reach — the RCA then asks whether the per-session
  in-turn advisory fired and was ignored, or never fired); the operation launched outside
  the wrapper (un-gated path — the RCA flags the coverage gap); or the projection
  under-estimated (calibration miss → CO-01 re-fit).

The registry's purpose is not blame; it is calibration and coverage. A cluster of breaches
on one operation class re-grades that class's budget or routing; a cluster on the un-gated
launch path is the strongest possible argument for the Owner to always launch via kclaude
(the only path that gives rung-3 coverage). The registry makes the cost of the coverage gap
*countable* instead of anecdotal.

### II.3 Connection to the 48h burn (the founding incident)

The Budget Violation Registry exists because the 49.2M/48h burn had no durable home. Had
the registry existed, the parallel-panes pattern would have appeared as a cluster of
session-budget breaches correlated with `repo_coordinator.parallel_burn()` detections, and
the systemic response (CO-08's hard cap) would have been data-driven from the first
recurrence rather than reconstructed forensically after the fact. CO-02 ensures the *next*
novel burn pattern is caught as a registry cluster long before it becomes a 48h forensic.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **Governor starves legitimate work (false REFUSE).** An over-tight envelope or a
  mis-calibrated projection refuses operations the Owner genuinely needs. Detection: a rise
  in REFUSE verdicts with high *projected* WU/MTok (the kernel is refusing work it predicted
  would be productive). Response: widen bands / revert calibration (shared with CO-00/CO-01
  rollback).
- **Envelope blind to an un-gated session.** A bare `claude` launch spends outside the
  governor's view, so the global total under-counts. Detection: a session in the transcripts
  with no wrapper pre-launch record; CO-10 surfaces the coverage gap rather than letting the
  global total silently lie.
- **Downgrade that harms quality.** Forcing Haiku on a task that genuinely needs Sonnet to
  earn its Work Units would trade a budget win for a WU loss. Detection: WU/MTok *falls*
  after a downgrade for that class → the downgrade rule for that class is wrong → revert
  (this is why the governor optimizes WU/MTok, not raw spend — a quality-destroying downgrade
  shows up as a worse ratio, not a better one).
- **Registry growth.** Append-only ledgers grow; CO-06 (GC) prunes resolved old entries
  under a retention policy, never orphaning open RCAs.

### III.2 Rollback protocol

CO-02's rollback mirrors CO-00's: (1) demote the governor from *enforcing* (ADMIT/DOWNGRADE/
REFUSE) back to *advisory* (the SCS C59 baseline — warn, never block), restoring prior
behavior while keeping the registry recording; (2) revert budget bands and downgrade rules
to last-good; (3) the registry itself never rolls back — its history is the data that fixes
the calibration. Disabling CO-02 entirely returns the system to `cost_gate`'s advisory
projection with no loss of the underlying token truth.

### III.3 Integration contract

- **CO-00** — context and compute envelopes co-govern; a context breach and a budget breach
  in one operation cross-reference as one incident.
- **CO-01** — the governor enforces budgets denominated in CO-01's cost vector and WU/MTok;
  every verdict is priced.
- **CO-03 / CO-08 / CO-09** — DOWNGRADE verdicts are *executed* by these: cheaper model
  (CO-03), sequential not parallel (CO-08), lower iteration cap (CO-09).
- **`/loop`** — refused/downgraded at admission if its projected cost breaches the envelope
  (CO-09 supplies the loop's cost projection).
- **`/compact` `/kclear` `/clear`** — priced recovery events (CO-01); the governor may
  *recommend* one when a session's per-session budget hits RED, staged for the Owner.
- **Cursor / parallel sessions** — the global envelope is summed across live sessions; this
  is the governor's defining capability and the direct answer to the parallel-panes burn.
- **Knowledge Vault** — registry clusters and re-grade decisions are CO-05 assets.

### III.4 Anti-patterns (forbidden)

- **A bypass flag on the budget gate.** Forbidden (CO-00 II.4 lineage). The gate is
  satisfied, not silenced.
- **Optimizing raw spend over WU/MTok.** A downgrade that destroys verified work is a loss,
  not a saving.
- **A forgotten breach.** Any hard-budget breach without a registry entry + RCA disposition.
- **Claiming a mid-turn spend halt.** The governor blocks at launch boundaries and advises
  in-turn; it does not pretend to stop a running turn's spend.
- **Hiding the un-gated path.** A session that escaped the wrapper must be flagged as
  uncovered, never counted as governed.

---

### CO-02 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Governs a nested global envelope (op/session/day/week) summed across all live sessions | At wrapper launch boundaries + in-turn advisory | A mid-turn halt of a running session's spend |
| Prefers DOWNGRADE over REFUSE; refusal has no bypass, only satisfaction | Always | That every over-budget op can be downgraded (minimum-viable breach = REFUSE) |
| Records every hard-budget breach in a durable registry with mandatory RCA | Always | — |
| Surfaces un-gated (non-wrapper) sessions as coverage gaps, never counts them as governed | Always | Coverage of sessions launched outside kclaude |
| Rollback demotes governor→advisory without losing the registry or token truth | On false-starvation | — |

**Guarantee level (honest):** rung-3 launch-refusal/downgrade + rung-2 in-turn advisory;
the registry is rung-independent (pure record). The governor makes overspend *expensive to
ignore*, not physically impossible mid-turn. *Sealed under SCS C61.*
