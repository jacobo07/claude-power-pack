# Session Resilience OS — Dataset 06 — Power Transition & Wake Recovery Engine (PTWRE)

**Family:** Session Resilience OS (Path A, residual-gap family — G6 EXTEND of the existing parent)
**Gap closed:** G6 — power-event continuity (sleep, wake, hibernate, battery↔AC, reboot, update,
ungraceful power loss), absent from every existing system. The family handled *crash* and *OOM*;
it never modelled the *power lifecycle* that precedes most real-world session loss.
**Depends on:** Crash-to-Exact-Terminal-Topology Guarantee (pp_dataset XI / CETTG),
CPC-OS (pp_dataset X, `modules/cpc_os`), UI / Editor State Persistence Layer (Dataset 01 / UESPL),
Multi-Window Coordinator (Dataset 02 / MWC), Incremental Snapshot & Session Versioning Engine
(Dataset 03 / ISVE), Recovery Acceptance Framework (Dataset 04 / RAF), Recovery Telemetry &
Diagnostics Layer (Dataset 05 / RTDL), RAM Stewardship OS (pp_dataset XII / RS-OS),
Resilient Workbench OS (pp_dataset XIV / RW-OS), and the `/resume v3` topology spec (Lazarus v3).
**Does NOT duplicate:** RAM/OOM detection and memory governance (owned by RS-OS); terminal pane
topology capture and restore (owned by CETTG); graceful-shutdown quiescence and the restore queue
(owned by RW-OS); editor-surface capture (owned by UESPL); delta storage (owned by ISVE). PTWRE
*orchestrates* those systems across power boundaries; it re-implements none of them.

---

## 1. System name and exact purpose

The Power Transition & Wake Recovery Engine is the system responsible for treating every machine
power event as a first-class, individually-contracted recovery scenario rather than as an
undifferentiated "crash". The existing family answers two questions extremely well: "what do we do
when the process dies for lack of memory?" (RS-OS) and "what do we do when the terminals and editor
are gone and we must rebuild the board exactly?" (CETTG + UESPL + MWC). Neither answers the question
the Owner actually lives with most often: "I closed the laptop lid, carried it to another room,
opened it, and it froze, powered off, rebooted, and came back to an empty Home screen with all my
panes gone." That sequence is not an out-of-memory crash and it is not a clean shutdown. It is a
*power transition* — specifically a sleep attempt that failed into an ungraceful power loss — and
until now no system in the family owned it.

PTWRE exists to make the outcome of a power transition deterministic and, wherever the host permits,
indistinguishable from a Reload Window. Its purpose is to (a) classify which power event actually
happened, because sleep, hibernate, reboot, update-restart and ungraceful power loss each demand a
different response; (b) guarantee that a durable, whole-session snapshot exists *before* the machine
suspends or loses power, so there is always something to restore; (c) reconcile the world on wake,
detecting what survived and what must be rebuilt; and (d) drive the existing restore machinery
(CETTG, UESPL, MWC, ISVE) in the correct order with no double-restoration and no silent loss. It is
the engine that turns "I lost my panes again" into "the workbench came back the way I left it,
without my doing anything."

## 2. Fundamental property guaranteed

After any power transition — graceful sleep and wake, hibernate enter and resume, battery-to-AC and
AC-to-battery changes, a deliberate reboot, a host or extension update-restart, or an ungraceful
power loss following a failed sleep — the workbench either returns to its last stable pre-transition
state with no Owner intervention, or, where the host technically cannot, the divergence is detected,
reported and reduced to the closest achievable approximation rather than silently abandoned to the
Home screen. The property has a hard precondition that PTWRE itself enforces: a durable snapshot of
the whole session must always exist no older than the last stable change, because no recovery system
can restore a state it never captured. PTWRE's first duty is therefore the existence of that
snapshot; its second is the correctness of the restore that consumes it.

This property explicitly subsumes the Owner's recurring failure mode. A lid-close that degrades into
a freeze-then-power-off is, after the fact, indistinguishable at the disk level from a reboot: every
terminal PTY is dead, the editor handles are invalid, and Cursor's own hot-exit state may never have
been flushed because the suspend never completed cleanly. PTWRE guarantees that this case is detected
as an *ungraceful* transition and routed to a full PP-driven workspace reentry, instead of being left
to Cursor's native restore — which, having nothing flushed to restore, falls back to the Home/Agents
screen.

## 3. Contracts offered to consumers

PTWRE offers per-event Recovery Contracts. Each names what it promises under normal conditions, what
it promises under degraded conditions, and — in the spirit of CETTG's honesty doctrine — what it can
never guarantee.

- **Sleep Contract.** Normal: before the machine suspends, the latest whole-session snapshot is
  durable on disk and a clean-exit-vs-suspend beacon records that a *suspend* (not a quit) is in
  progress. Degraded: if the suspend grace window is too short to flush a fresh snapshot, the most
  recent prior durable snapshot is guaranteed to already exist (because PTWRE keeps the continuous
  cadence non-empty), so the loss is bounded to the last delta, never the whole session. Never: it
  cannot extend the OS-granted suspend window, so it never blocks the machine from sleeping.
- **Wake Contract.** Normal: on resume, surviving terminals are reattached, dead ones are re-spawned
  via `--resume`, and the editor surface is reconciled against the snapshot. Degraded: if some
  conversations cannot be reattached, each is surfaced individually with its exact resume command,
  never collapsed into a generic "history restored". Never: it cannot revive a PTY whose host pty
  process the OS reaped during suspend — that pane is rebuilt, not resurrected.
- **Battery→AC / AC→Battery Contract.** Normal: capture cadence adapts (conserve on battery, resume
  full cadence on AC) while always keeping one durable snapshot current. Never: it does not touch the
  OS power plan; it governs only PP's own capture behaviour.
- **Hibernate Contract.** Normal: a hibernate-resume in which Cursor's own process image survived
  triggers *no* PP restore (avoiding double-restore); a hibernate that the host could not honour and
  degraded into power loss is treated as ungraceful. Never: it cannot guarantee the OS actually wrote
  a valid hibernation image — it detects which case occurred and acts accordingly.
- **Reboot Contract.** Normal: a deliberate reboot loses all volatile state by definition, so PTWRE
  performs a full PP-driven reentry from the last durable snapshot. Never: it cannot recover work
  that was never snapshotted before the reboot command was issued.
- **Update Contract.** Normal: a Cursor or extension update-restart re-arms PP's hooks and heartbeat,
  verifies the snapshot chain survived the version bump, and lets Cursor's own preserved workspace
  intent stand (an update is not a reboot). Never: it cannot repair a breaking host change to the
  underlying state schema; it detects and reports such a break.
- **Ungraceful-Loss Contract.** Normal: a startup following a detected ungraceful power loss triggers
  Cold-Start Workspace Reentry, restoring the last known windows, panes and editor surfaces. Degraded:
  if only a partial snapshot exists, the recoverable subset is restored and the gap is reported.
  Never: it cannot restore state that the failed suspend never flushed beyond the last durable delta.

## 4. Responsibilities — what it does and what it does NOT do

PTWRE **does**: subscribe to OS power-event signals and classify each into a precise transition
class with a confidence; maintain the always-non-empty durable snapshot invariant by coordinating
ISVE deltas against CETTG/UESPL/MWC captures; write and read the clean-exit-vs-suspend beacon; detect
ungraceful shutdown from the absence of a graceful-exit beacon combined with corroborating power-log
evidence; classify startup intent (first-run, graceful-reopen, post-sleep, post-hibernate,
post-update, post-ungraceful); drive Cold-Start Workspace Reentry through the existing restore path
(CPC-OS `restore_panes` + pane_map + MWC restoration order) only when native restore did not already
succeed; adapt capture cadence to the power source; and emit every transition and reconciliation
verdict to RTDL.

PTWRE **does NOT**: detect or govern memory pressure (RS-OS owns OOM — power loss and OOM are sibling
failure modes, not the same event); capture terminal topology or editor surfaces itself (it asks
CETTG and UESPL for those); store snapshot history (ISVE owns the chain); decide whether a restored
session is *acceptable* (RAF owns the verdict — PTWRE feeds it the reconciliation result); change OS
power settings or the user's power plan; or re-open windows when Cursor's native restore already
returned them correctly. PTWRE is an *orchestrator across power boundaries*, deliberately holding no
capture, no storage and no acceptance logic of its own so that each neighbouring system keeps exactly
one concern.

## 5. Relationships with existing PP systems

- **CETTG (pp_dataset XI).** PTWRE consumes CETTG's terminal-topology description as the terminal
  half of every snapshot it flushes before suspend, and invokes CETTG's restore ordering during
  reentry. It adopts CETTG's clean-close-vs-crash semantics and extends them with the finer
  power-event taxonomy (CETTG sees "crash"; PTWRE sees "sleep that failed into power loss").
- **UESPL (Dataset 01).** PTWRE folds UESPL's editor-surface description into the same durable
  snapshot so a wake restores tabs, order, focus, scroll, panels and splits, not only terminals.
- **MWC (Dataset 02).** PTWRE uses MWC's cross-window census and restoration order so a multi-window
  workbench returns as a coordinated whole after reentry, in the resource-safe sequence MWC defines.
- **ISVE (Dataset 03).** PTWRE relies on ISVE's cheap delta capture to keep the snapshot current
  within the suspend grace window; flushing a full snapshot on every sleep would be too slow, so the
  continuous delta chain is what makes the always-non-empty invariant affordable.
- **RAF (Dataset 04).** After a wake or reentry, PTWRE hands its reconciliation result to RAF, which
  renders the session-level "was recovery successful?" verdict and gates completion.
- **RTDL (Dataset 05).** PTWRE is a telemetry *producer*: every transition, beacon state and
  reconciliation outcome flows to RTDL through the redaction bus, extending recovery observability
  from crashes to the full power lifecycle.
- **RS-OS (pp_dataset XII).** Sibling, not overlap. RS-OS owns memory pressure and OOM; PTWRE owns
  power transitions. They meet only at the shared snapshot substrate, which both feed.
- **RW-OS (pp_dataset XIV).** RW-OS owns *graceful* quiescence and the restore queue. PTWRE's
  pre-suspend flush is the *power-triggered* sibling of RW-OS quiescence and reuses the restore queue
  rather than building a second one.
- **CPC-OS (pp_dataset X, `modules/cpc_os`).** PTWRE enters and exits through CPC-OS's snapshot entry
  point and `restore_panes` path; it adds power-event awareness on top, never a competing loop.
- **`/resume v3` (Lazarus v3) + NAMED_RECOVERY_INDEX.** When reentry must surface conversations for
  the Owner to pick, PTWRE uses the existing topology picker and the descriptive named index rather
  than inventing a new selection surface.

## 6. Entities that compose the system

### 6.1 Power Event Taxonomy Classifier
Purpose: convert raw OS power signals into a single, precise transition class. Inputs: OS suspend/
resume notifications, power-source-change notifications, session-end and startup signals, and the
power-event log. Outputs: a classified event (sleep, wake, hibernate-enter, hibernate-resume,
battery→AC, AC→battery, reboot, update-restart, ungraceful-loss) with a confidence. Behaviour: it is
the root every other entity keys off; an ambiguous signal is classified to the *safer* class (when
unsure between hibernate-resume and ungraceful-loss, it prefers ungraceful-loss so recovery runs
rather than being skipped). Success: each real-world transition maps to the class that triggers the
correct contract. Failure: a misclassification is caught downstream by the two-signal rule before any
destructive action. Evolution: learns host-specific signal quirks over time.

### 6.2 Pre-Suspend Quiescence Flusher
Purpose: guarantee a durable whole-session snapshot exists before the machine suspends or loses power.
Inputs: an imminent-suspend signal (where the OS provides one) and the continuous ISVE delta cadence.
Outputs: a flushed, durable snapshot plus a recorded flush timestamp. Behaviour: because many power
losses give no warning, it does not rely solely on the imminent-suspend signal — it keeps the ISVE
delta chain continuously durable so that even a zero-warning power-off loses at most the last delta.
When a suspend signal does arrive, it forces one final delta flush within the grace window. Success:
a non-empty durable snapshot always exists at suspend time. Failure: if the grace window is too short,
the prior durable snapshot still stands and the bounded loss is reported. Evolution: tunes its flush
budget to observed grace-window lengths per host.

### 6.3 Wake Reconciliation Engine
Purpose: on resume, determine what survived and what must be rebuilt. Inputs: the post-wake live
state (which PTYs are alive, which windows exist, clock delta, network and volume status) and the
last durable snapshot. Outputs: a reconciliation plan (reattach / re-spawn / rebuild per element) and
a verdict for RAF. Behaviour: it diffs live-vs-snapshot rather than blindly restoring, so surviving
panes are reattached and only missing ones are re-spawned — this is what prevents the duplicate-pane
class of bug. Success: the post-wake workbench equals the pre-sleep workbench. Failure: any element
it cannot reconcile is surfaced individually with its exact recovery action, never silently dropped.
Evolution: widens the set of inconsistencies it can detect (e.g. changed external monitors).

### 6.4 Battery / AC Policy Adapter
Purpose: adapt PP's capture behaviour to the power source. Inputs: power-source-change events.
Outputs: a cadence directive to ISVE/CPC-OS. Behaviour: on AC→battery it conserves (lower-frequency
capture, but always at least one current durable snapshot, because battery often precedes sleep);
on battery→AC it restores full cadence. Success: capture continuity is preserved without needlessly
draining the battery. Failure: if it cannot read the power source, it defaults to the safer full
cadence. Evolution: incorporates battery-level thresholds, not just source state.

### 6.5 Hibernate / Reboot / Crash Discriminator
Purpose: separate three post-hoc-identical-looking states that demand opposite responses. Inputs: the
classified event, the beacon state and OS hibernation-image evidence. Outputs: a routing decision
(no-op for a clean hibernate-resume, full reentry for a reboot, defer-to-CETTG/RS-OS for a crash).
Behaviour: prevents both double-restore (acting when Cursor already restored itself) and under-restore
(skipping when nothing survived). Success: exactly one restore path runs per transition. Failure: an
indeterminate case is routed to reentry with a reconcile-first plan so a no-op is still possible.
Evolution: improves hibernation-image detection per host.

### 6.6 Ungraceful-Shutdown Detector
Purpose: detect that the last shutdown was not graceful — the engine behind the Owner's Home/Agents
symptom. Inputs: the presence/absence and freshness of a graceful-exit beacon, stale session locks,
and the power-event log. Behaviour: a graceful close writes a fresh exit beacon; on startup, a missing
or stale beacon *combined with* corroborating power-log evidence (the two-signal rule, per the ACV
stale-marker lesson — a single signal is a known foot-gun for destructive ops) marks the prior
shutdown ungraceful. This is the precise signal that Cursor's native hot-exit/restoreWindows likely
has nothing to restore. Success: a freeze-then-power-off is reliably distinguished from a clean quit.
Failure: when signals conflict it errs toward "ungraceful" so reentry runs. Evolution: adds further
corroborating signals (e.g. last-heartbeat age) to raise confidence.

### 6.7 Cold-Start Workspace Reentry / Startup-Intent Router
Purpose: classify startup intent and, when warranted, re-open the last known workbench — folding the
Home/Agents auto-detect that the Reality Scan determined is *not* a config gap (the settings are
already correct) but a residual of unflushed state after ungraceful loss. Inputs: the startup-intent
classification and whether Cursor's native restore already returned the expected windows. Outputs: a
reentry action (or a deliberate no-op). Behaviour: it fires reentry *only* when an ungraceful shutdown
was detected and native restore did not already produce the workspace — driving CPC-OS `restore_panes`
+ pane_map + MWC order. It explicitly records that the configuration precondition
(`workbench.startupEditor:"none"`, `window.restoreWindows:"all"`, persistent sessions on, automatic
tasks off, hot-exit on) is already satisfied, so it handles only the case configuration alone cannot:
power loss before flush. Success: after an ungraceful loss the Owner lands in their workbench, not on
Home. Failure: if reentry cannot fully rebuild, it restores the recoverable subset and surfaces the
rest. Evolution: moves from a startup check toward a guarded, continuous restorer that diffs pane_map
against live terminals (the follow-up already named in `docs/cursor-startup-and-reload.md`).

### 6.8 Update Recovery Contract Engine
Purpose: handle host/extension update-restarts as their own class. Inputs: a detected version change
across restart. Outputs: a re-arm action for PP hooks/heartbeat plus a snapshot-chain integrity check.
Behaviour: treats an update as preserving Cursor's own workspace intent (so it does not force a reboot-
style reentry) while verifying PP's substrate survived the bump. Success: after an update the Owner's
workbench and PP recovery are both intact. Failure: a breaking schema change is detected and reported
as host-owned, not silently swallowed. Evolution: tracks known-breaking Cursor versions.

### 6.9 Power Transition Telemetry Bridge
Purpose: extend recovery observability to power events. Inputs: every classified event, beacon
transition and reconciliation verdict. Outputs: redacted telemetry records to RTDL. Behaviour: routes
all emissions through the redaction bus (HR-SECRET family) before persistence. Success: the Owner can
later see exactly which power events occurred and how each recovered. Failure: a telemetry write
failure never blocks recovery — observability is best-effort, recovery is not. Evolution: feeds
anomaly detection so a recurring failed-sleep pattern surfaces proactively.

## 7. Completion criteria for the system

PTWRE is complete when: every transition class in 6.1 is detected and routed to its contract in
section 3; the always-non-empty durable snapshot invariant holds such that no power loss costs more
than the last delta; a wake reconciles live-vs-snapshot with no duplicate panes and no silent drops;
an ungraceful shutdown is detected by the two-signal rule and triggers Cold-Start Reentry that lands
the Owner in their workbench rather than on Home/Agents; a clean hibernate-resume and a successful
native restore both correctly produce a no-op; update-restarts re-arm PP without a reboot-style
reentry; and every transition is observable in RTDL. A PTWRE that restores after a reboot but still
drops the Owner on Home after a failed-sleep power loss is incomplete by definition — that is the
exact case it exists to close.

## 8. Dependencies

PTWRE requires: OS power-event signals (or, where absent, the continuous-cadence fallback that makes
zero-warning loss survivable); the snapshot substrate and entry point (CPC-OS / ISVE); the capture
producers (CETTG terminals, UESPL editor, MWC windows); the restore path (CPC-OS `restore_panes`,
pane_map, MWC ordering); the acceptance verdict (RAF); the telemetry sink and redaction bus (RTDL /
URB); and a durable beacon location for the clean-exit-vs-suspend signal. It does not require RS-OS to
function, but power loss and OOM share the snapshot substrate, so the two compose cleanly.

## 9. Explicit anti-patterns

PTWRE must never: double-restore (fire Cold-Start Reentry when Cursor's native restore already
returned the workbench, or act on a clean hibernate-resume) — the duplicate-pane bug is the canonical
failure here; block or delay the OS suspend by holding the grace window hostage to a long flush (a
flush killed mid-write corrupts the snapshot — bound the flush, keep the prior snapshot as the floor);
assume PTY or PID continuity across a power loss (handles are invalid after resume, exactly as CETTG
holds for crashes); trust `window.restoreWindows` alone after a detected ungraceful shutdown (that is
precisely when native restore has nothing to restore); act on a single stale-marker signal (the
two-signal rule is mandatory before any reentry that re-spawns processes); over-capture on battery and
drain the very power the Owner is conserving; treat an update-restart as a reboot (which would discard
Cursor's own preserved workspace intent); or convert a telemetry failure into a recovery failure
(observability is best-effort, recovery is the invariant). It must also never re-implement OOM
detection, terminal capture, editor capture, delta storage or the acceptance verdict — it orchestrates
the systems that own those, and owns only the power-boundary logic.

## 10. Future evolution

PTWRE evolves along three axes. First, from discrete startup checks toward a *guarded continuous
restorer* that diffs pane_map against live terminals by working directory and re-spawns only where no
terminal exists — the follow-up already named in `docs/cursor-startup-and-reload.md`, which would let
cold starts auto-restore without reintroducing reload duplication. Second, from reactive detection
toward *predictive* power handling: a recurring failed-sleep pattern surfaced by the telemetry bridge
could pre-flush more aggressively when the lid-close-then-carry pattern is recognised. Third, from
best-effort host application toward a *host-capability registry* (shared with UESPL) that records, per
Cursor version, exactly which power-resume behaviours the host honours, so the unrestorable-marking
contract becomes data-driven rather than discovered at wake time. The long-horizon goal is that the
single most common real-world session-loss event the Owner experiences — close the lid, move, reopen,
freeze, reboot — ends not with an empty Home screen but with the workbench exactly as it was left,
with no action required, the same guarantee CETTG already gives the terminal half of a crash.
