# Cognitive OS — CO-00 — Hard Context Budget Contract

> **Root dataset of the Cognitive Operating System family.** Every other dataset
> (CO-01 … CO-10) inherits the law defined here. This is not a feature; it is the
> physical property under which the whole kernel operates: **the effective context
> of any session never exceeds 60%.** Not a warning. Not a soft target. A ceiling.
>
> Family metric (inherited by all): **verifiable work finished per unit of compute
> cost** (time + tokens + RAM + risk), never "tokens used".
>
> Decision lineage: Owner-approved 2026-06-30 — scope = 11 datasets; CO-00 framing =
> *layered guarantee with the wrapper-controlled surface pushed maximally hard*. A
> physical in-process kill switch is impossible inside Claude Code; CO-00 states that
> honestly and extracts every guarantee the architecture can actually provide.

---

## Part I — The Ceiling as a Physical Property of the System

### I.1 Why a ceiling at all, and why 60%

The Power Pack accumulated, over dozens of sessions, a measurable failure mode: a
session grows until the model is reasoning inside a context window so full that every
new turn is expensive, the cache churns, recovery becomes fragile, and the marginal
work produced per token collapses. The 2026-06-28→30 forensic made the cost legible —
**49.2M output tokens in 48 hours, 1.81× the historical daily rate**, driven by large
structured prompts fired in parallel panes of the same repository. SCS C59 (weekly
burn awareness) was the point response; this contract is the systemic one.

The number 60% is not arbitrary and it is not the visible context bar. Claude Code
reserves roughly 16.5% of the raw window for the autocompact buffer, so the *usable*
context is ~83.5% of the nominal window. The 60% ceiling is expressed against
**effective/usable** context, which means it sits comfortably below the zone where
autocompact, cache thrash, and recovery fragility begin. Above 60% effective, three
independent degradations compound: (1) per-turn input cost rises because more of the
window must be re-attended; (2) the probability that a single `/compact` or `/kclear`
can cleanly recover the session drops, because there is more live state to serialize;
(3) the risk that a host event (RAM pressure, Cursor reload, power loss) catches the
session in an unrecoverable state rises. 60% is the line beyond which the *cost of the
context itself* begins to dominate the cost of the work.

### I.2 The conservative action band: 45–55%

A ceiling defended only at the ceiling is already breached by the time it fires. CO-00
therefore defines an **action band of 45–55% effective context** as the operating
envelope. Inside this band the system begins *graduated* responses — surfacing
hygiene candidates (CO-06), proposing asset extraction (CO-05), recommending session
hibernation (CO-07), and biasing the router toward cheaper resolutions (CO-03) —
**before** the 60% line is in danger. The bands are deliberately layered:

- **≤ 45% — GREEN.** Normal operation. The kernel observes and accrues assets but
  does not intervene.
- **45–55% — AMBER (action band).** Graduated, non-blocking interventions begin.
  Hygiene, asset extraction, and routing pressure activate. The Owner sees advisories
  but work continues.
- **55–60% — RED (pre-ceiling).** Hard interventions are *staged*: the next
  launch-class operation (a new `/loop`, a subagent swarm, a large prompt) is gated by
  projection (Part II). Existing work is allowed to finish a bounded unit, then a
  checkpoint + `/compact` or `/kclear` is strongly recommended.
- **> 60% — BREACH.** A production incident (Part III). Not a normal event; it
  triggers mandatory RCA. The system must have *projected and prevented* this; if it
  occurred, the projection failed and that failure is itself the bug.

### I.3 Projective, not reactive — the defining inversion

The single most important property of CO-00, and the one that distinguishes it from
every pre-existing PP mechanism, is that it is **projective**. The existing parents —
`modules/zero-crash/hooks/context-watchdog.py` (snapshot at 60% used, advisory at
70%) and `modules/cpc_os/context_monitor.py` (HEALTHY / COMPACT_NEEDED / KCLEAR_NEEDED
from RAM, jsonl size, turn count) — are **reactive**: they observe a threshold that
has *already* been crossed and then advise. Reactive enforcement of a ceiling is a
contradiction in terms; by the time the threshold trips, the expensive context already
exists in the window.

CO-00 inverts this. Before any context-growing operation is admitted, the system must
answer a forward question: *if this operation runs, what is the projected effective
context after it completes?* The unit of admission is not "are we over budget now"
but "will this push us over." A large prompt with an estimated output and tool-call
fan-out has a projectable context cost; a `/loop` with N iterations and a per-iteration
growth estimate has a projectable trajectory; a subagent swarm has a projectable
aggregate. The projection is necessarily an *estimate with a confidence interval*, and
CO-00 mandates that the system act on the **conservative edge** of that interval — the
projection assumes the worse plausible outcome, so the ceiling is defended with margin.

This is why the action band is 45–55% and not 58–60%. The projection horizon needs
room. An operation admitted at 52% effective context with a projected +6% growth lands
at 58% — inside RED but under the ceiling — and that is acceptable *only because the
projection was made before admission*. The same operation admitted at 57% is refused,
because its conservative projection breaches 60%.

### I.4 What "effective context" is measured from

CO-00 does not invent a new sensor; it composes existing ones into a single effective-
context estimate and adds the projection layer on top. The inputs, all already on disk:

- **Transcript size** — the live `~/.claude/projects/<enc-cwd>/<sid>.jsonl` byte size,
  the same signal `context_monitor` uses (16MB COMPACT / 24MB KCLEAR bands).
- **Turn count** — the same monitor's 6000/12000 bands.
- **The statusline bridge** — `gsd-statusline.js` writes
  `/tmp/claude-ctx-<sid>.json` with `remaining_percentage` and `used_pct` on every
  render; `context-watchdog.py` already consumes it. This is the closest thing to a
  ground-truth context percentage the host exposes, and CO-00 treats it as the primary
  effective-context signal, cross-checked against jsonl size and turn count so a single
  stale or missing reading can never silently defeat the ceiling.
- **RAM** — `ram_guard` (WARN 20GB / CRIT 28GB on claude.exe), as a correlated-pressure
  signal, not a context measure per se, but a tie-breaker when the context estimate is
  ambiguous.

The **projection** layer is the genuinely new contribution: a forward estimate of how
each admitted operation moves the effective-context number, calibrated against the
historical relationship between operation class (prompt size, loop depth, swarm width)
and observed context growth recorded in the transcripts CO-01 will aggregate.

---

## Part II — The Enforcement Ladder and the Wrapper-Maximal Block

### II.1 The honest truth a physical switch cannot exist in-process

CO-00 begins from a refusal to lie. A **physical** kill switch — a mechanism that
prevents the model from reasoning past 60% *during a turn* — **does not exist and
cannot be built inside Claude Code.** A PreToolUse or Stop hook runs *around* tool
calls and turn boundaries; it can snapshot, it can inject advisory text, it can
debounce, but it cannot suspend the model mid-generation, and it cannot revoke context
that is already in the window. Any dataset claiming an "absolute, no-override, physical"
in-turn ceiling would be theater, and theater violates the Reality Contract that
governs every PP deliverable.

So CO-00 classifies every enforcement surface by the guarantee it can *actually*
provide, and then — per the Owner's 2026-06-30 decision — **pushes the one surface that
can truly block as hard as it will go.**

### II.2 The guarantee ladder (honest, five rungs)

| Rung | Surface | What it can genuinely guarantee for the 60% ceiling |
|---|---|---|
| 1 | **Prompt-only** | Nothing enforceable. Advisory text in CLAUDE.md / a prompt. Aspiration; relies entirely on the model and Owner. |
| 2 | **Claude Code hook (in-process)** | Detect + project + WARN. A Stop / PreToolUse / UserPromptSubmit hook can read the effective-context signal, run the projection, inject a hard-worded advisory and a staged checkpoint, and debounce. It **cannot block a turn already running** and cannot revoke context. Detection and projection are reliable; the *response* is advisory. |
| 3 | **Wrapper (kclaude, out-of-process, pre-launch)** | **Refuse to launch.** This is the only surface that can truly *block*. Between turns and between sessions/loops, the kclaude wrapper runs before claude.exe is (re)launched and before a `/loop` or swarm begins; it can decline to start an operation whose conservative projection breaches the ceiling. The block is real because it happens *outside* the model's turn, at a boundary the wrapper owns. |
| 4 | **Cursor extension** | Surface state, dedup on cold-start. Visualization and reload-dedup only; no compute veto. |
| 5 | **Host-limited** | The Windows/Cursor/Claude-Code internals the PP cannot reach. Documented as out of scope, never pretended-resolved. |

The ceiling, therefore, is a **layered guarantee**: rung 2 detects and warns inside the
turn; rung 3 blocks at every launch boundary; rung 1 and rung 4 inform; rung 5 is named
honestly as the residual the Owner's discipline must cover. CO-10 (Enforcement
Guarantee Ledger) generalizes this ladder across the whole kernel; CO-00 instantiates
it for the budget specifically.

### II.3 The wrapper-maximal block (the approved investment)

Per the Owner's decision — *push wrapper enforcement harder* — rung 3 is where CO-00
concentrates its real teeth. The contract for the wrapper surface (`modules/wrapper/`
prelaunch family, the kclaude launcher) is expanded from *advisory* to *gatekeeping* at
every boundary it owns:

- **Session launch/resume.** Before kclaude launches or `--resume`s a session, it
  estimates the resumed session's starting effective context (from the transcript it is
  about to reload). If resuming would *start* a session already in RED, the wrapper
  refuses the bare resume and instead offers only recovery-class entry: resume-after-
  `/compact`, resume-into-a-hibernated-snapshot (CO-07), or a fresh session that
  inherits a checkpoint. A session is never *born* over the ceiling.
- **`/loop` admission.** A loop is the highest-risk context grower because it
  compounds. The wrapper (and, where the loop is launched in-process, the hook at rung
  2) refuses to *start* a loop whose projected trajectory — starting context + per-
  iteration growth × iteration cap — breaches 60% before the iteration cap is reached.
  A loop that cannot prove it stays under the ceiling for its declared iteration budget
  is not admitted; it must be re-scoped, given a lower iteration cap, or restructured to
  checkpoint-and-hibernate between iterations (CO-09 defines the loop budget contract
  that feeds this projection).
- **Subagent swarm admission.** A parallel swarm's aggregate context pressure is
  projected before dispatch; a swarm whose width × per-agent footprint would breach the
  ceiling for the parent session is capped or staggered (CO-09 subagent economics).
- **Parallel session admission.** This is the literal root cause of the 48h burn —
  multiple hot panes on the same repo. CO-08 defines the hard hot-session cap; CO-00's
  contribution is that the *budget* projection is what the scheduler consults: a new hot
  session is refused at the wrapper boundary when the aggregate projected context/compute
  across already-hot sessions plus the new one breaches the global envelope.

The honest boundary: the wrapper can only block at a *launch boundary*. It cannot stop a
session that is already running from growing past 60% mid-turn — that residual is rung 2
(advisory) plus the breach-incident protocol of Part III. CO-00 does not pretend
otherwise. What it guarantees is that **no operation is ever admitted whose conservative
projection breaches the ceiling**, and that every breach that nonetheless occurs is
treated as an incident, not a normal event.

### II.4 No override, and what "no override" honestly means

The contract says no manual override, no "solo esta vez". Honestly scoped, this means:
the wrapper's launch-refusal has **no bypass flag**. There is deliberately no
`--ignore-budget` argument, because a bypass that exists will be used under pressure and
the ceiling will erode. The only path past a refusal is to *change the projection's
inputs* — reduce the loop's iteration cap, hibernate another session to free the global
envelope, `/compact` the session being resumed — i.e., to make the operation actually
fit, not to pretend it fits. This is the strongest honest form of "no override": the
gate cannot be told to look away; it can only be satisfied.

---

## Part III — Breach as Incident: RCA, Observability, Failure Modes, Rollback, Integration

### III.1 A breach is a production incident, not a warning

If effective context exceeds 60%, CO-00 has *already failed* — the projection should
have prevented admission of whatever grew the context. Therefore a breach is not logged
as a routine threshold event; it triggers a **mandatory Root Cause Analysis**. The RCA
must answer: which operation grew the context past the line; why did its pre-admission
projection under-estimate; was the projection skipped (a wiring gap) or wrong (a
calibration gap); and what calibration or gate change prevents the recurrence. The RCA
artifact is durable (a `vault/` incident record) and feeds CO-01's calibration data so
the projection improves. A breach with no RCA is itself a second defect — silent breach
is the worst outcome because it normalizes the ceiling's erosion.

### III.2 Observability — what is measured and where it is exposed

CO-00 is only as real as its visibility. The contract requires, at all times, a single
authoritative read of: current effective-context estimate (with the band: GREEN/AMBER/
RED/BREACH), the inputs that produced it (jsonl size, turn count, statusline %, RAM) so
a stale sensor is visible, the most recent admission decisions (what was admitted vs
refused and the projection behind each), and the breach ledger (count, last breach, open
RCAs). These surface through the existing statusline HUD (the context segment already
rendered by `gsd-statusline.js`), the wrapper's pre-launch advisory output, and a CO-00
state file consumed by CO-10's ledger. The principle (inherited from SCS C53 TCO
visibility): the number is read from ground truth (transcripts + the host bridge),
never estimated optimistically; missing measurement is reported as *unknown*, never as
*fine*.

### III.3 Failure modes and detection

- **Stale or missing context signal.** The statusline bridge file is absent or old →
  the effective-context estimate falls back to jsonl-size + turn-count bands, and the
  ambiguity is surfaced (not silently treated as GREEN). Detection: cross-sensor
  disagreement beyond a tolerance.
- **Projection under-estimates (calibration drift).** An operation class systematically
  grows context more than projected → breaches cluster on that class → the RCA ledger
  surfaces the pattern → CO-01 re-calibrates. Detection: breach-to-class correlation.
- **Wrapper bypassed.** A session launched outside kclaude (bare `claude`) escapes rung
  3 entirely → only rung 2 advisory protects it. Detection: sessions whose launch has no
  wrapper pre-launch record; CO-10 flags the un-gated launch path honestly rather than
  claiming coverage it lacks.
- **Fail-open vs fail-closed tension.** Every PP guard is fail-open (an error never
  breaks a working setup). But a fail-open *budget gate* that errors would admit an
  over-ceiling operation. CO-00 resolves this honestly: the *projection* fails open (an
  un-projectable operation is not blocked, but is loudly flagged and the breach ledger
  watches it), while the *measurement* never fabricates a healthy reading. The contract
  never trades a broken session for a defended ceiling — but it makes every fail-open
  admission visible so the residual risk is owned, not hidden.

### III.4 Rollback protocol

If CO-00's enforcement itself misbehaves — e.g. the wrapper gate refuses legitimate
operations because of a mis-calibrated projection (false-positive starvation) — the
rollback is staged and non-destructive: (1) demote rung 3 from *gatekeeping* back to
*advisory* (the wrapper warns but admits), restoring pre-CO-00 behavior while keeping
visibility; (2) the projection calibration reverts to its last-good parameters from the
CO-01 ledger; (3) the action bands widen toward the ceiling temporarily to reduce
false positives while the calibration is fixed. Because rung 2 (hook advisory) and the
breach ledger remain active throughout, rolling back the *block* never blinds the
*detection*. Full removal is a single switch (disable the wrapper budget gate) that
returns the system to the SCS C59 advisory baseline — no data migration, no orphaned
state.

### III.5 Integration contract (mandatory, explicit)

- **`/compact`** — the primary in-turn recovery when RED is reached or a breach occurs.
  CO-00 stages the recommendation; the existing BL-0003 rule (no auto-firing slash
  commands) holds, so the kernel advises and the Owner/▸ fires it. CO-06 (GC) decides
  *what* `/compact` should prioritize.
- **`/kclear`** — the harder reset when `/compact` is insufficient (RAM-correlated
  pressure, very large jsonl). CO-00 routes to `/kclear` via the existing
  `auto_reset_orchestrator` mapping, with a CO-07 hibernation checkpoint written first
  so nothing is lost.
- **`/clear`** — task-boundary reset; CO-00 treats a `/clear` as a budget reset event
  (effective context returns to ~baseline) and clears the session's RED/BREACH state.
- **`/loop`** — admission-gated per II.3; the loop's own budget lives in CO-09.
- **Subagents** — swarm width gated per II.3; per-agent budget in CO-09.
- **Cursor / parallel sessions** — the global envelope across hot panes is the
  scheduler's input (CO-08); CO-00 owns the projection it consults.
- **Knowledge Vault** — every breach RCA and every calibration update is a CO-05 asset,
  so the kernel learns from each incident exactly once.

### III.6 Anti-patterns (forbidden by this contract)

- **Defending the ceiling only at the ceiling.** Acting at 60% instead of projecting
  from the 45–55% band. The band exists precisely so the line is never the first line
  of defense.
- **A bypass flag.** Any `--ignore-budget`/"just this once" override. Forbidden; the
  gate can only be *satisfied*, not silenced (II.4).
- **Optimistic measurement.** Reporting GREEN when the signal is stale/missing.
  Unknown is reported as unknown.
- **Silent breach.** A breach without an RCA artifact. The breach ledger and mandatory
  RCA make every breach loud.
- **Claiming a physical in-turn switch.** Pretending rung 2 can block a running turn.
  The ladder is stated honestly or the contract is theater.
- **Fail-closed budget gate that breaks sessions.** A guard that, on its own error,
  refuses legitimate work. CO-00 fails open on projection while never fabricating a
  healthy measurement — it protects the session first and the number honestly.

---

### CO-00 verifiable contract (summary)

| Promise | Under what condition | What it never guarantees |
|---|---|---|
| No operation is admitted whose conservative projection breaches 60% effective context | At every wrapper-owned launch boundary (session/resume, /loop, swarm, parallel session) | It cannot stop an already-running turn from growing mid-generation — that residual is rung-2 advisory + breach RCA |
| Every breach triggers mandatory RCA + ledger entry | Always | — |
| Effective context is read from ground truth; unknown is reported as unknown | Always | It does not invent a healthy reading when sensors are stale |
| The block has no bypass flag; it can only be satisfied | At rung 3 | A bare `claude` launch outside kclaude escapes rung 3 (flagged by CO-10, not hidden) |
| Rollback demotes block→advisory without blinding detection | On enforcement misbehavior | — |

**Guarantee level (honest):** rung-2 *detect+project+advise* (in-turn) + rung-3
*launch-refusal* (between turns/loops/sessions, no override) + rung-1/4 inform + rung-5
named residual. **Not** a single physical in-turn switch — and the contract says so out
loud.

*CO-00 is the root. CO-01 supplies the cost ledger and calibration; CO-03 the router it
biases; CO-08 the parallel envelope; CO-09 the loop/subagent budgets; CO-10 the honest
ladder generalized. Sealed under SCS C61.*
