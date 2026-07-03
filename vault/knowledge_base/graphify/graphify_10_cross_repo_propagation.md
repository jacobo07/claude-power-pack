# Graphify — GK-10 — Cross-Repo Knowledge Propagation & Merge

> The kernel's collective intelligence. Learning in one repo should reduce cost in all of them. Today
> each repo learns alone: a fix found in KobiiCraft, a pattern proven in TUA-X, a decision settled in
> InfinityOps stays trapped in its origin, and every other project re-discovers it. GK-10 makes the
> coordinate system *actually* global — it propagates coordinates, edges, decisions, and assets that
> have cross-repo value from their origin into the shared space, and it resolves the conflicts that
> arise when two repos know overlapping things differently. A conclusion reached once becomes an
> asset the whole ecosystem can navigate.
>
> EXTEND, not NEW-from-scratch: this is the deferred **PM-06 candidate** (Cross Project Learning
> Network) the Parallel Mesh index already scoped — EXTEND the vault, CEPS (the cross-project error
> pattern store), `cross_project_dedup`, and `cross_signal_bus`'s propagation transport. GK-01 already
> makes the address space global-native; GK-10 is the *movement* engine over it. Honest (CO-10):
> propagation moves **files/records between on-disk stores at boundaries**, and a propagated
> cross-repo link is **inferred** trust — a candidate for reuse requiring verification in the target
> repo, never an assertion that two repos' resources are identical.

---

## Part I — What Propagates, and Why

### I.1 The global vs local partition

Not everything belongs in the global space, and GK-10 draws the line the Owner named. **Global**
(cross-repo) knowledge: UKDL entries, SCS seals, architectural decisions, reusable assets, traps,
and patterns that recur across projects — the knowledge whose value is not tied to one repo's code.
**Local** (repo-scoped): files, modules, tests, and dependencies specific to one project — the
knowledge that only means something in its own tree. The partition is by *transportability*: a
coordinate propagates to the global space when its knowledge would help another repo, and stays
local when it would not. Mis-partitioning is a failure mode both ways — a local detail polluting the
global space is noise; a genuinely-reusable pattern trapped locally is the re-discovery cost GK-10
exists to kill.

### I.2 Promotion: local finding to global asset

When a session's writeback (GK-08) produces a finding with cross-repo value — a fix pattern, a
resolved decision, a benchmark result — GK-10 *promotes* it: the local coordinate is copied into the
global registry as a canonical, cross-repo asset (GK-02 canonicalization ensures it does not
fracture against an existing global identity for the same pattern). Promotion is evidence-gated: a
finding is promoted when it is verified locally *and* shows a signal of general applicability (it
matches a recurring cross-project pattern in CEPS, or an Owner marks it transportable). A one-off
local quirk is not promoted; a thrice-seen cross-project trap is. This is the compound-learnings
signal-threshold model applied across repos.

### I.3 The reuse dividend

The payoff of promotion is the reuse dividend: once a pattern is a global asset, every repo's
navigation can reach it. A new project inherits the ecosystem's accumulated traps before it hits
them; a session in one repo reuses a decision settled in another instead of re-litigating it; a fix
proven once is applied everywhere the pattern recurs. GK-09 measures this as Cross-Repo Reuse Rate —
the fraction of navigation that draws on knowledge originating in a *different* repo. The dividend
compounds: the more repos contribute, the richer the global space, the more every repo saves. This
is the "aprender en un repo reduce coste en todos" thesis made a measured mechanism.

---

## Part II — Propagation, Diff, Merge, Conflict

### II.1 The propagation transport

GK-10 reuses `cross_signal_bus`'s proven transport (file-drop + dedup cache + digest), repointed from
research signals to graph knowledge, and CEPS as the cross-project pattern substrate. Propagation is
a boundary operation, not a live sync: a promoted asset is written to the global store, and consuming
repos pick it up at their next navigation boundary (the same disk-polled discipline as PM-01/PM-03,
honestly stated). There is no claim of instantaneous cross-repo consistency — a promotion made now is
visible to another repo at *its* next boundary, and that latency is named, never dressed up as
real-time propagation.

### II.2 Diff and merge

Two repos often know overlapping things, and GK-10 must reconcile them without destroying either. A
**diff** identifies where a global asset and a repo's local knowledge disagree (a decision the global
space records one way and a repo applies another; a pattern that diverged). A **merge** reconciles
them — but along the honest lines the deferred-backlog D1 lesson (apex-completion-standard drift)
already taught: a blind copy in either direction destroys content (HR-006, "sync direction propagates
corruption byte-perfectly"). So GK-10 merges by *union with provenance* — both versions are retained
with their origin and evidence, and the conflict is surfaced for resolution rather than silently
overwritten. The global space is a multi-project accumulator; byte-identity is the wrong invariant
for it, and GK-10 never imposes it.

### II.3 Conflict resolution

When two repos assert genuinely contradictory knowledge — repo A says pattern X is safe, repo B
recorded it as a trap — GK-10 does not pick a winner by recency or arrival order. It records the
**contradiction** as a first-class state (like GK-07's contradictory-edge finding), attaches both
evidences, and surfaces it for Owner or verification resolution. A contradiction is information, not
an error to be silently smoothed: it often means the pattern is context-dependent (safe in A's
context, a trap in B's), which is itself knowledge worth a coordinate. The engine's discipline is to
*preserve the disagreement with its evidence* until it is genuinely resolved, never to launder it
into a false consensus.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **Over-promotion (global pollution).** Local quirks promoted to the global space, bloating it with
  non-transportable noise. Detection: global assets with zero cross-repo reuse over a long window are
  demoted/GC'd (CO-06); promotion is signal-gated. Bias toward under-promote.
- **Corrupting merge.** A blind directional sync destroys one repo's content. Prevention: union-with-
  provenance merge (the D1/HR-006 lesson); no in-place directional overwrite of a shared accumulator.
- **False cross-repo equivalence.** Two different patterns merged as one across repos. Detection:
  GK-02 canonicalization is evidence-gated and cross-repo links are inferred trust; a failed reuse
  flags the equivalence for split.
- **Stale global asset.** A promoted asset that went stale at its origin still served to other repos.
  Detection: the asset carries its origin freshness anchor (GK-07); a stale global asset is a lead
  requiring re-verification in the consuming repo.

### III.2 Rollback protocol

GK-10 extends deferred, un-built infrastructure, so its rollback is to *not propagate*. (1) Disable
promotion — knowledge stays repo-local (today's baseline, each repo learns alone), losing the reuse
dividend but nothing stored. (2) Make the global space read-only-advisory — repos may consult it but
are not gated on it. (3) Fully disabled, the vault + CEPS remain as the durable per-project layers, so
nothing durable is lost — only the *hot cross-repo layer* pauses. Fail-safe: "keep it local and let
each repo re-derive," never "propagate a corrupting merge or a stale global asset."

### III.3 Integration contract

- **PM-06 candidate (parent)** — the pre-scoped Cross Project Learning Network; GK-10 is its
  architecture. Reuses vault + CEPS + `cross_project_dedup` + `cross_signal_bus`.
- **GK-01 / GK-02** — the global-native address space and cross-repo canonicalization are what make
  propagation a lookup; GK-10 moves canonical identities, not files.
- **GK-08** — writeback produces the local findings GK-10 evaluates for promotion.
- **GK-07** — propagated assets carry origin freshness; contradictions are integrity findings.
- **GK-09** — Cross-Repo Reuse Rate measures the dividend; global-pollution shows as zero-reuse assets.
- **CO-05 / CO-06** — global assets are CO-05 institutional memory; CO-06 prunes non-transportable ones.

### III.4 Anti-patterns (forbidden)

- **Promoting local quirks.** Global pollution; promotion is signal-gated toward under-promote.
- **Blind directional merge.** The HR-006 corruption path; merge by union-with-provenance.
- **Picking a conflict winner by recency.** Preserve the disagreement with evidence; surface it.
- **Asserting cross-repo identity on name alone.** Cross-repo links are inferred, verification-gated.
- **Claiming real-time cross-repo sync.** Propagation is boundary-polled disk; the latency is named.

---

### GK-10 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Cross-repo-valuable knowledge is promoted to the global space; local stays local | Evidence of transportability (recurrence / Owner mark) | Promotion of a one-off local quirk (signal-gated, under-promote bias) |
| A repo can navigate knowledge originating in another repo (the reuse dividend) | Asset promoted + consuming repo at a boundary | Real-time cross-repo consistency — propagation is boundary-polled |
| Overlaps merge by union-with-provenance; contradictions are preserved with evidence, surfaced | Always | A silent directional overwrite (HR-006 corruption is forbidden) |
| Cross-repo links are inferred trust, verification-gated before an agent acts | Always | That a transported pattern is identical in the target context |
| Rollback de-scopes to repo-local learning with vault/CEPS intact | On misbehavior | — |

**Guarantee level (honest):** GK-10 is a *cross-repo propagation* layer (level-2/3 class,
boundary-polled) — it turns local learning into an ecosystem asset and reconciles overlap without
corruption; propagation is disk-at-boundaries not IPC, and a cross-repo link is an inferred reuse
candidate requiring verification, never an assertion of identity. Parent: **deferred PM-06
(vault + CEPS + cross_signal_bus)**. *Sealed under SCS C69.*
