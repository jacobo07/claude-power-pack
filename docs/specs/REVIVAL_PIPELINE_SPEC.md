# Revival Pipeline Spec v1.0

**Status:** active | **Sealed:** 2026-07-19
**Contract:** [`docs/prd/SESSION_REVIVAL_CONTRACT.md`](../prd/SESSION_REVIVAL_CONTRACT.md)

Describes the pipeline **as verified on disk 2026-07-19**, not as originally
designed. Where the two differ, the observed behavior is authoritative.

---

## 1. Four entry points

A Claude pane can come into existence four ways. They are independent, and
conflating them has repeatedly produced misdiagnosis.

| # | Entry point | Fires when | Resumes? |
|---|---|---|---|
| 1 | `.vscode/tasks.json` `folderOpen` task | folder opens (needs `allowAutomaticTasks: on`) | **Yes** — explicit `--resume <sid>` |
| 2 | `"Last session"` terminal profile → `lazarus-shell-autoresume.ps1/.bat` | terminal created with that profile | Yes — FIFO / bindings / fallback resolver |
| 3 | `"Claude"` / `" kClaude"` profiles → `kclaude.ps1` | terminal created with that profile | **No — fresh by design** (`T-KCLAUDE-LAUNCH-CONTEXT-001`) |
| 4 | Cursor native terminal persistence | window reload, or (formerly) app quit | Reload: real pty reconnect. Quit: **buffer only** |

**#1 is the only guaranteed path across a full quit**, so any defect there is
maximally exposed in the Owner's most common scenario.

**#4 is not resume.** Cursor's setting description: it restores "contents/
history" *and recreates processes* — a NEW shell under OLD scrollback. On
reload it genuinely reconnects the live pty (a correct "History restored"); on
quit it repaints a corpse. Now disabled (`persistentSessionReviveProcess:
never`, invariant I6) so PP owns cross-quit restore.

## 2. Data flow (entry point #1)

```
kclaude.ps1  ──writes──▶  %TEMP%\kclaude-pane-<wrapperpid>.sid   [LIVENESS TRUTH]
                              │
SessionStart hub ──▶ PaneRegistry ──▶ snapshot.py ──▶ session_snapshot.json
                                                          │
PP-PaneMapUpdate (5 min) ──▶ build_pane_map.ps1 ──▶ pane_map.json
                                                          │
        ┌─────────────────────────────────────────────────┴────────┐
        │                                                          │
  SessionStart hub                                    pp-snapshot-writer (15 min)
  generate_from_snapshot(keep_sids={own})             generate_from_pane_map(--tiers)
        └──────────────────────┬───────────────────────────────────┘
                               ▼
                    .vscode/tasks.json  (merge_tasks: replaces ALL CPC tasks)
                               ▼
             Cursor folderOpen ──▶ kclaude.cmd --resume <sid>
```

Both writers apply the **same** liveness gate (invariant I2). They previously
did not, and since `merge_tasks` replaces all CPC tasks, the surviving set
depended on execution order — the mechanical cause of the inconsistency.

## 3. Component contracts

### `kclaude.ps1` — beacon producer
- **Writes** `%TEMP%\kclaude-pane-<wrapperpid>.sid` = `{sid, cwd, pid, ts}`.
- **Deletes** it on clean exit; a crash leaves it behind.
- **Therefore the file alone proves nothing.** 172 beacons were present against
  12 live panes. The PID must be verified running.
- Bare launch ⇒ new session, always. Only `--resume` resumes.

### Liveness test — the pipeline's keystone
Two implementations that **must agree** (I2):
- PowerShell: `tools/build_pane_map.ps1` — `Get-Process` PID set.
- Python: `modules/cpc_os/vscode_autorun.py::live_beacon_sids` / `_pid_alive`.

**`OpenProcess` alone is NOT a liveness test.** A terminated process keeps a
valid handle-table entry until every handle closes, so `OpenProcess` succeeds on
corpses. Measured: it reported 14 live where `Get-Process` saw 12; both extras
were exited. Python therefore gates on
`WaitForSingleObject(handle, 0) == WAIT_TIMEOUT`, which only signals after real
exit. Verified IDENTICAL at the same moment, twice.

*Failure mode:* PID reuse reads as live. Fail-open direction (I7).

### `build_pane_map.ps1` — four-tier classifier
- Tiers by **internal transcript timestamp** (content), never file mtime — a
  batch mtime-touch forges mtime liveness (`T-PANE-MAP-FALSE-LIVE-MTIME-001`).
- `OPEN-NOW` iff **live beacon** OR content newer than `LiveMinutes` (12).
- **Filters sub-agent transcripts** via `SUB_PREFIXES` — including any whose
  first user message is the local-command caveat. Consequence: such a session is
  invisible to this path entirely, at any tier. This is why `db5cb9f7` never
  appeared here and the pane_map path was wrongly exonerated during diagnosis.
- *Failure modes:* `%TEMP%` cleared ⇒ empty `$liveSids` ⇒ age-only fallback
  (fail-open). Unparseable timestamp ⇒ `PositiveInfinity` ⇒ ARCHIVE.

### `snapshot.py` / `PaneRegistry`
- `_LIVE_STATUSES = ("active", "stale", "paused")` — **stale panes are
  included by design**, because a lapsed heartbeat does not prove closure.
  Correct for a crash-recovery manifest, wrong as a task source: hence the
  liveness gate at the consumer, not a change here.
- `prune_stale(max_age_s=7200)` runs at SessionStart. **It cannot reclaim a
  resurrected pane** — each folder-open resets the heartbeat. Structural, not a
  bug in prune_stale.
- A pane is routinely `stale` while genuinely alive ⇒ invariant I3 exists.

### `vscode_autorun.py` — task writer
- `merge_tasks` preserves non-CPC tasks, replaces CPC ones (sentinel:
  `detail == "CPC-Restore autorun (pane_map label)"`). Idempotent.
- Backs up to `tasks.json.cpc-bak` before writing; skips write when unchanged.
- Panes without an explicit `--resume <sid>` are **empty shells** and emit no
  task (`BL-CPCOS-RESTORE-005`).
- `generate_from_snapshot(keep_sids=...)` — liveness gate ∪ caller's own sid.

### `.vscode/tasks.json`
- One task per live pane, `panel: "dedicated"` (own tab), `runOn: folderOpen`.
- Waves of 5 at 8 s (`T-FOLDEROPEN-STAMPEDE-001`); `&` not `&&` so a failed
  `timeout` still launches kclaude.
- **Requires `task.allowAutomaticTasks: "on"`** and a trusted workspace.

## 4. Protocol: session with no transcript

`lazarus-shell-autoresume.ps1` guards at the single egress point
(`BL-LAZ-STALE-001`): if `<sid>.jsonl` is missing, `claude --resume` prints "No
conversation found" and exits instantly, which also cancels in-flight SessionEnd
hooks. On a missing transcript it degrades to the fallback resolver rather than
attempting a doomed resume. Invariant I4: never substitute another
conversation — a missing chat is genuinely gone (`BL-CPCOS-RESTORE-002`).

Lost-session logging: `~/.claude/lazarus/autoresume_invocations.log`
(`ISO;sid;cwd`) records every attempt; the Lazarus `index.json` carries
per-session `status` (`clean_exit` / `crashed`).

## 5. Required configuration

| Key | Value | Why |
|---|---|---|
| `task.allowAutomaticTasks` | `"on"` | Without it **no** `folderOpen` task fires — total revival failure, silent |
| `terminal.integrated.persistentSessionReviveProcess` | `"never"` | Stops ghost-buffer tabs competing with real resumes (I6) |
| `terminal.integrated.enablePersistentSessions` | `true` | Genuine pty reconnect on **reload** — different mechanism, keep it |
| `window.restoreWindows` | `"all"` | Reopens the folders whose tasks then fire |

`terminal.integrated.restoreTerminals` **is not a Cursor setting** (0
occurrences in `workbench.desktop.main.js`). Present in config it is inert and
actively misleading — it reads as if terminal restore were disabled. Removed.

## 6. Diagnostic checklist

1. `python tools/test_session_revival.py` — settings + liveness + writer parity.
2. `.vscode/tasks.json` — one task per live pane? corpses? duplicates?
3. Beacons: count files vs PIDs alive (expect many dead — normal).
4. `%TEMP%\pp-snapshot-writer.log` — last cycle's per-repo task counts.
5. Cursor **Output → Tasks** — did `folderOpen` actually fire?
6. `~/.claude/lazarus/<project>/index.json` — is the sid `clean_exit`?

**Do not** diagnose from `pane_map.json` alone: `SUB_PREFIXES` filtering means a
real pane can be legitimately absent.
