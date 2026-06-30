# Cognitive OS — CO-08 — Parallel Session Scheduler & Swarm Optimizer

> The direct systemic answer to the founding incident: **49.2M output tokens in 48 hours,
> driven by large prompts fired in parallel panes of the same repo.** CO-08 imposes a **hard
> cap on hot sessions** and schedules parallel work so concurrency multiplies *progress*, not
> *burn*. Where SCS C59 made the burn *visible* and `repo_coordinator` (W4) *advises*, CO-08
> *governs*.
>
> EXTEND, not NEW: `modules/wrapper/repo_coordinator.py` (W4) already detects a second same-repo
> pane (`coordinate()`) and the parallel-burn pattern (`parallel_burn()`) — but only as
> fail-open advisories that never block. CO-08 promotes those detectors into a scheduler with a
> real cap, using CO-07 hibernation as the tool that makes the cap non-destructive.

---

## Part I — The Hard Hot-Session Cap

### I.1 Why advisory was not enough

The Reality Scan was unambiguous: there is **no hard limit** on parallel hot sessions today —
`repo_coordinator` warns and offers resume, but the launch proceeds; `restore_guard.js` only
prevents reload-duplication. The 48h burn happened *despite* the advisory, because an advisory
is a suggestion and suggestions lose to momentum under pressure. The TCO doctrine already states
the rule the system did not enforce: *maximum 2 parallel active sessions; a third pane must
`/compact` the longest session first.* CO-08 turns that rule from documentation into a governed
cap.

### I.2 The cap and the global envelope

CO-08 governs two coupled limits:

- **A hard cap on hot sessions** — a maximum number of simultaneously *hot* (context-holding,
  actively-working) sessions. The default follows the existing TCO doctrine (2 active; a 3rd
  requires freeing one first), tunable but never unbounded. "Hot" is the operative word:
  hibernated sessions (CO-07) do not count — they hold no live context and no envelope. So the
  cap limits *concurrent live burn*, not the *number of projects in flight*.
- **The global compute/context envelope** (CO-00 + CO-02) — even under the count cap, the
  *aggregate* projected context and weekly burn across hot sessions must stay within the global
  envelope. Two hot sessions both firing ULTRA prompts can breach the weekly envelope while
  satisfying the count cap; CO-08 consults CO-02's summed envelope, not just the count.

Admission of a new hot session therefore requires *both*: under the count cap AND the aggregate
projection stays within the envelope. This is the property the 48h burn needed — a gate that sees
the *sum* across panes, not each pane in isolation.

### I.3 Cap enforcement is non-destructive (via hibernation)

A hard cap is only humane if hitting it does not lose work. CO-08's enforcement, when the cap is
reached and a new hot session is genuinely needed, is **not** "refuse the new session" (which
blocks the Owner) and **not** "kill an old one" (which loses work) — it is **hibernate the
lowest-priority hot session** (CO-07) to free a slot, then admit the new one. The displaced
session is preserved in a verified cold archive and restored on demand. This is what makes the
cap enforceable without friction: the Owner can always start the work they need; the kernel makes
room by parking the least-active session safely. Only when *nothing* can be hibernated (every hot
session is actively mid-operation and pinned) does CO-08 refuse — and like every kernel gate, the
refusal has no bypass, only satisfaction (finish or checkpoint a hot session to free a slot).

### I.4 The same-repo special case (the literal burn pattern)

The forensic's specific pattern — *multiple hot panes on the **same repo*** — gets special
handling, because it is the highest-waste form: same-repo panes re-derive overlapping context and
regenerate overlapping work, so their combined WU/MTok is far below the sum of their tokens. CO-08
treats a second hot session on a repo that already has one as a *strong* hibernate/serialize-or-
sequence signal: the default is to prefer one hot session per repo, with additional same-repo work
either sequenced (after the first checkpoints) or run as bounded subagents within the existing
session (CO-09) rather than as a second full hot pane. `repo_coordinator.coordinate()` already
detects the same-repo collision; CO-08 acts on it.

---

## Part II — The Swarm Optimizer and Scheduling

### II.1 Scheduling parallel work for progress, not burn

Concurrency is valuable when tasks are genuinely independent and each does distinct work; it is
ruinous when concurrent tasks overlap. CO-08's scheduler decides *what* runs concurrently by the
independence and ROI of the work, not by how many panes the Owner happened to open. The
scheduling primitives:

- **Independence check.** Two units of work are admitted to run concurrently only if they are
  genuinely independent (different repos, or non-overlapping scopes within a repo). Overlapping
  work is *sequenced*, not parallelized — sequential single-pane work with `/kclear` between
  features (the TCO rule) beats parallel same-repo panes on WU/MTok every time.
- **Priority and hibernation.** When demand exceeds the cap, the scheduler ranks hot sessions by
  priority (active vs idle, ROI, deadline) and hibernates the lowest to admit higher-value work.
- **Forward reservation.** A session that will need a large context block soon can reserve
  envelope (CO-01's futures primitive), so the scheduler does not admit intervening sessions that
  would starve it.

### II.2 The Swarm Optimizer (subagent fan-out)

A subagent swarm is parallelism *within* a session, and it carries the same multiply-the-burn risk
as parallel panes. CO-08's swarm optimizer governs fan-out width: the number of concurrent
subagents is capped by the aggregate projected context/compute they add to the parent (the
Windows parallel-subagent cap of 2 is the host-reliability floor; the economy cap may be lower
under envelope pressure). The optimizer also de-duplicates swarm work — N subagents researching
overlapping surfaces is the same waste as N parallel panes, so the optimizer prefers a smaller set
of non-overlapping agents (the multi-modal-sweep pattern: each agent searches a *different* way),
and it routes each subagent's model through CO-03 (exploration/test/doc agents → Haiku/Sonnet,
never Opus). CO-09 owns the per-subagent budget; CO-08 owns the *width* and *overlap* of the swarm.

### II.3 Why this is the systemic fix, not another advisory

The difference between CO-08 and SCS C59 is enforcement surface. SCS C59 added *awareness* (a
weekly-burn advisory). CO-08 adds *governance*: at the wrapper launch boundary, a new hot session
or a swarm that would breach the cap or the envelope is not admitted in its full form — it is
hibernated-into, sequenced, downgraded to subagents, or (last resort) refused. The honest limit
(CO-10): the wrapper governs *launch*; it cannot stop the Owner from manually opening a third
Cursor terminal outside kclaude. That manual case is surfaced loudly (an un-gated hot session is
flagged, its burn counted against the envelope, and the Owner advised) — not silently absorbed and
not falsely claimed as prevented.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **Cap starves legitimate parallel work.** Two genuinely-independent high-ROI tasks are blocked by
  a too-low cap. Detection: REFUSE verdicts on independent, high-projected-WU work → the cap or the
  independence check is too strict → tune (the cap optimizes WU/MTok, so a starving cap shows as
  *foregone* productive work, which is measurable).
- **Hibernation churn under the cap.** The cap thrashes sessions in and out as demand oscillates.
  Detection: freeze/restore churn (CO-07 III.1) → raise hysteresis (don't hibernate a session that
  was just restored).
- **Un-gated manual pane.** The Owner opens a third terminal outside kclaude → escapes the cap.
  Detection: a hot session with no wrapper pre-launch record (the same un-gated-path detector
  CO-02/CO-10 use) → flagged, counted, advised — never hidden.
- **Same-repo overlap misjudged.** Two scopes flagged as overlapping that are actually independent
  (or vice-versa). Detection: post-hoc WU/MTok — if "parallel same-repo" turns out high-ROI for a
  pattern, relax; if "independent" panes turn out to overlap and waste, tighten.

### III.2 Rollback protocol

CO-08 promotes advisories to enforcement; rollback demotes them back: (1) demote the scheduler from
*enforcing* (cap + envelope gate) to *advisory* (the W4 baseline — warn, offer resume, never block),
restoring exactly today's behavior; (2) disable swarm-width governance, reverting to the host
reliability cap (2 parallel) alone; (3) disable hibernation-to-free-a-slot, so the cap (if still
enforced) refuses rather than displaces. The fail-safe direction is *advisory, never blocking* — a
broken scheduler must not block the Owner's work; it reverts to warning. Because hibernation (CO-07)
is store-then-destroy, even an over-eager scheduler can never lose a displaced session.

### III.3 Integration contract

- **CO-00 / CO-02** — CO-08 consults the summed context/compute envelope; admission requires both the
  count cap and the aggregate projection under budget. This is the cross-session sum the 48h burn
  needed.
- **CO-07** — hibernation is the cap's enforcement tool: displace, don't refuse or kill.
- **CO-01** — scheduling and swarm decisions are ranked by Cognitive ROI; same-repo overlap is the
  canonical low-ROI pattern.
- **CO-03 / CO-09** — swarm subagents route their model through CO-03 and draw per-agent budgets from
  CO-09; CO-08 governs only width and overlap.
- **`/loop`** — a loop is single-session work; a *swarm of loops* is governed as fan-out. Parallel
  panes each running loops is the worst burn shape and the one CO-08 most strongly sequences.
- **`/kclear` `/compact`** — the TCO rule (`/kclear` between large features, `/compact` the longest
  session before a 3rd pane) is the manual expression of CO-08's policy; the scheduler automates it.
- **Cursor / repo_coordinator (W4) / Knowledge Vault** — CO-08 builds on W4's detectors and the pane
  map; burn-pattern clusters are stored as CO-05 assets so novel patterns are caught early.

### III.4 Anti-patterns (forbidden)

- **Unbounded hot sessions.** The exact precondition of the 48h burn. The cap is never disabled to
  "just get more done in parallel" — that is the anti-pattern, measurably (parallel same-repo burn).
- **Parallel same-repo panes for overlapping work.** Sequenced single-pane + `/kclear` wins on
  WU/MTok; same-repo parallelism is the canonical waste.
- **Killing a session to enforce the cap.** Enforcement is via non-destructive hibernation, never
  discard.
- **A bypass flag on the cap.** Forbidden; satisfied (free a slot), never silenced.
- **Silently absorbing an un-gated manual pane.** It is flagged, counted, and advised — coverage is
  reported honestly (CO-10).

---

### CO-08 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Enforces a hard hot-session cap (hibernated sessions don't count) at the wrapper launch boundary | kclaude-launched sessions | Coverage of a manually-opened terminal outside kclaude (flagged, counted, never hidden) |
| Admission requires BOTH the count cap AND the summed context/compute envelope under budget | Always | — |
| Cap enforcement displaces via CO-07 hibernation (non-destructive), refuses only when nothing can free | Always | A bypass flag; the cap is satisfied, never silenced |
| Same-repo second hot session is strongly sequenced/hibernated/sub-agented (the burn pattern) | Always | — |
| Swarm width capped by aggregate projection + host floor (2 on Windows); overlap de-duplicated | Always | — |
| Rollback demotes scheduler to W4 advisory without losing any displaced session | On misbehavior | — |

**Guarantee level (honest):** rung-3 wrapper enforcement (the cap blocks at launch) + rung-2
in-turn advisory + CO-07 non-destructive displacement. It governs every kclaude-launched session;
it cannot govern a manually-opened terminal (CO-10 flags that residual). This is the systemic fix
the 49.2M/48h burn demanded. *Sealed under SCS C61.*
