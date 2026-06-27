# Session Resilience OS — Dataset 03 — Incremental Snapshot & Session Versioning Engine (ISVE)

**Family:** Session Resilience OS (Path A, residual-gap family)
**Gap closed:** G3 — delta snapshots and restore-to-a-prior-version (absent; only full-state snapshots exist)
**Depends on:** CPC-OS snapshot substrate (pp_dataset X, modules/cpc_os/snapshot.py),
Crash-to-Exact-Terminal-Topology Guarantee (pp_dataset XI / CETTG),
UI / Editor State Persistence Layer (Dataset 01), Multi-Window Coordinator (Dataset 02)
**Does NOT duplicate:** the act of *capturing* state (owned by CETTG / Dataset 01 / Dataset 02),
RAM checkpointing (RS-OS), setup-transaction rollback (setup_os, a different domain)

---

## 1. System name and exact purpose

The Incremental Snapshot & Session Versioning Engine is the historian of session state.
Today the PP captures state as **full snapshots**: each capture writes a complete picture and
the last good one is promoted to last-known-good. That is correct but lossy in two ways.
First, it is *expensive*: writing a complete picture on every meaningful change is wasteful
when only one tab moved or one pane switched conversation, so capture cadence is forced lower
than it should be, widening the window in which a crash loses recent work. Second, it is
*amnesiac*: there is exactly one restorable point — the last good state. The Owner cannot say
"take me back to how the board looked an hour ago, before I tore down those three panes",
because no prior arrangement is retained.

ISVE exists to fix both. Its purpose is to store session state as a **chain of baselines and
deltas** so that captures become cheap (enabling a tighter cadence and therefore less lost
work on crash) and to maintain a **catalog of restorable versions** so that recovery is not
limited to the single most recent state but can target any retained prior version. It does
not capture state itself — it consumes the descriptions the capture systems already produce
and turns them into a compact, navigable history.

## 2. Fundamental property guaranteed

At any moment there exists a chain of state versions from which the engine can reconstruct,
exactly and validity-checked, both the most recent stable session state **and** any retained
prior version. Reconstruction of any offered version is byte-faithful to what was captured at
that point: applying a version's baseline plus its delta sequence yields precisely the state
that existed then. No offered version can be partially reconstructed; if the chain to a
version cannot be validated end-to-end, that version is withheld rather than restored wrong.

## 3. Contracts offered to consumers

- **Cheap-capture contract.** Recording a new state costs proportional to *what changed*, not
  to total state size, so consumers can capture frequently without prohibitive cost.
- **Faithful-reconstruction contract.** Any version the catalog offers can be reconstructed to
  exactly the captured state; the engine never offers a version it cannot fully rebuild.
- **Navigability contract.** Consumers can enumerate retained versions with enough metadata
  (when, why captured, what changed at a glance) to choose one, and can request a
  human-readable difference between any two.
- **Retention contract.** The engine honours a declared retention policy — which anchors and
  deltas survive, which are compacted, which are pruned — and never prunes a version still
  reachable as a restore target without saying so.
- **Integrity contract.** Every reconstruction is validated against the chain's integrity
  markers before being handed out; a broken chain degrades to the nearest fully-valid version,
  reported.
- **Secret-safety contract.** Deltas and baselines inherit the secret-safety of their sources;
  the engine adds no new egress and routes any persisted metadata through redaction.

## 4. Responsibilities — what it does and what it does NOT do

ISVE **does**: compute the difference between a newly-presented state description and the
prior one; store baselines (periodic full anchors) and the deltas between them; maintain an
ordered chain linking deltas to their baseline; catalog named/timestamped restorable versions
with metadata; reconstruct any cataloged version on request by replaying its baseline and
deltas; compact old delta runs and prune by retention policy; validate chain integrity before
every reconstruction; and present human-readable diffs between versions.

ISVE **does NOT**: capture live state (it is fed descriptions by CETTG, Dataset 01, Dataset 02
and CPC-OS); decide *when* to capture (cadence is the capture systems' and CPC-OS's concern —
ISVE just records what it is given); decide *whether* to restore after a crash (the recovery
orchestrator does); judge whether a restore *succeeded* (Dataset 04 does); or govern resources
(RS-OS / RW-OS). It is purely the storage-and-history concern, deliberately separated so that
capture, history, recovery decision and acceptance each have one owner.

It is explicitly **distinct from setup_os transaction rollback**: that system rolls back
*setup/installation* transactions; ISVE versions *session UI/terminal/window state*. They
share the word "rollback" and nothing else.

## 5. Relationships with existing PP systems

- **CPC-OS snapshot substrate (modules/cpc_os/snapshot.py).** ISVE sits behind the existing
  snapshot entry point: where CPC-OS today writes a full snapshot and promotes last-known-good,
  ISVE intercepts to store a delta against the current baseline and to promote a *version*
  rather than overwriting a single file. Last-known-good becomes "the latest validated version"
  — a special case of the catalog, preserving every existing consumer's expectation.
- **CETTG / Dataset 01 / Dataset 02.** These are ISVE's data sources. Each produces a
  description (terminal topology, editor surface, window census) presented through their diff
  adapters so deltas are small and legible.
- **RS-OS (pp_dataset XII).** RAM checkpointing triggers a capture at high memory pressure;
  ISVE records that capture cheaply, so frequent pre-OOM checkpoints do not bloat storage.
- **Recovery orchestrator / Recovery Acceptance Framework (Dataset 04).** The orchestrator
  asks ISVE for a version to restore (usually latest, sometimes a chosen prior one); RAF later
  scores whether the restore matched the version's reconstruction.
- **Recovery Telemetry & Diagnostics (Dataset 05).** ISVE emits events (version promoted,
  chain repaired, pruned) for observability.

## 6. Entities that compose the system

### 6.1 Delta Capture Engine
Purpose: compute the change between a newly-presented state description and the immediately
prior one. Inputs: the current description from a capture system, plus the prior description.
Outputs: a delta expressing only what changed. Behaviour: relies on the stable canonical form
the capture systems' diff adapters provide so a small real change produces a small delta;
falls back to a full description when no meaningful prior exists. Success: a single-property
change yields a proportionally tiny delta. Failure: if a clean delta cannot be computed, it
records a new baseline instead and flags the inefficiency. Evolution: smarter structural
diffing as descriptions grow richer.

### 6.2 Baseline Anchor Registry
Purpose: hold the periodic full-state anchors that deltas reference. Inputs: full descriptions
at anchor points (first capture, post-compaction, on policy interval). Outputs: a set of
baseline anchors. Behaviour: anchors are created often enough that no reconstruction must
replay an unbounded delta run, balancing cost against replay length. Success: every delta has
a reachable baseline within the policy's replay bound. Failure: a missing or corrupt baseline
forces promotion of the next valid full capture to anchor and reports the gap. Evolution:
adaptive anchoring frequency based on change velocity.

### 6.3 Snapshot Chain Manager
Purpose: maintain the ordered linkage baseline → delta → delta → … so any point is
reconstructable. Inputs: baselines and deltas. Outputs: an ordered, validated chain. Behaviour:
enforces that the chain is append-only and totally ordered; detects breaks. Success: the chain
is a single valid sequence from each baseline. Failure: a break splits the chain at the last
valid point and everything after is quarantined, reported, never silently bridged. Evolution:
supports branching chains if versioning ever needs alternate timelines.

### 6.4 Version Catalog
Purpose: present restorable versions as a navigable list. Inputs: chain positions designated as
versions, with metadata (timestamp, capture reason, brief change summary, crash-confidence at
capture). Outputs: an enumerable catalog. Behaviour: every promoted stable point becomes a
cataloged version; the latest validated one is the implicit last-known-good. Success: the Owner
or orchestrator can list versions and understand each without reconstructing it. Failure: a
version whose chain is broken is shown as unrestorable-with-reason, not hidden. Evolution:
richer metadata (which window/pane changed, tags like "before deploy").

### 6.5 Version Restore Selector
Purpose: choose which version to reconstruct for a given recovery. Inputs: a request (latest,
a specific version, or "the last version before condition X"). Outputs: the selected version's
fully-reconstructed state. Behaviour: defaults to latest validated; honours explicit prior-
version requests; refuses selections whose chain fails integrity. Success: the requested
version is reconstructed exactly. Failure: an unrestorable selection returns the nearest valid
alternative with a clear explanation, never a silent substitution. Evolution: query-style
selection ("last stable 3-window arrangement").

### 6.6 Compaction & Retention Engine
Purpose: keep history bounded. Inputs: the chain plus a retention policy. Outputs: a compacted,
pruned chain. Behaviour: collapses long delta runs into fresh baselines, prunes versions older
than policy or beyond a count, but never prunes a version still designated a live restore
target without surfacing the decision. Success: storage stays bounded while all policy-
protected versions remain reconstructable. Failure: if compaction would orphan a protected
version it aborts that step and reports. Evolution: value-aware retention (keep "interesting"
versions longer).

### 6.7 Integrity Chain Validator
Purpose: prove a version reconstructs validly before it is handed out. Inputs: a baseline and
its delta run. Outputs: a validity verdict plus the reconstructed state when valid. Behaviour:
replays and checks integrity markers end-to-end; runs before every reconstruction, not only at
write. Success: only fully-valid reconstructions are released. Failure: an invalid chain
yields no reconstruction; the validator points the selector at the nearest valid version.
Evolution: incremental validation caching for speed.

### 6.8 Version Diff Presenter
Purpose: explain the difference between two versions in human terms. Inputs: two cataloged
versions. Outputs: a readable difference (tabs opened/closed, panes added/removed, windows
changed, focus moved). Behaviour: operates on descriptions, not raw bytes, so the diff is
meaningful to the Owner. Success: the Owner can decide which version to restore from the diff
alone. Failure: if a version cannot be reconstructed for diffing it says so. Evolution: visual
diffs surfaced through the PP Sessions extension.

## 7. Completion criteria for the system

ISVE is complete when: new state is recorded as a delta proportional to change against a
reachable baseline; the chain is append-only, ordered and break-detecting; a catalog of
restorable versions exists with meaningful metadata and an implicit last-known-good; any
offered version reconstructs exactly and is integrity-validated before release; retention keeps
storage bounded without orphaning protected versions; and diffs between versions are
human-readable. An engine that stores deltas but cannot reconstruct a chosen prior version, or
that prunes a live restore target silently, is incomplete.

## 8. Dependencies

ISVE requires: the capture systems' stable canonical descriptions (CETTG, Dataset 01, Dataset
02) as input; the CPC-OS snapshot entry point to intercept; a durable storage substrate;
integrity markers on stored artifacts; and the redaction bus for any added metadata. It does
not require the recovery orchestrator to function, but its history is only *exercised* through
recovery and version-restore requests.

## 9. Explicit anti-patterns

ISVE must never: write a full snapshot on every change when a delta suffices (defeating its
own purpose); offer a version it cannot fully reconstruct; silently bridge a broken chain
across a quarantined gap; prune a version still designated a restore target without surfacing
it; conflate session-state versioning with setup-transaction rollback; capture state itself
instead of consuming the capture systems' descriptions; or promote a delta computed against a
stale or wrong prior description. It must also never let the chain grow unbounded — absence of
compaction is a defect, not a default.

## 10. Future evolution

ISVE evolves from a single linear timeline toward optional branching (alternate session
timelines the Owner can switch between), from time/count retention toward value-aware retention
that preserves semantically significant versions (the state before a deploy, before a large
refactor, before a known-good moment), and from byte-level diffs toward rich semantic diffs
surfaced visually in the PP Sessions extension. Tighter co-design with the capture systems
will shrink deltas further, permitting a near-continuous capture cadence that reduces the
crash-loss window toward zero — the storage-side contribution to making an OOM crash lose no
more than a Reload Window does.
