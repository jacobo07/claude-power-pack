# Cognitive OS — CO-09 — Loop & Subagent Economics

> The two highest-risk context/compute growers in the kernel are **loops** (they compound) and
> **subagent swarms** (they multiply). **No `/loop` and no swarm starts without a budget: expected
> cost, expected context growth, a maximum iteration count, a checkpoint plan, stop gates, a kill
> switch, and a resume plan.** Each subagent carries its own budget, allowed model, context limit,
> escalation criterion, cancellation criterion, and ROI justification.
>
> NEW: the Reality Scan found `/loop` **unbounded** (no iteration max, no cost check, no kill switch)
> and subagents **ungoverned** (their transcripts are even *excluded* from burn analysis). CO-09 is
> the missing budget contract; it consumes CO-00 (admission), CO-01 (pricing), CO-03 (per-task model).

---

## Part I — The Loop Budget Contract

### I.1 Why loops are special

A loop is the only kernel operation whose cost is *unbounded by default*: each iteration adds
context and tokens, and without a cap the trajectory runs to the ceiling or the budget with no
natural stop. The Reality Scan confirmed `/loop` has no iteration max and no pre-launch cost check —
it is the single most dangerous primitive for the 60% ceiling because it compounds silently. CO-09
makes a loop *prove it stays bounded* before it is admitted.

### I.2 The seven-part loop budget (mandatory before admission)

No loop is admitted (at the wrapper/launch boundary, CO-00 II.3) without declaring:

1. **Expected cost** — the per-iteration cost vector × iteration cap, priced by CO-01. The loop must
   fit the operation/session budget (CO-02).
2. **Expected context growth** — the per-iteration effective-context delta × iterations, projected
   against the 60% ceiling (CO-00). A loop whose trajectory breaches the ceiling before its cap is
   *not admitted in that form*.
3. **Maximum iterations** — a hard cap, declared up front. An uncapped loop is refused. The cap is
   the loop's most important parameter; it converts "run until something happens" into a bounded
   commitment.
4. **Checkpoint plan** — where the loop commits durable progress (so an interrupted loop is not
   wasted). A loop that grows context across iterations must checkpoint-and-demote (CO-04/CO-07)
   between iterations rather than accreting unbounded HOT.
5. **Stop gates** — the conditions under which the loop *should* stop early (success criterion met,
   no-progress detected, the loop-until-dry convergence). A loop without a success/convergence gate
   is a spin.
6. **Kill switch** — the condition under which the loop is *forcibly* terminated regardless of its
   own logic: cost exceeds 2× budget (HR-COST-002), context projection breaches the ceiling, or the
   2-consecutive-failures law trips. The kill switch is the loop's hard stop; it has no bypass.
7. **Resume plan** — how the loop's progress is recovered if it is killed or hibernated mid-run, so a
   stopped loop resumes from its last checkpoint rather than restarting.

### I.3 Honest enforcement of the loop budget

Per CO-00's ladder: a loop *launched* through the wrapper (or a `/loop` whose admission the kernel
gates) can be **refused at the start** if its declared budget breaches the ceiling/envelope — this is
real rung-3 enforcement. Once running, the kill switch operates at iteration boundaries (between
iterations, a hook/wrapper checkpoint evaluates the kill conditions) — this is the strongest in-loop
enforcement available, because each iteration is a boundary the kernel owns, unlike a single turn's
interior. CO-09 is honest that it cannot interrupt the *middle* of one iteration's generation; it
governs at iteration boundaries, which for a loop is frequent enough to be a real guarantee. A loop
that converts a bounded budget into runaway spend is the failure CO-09 exists to make impossible.

---

## Part II — Subagent Economics

### II.1 Each subagent is a budgeted economic actor

A subagent is a child operation with its own context window and cost. Ungoverned, a swarm multiplies
burn (CO-08 governs *width*; CO-09 governs *each agent*). Before dispatch, each subagent declares:

- **Budget** — its cost ceiling (priced by CO-01, bounded by the parent's envelope share). A subagent
  cannot spend more than its allocation; exceeding it trips its kill condition.
- **Allowed model** — chosen by CO-03's cascade for the subagent's task shape. The standing rule
  (TCO): exploration/test/doc/commit subagents use Haiku/Sonnet, never Opus; Opus is reserved for the
  parent's genuine architectural reasoning. A subagent on Opus for a grep is a budget hole (HR-COST-001).
- **Context limit** — its own share of the effective-context budget; a subagent that would itself
  breach a sub-ceiling is re-scoped or split.
- **Escalation criterion** — when the subagent may escalate its model (CO-03's escalation ladder), and
  the cap on that escalation.
- **Cancellation criterion** — when the subagent is killed: it exceeded budget, it is no longer needed
  (its result was superseded), or the parent's envelope tightened. Cancellation is clean (the
  subagent's partial work is checkpointed if useful, discarded if not).
- **ROI justification** — why this subagent earns its cost: the projected Work Units it contributes vs
  its budget. A subagent that cannot justify its ROI is not dispatched — the kernel prefers fewer,
  higher-ROI agents over a wide low-ROI swarm.

### II.2 Swarm composition (with CO-08)

CO-08 caps the *width* and de-duplicates overlap; CO-09 ensures *each* admitted agent is individually
budgeted and ROI-justified. Together they enforce the swarm patterns the PP already knows work:
multi-modal sweep (each agent searches a *different* way, no overlap), adversarial verify (N skeptics
only when the finding's value justifies N budgets), and the host reliability floor (≤2 parallel on
Windows). The anti-pattern — spinning up a wide swarm "to be thorough" without per-agent budgets — is
exactly the burn multiplier CO-09 forbids; thoroughness is scaled to the task's value (the
deep-research scaling rule), not maximized blindly.

### II.3 The subagent burn-analysis gap (a found defect)

The Reality Scan surfaced that `token_ground_truth` *excludes* subagent transcripts from burn analysis
("Skip subagent logs"). This means subagent spend is currently *invisible* to the economy. CO-09
closes this honestly: subagent cost is attributed to the parent operation's cost vector (CO-01), so a
swarm's burn appears in the parent session's ledger and counts against its budget (CO-02) and the
global envelope (CO-08). A swarm can no longer be a blind spot — its cost is the parent's cost.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **Runaway loop (kill switch fails to fire).** A loop exceeds budget/ceiling but the inter-iteration
  check did not trip. Detection: post-hoc, the loop's realized cost vs its declared cap → a kill-switch
  wiring gap → RCA (CO-00/CO-02 breach protocol). The declared cap is the backstop: even if a soft stop
  gate misfires, the hard iteration cap bounds the worst case.
- **Spin (no-progress loop).** A loop iterating without converging. Detection: the no-progress stop
  gate (loop-until-dry: K consecutive iterations with no new result → stop). A loop with no convergence
  gate is refused at admission.
- **Swarm overspend.** Subagents collectively exceed the parent envelope. Detection: the parent's cost
  vector (now including subagent attribution) crosses budget → CO-02 governs; new agent dispatch is
  refused/downgraded.
- **Orphan subagents.** A dispatched subagent whose parent died, still running. Detection: the
  cancellation criterion + the parent-liveness check; an orphaned agent is cancelled. (This also guards
  the Windows orphan-process hygiene the PP already enforces for dev servers.)
- **Subagent on the wrong model.** An expensive model on a cheap task. Prevention: CO-03 routes each
  subagent; detection: HR-COST-001 (Opus on a NANO subagent task).

### III.2 Rollback protocol

CO-09 is new governance over previously-ungoverned primitives; rollback returns them to ungoverned but
*visible*: (1) disable loop-budget *enforcement* (admission refusal) but keep the projection + the hard
iteration cap as an advisory + the kill switch on hard-budget-2× — i.e., the loop still cannot run
truly unbounded, but soft gating relaxes; (2) disable per-subagent budget enforcement but keep subagent
cost *attribution* (the found-defect fix stays — visibility is never rolled back); (3) revert swarm
width to CO-08's host floor alone. The fail-safe keeps the two things that must never regress: the hard
iteration cap (no truly-unbounded loop) and subagent cost visibility (no blind-spot burn).

### III.3 Integration contract

- **CO-00** — loop trajectory and swarm aggregate are projected against the ceiling at admission; the
  kill switch enforces at iteration boundaries.
- **CO-01 / CO-02** — loops and subagents are priced and budgeted; subagent cost attributes to the
  parent (closing the burn blind spot); over-budget loops/swarms are refused/downgraded.
- **CO-03** — each loop iteration and each subagent routes its model through the cascade; persistent
  escalation re-grades the starting model.
- **CO-04 / CO-07** — loops checkpoint-and-demote between iterations; a long loop can hibernate between
  iterations to free context; the resume plan uses CO-07 restore.
- **CO-08** — swarm width and overlap are CO-08's; per-agent budget is CO-09's; together they govern
  fan-out.
- **`/loop`** — this dataset *is* the `/loop` budget contract; `/loop` is admitted only with the
  seven-part budget declared.
- **Knowledge Vault / Cursor** — loop/swarm ROI outcomes are CO-05 assets, so the kernel learns which
  loop/swarm shapes are productive and which spin.

### III.4 Anti-patterns (forbidden)

- **An uncapped loop.** No maximum iterations declared. Refused at admission — the single most
  important loop rule.
- **A loop with no convergence/stop gate.** A spin waiting to happen.
- **A bypass on the kill switch.** Forbidden; the loop is bounded, not optionally-bounded.
- **A wide swarm without per-agent budgets/ROI.** "Be thorough" as an excuse for unbounded fan-out;
  thoroughness is scaled to value.
- **Opus on a cheap subagent.** HR-COST-001; subagents route through CO-03.
- **Invisible subagent spend.** Excluding subagent cost from the parent's ledger — the found defect,
  closed; never reopened.

---

### CO-09 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| No loop admitted without the 7-part budget (cost/growth/max-iter/checkpoint/stop/kill/resume) | At admission | It cannot interrupt the interior of a single iteration's generation — it governs at iteration boundaries |
| A hard iteration cap always bounds the worst case; the kill switch has no bypass | Always | — |
| Each subagent is budgeted, model-routed (CO-03), context-limited, ROI-justified, cancellable | Before dispatch | — |
| Subagent cost attributes to the parent's ledger — no blind-spot burn | Always | — |
| Rollback keeps the hard iteration cap + subagent cost visibility (never regress these) | On misbehavior | Soft-gating enforcement (relaxes to advisory) |

**Guarantee level (honest):** rung-3 admission refusal + iteration-boundary kill switch (frequent, real)
+ subagent cost attribution. It cannot halt one iteration's mid-generation, but a loop's boundaries are
frequent enough that the kill switch is a genuine guarantee, and the hard cap is the absolute backstop.
*Sealed under SCS C61.*
