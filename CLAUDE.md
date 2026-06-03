# Claude Power Pack -- Project CLAUDE.md

Power Pack execution doctrine inline. Hard rules below are sealed bug stops. See `vault/hard_rules/HARD_RULES.md` for the canonical archive.

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
<!-- PP-HARD-RULES-END -->
