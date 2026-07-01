# Parallel Mesh — PM-03 — Shared Findings Bus (+ Redundancy Tax)

> Where PM-01 shares *standing* repo understanding and PM-02 prevents *starting* duplicate
> work, PM-03 shares *fresh discovery* and prevents *re-deriving* a conclusion another pane
> already reached. A finding is expensive: a pane spends real tokens to learn that a function
> is dead, a premise is false, a trap exists. The Bus publishes that finding once so no other
> pane pays to rediscover it. It also carries the **Reasoning Deduplication** gate (proposed
> as its own system, folded here to avoid the very duplication the mesh forbids): *before a
> pane reasons, it asks whether the conclusion already exists* — in the Vault, the Bus, or the
> Brain. If it does, the pane reuses it for zero new tokens. The **Redundancy Tax** is the
> enforcement edge: a pane attempting work already on the Bus is stopped and pointed at the
> existing result.
>
> EXTEND, not NEW: the Bus is the **hot, pane-to-pane layer of CO-05 (Zero Token Layer & Asset
> Registry)** — a published finding is a CO-05 asset with a freshness anchor. Its transport is
> the proven file-drop + dedup-cache + digest pattern of `autoresearch/cross_signal_bus.py`.
> Honest (CO-10): the Bus is an **append-only set of files plus a dedup cache, read at
> turn-start** — not a live event stream between Claude instances.

---

## Part I — Publishing and Consuming Findings

### I.1 What a finding is

A finding is a small, structured, *reusable* conclusion a pane paid to reach: "this function
has no callers," "this API's real signature is X, not the assumed Y," "this test is flaky for
reason Z," "this file is the wrong one to edit — the live copy is elsewhere." It is precisely
the class of knowledge that is expensive to derive and cheap to reuse — the same economics that
justify CO-05's asset registry, applied to *in-session discoveries* rather than durable assets.
A finding carries its evidence (the file:line or command that proved it), a freshness anchor
(the HEAD/hash it was true against), and the pane that published it — so a consumer can judge
whether to trust it directly or re-verify.

### I.2 Consume before you reason (the Zero-Token gate)

The operative discipline, inherited straight from CO-05: **before reasoning, ask if the answer
already exists.** PM-03 gives that question three places to look, checked in cost order —
cheapest first: the **Repo Shared Brain** (PM-01, standing knowledge), the **Findings Bus**
(hot, recent discoveries), and the **Knowledge Vault** (durable, cross-session, cross-repo).
A hit means the pane reuses the existing conclusion for zero new model tokens; only a miss
justifies spending tokens to derive it — and when it does, the result is *published back*, so
the miss is paid once by the whole mesh. This is CO-05's "can this be answered without a model?"
extended with two new sources (Brain, Bus) beyond the asset registry. Folding it here — rather
than as a standalone "Reasoning Dedup" dataset — is the root law applied to the mesh's own
design: a dedup engine that duplicated CO-05 would be self-refuting.

### I.3 The Cross-Pane Commit Protocol

A pane's discoveries are worthless to the mesh if they die with the pane. On close, every pane
runs the **Cross-Pane Commit Protocol**: publish what changed (files, decisions), what it
learned (findings), what assets it created (reusable outputs for CO-05), and — critically — what
must **not** be repeated (the trap it hit, so the next pane is warned before paying for it). This
is the write-half of the Bus, and it is what turns a pane's ephemeral session into compounding
mesh knowledge. It is the direct sibling of the compound-learnings and NEVER_AGAIN pipelines,
scoped to the live work window rather than to end-of-session distillation.

---

## Part II — The Redundancy Tax and Trust

### II.1 The Redundancy Tax

Consuming-before-reasoning is a discipline; the Redundancy Tax is its *enforcement*. When a pane
declares (PM-02) or begins work whose output already exists on the Bus — a finding another pane
just published, an asset already in CO-05 — the mesh does not let it silently re-derive. It
**stops the redundant work and points the pane at the existing result**, exactly as PM-02's
Reuse resolution does at declaration time. The Tax is not a punishment; it is a redirect: the
"cost" of attempting duplicate work is being handed the answer instead. This closes the loop that
an advisory alone leaves open — the 48h burn happened because nothing *stopped* the duplication,
only warned about it. The Tax is the stop.

### II.2 A published finding is untrusted input until anchored

The Bus carries findings from *other* panes — and the Prompt-Defense baseline treats
cross-boundary data as untrusted until validated. A consumer does not blindly act on a published
finding; it weighs the finding's freshness anchor and evidence. A finding whose anchor still
matches live state (the file it described is unchanged) is trusted directly — zero re-derivation.
A finding whose anchor is stale (the underlying file moved on) is treated as a *lead*, not a
fact: the consumer re-verifies the specific claim against source (HR-PREMISE-001) before acting.
This is the same primary-source-wins discipline PM-01 applies to the Brain: the Bus accelerates,
it never overrides verification on the specific artifact about to change.

### II.3 Dedup without suppressing novelty

The dedup cache — reused from `cross_signal_bus`'s proven design — must catch true repeats
without silencing genuinely-new findings that merely *resemble* old ones. PM-03 dedups on
finding *identity* (the claim + the artifact it concerns), not on surface text similarity, so
"function A is dead" and "function B is dead" are two findings, not a near-duplicate collapsed to
one. A collapse that hides a novel finding is the dangerous failure (III.1), and the cache is
tuned toward *publishing a possible-duplicate* over *suppressing a possible-novelty* — false
publication costs a little Bus space; false suppression loses knowledge the mesh paid for.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **Finding never published.** A pane learns something and closes without committing it → the
  next pane re-pays. Detection: the Cross-Pane Commit Protocol is a close-boundary gate; a pane
  that made edits but published no findings/deltas is flagged (a silent close is the bug, the
  sibling of the write-without-read lesson — a discovery with no publication is documentation of
  nothing).
- **Stale finding consumed as fact.** A consumer acts on an anchor-stale finding. Detection:
  every consume computes the anchor verdict; a stale finding is a lead requiring re-verification,
  never a fact. Fail toward re-verify.
- **Dedup suppresses a novel finding.** The cache collapses a real discovery into an old one.
  Detection: dedup on claim+artifact identity, not text similarity; audit collapses where the
  artifacts differ → loosen. Tuned toward over-publish, never over-suppress.
- **Bus bloat.** Findings accrete and the Bus becomes its own read cost. Detection: Bus size vs
  consume-tokens-saved; CO-06 garbage-collects findings whose anchors are long-dead or whose
  claims were superseded.

### III.2 Rollback protocol

PM-03 degrades to no-Bus with zero knowledge loss. (1) Demote the Redundancy Tax from *stopping*
to *advising* (warn that work may be duplicate, let it proceed) — restoring pre-mesh behavior
where nothing blocked re-derivation. (2) Make the Bus read-only-advisory — panes may consult it
but are not gated on it. (3) Full disable — each pane keeps findings private; the Vault (CO-05)
remains as the durable cross-session layer, so nothing durable is lost, only the *hot* pane-to-
pane layer. The fail-safe direction is **toward re-derivation, never toward stale-trust**: a
broken Bus must degrade to "ignore me and derive it," never to "trust my stale finding."

### III.3 Integration contract

- **CO-05 (parent)** — a published finding is a CO-05 asset with a freshness anchor; the Vault is
  the durable tier below the hot Bus. The consume-before-reason gate *is* CO-05's zero-token
  principle with Brain + Bus added as sources.
- **`autoresearch/cross_signal_bus.py`** — the reused transport pattern (file drop + dedup cache
  + digest); PM-03 is that mechanism repointed from research signals to pane findings.
- **CO-06** — garbage-collects dead/superseded findings on the memory-hygiene policy.
- **PM-01 / PM-02** — the Brain's "recent findings" section points at the Bus; PM-02's Reuse
  resolution is the Redundancy Tax applied at declaration time (before work starts) rather than
  mid-work.
- **NEVER_AGAIN / compound-learnings** — the "what must not be repeated" half of the Commit
  Protocol feeds the same durable pipelines at session end.
- **`/kclaude`** — a launching pane consumes the Bus in its opening briefing (with the Brain).
- **`/compact`** — the Bus is external memory: a compacted pane re-reads it rather than
  re-deriving lost findings. **`/kclear`** — clears the session but not the Bus (repo-scoped
  knowledge persists). **`/loop`** — a loop consumes the Bus once at entry and publishes findings
  per iteration only if they are *new*; re-publishing the same finding each iteration is Bus spam
  (III.4).

### III.4 Anti-patterns (forbidden)

- **Reasoning before consulting Brain / Bus / Vault.** The zero-token gate is mandatory; deriving
  a conclusion that already exists is the canonical duplicate cognition.
- **Closing a pane without the Commit Protocol.** A discovery not published is paid for again by
  the next pane.
- **Acting on a stale finding as fact.** Anchor-stale findings are leads; verify against source.
- **Dedup on text similarity.** Collapses novel findings; dedup on claim+artifact identity, biased
  toward over-publish.
- **Re-publishing the same finding every loop iteration.** Publish new findings once; the Bus is
  not a log.
- **Claiming the Bus is a live event stream.** It is append-only files + a dedup cache read at
  boundaries (CO-10).

---

### PM-03 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| A pane consults Brain / Bus / Vault before reasoning; a hit reuses for zero new tokens | Panes follow the consume-before-reason gate | Coverage of a pane that reasons without consulting (flagged like an un-gated pane) |
| A finding is published once; the mesh pays a miss once, not per-pane | Cross-Pane Commit Protocol runs at close | A finding never committed (flagged) |
| The Redundancy Tax stops declared/started work that duplicates an existing result | Work matches a Bus/asset entry | Detection of duplication that no pane published |
| Published findings are untrusted-until-anchored; stale ones are leads requiring re-verify | Always | Trust of a stale finding as fact |
| Rollback degrades to no-Bus with the durable Vault intact; zero knowledge loss | On misbehavior | — |

**Guarantee level (honest):** rung-2/3 — consume-before-reason is a prompt/hook discipline; the
Redundancy Tax stops at the declaration boundary (wrapper, via PM-02) and advises mid-work. The
Bus is **append-only files + a dedup cache read at turn-start**, not IPC. It governs panes that
consult it; a pane that never consults is flagged, not silently covered. Parent: **CO-05**.
*Sealed under SCS C65.*
