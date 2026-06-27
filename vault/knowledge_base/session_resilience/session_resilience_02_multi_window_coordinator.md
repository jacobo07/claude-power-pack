# Session Resilience OS — Dataset 02 — Multi-Window Coordinator (MWC)

**Family:** Session Resilience OS (Path A, residual-gap family)
**Gap closed:** G2 — cross-window topology and coordination (grep confirmed zero existing coverage)
**Depends on:** Crash-to-Exact-Terminal-Topology Guarantee (pp_dataset XI / CETTG),
UI / Editor State Persistence Layer (Dataset 01), CPC-OS (pp_dataset X),
Resilient Workbench OS (pp_dataset XIV / RW-OS), Recovery Telemetry & Diagnostics (Dataset 05)
**Does NOT duplicate:** single-window pane topology (CETTG), editor surface state (Dataset 01),
RAM governance (RS-OS)

---

## 1. System name and exact purpose

The Multi-Window Coordinator is the system that owns session state **above the single
window**. Every existing recovery system in the PP is window-local: CETTG restores the
terminal panes of *a* workspace, the editor-state layer restores the editor surface of *a*
window, CPC-OS keys its manifests by a workspace identity. None of them owns the fact that
the Owner frequently runs **several Cursor windows at once** — different repositories,
different monitors, a reference window beside a work window — and that, after an out-of-
memory crash or a machine reboot, the Owner does not merely want *one* window back: they
want the *whole arrangement of windows* back, each restored to its own internal state, in
the right relationship to the others.

MWC exists to make the *set of windows* a recoverable entity. Its purpose is to know how
many Cursor windows existed, which workspace each hosted, how they related, which one was
foreground, and to drive their restoration as a coordinated whole rather than as
independent, racing, possibly-colliding single-window recoveries. It is the conductor that
turns N window-local recovery guarantees into one workspace-of-windows guarantee.

## 2. Fundamental property guaranteed

After any crash-suspected restart, the Owner's full multi-window arrangement is restored:
the same number of Cursor windows, each bound to the same workspace it previously hosted,
each restored to its own internal terminal topology (via CETTG) and editor surface (via
Dataset 01), with the same window holding foreground focus, and with no two windows
contending for the same conversation, pane lock or workspace. Where a window cannot be
auto-restored, MWC produces an exact per-window manual plan, never silently dropping a
window — the CETTG no-loss doctrine raised one level, from panes-within-a-window to
windows-within-a-session.

## 3. Contracts offered to consumers

- **Census contract.** MWC can always state how many windows existed in the last stable
  state and what each hosted, derived from durable records — never from live process or
  handle counts, which are invalid after a crash.
- **Binding contract.** Every window in the census carries a stable window identity bound to
  a specific workspace/folder, so restore re-creates the *right* window for the *right*
  repository, not a generic window.
- **Coordination contract.** MWC guarantees that multi-window restore is ordered and
  conflict-free: dependent windows wait for their prerequisites, and no two windows are
  ever directed to claim the same conversation, pane or lock simultaneously.
- **Foreground contract.** Exactly one window is designated foreground after restore — the
  one that held focus pre-crash — so the Owner lands where they left off rather than in an
  arbitrary window.
- **No-loss contract.** Every window from the census ends restore in an explicit state:
  restored, intentionally-skipped, manual-required or blocked-with-reason. A window cannot
  vanish without explanation.
- **Secret-safety contract.** Window and workspace records carry paths and identities only,
  routed through redaction, never credentials or file contents.

## 4. Responsibilities — what it does and what it does NOT do

MWC **does**: maintain a durable registry of Cursor windows and their workspace bindings;
compute the cross-window topology (which windows existed, how they related, which was
foreground); resolve stable window identity across restart without trusting PIDs or
handles; decide the order in which windows are restored and which may proceed in parallel;
arbitrate foreground focus after restore; coordinate locks so concurrent window recoveries
never collide on a shared conversation or pane; and emit a per-window completion accounting.

MWC **does NOT**: restore the *inside* of any window — terminal panes belong to CETTG, the
editor surface to Dataset 01; MWC orchestrates *which* windows and *in what order*, then
delegates inward. It does not decide *whether* a crash occurred (that is the crash-
confidence scorer's job) — it consumes that verdict. It does not store the *history* of
window arrangements over time (that is the versioning engine, Dataset 03) — it owns the
current/last-stable census. It does not govern resources (RS-OS) — but it *honours* RW-OS
throttle and RAM-aware restore signals when sequencing windows, so a multi-window restore
under memory pressure becomes sequential rather than a simultaneous blast.

## 5. Relationships with existing PP systems

- **CETTG (pp_dataset XI).** MWC is the layer above CETTG. CETTG already restores the
  terminal topology *of one window*; MWC tells CETTG *which* windows to act on and in what
  order, then composes the per-window results. MWC inherits CETTG's clean-vs-crash and
  no-loss doctrines and applies them at the window granularity.
- **UI / Editor State Persistence Layer (Dataset 01).** Per-window editor state is produced
  by Dataset 01; MWC aggregates these into the cross-window picture and ensures each window's
  editor surface is restored after its window is created and bound.
- **RW-OS (pp_dataset XIV).** MWC consumes RW-OS's resource-safe restore queue, auto-throttle
  levels and pane scheduler signals to decide whether windows restore in parallel or
  sequentially, and to pause window restore when stability is low. RW-OS governs *resource
  safety*; MWC governs *window correctness*; they compose.
- **CPC-OS (pp_dataset X, modules/cpc_os).** MWC extends CPC-OS's workspace-keyed manifests
  with an explicit window dimension, reusing CPC-OS identity and heartbeat rather than
  inventing a parallel one.
- **Incremental Snapshot & Session Versioning Engine (Dataset 03).** MWC's census is one of
  the things ISVE versions, so the Owner can restore not just the last window arrangement
  but a previous one.
- **Recovery Telemetry & Diagnostics (Dataset 05).** MWC emits window-level recovery events
  (window restored, blocked, manual-required) into the telemetry layer for observability and
  trend detection.
- **PP Sessions extension (extension/).** The extension is per-window; MWC is the
  cross-window brain that the per-window extension instances report into and receive restore
  direction from.

## 6. Entities that compose the system

### 6.1 Window Registry
Purpose: the durable inventory of Cursor windows. Inputs: window open/close/bind events from
each window's extension instance and from CPC-OS bootstrap. Outputs: a record per window
naming its stable window identity, host workspace path, display/monitor placement hint,
foreground flag and last-stable timestamp. Behaviour: written on every window lifecycle
event, not only at shutdown, so a crash finds a current census. Success: the registry's
window count and bindings match the real arrangement at the last stable point. Failure: a
window whose binding cannot be resolved is retained as recovery-pending, never deleted.
Evolution: grows to record monitor geometry as fidelity rises.

### 6.2 Cross-Window Topology Engine
Purpose: compute the relationship graph among windows — which existed together, which was
foreground, any declared relationships (a reference window paired with a work window).
Inputs: the registry plus relationship hints. Outputs: a cross-window topology description.
Behaviour: composes per-window CETTG and Dataset 01 descriptions into one whole-session
picture. Success: the topology reproduces the count, bindings and foreground of the last
stable arrangement. Failure: an inconsistency (two windows claiming foreground) is resolved
deterministically and reported. Evolution: learns richer inter-window relationships.

### 6.3 Window Identity Resolver
Purpose: assign each window an identity that survives restart. Inputs: workspace path,
durable per-window markers, registry history. Outputs: a stable window identity decoupled
from PID/handle. Behaviour: after a crash or reboot it never trusts prior process handles;
it re-derives identity from durable signals. Success: the same logical window is recognised
across the crash boundary. Failure: when identity is genuinely ambiguous (two windows on the
same workspace), it disambiguates by durable secondary markers and, failing that, marks the
pair manual-required. Evolution: strengthens markers to reduce ambiguity.

### 6.4 Window-to-Workspace Binding Engine
Purpose: guarantee each restored window opens the correct repository/folder. Inputs: registry
bindings. Outputs: a verified binding per window-to-restore. Behaviour: validates that the
bound workspace path still exists; flags missing paths rather than opening a wrong or empty
window. Success: each window reopens on its exact prior workspace. Failure: a missing
workspace yields a blocked-with-reason window and a manual instruction, never a silent
substitution. Evolution: supports moved/renamed workspace detection.

### 6.5 Window Restoration Orchestrator
Purpose: decide the order and parallelism of window restoration and drive it. Inputs: the
topology, dependency hints, and RW-OS resource/throttle signals. Outputs: an ordered restore
plan over windows, marking which may proceed in parallel. Behaviour: restores higher-priority
or prerequisite windows first; collapses to sequential restore under memory pressure;
delegates each window's interior to CETTG and Dataset 01 once the window exists and is bound.
Success: all census windows reach a terminal restore state in a safe order. Failure: a window
whose interior restore fails is marked and does not block unrelated windows. Evolution:
gains dependency-graph awareness as inter-window relationships are modelled.

### 6.6 Focus Arbitration Engine
Purpose: ensure exactly one window is foreground after restore — the one that held focus.
Inputs: the foreground flag from the topology. Outputs: a single foreground designation.
Behaviour: applies foreground only after all windows are created so it is not overwritten by
later window creation. Success: the Owner lands in the pre-crash foreground window. Failure:
if the foreground window is unrestorable, focus degrades to the highest-priority restored
window and the change is reported. Evolution: extends to per-monitor foreground when
multi-display geometry is modelled.

### 6.7 Cross-Window Lock Coordinator
Purpose: prevent two windows from claiming the same conversation, pane or workspace lock
during concurrent restore. Inputs: the locks recorded by CETTG/CPC-OS per window. Outputs: a
serialized lock-acquisition order across windows. Behaviour: a conversation or pane may be
owned by exactly one window; if two windows' restores would both claim it, the coordinator
grants it to the rightful owner per the census and blocks the other with a reason.
Success: no duplicate conversation/pane ownership after multi-window restore. Failure: a
genuine conflict is surfaced as manual-required rather than resolved by guesswork. Evolution:
integrates with repo_coordinator (W-series) for repository-level exclusivity.

### 6.8 Window Lifecycle Event Channel
Purpose: carry window-level events — opened, closed-cleanly, moved, merged, foreground-
changed, restored, blocked — to consumers (telemetry, versioning, the registry itself).
Inputs: host window events via the extension. Outputs: a stream of secret-safe lifecycle
events. Behaviour: distinguishes intentional clean close (which reduces the expected census)
from crash disappearance (which preserves the window for recovery), mirroring CETTG's pane
semantics at the window level. Success: every window state change is observable downstream.
Failure: a dropped or ambiguous event degrades to a reconciliation pass against the registry.
Evolution: unifies with RW-OS crash-replay so window events join the replay timeline.

## 7. Completion criteria for the system

MWC is complete when: the registry maintains an accurate, durable, PID-free census of windows
and their workspace bindings, updated on lifecycle events; the topology engine reproduces
count, bindings and foreground for the last stable arrangement; multi-window restore is
ordered, resource-aware and conflict-free, delegating each window's interior to CETTG and
Dataset 01; exactly one foreground window results; every census window ends in an explicit
restored/skipped/manual/blocked state with no silent loss; and all records are secret-safe.
An MWC that restores windows but lets two claim one conversation, or that restores the wrong
foreground, or that loses a secondary window, is incomplete.

## 8. Dependencies

MWC requires: a stable window-identity substrate (shared with CETTG/Dataset 01); the
per-window interior restorers (CETTG for terminals, Dataset 01 for editor); RW-OS resource
and throttle signals for safe sequencing; the redaction bus for secret-safe records; and the
PP Sessions extension as the per-window agent it directs. It consumes the crash-confidence
verdict but does not produce it.

## 9. Explicit anti-patterns

MWC must never: trust PIDs, window handles or live process counts to determine how many
windows existed (invalid after crash/reboot); restore all windows simultaneously under memory
pressure (it must honour RW-OS sequential restore); allow two windows to claim the same
conversation, pane or lock; open a window on a wrong or empty workspace when the bound path
is missing (it must block-with-reason instead); silently drop a secondary window because only
the last-focused one is "obviously" wanted (the explicit reason CETTG was built — never
restore only the last session); apply foreground before all windows exist; or duplicate
CETTG/Dataset 01 logic by restoring window interiors itself. It must also never reduce the
expected window census on a crash disappearance — only an intentional clean close may do that.

## 10. Future evolution

MWC evolves from a flat window census toward a modelled inter-window relationship graph
(reference-and-work pairs, monitor-anchored layouts, declared window roles), enabling
restores that re-create not just the windows but their *spatial and functional* arrangement
across displays. It deepens its integration with RW-OS so window scheduling and resource
governance become one decision surface, and with ISVE so the Owner can roll an entire
multi-window arrangement back to a prior version. The long-horizon goal is that the unit of
recovery becomes the Owner's whole operational board — every window, every terminal, every
editor surface — restored as one coherent whole after any crash, making a catastrophic OOM
reboot indistinguishable from a deliberate Reload Window across the entire session.
