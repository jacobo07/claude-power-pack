# Parallel Mesh — PM-04 — Parallel Budget Auction & Concurrency Modes

> Once N panes are allowed (PM-02) and are not duplicating (PM-01/PM-03), a scarcer question
> remains: under a shared compute envelope, **which pane gets to spend, and how much?** The
> default answer today is implicit and wrong — budget goes to whoever fires first, so a
> low-value refactor in one pane can burn the envelope a high-value production fix in another
> pane needed. PM-04 replaces arrival-order with an **ROI auction**: panes compete for a shared
> budget by the value of their declared work, and the mesh grants spend to the highest return.
> It also defines **concurrency modes** — Green / Yellow / Red / Black — that scale every pane's
> allowed spend to the *aggregate* envelope pressure, and an **Opus Singleton** rule that keeps
> the most expensive model from being run in parallel against itself.
>
> EXTEND, not NEW: the auction is CO-01's **Cognitive Capital + ROI** made competitive across
> panes; the modes are CO-00's context bands and CO-02's DOWNGRADE-over-REFUSE governor read at
> the *aggregate* (multi-pane) level; the Opus Singleton is CO-08's same-repo discipline applied
> to the model axis. Honest (CO-10): the auction arbitrates grants at the launch/turn boundary
> via the wrapper; it cannot bill a manually-opened pane that never entered the auction.

---

## Part I — The ROI Auction

### I.1 Budget as capital, panes as bidders

CO-01 already frames compute as *Cognitive Capital* measured in Work-Units per M-Tokens. PM-04
makes that capital *contested*: the shared envelope (CO-00's ceiling, CO-02's weekly budget) is a
finite pool, and each pane's intent declaration (PM-02) is a *bid* stating expected cost and
expected ROI. The mesh grants spend in ROI order — the pane whose work returns the most verified
value per token spent is funded first; lower-ROI work is funded from what remains, downgraded, or
deferred. This is the portfolio principle (the proposed "Cognitive Portfolio Manager," which is
otherwise CO-01 and was deferred as COVERED) reduced to its one genuinely-new mechanic: *cross-
pane arbitration* of a shared pool, which no single-session dataset owns.

### I.2 ROI is estimated honestly, then corrected empirically

An auction is only as good as its ROI estimates, and estimates are fallible. PM-04 does not
pretend otherwise. A bid's ROI is a *projection* (value class × confidence ÷ projected cost),
and every grant is reconciled after the fact against CO-01's realized WU/MTok: a pane that bid
high-ROI and delivered low is trusted less on its next bid; a pattern of over-bidding is
surfaced. The auction thus self-calibrates — the same honest-confidence discipline CO-01 applies
to its WU ledger, applied to bids. It never claims to know true ROI in advance; it ranks by best
estimate and corrects by observation.

### I.3 What the auction never does

The auction allocates *spend*, not *permission to exist*. It never blocks a pane from running —
PM-02 governs admission, PM-04 governs budget. A pane that loses the auction is not refused; it is
**downgraded** (smaller model via CO-03, capped output) or **deferred** (run after a funded pane
frees envelope), never killed. This is CO-02's DOWNGRADE-over-REFUSE doctrine at the mesh level:
the fail-safe is always a smaller spend, never a lost pane.

---

## Part II — Concurrency Modes and the Opus Singleton

### II.1 The four modes scale spend to aggregate pressure

The mesh reads one global signal — the *aggregate* projected context/burn across all hot panes
(CO-00 bands + CO-02 summed envelope) — and sets a **concurrency mode** that bounds every pane's
allowed spend:

- **Green** — aggregate pressure low. Small prompts run freely, any model, no output caps. The
  mesh is cheap and fluid.
- **Yellow** — pressure rising (CO-00's 45–55% action band at the aggregate). Output caps and
  model caps apply; the auction tightens; expensive bids are downgraded before cheap ones.
- **Red** — pressure high. **Only one heavy task runs;** every other pane is restricted to
  review / index / verify work (the non-duplicative roles from PM-02's demote resolution). The
  envelope is protected by collapsing parallel *heavy* work to one.
- **Black** — pressure at the ceiling (CO-00's 60% / CO-02's breach). **Checkpoint + `/compact`
  is mandatory** before any new heavy spend; the mesh stops taking on new load and preserves
  state (the CO-05 breach-RCA + CO-07 hibernation surfaces). Black is the kernel's "stop digging"
  band, expressed across panes.

The modes are not arbitrary tiers; each maps to a CO-00 band, so PM-04 inherits the sealed root
law rather than inventing a parallel one.

### II.2 The Opus Singleton rule

The single most expensive parallelism is *two Opus-heavy panes on the same repo* — maximum token
rate, maximum overlap risk. PM-04's **Opus Singleton**: at most one Opus-heavy hot session per
repo without an explicit Owner justification. A second pane wanting Opus on the same repo is
arbitrated down to Sonnet/Haiku via CO-03 (exploration / test / doc / review work does not need
Opus — that is the HR-COST-001 discipline), or it waits for the first Opus session to free the
slot. This is CO-08's same-repo cap re-expressed on the *model* axis: the recalibration (PM-02)
allows N same-repo panes, but not N *Opus* same-repo panes — the most expensive resource keeps a
singleton default, satisfiable only by explicit justification, never by a silent second grant.

### II.3 Interaction with the recalibrated cap

PM-04 and PM-02 are complementary halves of the recalibration. PM-02 answers *may this pane run*
(scope non-overlap); PM-04 answers *how much may it spend* (ROI + mode + model). Together they
replace CO-08's single blunt lever (count) with two precise ones (scope, budget). A repo can thus
run four panes — one Opus author (funded, Green/Yellow), two Sonnet reviewers/indexers (cheap,
non-overlapping), one Haiku doc pane — and stay within an envelope that CO-08's `SAME_REPO_CAP=1`
would have forbidden outright, because the mesh can now *prove* the four are non-overlapping and
*bound* their combined spend.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **ROI mis-estimate funds low-value work.** A pane over-bids and wins budget it did not deserve.
  Detection: post-hoc realized WU/MTok vs bid; persistent over-bidders are down-weighted (I.2).
- **Mode thrash.** Aggregate pressure oscillates around a band edge, flipping Green↔Yellow↔Red
  rapidly. Detection: mode-flip frequency; apply hysteresis (a mode holds until pressure clears
  the band by a margin), the same anti-thrash discipline CO-08 uses for hibernation churn.
- **Opus Singleton escaped by a manual pane.** An Owner opens a second Opus session outside
  kclaude. Detection: the un-gated-pane detector (CO-02/CO-10) flags it; its burn is counted
  against the envelope and surfaced — never silently absorbed.
- **Starvation of a legitimate high-cost task.** A genuinely high-ROI but expensive task never
  wins because the mode is stuck Red. Detection: foregone high-projected-WU work → the mode
  thresholds or the auction is too conservative; tune against realized ROI.

### III.2 Rollback protocol

PM-04 degrades to CO-02 + CO-08 alone. (1) Demote the auction to *arrival-order* with CO-02's
existing per-session governor — today's behavior, no cross-pane ranking. (2) Disable the modes,
reverting to CO-00's per-session bands without the aggregate mode overlay. (3) Demote the Opus
Singleton to CO-08's count cap. The fail-safe direction is **toward smaller spend and the sealed
CO-02/CO-08 baseline, never toward unbounded grants**: a broken auction must not hand out more
budget than the single-session governor already allows; it reverts to that governor.

### III.3 Integration contract

- **CO-01 (parent)** — the auction ranks by CO-01's Cognitive ROI; grants are reconciled against
  its realized WU/MTok ledger.
- **CO-02 (parent)** — the modes are CO-02's DOWNGRADE-over-REFUSE governor read at the aggregate;
  a lost auction is a downgrade, never a refusal.
- **CO-08 (parent)** — the Opus Singleton is CO-08's same-repo discipline on the model axis; the
  summed envelope is inherited.
- **CO-00** — each mode maps to a CO-00 context band (Green<action-band, Yellow=action-band,
  Red=high, Black=ceiling), so the root law governs the modes.
- **CO-03** — downgrades and Opus-arbitration route through the Dynamic Router.
- **PM-02** — bids *are* the cost/ROI/model fields of the intent declaration.
- **`/kclaude`** — the auction runs at launch (grant the model/budget) and the mode is set from
  aggregate pressure. **`/compact`** — mandatory in Black; frees envelope and can lift the mode.
  **`/kclear`** — a cleared pane returns its budget to the pool. **`/loop`** — a loop's per-
  iteration spend is bid once and bounded by the current mode; a loop in Red is restricted or
  paused (it is heavy repeated spend, the CO-09 surface).

### III.4 Anti-patterns (forbidden)

- **Funding by arrival order.** The pre-mesh default; budget goes to ROI, not to whoever fired
  first.
- **Refusing a losing pane instead of downgrading it.** DOWNGRADE-over-REFUSE; a lost auction is a
  smaller spend, never a killed pane.
- **Two Opus-heavy panes on one repo without explicit justification.** The Opus Singleton default;
  satisfied by justification, never by a silent second grant.
- **Running heavy parallel work in Red/Black.** Red collapses to one heavy task; Black mandates
  checkpoint+compact. Ignoring the mode is the burn the bands exist to prevent.
- **Trusting a bid's ROI without post-hoc reconciliation.** Bids self-calibrate against realized
  WU/MTok; an unreconciled auction drifts.
- **Claiming the auction bills a manual pane.** It governs panes that enter through the wrapper;
  un-gated panes are flagged and counted, not silently billed (CO-10).

---

### PM-04 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Shared budget granted in ROI order, reconciled post-hoc against realized WU/MTok | Panes bid via their intent declaration | True ROI known in advance (bids are estimates, corrected by observation) |
| Concurrency mode (Green/Yellow/Red/Black) scales every pane's spend to aggregate CO-00 pressure | Always | A mode for a manual pane that never entered the auction (flagged, counted) |
| Opus Singleton: ≤1 Opus-heavy session per repo without explicit justification | Wrapper-launched panes | Prevention of a manually-opened second Opus pane (flagged, counted) |
| A lost auction downgrades or defers a pane; never kills it | Always | Unbounded grants — the fail-safe is always smaller spend |
| Rollback reverts to CO-02 governor + CO-08 cap (arrival order), no over-grant | On misbehavior | — |

**Guarantee level (honest):** rung-3 at the launch boundary (grant + mode set in kclaude) +
rung-2 in-turn (mode-driven caps advised) + CO-02 downgrade enforcement. The auction reads
**declaration files + envelope state**, not IPC; it governs wrapper-entered panes and flags
un-gated ones. Parents: **CO-01 / CO-02 / CO-08**. *Sealed under SCS C65.*
