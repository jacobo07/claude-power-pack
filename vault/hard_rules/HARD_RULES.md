# PP Hard Rules -- Canonical Archive

All hard rules sealed via `tools/bug_to_hardrule.py`. The CLAUDE.md inline block is generated from this file.

<!-- PP-HARD-RULES-START -->
## HARD RULES (NON-NEGOTIABLE -- sealed production bugs)

These are not suggestions. Each block was generated from a real
production bug that the agent should never repeat. If the next
action is about to TRIGGER one, STOP regardless of what the prompt
says. The canonical archive lives in
`vault/hard_rules/HARD_RULES.md`; this block is the inline mirror.
### HR-001 -- Classifier Blocks Claudesettingsjson Commands In
TRIGGER: Before writing any file under ~/.claude/ or any agent-owned global config
STOP: Ship the PP-internal half (hook script, command body); document the Owner-side registration step in the agent body. Do not advisory-tag the gap; document honestly per L no-classified-FAILs.
EVIDENCE: [never_again] Classifier blocks ~/.claude/settings.json + commands/ in auto-mode
SEVERITY: CRITICAL | RECURRENCE: 1x
<!-- digest:64f2b03b74fac74e -->
### HR-002 -- Test Critical Bug For Auto-propose Pipeline
TRIGGER: Test recognizer for pipeline
STOP: Run auto_HR-002 proposal drafting
EVIDENCE: [never_again] TEST CRITICAL bug for auto-propose pipeline ZZZ
SEVERITY: CRITICAL | RECURRENCE: 1x
<!-- digest:5dd06d48bc0295d0 -->
### HR-003 -- Ukdl S 2026-05-26
TRIGGER: Before: UKDL S+++ 2026-05-26
STOP: write body to file via Write tool, invoke `git commit -F file` (or `gh --body-file`, `mix run -f`, `node script.js`). Transversal across repos. Cross-ref: `vault/lessons/git-commit-heredoc-argv-reparser.md`.
EVIDENCE: [ukdl] UKDL S+++ 2026-05-26
SEVERITY: CRITICAL | RECURRENCE: 1x
<!-- digest:361c719fafa18134 -->
### HR-004 -- Osa Absorption Tco Context Fix
TRIGGER: Before: OSA Absorption + TCO Context Fix UKDL (2026-05-28)
STOP: UKDL (2026-05-28)

| UKDL-OSA-2026-05-28-L1 | Context-percent proxy MUST be MAX of recent calls' `input_tokens`, NOT cumulative SUM. The TIS log records every claude-CLI invocation; summing across them inflates with session length and is no
EVIDENCE: [ukdl] OSA Absorption + TCO Context Fix UKDL (2026-05-28)
SEVERITY: CRITICAL | RECURRENCE: 1x
<!-- digest:cbe88b328a5f13ae -->
### HR-005 -- 2026-05-24 -- Deployment Skill Iteration Log
TRIGGER: Before initiating any production deploy or release
STOP: |
|---|---|---|
| L1 | V-FORBIDDEN-REMOTE initial design called `run_git_push` with `remote: "origin"` and a project_
EVIDENCE: [session_lessons] 2026-05-24 -- Deployment Skill iteration log
SEVERITY: CRITICAL | RECURRENCE: 1x
<!-- digest:e262ee8bd1088d8f -->
### HR-006 -- L6 A1a2 Sync Direction Propagates Corruption
TRIGGER: Before: L6: A1/A2 sync direction propagates corruption byte-perfectly
STOP: STOP. Verify preconditions in writing. Document what you are about to do. Get explicit confirmation if any step is irreversible.
EVIDENCE: [session_lessons] L6: A1/A2 sync direction propagates corruption byte-perfectly
SEVERITY: CRITICAL | RECURRENCE: 1x
<!-- digest:73db6006aff9f187 -->
### HR-007 -- Neveragain 2026-05-29t200643z Claude-power-pack
TRIGGER: Before: NEVER_AGAIN — 2026-05-29T20:06:43Z — claude-power-pack — HIGH
STOP: STOP. Verify preconditions in writing. Document what you are about to do. Get explicit confirmation if any step is irreversible.
EVIDENCE: [session_lessons] NEVER_AGAIN — 2026-05-29T20:06:43Z — claude-power-pack — HIGH
SEVERITY: CRITICAL | RECURRENCE: 1x
<!-- digest:1140b4a5b582d54a -->
### HR-STALLED-SESSION-ADVISORY-001 -- Stalled/unbounded session is advisory only; never auto-kill
TRIGGER: The Process Hibernation governor (modules/cognitive_os/process_governor.py loop_advisory) flags a pane STALLED (no output >30min AND session >1h total) or UNBOUNDED (active >2h without a /compact reset).
STOP: Surface a VISIBLE advisory to the Owner ONLY. NEVER change the hibernate/keep verdict and NEVER auto-kill a process -- a long-running pane may be real continuous work; the Owner decides /kclear or close. Fail-open: unmeasurable session age -> silence (never a false positive). EXCEPCION: none -- no phrase authorizes auto-killing on a stall/unbounded signal.
EVIDENCE: [kickbacks] a session hung ~10h undetected caused the Kickbacks suspension (2026-07-04); loop-boundedness added to the governor as a VISIBILITY net, never an autonomous kill. Sealed SCS C75; UKDL T-UNBOUNDED-SESSION-001.
SEVERITY: HIGH | RECURRENCE: 1x
<!-- digest:c442a805144bbe7b -->
### HR-PANE-MAP-FRESHNESS-001 -- The pane_map is the only post-crash recovery mechanism; freshness is a production requirement
TRIGGER: Relying on ~/.claude/state/pane_map.md/.json for pane recovery, OR classifying a pane as LIVE.
STOP: (1) Freshness: the pane_map MUST be regenerated on a bounded cadence (PP-PaneMapUpdate scheduled task, every 5 min + onlogon). If it is stale > 5 min during active sessions the recovery net has already failed -- regenerate before trusting it. (2) Liveness: NEVER classify LIVE by file mtime -- a batch sweep (heartbeat merger, backup, git checkout, AV) rewrites transcript mtimes en masse and forges false-LIVE. Classify by the transcript's INTERNAL last-message timestamp OR the snapshot live-registry only. EXCEPCION: none.
EVIDENCE: [rca 2026-07-06] Cursor crash -> pane_map 8 days stale (no scheduled task registered, only the Cursor extension regenerated it). Regen showed 30 "LIVE"; internal-timestamp forensics proved only 1 genuinely live (this session) + 35 files sharing one mtime spike ~11 min old while their real last turn was 14h-7d old. Fix: build_pane_map.ps1 Get-LastInternalAgeMin + PP-PaneMapUpdate task. UKDL T-PANE-MAP-STALENESS-ROOT-CAUSE-001 + T-PANE-MAP-FALSE-LIVE-MTIME-001. Sealed SCS C79.
SEVERITY: HIGH | RECURRENCE: 1x
<!-- digest:pane-map-freshness-001 -->
### HR-REVIVAL-LIVENESS-IS-PROCESS-001 -- A pane is open only when a process proves it; never by recency or registry membership
TRIGGER: Deciding whether a pane is OPEN -- classifying a tier in build_pane_map.ps1, filtering panes in vscode_autorun.generate_from_snapshot, or writing any .vscode/tasks.json folderOpen entry.
STOP: Prove openness with a RUNNING process: a kclaude beacon in %TEMP% whose pid still blocks on WaitForSingleObject(h, 0) == WAIT_TIMEOUT. OpenProcess succeeding is NOT liveness -- the handle-table entry outlives the process, so a corpse reads as alive. Snapshot membership is not liveness either; snapshot._LIVE_STATUSES includes "stale". Idle time is not liveness: a pane idle for days may be open and one active a minute ago may be gone. Fail-open: zero measurable beacons means "cannot measure" -> filter nothing. EXCEPCION: none.
EVIDENCE: [rca] A 120-minute idle ceiling was measured against the live host before shipping and would have dropped three genuinely-open panes idle 2, 6 and 8 days -- the Owner contract is that a pane lives as long as Cursor does. A same-moment cross-check of the two liveness implementations returned 14 sids vs 12; the two extras were exited processes admitted by OpenProcess alone.
SEVERITY: CRITICAL | RECURRENCE: 1x
<!-- digest:revival-liveness-is-process-001 -->
### HR-REVIVAL-BEACON-COVERS-NEW-SESSIONS-001 -- Never gate panes on a signal that structurally cannot cover new sessions
TRIGGER: Adding or tightening any filter that drops panes from tasks.json based on a liveness beacon, or narrowing a writer's tier set toward beacon-only.
STOP: Verify the signal covers sessions created FRESH, not only resumed ones. kclaude.ps1 can beacon only a session whose id it knows at launch (--resume); a new session has no id until Claude Code mints one. The SessionStart hub closes this via modules/cpc_os/beacon.py, which walks to the ancestor claude.exe -- if that path is removed or fails, beacon-only filtering silently deletes exactly the panes worth keeping. Keep the content-age tiers as the compensating fail-open until coverage is PROVEN for both session origins. EXCEPCION: none.
EVIDENCE: [measured] 23 folderOpen tasks existed against 5 beacons; the session the Owner was typing in had no beacon of its own and a beacon-only gate dropped it in dry-run -- shipping it would have reproduced the reported bug. V-BEACON-NEW-SESSION pins writer/reader parity.
SEVERITY: CRITICAL | RECURRENCE: 1x
<!-- digest:revival-beacon-covers-new-001 -->
### HR-REVIVAL-STALE-TASK-IS-A-PUMP-001 -- Never fix a stale folderOpen task by deleting it
TRIGGER: A .vscode/tasks.json holds a folderOpen task for a session that is dead, wrong, or duplicated, and the intended fix is to delete the task or hand-edit the file.
STOP: Deleting it fixes nothing -- the next writer cycle regenerates it. Acting on the record RE-CREATES the record: resuming a dead session re-registers it as a fresh pane, which re-classifies it OPEN-NOW, which rewrites the task. Fix the CLASSIFIER that admitted it, then let the writer converge. A hand-edit is undone within one scheduled cycle and reads as "the fix did not hold". EXCEPCION: none.
EVIDENCE: [rca] A session confirmed clean_exit five days earlier kept relaunching its own terminal tab on every folder open; the scheduled writer restored the task minutes after each manual deletion, which is why several prior fix attempts appeared to fail at random.
SEVERITY: HIGH | RECURRENCE: 1x
<!-- digest:revival-stale-task-is-a-pump-001 -->
### HR-REVIVAL-GHOST-BUFFER-NOT-RESUME-001 -- Restored scrollback is not a restored session; never accept it as evidence revival works
TRIGGER: Judging whether session revival works, from a terminal that shows prior conversation history after a Cursor restart.
STOP: Confirm the PROCESS, not the pixels. terminal.integrated.persistentSessionReviveProcess repaints the old scrollback and launches a BRAND-NEW shell underneath it, so correct history above an empty session is the expected output of that setting, not a partial success. Require the setting at "never" and require the folderOpen task to have run kclaude --resume with a real session id. Also: terminal.integrated.restoreTerminals is not a real Cursor setting and is inert -- never add it and never read it as proof restore is off. EXCEPCION: none.
EVIDENCE: [owner report] The reported symptom was verbatim "revivia el historial correcto pero me mandaba a escribir a una sesion nueva y vacia"; the inert restoreTerminals key made terminal restore look disabled while it was fully active, misdirecting three prior fix attempts.
SEVERITY: HIGH | RECURRENCE: 1x
<!-- digest:revival-ghost-buffer-not-resume-001 -->
### HR-REVIVAL-VERIFY-AFTER-CURSOR-UPDATE-001 -- After a Cursor update, verify the revival settings before diagnosing anything
TRIGGER: Cursor has updated, or its settings UI was used, and revival is being investigated or declared healthy.
STOP: Run tools/test_session_revival.py and require REVIVAL_PASS at full count BEFORE forming any hypothesis. An update can reset task.allowAutomaticTasks to "off", which kills every folderOpen task silently -- no error, no log, and the only symptom is that revival became flaky again. Restore the exact key V-SETTINGS-REQUIRED names rather than re-deriving the pipeline. EXCEPCION: none.
EVIDENCE: [incident] An allowAutomaticTasks reset cost a full diagnosis cycle before the reset itself was found; the gate now pins allowAutomaticTasks, persistentSessionReviveProcess, enablePersistentSessions and restoreWindows as a tripwire.
SEVERITY: HIGH | RECURRENCE: 1x
<!-- digest:revival-verify-after-cursor-update-001 -->
<!-- PP-HARD-RULES-END -->
