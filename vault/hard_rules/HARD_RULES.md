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
### HR-SECRET-001 -- Stop before Write/Edit/MultiEdit if CRITICAL secret detected
TRIGGER: PreToolUse on Write / Edit / MultiEdit with content matching a CRITICAL pattern (anthropic_key, openai_key, github_pat, aws_access_key, private_key, connection_string).
STOP: Hook returns `continue:false` with stopReason "HR-SECRET-001 -- Secret Firewall blocked <Tool>. Rotate the secret before retrying." Detector never logs raw values; reporter records pattern_name + severity + line_no only. EXCEPCIÓN: Owner phrase "rotated and authorized -- HR-SECRET-001 OK" for ONE turn only.
EVIDENCE: [bl-secret-001] hooks/secret_firewall_gate.js + modules/secret_firewall/* shipped 2026-06-01 (commits cbed005, 4ee00ca, fc4b0ff)
SEVERITY: CRITICAL | RECURRENCE: 0x
<!-- digest:hr-secret-001-seed01 -->
### HR-SECRET-002 -- Never log raw secret values; use [REDACTED]
TRIGGER: About to emit text (log line, audit record, sub-agent prompt, additionalContext) that might contain a credential pattern.
STOP: Route the emission through modules.secret_firewall.redactor.redact() or redact_for_log() FIRST. The Universal Redaction Bus replaces matches with [REDACTED:<pattern_name>]. Audit/log records carry pattern_name + severity + line_no only; never the raw value.
EVIDENCE: [bl-secret-001] reporter.py + redactor.py implement the URB layer
SEVERITY: CRITICAL | RECURRENCE: 0x
<!-- digest:hr-secret-002-seed01 -->
### HR-SECRET-003 -- Never auto-rotate secrets; recommend and wait for Owner
TRIGGER: Detector classifies a secret as CRITICAL during analysis, audit, or post-commit scan.
STOP: Surface a recommendation to the Owner with (a) pattern_name, (b) file:line, (c) suggested rotation provider. NEVER call provider rotation APIs autonomously. NEVER write a new credential to disk autonomously. Owner approval required for every rotation action (per OD1, sealed 2026-06-01).
EVIDENCE: [bl-secret-001] OD1 = "secret rotation = Owner-decide (no auto)"
SEVERITY: CRITICAL | RECURRENCE: 0x
<!-- digest:hr-secret-003-seed01 -->
### HR-SECRET-004 -- Never git-add .env-class files without verifying .gitignore
TRIGGER: About to stage a file named `.env*`, `*.pem`, `*.key`, `id_rsa*`, or any path under known-secret directories (e.g. `vault/secrets/`, `_secrets/`).
STOP: Verify .gitignore (or .git/info/exclude) excludes the path BEFORE staging. If the path was already tracked and is about to land in a commit, abort the commit, `git rm --cached <path>`, append to .gitignore, then redo. Owner confirmation required if the file was already pushed.
EVIDENCE: [bl-secret-001] reinforces existing deploy doctrine (HR-005)
SEVERITY: CRITICAL | RECURRENCE: 0x
<!-- digest:hr-secret-004-seed01 -->
### HR-SECRET-005 -- Never hardcode real credentials in test fixtures
TRIGGER: Writing test code under tests/, _logs/, fixtures/, or any tracked path that includes a credential-like literal.
STOP: Use synthetic test values that ARE CLEARLY FAKE: `sk-ant-` + repeating literal (e.g. 'A'*50), `sk-fake-...`. Real-format synthetic keys (e.g. `sk-ant-` + 50 alphanumerics) ARE intentionally detectable -- they SHOULD trigger the firewall in CI to prove the firewall fires. NEVER paste a real provider key into a test.
EVIDENCE: [bl-secret-001] M1 done-gate uses `sk-ant-` + ('A' * 50) explicitly to prove detection on a clearly-fake but real-shape input
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-secret-005-seed01 -->
### HR-SECRET-006 -- Never send raw secrets in additionalContext or sub-agent prompts
TRIGGER: Building additionalContext (JIT cards, gatekeeper-semantic injection, learning sentinels), hook stdout, or sub-agent prompt that may include file content or tool_input transcripts.
STOP: All such text MUST pass through redact_for_log() FIRST. Hooks emitting context (Stop-event injectors, JIT loaders, learning-sentinel summaries) must wrap user-text before serialization. Sub-agent prompts must redact tool_input transcripts before composing the Agent call.
EVIDENCE: [bl-secret-001] URB designed as the universal sieve for all egress
SEVERITY: CRITICAL | RECURRENCE: 0x
<!-- digest:hr-secret-006-seed01 -->
### HR-SECRET-007 -- Post-commit secret detection: rotate FIRST, scrub after
TRIGGER: Post-commit audit (GitHub Push Protection alert, `vault/secret_firewall/audit.jsonl` entry, dependabot scan) flags a secret that already landed in commit history.
STOP: STOP all other work. Steps in order: (1) ROTATE at the provider FIRST (Owner-authorized), (2) revoke the leaked credential at the provider, (3) THEN optionally rewrite history. Force-push only after explicit Owner go-ahead. NEVER assume rotation can wait until "after this PR". Doctrine: scrubbed history with un-rotated credentials is still a leak.
EVIDENCE: [bl-secret-001] industry-standard rotate-first-scrub-second + OD1 alignment
SEVERITY: CRITICAL | RECURRENCE: 0x
<!-- digest:hr-secret-007-seed01 -->
### HR-CASCADE-001 -- STOP before deploy if tests_passed=False
TRIGGER: Bash / PowerShell command matching `(deploy|kubectl apply|helm install|fly deploy)` without explicit verification that the relevant tests passed in this session.
STOP: Refuse to dispatch. Surface the missing-test condition with the exact command to run tests first. EXCEPCIÓN: Owner phrase "deploy without tests authorized" for ONE turn only.
EVIDENCE: [bl-cascade-001] modules/cascade_prevention/engine.py _detect_deploy -> C4 (block)
SEVERITY: CRITICAL | RECURRENCE: 0x
<!-- digest:hr-cascade-001-seed01 -->
### HR-CASCADE-002 -- STOP before rm -rf or Remove-Item -Recurse -Force without backup
TRIGGER: Bash `rm -rf <path>` (path NOT under /tmp) OR PowerShell `Remove-Item ... -Recurse ... -Force` without an explicit backup precondition.
STOP: Refuse. Require an explicit `cp -r` / `Copy-Item -Recurse` backup OR Owner override. The dangerous_cmds.py registry (M11 GAP-2) is the source of truth for the pattern set.
EVIDENCE: [bl-cascade-001] modules/cascade_prevention/dangerous_cmds.py + _detect_bash
SEVERITY: CRITICAL | RECURRENCE: 0x
<!-- digest:hr-cascade-002-seed01 -->
### HR-CASCADE-003 -- STOP before commit without verification
TRIGGER: About to invoke `git commit` without a prior successful test / lint run in the current session.
STOP: Pause. Run the verification step OR escalate to Owner with the explicit gap. Sister of HR-CASCADE-001 for the commit surface.
EVIDENCE: [bl-cascade-001] _detect_commit -> C3 when verified=False
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-cascade-003-seed01 -->
### HR-CASCADE-004 -- STOP if a CRITICAL secret appears in any emission mid-turn
TRIGGER: Any text the agent emits (response, tool output it reads, sub-agent prompt) contains a CRITICAL Secret Firewall match.
STOP: Halt. Route through redact_for_log() BEFORE further emission. Sister of HR-SECRET-002 / HR-SECRET-006; integrates the Secret Firewall (M1) + URB into the cascade engine.
EVIDENCE: [bl-cascade-001] integrates Secret Firewall + URB on the cascade surface
SEVERITY: CRITICAL | RECURRENCE: 0x
<!-- digest:hr-cascade-004-seed01 -->
### HR-CASCADE-005 -- WARN at context >= 85% / BLOCK at context >= 95%
TRIGGER: Context-usage proxy (input_tokens / max_context_tokens) crosses the threshold.
STOP: 85-94% -> surface a /compact recommendation in the closing emission (advisory, do not block). 95%+ -> refuse to start new sub-agent dispatches; finish current state in-place and request Owner-driven /compact.
EVIDENCE: [bl-cascade-001] _detect_context CONTEXT_WARN_PCT=85 / CONTEXT_BLOCK_PCT=95
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-cascade-005-seed01 -->
### HR-OUTPUT-001 -- STOP declaring DONE if output has slop tokens
TRIGGER: About to claim "done" / "ready" / "shipped" with a deliverable whose content matches an OQS slop pattern.
STOP: Refuse the DONE claim. Surface the slop hit + surrounding context so the Owner sees the gap. Aligns with the Wozniak slop-veto already enforced via PreToolUse Write hook.
EVIDENCE: [bl-output-001] modules/output_contracts/validator.py + hooks/output_contract_stop.js (advisory)
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-output-001-seed01 -->
### HR-OUTPUT-002 -- STOP declaring DONE if tests_passed=False
TRIGGER: About to claim "done" / "ship" for a code output where the relevant test suite has not been empirically observed to pass (tests_passed=False or unmeasured).
STOP: Run the test and observe a real PASS, OR demote the claim to "draft, tests pending". DONE without observed PASS violates the Reality Contract (kernel vMAX-NULL-ERROR).
EVIDENCE: [bl-output-001] OQS validator passes_test check on `tests` field
SEVERITY: CRITICAL | RECURRENCE: 0x
<!-- digest:hr-output-002-seed01 -->
### HR-OUTPUT-003 -- STOP shipping code if OQS < 70
TRIGGER: is_done(contract='code', ctx) returns (False, score) with score < OQS_DONE_THRESHOLD (70).
STOP: Block the ship. Surface the OQS score + the failing checks (missing file_path / failed syntax / failed tests / slop in content) so the Owner sees the exact gap.
EVIDENCE: [bl-output-001] OQS scorer + 4 contracts (code/docs/deploy/test)
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-output-003-seed01 -->
### HR-ONESHOT-001 -- Compile contract before any L/XL task
TRIGGER: About to start a task whose pre-estimated size is L (>$30) or XL (>$100).
STOP: Pause. Run `compile_contract(description, size)` first. Inspect scope / out_of_scope / done_gate / budget. Confirm with Owner if estimate exceeds the OD3 cap for the chosen size.
EVIDENCE: [bl-oneshot-001] modules/one_shot/compiler.py + OD3 budget table
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-oneshot-001-seed01 -->
### HR-ONESHOT-002 -- STOP if execution deviates > 40% from scope
TRIGGER: Mid-execution check: is_deviated(contract, files_touched) is True (fewer than SCOPE_DEVIATION_THRESHOLD=0.40 of touched files match scope tokens).
STOP: Pause. Surface the touched-vs-scope diff to Owner. Either extend the contract (re-compile) OR revert the out-of-scope changes.
EVIDENCE: [bl-oneshot-001] modules/one_shot/lock.py fidelity_score + is_deviated
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-oneshot-002-seed01 -->
### HR-ONESHOT-003 -- After 3 consecutive fails, STOP -- Owner decision
TRIGGER: should_stop(fail_count) is True (fail_count >= STOP_AT=3).
STOP: Stop autonomous retries. Escalate to Owner with the failing-attempt log. Companion of anti-antipatterns Rule 12 (2-consecutive-failures pivot).
EVIDENCE: [bl-oneshot-001] modules/one_shot/escalation.py + OD7 ladder
SEVERITY: CRITICAL | RECURRENCE: 0x
<!-- digest:hr-oneshot-003-seed01 -->
### HR-COST-001 -- NEVER use Opus for format/lint/rename tasks
TRIGGER: About to dispatch a task that route(description).route_class == NANO with a model other than claude-haiku-4-5.
STOP: Refuse. Re-dispatch on Haiku. Opus tokens on a rename is a self-inflicted budget hole; cost discipline is non-negotiable.
EVIDENCE: [bl-cost-001] modules/cost_collapse/router.py NANO_KEYWORDS
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-cost-001-seed01 -->
### HR-COST-002 -- STOP if estimated cost > 2x task budget
TRIGGER: Mid-task: running cost estimate (input + output token spend) exceeds 2x the contract's budget_usd.
STOP: Pause. Surface the over-budget condition. Either Owner extends the budget (re-compile_contract at a higher size class) OR collapse the task scope to fit.
EVIDENCE: [bl-cost-001] OD3 ceilings (NANO $1 / MICRO $15 / MACRO $30 / ULTRA $100)
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-cost-002-seed01 -->
### HR-COST-003 -- Route trivial tasks to Haiku by default
TRIGGER: About to start a task whose description has no MACRO/ULTRA keyword AND no specific reason to prefer Sonnet/Opus.
STOP: Apply `route(description)`; respect the routed RouteClass. Default MICRO (Sonnet) for unspecified-but-non-trivial; NANO (Haiku) for keyword-matched trivial.
EVIDENCE: [bl-cost-001] modules/cost_collapse/router.py default path
SEVERITY: MEDIUM | RECURRENCE: 0x
<!-- digest:hr-cost-003-seed01 -->
### HR-BACKLOG-001 -- Run /what-now before starting new session work
TRIGGER: SessionStart on a project with a backlog file present, about to start NEW work rather than continue prior.
STOP: Invoke /what-now (or `modules.backlog_autopilot.what_now` programmatically). Picking a P2 over an actionable P0 is a process bug.
EVIDENCE: [bl-backlog-001] modules/backlog_autopilot/engine.py + commands/what-now.md
SEVERITY: MEDIUM | RECURRENCE: 0x
<!-- digest:hr-backlog-001-seed01 -->
### HR-BACKLOG-002 -- NEVER start L/XL task without backlog check
TRIGGER: About to start a task whose size class is L (>$30) or XL (>$100) without consulting the project's backlog.
STOP: Refuse. Run /what-now first. Confirm the task is the recommended item OR Owner-explicitly-authorized despite the recommendation.
EVIDENCE: [bl-backlog-001] enforces the spirit of OD3 budget discipline
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-backlog-002-seed01 -->
### HR-BACKLOG-003 -- STOP if new task would block a P0 item
TRIGGER: About to start new BacklogItem when the backlog has at least one P0 item that is currently actionable (not done, not blocked).
STOP: Refuse the lower-priority work. Surface the P0 contention. Either Owner explicitly defers the P0 OR you flip the queue.
EVIDENCE: [bl-backlog-001] what_now() filtering + priority scoring
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-backlog-003-seed01 -->
### HR-PREMISE-001 -- Verify file/function premises before executing a plan
TRIGGER: About to act on a plan that names specific file paths, module functions, classes, or APIs that have NOT been verified to exist in THIS repo.
STOP: Run modules.error_prevention.assert_premises([...]) (or python modules/error_prevention/premise_verifier.py --premises -) FIRST. A failing premise returns the REAL public API as the correction. Never write code against an assumed signature. EXCEPCION: Owner phrase "premises verified -- HR-PREMISE-001 OK" for ONE turn. ORIGEN: a plan asserted a 4-param compile_contract that does not exist (real signature is 2-param, description+size).
EVIDENCE: [bl-premise-001] modules/error_prevention/premise_verifier.py + verify_spp premise-verifier row
SEVERITY: HIGH | RECURRENCE: 1x
<!-- digest:hr-premise-001-seed01 -->
### HR-SPEC-001 -- L/XL task requires a spec gate check before coding
TRIGGER: About to start coding an L (>$30) or XL (>$100) task without checking whether a spec exists in the repo.
STOP: Run modules.spec_gate.check_spec_gate(desc, cwd, "L"|"XL"). gate_passed=False (action=create_spec) means establish a spec FIRST -- the auto-injected One-Shot contract (scope+done-gate) or the karimo PRD parser. S/M tasks are exempt. EXCEPCION: Owner phrase "spec gate waived -- HR-SPEC-001 OK" for ONE turn.
EVIDENCE: [bl-spec-gate-001] modules/spec_gate/gate.py + one_shot compiler advisory + skill_router spec domain
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-spec-001-seed01 -->
### HR-CONTEXT-001 -- Verify a plan's output files exist before declaring complete
TRIGGER: About to declare a multi-file plan "complete"/"done"/"shipped" when the plan's promised output files have NOT been verified to exist on disk.
STOP: Check every planned output -- assert_premises([{"type":"file_exists","path":p} for p in planned_outputs]). A "done" claim whose artifacts are absent is the Scaffold Illusion (Mistake #16). DONE = files exist AND a V-gate observed them working.
EVIDENCE: [bl-premise-001] premise_verifier.verify_file_exists + Reality Contract (kernel vMAX-NULL-ERROR)
SEVERITY: HIGH | RECURRENCE: 0x
<!-- digest:hr-context-001-seed01 -->
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
### HR-NOVELTY-001 -- Require the 13-question novelty proof before admitting a new institutional mega-system
TRIGGER: A proposal to build a new "fabric", "compendium", institutional operating system, kernel, civilization, governance layer, or intelligence platform (`modules/spec_gate/gate.py::check_novelty_gate`).
STOP: Refuse GENUINELY_NEW_DATASET status until all 13 questions (problem owner gap, new outcome, real consumer, extension insufficiency, new primitive, new decisions, new evidence, failure class prevented, interfaces with existing owners, value measurement, complexity introduced, retirement condition, why-not-rhetorical-layer) are answered with cited file:line evidence from a DISCOVERED sweep of the repo -- never from the proposal's own curated list of what it assumes doesn't exist. Missing evidence on any question -> classify as EXTEND_EXISTING_OWNER, NEW_MODULE, NEW_VIEW, NEW_POLICY_PACK, NEW_SCANNER_OR_GATE, or REJECT instead. EXCEPCION: Owner phrase "novelty proof waived -- HR-NOVELTY-001 OK" for ONE turn.
EVIDENCE: [iig-compendium-2026-07-30] 6 consecutive mega-corpus proposals for this repo (AISHF, RE Baseline's 3 NEW families -> 1 (CLAE), KSF's 22 -> 4-deferred, the UKR Compendium's 8-step escalation -> 0, this IIG pass's 30 candidates A-AD -> 0) measured as majority-or-fully owned once checked against a discovered denominator instead of the proposal's own list. `vault/plans/iig-compendium-2026-07-30.md`.
SEVERITY: HIGH | RECURRENCE: 6x
<!-- digest:novelty-proof-required-001 -->
<!-- PP-HARD-RULES-END -->
