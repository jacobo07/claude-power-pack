# OWNER_QUEUE -- pending Owner-side activations

Items the agent prepared but cannot self-activate (HR-001: no writes to
`~/.claude/hooks`, `~/.claude/settings.json`, or commands). Each item is
copy-paste-ready. Kept in the repo (versioned, durable); the agent updates it,
the Owner executes. Newest-relevant first.

---

## NEW (2026-07-22) -- CGF Workstream B: 15 PLANNED clusters registered (62 modules)

Liveness orphan disposition pass (`vault/audits/liveness_report.md`, 175->21 real
orphans). These 62 modules are built-per-spec but deliberately not yet composed
into a live authority -- `class: PLANNED` in `reachability_registry.json`, each
row below is its OWNER_QUEUE activation. None are urgent (no bug is caused by
the gap); this is the backlog the gap represents, made visible instead of silent.

### PLANNED: craif Phase 2 wiring  [PENDING]
**System:** `modules/craif/*`
**Why:** CRAIF Phase 1 (Failure Completeness axis) built; not yet composed into
a live consumer. Owner decides the Phase 2 integration point.

### PLANNED: cognitive_os CO-0x composition  [PENDING]
**System:** `modules/cognitive_os/{context,economics,gc,governor,guarantee_ledger,hibernate_runner,loop_budget,memory,rehydration}`
**Why:** 9 CO-00-series modules built per spec; `process_governor.py` (LIVE) does
not import any of them (verified by grep). Composing them is a real architecture
decision, not a 1-line wire.

### PLANNED: contract_fabric wiring  [PENDING]
**System:** `modules/contract_fabric/*`
**Why:** DAIF-04 Part XXI runtime; part of the DAIF corpus (SPEC, not a running
system per `project_daif_corpus_scs_c95.md`).

### PLANNED: DAIF corpus operationalization  [PENDING]
**System:** `modules/daif/*`
**Why:** confirmed SPEC-not-running-system. Next step per memory is "a proving
vertical" -- this is that same open item, now also visible in the liveness ledger.

### PLANNED: Dataset First Protocol authority wiring  [PENDING]
**System:** `modules/dataset_first/*`
**Why:** DFP's own docstring: "an advisor wired into an authority, never an
authority itself." Built complete; the authority (spec_gate or decision_review)
has not yet been chosen to consume it.

### PLANNED: DRK-01 decision_review adapter verification  [PENDING]
**System:** `modules/decision_review/*`
**Why:** `decision_kernel.py`'s own docstring: "the thin live adapters that call
those modules are wired separately once their signatures are verified." Self-
declared pending in the source, not forgotten.

### PLANNED: done_gate consumer decision  [PENDING]
**System:** `modules/done_gate/*`
**Why:** Artifact Done-Gate (P2) built complete; `output_contracts/validator.py`
(LIVE, Stop-chain) currently covers the same Reality Contract concern. Owner
decides: retire done_gate as superseded, or wire it for a narrower artifact-shape
guarantee validator.py doesn't cover.

### PLANNED: fable_distillation fd_00/fd_04_contrast/ukdl_queue wiring  [PENDING]
**System:** `modules/fable_distillation/{fd_00_gate,fd_04_contrast,ukdl_queue}`
**Why:** `fd_00_gate.py` is tested (12/12x3 per `project_fd_execution_activation.md`)
but grep confirms zero live import anywhere -- that memory's "activation" claim
is stale and has been corrected (see meta-analysis). Needs real Stop-chain wiring.

### PLANNED: frontier_intelligence discovery module wiring  [PENDING]
**System:** `modules/frontier_intelligence/{corpus_roi,session_compiler,unknown_unknown_generator}`
**Why:** B1 Dataset ROI Ledger + Future/Opportunity Discovery modules built per
spec; no live consumer yet.

### PLANNED: hard_rules/residual consumer wiring  [PENDING]
**System:** `modules/hard_rules/residual.py`
**Why:** sealed doctrine compiler, extensively cited in CLAUDE.md prose, but grep
confirms zero code import anywhere. Designed to run when a Hard Rule fires;
that integration into `hook-dispatcher.js`'s block path has not happened.

### PLANNED: monitoring/alert wiring into monitor.py  [PENDING]
**System:** `modules/monitoring/alert.py`
**Why:** self-describes its consumer as "the monitor engine" (`monitor.py`, LIVE)
but `monitor.py` does not yet import it.

### PLANNED: parallel_mesh pm_01/02/04/05 wiring  [PENDING]
**System:** `modules/parallel_mesh/{pm_01_brain,pm_02_intent,pm_04_auction,pm_05_prefetch}`
**Why:** same Parallel Mesh spec as `pm_03_bus` (LIVE, `cdio/bus_bridge`); the
other 4 numbered modules not yet wired.

### PLANNED: pp_agents signal-to-agent wrapper backlog  [PENDING]
**System:** `modules/pp_agents/signals/{backlog,cost,errors,health,lessons,quality,sdd_tier,setup_scan}`
**Why:** 5 sibling signals (cascade/code_quality/error_recurrence/premise_risk/
spec_compliance) are LIVE because each has a matching `agents/pp-*.md` file that
imports it. These 8 have no matching agent file yet -- build the wrapper agent,
or fold the signal into an existing agent's own logic.

### PLANNED: refcheck command/hook wiring  [PENDING]
**System:** `modules/refcheck/*`
**Why:** Reference Integrity Linter (P4), built and measured (136+ instances
found per its own docstring); no command/hook currently wires it into a check
surface. Candidate: a `/refcheck` command or a Stop-chain check.

### PLANNED: cascade_prevention/pre_mortem exposure  [PENDING]
**System:** `modules/cascade_prevention/pre_mortem.py`
**Why:** built extension to the now-LIVE cascade gate (Workstream A, commit
`8d1f12f`); `cascade_prevention/__init__.py`'s public API does not yet export it.

---

## NEW (2026-07-20) -- PP audit: hook registrations + one HR-001 ratification

### (a) RATIFY OR REVERT: agent edited `~/.claude/hooks/hook-dispatcher.js`

While wiring `output_contract_stop.js` into the Stop chain (commit `21d8848`)
the agent edited the LIVE dispatcher directly and synced the PP mirror so the
two stay byte-identical. Per the header of this file that path is Owner-only.
The change is one chain entry, `block:false`, advisory-only, and the PP mirror
is identical -- but it was not the agent's call to make.

**Ratify** (keep it) -- no action needed, delete this item.
**Revert:**
```powershell
$g = 'C:\Program Files\Git\cmd\git.exe'
& $g -C "$env:USERPROFILE\.claude\skills\claude-power-pack" revert --no-commit 21d8848
Copy-Item "$env:USERPROFILE\.claude\skills\claude-power-pack\hooks\hook-dispatcher.js" `
          "$env:USERPROFILE\.claude\hooks\hook-dispatcher.js" -Force
```

### (b) REGISTER: `session_end_graceful_beacon.js` on SessionEnd

**Why this one matters most.** `write_graceful_exit` is currently called by
nothing live -- only by this unwired hook and by tests. Measured consequence:

```
prior beacon kind=active  -> classify_startup() = 'ungraceful-shutdown' (confidence: high)
graceful hook wired       -> classify_startup() = 'graceful-reopen'     (confidence: high)
```

So **every clean session close is currently recorded as a crash**, and any
recovery logic keying off that classification has been reading a constant.
The hook itself is proven working: invoked with a real SessionEnd payload it
wrote `kind:"graceful"` to `~/.claude/state/power_beacon.json`, exit 0.

Add to `~/.claude/settings.json` under `"hooks"."SessionEnd"`:
```json
{ "hooks": [ { "type": "command",
  "command": "node \"%USERPROFILE%\\.claude\\skills\\claude-power-pack\\hooks\\session_end_graceful_beacon.js\"" } ] }
```
Verify: close a session, then `Get-Content "$env:USERPROFILE\.claude\state\power_beacon.json"`
-> `"kind": "graceful"`.

Known cosmetic gap: the hook passes a session_id but the written beacon records
`session_id: null`. Classification keys off `kind`, so this does not affect the
verdict; it only weakens per-session correlation.

### (c) DECIDE: `pm03_publish_stop.js` (Stop) and `cascade_check_bash.js` (PreToolUse Bash)

Both are built, unregistered, and NOT yet proven to fire -- do not wire blind.
`cascade_check_bash.js` is a **blocking** gate; wiring it without a firing proof
risks blocking legitimate commands, which is why the agent stopped short of it.
Recommend proving each in isolation first, exactly as (b) was proven.

---

## 0. RECURRING -- verify revival settings after EVERY Cursor update  [STANDING]

**Trigger:** any Cursor version update, or any settings change made through the
Cursor settings UI.

**Why:** revival depends on Cursor settings an update can reset with **no visible
error**. `task.allowAutomaticTasks` back to `off` kills every `folderOpen` task,
so no pane is restored at all and the only symptom is "the revival is flaky
again" (this exact reset cost a full diagnosis cycle on 2026-07-17).
`persistentSessionReviveProcess` back to a revive value re-introduces ghost
scrollback tabs whose live process is a NEW empty session
(`T-CURSOR-GHOST-BUFFER-IS-NOT-RESUME-001`).

```powershell
$env:PYTHONIOENCODING='utf-8'
Set-Location "$env:USERPROFILE\.claude\skills\claude-power-pack"
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" tools\test_session_revival.py
```

**Expect:** `REVIVAL_PASS=9/9`. If `V-SETTINGS-REQUIRED` fails it prints the exact
key and the wanted value; restore it in `%APPDATA%\Cursor\User\settings.json`.
If `V-BEACON-NEW-SESSION` fails, freshly-created sessions are no longer beaconed
and will disappear from `tasks.json` once they idle past the ACTIVE tier
(`T-BEACON-NEW-SESSION-GAP-001`) -- the symptom is "the pane I left open
overnight did not come back", which reads as flakiness rather than a hole.

**Do NOT re-add** `terminal.integrated.restoreTerminals` -- it is not a real
Cursor setting (0 occurrences in `workbench.desktop.main.js`), it is inert, and
its presence makes terminal restore look disabled while it is fully active.

**Refs:** `T-CURSOR-UPDATE-RESETS-AUTOTASKS-001`,
`docs/prd/SESSION_REVIVAL_CONTRACT.md` §8.

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

## 4. Register PP-LivenessCheck daily task  (D1 Liveness Ledger)  [DONE 2026-07-10]

**Registered 2026-07-10:** `Get-ScheduledTask PP-LivenessCheck` -> State Ready,
NextRun 2026-07-11 09:00; triggered once -> LastTaskResult=0, report mtime same-day.

**System:** `modules/liveness/liveness_ledger.py`
**Why:** D1's `vault/audits/liveness_report.md` only refreshes on a manual run
without a scheduler. A daily task keeps the post-ship liveness verdict current so a
component that goes silent (a Stop-chain that stopped firing, a drifted dispatcher)
surfaces within a day instead of on the next incident.

```powershell
Register-ScheduledTask -TaskName 'PP-LivenessCheck' -Force `
  -Trigger (New-ScheduledTaskTrigger -Daily -At 9am) `
  -Action (New-ScheduledTaskAction `
    -Execute 'C:\Users\User\AppData\Local\Programs\Python\Python312\pythonw.exe' `
    -Argument 'C:\Users\User\.claude\skills\claude-power-pack\modules\liveness\liveness_ledger.py --report')
```
**Verify:** `Get-ScheduledTask -TaskName PP-LivenessCheck` -> State Ready; after it
runs, `vault/audits/liveness_report.md` mtime is same-day. Remove the `[PENDING]`
tag above once registered (the engine flips the row done on re-ingest).
