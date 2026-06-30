# Cognitive OS — CO-06 — Cognitive Garbage Collector

> The kernel's hygiene engine. CO-04 provides the *mechanism* to move content between memory
> tiers; **CO-06 provides the policy — what to evict from HOT, when, and what to prune from the
> registry — so context stays minimal and the asset store stays clean.** It is the proactive
> counterpart to `/compact`: continuous, surgical eviction instead of an occasional blunt reset.
>
> EXTEND, not NEW: `modules/cpc_os/auto_reset_orchestrator.py` already decides, on pressure, to
> save work-state (M2) and advise `/compact`/`/kclear`. CO-06 generalizes that single reactive
> decision into a continuous aging/relevance policy that evicts *before* the blunt reset is needed.

---

## Part I — The Eviction Policy

### I.1 Why a GC, and why it is not /compact

`/compact` is stop-the-world garbage collection: it pauses, demotes the *entire* session to a
summary, and resumes — lossy, host-driven, all-or-nothing. A real garbage collector runs
*continuously* and evicts *selectively*: it reclaims the HOT context that is no longer part of the
working set while leaving the working set untouched. CO-06 is that collector. Its existence is what
lets CO-00 defend the 60% ceiling proactively — the kernel does not grow to the band and then
compact; it continuously reclaims dead context so the band is reached far less often, and when a
`/compact` *is* needed, CO-06 has already kept HOT lean so the compaction is cheaper and the
working set is clearly identified.

### I.2 The three eviction signals (recency, relevance, aging)

CO-06 scores every HOT item for eviction by composing three signals, none sufficient alone:

- **Recency (LRU).** When was this item last referenced by the active task? Content not touched in
  many turns is a strong eviction candidate. This is the classic cache signal and the cheapest to
  compute (the kernel knows what it just used).
- **Relevance.** Does this item belong to the *current* working set, or is it residue from a prior
  sub-task? A task that finished reading file A and moved to designing feature B no longer needs A's
  full content HOT — A demotes to WARM (a pointer), recoverable if B turns out to need it. Relevance
  is task-boundary-aware: a `/clear` or a task pivot is a strong demotion trigger for the old task's
  residue.
- **Aging.** How long has this been HOT, and at what depth? Old full-depth content that has not
  earned its place (no recent references, not in the working set) ages out to a summary or a pointer.
  Aging prevents the slow accretion of "loaded once, never evicted" content that is the mechanism of
  context bloat.

The composite score, evaluated as the action band (CO-00, 45–55%) approaches, ranks HOT content for
demotion. The kernel evicts lowest-value first, lossless (CO-04 guarantees paged-out content is in
WARM/COLD), until HOT is back to the working set. Eviction is *graduated*: at the AMBER band it
trims aggressively-stale residue; only deeper (RED) does it demote more aggressively.

### I.3 What is never evicted (pinning)

A garbage collector that evicts the working set is worse than none — it forces thrashing (CO-04
III.1). CO-06 therefore *pins* the current task's working set: the files, decisions, and context the
active task is provably using are exempt from eviction for the task's duration. Hard-rule-class
knowledge and the active todo/task state are likewise pinned. Pinning is the safety rail that makes
aggressive eviction safe: the kernel can reclaim freely *because* the things that matter right now
are protected. The pin set is exactly the working set CO-04 defines — the two datasets share this
boundary.

---

## Part II — Registry Hygiene and the Aging of Assets

### II.1 GC over the asset registry (CO-05)

CO-06 collects two heaps: live HOT context (Part I) and the durable asset registry (CO-05). The
registry needs hygiene too — over a long-running kernel, assets accrete, some never retrieved (dead
knowledge), some superseded (a newer asset answers the same need better), some stale (freshness
anchor broken, never re-verified). CO-06's registry pass prunes by a retention policy: an asset with
zero retrievals over a long window *and* no protected class (not a hard rule, not recently created)
is a prune candidate; a superseded asset is merged into its successor (its retrieval history
transfers, so the successor inherits the evidence of usefulness); a stale-unverified asset is
demoted to "verify-before-use" rather than deleted. The policy is conservative by construction —
the cost of dropping a useful asset (a future re-derivation, wasted WU/MTok) exceeds the cost of
keeping a dead one (a little index space), so CO-06 prunes slowly and never drops protected classes.

### II.2 Pruning the operational exhaust

Beyond knowledge assets, the kernel produces operational exhaust — old `mirror-drift` handoffs, old
`sleepy_index` snapshots, resolved breach RCAs, expired cache entries, old research files. The
Reality Scan found dozens of these accumulating in `vault/`. CO-06 owns their retention: append-only
incident ledgers (CO-00 breaches, CO-02 violations) keep *open* items and recent history, archiving
resolved old entries to COLD; expired Cognitive Cache entries (input hash no longer present) are
reclaimed; superseded snapshots beyond the retention window are pruned (the session-resilience
snapshot store already caps at 50 versions + tagged — CO-06 generalizes that cap discipline). The
guarantee, inherited from the Session Safety Contract: **no `.jsonl` transcript is ever destroyed by
GC** — operational exhaust is prunable; the durable session record is sacred. CO-06 prunes derived
and resolved artifacts, never primary session history.

### II.3 The honest limit of GC

CO-06 collects what the *kernel* loaded and what the *registry* holds. It cannot collect context the
*model's current turn* is holding mid-generation (the rung-2 limit, CO-00) — that is `/compact`'s
job, invoked at a turn boundary. CO-06's value is that, by continuously keeping HOT lean and the
registry clean, it makes those blunt resets rare. It is a *proactive* hygiene layer, not a mid-turn
context revoker, and it says so.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **Evicting the working set (thrashing).** Mis-scored relevance demotes content the task still
  needs → immediate page-in → churn. Detection: page-in within N turns of an eviction → the item was
  working-set; pin it and re-tune the relevance signal. (Shared with CO-04 III.1.)
- **Over-aggressive registry prune.** Dropping an asset that later proves useful → a re-derivation.
  Prevention: conservative retention + protected classes + merge-not-delete for superseded assets;
  detection: a freshly-reasoned conclusion matching a recently-pruned asset → widen retention.
- **Under-collection (bloat persists).** GC too timid, HOT still grows to the ceiling. Detection:
  frequent `/compact` triggers despite GC running → the eviction thresholds are too lax → tighten.
- **Pruning primary history (forbidden failure).** Any path that could delete a `.jsonl` transcript
  is a Session-Safety-Contract violation. Prevention: GC's prune scope is an allow-list of derived/
  resolved artifact classes; transcripts are categorically excluded, never matched.

### III.2 Rollback protocol

CO-06's rollback is graceful and fail-safe toward *retention*: (1) disable HOT eviction and revert to
`auto_reset_orchestrator`'s reactive-only behavior (advise `/compact` on pressure, no continuous
collection) — the kernel loses proactive hygiene but the blunt reset still works; (2) disable registry
pruning, so the asset store only grows (no risk of dropping a useful asset) until the policy is fixed;
(3) the pin set defaults to "pin everything" under fault, so a broken relevance signal can never evict
the working set. The fail-safe direction is always *keep more, evict less* — the pre-kernel behavior —
never aggressive deletion.

### III.3 Integration contract

- **CO-00** — CO-06 is the primary *proactive* mechanism that keeps the kernel off the 60% ceiling;
  it evicts as the action band approaches so the line is rarely threatened.
- **CO-04** — CO-06 supplies the eviction *policy* (what/when); CO-04 supplies the *mechanism* (the
  lossless page-out path). They share the pin set / working-set boundary.
- **CO-05** — CO-06 keeps the registry clean (prune dead, merge superseded, demote stale) without
  dropping protected knowledge.
- **CO-01 / CO-02** — eviction and prune decisions are priced; a prune that causes a later re-derivation
  shows as a WU/MTok loss, tuning the policy toward retention.
- **`/compact` `/kclear` `/clear`** — CO-06 makes them rarer (continuous surgical eviction) and informs
  them (the pin set tells `/compact` what to preserve); a `/clear` is a strong task-boundary demotion
  trigger.
- **Session Safety Contract** — CO-06's prune scope categorically excludes `.jsonl` transcripts; it
  collects derived/resolved exhaust only.
- **Knowledge Vault / Cursor** — registry hygiene runs over the vault; the statusline can expose HOT
  size + last-GC as a proactive signal.

### III.4 Anti-patterns (forbidden)

- **Evicting the working set.** The thrashing failure; the pin set exists to prevent it.
- **Aggressive registry deletion.** Dropping assets fast; the cost asymmetry mandates slow,
  conservative pruning with protected classes.
- **Treating /compact as the GC.** Relying on the blunt periodic reset instead of continuous
  eviction — the reactive pattern CO-06 replaces.
- **Pruning primary session history.** Any `.jsonl` transcript deletion. Categorically forbidden
  (Session Safety Contract §1).
- **Fail-closed GC.** A GC that, on its own fault, evicts more — CO-06 fails toward retention always.

---

### CO-06 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Continuously evicts non-working-set HOT content (recency+relevance+aging), lossless to WARM/COLD | As the CO-00 action band approaches | It cannot evict context the running turn holds mid-generation (that is /compact) |
| Pins the current working set + hard-rule-class + active task state — never evicted | Always | — |
| Prunes the asset registry + operational exhaust conservatively, protected classes exempt | On a retention schedule | — |
| Never deletes a `.jsonl` transcript — prune scope is a derived-artifact allow-list | Always | — |
| Rollback fails toward retention (keep more, evict less), pin-everything under fault | On misbehavior | — |

**Guarantee level (honest):** CO-06 is a *proactive hygiene* layer — it keeps HOT lean and the
registry clean continuously, making blunt resets rare; it cannot revoke a running turn's context
(rung-2 limit). It collects derived exhaust and dead knowledge, never primary history. *Sealed under
SCS C61.*
