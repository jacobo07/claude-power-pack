# Graphify — GK-12 — Graph-First Enforcement & Honest Guarantee Ledger

> The kernel's conscience and its enforcement edge. GK-00 declares the paradigm — navigate before you
> explore, one source of truth, coordinates not files. GK-12 is what makes that declaration *bite*
> and *stay honest*. It detects when a task explored without first consulting the graph (the
> Graph-First violation), it registers what every GK guarantee can *actually* promise, and it flags
> any claim that inflates beyond its real strength. The kernel must never pretend to enforce what it
> only advises, and it must never let an efficiency violation pass unmeasured. GK-12 is the dataset
> that keeps the whole family out of theater.
>
> EXTEND, not NEW: this is **CO-10 (Enforcement Guarantee Ledger)** applied to the navigation family —
> the same 5-level honesty ladder (prompt-only / in-process hook / wrapper / extension / host-limited)
> and the same un-gated-path detector, specialized for the graph-first surface. It reuses CO-10's
> ledger structure and the un-gated-path detection CO-02/CO-08 share. Honest by its own nature: the
> Graph-First rule is a **level-2 detect/project/warn plus a route-compiler redirect**, *not* a
> physical block — no in-process mechanism can stop a model mid-turn from choosing to grep, and GK-12
> is the dataset that says so out loud rather than claiming a switch it does not have.

---

## Part I — Graph-First Enforcement

### I.1 The rule and its honest level

The Graph-First rule: before any expensive knowledge operation — a `/loop`, a subagent dispatch, a
research pass, a deep analysis, a planner run, or a bulk read — the task must have consulted the graph
(a coordinate resolution, a query, a route compile). GK-12 states this rule's enforcement level
plainly, per CO-10: it is **level-2 (detect / project / warn) plus a level-3 redirect** — the route
compiler *offers* the cheaper path first, and a task that explores anyway is *detected and measured*,
not physically stopped. The strongest honest guarantee is "the cheap path is presented first, and the
expensive one is counted when taken." Any downstream doc that upgrades this to "graph-enforced" or
"exploration blocked" is inflating the claim, and GK-12's own audit flags it.

### I.2 Detecting the violation

A Graph-First violation is a task that began an expensive operation with *no preceding graph
consultation record*. GK-12 detects it the way CO-10 detects un-gated sessions: it cross-checks the
operation against the query/route log; an expensive exploration with no query record is flagged as a
violation. The violation is not blocked (honest level-2) — it is **attributed** (its burn counts
against the session, GK-09) and **surfaced** (an advisory: "this task explored without a graph query;
a route may have resolved it cheaper"). The point is to make the boundary of navigation *visible*, so
exploration-without-navigation is a known, measured residual rather than a silent inefficiency. Over
time, the trend is the pressure to close the gap by making navigation the path of least resistance.

### I.3 Redirect, not refusal

Where GK-12 *can* act at the moment of intent, it redirects rather than refuses: when a task is about
to explore, the kernel offers the compiled route first (GK-06), so the cheaper path is the default
choice, not a discipline the agent must remember. This is the level-3 surface — the route compiler
owning the pre-exploration boundary — analogous to the kclaude wrapper being the only surface that
truly gates in the CO family. But GK-12 is honest that this redirect only covers operations that
*flow through* the kernel; a task that issues a raw grep directly bypasses it (the un-gated path,
level-5 residual), and that residual is named and counted, never claimed as covered.

---

## Part II — The Guarantee Ledger

### II.1 Every GK mechanism, classified

GK-12 maintains a living ledger mapping each GK dataset's central guarantee to its honest level and
its residual — the navigation-family counterpart of CO-10's kernel ledger:

| GK mechanism | Level | Honestly guarantees | Residual (level-5) |
|---|---|---|---|
| GK-01 coordinate resolution | 2 | Stable identity + one-lookup resolution when mapped | An unmapped resource; a stale binding until rebound |
| GK-03 compiler | 2 | A navigable, compressed graph as fresh as its last scan | A resource created after the last scan |
| GK-04 edge registry | 2 | Typed, evidence-backed, confidence-graded relations | An edge whose evidence was never captured |
| GK-05 query / GK-06 route | 2 | Minimal coordinates/route when the graph holds the answer | A miss → falls through to exploration |
| GK-07 freshness/integrity | 2 | Scan-time staleness/defect verdicts; safe auto-repair | Real-time change; ambiguous repair (proposed) |
| GK-08 writeback | 2 | Verified discoveries structured into the graph at close | A silently-closed session |
| GK-10 cross-repo | 2/3 | Boundary-polled propagation of transportable knowledge | Real-time cross-repo consistency |
| GK-11 librarians | 2 | Compressed routes from cheap finders (agents deferred) | A manual expensive-agent exploration |
| **GK-12 graph-first** | **2 + redirect** | **Violations detected, attributed, surfaced; route offered first** | **A raw grep issued outside the kernel** |

The ledger is the single place the Owner reads *exactly* how strong each navigation guarantee is — the
opposite of marketing: it enumerates every residual the kernel cannot close so expectations match
reality.

### II.2 Anti-inflation audit

GK-12's central prohibition, inherited from CO-10: **no mechanism may claim a guarantee above its
registered level.** When a GK dataset's blockquote or contract asserts a strength, GK-12 audits it
against the ledger; an over-claim — "graph-enforced," "always current," "guaranteed minimal" for a
level-2 mechanism — is flagged as the theater path. Every new GK mechanism must declare its level and
residual to this ledger before it can claim enforcement, and a claim that exceeds its level is
flagged unverified. This is how the family stays honest as it grows: the ledger is the conscience that
prevents quiet guarantee-inflation across a dozen datasets.

### II.3 The single-source-of-truth invariant

GK-12 also enforces (at level-2) GK-00's architectural law: exactly one navigation system. It detects
a **shadow locator** — a code path that locates knowledge without consulting the coordinate system —
and surfaces it as a single-source-of-truth violation to be consolidated. It cannot *prevent* a tool
from writing its own grep-wrapper (that is a level-5 host residual), but it makes the divergence
*visible* so it can be folded back before it drifts into a second, disagreeing map. The invariant is
maintained by detection and consolidation pressure, honestly, not by a claimed block.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **Guarantee inflation.** A GK doc drifts to claim a stronger level than it has. Detection: the
  anti-inflation audit compares each claim to the ledger; an over-claim is flagged. The most important
  failure GK-12 prevents — the path back to theater.
- **Violation under-detection.** An expensive exploration is not flagged as graph-first-skipping.
  Detection: cross-check expensive operations against the query/route log; an operation with no record
  is a violation by definition.
- **Residual normalization.** A named residual (raw grep, manual agent) is quietly treated as "fine."
  Prevention: residuals are *measured* (the un-navigated burn is trended), so a growing residual is
  visible pressure, not an accepted loss.
- **Stale ledger.** A GK mechanism changes its guarantee but its ledger row does not. Detection: the
  ledger is regenerated from each mechanism's declared level; a mechanism with no current declaration
  is flagged unverified.

### III.2 Rollback protocol

GK-12 enforces nothing physically, so its rollback is pure de-scope. (1) Disable the graph-first
violation advisory — the detector still records for the ledger, it just stops nagging (visibility
retained). (2) Revert the ledger to a static document if the live audit misbehaves. (3) Fully
disabled, GK-12's classification persists as documentation, so the honest framing of every guarantee
survives. GK-12 never blocks any operation, so disabling it breaks nothing — it only removes the
honesty audit, which is itself the thing to keep, not to disable. Fail-safe: even fully off, the
paradigm's honest labeling remains.

### III.3 Integration contract

- **CO-10 (parent)** — the 5-level ladder, the un-gated-path detector, and the anti-inflation
  discipline, specialized for the navigation family; GK-12 is CO-10's method applied to GK-00..GK-11.
- **GK-00** — GK-12 holds the honest framing of the flagship "graph-first" claim against drift and
  enforces (at level-2) the single-source-of-truth law.
- **GK-05 / GK-06** — the route-compiler redirect is GK-12's level-3 surface; a query/route record is
  what proves a task was graph-first.
- **GK-09** — violation burn and residual trends are observatory metrics; the ledger's residuals are
  measured there.
- **Every GK dataset** — each declares its guarantee level + residual to GK-12; GK-12 audits and
  surfaces them, the cross-cutting relationship that makes it the family conscience.
- **`/loop` `/compact` `/kclear` / wrapper** — GK-12 classifies what each can and cannot guarantee, so
  the family's integration contracts are themselves honestly labeled.

### III.4 Anti-patterns (forbidden)

- **Claiming a guarantee above the mechanism's level.** "Graph-enforced" for a detect-and-redirect
  layer; the theater path, GK-12's central prohibition.
- **Silently absorbing a graph-first violation.** The residual is measured and surfaced, never hidden.
- **Treating a documented residual as resolved.** Naming a gap is not closing it; residuals are trended.
- **A new GK mechanism with no declared level.** Enforcement claims require a ledger registration.
- **Pretending host limits don't exist.** A raw grep and a manual agent are level-5, named honestly.

---

### GK-12 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Graph-first violations (explore without a preceding query) are detected, attributed, surfaced | Operation flows through the kernel | A physical block on a raw grep issued outside the kernel (level-5) |
| The route compiler is offered before exploration (the level-3 redirect) | Task routed through the kernel | Coverage of a task that bypasses the kernel entirely |
| Every GK guarantee is classified into an honest level with its residual; over-claims are flagged | Always; new mechanisms must register | Closing a residual — it names and measures it, not closes it |
| The single-source-of-truth law is enforced at level-2 (shadow locators surfaced) | Always | Prevention of a private grep-wrapper (level-5 residual) |
| Rollback de-scopes to documentation; GK-12 never blocks work | On misbehavior | — |

**Guarantee level (honest):** GK-12 is itself a *classification/visibility* layer (level-2 class) —
it enforces nothing physically; it makes the graph-first rule bite by detection-and-redirect,
measures the residual honestly, and keeps every GK guarantee from inflating past its real strength.
It is the dataset that guarantees the family tells the truth about what it guarantees. Parent:
**CO-10**. *Sealed under SCS C69.*
