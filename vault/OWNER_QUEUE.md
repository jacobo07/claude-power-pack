# OWNER_QUEUE -- pending Owner-side activations

Items the agent prepared but cannot self-activate (HR-001: no writes to
`~/.claude/hooks`, `~/.claude/settings.json`, or commands). Each item is
copy-paste-ready. Kept in the repo (versioned, durable); the agent updates it,
the Owner executes. Newest-relevant first.

---

## 1. Activate recovery graceful-beacon  (SCS C83)  [PENDING]

**System:** `hooks/session_end_graceful_beacon.js`
**Why:** without it, `power_beacon.classify_startup` reads EVERY shutdown as
`ungraceful-shutdown` (the active beacon is never overwritten). The beacon makes
the graceful-reopen vs ungraceful-shutdown distinction real.
**Runbook (full):** `vault/plans/recovery-beacon-activation-2026-07-10.md`

```powershell
# Paso 1: mirror canonical -> live
Copy-Item "C:\Users\User\.claude\skills\claude-power-pack\hooks\session_end_graceful_beacon.js" "$env:USERPROFILE\.claude\hooks\session_end_graceful_beacon.js" -Force
# Paso 2: anadir al array "SessionEnd" de ~/.claude/settings.json:
#   { "hooks": [ { "type": "command",
#     "command": "\"/c/Program Files/nodejs/node.exe\" \"C:/Users/User/.claude/hooks/session_end_graceful_beacon.js\"",
#     "timeout": 5000 } ] }
# Paso 3: /restart
```
**Verify:** `Test-Path "$env:USERPROFILE\.claude\hooks\session_end_graceful_beacon.js"` -> True;
after a clean close `power_beacon.json` shows `"kind": "graceful"`.

---

## 2. Surface the Recovery Accuracy Score  (G4/G5 orphans)  [PENDING -- needs wiring]

**Systems:** `modules/session_resilience/reentry.py` (G5) + `acceptance.py` (G4)
+ `integration.py` (I1/I2). All built + unit-tested but with **0 runtime callers**
(orphaned). The score (RECOVERED/PARTIAL/FAILED + fidelity) is computed by
`reentry.record_reentry`, which is never invoked at startup.
**Why it is not a 1-line copy:** the verdict is only meaningful on an *ungraceful*
startup AND needs the live-terminal count (which a bare python hook cannot read;
the extension/hub knows it). So activation = a SessionStart wire that passes the
live-terminal count into `reentry.py`, not just a Copy-Item.
**Owner options:**
- (a) run manually to inspect after an ungraceful boot:
  ```powershell
  $env:PYTHONPATH="C:\Users\User\.claude\skills\claude-power-pack"; python -m modules.session_resilience.reentry --state-dir "$env:USERPROFILE\.claude\state" --live-terminals 0
  ```
  (prints the G4 verdict + G5 event for the current pane_map).
- (b) full activation: extend `hooks/session_start_hub.js` (canonical) to call
  `classify_startup` -> `record_reentry` and log the verdict, then Copy-Item the
  hub to `~/.claude/hooks/` + `/restart`. This is an Owner-gated canonical edit
  (the hub already writes the active beacon at line ~447; the verdict-read side
  belongs next to it). Prerequisite: item 1 (graceful beacon) live, else every
  boot reads ungraceful and the score is noisy.
**Note:** depends on item 1. Do item 1 first.

---

## 3. Prerequisite mirrors (if not already done)

- `hooks/hook-dispatcher.js` canonical->live (FIOS token_irr drift):
  `vault/plans/fios-dispatcher-resync-2026-07-10.md`.
- The `pp-snapshot-writer` 15-min task now sources `--pane-map` automatically on
  its next cycle (no Owner action); to apply immediately:
  `powershell -File tools\snapshot_auto_writer.ps1 -Action run`.

---

## 4. Register PP-LivenessCheck daily task  (D1 Liveness Ledger)  [PENDING]

**System:** `modules/liveness/liveness_ledger.py`
**Why:** D1's `vault/audits/liveness_report.md` only refreshes on a manual run
without a scheduler. A daily task keeps the post-ship liveness verdict current so a
component that goes silent (a Stop-chain that stopped firing, a drifted dispatcher)
surfaces within a day instead of on the next incident.

```powershell
Register-ScheduledTask -TaskName 'PP-LivenessCheck' -Force `
  -Trigger (New-ScheduledTaskTrigger -Daily -At 9am) `
  -Action (New-ScheduledTaskAction `
    -Execute 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe' `
    -Argument 'C:\Users\User\.claude\skills\claude-power-pack\modules\liveness\liveness_ledger.py --report')
```
**Verify:** `Get-ScheduledTask -TaskName PP-LivenessCheck` -> State Ready; after it
runs, `vault/audits/liveness_report.md` mtime is same-day. Remove the `[PENDING]`
tag above once registered (the engine flips the row done on re-ingest).
