# Session Resilience OS — Dataset 01 — UI / Editor State Persistence Layer (UESPL)

**Family:** Session Resilience OS (Path A, residual-gap family)
**Gap closed:** G1 — editor/UI surface state, absent from the existing terminal-only topology system
**Depends on:** Crash-to-Exact-Terminal-Topology Guarantee (pp_dataset XI / CETTG),
CPC-OS (pp_dataset X), Incremental Snapshot & Session Versioning Engine (Dataset 03),
Recovery Acceptance Framework (Dataset 04)
**Does NOT duplicate:** terminal pane topology (owned by CETTG), RAM governance (RS-OS),
workbench scheduling (RW-OS)

---

## 1. System name and exact purpose

The UI / Editor State Persistence Layer is the system responsible for capturing,
validating, persisting and restoring everything the human sees and touches inside a
Cursor window that is **not** a terminal pane. The existing Crash-to-Exact-Terminal-
Topology Guarantee restores the working *board of terminals* — how many panes existed,
which conversation lived in each, the working directory, the locks. That guarantee stops
at the terminal boundary. The editor surface above the terminals — the open files, the
order of their tabs, which one had focus, where the caret sat, how far each document was
scrolled, which side panels were open and how wide they were, how the editor was split
into groups — is today lost on any crash. When the Owner reopens Cursor after an
out-of-memory crash, the terminals can return exactly while the editor returns to a
generic default. That asymmetry is the precise reason a crash still *feels* different
from a Reload Window even when terminal recovery is perfect.

UESPL exists to erase that asymmetry for the editor surface. Its purpose is to make the
visual and interactive editor state a first-class element of recoverable session state,
captured continuously before any crash, stored alongside the terminal topology, and
restored as part of the same recovery flow — so that the editor a crash leaves behind is
the editor the Owner was looking at, not a blank reset.

## 2. Fundamental property guaranteed

After any crash-suspected restart, the editor surface of every recovered window is
**visually and interactively indistinguishable** from its last stable pre-crash state,
to the maximum fidelity the host editor exposes. Concretely: the same documents are open,
in the same tab order, in the same editor groups and splits, with the same tab pinned or
previewed, the same tab and group holding focus, each document scrolled to the same
position with the same caret and selection, and the same side panels open at the same
sizes. Where the host cannot technically restore a property, UESPL records the property
as *known-but-unrestorable* and surfaces it, rather than silently dropping it — the same
"never silently degrade" contract CETTG applies to panes, extended to the editor.

## 3. Contracts offered to consumers

UESPL promises its consumers — chiefly the recovery orchestrator, the snapshot/versioning
engine, and the acceptance framework — the following:

- **Completeness contract.** For every editor window under management, UESPL can produce a
  complete UI-state description covering tabs, order, focus, scroll/caret, panel layout
  and split topology. No captured window is partial-by-omission; any field it cannot
  obtain is explicitly marked unavailable with a reason.
- **Freshness contract.** The persisted UI state reflects a point no older than the last
  stable UI-change event. UESPL captures on meaningful UI transitions, not only at
  shutdown, so a crash never finds the state empty.
- **Validity contract.** UESPL never promotes a UI-state description to "restorable" unless
  it passes internal validation (the referenced files exist or are flagged missing, the
  focus target is a member of the captured set, the split topology is internally
  consistent). A description that fails validation is retained as diagnostic but never
  offered as a restore source.
- **Idempotent restore contract.** Applying the same UI-state description twice produces the
  same editor layout — no duplicated tabs, no compounding splits, no focus thrash.
- **Secret-safety contract.** UESPL stores file *paths and positions*, never file *contents*;
  any incidental capture that could carry a secret is routed through the redaction bus
  before persistence, consistent with the HR-SECRET family.

## 4. Responsibilities — what it does and what it does NOT do

UESPL **does**: enumerate open editor documents per window; record their canonical tab
order within each editor group; record which document, group and window held focus;
record per-document scroll offset, caret position and active selection; record the
open/closed state, dimensions and active view of the sidebar, panel and auxiliary bars;
record the editor split/group grid and its sizing; classify each tab as pinned, preview
or normal; and hand a validated, secret-safe UI-state description to the snapshot layer on
demand and on UI-change events.

UESPL **does NOT**: capture or persist file contents (that is the editor's own working-
copy/dirty-buffer concern and the version-control system's concern); manage terminal panes
(owned by CETTG); decide *when* a crash happened or *whether* to restore (owned by the
recovery orchestrator and crash-confidence scorer); store history of UI states over time
(owned by the Incremental Snapshot & Session Versioning Engine — UESPL produces the current
description, ISVE keeps the chain); coordinate across multiple windows (owned by the
Multi-Window Coordinator — UESPL describes one window's editor surface, MWC composes
windows). UESPL is a *describer and applier* of one window's editor surface, deliberately
narrow so each neighbouring system owns exactly one concern.

## 5. Relationships with existing PP systems

- **CETTG (pp_dataset XI).** Sibling, not overlap. CETTG owns the terminal half of a
  window; UESPL owns the editor half. A window's complete recoverable state is the union
  of a CETTG terminal-topology description and a UESPL editor-state description, joined on
  the same window/workspace identity. UESPL adopts CETTG's clean-close-vs-crash semantics
  and its "account for every element, never silently drop" doctrine.
- **CPC-OS (pp_dataset X, modules/cpc_os).** UESPL plugs into the same snapshot/heartbeat
  cadence CPC-OS already runs, contributing the editor portion of each snapshot rather
  than running a competing capture loop.
- **Incremental Snapshot & Session Versioning Engine (Dataset 03).** UESPL is a *producer*
  of UI-state descriptions; ISVE is the *historian* that stores them as baselines and
  deltas. UESPL exposes a stable description so ISVE can diff cheaply.
- **Multi-Window Coordinator (Dataset 02).** MWC is a *consumer* that aggregates per-window
  UESPL descriptions into a cross-window picture and drives multi-window restore order.
- **Recovery Acceptance Framework (Dataset 04).** RAF *audits* a restored editor against the
  UESPL description it was restored from, scoring fidelity and feeding the equivalence
  oracle that judges "post-OOM == post-Reload-Window".
- **PP Sessions extension (extension/).** The extension is the in-editor vantage point that
  can actually read and re-apply editor state; UESPL defines *what* it must read and apply,
  the extension provides the host access. Where the extension/host cannot apply a property,
  UESPL's unrestorable-marking contract governs the degradation.

## 6. Entities that compose the system

### 6.1 Editor Tab Inventory Engine
Purpose: enumerate the open editor documents of a window. Inputs: the live editor's set of
open documents per editor group. Outputs: a per-group list of document references (stable
path or resource identity) with each document's kind (file, diff, notebook, settings,
virtual). Behaviour: enumerates on capture and on tab open/close/move; resolves each
document to a stable, path-based identity that survives restart; flags untitled/unsaved
documents distinctly because they may not be restorable by path. Success: every visible
editor document appears exactly once with a resolvable identity. Failure: a document whose
identity cannot be resolved is recorded as unrestorable-with-reason rather than omitted.
Evolution: grows to understand new editor document kinds as the host adds them.

### 6.2 Tab Ordering Registry
Purpose: preserve the canonical left-to-right order of tabs within each editor group.
Inputs: the inventory plus the host's tab order per group. Outputs: an ordered sequence per
group. Behaviour: order is treated as state, not incidental — reorders are capture events.
Success: restored tab order matches the captured order position-for-position. Failure: if a
document is missing at restore, its slot is held or collapsed deterministically, never
allowed to silently scramble the remaining order. Evolution: extends to multi-dimensional
ordering if the host introduces nested tab groupings.

### 6.3 Active Focus Engine
Purpose: record the single focus path — which window, which editor group, which tab, and
where within (editor body vs a panel) — was active. Inputs: host focus signals. Outputs: a
focus descriptor pointing at members of the captured set. Behaviour: captures focus on
focus-change; validates that the focus target exists in the inventory. Success: after
restore the same tab in the same group is focused. Failure: if the focus target is
unrestorable, focus degrades to the nearest deterministic fallback (same group, first tab)
and the degradation is reported. Evolution: extends to widget-level focus (search box,
panel input) as fidelity demands rise.

### 6.4 Scroll & Cursor Position Layer
Purpose: record, per open document, the scroll offset, caret position and active selection.
Inputs: per-document viewport and selection state. Outputs: a position descriptor per
document. Behaviour: captures on a debounced scroll/selection-settle signal to avoid noise;
positions are stored relative to document structure so they survive minor external edits
where possible. Success: a restored document opens at the same scroll position with the
same caret/selection. Failure: if the document changed enough that the position is invalid,
the layer clamps to the nearest valid position and marks it approximate. Evolution: moves
from line/column anchors toward content-anchored positions for robustness against drift.

### 6.5 Panel Layout Engine
Purpose: record the open/closed state, dimensions and active view of the sidebar, bottom
panel, secondary sidebar and any auxiliary bars. Inputs: host layout state. Outputs: a
layout descriptor naming each region, its visibility, its size and its active view.
Behaviour: captures on layout-change. Success: restored window shows the same panels at the
same sizes with the same active views. Failure: a region the host will not let UESPL size
is restored to visibility only, with the size gap reported. Evolution: tracks new layout
regions the host introduces.

### 6.6 Editor Split Topology Engine
Purpose: record how the editor area is divided into groups — the grid of rows and columns,
which group sits where, and the relative sizing. Inputs: host editor-group layout. Outputs:
a split-topology descriptor. Behaviour: treats the split grid as recoverable structure that
must be rebuilt *before* tabs are placed into it, mirroring CETTG's "restore topology before
content" ordering rule at the editor level. Success: restored editor has the same number of
groups in the same arrangement and proportions. Failure: if the exact grid cannot be
rebuilt, the engine produces the closest achievable arrangement and reports the difference.
Evolution: supports richer nested/locked group models as the host evolves.

### 6.7 Pinned & Preview Tab Classifier
Purpose: distinguish pinned tabs, preview (italic, single-click-replaceable) tabs and normal
tabs, because these have different restore semantics. Inputs: per-tab host flags. Outputs: a
classification per tab. Behaviour: pinned tabs are high-priority restore targets; preview
tabs may be restored as normal or skipped per policy to avoid noise. Success: pinned stays
pinned, normal stays normal. Failure: ambiguous classification defaults to normal and is
reported. Evolution: absorbs new tab modes.

### 6.8 UI State Diff Adapter
Purpose: present the current UI-state description to the snapshot/versioning engine in a
form that diffs cheaply, so incremental snapshots of UI changes are small. Inputs: the
composed descriptor from the engines above. Outputs: a stable, canonically-ordered
description suitable for delta computation. Behaviour: guarantees field ordering and naming
stability so a tab reorder produces a small, legible delta rather than a whole-state churn.
Success: a single UI change yields a proportionally small delta. Failure: if canonical form
cannot be produced, it falls back to a full description and flags the inefficiency.
Evolution: co-evolves with ISVE's delta format.

## 7. Completion criteria for the system

UESPL is complete when: every editor surface property listed in section 6 is captured on
its corresponding change event and at the snapshot cadence; a captured description passes
validation before being offered for restore; a restore reproduces the surface to the host's
maximum fidelity with every unrestorable property explicitly reported; the restore is
idempotent under repetition; the editor description joins cleanly with a CETTG terminal
description on shared window identity; and no file contents or secrets are persisted. A
UESPL that captures tabs but not focus, or focus but not scroll, is incomplete by
definition — the Owner would still perceive the difference.

## 8. Dependencies

UESPL requires: a window-identity source stable across restart (shared with MWC and CETTG);
the snapshot cadence and storage substrate (CPC-OS / ISVE); the in-editor host access that
can read and re-apply editor state (PP Sessions extension); and the redaction bus for
secret-safe persistence. It does not require the terminal subsystem to function, but its
output is only *useful* when joined with CETTG terminal topology to form a whole-window
recovery.

## 9. Explicit anti-patterns

UESPL must never: persist file contents or dirty-buffer text under the guise of "UI state";
restore tabs before the split topology that must contain them; silently drop an
unrestorable property instead of reporting it; capture on every micro-event without
debouncing (a scroll storm must not flood the snapshot chain); treat preview tabs as
permanent state and accumulate noise across sessions; reorder surviving tabs to fill a gap
left by a missing document; or assume PID/handle continuity across a crash (editor handles
are invalid after restart, exactly as PIDs are for CETTG). It must also never compete with
CPC-OS by running a second capture loop — it contributes to the existing cadence.

## 10. Future evolution

UESPL evolves along the fidelity axis: from path-and-line anchors toward content-anchored
positions resistant to external edits; from file-level tabs toward richer document kinds
(notebooks, diffs, custom editors) as the host adds them; from per-window description toward
tighter co-design with the Multi-Window Coordinator so editor state and window state form a
single restorable graph; and from best-effort host application toward a capability registry
that records, per host version, exactly which properties are restorable — so the
unrestorable-marking contract becomes data-driven rather than discovered at restore time.
The long-horizon goal is that the editor half of a window reaches the same recovery
guarantee CETTG gives the terminal half, making "OOM crash" and "Reload Window"
indistinguishable across the entire window, not just its terminals.
