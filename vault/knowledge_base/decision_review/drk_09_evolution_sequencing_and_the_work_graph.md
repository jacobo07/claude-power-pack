# DRK-09 — Evolution Sequencing & the Work Graph

> The dataset that governs **order**. DRK-00–08 decide whether a decision is sound and, since DRK-08,
> whether the option it chose among was a real set. Neither asks the question that determines whether
> a sound decision can be acted on at all: **what must land before this becomes possible, and what
> does landing it make unnecessary?** The estate ranks its work as a flat list, which is a shape that
> silently asserts the items are independent. They are not, and the relations a list discards are
> precisely the ones that decide sequence. **Parent it EXTENDs:** `modules/backlog_autopilot`
> (`what_now` is a sound ranker over a flat list; this changes its *input*, not its algorithm).
> **Cross-references (never re-narrated):** `owner_queue` + `stop_ledger` (escalation transport and
> STOP disposition), `ias_c2/opportunity_cost` (rank, forgo, settle), `capability_runtime/retirement`
> (retirement evaluation), `modules/liveness` (standing debt as a named set), `architecture_horizon`
> (the executable that already computes dependents and detects cycles).
>
> **Standing verdict this honours rather than reopens:** `gap-reverification-2026-08-03.md:62`,
> candidate E — *ALREADY_OWNED (as a ranker) / EXTEND (as a graph)*. The ranker is not rebuilt here,
> and this dataset exists only because the graph half of that verdict was never written.
>
> **Origin:** UPAC ownership audit 2026-08-18, system 24 (ASEG). Owner selected option D at STOP #1.

---

## PART I — WHY A LIST CANNOT SEQUENCE

### IX.1 The independence assumption

A ranked list carries a hidden claim: that each item's value can be assessed on its own, and that any
item may be started whenever it reaches the top. Both halves fail for real engineering work, and they
fail in a way that a better ranking function cannot repair, because the information needed is not in
the items — it is in the relations *between* them, and a list has no place to put a relation.

The visible symptom is the **perpetually-next item**: something ranks first, is selected, is found to
be blocked, is deferred, and ranks first again on the following pass. Its rank is stable because its
value is stable; nothing in the ranker can represent the reason it keeps not happening. The estate
reads this as a prioritization dispute and it is a data-model defect.

### IX.2 The four relations a list discards

| Relation | Meaning | What its absence causes |
|---|---|---|
| **Enables** | A must land before B is possible | B is scheduled, blocked, deferred, and re-ranked forever |
| **Invalidates** | A landing makes B unnecessary | B stays in the backlog at a stale rank, competing for attention it can no longer repay |
| **Shares substrate** | A and B touch the same surface | done separately, the surface cost is paid twice; done concurrently, they collide |
| **Competes** | A and B are alternative answers to one problem | both are built, which is the duplication this estate's base rate already predicts |

**Invalidates** is the relation whose absence is most expensive and least visible. A completed item
that removes the need for three queued items produces no signal at all in a list model: the three
remain, correctly ranked against a problem that no longer exists, and they will be worked eventually
because nothing ever told them to stop. Retirement is only possible if the relation that retires them
is recorded when it is known — at the moment A is planned, not discovered later by someone who
happens to notice.

**Competes** is the relation the estate has the most evidence for and the least tooling against. When
two entries answer the same problem, ranking them independently means the higher-ranked one is built
and the lower-ranked one waits, retaining its rank, and is eventually built too.

### IX.3 The recorded instance

This estate carries a sealed construction order: CRPF, then IGEF, then five extend passes, then a
further family deferred behind them. The order was dependency-derived and written down in prose,
with the reasoning stated — the first family supplies the measurement discipline the rest are scored
against, so building it last would mean the rest were built without an external bar.

Every predecessor in that chain was subsequently struck. The deferred family is still recorded as
deferred, waiting on items that no longer exist and will never land. Nothing detected this, because
the dependency was a sentence in a charter rather than an edge, and a sentence cannot notice that its
subject was retired.

That is the complete case for this dataset in one artifact: the estate is fully capable of deriving
correct dependency order, records it faithfully in prose, and has no mechanism that reacts when the
order's premises change.

---

## PART II — THE WORK GRAPH

### IX.4 Nodes, typed edges, and their scheduling consequences

A node is a unit of work with an identity stable across re-ranking. Edges are typed, and each type
has exactly one scheduling consequence.

| Edge | Direction | Scheduling consequence |
|---|---|---|
| **Enables** | A → B | B is not in the ready set while A is unlanded |
| **Invalidates** | A → B | on A landing, B transitions to retired, with the edge as its evidence |
| **Shares substrate** | A ↔ B | A and B are not *concurrently* ready; both may be individually ready |
| **Competes** | A ↔ B | at most one survives selection; the other is retired or explicitly deferred with a reason |

The edge types are deliberately few. A relation model rich enough to express every nuance of how work
relates is one nobody maintains, and an unmaintained graph is worse than a list, because a list at
least does not claim to know the order.

### IX.5 The ready set — the one change to the ranker

> **The ranker's correct input is the ready set, not the backlog.**

A node is ready when every enabling predecessor has landed. Ranking is then applied to the ready set
exactly as it is applied today: the same scoring, the same priorities, the same hard-rule bindings
that make an actionable high-priority item non-deferrable.

This is the whole integration, and its modesty is the point. `what_now` is not modified, not
re-tuned, and not second-guessed. A filter is placed in front of it. The perpetually-next item stops
surfacing not because its value was re-assessed but because it is no longer offered — and it appears,
correctly ranked, on the pass after its blocker lands.

### IX.6 The critical path

The longest chain of enabling edges is the critical path, and it changes how delay is priced. An item
off the path can be delayed by the length of its slack at no cost to the whole. An item on the path
delays everything downstream by exactly the delay it takes.

A ranker without this notion will schedule a high-value leaf ahead of a modest item on the path,
which is locally correct and globally wrong — the leaf's value is real, and the path's stall is
larger and invisible. **Position on the critical path is a scheduling input, not a value input**, and
conflating the two by folding it into the score would corrupt the ranking it is meant to inform.

### IX.7 Invalidates is a transition producer

When A lands, every node A invalidates transitions to retired, carrying the edge as its evidence and
the landing as its timestamp. This is not a priority adjustment. Deprioritizing an unnecessary item
leaves it in the queue at a low rank, where it will eventually rise as the queue drains.

The estate has already learned this shape from the other direction: a queue was found carrying a
status field that no producer could ever transition, so the field was a constant and the ledger it
fed reported a state that never changed. **A relation with no transition producer is decoration**, and
the invalidates edge exists specifically to be that producer for retirement.

---

## PART III — SEQUENCING UNDER THIS ESTATE'S CONSTRAINTS

### IX.8 Concurrency and the shared substrate

Two items may each be ready and still not be jointly schedulable. Where both touch the same
substrate, running them in parallel produces the conflict class this estate already governs at the
commit layer, and running them sequentially pays the substrate's setup cost twice.

The graph's contribution is limited and precise: it reports that two ready items share a substrate.
It does not decide the resulting policy — whether to serialize, to merge them into one unit, or to
accept the conflict risk — because that decision depends on the substrate and belongs to whoever owns
it. Reporting the condition is the part nothing currently does.

### IX.9 Blocked-by-external is a different queue

A node whose enabling predecessor is outside the estate's control — an Owner decision, an upstream
release, a third party — is not a backlog item. It is an escalation, and its home is the Owner queue
with its STOP disposition, not the ranked work list.

The distinction matters because unactionable items **dilute a ranking**. A backlog holding twenty
items nobody can start ranks them against the ones that can be started, and the resulting order is
a judgement about work that partly does not exist. The rule is a routing rule: an external blocker
moves the node out of the backlog and into the escalation surface, and it returns when the blocker
clears.

The estate has a live instance: twenty-three plans hold sealed identifiers awaiting a promotion
decision that is the Owner's to make. They are correctly parked as a decision, not carried as
schedulable work.

### IX.10 The debt view is a named set

Any standing-debt view over this graph is a **set of node names**, never a count and never a ratio.
This is a rule the estate has already paid for twice: a count falls by deleting a node, and a ratio
falls by adding a healthy one, so both can be satisfied without a single blocked item becoming
unblocked. Only names force the number down for the right reason.

---

## PART IV — GOVERNANCE, FAILURE MODES, CONTRACT

### IX.11 What this dataset does not own

It does not own the scoring function or the priority ladder — `backlog_autopilot` does, unchanged. It
does not own escalation transport or STOP disposition — `owner_queue` and `stop_ledger` do. It does
not own the comparison of value against forgone alternatives — that is the opportunity-cost owner. It
does not own retirement *evaluation*, only the retirement *trigger* the invalidates edge produces —
the contract evaluator decides whether a capability has outlived its purpose. It does not own the
reachability debt set. And it does not compute dependents or detect cycles itself; the architecture
horizon module already does both, and a second implementation would be a second source of truth for a
fact one of them would eventually get wrong.

It owns the relation layer, the ready-set filter, and the critical path.

### IX.12 A cycle is a specification defect

A cycle in the enabling relation means two items each wait on the other. This is never a scheduling
problem to be resolved by picking one; it is a statement that at least one of the two edges is wrong,
or that the units are drawn at the wrong granularity and should be one node.

It must fail loudly rather than degrade into an arbitrary order, because an arbitrary order will work
— one of them will be started, and the estate will conclude the dependency was soft. The cycle
detection already exists and is reused rather than reimplemented.

### IX.13 Failure modes

| # | Failure | Why it survives |
|---|---|---|
| 1 | **Perpetually-next item** | its rank is stable and correct; the blockage has no representation |
| 2 | **Unnecessary item worked** | it was correctly ranked against a problem that had quietly gone away |
| 3 | **Both competitors built** | each was independently justified, and nothing compared them to each other |
| 4 | **Critical path stalled behind a leaf** | the leaf's value is real and visible; the stall is neither |
| 5 | **Dependency recorded in prose** | it reads as documented, and it reacts to nothing |
| 6 | **Chain waiting on retired predecessors** | the deferral is faithfully recorded and permanently unsatisfiable |
| 7 | **Unactionable items diluting the ranking** | the queue looks full, and the order is partly about work nobody can start |
| 8 | **Cycle resolved by arbitrary choice** | it works, and the false conclusion is that the dependency was soft |
| 9 | **Debt reported as a count** | the number falls, and it falls by deletion |
| 10 | **Concurrent work on one substrate** | both items were ready, and readiness was the only condition checked |

### IX.14 Detection signatures

- An item selected and deferred on three or more consecutive passes with an unchanged rank.
- A deferred node whose enabling predecessor no longer exists in the graph.
- A dependency stated in a plan or charter with no corresponding edge.
- Two nodes with near-identical problem statements and no competes edge between them.
- A landed node with no invalidates edges evaluated on landing.
- A ranking pass whose input size equals the backlog size — the ready-set filter is not applied.
- A debt figure reported as a count or a percentage.
- Two concurrently-active units whose changes touch one surface.

### IX.15 Rule seeds

- **Rank the ready set, never the backlog.**
- **A dependency is an edge.** A dependency that exists only as prose is unrecorded, however clearly
  it is written.
- **On landing, evaluate the invalidates edges** and transition the nodes they point at.
- **An externally blocked node leaves the backlog** for the escalation surface, and returns when the
  blocker clears.
- **A cycle in the enabling relation fails loudly** and is never resolved by choosing.
- **Critical-path position informs scheduling and never enters the value score.**
- **Debt over this graph is a named set.**

### IX.16 Eval seeds

- Count items selected and deferred on three or more consecutive passes. That count is the
  perpetually-next population, and it should fall to near zero once the ready-set filter is applied —
  if it does not, the blockage is not a dependency and the model is wrong about the cause.
- For each landed item, count nodes retired by its invalidates edges. A sustained zero means the
  edges are not being authored, and an unauthored edge type is indistinguishable from an absent one.
- Compare completion order against critical-path order. Persistent divergence quantifies what leaf
  scheduling costs.
- Audit deferred nodes for predecessors that no longer exist. Any hit is the recorded instance of
  §IX.3 recurring, and its count is the direct measure of what prose dependencies cost.
- Re-run a historical ranking pass with and without the ready-set filter and compare the selected
  item. Where they never differ, this estate's work is genuinely independent and the graph should be
  withdrawn rather than maintained.

### IX.17 The fundamental property

> **Value decides what is worth doing; relations decide what can be done next, and only one of the two
> was ever modelled.** The work graph adds four edges and one filter: rank the ready set rather than
> the backlog, retire on landing rather than deprioritize, refuse a cycle rather than resolve it, and
> route an externally blocked item to the surface that can actually clear it. The ranker is untouched,
> because it was never wrong — it was answering the only question its input shape could pose. A
> dependency written in prose is a dependency the estate cannot react to, and the proof is already on
> record: a construction order whose every predecessor was struck, with the item behind it still
> faithfully waiting.
