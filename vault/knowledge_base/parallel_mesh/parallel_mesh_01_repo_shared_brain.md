# Parallel Mesh — PM-01 — Repo Shared Brain

> The mesh's central nervous system. The 48h burn was not caused by parallelism itself
> but by **each pane re-deriving the same repo context from zero**. PM-01 makes that
> derivation happen **once per repo** and be consumed by every pane, so N panes pay the
> context-building cost of one. The root law made concrete: *parallel allowed, duplicate
> cognition forbidden* — and the first, largest duplicated cognition is "understand this
> repo again."
>
> EXTEND, not NEW store: the Shared Brain is a **Warm-tier artifact of CO-04 (Context
> Virtual Memory)**, one per repo, with the freshness discipline of CO-05's asset
> registry. PM-01 does not invent a memory tier — it defines a specific, mesh-shared
> occupant of the tier CO-04 already governs. Honest from line one (CO-10): the Brain is a
> **file on disk polled at pane boundaries**, never shared memory between Claude instances.

---

## Part I — The Shared State Object

### I.1 What the Brain is, and what it replaces

A Repo Shared Brain is a single, versioned, live state document per active repo that every
pane reads **before** it reasons about that repo. It is the answer to a measurable waste:
today, a second pane opening the same repo reads the same CLAUDE.md, greps the same
modules, and reconstructs the same mental model the first pane already built — spending
thousands of tokens to arrive where another pane already stands. The Brain is that mental
model, externalized once and shared.

Its contents are exactly the expensive-to-rederive facts, and nothing that the code itself
already records cheaply:

- **Current briefing** — what this repo is, what is being worked on right now, the active goal.
- **Decisions taken** — Owner-locked answers and design rulings, so no pane re-litigates a
  settled choice (the sibling of the "check sibling commits before refactor" lesson).
- **Relevant files** — the working set for the current effort, so a new pane does not
  re-discover it by glob-and-grep.
- **Known risks and traps** — the repo's live hazard list (the bug-to-hard-rule surface,
  the traps a pane already paid to learn).
- **Active plans** — plans in flight and their owning pane, so work is not duplicated.
- **Recent findings** — a pointer into the Shared Findings Bus (PM-03), the hot layer of
  what other panes just discovered.

### I.2 Generated once, consumed by all

The defining property: the Brain is **generated once and read many times**. The first pane
to touch a repo in a work window (or a launch-boundary hook) builds the Brain; every
subsequent pane consumes the cached artifact rather than rebuilding it. This is the same
economy CO-05 provides for assets and the DNA-3000 audit-cache provides for source
summaries — the Brain is that pattern applied to *whole-repo situational awareness*. The
generation cost is paid by one pane; the read cost (a single file load, a Warm-tier
promotion under CO-04) is paid by each. For a repo touched by three panes in an hour, the
Brain converts three full context-buildings into one build plus two reads.

### I.3 The Brain is a cache, never the source of truth

A hard invariant inherited from the "plan code is a hypothesis — verify source first"
doctrine: the Brain is a **cache of understanding, not ground truth**. When a pane needs to
act on a specific file, function, or API named in the Brain, it verifies that premise
against the live source (HR-PREMISE-001) before writing code. The Brain accelerates
*orientation*; it never substitutes for *verification* on the specific artifact a pane is
about to change. A Brain that is trusted over the code is the Scaffold-Illusion failure
mode wearing a new hat, and PM-01 forbids it explicitly (III.4).

---

## Part II — Generation, Freshness, and Consumption

### II.1 Freshness is anchored, not assumed

A shared cache is only safe if staleness is *detectable*. The Brain carries freshness
anchors exactly as CO-05's registry does: the repo HEAD commit it was built against, a
content hash of the working-set files it summarizes, and a build timestamp. A consuming
pane compares those anchors to live state at read time. Three outcomes: **fresh** (anchors
match → consume directly, zero re-derivation); **stale-soft** (HEAD advanced but the
working set is untouched → consume with a surfaced advisory to refresh); **stale-hard**
(the summarized files changed → the Brain's summary of *those* files is not trusted; the
pane re-reads them and triggers a Brain refresh). There is no silent consumption of an
unvalidated Brain — the staleness verdict is always computed and always surfaced.

### II.2 Who writes, and the concurrent-writer problem

Because ≥2 panes share a repo, the Brain is a shared file with concurrent writers — the
exact hazard the CPC tab-count and pathspec-commit lessons were sealed on. PM-01's write
discipline: the Brain is **append-structured for volatile sections** (findings, decisions
accrue; they are not rewritten) and **single-writer-with-anchor for the summary sections**
(a refresh writes a new version tagged with its HEAD+hash; a racing refresh detects the
newer anchor and yields rather than clobbering). Refreshes are idempotent by anchor: two
panes refreshing against the same HEAD produce the same summary, so a race wastes at most
one redundant build, never corrupts state. This mirrors CO-07's store-then-destroy
durability rather than in-place mutation.

### II.3 Consumption at pane boundaries

The Brain is consumed at the honest coordination points — the only moments a
file-on-disk mesh *can* act: at **launch** (kclaude reads the Brain and injects the
briefing), at **turn-start** (a pane re-checks freshness and the Findings Bus before
reasoning), and at **close** (the pane commits its deltas back — decisions made, findings
published, traps learned — via the Cross-Pane Commit Protocol of PM-03). Between those
boundaries there is no live sync, and PM-01 never claims one. A pane that discovers
something mid-turn does not push it to other live panes; it writes it to the Brain/Bus,
and the next pane picks it up at *its* next boundary. This latency is stated, not hidden.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **Stale Brain consumed as fresh.** Anchors not checked → a pane acts on an outdated
  model. Detection: every consume logs the freshness verdict; a consume with no verdict is
  the bug. Protocol: block consumption until the anchor comparison runs (fail toward
  re-read, never toward trust).
- **Brain drift from reality.** The summary diverges from the code it describes. Detection:
  the content-hash anchor mismatches on the working-set files → stale-hard → forced
  re-read. The primary source (the code) always wins over the secondary artifact (the
  Brain), per the PR-VISUAL-01 primary-source doctrine.
- **Concurrent-writer clobber.** Two refreshes race. Detection: a version whose anchor is
  older than an already-written version → the older refresh yields; append sections never
  clobber by construction.
- **Brain bloat.** The Brain accretes stale decisions/findings and becomes its own token
  cost. Detection: Brain size vs consumption-tokens-saved; CO-06's garbage collector evicts
  aged findings and superseded decisions on the same recency/relevance policy it applies to
  memory tiers.

### III.2 Rollback protocol

PM-01 degrades to exactly today's behavior with no data loss. (1) Demote the Brain from
*consumed* to *advisory* — panes read it as a hint but always cold-read the repo, restoring
current per-pane context-building. (2) Disable shared writes — each pane keeps a private
scratch, no shared file. (3) Full disable — the mesh has no Brain and each pane operates
exactly as an ungoverned pane does now. The fail-safe direction is **cold-read, never
stale-trust**: a broken Brain must degrade to "ignore me and read the repo," never to
"trust my stale summary." Because volatile sections are append-only and summaries are
versioned-by-anchor, rollback never destroys a decision or finding already recorded.

### III.3 Integration contract

- **CO-04 (parent)** — the Brain is a Warm-tier occupant; CO-04 governs its load/demote
  discipline and marks it untrusted-until-verified for the specific-file case.
- **CO-05** — freshness anchors reuse the asset-registry pattern; a verified Brain summary
  is itself a reusable asset.
- **CO-06** — garbage-collects aged Brain sections (superseded decisions, stale findings).
- **PM-02 / PM-03** — the Brain records active plans (read by the Collision Detector) and
  points at the Findings Bus (the hot layer of "recent findings"); the Cross-Pane Commit
  Protocol writes deltas back.
- **`/kclaude`** — generates/refreshes the Brain at the launch boundary and injects the
  briefing; the primary honest coordination point.
- **`/compact`** — the Brain is external memory, so it *survives* compaction: a compacted
  pane re-reads the Brain to restore repo awareness without re-deriving it.
- **`/kclear`** — the Brain is **repo-scoped, not session-scoped**: a `/kclear` between
  features clears the session but the Brain persists, so the next feature starts oriented.
- **`/loop`** — a loop reads the Brain once at entry, not every iteration; iterating on the
  Brain is duplicate cognition inside a single pane.

### III.4 Anti-patterns (forbidden)

- **Trusting the Brain over the code.** It is a cache; specific-file actions verify against
  source (HR-PREMISE-001). The primary source always wins.
- **N panes each regenerating the Brain.** Defeats the entire purpose — generate once,
  consume many. A second concurrent build against the same HEAD is the waste PM-01 exists to
  kill.
- **Silent consumption without a freshness verdict.** Every consume computes and surfaces
  fresh / stale-soft / stale-hard.
- **In-place mutation of shared summary sections.** Versioned-by-anchor refresh only;
  in-place edits race and corrupt.
- **Claiming live pane-to-pane sync.** The Brain is disk polled at boundaries; the latency is
  stated (CO-10), never dressed up as shared memory.

---

### PM-01 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| One repo Brain built once, consumed by every pane before it reasons | Panes launched/refreshed through the mesh boundary | Coverage of a manual pane that never reads the Brain (flagged like CO-08's un-gated pane) |
| Every consume computes and surfaces a freshness verdict (fresh/stale-soft/stale-hard) | Always | Trust of a stale-hard summary — that forces a re-read |
| Concurrent refreshes are anchor-idempotent; append sections never clobber | Always | Perfect single-build under a race — at most one redundant build, never corruption |
| Specific-file actions verify against live source, not the Brain | Always | The Brain as source of truth (it is a cache) |
| Rollback degrades to per-pane cold-read with zero loss of recorded decisions/findings | On misbehavior | — |

**Guarantee level (honest):** rung-2/3 — the Brain is generated and injected at the kclaude
launch boundary (wrapper) and re-checked at turn-start (hook/prompt); it is a **shared file
on disk polled at pane boundaries**, not IPC. It governs panes that read it; a pane that
never reads it is flagged, not silently covered. Parent: **CO-04**. *Sealed under SCS C65.*
