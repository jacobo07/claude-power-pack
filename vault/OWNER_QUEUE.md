# OWNER_QUEUE -- pending Owner-side activations

Items the agent prepared but cannot self-activate (HR-001: no writes to
`~/.claude/hooks`, `~/.claude/settings.json`, or commands). Each item is
copy-paste-ready. Kept in the repo (versioned, durable); the agent updates it,
the Owner executes. Newest-relevant first.

---

## NEW (2026-07-26) -- KSF Phase 0 audit: three pre-existing defects

Surfaced by the Knowledge Sovereignty Fabric Phase -1/Phase 0 corpus audit
(`vault/plans/ksf-compendium-2026-07-26.md`). None was caused by that mission.
Owner disposition at STOP #1: repair (a) now, defer (b) and (c) to backlog.

### (a) PLUGIN-INSTALL trigger class carries zero rules  [RESOLVED 2026-07-27 -- RETIRED, no corpus; reopen with evidence]

**System:** `modules/rule_compiler/digest.py` + `tools/hardrule_compile.py`
**Status:** the *silent* half is fixed this session. `build_digest` used to drop
any empty class, so a trigger class the global `~/.claude/CLAUDE.md` router
contracts on vanished from the digest entirely -- the agent could not tell "no
rules" from "no such class", and `--class PLUGIN-INSTALL` answered `0 rules.
Comply before acting.` at **exit 0**, which reads exactly like a clean pass.
Now: contracted-but-empty classes stay in the digest with an explicit `0`, are
named under `## CONTRACTED BUT UNENFORCED`, and the CLI returns **exit 3**.
Verified: digest 2154 -> 2409 B (cap 4096), `ENFORCEMENT_PASS=19/19`, exit 0.

**RESOLVED 2026-07-27 -- Owner decision: RETIRE the trigger.** A contracted
trigger with zero corpus rules cannot be governance; it is governance theater.
Reopened only when concrete evidence exists to control.

Shipped (PP side, commit below): `PLUGIN-INSTALL` moved out of
`ROUTER_CONTRACTED` into a new `RETIRED_CLASSES` registry in
`modules/rule_compiler/digest.py`. The class stays **defined**, deliberately --
deleting it would repeat the silent drop this whole item is about, and no reader
could then tell a deliberate retirement from an accidental rename. Effects:
digest now carries `## RETIRED TRIGGERS` with the reason instead of a coverage
defect; `--class PLUGIN-INSTALL` prints `RETIRED_NO_CORPUS` + the reopen
condition at **exit 0**; if a future rule ever classifies there, the digest
raises `## REOPEN CONDITION MET` and the CLI says those rules are not yet
contracted. Import-time guards reject a class that is both contracted and
retired, or retired but undefined.

Verified: `CONTRACTED BUT UNENFORCED` occurrences in the digest = **0**;
digest 2,409 -> 2,653 B (cap 4,096); `--compile` exit 0; `--check` exit 0;
`--class DEPLOY` exit 0 unchanged; `ENFORCEMENT_PASS=19/19` exit 0.

**Reopen condition (documented, not implied).** A real plugin-install incident
that yields at least one schema-valid rule (observable TRIGGER, imperative
ACTION, that incident as EVIDENCE). Then move `PLUGIN-INSTALL` back into
`ROUTER_CONTRACTED` and restore the router's fourth trigger.

**Residual Owner-side step (HR-001 -- the agent may not edit `~/.claude/CLAUDE.md`).**
The global router still lists a fourth trigger the compiler no longer contracts.
Until this line is removed the router and the corpus disagree. In the
`## HARD RULES — ROUTER` block, delete trigger 4:

```
4. Installing or updating a plugin (any JAR write to `/plugins/`)
```

and change "Triggers (any one fires the read)" to read three. **Verify:**
`python ~/.claude/skills/claude-power-pack/tools/hardrule_compile.py --class PLUGIN-INSTALL`
-> `RETIRED_NO_CORPUS`, exit 0; the digest's class table lists three contracted
classes plus the domain classes, and the `## RETIRED TRIGGERS` section explains
the fourth.

### (b) CPP-IAS non-duplication verdicts rest on a short denominator  [PENDING -- backlog]

**System:** `vault/knowledge_base/cpp_ias/13_REGISTRIES/SYSTEM_REGISTRY.md`
**Why:** it maps the estate as "18 domains, ~524k words" and omits `d2a_fabric`
(DAIF, 292,276 words -- the single largest family) and `crawl_os` (117,114 w).
Every ABSORB/REFERENCE verdict citing that registry was decided against a
denominator missing ~416k words of its nearest neighbours, so IAS-vs-DAIF overlap
has never actually been tested. Already recorded inside `CPP_IAS_INDEX.md` as the
fifth measured instance of `T-D2A-REGISTRY-BLIND-SPOT-001`; carried here so it is
visible outside the family that owns it. Fix = rebuild the registry from a
discovered set (`PR-COVERAGE-BY-CONSTRUCTION-001`), never a curated one, then
re-run the affected verdicts at content tier.

### (c) DAIF marked SEALED with four done-gate artifacts NOT_STARTED  [PENDING -- backlog]

**System:** `vault/knowledge_base/d2a_fabric/DAIF_INDEX.md`
**Why:** the manifest reads `8/8 SEALED · 160/160 Parts · 292,276 words`, while
its own governance table lists `DAIF_CONTAMINATION_AUDIT.md`,
`DAIF_COVERAGE_MATRIX.md`, `DAIF_COMPOUNDING_MAP.md` and `tools/test_daif.py`
as `NOT_STARTED`. A SEALED claim whose done-gate artifacts do not exist is the
Scaffold Illusion at corpus scale (Mistake #16, HR-CONTEXT-001). Either produce
the four artifacts, or demote the family's state to `CONTENT_COMPLETE` until
they exist. The word counts are not in question; the *verdict* is.

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
**System:** `modules/cognitive_os/{context,economics,gc,governor,guarantee_ledger,loop_budget,memory,rehydration}`
**Why:** 8 CO-00-series modules built per spec; `process_governor.py` (LIVE) does
not import any of them (verified by grep). Composing them is a real architecture
decision, not a 1-line wire. **Dependency-ordered** — `context`→`governor`,
`economics`→`guarantee_ledger`, `memory`→`gc`: wiring a dependent alone yields a
consumer with no producer. Per-module intended consumer, blocker and evidence:
`vault/plans/crpf-option-a-wiring-2026-07-27.md`.
**Amended 2026-07-27:** `hibernate_runner` removed from this row — it was never
silent. Task **PP-Hibernation** invokes it every five minutes via
`hibernation_daemon.ps1` → `tools/run_hibernation.py` (341 KB of daemon log,
rc=0). It read as ORPHAN because `reachability.py` could not see the Task
Scheduler at all; fixed in `a91328c`, and it is now REACHABLE by discovery.

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
**Amended 2026-07-27:** `pm_03_bus` is live only because `cdio/bus_bridge` reuses
it **as a store** — nothing runs the mesh itself, so its liveness is not evidence
that the mesh is running. PM-05 prefetch additionally needs PM-04's pressure mode
and PM-02's intent declaration, neither of which has a producer; it cannot be
wired first. Evidence: `vault/plans/crpf-option-a-wiring-2026-07-27.md`.

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

## NEW (2026-07-22) -- CGF Workstream D: register `prompt_minimalism_gate.js` on Task  [PENDING]

**System:** `hooks/prompt_minimalism_gate.js` (mirrored to `~/.claude/hooks/` already).
**Why:** the CGF Phase -1 audit confirmed this is the one genuinely-new mechanism
in the whole proposal -- neither `prompt_pattern_optimizer.py` (CLAUDE.md token
waste) nor `prompt_defense_baseline.py` (security defenses) checks whether an
outgoing sub-agent prompt hands over literal implementation instead of a
contract. Built, unit-validated (`tools/test_prompt_minimalism.py`,
`PROMPT_MINIMALISM_PASS=5/5 false_positive_rate=0.00` against real/representative
cases including this session's own CGF prompt as a should-NOT-trip contract
example), but NOT proven to fire in the live harness yet -- do not wire blind,
same discipline as item (c) below.

Add to `~/.claude/settings.json` under `"hooks"."PreToolUse"`, alongside the
existing `subagent-bash-avoidance-advisor.js` / `agent-solo-guard.js` entries
on the same `"Task"` matcher:
```json
{
  "matcher": "Task",
  "hooks": [
    { "type": "command",
      "command": "\"/c/Program Files/nodejs/node.exe\" \"C:/Users/User/.claude/hooks/prompt_minimalism_gate.js\"",
      "timeout": 5,
      "statusMessage": "Prompt Minimalism advisory (CGF Workstream D, 2026-07-22)" }
  ]
}
```
**Verify:** dispatch an Agent with a prompt containing a fenced code block that
defines a function (not framed as "existing code") -- `additionalContext`
should carry the PROMPT MINIMALISM advisory; a normal contract-style prompt
(paths, constraints, done-gate, no code fence) should produce no output.

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
