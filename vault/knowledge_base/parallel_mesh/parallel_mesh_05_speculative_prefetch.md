# Parallel Mesh — PM-05 — Speculative Prefetch Engine

> The mesh's one *forward-looking* dataset. PM-01 through PM-04 remove duplication from work
> already happening; PM-05 removes *latency and cost* from work about to happen, by preparing
> the cheap assets a pane will predictably need **before** it needs them — during idle envelope,
> with cheap models — so the expensive moment is served from a warm asset instead of a cold
> derivation. When a pane declares intent to touch a subsystem (PM-02), its index, its
> dependency map, and its recent-findings slice can be built speculatively so that by the time
> the pane reasons, orientation is already in the Warm tier.
>
> The most honestly-bounded dataset in the family (CO-10). Speculation is *prediction*, and
> prediction is wrong sometimes — so PM-05 is governed by three hard constraints that make a
> wrong guess harmless: **cheap-only** (never speculate with Opus, only deterministic/Haiku
> work), **idle-only** (only in the Green concurrency mode, never under envelope pressure), and
> **net-positive** (the engine tracks its own hit rate and disables any prefetch class that
> costs more than it saves). EXTEND, not NEW: prefetched artifacts are speculative occupants of
> **CO-04's Warm tier** and provisional **CO-05 assets**; PM-05 adds only the *when* and the
> *what-to-guess*.

---

## Part I — Speculation Under Hard Constraints

### I.1 What is safe to prefetch

Only cheap, reusable, verifiable artifacts — never reasoning. The prefetchable set is exactly the
class CO-03 already routes to its deterministic and cheap-model rungs: file/symbol **indexes**,
**dependency maps**, **grep/glob results** over a declared scope, **source summaries** (the
DNA-3000 audit-cache pattern), and the **Findings-Bus slice** relevant to a declared subsystem.
These share three properties: they are cheap to build (deterministic or Haiku, not Opus), they
are reusable (many downstream steps consume them), and they are verifiable against a freshness
anchor (so a stale prefetch is detectable, not silently trusted). Anything expensive, one-shot, or
requiring model reasoning is **not** prefetchable — speculating on it risks spending Opus tokens on
a guess, the exact anti-economy the kernel exists to prevent.

### I.2 The three constraints that make a wrong guess harmless

- **Cheap-only.** Prefetch runs on CO-03's deterministic / Haiku rungs. A missed prediction wastes
  a few cheap tokens, never expensive ones. This bounds the *downside* of every wrong guess to
  near-zero by construction.
- **Idle-only.** Prefetch runs **only in PM-04's Green mode** — when aggregate envelope pressure is
  low and the cheap compute is genuinely spare. Under Yellow/Red/Black, prefetch is suspended
  entirely: speculation never competes with real work for a contended envelope. This is the
  difference between using idle capacity and stealing needed capacity.
- **Net-positive.** The engine tracks, per prefetch *class*, its hit rate (prefetched-and-used vs
  prefetched-and-discarded) and its cost-vs-savings. A class whose speculation costs more than it
  saves is **auto-disabled** — the engine is self-limiting, not perpetually optimistic. A prefetch
  strategy that does not pay for itself is switched off, measurably.

### I.3 What informs the prediction

Prediction is driven by *declared* and *observed* signal, not by guessing blind: a pane's intent
declaration (PM-02) names the scope it will touch — the strongest predictor; the Repo Shared Brain
(PM-01) names the active working set and plans; and historical access patterns (which assets a
similar task needed last time, a CO-05 record) refine it. The engine prefetches for the *declared
next scope*, not for an imagined future — so the prediction is grounded in a pane's own stated
intent, which makes the hit rate high enough to clear the net-positive gate on the classes that
matter.

---

## Part II — Placement, Freshness, and Discard

### II.1 Prefetched artifacts live in the Warm tier, provisionally

A prefetched artifact is placed in CO-04's Warm tier tagged **speculative** and carrying a
freshness anchor (HEAD + content hash, like every other mesh cache). When the predicted pane
actually reaches the moment, it consumes the warm artifact after the standard anchor check — fresh
→ zero-latency reuse; stale → re-derive (the prefetch became a miss, discarded). A speculative
artifact never *promotes* to a trusted CO-05 asset until it has been anchor-validated at point of
use; until then it is a convenience, not a fact. This keeps prefetch on the right side of the
primary-source-wins doctrine: a guess is a lead, verified before it is trusted.

### II.2 Discard is cheap and silent-safe

Because prefetch is cheap-only and idle-only, discarding a miss costs nothing beyond the small
cheap-compute already spent — there is no envelope harm to unwind, no state to roll back. CO-06's
garbage collector evicts unused speculative artifacts on a short timer (they are the lowest-
priority tier occupant by definition: unvalidated guesses). A prefetch that is never consumed
simply ages out. This is why PM-05 can be aggressive within its constraints: the failure mode of
over-prefetching is *bounded cheap waste*, self-corrected by the net-positive gate, not a burn.

### II.3 The net-positive ledger

The engine keeps a per-class ledger — for each prefetch class (index, depmap, grep, summary,
findings-slice), its prefetch count, hit count, spent tokens, and saved tokens. This ledger is the
engine's conscience: it is consulted before every speculation (a disabled class does not run) and
audited periodically (a class drifting toward net-negative is disabled and surfaced). The ledger
reuses CO-01's WU/MTok accounting — prefetch savings are counted in the same currency as all mesh
economics, so "was prefetch worth it" is answered in the kernel's one honest metric, not by
adjectives.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **Over-speculation (cost > savings).** A prefetch class guesses wrong more than it helps.
  Detection: the net-positive ledger flips negative for that class → auto-disable + surface. This
  is the primary designed-for failure, and the ledger is its detector.
- **Speculating with an expensive model.** A prefetch routes to Opus. Detection: prefetch is
  hard-pinned to CO-03's deterministic/Haiku rungs; an Opus prefetch is a routing bug, blocked at
  the router, never merely warned.
- **Prefetch under pressure.** Speculation runs in Yellow/Red/Black and steals needed envelope.
  Detection: the idle-only gate checks PM-04's mode before every prefetch; a prefetch in a non-
  Green mode is the bug, suspended on detection.
- **Stale prefetch consumed as fresh.** A warm speculative artifact is trusted without its anchor
  check. Detection: consumption runs the standard freshness verdict (PM-01/PM-03); a speculative
  artifact with no verdict is never promoted.

### III.2 Rollback protocol

PM-05 is the family's most trivially-reversible dataset — it is pure acceleration over a correct
lazy baseline. (1) Disable a single prefetch class (the net-positive gate does this automatically).
(2) Disable the engine entirely — the mesh reverts to **lazy-only**: every asset is built at point
of use, exactly as it is today, with zero behavior change beyond losing the warm-start latency
win. (3) Because prefetch never *replaces* verification (it only pre-warms a cache that is anchor-
checked at use), disabling it can never produce a wrong result — only a slightly colder start. The
fail-safe direction is **lazy derivation**, which is always correct; PM-05 is strictly optional
speed, never a correctness dependency.

### III.3 Integration contract

- **CO-04 (parent)** — prefetched artifacts are speculative Warm-tier occupants; CO-04 governs
  their placement and untrusted-until-verified status.
- **CO-05 (parent)** — a validated prefetch promotes to a CO-05 asset; the historical-access record
  informing prediction is a CO-05 pattern.
- **CO-03** — prefetch is pinned to the deterministic/Haiku rungs; an expensive prefetch is a
  routing violation.
- **CO-06** — evicts unused speculative artifacts on a short timer (lowest-priority tier occupant).
- **CO-01** — the net-positive ledger is denominated in WU/MTok.
- **PM-01 / PM-02** — predictions are driven by the Brain's working set and the pane's declared
  next scope; the strongest, best-grounded signal.
- **PM-04** — the idle-only constraint *is* Green-mode-only; PM-05 is the first thing suspended as
  pressure rises.
- **`/loop`** — a loop can prefetch the next iteration's cheap assets during the current iteration's
  idle envelope (a natural, well-grounded prediction). **`/kclaude`** — a launch can pre-warm the
  declared scope's index before the first turn. **`/compact` / `/kclear`** — speculative artifacts
  are the first evicted; they never survive a compaction as "important."

### III.4 Anti-patterns (forbidden)

- **Prefetching with an expensive model.** Cheap-only; an Opus guess is the anti-economy the kernel
  forbids.
- **Prefetching under envelope pressure.** Idle-only (Green); speculation never competes with real
  work.
- **Keeping a net-negative prefetch class alive.** The ledger auto-disables it; optimism is not a
  strategy.
- **Trusting a speculative artifact without its anchor check.** A guess is a lead; verify at use.
- **Treating prefetch as a correctness dependency.** It is pure acceleration over a correct lazy
  baseline; the lazy path must always remain the fallback.
- **Predicting blind.** Prefetch follows *declared* next scope and the Brain's working set, not an
  imagined future.

---

### PM-05 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Cheap, reusable, anchor-verifiable assets pre-warmed before a pane's predicted need | Green mode + a declared next scope | Prefetch of anything expensive or reasoning-based (forbidden by construction) |
| Every prefetch is cheap-only (deterministic/Haiku) and idle-only (Green mode) | Always | Speculation under Yellow/Red/Black pressure (suspended) |
| Net-positive gate auto-disables any prefetch class costing more than it saves | Always | That every guess hits — misses are bounded cheap waste, self-corrected |
| Speculative artifacts are untrusted-until-anchored; verified at point of use | Always | Trust of a stale speculative artifact |
| Rollback to lazy-only is always correct; prefetch is speed, never a correctness dependency | Any time | — |

**Guarantee level (honest):** rung-1/2 — prefetch is a HOOK/wrapper convenience that pre-warms a
cache; it is **strictly optional acceleration** over a correct lazy baseline, gated cheap-only,
idle-only, and net-positive. It holds the weakest guarantee in the family *by design* — a wrong
guess is bounded cheap waste, never a burn and never a wrong result. Parents: **CO-04 / CO-05**.
*Sealed under SCS C65.*
