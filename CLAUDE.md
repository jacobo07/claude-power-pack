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
<!-- PP-HARD-RULES-END -->
