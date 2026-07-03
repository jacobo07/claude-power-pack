# Graphify — GK-09 — Graph Navigation Observatory & Benchmark Suite

> The kernel's instruments. A navigation kernel makes a strong claim — "navigation is cheaper than
> exploration" — and that claim must be *measured*, not asserted. GK-09 is the single observability
> surface for the whole family: it reports what fraction of the workspace is represented, which zones
> are blind, which relations are missing, which queries fail, which routes save the most, which
> assets get reused, and which librarians earn their keep. It also holds the Benchmark Suite — the
> hard metrics that prove (or disprove) the kernel is paying for itself. If the graph is not
> measurably reducing context and time, GK-09 is where that failure becomes visible.
>
> EXTEND, not NEW: the ~8 "Observatories" the Owner named (Coverage / Freshness / Navigation / Route
> / Quality / Librarian / Query / Asset) are folded into **one** dataset — fragmenting them into eight
> would be the monolith-by-proliferation the kernel forbids. It reuses CO-01's Work-Unit / WU-per-MTok
> ROI discipline, the `session_resilience/telemetry.py` recording pattern, and `vault/benchmarks/
> ledger.json` as the durable metric store. Honest (CO-10): the observatory *measures and reports*;
> it enforces nothing (level-2). A metric it surfaces is a signal to the Owner and the learning
> engines, never an automatic gate.

---

## Part I — What the Observatory Watches

### I.1 Coverage and blind spots

The first question of any knowledge graph is *how much of the workspace does it actually know?* GK-09
reports **coverage** — the fraction of resources (across each node type: code, datasets, decisions,
bugs, assets) that have coordinates — and, more importantly, the **blind spots**: the zones with no
representation, the node types under-mapped, the repos not yet compiled. Coverage is reported per
region and per type, never as a single flattering number, because a graph that is 90% on code and 5%
on decisions is blind exactly where navigation matters most. Blind spots are the observatory's
highest-value output: they are the work-list for GK-03 (compile these) and the honest boundary of
what the kernel can currently navigate (GK-00's coverage-illusion guard).

### I.2 Freshness, integrity, and quality

The observatory surfaces the health GK-07 computes: what fraction of the graph is fresh vs
stale-soft vs stale-hard, how many broken bindings / contradictions / orphans exist, and which
regions are *declared unreliable*. It rolls these into a **quality score** per region — a composite of
freshness, evidence-backing, and integrity — so the Owner can see at a glance where the graph is
trustworthy and where it needs repair. A falling quality score in a region is an early warning of rot;
a region stuck at low quality is a repair target. Quality is reported honestly: a high score means
"navigable with confidence here," a low one means "verify before trusting," never a blanket "the graph
is healthy."

### I.3 Hot-spots and usage

The observatory tracks *how the graph is used*: which coordinates are most-navigated (hot-spots — the
most-connected, most-queried nodes, the natural entry points for a region), which are never touched
(candidates for GC or for missing edges that would surface them), which change most often (volatility
hot-spots feeding GK-07's freshness prediction), and a **heatmap** of navigation traffic across the
graph. Usage is what turns the graph from a static artifact into a living system with observable
behavior: it reveals the working structure of the ecosystem (what people actually navigate to) rather
than the declared structure (what the folders imply).

---

## Part II — The Benchmark Suite

### II.1 The metrics that matter

GK-09 measures the kernel against hard numbers, not vibes. The suite includes **Time To Correct Node**
and **Time To Correct Asset** (how fast navigation reaches the right resource), **Time To Useful
Context** (intent → loaded pack), **Context Reduction Ratio** (pack size vs the bulk read it
replaced), **Tokens Avoided** and **Files Avoided** (the exploration the graph prevented), **Reasoning
Eliminated** (conclusions reused vs re-derived, CO-05's payoff), **Graph Coverage**, **Knowledge
Reuse Rate**, **Navigation / Route Precision** (how often the returned coordinate/route was right),
**Query Success Rate**, **Cross-Repo Reuse**, **Asset Reuse**, and **Work Units per Graph Query** (the
CO-01 ROI unit applied to navigation). These are stored in `ledger.json` and trended, so the kernel's
value is a measured trajectory, not a one-time claim.

### II.2 The self-refutation guard

The benchmark suite exists in part to catch the kernel refuting itself. The whole thesis is that
navigation costs less than exploration; if **Context Reduction Ratio** ever goes the wrong way — a
route that loads *more* than the bulk read it replaced, a query answer larger than a direct grep, a
graph whose maintenance costs more tokens than it saves — that is a measured failure, surfaced loudly,
not buried. GK-00's compression invariant is enforced *here*, empirically: a component that inflates
context is caught by its own benchmark. This is the honest counterpart to the kernel's ambition — the
system is built to be disproven if it stops paying off.

### II.3 Route and query benchmarks

Beyond aggregate ROI, GK-09 benchmarks the navigation engines themselves: which route classes are too
large (feeding GK-06's learning), which queries reliably fail (feeding GK-05's planner and GK-08's
blind-spot writeback), which cached routes save the most (justifying their cache slot), and which
assets produce the most reuse (justifying their registry slot). These per-engine benchmarks are what
let the family *improve* rather than merely *run*: an engine's weakness shows up as a bad number, and
the number is the signal to tune it.

---

## Part III — Librarian & Failure Observability, Rollback, Integration, Anti-patterns

### III.1 Librarian performance

When the Librarian Swarm (GK-11) is active, GK-09 measures each librarian's value: its **hit rate**
(how often it returned a usable route), its **context cost** (a librarian that consumes more than it
saves is a net loss — the Swarm's cardinal sin), its **route precision**, and its **ROI**. A librarian
that reliably locates cheaply earns its dispatch; one that reliably over-returns or misses is retuned
or retired. This measurement is what keeps the Swarm honest to its contract ("locate, do not reason;
never consume more than you save") — the contract is enforced by the number, not by hope.

### III.2 Failure modes and detection

- **Vanity coverage.** A single high coverage number hides type/region blind spots. Detection: GK-09
  never reports one number — coverage is always per-type and per-region; a flat headline is the bug.
- **Metric without action.** Numbers are reported but never fed to the learners. Detection: each
  benchmark names its consumer (GK-05/06/07/08); a metric with no downstream is dead weight, pruned.
- **Observer cost.** The observatory itself consumes meaningful context/compute. Detection: GK-09's own
  cost is a tracked line; an observatory that is expensive to run violates the kernel's economy and is
  trimmed to the metrics that drive action.
- **Silent cap.** A benchmark samples or truncates and reports as if complete. Detection: any bounded
  measurement declares its bound (the "no silent caps" doctrine); a truncated metric that reads as
  total is the failure.

### III.3 Rollback protocol

GK-09 measures and never enforces, so rollback is pure de-scope. (1) Disable the learning-feed and
retain only the human-facing dashboard (visibility without auto-tuning). (2) Reduce to the core ROI
metrics (Context Reduction Ratio, Tokens Avoided, Coverage) if the full suite is expensive. (3) Fully
disabled, the kernel runs blind but unbroken — GK-09 gates nothing, so disabling it removes insight,
not function. Fail-safe: "measure less," never "assert a number you did not measure." Even disabled,
the last `ledger.json` snapshot persists as the honest record.

### III.4 Integration contract

- **CO-01 (parent)** — the Work-Unit / WU-per-MTok ROI discipline; navigation metrics are CO-01's ROI
  applied to finding-and-loading.
- **session_resilience/telemetry.py (pattern parent)** — the recording/telemetry pattern, repointed
  to graph navigation.
- **vault/benchmarks/ledger.json** — the durable metric store; trended over time.
- **GK-05 / GK-06 / GK-07 / GK-08 / GK-11** — every engine's performance is a benchmark here; every
  metric feeds a learner.
- **GK-00 / CO-10** — the compression invariant is enforced empirically here; the observatory is a
  measurement layer (level-2), honest about its bounds.

### III.5 Anti-patterns (forbidden)

- **A single flattering coverage number.** Coverage is per-type, per-region, with blind spots named.
- **Measuring without feeding a learner.** A metric that drives no tuning is dead weight.
- **An expensive observatory.** Instruments that cost more than the insight they yield violate the
  economy.
- **Silent truncation.** A sampled/bounded metric must declare its bound, never read as complete.
- **Asserting ROI without the ledger.** The kernel's value is a measured trajectory, not a claim.

---

### GK-09 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Reports coverage per-type and per-region with named blind spots | Always | A single completeness number — blind zones are always surfaced |
| Benchmarks the kernel's ROI (Context Reduction, Tokens/Files Avoided, Reasoning Eliminated, WU/query) into the ledger | Always | That the ratio is favorable — an unfavorable ratio is surfaced, not hidden |
| Every metric names a consumer (a learning engine or the Owner) | Always | Action from a metric on its own — GK-09 measures, does not enforce |
| Librarian value (hit rate, context cost, ROI) is measured; net-negative librarians are retired | Swarm active | — |
| Rollback de-scopes to core metrics / dashboard without breaking function | On misbehavior | — |

**Guarantee level (honest):** GK-09 is a *measurement/visibility* layer (level-2 class) — it makes
the kernel's value and health measured rather than asserted, enforces the compression invariant
empirically, and names its own bounds; it gates nothing and drives improvement only by feeding the
learners and the Owner. Parents: **CO-01 ROI + session_resilience telemetry + ledger.json**.
*Sealed under SCS C71.*
