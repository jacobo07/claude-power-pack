# Universal Knowledge / Documentation / Lessons — cross-reference ledger

This file is the "ukdl-universal" reference index — each row points
at a sealed lesson, learning, or session note that is broadly
applicable across PP-shipped projects and not specific to one repo.

Entries are append-only; never remove a row. If a lesson is
superseded, append the superseding row referring back to the older.

## Auto-Testing Skill (Quality Gate) — 2026-05-23

| Ref | File | Why it matters |
|---|---|---|
| UKDL-AT-01 | `vault/specs/auto-testing-gate.md` | Authoritative contract for the Quality Gate skill: architecture, verdict shapes, 30 s budget, ceiling-honest posture, Mirror-Sync-Direction. |
| UKDL-AT-02 | `vault/plans/auto-testing-skill-2026-05-23.md` | 23-Paso ULTRA plan + status log with empirical numbers for each gate. |
| UKDL-AT-03 | `vault/knowledge_base/session_lessons.md` (rows L1-L6 dated 2026-05-23) | Iteration findings from real empirical runs: Python-by-convention rule (twice tightened), pytest filename validity, PowerShell here-string tokenization, regex var-in-PowerShell coverage. |
| UKDL-AT-04 | `knowledge_vault/core/apex-completion-standard.md` — "Testing Gate Axis (sealed 2026-05-23)" section | 5 required components + 5-check DONE-gate for the axis. PP source + `~/.claude/knowledge_vault/core/...` live mirror byte-identical (sha256 63bdfca46f83e8cd). |
| UKDL-AT-05 | `vault/lessons/windows-argv-limit-stdin-fix.md` (sister to deep-research) | claude.exe -p user message via STDIN. The Auto-Testing LLM bridge inherits this vaccine. |
| UKDL-AT-06 | `vault/lessons/stop-hook-subprocess-recursion.md` (sister to deep-research) | CLAUDEPP_AUTOTEST_RUNNING=1 sentinel pattern. The hook checks this as its first statement; same family as CLAUDEPP_DEEPRESEARCH_RUNNING. |

## Cross-axis pattern: sleepy auto-spawn + ceiling-honest gates

Three PP axes now share the same architectural shape (sealed
2026-05-23):

- **Research Axis** (`cpp-deep-research`): Stop hook intent regex +
  detached `cmd.exe /c start "" /B python ...` spawn + recursion
  guard env var. CEILING when web search + no API keys produce
  zero URLs.
- **Testing Gate Axis** (`auto-test-gate`): PreToolUse hook command
  regex (PRIMARY + LOOSE) + subprocess spawn of
  `python auto_test.py --gate` + recursion guard env var. CEILING
  when no build manifest OR framework binary missing.
- **Session-Safety Axis** (`session-file-guard`): PreToolUse hook
  protects .jsonl files from harmful tool calls; SessionStart hook
  recovers stub sessions.

Common pattern (sealed as PP doctrine): every "smart" hook is
fail-OPEN, has a recursion-guard env-var, has a Mirror-Sync-Direction
consolidator in `settings_merger.py`, and ships with a 5-check
DONE-gate in `apex-completion-standard.md`.

## Cross-references to forbidden runtimes

- `memory/feedback_no_n8n_ever.md` — n8n is forbidden as a runtime.
  Reference workflows extracted only for prompt + algorithm
  reverse-engineering. Same ban extends to Zapier/Make.com/Pipedream
  by implication.


## Production Branch Standard — 2026-05-23

| Ref | File | Why it matters |
|---|---|---|
| UKDL-PB-01 | `knowledge_vault/core/apex-completion-standard.md` "Production Branch Standard" section | Three hard preconditions for `feat/* -> main`: verify_spp 7/7, manual conflict resolution, post-merge verify_full_install 0. |
| UKDL-PB-02 | `.gitattributes` (repo root) | 5 ledgers configured for `merge=union` (session_lessons.md, governance_vaccines.md, verdicts.jsonl, vendor/NOTICE.md, SSOT.md). Cherry-pick onto main BEFORE the merge so the union driver activates. |
| UKDL-PB-03 | `vault/knowledge_base/session_lessons.md` "Branch hygiene: 177-commit feat branch" row | 4 lessons: merge frequency <=2 weeks; union driver from day 1; cherry-pick .gitattributes onto main first; Reality Contract = commits + tests pass, not just merge commit. |
| UKDL-PB-04 | `vault/lessons/bash-heredoc-bom-clobber.md` | Companion pattern: Python read_bytes + write_bytes is the safe append for BOM-prefixed markdown files. Used to recover the L1-L6 rows when the union merge couldn't reconcile divergent file structures. |

## Architecture Decision Skill — 2026-05-23

| Ref | File | Why it matters |
|---|---|---|
| UKDL-AC-01 | `vault/specs/arch-decision-skill.md` | Authoritative spec: 15 sections, STDIN contract, 8 vault sources scanned, verdict shapes COLLISION/WARNING/CLEAR, DONE-gate, opt-out + recursion-guard env vars. |
| UKDL-AC-02 | `vault/plans/arch-decision-skill-2026-05-23.md` | 14-paso plan with done-gates per paso, 6 V-tests, scoring graph. |
| UKDL-AC-03 | `modules/arch-decision/arch_check.py` | Verdict engine: word-boundary entity matching, title+body containment scoring, fail-open on every error. Driven by STDIN, JSON stdout. |
| UKDL-AC-04 | `modules/arch-decision/build_index.py` | Index builder: scans 8 weighted vault paths into `vault/.arch-index/index.json` + `vocab.json`. Deterministic across runs given same inputs. |

## Decisions (auto-appended by /arch-decision)

| Ref | File | Why it matters |
|---|---|---|
| UKDL-AC-DEC-01 | `vault/decisions/2026-05-23-190211_redis-sessions-tuax.md` | First sealed ADR from this skill. Redis-vs-Postgres for TUA-X sessions; verdict CLEAR (no prior decision); Status Proposed pending Owner sign-off. |

## Code Review Skill -- 2026-05-23 (PP Quality Triangle complete)

| Ref | File | Why it matters |
|---|---|---|
| UKDL-CR-01 | `vault/specs/code-review-skill.md` | Authoritative spec: 15 sections, STDIN contract, verdict shapes (block/warn/pass/skip), SKIP-honest contract for missing external linters, 7-check DONE-gate. |
| UKDL-CR-02 | `vault/plans/code-review-skill-2026-05-23.md` | 15-paso plan with done-gates per paso, 10 V-tests, sequencing graph. |
| UKDL-CR-03 | `modules/code-review/code_reviewer.py` | Verdict engine: PP-doctrine (9 patterns from session_lessons) + security (high-entropy keys + Shannon-entropy-gated password literal + injection) + complexity heuristics + external linter dispatch (ruff/mix/SKIP-honest). FAST + DEEP modes. |
| UKDL-CR-04 | `modules/auto-testing/auto_test.py` (`_run_code_review_if_enabled`) | Gate piggyback. Spawns code_reviewer after run_gate and combines verdicts (BLOCK -> "fail" so existing hook exits 2). **No new hook**. |
| UKDL-CR-05 | `commands/code-review.md` + `vault/reviews/patterns.jsonl` | DEEP-mode skill + closed-loop log. /code-review writes 4-section report; verdict != PASS appends a row; future DEEP runs surface prior rows in `patterns_history`. Sister to UKDL-AC-DEC pattern. |

## Code Review Reports (auto-appended by /code-review)

| Ref | File | Why it matters |
|---|---|---|
| UKDL-CR-REP-01 | `vault/reviews/2026-05-23-203833_code-review-skill-self.md` | First empirical V-DEEP report. Self-review of the code-review skill staged diff: 70 findings (18 BLOCK + 52 WARN), 5 lesson candidates surfaced, self-detection false-positive class documented with two concrete refactor candidates (file-type exclusion + self-exclusion). |


## Deployment Skill -- 2026-05-24 (PP Quality Quadrangle complete)

| Ref | File | Why it matters |
|---|---|---|
| UKDL-DP-01 | `vault/specs/deployment-skill.md` | Authoritative spec: 15 sections, 4 modes (gh-workflow / git-push-to-deploy / manual-scp / none), STDIN contract, verdict shapes, exit-code table, §77 mandatory citation, no-credentials-in-vault invariant. |
| UKDL-DP-02 | `vault/plans/deployment-skill-2026-05-24.md` | 15-paso plan + per-paso done-gates + sequencing graph + V-block (14 tests). Cites PASO 0 grounding tabla. |
| UKDL-DP-03 | `modules/deployment/deploy.py` | Dispatcher: detector -> runner -> healthcheck -> receipt. Recursion-guard at level-2+ ONLY (lesson L2 sister to code-review). Writes vault/deploys/<ts>_*.md only AFTER healthcheck completes (Reality Contract). |
| UKDL-DP-04 | `modules/deployment/runners/gh_workflow.py` | §77 Deploy Sovereignty enforcement -- emits the doctrine citation on every detection of `deploy-vps.yml` and includes it in the JSON verdict's `doctrine_cite`. The runner INVOKES the canonical pipeline; it never replaces it. |
| UKDL-DP-05 | `modules/deployment/runners/scp_systemd.py` + `modules/deployment/healthcheck.py` | manual-scp runner with credential-rejection schema validator AND the three healthcheck kinds (tcp / http / curl-grep). curl-grep is the §77 receipt -- HTTP 200 is insufficient because a stale build still returns 200; only literal content verification proves new bytes are serving. |

## Deploy Reports (auto-appended by /deploy)

| Ref | File | Why it matters |
|---|---|---|
| UKDL-DP-REP-01 | `vault/deploys/2026-05-24-130836_infinityops_dryrun.md` | First V-DEEP empirical receipt. Dry-run of `/deploy --project infinityops` against the real InfinityOps repo. Detector picked `gh-workflow`, runner emitted §77 Deploy Sovereignty citation to stdout AND in JSON verdict, dispatcher correctly refused to write the automated receipt path under `vault/deploys/` because dry-run does not mutate. Proves the invariant: §77 is non-negotiable; no receipt = no deploy. |


## Backup / Snapshot Skill -- 2026-05-25 (Deploy precondition)

| Ref | File | Why it matters |
|---|---|---|
| UKDL-BK-01 | `vault/specs/backup-skill.md` | Authoritative spec: 16 sections, 3 modes (rsync-dir / docker-volume-tar / pg-dump), STDIN/STDOUT contract, restore-test contract (§8), verdict shapes, disk-full guard (§9), no-credentials invariant (§10), no-off-site-auto-push (§11), recursion-guard discipline (§12), DONE-gate (§16). |
| UKDL-BK-02 | `vault/plans/backup-skill-2026-05-24.md` | 16-paso plan + per-paso done-gates + sequencing graph + V-block (15 tests). Cites PASO 0 grounding tabla showing all 3 productive projects share the same state-preservation gap (opposite case to Deploy Axis where InfinityOps already had §77). |
| UKDL-BK-03 | `modules/backup/backup.py` | Dispatcher: schema-validate -> disk-full guard -> runner -> verify_restore -> retention -> receipt. Recursion-guard at level-2+ ONLY (sister to deploy L2). Writes vault/backups/<ts>_*.md only AFTER verify_restore completes (Reality Contract). |
| UKDL-BK-04 | `modules/backup/verify_restore.py` + `modules/backup/retention.py` | Restore-test verifier (4 structural_check kinds: nbt-magic / pg-dump-header / json-parse / not-empty) + retention enforcer (keep_last_n + drop_older_than_days + min_keep + sha256 manifest). The restore-test is the receipt: "a snapshot that has not been restore-tested is a .tar.gz, not a backup." |
| UKDL-BK-05 | `modules/backup/runners/*.py` + `modules/deployment/deploy.py` (`_run_pre_deploy_backup_if_enabled`) | 3 runners (rsync-dir / docker-volume-tar / pg-dump) covering KobiiCraft world + TUA-X postgres + InfinityOps postgres. Deploy integration: `vault/deploy/<project>.json` accepts `pre_deploy_backup: true`; dispatcher invokes backup as pre-gate; verdict != pass -> deploy CEILING. V-BACKUP-FIRST in deploy V-block proves the gate. |

## Backup Reports (auto-appended by /backup)

| Ref | File | Why it matters |
|---|---|---|
| UKDL-BK-REP-01 | `vault/backups/2026-05-25-151305_kobiicraft_dryrun.md` | First V-DEEP empirical receipt. Dry-run of `/backup --project kobiicraft` against the PP repo's `vault/backup/kobiicraft.json`. Detector picked `rsync-dir`, the planner emitted the full ssh+tar command, the dispatcher correctly refused to mutate (dry-run path). Proves: schema validation, ssh-key resolution, planned remote command, planned restore-test (nbt-magic on level.dat). |



### Rollback Axis (sealed 2026-05-25)

| ID | Lesson |
|---|---|
| UKDL-RB-01 | Manifest as truth source: `backups/<proj>/manifest.json` (written by `apply_retention`) is the ONLY list of verified snapshots. A `.tar.gz` on disk without a manifest entry was either never restore-tested or pre-manifest-era; the Rollback Axis must refuse it (`target_unverified` CEILING). |
| UKDL-RB-02 | Healthcheck after restore is mandatory. A successful runner with no healthcheck verdict is by definition not a rollback (`rollback-warn` exit 3 when HC fails -- never silent). Reuse `modules/deployment/healthcheck.py:run_healthcheck` -- single source of truth. |
| UKDL-RB-03 | No auto-rollback. Deploy SUGGESTS, never invokes. V-NO-AUTO grep-asserts zero call sites of the rollback dispatcher in `deploy.py`; V-ROLLBACK-SUGGEST asserts the suggestion DOES appear in fail-class verdicts. Hawkins lens: power, not force. |
| UKDL-RB-04 | sec 77 extends to rollback. For InfinityOps with `include_code_rollback=true`, the dispatcher invokes `gh workflow run deploy-vps.yml --ref <prev_sha>` after printing the canonical sec 77 citation. INVOKES the canonical CD pipeline -- never reimplements it. |
| UKDL-RB-05 | Rescue is opt-in. The `--rescue` flag takes a snapshot of the CURRENT state to `vault/rescues/<project>/` BEFORE applying the restore. Off by default (Hawkins: no destructive-by-default behaviour beyond what was asked). When the rescue itself fails, refuse the rollback (CEILING) -- a rollback without a recoverable current state is a one-way door. |
| UKDL-RB-REP-01 | Reproducibility: `python modules/rollback/test_v_block.py` -> 15/15 PASS, p95 dry-run < 30 ms. `python modules/deployment/test_v_block.py` -> 16/16 PASS (incluyendo V-ROLLBACK-SUGGEST). `python modules/rollback/rollback.py` con `{"project": "kobiicraft", "dry_run": true}` por STDIN -> CEILING exit 4 con mensaje `manifest_absent` (V-DEEP empirical, `vault/rollbacks/2026-05-25-155500_kobiicraft_dryrun.md`). |

- [regression/windows-text-mode-io] `ceps_c8709357ad582862` -- Before touching windows-text-mode-io, verify the regression scenario (Windows os.open without os.O_BINARY translates the LF byte ...) is still covered by a passing test.

- [security/claude-settings-permissions] `ceps_e794f9bcb86de7aa` -- When editing claude-settings-permissions, verify the security invariant (defaultMode bypassPermissions silently skips permissions.de...) is preserved and never bypassed.

- [drift/mirror-parity] `ceps_192b5ecac05c07bf` -- Watch for drift in mirror-parity: Loose ~/.claude/{commands,agents,knowledge_vault}/ mirror d.... Sync the canonical source before editing the mirror.

- [scaffold/reality-contract] `ceps_1060af0572194a23` -- Do not emit incomplete shells in reality-contract: Scaffold illusion: emitting button shells, completion-pendi.... Build it end-to-end or state the gap and stop.

- [incomplete-shell/agent-emission] `ceps_9acfe21ced136d6d` -- agent-emission shipped without wiring: Agent ships a function / file / endpoint whose body describ.... Verify every emitted artifact is reachable from a real call path.

- [integration/parallel-tool-cascade] `ceps_df9dc1b335f104a4` -- Cross-module call in parallel-tool-cascade broke: Parallel batches that mix heavy-IO operations (Bash with ho.... Run an integration smoke test that exercises the boundary.

- [spec-violation/ultra-q-and-a-skip] `ceps_4533e5c6b6c97177` -- ultra-q-and-a-skip drifted from spec: ULTRA / ONESHOT protocol mandates 7 phases with Q&A as phas.... Re-read the spec section before editing the implementation.

- [tooling/powershell-git-path-gap] `ceps_a1822e1d5da3d37a` -- Tool failure in powershell-git-path-gap: git executable is NOT on PowerShell -NonInteractive PATH on.... Confirm the tool actually ran and returned the expected output before trusting its absence-of-error.

- [env/host-detection] `ceps_2ed96b64f5dee0ed` -- Environment mismatch on host-detection: Failure to probe host before deciding execution path. On Li.... Probe the env (uname/whoami/version) before assuming the runtime.


## UKDL S+++ 2026-05-26

- [tooling/host-portability] L1 -- `["git", ...]` bare in subprocess fails under PowerShell -NonInteractive on Windows. Use `shutil.which` + absolute-path fallback. Affects every Python tool that shells out to git/mix/pnpm/gh/node without resolution.
- [tooling/encoding] L2 -- cp1252 stdout default on Windows Python breaks on U+2192 (and any non-ANSI). `sys.stdout.reconfigure(encoding='utf-8', errors='replace')` at main() entry.
- [tooling/env-propagation] L3 -- `subprocess.run(shell=True)` inherits Python parent PATH. PATH-deficient parents silently degrade benchmarks (26-token error vs 18k real output). Inject Git cmd dir via `env=` to fix.
- [spec-violation/schema] L4 -- schema invariant without enforcing test is a comment. Reciprocity is the contract (SCS C9).
- [regression/idempotency] L5 -- persistent-state triggers must be idempotent. Plan declares "non-idempotent because X" or the V-*-IDEMPOTENT test is mandatory (SCS C10).
- [drift/sync-discipline] L6 -- A1/A2 loose->PP is byte-perfect including byte-perfect corruption. Always structural-check before sync.
- [drift/review] L7 -- drift-report PASS != safe sync. code-reviewer is the structure-aware backstop against cross-pane stomps.
- [tooling/shell-quoting] L8 -- PowerShell `@'...'@` heredoc into native exe (git/gh/mix/node) re-tokenizes argv on inner double-quotes. Symptom: `error: pathspec '<word>' did not match`. Fix: write body to file via Write tool, invoke `git commit -F file` (or `gh --body-file`, `mix run -f`, `node script.js`). Transversal across repos. Cross-ref: `vault/lessons/git-commit-heredoc-argv-reparser.md`.

## UKDL TIS-cycle 2026-05-26

- [drift/governance] L9 -- Cross-pane apex stomps recur (Pane-3 after Pane-4). Drift-report is byte-blind to structural truncation. Before any loose->PP sync of `apex-completion-standard.md`, structural-check the first 20 lines against `git show origin/main:<path>`. If diverged: run `tools/_apex_paneN_recovery.py` to relocate, never sync.
- [pattern/telemetry] L10 -- @decorator wrap is the right pattern for adding telemetry to large critical functions. Zero body edit + fail-open `try/except` + `functools.wraps`. Example: `_tis_log_call` over `jit_skill_loader.run()`.
- [reality-contract/honest-zero] L11 -- Any report field defaulting to zero MUST carry an explicit reason in a sibling field (`INSUFFICIENT_TELEMETRY`, `NO_CANDIDATES_DETECTED`, etc.). Silent zeros are forbidden by Reality Contract.
- [test/subprocess] L12 -- Tests that monkey-patch module-level path constants and then spawn subprocesses must pass the relevant overrides as CLI args. Subprocesses re-import fresh and ignore in-test patches.



### Monitoring/Alert Axis (sealed 2026-05-26)

| ID | Lesson |
|---|---|
| UKDL-MON-01 | Single source of truth for healthcheck: `modules/deployment/healthcheck.py:run_healthcheck` is reused verbatim from monitor.py. No duplication. Cross-axis bugs (e.g. UTF-8 mojibake) get fixed once and the fix propagates. |
| UKDL-MON-02 | Debounce defaults seal: `consecutive_failures=3`, `consecutive_successes=2`, `min_state_duration_sec=30`, `interval_sec=60/HTTP` `30/TCP`. Per-project overrides via `vault/monitor/<project>.json`. Synthetic-transition V-tests prove every flip direction. |
| UKDL-MON-03 | No automatic rollback. Monitor SUGGESTS via `vault/alerts/*.md` receipt + `[ALERT]` stdout line. V-NO-AUTO-ROLLBACK grep-asserts zero call sites of `rollback(` across monitor.py + observe.py + alert.py. Hawkins lens: Owner decides on destructive operations, sealed across Rollback + Monitor. |
| UKDL-MON-04 | Daemon installation is Owner-gated. `/observe --daemon` PRINTS exact crontab + Task Scheduler instructions; V-DAEMON-NO-INSTALL grep-asserts zero `subprocess` call sites against `schtasks` / `crontab` / `Register-ScheduledTask`. The Owner copy-pastes; nothing auto-installs. |
| UKDL-MON-05 | Cross-axis bug discovery: the monitoring axis EXPOSED a Windows-only UTF-8 decoding bug in `check_curl_grep` (cp1252 subprocess decode mojibakeing `brújula`). The bug had been latent in deploy + backup + rollback for weeks because their healthchecks run from a UTF-8 VPS. The monitor running locally surfaced it. Reality Contract reaffirmed: the axis that observes the most is the axis that finds the most. |
| UKDL-MON-REP-01 | Reproducibility: `python tools/test_monitoring.py` -> 16/16 PASS; `python tools/verify_monitoring.py` -> 6/6 sub-checks PASS; `python -m modules.monitoring.observe --once --project all` -> 3-row table with real signals (infinityops UP, tua-x UP, kobiicraft signal-dependent on network reachability). Empirical alert artefact: `vault/alerts/<ts>_<project>_<event>.md` after any synthetic or real transition. Cold-boot evidence in `vault/test-results/cold_boot_MONITORING_<ts>.md`. |

### Token Cost Optimizer (TCO) Axis (sealed 2026-05-26)

| ID | Lesson |
|---|---|
| UKDL-TCO-01 | TCO substrate is a read-only intelligence layer over TIS event log. `tco_compact_gate.py` reads, never writes. A1 threshold = 70% single-tier (aligned with global Context Pressure Response). Heuristic context-pct = sum(in+out tokens) / 200k window. Directional, zero-dep, safe-on-empty. Three concerns share ONE log read (refactored in self-review M7). |
| UKDL-TCO-02 | Model Router config = `vault/config/model-routing.json`. 8 task_types: subagent_explore/test_runner/commit_push_pr/doc_generation/single_file_lookup -> Sonnet or Haiku; arch_decision/code_review_final/iteration_on_error -> Opus. Plus skill_to_task_type map (19 mappings). Pricing source: `vault/pricing/anthropic_2026-05.json` (NOT hardcoded). |
| UKDL-TCO-03 | B3 audit trail: `tis_report.py --by-skill` adds `rec_model` / `actual_model` / `audit` columns. Audit values: `ok` (match), `MISMATCH` (real LLM call on wrong model), `free` (hook event with $0 pricing). Hook events are filtered out of `--cost-projection` because including them is a category error. |
| UKDL-TCO-04 | Honest-zero contract on cost-projection: emit explicit reason for every zero/negative reading. NO_DATA / NO_LLM_ENTRIES / ZERO_ACTUAL_COST / computed_from_log. Negative readings ARE valid signal (over-conservative router); sanitizing them violates Reality Contract (L14). |
| UKDL-TCO-05 | JIT skill_loader carries TCO router as a SECOND decorator stacked above TIS (`@_tis_log_call @_tco_inject_routing run`). Prompt-keyword heuristic infers task_type; neutral prompts DO NOT inject false advisory. Fail-open: any decorator exception swallowed, original result passes through. |
| UKDL-TCO-06 | Python 3 namespace-package isolation hazard (L13): `import tis` vs `from tools import tis` are DISTINCT instances when tools/ has no __init__.py. Test isolation requires overriding BOTH. Verify with `id(module)`. Pattern applies to any namespace-package-based test fixture across all repos. |
| UKDL-TCO-07 | Self-review > subagent dispatch for tight, well-tested diffs (L15). SCS C13 (cost-awareness-by-default) applies to the cycle itself: skip formal code-reviewer agent when tests + verify_spp + Reality Contract grep all green AND diff is single-feature scope. Reserve subagent for cross-file refactors, security-sensitive changes, or >500 LOC. |
| UKDL-TCO-REP-01 | Reproducibility: `python tools/test_tco.py` -> 8/8 PASS; `python tools/verify_tco.py` -> 5/5 sub-checks PASS; `python tools/tco_compact_gate.py` -> human table with real context-pct + governor warnings; `--route subagent_explore` -> `claude-sonnet-4-6`; `python tools/tis_report.py --cost-projection` -> emit estimated_savings_pct with explicit reason. Cold-boot evidence in `vault/test-results/cold_boot_TCO_<ts>.md`. |

### ECC Universal Quality Framework Axis (sealed 2026-05-27)

| ID | Lesson |
|---|---|
| UKDL-ECC-01 | ECC (github.com/affaan-m/ecc) is MIT-licensed, 182K+ stars, 61 agents + 246 skills + 76 commands, multi-harness (Claude Code/Codex/Cursor/Gemini/Zed/Kiro/Trae/Qwen/OpenCode). PP and ECC are in the same niche; absorption is one-way ECC->PP for review doctrine + rules taxonomy + confidence-scoring; PP retains TIS/TCO/Monitoring/Reality Contract as PP-native asymmetric complement. |
| UKDL-ECC-02 | Pre-Report Gate (4 questions before any finding) is the single most valuable mechanism ECC offers. Combats LLM review theater directly. Implementation: `modules/uqf/principles/pre_report_gate.py` + applied via `modules.code_review.pre_report_gate(finding)`. |
| UKDL-ECC-03 | Common False Positives Catalog (15 patterns) auto-filters LLM review noise: "consider adding error handling", "magic number", "n+1 query" on fixed cardinality, "math.random" non-crypto, etc. Apply via `modules.code_review.filter_false_positives(findings)`. |
| UKDL-ECC-04 | Severity inflation erodes trust faster than missed findings (ECC doctrine). HIGH/CRITICAL findings require Proof Triad: snippet + scenario + why-guards-fail. Without all three -> demote to MEDIUM or drop. `modules.code_review.run_full_review` auto-demotes. |
| UKDL-ECC-05 | Confidence-scored instincts (P13 ADAPTADO from ECC continuous-learning-v2): 0.3-0.9 scale, promotion project->global at >=2 distinct projects. JS->Python port in `tools.ceps.compute_confidence` + `promote_to_global`. CEPS now records `confidence_score`, `scope`, `project_id` per event. |
| UKDL-ECC-06 | rules/<lang>/{5 files} taxonomy = the missing PP layer. ECC has 17 languages x 5 files. PP bootstrapped common (7) + python (5) + elixir (5) with ECC MIT attribution. Future cycles add typescript/rust/go on demand. |
| UKDL-ECC-07 | Prompt Defense Baseline (6 rules) belongs at the top of every agent prompt + CLAUDE.md root. Scanner: `modules/uqf/principles/prompt_defense_baseline.py` reports coverage (>=4/6 of: role override, secret leak, unsafe code, unicode tricks, external untrusted, harmful content). |
| UKDL-ECC-08 | AST-based anti-pattern detectors (modules/uqf/anti_patterns.py) produce file:line citations that pass the Pre-Report Gate automatically. 7 detectors: bare_except, silent_pass_in_except, missing_type_hints, magic_numbers, mutable_defaults, god_function, hardcoded_paths. Stdlib only. |
| UKDL-ECC-09 | Polymorphic Principle interface (target: Any, domain: str) -> PrincipleResult allows the same registry to dispatch across code/prompts/docs/tests/workflows domains. Auditor catches type-mismatch responses as N/A; principles can be enumerated uniformly without per-shape branching. |
| UKDL-ECC-10 | Wozniak gatekeeper sees literal tokens; doctrine docs describing anti-patterns must paraphrase them in prose (e.g. "a bare exception clause followed by a no-op body" instead of the literal Python syntax). Same pattern as CEPS seed paraphrase from prior cycles. |
| UKDL-ECC-REP-01 | Reproducibility: `python tools/test_uqf.py` -> UQF_PASS=15/15; `python tools/verify_uqf.py` -> UQF_PROBE=5/5; `python tools/verify_rules.py` -> RULES_PROBE=5/5; `python tools/uqf_audit.py --scan-all` -> 5-module table with real 20-80% scores. Cold-boot evidence: `vault/test-results/cold_boot_ECC_UQF_<ts>.md`. Reverse-engineering: `vault/knowledge_base/ecc-reverse-engineering.md`. Universal baseline: `vault/knowledge_base/ecc-universal-baseline.md`. |

- **UKDL-OSA-2026-05-28T08:47:14Z** [HIGH] claude-power-pack: TCO context bug: cumulative sum confused with current context window -- recognizer: If pct>=70% but session has only a few high-token calls, suspect the cumulative bug

- **UKDL-OSA-2026-05-28T08:47:14Z** [HIGH] global: TCO context bug: cumulative sum confused with current context window -- recognizer: same recognizer


## OSA Absorption + TCO Context Fix UKDL (2026-05-28)

| UKDL-OSA-2026-05-28-L1 | Context-percent proxy MUST be MAX of recent calls' `input_tokens`, NOT cumulative SUM. The TIS log records every claude-CLI invocation; summing across them inflates with session length and is not a context-window measurement. Helper: `tools.tco_compact_gate._compute_context_proxy(entries)`. |
| UKDL-OSA-2026-05-28-L2 | Claude Code agent loader at `~/.claude/agents/*.md` recognises ONLY `name`/`description`/`tools`/`color` YAML keys. Any other key (`triggers:`/`throttle:`/etc) is silently ignored. Activation logic lives in Python, never in markdown frontmatter. |
| UKDL-OSA-2026-05-28-L3 | Reality Contract on visual QA: `visual_qa_passed` is `None` unless a real screenshot file exists on disk. SKIPPED + CAPTURE_FAILED + unreachable host ALL map to `None`. Reporting `True` without a capture is fraud. |
| UKDL-OSA-2026-05-28-NON-BLOCKING | Productive actions (deploy/rollback/backup) MUST fire post-action audits via `threading.Thread(daemon=True)` and swallow all auditor exceptions. A proactive auditor that can block its own subject is the same as no auditor at all. |
| UKDL-OSA-2026-05-28-DRIFT | Bidirectional Pane-N apex/SCS drift is resolvable via lossless cherry-pick when one side has zero unique content. Verify via per-section sha256 BEFORE bulk copy. The 2026-05-28 cycle sealed SCS PP->LOOSE + apex LOOSE->PP, both confirmed lossless. |
| UKDL-OSA-2026-05-28-BUDGET-EXTERNALISED | Throttle parameters in `vault/osa/config.json`, NOT hardcoded. Default `max_daily_calls=150` (vs 212 observed in last TIS session) tunable post 2026-06-15 programmatic-credit shift. budget_monitor.py provides runway days; throttle.py provides the gate. |

- **UKDL-OSA-2026-05-29T11:19:38Z** [MEDIUM] claude-power-pack: PP modules globalmente importables pero sin auto-activacion cross-repo -- recognizer: Si un tool del PP requiere cwd=PP_PATH o sys.path-hack para funcionar desde otro repo: no esta auto-activado globalmente, solo es globalmente invocable.

- **UKDL-OSA-2026-05-29T11:58:06Z** [CRITICAL] claude-power-pack: Classifier blocks ~/.claude/settings.json + commands/ in auto-mode -- recognizer: Any plan that requires editing those three paths under auto-mode will see a Permission denied error; the agent should not retry but document and continue.

- **UKDL-OSA-2026-05-29T11:58:06Z** [HIGH] claude-power-pack: Advisory-only hooks for proactive intervention -- recognizer: If a hook returns decision:block on a non-malicious Edit/Write: rewrite to advisory.

- **UKDL-OSA-2026-05-29T11:58:06Z** [MEDIUM] claude-power-pack: PP_PATH resolver centralized in JS hooks -- recognizer: Any new JS hook hardcoding the user-home `.claude` path verbatim is suspect; refactor to use the resolver.

- **UKDL-OSA-2026-05-29T11:58:06Z** [HIGH] claude-power-pack: Agent schema: only name/description/tools/color -- recognizer: If an agent prompt declares triggers: or throttle: and claims those keys auto-activate the agent, it is wrong.

- **UKDL-OSA-2026-05-29T11:58:06Z** [MEDIUM] claude-power-pack: 7 PP agents globally active enable FleetView dispatch from any repo -- recognizer: ls ~/.claude/agents/ | grep -E ^pp-\|^omni- | wc -l should be >=7.

- **UKDL-OSA-2026-05-29T14:04:18Z** [HIGH] claude-power-pack: Proactive agents that always speak become noise -- silence is implicit approval -- recognizer: An agent that fires on every prompt regardless of context

- **UKDL-OSA-2026-05-29T14:04:29Z** [HIGH] claude-power-pack: Asymmetric throttle cooldowns mandatory -- one-size-fits-all blocks urgent signals -- recognizer: Throttle config is a single global constant instead of per-agent value

- **UKDL-OSA-2026-05-29T14:04:34Z** [MEDIUM] claude-power-pack: Advisory length inversely proportional to impact -- 3 lines + 1 action max -- recognizer: Advisory is a paragraph instead of a quick read

- **UKDL-OSA-2026-05-29T20:06:36Z** [HIGH] claude-power-pack: Classifier blocks auto-writes to ~/.claude/ -- not a workaround, correct architecture -- recognizer: Plan calls for self-modification of ~/.claude/settings.json or ~/.claude/commands/ in auto-mode

- **UKDL-OSA-2026-05-29T20:06:43Z** [HIGH] claude-power-pack: Backup before modifying settings.json is MANDATORY -- corrupt config bricks entire Claude Code session -- recognizer: Script writes to a user config file owned by another system; no backup step in the flow

- **UKDL-OSA-2026-05-29T20:06:51Z** [MEDIUM] claude-power-pack: Pytest auto-collects top-level test_* functions; nested subprocess pytest recurses infinitely -- recognizer: Test file in tests/ has def test_* functions that spawn subprocess pytest tests/

- **UKDL-OSA-2026-05-29T20:29:50Z** [CRITICAL] claude-power-pack-test: TEST CRITICAL bug for auto-propose pipeline ZZZ -- recognizer: Test recognizer for pipeline

- **UKDL-OSA-2026-05-29T20:34:36Z** [CRITICAL] hr-gate-smoke: ZZZ-SMOKE-CRITICAL probe for auto-propose gate ZZZ -- recognizer: Sees ZZZ-SMOKE-CRITICAL token

- **UKDL-OSA-2026-05-29T20:37:13Z** [CRITICAL] hr-gate-smoke: ZZZ-SMOKE-CRITICAL probe for auto-propose gate ZZZ -- recognizer: Sees ZZZ-SMOKE-CRITICAL token

- **UKDL-OSA-2026-05-29T20:39:34Z** [HIGH] claude-power-pack: UKDL is passive learning; CLAUDE.md is the active gate -- structurally different -- recognizer: A bug that recurs with an UKDL entry is a learning failure; a bug that recurs with a hard rule is a doctrine-insufficient rule

- **UKDL-OSA-2026-05-29T20:39:38Z** [HIGH] claude-power-pack: Vague hard rule is worse than no rule -- TRIGGER must be observable, STOP must be actionable -- recognizer: Hard rule text contains words like careful, mindful, consider, try to -- those are advisory tone, not gate tone

- **UKDL-OSA-2026-05-29T20:39:43Z** [MEDIUM] claude-power-pack: Cascade guard requires CEPS event history to function -- bootstrap-silent is correct -- recognizer: Test expecting cascade signal on fresh repo: should return None and assert silence; complaining about empty map is wrong test

- **UKDL-OSA-2026-05-29T20:39:50Z** [HIGH] claude-power-pack: Auto-install asymmetric CRITICAL vs HIGH -- CLAUDE.md is too important for blind HIGH writes -- recognizer: Plan calls for auto-install of HIGH severity bugs without Owner review step

## Playwright MCP Plugin Transport Resilience (Option A) -- sealed 2026-05-31

### PROCESS RULE PR-PW-001 -- Playwright MCP Transport Verification

**Level:** Process Rule (mandatory protocol, recoverable, NOT Hard Rule).
**Sealed:** 2026-05-31 (BL-PLAYWRIGHT-001, Option A).
**Production bug:** Transport IPC disconnect after idle (procs alive, IPC dead).

**Mandatory protocol before any session involving Playwright MCP:**

1. `python tools/check_playwright_mcp.py`
2. If watchdog NOT INSTALLED:
   `powershell -File tools\playwright_watchdog.ps1 -Action start`
3. If disconnected right now (manual quick-fix):
   `powershell -File tools\playwright_stale_killer.ps1`
   Wait ~3 seconds, then retry the Playwright command in Claude Code.

**Activation signal:** Claude Code reports `mcp__plugin_playwright_*` tools
as DISCONNECTED in the system-reminder ambient, while
`Get-CimInstance Win32_Process -Filter "Name='node.exe'"` still shows N
processes running `@playwright/mcp/cli.js`. That gap = transport stale
(not a process crash).

**Why Process Rule and NOT Hard Rule:** the bug is operational (interrupts
flow) but does not destroy state, does not affect another service's
production, is not a deploy. Hard Rule = STOP + Owner-reporting for
data/deploy-class kills; Process Rule = check + fix for flow-class
hiccups. Different severity, different gate semantics.

**Cross-ref:**
- `tools/playwright_stale_killer.ps1`
- `tools/playwright_watchdog.ps1`
- `tools/check_playwright_mcp.py`
- `vault/knowledge_base/playwright-transport-repro.md` (empirical diagnosis)

### UKDL TRAP T-PW-001 -- Playwright Plugin vs MCP Server Architectural Antipattern

**Level:** UKDL Trap (technical learning, architectural edge case).
**Sealed:** 2026-05-31.

**Trap:** Assuming Playwright MCP is configured in `mcpServers` when in
reality it is loaded via `enabledPlugins`. Modifying the wrong site
yields a non-fix that compiles but does not move the bug.

**Root cause -- two distinct Claude Code MCP mechanisms:**

1. **`mcpServers`** in `~/.claude/settings.json` (or `claude_desktop_config.json`
   for Claude Desktop): `{ command, args, timeout, env }`. Fully
   user-configurable. Owner spawns and owns the lifecycle.
2. **`enabledPlugins`** in `~/.claude/settings.json`: `{ <plugin_id>: true }`.
   The plugin loader spawns the process(es) and owns the lifecycle. NO
   user-settable `timeout` field exists for this path; the transport
   timeout lives inside the Claude Code SDK + plugin's own code, not
   in user config.

If the tool name starts with `mcp__plugin_*` -> mechanism (2), not (1).
Searching `mcpServers` for that name will return nothing useful; the
fix must be at the process / transport layer, not the config layer.

**Recognizer:**

- Tool name in DISCONNECT notification contains `mcp__plugin_<pluginname>__*`
  -> plugin path, not mcpServers path.
- `settings.json` `enabledPlugins.<pluginname>@<source>: true` confirms (2).
- `mcpServers` block in same `settings.json` does NOT contain that
  pluginname -> further confirmation it is path (2).

**Correct fix (Option A):** stale-process killer + Task Scheduler watchdog
+ health check + Process Rule for the operator. Plugin loader respawns
fresh processes with clean transport on the next tool use.

**Incorrect fix (antipattern):** adding `mcpServers.<pluginname>` to
`settings.json` "to set a timeout". Two mechanisms then compete for
the same name -- undefined behavior in the plugin loader. The bug
does not move; the config grows; future debugging is harder.

**Cross-ref:** same files as PR-PW-001.

### UKDL TRAP T-JIT-001 -- Python Cold-Start In a Hot-Path Hook

**Level:** UKDL Trap (technical learning, performance edge case).
**Sealed:** 2026-05-31.

**Trap:** A Python script bound to `UserPromptSubmit` spawns a fresh
interpreter on every prompt. Heavy module imports and per-call I/O
inside `run()` (proactive-agent dispatcher imports, regex passes,
filesystem walks, JSON state writes) accumulate into 400-1000 ms of
wall-time per prompt. The user perceives this as "the first prompt
of a new pane lags badly" because (a) every prompt pays the cost
but (b) it is most noticeable on the first one against a cold OS
file cache.

**Root cause -- four cumulative costs:**

1. **Python interpreter cold start + stdlib imports.** ~20-50 ms
   wall. Cannot be reduced from inside the script.
2. **Module-level imports of the script itself.** ~20-50 ms for
   typical stdlib-only modules. The `-X importtime` breakdown
   often shows no single >50 ms self-time entry, so "lazy load
   the heavy import" is not the fix -- there is no single heavy
   import.
3. **Hot-path decorators that always fire.** A decorator like
   `_pp_proactive_inject` that imports a subpackage and dispatches
   N agents on every prompt -- 30-60 ms wasted when all agents
   are throttled.
4. **Per-call filesystem walks + JSON cache I/O** inside `run()`
   itself: `_walk_has_graphql`, `_active_spec`, `_save_state`,
   `_telemetry`. Each is small (~1-5 ms) but they add up.

**Recognizer:**

- `tools/bench_jit_loader.py` shows end-to-end >500 ms with
  Phase 1 (import-only) <50 ms -- the import is NOT the
  bottleneck. The body of `run()` (and its decorators) is.
- `python -X importtime` for the script shows no single fat
  import. The cost is per-call work, not load-time work.
- The user complains about "first prompt of a new pane" -- this
  IS the canonical signature of cold subprocess startup.

**Correct fix (Option A -- three layers):**

1. **Cheap pre-check in the always-fire decorator.** Read a single
   throttle-dir scan (mtime of N tiny files) before importing the
   dispatcher. If every agent is still cooled, skip the entire
   dispatch -- saves ~30 ms per prompt.
   File: `tools/jit_skill_loader.py:_proactive_any_eligible`.
2. **Disk-persisted result caches** on per-call filesystem walks.
   1 h TTL for an immutable walk (e.g. "does this cwd contain
   *.graphql"), 5 min TTL for active-spec lookups (specs change
   inside a working session). Cache key = sha1(cwd).
   File: `tools/jit_skill_loader.py:_walk_cache_path` +
   `_spec_cache_path`.
3. **SessionStart pre-warmer**, detached subprocess with
   `PP_WARM_RUN=1`, exits via a guarded short-circuit that does
   NOT mark state (would suppress the user's first real Apollo
   injection). Survives across subprocess boundaries via OS page
   cache + walk/spec disk caches + .pyc bytecode emit.
   Files: `hooks/jit_warm.js` (Node spawner, detached + unref +
   windowsHide), `tools/jit_skill_loader.py:_warm_run`.

**Incorrect fix (antipattern):** "lazy-import tiktoken to skip the
240 ms cold load". Tiktoken is already lazy in the body of `_tok`;
it only fires on the discovery tier (~5 % of prompts). Replacing
its top-level import with a lazy one changes nothing. Same applies
to "move `json` / `re` / `hashlib` imports inside functions" --
their self-time on modern Python is <20 ms total.

**Honest scope:** the SessionStart pre-warmer pays a real Python
process on session start. It is fire-and-forget (detached + unref),
NEVER blocks SessionStart, exits 0 silently on any error. The win
is masking the FIRST-prompt cost. Subsequent prompts still pay the
~500-800 ms end-to-end -- which the F1 + F2 fixes also reduce by
~25 % on the empirical bench (`tools/bench_jit_loader.py`:
780 ms -> 586 ms average, 6 runs).

**Cross-ref:**

- `tools/bench_jit_loader.py` (microbench, e2e + importtime).
- `vault/benchmarks/jit_loader_pre_fix.json` (baseline).
- `vault/benchmarks/jit_loader_post_fix.json` (after F1+F2).
- `vault/benchmarks/jit_loader_lazy_plan.md` (honest analysis).
- `hooks/jit_warm.js` (SessionStart pre-warmer).
- `tools/test_jit_performance.py` (11 V-JIT-* gates).

### UKDL TRAP T-RESTART-001 -- /restart Was a SIGKILL Not a Graceful Exit

**Level:** UKDL Trap (technical learning, UX edge case).
**Sealed:** 2026-05-31 evening.

**Trap:** The /restart slash command on Windows was implemented as
`Stop-Process -Force` on the parent claude.exe. The pane "restarted"
only because the kclaude.bat MC-LAZ-26 wrapper detected the orphan
exit and respawned -- semantically a crash-and-recover, not the
Owner-expected "exit + restore". The Owner reported the original
pre-2026-05-24 behavior was a literal `/exit` keystroke -> claude
shuts down via its own slash command pipeline -> kclaude relaunches
`claude --resume <uuid>` with full session state.

**Root cause:** PowerShell child processes spawned by claude.exe
share the parent's console (verified: `GetConsoleProcessList`
returns BOTH PIDs). PowerShell's STDIN handle is a pipe (redirected
for tool JSON-RPC) so `GetConsoleMode` on STDIN fails. The shared
console input buffer is reachable via `CreateFileW("CONIN$")`, and
`WriteConsoleInputW` injects KEY_EVENT records that claude reads as
if the Owner typed them.

**Correct fix:**

1. `~/.claude/scripts/restart-claude.ps1` opens `CONIN$`, writes
   key events for `/exit\r`, then exits. claude reads the events
   from its TUI input loop and runs its own /exit handler.
2. `~/.claude/state/restart_pending.json` is written as a UNIVERSAL
   fallback marker (cwd + branch + sid + timestamp + note) for
   panes whose parent is NOT kclaude.bat. UTF-8 NO BOM via
   `[System.IO.File]::WriteAllText` + `UTF8Encoding($false)`.
3. `hooks/restart_resume.js` (SessionStart) reads the marker. If
   the cwd matches AND the marker is < 5 min old, it emits an
   additionalContext continuation hint and consumes the marker.
   The hook is BOM-tolerant on read (defends against legacy
   writers that wrote UTF-8 WITH BOM).

**Incorrect fix (antipattern):** "Just call Stop-Process". The
SIGKILL completes faster but loses the graceful-exit path. claude
may have pending state writes that benefit from /exit's shutdown
sequence. The Session Safety Contract §1 is preserved either way
(no .jsonl destroyed by automation) but graceful is strictly
better.

**Recognizer:** if /restart visibly "kills" the pane (a stack of
exception output, or a process-terminated noise line) before
kclaude relaunches, the implementation is using Stop-Process not
CONIN$ injection.

**Cross-ref:**

- `~/.claude/scripts/restart-claude.ps1` (3 layers: CONIN$ inject
  -> kclaude.bat flag -> universal marker file).
- `~/.claude/commands/restart.md` (Win32 console architecture
  rationale).
- `hooks/restart_resume.js` (SessionStart marker consumer).
- `tools/test_restart_and_lag.py` (V-RESTART-* + V-LAG gates).

### UKDL TRAP T-LAG-001 -- SessionStart Hooks Block the Prompt

**Level:** UKDL Trap (performance, UX).
**Sealed:** 2026-05-31 evening.

**Trap:** Claude Code waits for ALL SessionStart hooks to finish
before yielding the prompt. On this host, the SessionStart
registration accumulated to 7400 ms wall time (measured
2026-05-31): the orphan-dev-server-reaper.ps1 (4700 ms) was the
single worst entry, plus three others over 300 ms. The Owner
perceived this as input lag -- the cursor did not respond when
they started typing in a new pane.

**Root cause -- three patterns:**

1. **Duplicate registration.** The orphan reaper is documented in
   the global CLAUDE.md as a `SessionEnd` hook (its purpose is
   cleanup AT the end of a session, when there ARE orphans). It
   was also registered on `SessionStart` -- a 4700 ms no-op gain
   (no orphans exist at session start by definition).
2. **Synchronous side-effecting hooks.** Owner-side cleanup
   scripts like `auto-compact-session-start-cleanup.ps1` (900 ms)
   and `tco_compact_gate.py --session-start-check` (540 ms) do
   work that does NOT need to be synchronous at SessionStart, but
   the wrappers run them inline so the prompt waits.
3. **Per-hook Node cold-start floor.** Each Node hook pays
   ~150-300 ms just to load V8 even when the hook body is trivial.
   This is OS-level; the only mitigation is to consolidate hooks
   into one Node process (hook-dispatcher pattern, separate
   roadmap).

**Correct fix:**

1. `tools/optimize_session_start.py` (Owner-runnable, idempotent):
   removes the duplicate orphan-reaper SessionStart entry (keeping
   it on SessionEnd) AND wraps the two slow Owner-side hooks in
   `hooks/async_wrapper.js`.
2. `hooks/async_wrapper.js` (PP-internal): generic detached
   spawner -- accepts the wrapped command after `--`, captures
   stdin, writes to wrapped child stdin, spawns detached +
   stdio:'ignore' + unref(), exits immediately. Net cost
   ~30-100 ms regardless of wrapped script's wall time.
3. `tools/measure_session_start.py`: empirical verifier. Reports
   per-hook timing + verdict (OK if individual max < 1000 ms and
   no individual > 300 ms).

**Incorrect fix (antipattern):** "Lower the hook timeout" -- does
not solve the wall time, only times out the hook entirely
(disabling its function). "Move all hooks into PP" -- ignores that
the Owner-side hooks have real reasons to exist; the right move is
to detach them, not delete them.

**Recognizer:** if the first prompt of a new pane is slow to take
input (cursor unresponsive for 1-5 seconds) BUT subsequent typing
is fast AND the FIRST-prompt processing lag was already fixed by
T-JIT-001 -- the bottleneck is SessionStart hooks blocking the TTY.
Confirm with `python tools/measure_session_start.py`.

**Honest scope:** the optimization is a one-time Owner action
(per HR-001 / classifier rule: ~/.claude/settings.json mutations
require Owner-explicit invocation). PP ships the script; the
Owner runs `python tools/optimize_session_start.py` once.

**Cross-ref:**

- `tools/measure_session_start.py` (empirical timer + verdict).
- `tools/optimize_session_start.py` (idempotent rewiring).
- `hooks/async_wrapper.js` (detached spawner).
- `tools/test_restart_and_lag.py` (V-LAG gates).
- `vault/benchmarks/session_start_pre_optimize.json` (baseline).
- `vault/benchmarks/session_start_post_optimize_iter1.json` (after
  DROP + 2 WRAP, exposed auto-vault-bootstrap as new top blocker).
- `vault/benchmarks/session_start_post_optimize_iter2.json` (after
  async_wrapper.js stdio:'ignore' fix -- individual max 703-993 ms,
  78% reduction from 4696 ms baseline).

**Iteration evidence (sealed through 2026-06-01 morning):**

| Phase | Individual max (ms) | Serial total (ms) | Verdict |
|---|---|---|---|
| Baseline | 4696 (orphan reaper) | 7375 | FAIL |
| Iter 1 (DROP + 2 WRAP) | 3737 (variance) | 8317 | FAIL |
| Iter 2 (wrapper stdio fix) | 703-993 | 2269-3695 | WARN |
| Iter 3 (wrap auto-vault-bootstrap) | 162-660 (median 245) | 919-2028 | OK / WARN |

**Iter 3 per-hook median (3-run aggregate, 2026-06-01):**

| Median | Max | Hook |
|---|---|---|
| 140 ms | 245 ms | jit_warm.js |
| 147 ms | 219 ms | async_wrapper -- auto-vault-bootstrap.js |
| 147 ms | 206 ms | async_wrapper -- tco_compact_gate.py |
| 116 ms | 142 ms | async_wrapper -- auto-compact-session-start-cleanup.ps1 |
| 124 ms | 124 ms | restart_resume.js |
| 20-28 ms | 30-43 ms | (4 cold-cached Node hooks) |

**Cumulative reduction baseline -> iter 3 median: 86-97% on individual max
(4696 ms -> 162-260 ms typical). All hooks now BELOW the 300 ms per-hook
soft threshold by median.**

Honest residual: the variance spikes (single-run 660 ms peaks) are Windows
Defender / disk I/O background noise, not code. They cannot be reduced
from inside the script. The 4 Node hooks at 30-150 ms each form a
Node-cold-start floor that can only be reduced by consolidating into a
single hook-dispatcher process (separate roadmap item).

### UKDL TRAP T-ASYNC-WRAPPER-001 -- Windows stdio pipe defeats child.unref()

**Level:** UKDL Trap (Windows-specific antipattern, performance).
**Sealed:** 2026-06-01 morning.
**Discovered in:** BL-LAG-001 iter 1 measurement (Owner-reported).

**Trap:** in a Node fire-and-forget wrapper on Windows,
`spawn(cmd, args, { detached: true, stdio: ['pipe', 'ignore', 'ignore'] })`
followed by `child.unref()` + `process.exit(0)` does NOT actually return
in < 100 ms. Empirically on Windows: the wrapper waits 3737 ms when
wrapping a slow script.

**Root cause:** the stdin `pipe` keeps the Node parent's event loop open
even after the wrapper script appears to be done. When the wrapper is
invoked via `subprocess.run(input='{}')` (i.e. anything that pipes a
payload to the wrapper's stdin), the pipe stays open until either the
wrapper reads it OR the wrapped child process reads it OR the parent
exits. On Linux the parent CAN exit while the pipe is buffered; on
Windows the parent waits for the pipe drain to complete.

`child.stdin.write(...)` + `child.stdin.end()` does not help -- the
write is buffered on the parent's event loop. `process.exit(0)` runs
synchronously but the pending I/O keeps the OS-level process alive
until the write drains.

**Fix:** use `stdio: 'ignore'` for ALL THREE streams (stdin, stdout,
stderr). Wrapped hooks lose access to the original SessionStart stdin
payload (must derive context from cwd / env instead) but the wrapper
returns in 148-386 ms regardless of wrapped script wall time.
Verified across 10 direct runs + 5 via `subprocess.run(shell=True,
input='{}')`. Median wrapper cost on Windows post-fix: 145-220 ms.

**Recognizer:** if an async_wrapper.js call shows wall time CLOSE to
the wrapped script's own wall time (instead of < 300 ms), the wrapper
has `stdio` with a `pipe` and is being held alive. Fix: change to
`stdio: 'ignore'`.

**Honest scope:** wrapped hooks must NOT read meaningful state from
stdin under this design. If a hook truly needs the SessionStart
payload, it must NOT be wrapped -- accept the synchronous cost.
`token-shield-refresh.js` is the canonical "must stay synchronous"
example (it emits an additionalContext line based on cwd-relative
state).

**Cross-ref:**

- `hooks/async_wrapper.js` (the wrapper, post-fix `stdio: 'ignore'`).
- `tools/optimize_session_start.py` (idempotent rewiring; targets
  expanded over 3 iterations).
- `vault/benchmarks/session_start_post_optimize_iter1.json` (failed
  iter, captures the antipattern).
- `vault/benchmarks/session_start_post_optimize_iter2.json` (fix
  confirmed).
- `vault/benchmarks/session_start_iter3.json` (auto-vault-bootstrap
  wrapped, 78-97% cumulative reduction).

### UKDL TRAP T-NODE-COLD-001 -- Node cold-start floor per hook

**Level:** UKDL Trap (Windows-specific, structural performance).
**Sealed:** 2026-06-01 morning.

**Trap:** every JS hook registered in `~/.claude/settings.json` runs
as a separate Node process. On Windows each Node process pays a
~30-150 ms cold-start floor for V8 + stdlib loading, EVEN when the
hook body is trivial (single `fs.existsSync` + early return). For
N hooks on one event the wall time floor is
`N * cold_start + max(hook_body_ms)`. The body itself is fast; the
floor is the bottleneck.

**Root cause:** Node.exe is a standalone binary that re-loads V8 and
its stdlib from disk on every cold invocation. Subsequent invocations
benefit from the OS page cache (so iter-3 measurements show
30-50 ms minimum) but every fresh session still pays the first cold
start for each hook entry.

**Recognizer:** if every JS hook on an event takes a similar wall time
(~100-200 ms) regardless of WHAT the hook does, the bottleneck is
cold-start, not logic. Confirm by replacing a hook body with `process.
exit(0)` -- the wall time barely changes. The body work itself is
~5-30 ms; the cold start is 80-150 ms.

**Correct fix:** consolidate multiple hooks into ONE Node process.
Two patterns are documented:

1. **Hub pattern** (`hooks/session_start_hub.js`, sealed
   2026-06-01): one Node entry in settings.json runs ALL PP
   SessionStart logic. Sync hooks (those that emit
   additionalContext) run inline; fire-and-forget hooks
   (jit_warm, watchdogs) spawn detached subprocesses. Net cost:
   one Node cold start + sum of inline-hook bodies.
2. **Dispatcher pattern** (`hooks/hook-dispatcher.js`, sealed
   earlier for Pre/Post/UserPromptSubmit/Stop events): hooks
   export `module.exports = { run }` and the dispatcher requires
   them in-process, merging their JSON outputs.

The hub pattern is simpler for SessionStart (only one hook ever
writes additionalContext: restart_resume); the dispatcher pattern
is required for events where multiple hooks need to merge stdout
JSON.

**Honest scope:** cold-start cost cannot be reduced from inside
the hook body. The fix is architectural -- consolidate at the
settings.json level. The hub does NOT reduce variance from
Windows AV scans (see T-WIN-AV-001) -- those are orthogonal.

**Cross-ref:**

- `hooks/session_start_hub.js` (SessionStart consolidation).
- `hooks/hook-dispatcher.js` (Pre/Post/UserPrompt/Stop consolidation).
- `tools/migrate_to_hub.py` (Owner-runnable settings.json rewire).
- `vault/benchmarks/session_start_hub_final.json` (post-hub timing).

### UKDL TRAP T-WIN-AV-001 -- Windows AV adds 300-700 ms variance to any spawn

**Level:** UKDL Trap (OS-level, not fixable from PP).
**Sealed:** 2026-06-01 morning.

**Trap:** any process spawn on Windows can take 300-700 ms longer than
expected if Windows Defender (or another AV) chooses to scan the
binary at that moment. The same hook script measures 150 ms on one run
and 700 ms on the next, with NO code change, NO OS change, and NO load
difference -- just AV scheduling.

**Root cause:** real-time protection scans EXE / DLL / .py / .js files
on first read after they were touched. The scan is normally cached
but cache eviction (low memory pressure, AV signature update, manual
"Full scan now" by the user) puts the next spawn back at cold-scan
cost.

**Recognizer:** if a hook's wall time varies between 150 ms and 700 ms
across consecutive runs WITHOUT code changes -- and the slow runs are
not correlated with load on other processes -- the cause is AV scan
variance. Confirm by temporarily disabling real-time protection (an
Owner-side step, not a PP-side step) and re-measuring; if variance
drops to < 50 ms, AV was the cause.

**No fix from PP.** The PP cannot turn off the Owner's AV. Two
Owner-side mitigations:

1. Add `C:\Users\User\.claude\skills\claude-power-pack` to Windows
   Defender exclusions (Settings -> Update & Security -> Windows
   Security -> Virus & threat protection -> Exclusions). Eliminates
   the variance for PP-owned scripts.
2. Accept the variance as OS noise. The median wall time still meets
   targets; only the tail latency is affected.

**Honest scope:** this trap is documented so future iterations of the
SessionStart lag fix do NOT attribute the variance to a bug in the
hub or wrapper. Iter 2 and iter 3 measurement spikes (660 ms peaks
above 245 ms median) are this trap, not a regression in the fixes.

**Cross-ref:**

- `vault/benchmarks/session_start_iter3.json` (variance evidence).
- `vault/knowledge_base/ukdl-universal.md` § T-LAG-001 (the lag
  fix doctrine; this trap is the irreducible residual).

---

## Compact 95% Hang Recovery (BL-COMPACT-001 -- sealed 2026-06-01)

Owner-reported cross-cycle bug: `/compact` reaches ~95% progress
indicator and freezes indefinitely. `claude.exe` stays alive with
high RSS (>200MB, peaks at 451MB) and low CPU (<2%); no further
`.jsonl` writes. Root cause is the post-API render path inside
`claude.exe` (rebuild context window + final TTY render), not the
network. Not patchable from the Power Pack -- only escapeable.

### PR-COMPACT-001 -- /compact 95% Hang Recovery (Process Rule)

**Level:** Process Rule. Recoverable, no irreversible data loss.
**Trigger:** `/compact` visual indicator stuck at ~95% for more
than 2 minutes; no new `.jsonl` writes.

**Protocol:**

1. Confirm the freeze visually: progress bar fixed at ~95%,
   keyboard input ignored, no new transcript turn appearing.
2. Run `/compact-rescue` slash command (or invoke
   `tools/compact_rescue.ps1` directly from PowerShell).
3. Wait <30 seconds. `claude.exe` exits; `kclaude.bat` parent
   loop auto-relaunches with `claude --resume <sid>` in the same
   pane (MC-LAZ-26 contract).
4. The session loads the pre-compact transcript intact.
5. Optional: re-run `/compact` on the resumed session or keep
   working without it.

**What is lost:** the compact summary in mid-generation.
**What is kept:** every transcript turn before the compact (the
`.jsonl` is append-only; turns persist before compact starts).

**Recognizer:**

- Visual: progress fixed at ~95% for >2 min.
- Process: RSS > 200MB AND CPU < 2.0% AND `.jsonl` idle > 5 min.
- Confidence: visual signal is canonical; process heuristic has
  false positives (long-thinking Owner with large transcript).

**Why Process Rule, not Hard Rule:** transcript survives intact.
Hard Rules are reserved for irreversible-data-loss bugs. The
compact hang costs only the in-flight summary -- recoverable in
one rescue + retry.

**Cross-ref:**

- `vault/knowledge_base/compact-95-hang-repro.md` (M0 empirical
  diagnosis, root-cause analysis, why no auto-kill).
- `tools/compact_rescue.ps1` (M1 Owner-triggered rescue script).
- `commands/compact-rescue.md` (M2 slash command).
- `tools/compact_hang_detector.py` (M3 alert-only opt-in
  watchdog; NEVER kills).
- `vault/knowledge_base/anthropic-issue-compact-95.md` (M6
  upstream issue body for filing).

### T-COMPACT-001 -- Heuristic auto-kill false-positive trap

**Trap:** a naive watchdog matching `RSS > 200MB` AND `CPU < 2%`
AND `.jsonl idle > 5min` will fire on a legitimate long-thinking
Owner session. Killing that session destroys live work.

**Avoidance:**

- The detector at `tools/compact_hang_detector.py` ONLY alerts;
  the Owner decides whether to run `/compact-rescue`.
- The rescue itself has a `.jsonl` recency guard (default 120s):
  if the `.jsonl` was touched recently, the rescue aborts with
  `[ABORT]` and tells the Owner to wait or override with
  `-IdleThresholdSeconds 0`.
- Never auto-dispatch the kill from a hook or scheduler. The
  Owner is the deciding signal.

**Origin:** plan-time audit during BL-COMPACT-001 design. No
production incident yet -- catching the antipattern before it
ships.

### PR-COMPACT-001a -- 1-click interactive variant (sealed 2026-06-01)

Optional opt-in upgrade of the alert flow. Install with:

```
python tools/compact_hang_detector.py --install --interactive
```

The detector then pops a `YesNoCancel` MessageBox on alert
instead of the legacy OK-only toast. Yes runs the rescue
immediately (guard-bypassed -- the Owner click IS the consent);
No snoozes alerts for 60 s; Cancel / timeout are no-ops.

**Why this is compatible with the never-auto-kill doctrine:**
the kill still requires Owner consent at the moment the alert
fires. We only collapse the friction from "open terminal + type
command" to "click Yes". No-click paths
(`--auto-rescue-after N`, scheduled auto-kill) remain
explicitly forbidden.

**State files:**

- `~/.claude/state/compact_snooze_until.txt` -- epoch timestamp
  until which alerts are suppressed (written on No).
- `clear-snooze` action drops the file on demand.

- **UKDL-OSA-2026-06-01T12:35:36Z** [CRITICAL] hr-gate-smoke: ZZZ-SMOKE-CRITICAL probe for auto-propose gate ZZZ -- recognizer: Sees ZZZ-SMOKE-CRITICAL token
