# Graphify — GK-11 — Librarian Swarm, Route Governor & Compression Contract

> The kernel's finders. When a task needs knowledge the graph can locate, an expensive reasoning
> agent should never be the one to go looking — a cheap, specialized *librarian* should locate it,
> compress it to a route, and hand it over. GK-11 is the agent family whose entire purpose is to
> **locate, filter, relate, and deliver the minimum knowledge in the smallest context** — never to
> reason deeply, never to write code, never to produce essays. Multiple librarians can propose; a
> Route Governor arbitrates their proposals into one minimal route. The Swarm exists so that costly
> agents inherit a compiled route instead of exploring.
>
> EXTEND, not NEW substrate: librarians ride the coordinate system (GK-01), the query runtime
> (GK-05), and the route compiler (GK-06) — they are *specialized query agents*, not a new locator.
> They extend the Explore-agent pattern (read-only fan-out search) but invert its output: Explore
> returns excerpts/prose; a librarian returns a *compressed route*. Honest (CO-10): librarians are
> **datasets/architecture now; live `~/.claude/agents/graphify-*.md` are a deferred EXECUTION-mode
> build** (agent files cold-load, need `/restart`). A librarian that consumes more context than it
> saves is a net loss — the Swarm's cardinal, measured sin (GK-09).

---

## Part I — The Swarm and Its Discipline

### I.1 Specialization without overlap

The Swarm divides knowledge by *type*, so no two librarians investigate the same thing. A **Repo
Librarian** finds code resources (which module governs this, which entrypoint starts this flow, what
must not be touched). A **Dataset Librarian** navigates architecture text (parent systems, contracts,
superseded datasets — preventing architectural duplication). A **Decision Librarian** recovers prior
rulings (why this was decided, what was rejected, what must not be re-litigated). A **Bug-History
Librarian** surfaces past failures (root causes, fixes, hot files, the trap to avoid). An **Asset
Librarian** finds reusable outputs. A **Workflow Librarian** finds how-to (commands, done-gates,
recovery flows). A **UKDL Librarian** delivers rules/traps/standards. A **Cross-Repo Librarian**
connects equivalent knowledge across projects (GK-10). A **Video/Multimodal Librarian** locates media
engines and pipelines — the reference case for the Resource Locator. Each owns a domain; overlap is a
design defect, because two librarians on one question is the duplicate cognition the kernel forbids.

### I.2 The cardinal contract: locate, do not reason

Every librarian obeys one contract: **find, do not think deeply.** A librarian's job is to reduce a
question to a route, not to solve the problem. It does not reason through the task, write the code,
or produce analysis — it locates the coordinates, applies its domain filter, and returns the minimal
set. This is what makes librarians *cheap*: they run on a cheap model (Haiku/Sonnet per CO-03), do
one pass, and return compressed output. A librarian that starts reasoning has become the expensive
agent it exists to prevent, and violates its contract. The discipline is enforced by measurement
(GK-09): a librarian whose output is large or whose context cost exceeds its savings is retuned or
retired.

### I.3 The Output Compression Contract

A librarian's output is tightly bounded by format: a **route** (the coordinates), **minimal
evidence** (why these, not an essay), **risks/traps**, **applicable contracts**, and the **next
action**. It never returns full documentation, never duplicates content the caller could page from a
coordinate, never loads irrelevant context. If a librarian's output is long, it must *justify why* —
the default is terse. This contract is the Swarm's reason for existing: the point of a librarian is to
*shrink* what the expensive agent must load, so a verbose librarian is self-defeating. Compression is
not a nicety here; it is the entire value proposition.

---

## Part II — The Council, the Governor, and Confidence

### II.1 The Autonomous Librarian Council

For a complex task, several librarians may each hold part of the answer, and they propose in parallel
— but must not flood the context. The Council is the structured competition: each librarian returns
its candidate coordinates, its confidence, its minimal evidence, its load cost, and — critically —
*what should not be loaded* and *what can be reused*. The Council is not a merge of everything found;
it is a set of *competing minimal proposals*, each arguing that its coordinates are sufficient. The
discipline is that more librarians must not mean more context — it means more *options* for the
Governor to choose the cheapest sufficient one from.

### II.2 The Route Governor

The Governor is the arbiter that turns competing proposals into one route. It resolves the conflicts
the Council surfaces: duplicate coordinates across proposals, redundant paths, contradictory evidence,
excess context, stale nodes, weak relations. It selects the route with the best combination of
**precision, low context, freshness, evidence, ROI, and success probability** — and it produces a
*single* minimal route, not a union of proposals. The Governor is where the Swarm's parallelism is
reconciled back to minimality: many librarians find, one Governor decides, one route ships. Without
it, the Swarm would inflate context (every librarian's findings loaded); with it, the Swarm's breadth
becomes a cheaper, better single answer. The Governor is GK-06's route compiler consuming Council
proposals as its input.

### II.3 The Confidence Framework

Every librarian output carries explicit confidence, because Claude must not treat all routes as
equally reliable. A route is labeled **confirmed** (verified coordinates), **inferred** (relationship-
derived), **stale** (freshness-flagged), **host-limited** (points at something the PP cannot fully
see), **speculative**, or **requires-verification-before-execution**. The Governor propagates the
weakest link's confidence to the final route (GK-04/GK-06 discipline), and a low-confidence route is
delivered as a *lead to verify*, never as an authoritative answer. A librarian that hides its
uncertainty — returns an inferred route as confirmed — violates the framework; surfacing uncertainty
is mandatory.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **Net-negative librarian.** A librarian consumes more context than it saves. Detection: GK-09
  measures per-librarian context-cost vs savings; a net-negative librarian is retuned or retired. The
  Swarm's cardinal sin, caught by the number.
- **Reasoning drift.** A librarian starts solving instead of locating, ballooning output and cost.
  Detection: output length + model tier vs the compression contract; a librarian producing analysis
  is out of contract.
- **Council flood.** Every librarian's findings are loaded instead of the Governor's single route.
  Detection: context loaded vs the Governor's chosen route size; the delta is wasted breadth → the
  Governor's selection is tightened.
- **Overlap.** Two librarians investigate the same question. Detection: domain-boundary audit; a
  question answered by two librarians is a specialization defect → boundaries clarified.

### III.2 Rollback protocol

GK-11 is an agent family riding existing engines, so rollback removes agents, not capability. (1)
Disable the Swarm and route queries directly through GK-05/GK-06 (the runtime and compiler still
locate and route; only the specialized-agent layer is gone). (2) Reduce to a single general librarian
(the Explore-agent baseline) rather than the specialized Swarm. (3) Fully disabled, the kernel
navigates via the runtime without agents. Because live librarian `.md` files are a *deferred*
EXECUTION build, the rollback of the *dataset* is simply not shipping the agents — the architecture
stands, the live layer is opt-in. Fail-safe: "route through the runtime directly," never "let a
librarian reason."

### III.3 Integration contract

- **GK-01 / GK-05 / GK-06 (parents/substrate)** — librarians navigate coordinates via the query
  runtime and hand proposals to the Governor, which is the route compiler consuming Council input.
- **Explore-agent pattern (parent)** — read-only fan-out search, with output inverted from prose to a
  compressed route.
- **CO-03** — each librarian is routed to a cheap model (Haiku/Sonnet); a librarian on Opus is the
  HR-COST-001 violation.
- **GK-04** — librarians travel typed edges; confidence propagates through the Governor.
- **GK-09** — every librarian's hit rate, context cost, precision, and ROI is measured; net-negative
  ones are retired.
- **GK-10** — the Cross-Repo Librarian is the propagation engine's finder counterpart.
- **Windows subagent doctrine** — live Swarm dispatch respects the cap-2-parallel-agents rule; the
  deferred agent files carry the Bash-avoidance directive.

### III.4 Anti-patterns (forbidden)

- **A librarian that reasons deeply.** It exists to locate, not solve; reasoning is the expensive
  agent it prevents.
- **A librarian that consumes more than it saves.** The cardinal sin, measured and retired.
- **Loading every Council proposal.** The Governor ships one minimal route, not a union.
- **Hiding uncertainty.** Confidence is explicit; an inferred route labeled confirmed is a violation.
- **Overlapping domains.** Two librarians on one question is duplicate cognition.

---

### GK-11 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Specialized librarians locate knowledge by domain and return a compressed route, not prose | Query has a domain owner | Locating knowledge the graph has not mapped (falls through to exploration) |
| The Route Governor arbitrates competing proposals into one minimal route | Council proposals available | A route smaller than the task's true need — sufficiency preserved |
| Every route carries explicit confidence; low-confidence routes are labeled verify-first | Always | That a librarian route is always correct — inferred routes are leads |
| A net-negative librarian (cost > savings) is measured and retired | GK-09 active | — |
| Rollback removes agents, not capability — the runtime/compiler still navigate | On misbehavior | — |

**Guarantee level (honest):** GK-11 is an *agent-family* layer (level-2 class; architecture now,
live agents deferred) — specialized cheap finders that compress knowledge to a route so expensive
agents never explore, arbitrated to a single minimal answer and measured against the locate-not-
reason / never-consume-more-than-you-save contract. Parents: **GK-05/06 + Explore pattern**.
*Sealed under SCS C69.*
