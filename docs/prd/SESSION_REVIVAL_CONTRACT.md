# Session Revival Contract v1.0

**Status:** active | **Sealed:** 2026-07-19 | **Owner:** Jacobo
**Spec:** [`docs/specs/REVIVAL_PIPELINE_SPEC.md`](../specs/REVIVAL_PIPELINE_SPEC.md)
**Gate:** `python tools/test_session_revival.py`

---

## 1. Problem

Cursor session revival was inconsistent across many attempts. The reported
symptom, verbatim:

> "revivía el historial correcto pero me mandaba a escribir a una sesión nueva
> y vacía"

A pane came back showing the *right* conversation, but typing went into an
empty new session. Earlier fixes (`task.allowAutomaticTasks`,
`window.restoreWindows`, a kclaude wrapper split-brain fix) each addressed a
real defect yet the symptom survived, because **three independent causes were
in play and each fix removed only one**.

### Cause A — Cursor repaints a corpse (the reported symptom)

`terminal.integrated.persistentSessionReviveProcess` was `onExitAndWindowClose`.
Cursor's own description: this decides when session *"contents/history should be
restored **and processes be recreated**"*. On a full quit the original process
is gone, so Cursor repaints the old **scrollback** and starts a **brand-new
shell underneath it**. The visible history belongs to a dead session; the live
process is a newborn. Exactly the reported symptom.

It also *doubled* panes: the `.vscode/tasks.json` `folderOpen` task opened a
real dedicated terminal for the same session, so the ghost and the real tab
coexisted.

Compounding it, `terminal.integrated.restoreTerminals: false` was set as a
guard — but **that setting does not exist** (0 occurrences in Cursor's
`workbench.desktop.main.js`). It was inert and made terminal restore *appear*
disabled while it was fully active.

### Cause B — two writers, two policies, one file

Two components maintained the same `.vscode/tasks.json`:

| Writer | Trigger | Source | Liveness policy |
|---|---|---|---|
| SessionStart hub | every session open | `session_snapshot.json` | **none** |
| `pp-snapshot-writer` | every 15 min | `pane_map.json` | tier + sub-agent filter |

Both call `merge_tasks`, which **replaces every CPC task**. So the file's
contents depended on which writer ran last — the mechanical source of
"sometimes it works". `snapshot._LIVE_STATUSES` includes `"stale"`, so the hub
emitted `folderOpen` tasks for sessions abandoned days earlier.

### Cause C — the resurrection loop

Cursor fires *every* `folderOpen` task on open. Each stale task ran
`kclaude --resume <dead sid>`; that relaunch **re-registered the sid as a fresh
pane**, which put it back in `session_snapshot.json`, which regenerated the same
task. `PaneRegistry.prune_stale()` could never reclaim it because every
folder-open reset its heartbeat.

Proven live 2026-07-19: sid `db5cb9f7` (clean_exit **2026-07-14**) was still
running as a resurrected zombie five days later, with its own `folderOpen` task.

---

## 2. Objective

Every pane that was **open when Cursor closed** returns as a real resumed
session, in its own terminal, whose visible history is that live session's
history. Nothing else opens.

## 3. Non-goals

- Restoring panes the Owner had already closed.
- Resurrecting sessions that were never open in the current Cursor lifetime.
- Changing `kclaude.ps1`'s bare-launch behavior. A bare `kclaude` opening a NEW
  session is **intended** (`T-KCLAUDE-LAUNCH-CONTEXT-001`), for parity with the
  native Claude button. Only an explicit `--resume` resumes.
- Recovering a session whose transcript no longer exists on disk.

## 4. Pane lifetime (Owner contract)

> "lo que dure Cursor es lo que dura una sesión de los panes que quiero
> recuperar"

**A pane's lifetime is Cursor's lifetime.** A pane open but untouched all day
must still return.

This forbids **recency** as the liveness test. An idle-but-open pane and an
abandoned corpse have identical elapsed times; only a process fact separates
them. A 120-minute ceiling was implemented, measured, and **rejected** — it
would have dropped three genuinely-open panes idle 2, 6 and 8 days
(`70e1c9fc`, `00400465`, `f0830618`).

## 5. Invariants

- **I1 — Open-ness is a process fact.** A pane is OPEN iff a kclaude beacon
  (`%TEMP%/kclaude-pane-<pid>.sid`) exists **and its PID is still running**.
  Never inferred from elapsed time or registry membership.
- **I2 — One definition, all writers.** Every `tasks.json` writer applies I1
  identically. Divergent policies over a shared file re-create Cause B.
- **I3 — Never drop the caller's own session.** A writer must pin its own sid
  (`keep_sids`). The live session is routinely marked `stale` and may have no
  beacon; a beacon-only gate drops the pane the Owner is typing in.
- **I4 — No transcript, no resume.** If `<sid>.jsonl` is absent, open a fresh
  session and **log the loss**; never silently substitute another conversation.
- **I5 — One task per live pane.** No repo accumulates duplicate or corpse
  `folderOpen` tasks.
- **I6 — Cursor does not compete.** `persistentSessionReviveProcess` stays
  `never`. PP owns cross-quit restore; ghost buffers are not restore.
- **I7 — Fail-open, never fail-closed.** If liveness cannot be measured, do not
  filter. Losing a pane is worse than keeping a stale one.

## 6. Acceptance gates

| Gate | Criterion |
|---|---|
| `V-REVIVAL-LIVENESS-IS-PROCESS` | A stale-status pane with no live PID is excluded; a live-PID pane is kept at any idle age |
| `V-REVIVAL-OWN-SESSION-PINNED` | `keep_sids` survives the gate even with no beacon |
| `V-REVIVAL-WRITERS-AGREE` | PowerShell and Python liveness sets are identical at the same moment |
| `V-REVIVAL-NO-DUPLICATE-FOLDEROPEN` | One task per distinct live session per repo |
| `V-REVIVAL-PID-NOT-OPENPROCESS` | Liveness rejects an exited-but-open-handle PID |
| `V-SETTINGS-REQUIRED` | `persistentSessionReviveProcess=never`, `enablePersistentSessions=true`, `allowAutomaticTasks=on`, `restoreWindows=all`, no `restoreTerminals` |
| `V-REVIVAL-FAIL-OPEN` | Zero measurable beacons ⇒ no filtering |

## 7. Scenarios

**Covered:** full quit + reopen; laptop reboot; window close with others open;
window reload (native pty reconnect, untouched by this work); crash.

**Not covered (with reason):**
- A session created <5 min before quit whose transcript has not flushed and
  which is not the hub's own sid — the pane_map cannot see it yet. Mitigated by
  I3 for the current pane.
- Panes launched by a route that does not write a beacon (a bare `claude`, not
  `kclaude`). Such panes are invisible to I1; they rely on the hub's `keep_sids`
  and content-age fallback.
- PID reuse. A recycled PID matching a stale beacon reads as live. Bounded and
  rare; a stale kept pane is the fail-open direction (I7).

## 8. Regression detection

`python tools/test_session_revival.py` (hermetic; safe to run any time).
`V-SETTINGS-REQUIRED` is the tripwire for
`T-CURSOR-UPDATE-RESETS-AUTOTASKS-001`: a Cursor update can silently reset these
keys, breaking revival with no visible error. **Run it after every Cursor
update** — see `OWNER_QUEUE`.

## 9. Review

Revisit when: Cursor changes terminal-persistence semantics; a new `tasks.json`
writer is added (must adopt I1/I2/I3 *before* shipping); or a pane is reported
lost or duplicated on restore.
