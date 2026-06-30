# Cognitive OS — CO-05 — Zero Token Layer & Cognitive Asset Registry

> The kernel's institutional memory. **Every pattern, rule, template, mapping, schema, or
> decision the kernel discovers and verifies becomes a permanent asset, retrieved thereafter
> at zero new model cost.** The system never reasons the same thing twice. This is the rung
> CO-03's cascade reaches first and the content WARM memory (CO-04) holds.
>
> EXTEND, not NEW: the Knowledge Vault (`vault/knowledge_base/`, UKDL, FTS5 indices,
> `_audit_cache/source_map.json`, the false-positives catalog) already stores knowledge;
> `jit_skill_loader`'s session-dedupe already suppresses re-injection within a 2h window. CO-05
> unifies these into a single asset registry with an explicit lifecycle and freshness model,
> and adds the missing piece — *de-duplication of reasoning across sessions*, permanently.

---

## Part I — The Asset Lifecycle

### I.1 What is an asset

A Cognitive Asset is a unit of verified, reusable knowledge that resolves a recurring need
without re-reasoning it. The PP already produces these constantly but inconsistently — a UKDL
trap, a hard rule, a false-positive entry, an audit-cache neural summary, a routing decision, an
RCA disposition. CO-05 names them one class and gives them one home. The defining property,
inherited from the Reality Contract: **an asset is only stored after it is verified.** A pattern
observed once is a hypothesis; a pattern that passed a done-gate, recurred, or was confirmed by
an RCA is an asset. CO-05 stores the latter, never the former — an unverified "asset" would
poison CO-03's cheap rungs with wrong answers.

### I.2 The lifecycle: discover → verify → store → retrieve → refresh

- **Discover.** The kernel encounters a resolution worth keeping — a working pivot, a mapping, a
  decision with its rationale. The signal thresholds the PP already uses (the compound-learnings
  model: 1=skip, 2=consider, 3+=strong, 4+=create) gate which discoveries become candidate
  assets, so the registry does not fill with one-offs.
- **Verify.** The candidate must clear the Production Reality Gate (the same gate CO-01 uses for
  Work Units) — observed to work, not merely plausible. Verification is what separates an asset
  from a note.
- **Store.** The verified asset is written to the registry (the Vault), indexed for retrieval,
  tagged with its applicability conditions and a freshness anchor (a hash/mtime of whatever it
  describes, so staleness is detectable).
- **Retrieve.** CO-03's cascade and CO-04's WARM tier read the registry first; a hit resolves the
  task at zero new model cost. This is the payoff rung — the whole point of storing.
- **Refresh.** An asset whose freshness anchor no longer matches (the file/API/fact it describes
  changed) is flagged stale and either re-verified or demoted, never served blind. This closes
  the loop that today's static vault entries lack — a stored answer that silently went wrong is
  worse than no answer.

### I.3 "Never reason the same thing twice" — the genuinely new contribution

The Reality Scan rated the Zero Token Layer ABSENT because `jit_skill_loader`'s dedupe is
*TTL-only* (it suppresses re-injecting the same skill within 2h) — it does not prevent the kernel
from *re-deriving the same conclusion* in a new session next week. CO-05's new contribution is
*cross-session reasoning de-duplication*: when the kernel is about to reason through a problem, the
cascade (CO-03) checks whether a verified asset already holds the conclusion. If the same
Windows-bash pivot, the same git-path workaround, the same false-positive classification has been
reasoned and stored before, it is *retrieved*, not *re-derived*. The savings compound over time —
the longer the kernel runs, the larger its asset base, the more often the cheapest rungs resolve
tasks, the higher the WU/MTok. A mature kernel reasons from a vast retrieved base and pays models
only for genuinely novel problems.

---

## Part II — Registry Structure, Vault Router, Cognitive Cache

### II.1 The registry and the Vault Router

The registry is the Knowledge Vault, organized so retrieval is fast and precise. The **Vault
Router** (the partially-existing system the Reality Scan found in `jit_skill_loader` triggers +
the FTS5 indices) is the lookup layer: given a task, it returns the matching assets ranked by
applicability and freshness. CO-05 formalizes it as the index over the asset registry that CO-03's
rung-1 consults. It composes the existing pieces — FTS5 BM25 search, the audit-cache hash map, the
JIT trigger table — into one query surface, rather than the three separate lookups that exist
today. The router returns *pointers* (WARM, CO-04), paged to full content only on confirmed need,
so consulting the registry is itself near-zero context cost.

### II.2 The Cognitive Cache (computed-result reuse)

Distinct from stored *knowledge* assets, the Cognitive Cache holds reusable *computed results*:
an audit summary keyed by file-hash (`audit_cache` already does this — hash-match = use cached
summary, skip re-read), a parsed structure, a derived mapping. The cache is the deterministic rung
(CO-03 rung 3) made durable across sessions. Its discipline is freshness-by-hash: a cached result
is valid only while its input hash matches; on mismatch it is recomputed. The cache is what lets
the kernel skip not just re-reasoning but re-*reading* — the Token Austerity Protocol's circuit
breaker (40KB raw-read budget, hash-match → cached summary) is exactly this, generalized.

### II.3 Freshness as a first-class property (why static vaults rot)

The failure mode of every knowledge store is rot: an entry that was true when written and is
quietly false now (a recalled memory naming a file/flag that no longer exists — the exact risk the
PP's own memory protocol warns about). CO-05 makes freshness first-class: every asset carries an
anchor (hash, mtime, version, or an explicit "verify-before-use" flag for facts that can drift),
and retrieval *checks the anchor*. A stale asset is never served as fresh; it is re-verified or
demoted. This is the single most important difference between CO-05 and a passive documentation
folder — the registry is a *live* memory that knows when it has gone stale, not an archive that
confidently serves rot.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **Poisoned asset (unverified stored as verified).** A wrong pattern enters the registry and
  CO-03 serves it cheaply thereafter — high-leverage corruption. Prevention: the verify gate is
  mandatory; detection: an asset whose retrievals produce gate-failures is auto-flagged and
  quarantined (its WU/MTok contribution is negative).
- **Stale asset served blind.** Anchor check skipped or anchor missing. Prevention: no asset is
  retrievable without an anchor; anchor-less legacy entries are treated as "verify-before-use".
- **Registry bloat / low-value assets.** The 1=skip/2=consider/3+=create thresholds keep one-offs
  out; CO-06 (GC) prunes assets with zero retrievals over a long window (dead knowledge) under a
  retention policy that never drops a hard-rule-class or recently-useful asset.
- **Retrieval miss (asset exists but isn't found).** The Vault Router's index is stale or the
  query is too narrow → the kernel re-reasons something it already knew (a silent efficiency leak).
  Detection: post-hoc match between a freshly-reasoned conclusion and an existing asset → the index
  is improved so the next lookup hits.

### III.2 Rollback protocol

CO-05 is additive knowledge, so rollback is safe: (1) disable cross-session reasoning-dedupe and
revert to `jit_skill_loader`'s TTL-only behavior + the static vault (today's baseline) — the kernel
loses the zero-token reuse but keeps every stored entry; (2) if a poisoned asset is suspected,
quarantine the registry write path (read-only mode) so no new assets enter while existing ones are
audited; (3) the freshness/anchor layer can be disabled, reverting to static vault reads (with the
known rot risk, but no worse than pre-kernel). The registry's *content* never rolls back — it is the
institutional memory; only the *active reuse* can be paused.

### III.3 Integration contract

- **CO-03** — CO-05 *is* the router's rung-1/2 (Vault + asset). The cascade is the registry's
  primary consumer.
- **CO-04** — the registry is the bulk of WARM memory; CO-05 supplies content + freshness, CO-04 the
  tiering.
- **CO-00 / CO-01 / CO-02** — every breach RCA, calibration insight, and budget-violation pattern is
  stored as an asset, so the kernel learns from each incident exactly once and routes around it
  thereafter. This is how the ceiling and the budgets *sharpen over time*.
- **CO-06** — provides the eviction policy that prunes dead/low-value assets without dropping
  hard-rule-class knowledge.
- **`/compact` `/kclear`** — before a reset, durable conclusions are extracted to the registry
  (compound-learnings model) so the reset loses transient context but not verified knowledge.
- **Knowledge Vault / Cursor** — the registry *is* the vault; the FTS5 indices are the Vault Router;
  the statusline/`/cpp-compound` surfaces accrual.

### III.4 Anti-patterns (forbidden)

- **Storing the unverified.** A hypothesis written as an asset poisons CO-03's cheap rungs.
- **Serving without a freshness check.** The static-vault rot trap.
- **Re-reasoning a stored conclusion.** The efficiency leak CO-05 exists to close — every avoidable
  re-derivation is wasted WU/MTok.
- **Hoarding one-offs.** Filling the registry below the 3+ recurrence threshold, drowning real assets.
- **A parallel verification standard.** Assets are verified by the Production Reality Gate, not a
  CO-05-private notion of "good enough".

---

### CO-05 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Stores a discovery as an asset only after the Production Reality Gate verifies it | Always; signal-threshold gated | That every useful thing is captured — sub-threshold one-offs are intentionally skipped |
| Retrieval resolves recurring tasks at zero new model cost (CO-03 rung-1/2) | When a fresh matching asset exists | A hit for genuinely novel problems (those pay a model, correctly) |
| Every asset carries a freshness anchor; stale assets are re-verified or demoted, never served blind | Always | — |
| Cross-session reasoning de-dup: the kernel never re-derives a stored, verified conclusion | When the Vault Router index finds it | Zero retrieval-misses (improved continuously, not perfect) |
| Rollback pauses active reuse without losing stored knowledge | On poisoning/misbehavior | — |

**Guarantee level (honest):** CO-05 is a *knowledge-reuse* layer (rung-2 class, deterministic
retrieval) — it makes re-reasoning *avoidable* and zero-cost when an asset exists; it cannot
guarantee an asset exists for a novel task, and a retrieval-miss silently costs a model call (the
miss is detected post-hoc and the index improved). *Sealed under SCS C61.*
