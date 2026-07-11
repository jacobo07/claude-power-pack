# Universal Knowledge / Documentation / Lessons — cross-reference ledger

This file is the "ukdl-universal" reference index — each row points
at a sealed lesson, learning, or session note that is broadly
applicable across PP-shipped projects and not specific to one repo.

Entries are append-only; never remove a row. If a lesson is
superseded, append the superseding row referring back to the older.

## Universal Meta-Systems Runtime (SCS C86) — 2026-07-10

Runtime that makes the 7 universal meta-systems executable in any repo WITHOUT
reimplementing them. The corpus (SHA `45dd1f9`) is machine-parseable doctrine —
**38 named operations** across 7 datasets (PART V ops with `*Guarantee:*` +
optional `*Never:*`, PART VI pipelines, PART VII lifecycle + `GV-N` gates). The
runtime parses that contract layer, applies the repo's noun-map
(`.pp_meta_systems.json`, generic fail-open, propose-from-CLAUDE.md), and emits a
domain-substituted, gate-checked execution plan. Architecture: **Option C
(interpreter)**, chosen over B (7 runners = reimplementation) and A (corpus-blind
= empty abstraction). Audit == MS-6 applied to the repo (no separate audit engine
— that would reimplement the Absence Engine). Carries:
`modules/universal-meta-systems/runtime/` (corpus_parser · noun_map · executor ·
loop · runtime); test `tools/test_meta_systems_runtime.py` (7 V-gates ×3 hermetic).

### PROCESS RULE PR-META-SYSTEMS-EXPOSE-NOT-REIMPLEMENT-001
The meta-systems runtime NEVER reimplements a meta-system. It reads the corpus,
applies the noun-map, and produces an execution plan. The logic lives in the
corpus; the runtime is an interpreter, not a copy. Corollary 1: a per-meta-system
"runner" that encodes the meta-system's own logic in code is a reimplementation
and is rejected — the parser + noun-map is the only permitted mechanism.
Corollary 2: an "audit engine" that re-derives gap-detection logic is a
reimplementation of MS-6; audit MUST be `apply(MS-6, repo)`.

### UKDL TRAP T-META-SYSTEMS-CORPUS-READONLY-001
The meta-systems corpus is read-only for the runtime. No corpus file may be
modified by the parser, executor, loop runner, or audit engine. Modifying the
corpus from the runtime is an architecture violation. Detection: V-CORPUS-UNTOUCHED
snapshots the datasets hash before/after a full run and asserts equality (+ git
HEAD @ `45dd1f9`). Origin: an editor-that-writes-back would couple the universal
source to one consumer; the runtime must interpret doctrine, never edit it.

## Workspace Recovery Control Plane — Execution Mode (SCS C83) — 2026-07-10

| Ref | File | Why it matters |
|---|---|---|
| UKDL-WRCP-01 | `vault/lessons/recovery-control-plane-scs-c83.md` | Sealed lesson: Reality-Scan verdict (Execution Mode, not a new Control Plane), the 3 root causes (1-pane-per-repo, shutdown!=restart, only-works-in-PP), the Sprint-0 wiring fix, HR-CONTROL-PLANE-EXCLUSIVE-RESP-001 + T-RECOVERY-HOST-COUPLING-001 + PR-RECOVERY-MANIFEST-SOURCE-001, and Owner-gated orphan-activation follow-ups. |
| UKDL-WRCP-02 | `modules/cpc_os/vscode_autorun.py` (`generate_from_pane_map`) + `tools/snapshot_auto_writer.ps1` | The fix: automatic restore artifact (tasks.json) now derives from the corrected pane_map.json (all repos, all panes, no truncation) via one shared adapter — killing the host-coupled per-cwd/legacy-snapshot regression. |
| UKDL-WRCP-03 | `tools/test_recovery_control_plane.py` | 6 V-gates x3 hermetic proving all-panes/multi-repo/parity/no-duplicate-manifest/exclusive-responsibility. Complements test_restore_all_panes.py (different layer). |

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

### UKDL TRAP T-MCP-RECONNECT-001 -- stdio mcpServer -32000 is NOT externally recoverable

**Level:** UKDL Trap (architectural edge case).
**Sealed:** 2026-06-04 (BL-MCP-STABILITY-001).
**Production reality:** `magic-ui` + `coplay-mcp` stdio mcpServers found DEAD
(zero processes) emitting JSON-RPC `-32000`.

**Trap:** Treating a stdio `mcpServer` `-32000` like a network/plugin failure
and "fixing" it with an external watchdog/launcher (Task Scheduler relaunch,
a `npx <pkg>` respawn script). This does NOT reconnect the server -- it
creates an ORPHAN.

**Root cause -- who owns the pipe:** a stdio `mcpServer` (the `~/.claude.json`
`mcpServers` mechanism, T-PW-001 path 1) is a CHILD of `claude.exe`,
communicating over claude's own stdin/stdout pipe. When it exits you get
`-32000`. An externally-spawned process has its OWN stdio and is not wired to
claude's pipe -- it is a leaked orphan, not a reconnection. Only a Claude-side
action resurrects it:
1. `/mcp` -> reconnect `<name>` (client re-spawns the child).
2. Restart Claude Code (full re-spawn).

**Contrast with the plugin path (playwright, T-PW-001 path 2):** the plugin
LOADER owns the lifecycle and respawns clean transport on next tool use, so
killing stale procs IS recovery -- there an external watchdog works. The two
mechanisms have OPPOSITE recovery models; do not apply the playwright watchdog
design to a stdio server.

**Recognizer:**
- Server name appears under `mcpServers` in `~/.claude.json` (not
  `mcp__plugin_*`) -> stdio path -> external relaunch is wrong.
- `-32000` + zero matching node/bun/uv processes -> the client-owned child
  died -> Claude-side reconnect only.

**Correct fix:** DETECTION + ADVISORY (`tools/mcp_health_check.py` reports
DEAD + prints the `/mcp` reconnect command) + telemetry to classify the
death-mode. NEVER an external relauncher for a stdio server.

**Cross-ref:** `tools/mcp_health_check.py`, `tools/verify_mcp_health.py`,
`vault/telemetry/mcp_health/mcp_state.jsonl`,
`vault/knowledge_base/mcp-stability.md`.

### UKDL TRAP T-MCP-IDLE-001 -- stdio death-mode is unknown until classified (PENDING)

**Level:** UKDL Trap (PENDING -- not yet sealed; awaiting telemetry).
**Opened:** 2026-06-04 (BL-MCP-STABILITY-001).

**Trap (anticipated):** stdio mcpServers may die at session start vs after
idle vs randomly. Each death-mode needs a DIFFERENT fix (config/spawn fix vs
keep-alive vs crash handling). Asserting one cause without evidence is a guess.

**Status:** the Owner could not name when `magic-ui` dies ("not sure / always
-32000"). Rather than guess, `tools/mcp_health_check.py --source session_start`
appends a classified row to `vault/telemetry/mcp_health/mcp_state.jsonl` each
run. After N sessions the rows reveal the pattern; THEN this trap gets sealed
with the empirical death-mode + its specific fix. Do not seal on a hypothesis.

### UKDL TRAP T-SESSIONFOLD-001 -- folding a SessionStart hook needs payload + mechanism care

**Level:** UKDL Trap (architectural edge case).
**Sealed:** 2026-06-04 (BL-SESSION-FOLD-001).

**Trap A -- wrong mechanism.** Reaching for `migrate_hub_fold.py` to fold
SessionStart. That tool folds Stop / UserPromptSubmit / PostToolUse into
`hook-dispatcher.js` CHAIN_MAP and EXPLICITLY leaves SessionStart untouched
(guard #3 in its docstring). SessionStart uses a DIFFERENT model:
`session_start_hub.js` detached-spawns the folded hooks. Running
`migrate_hub_fold.py` against SessionStart is a no-op. Use the dedicated
`migrate_sessionstart_fold.py`.

**Trap B -- payload starvation.** A SessionStart hook that reads `cwd` /
`session_id` from stdin CANNOT be folded by a naive detached spawn: a detached
child gets no stdin, so the hook silently no-ops (cwd undefined -> early
return). Fix: the hub passes the payload via env (`PP_EVT_CWD` / `PP_EVT_SID`,
the existing `cpc_register` / `jit_warm` pattern) AND each folded hook reads env
as a fallback when stdin is empty -- `const cwd = (event && event.cwd) ||
process.env.PP_EVT_CWD;`. Verify the env path does REAL work (not just that the
hub spawns the child): run the hook with empty stdin + the env var set and
confirm its side effect lands.

**Trap C -- folding the wrong class.** Only fire-and-forget hooks (side-effect
only, silence on stdout) are safe to detach. stdout-consumed hooks (they emit
`additionalContext`) and load-bearing recovery hooks (lazarus-*, restart-*,
terminal-slot-recorder writing the Lazarus registry) MUST stay standalone --
detaching them drops their consumed output or their recovery write. The biggest
wall-time hooks are often exactly the recovery ones, so the safe fold buys
spawn-count, not the multi-second win.

**Recognizer:** grep the candidate hooks for `additionalContext` /
`process.stdout.write` (stdout-consumed) and for writes under `lazarus/` or a
recovery registry (load-bearing). Anything that matches stays standalone.

**Cross-ref:** `tools/migrate_sessionstart_fold.py`,
`hooks/session_start_hub.js`, `vault/knowledge_base/sessionstart-fold.md`.

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
3. The SessionStart marker logic reads the marker. If the cwd
   matches AND the marker is < 5 min old, it emits an
   additionalContext continuation hint and consumes the marker.
   It is BOM-tolerant on read (defends against legacy writers that
   wrote UTF-8 WITH BOM). **Fold note (2026-06-22, PF-7):** this
   logic runs as `hookRestartResume` INSIDE
   `hooks/session_start_hub.js` (hub-fold 2026-06-04). The
   standalone `hooks/restart_resume.js` is REFERENCE-ONLY and is
   NOT registered in settings.json.

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
- `hooks/session_start_hub.js` (hookRestartResume -- the LIVE marker
  consumer); `hooks/restart_resume.js` (reference-only, folded).
- `tools/test_restart_and_lag.py` (V-RESTART-* + V-LAG gates);
  `tools/test_restart_kclear.py` (PF-1..7 recursive-audit gates).

### UKDL TRAP T-RESTART-SELFHEAL-OBSOLETE-001 -- restart-target.json Self-Heal Is Permanently Inert (Reader Without Producer)

**Level:** UKDL Trap (CLASE-0 orphan consumer; dead recovery path).
**Sealed:** 2026-06-22 (restart-kclear recursive audit PF-1).

**Trap:** `~/.claude/hooks/restart-target-consumer.js` (registered
standalone in settings.json SessionStart) reads
`~/.claude/lazarus/restart-target.json`, compares `target.session_id`
to the new session's id, and on MISMATCH spawns
`~/.claude/scripts/lazarus-revive.ps1 -Launch -OnlySession <sid>` as a
self-heal (sealed "BL-NULL-ERROR Step 5"). But **nothing writes
`restart-target.json`** -- the producer `Write-RestartTarget` was
DELETED on 2026-05-24 when /restart stopped killing claude
(`vault/lessons/restart-command-pane-eviction.md`, "Removed the
Restore-LiveJsonl and Write-RestartTarget machinery"). The consumer was
never removed. It runs every SessionStart and always early-exits at
`!fs.existsSync(TARGET_FILE)`. The advertised self-heal NEVER fires =
false safety net + a wasted spawn per session.

**Why NOT to "fix" it by reviving the producer (the obvious trap):**
the consumer matches on `session_id` EQUALITY, but a successful
/restart lands a *fresh* session_id by design -- the SessionStart hub
matches its `restart_pending.json` marker by **cwd, not sid**, exactly
because `claude --resume`/`--continue` does not guarantee the same
session_id in the SessionStart payload. So a revived
`Write-RestartTarget` would make the consumer read EVERY successful
restart as a mismatch and spawn a spurious `lazarus-revive` every time
-- strictly worse than dead. (Audited and rejected 2026-06-22.)

**Correct resolution:** the mechanism is OBSOLETE BY DESIGN (it only
made sense in the kill-and-respawn era). The live resume path is
`restart_pending.json` (cwd-matched, hub). The dead-mechanism surface is
actually THREE references, all harmless no-ops while no producer exists:
(1) `~/.claude/hooks/restart-target-consumer.js` (SessionStart
match/revive), (2) its `lazarus-revive.ps1` spawn target, and (3)
`~/.claude/hooks/lazarus-janitor.js` "BL-NULL-ERROR Step 9" zombie-marker
pruner -- whose comment "the consumer deletes the marker after a
SessionStart" is now counterfactual. Owner-side step: deregister
`restart-target-consumer.js` from `~/.claude/settings.json` SessionStart
(HR-001: agent documents, Owner applies); the `lazarus-janitor.js` pruner
can stay (it no-ops and would still serve a future producer). Until then
all three are harmless. (Janitor reference added: restart-kclear audit
R2-1, 2026-06-22.)

**Recognizer:** a registered hook whose first real action is
`if (!existsSync(FILE)) exit(0)` against a file no producer writes =
orphan consumer. Grep the codebase for the WRITE of that path; zero
hits = dead.

### UKDL TRAP T-RAM-DEDUP-001 -- Two RAM Advisories, Recalibration Reached the Orphan Not the Live Hook

**Level:** UKDL Trap (drift; alert fatigue / monitor theater).
**Sealed:** 2026-06-22 (restart-kclear recursive audit PF-3/PF-4).

**Trap:** Two RAM advisories fire on the Stop-chain:
`modules/zero-crash/hooks/ram-watchdog.js` (was 1500 MB) and
`context_monitor` via `context-watchdog.py` (20/28 GB, the M4
auto-reset overlay). The 2026-06-04 RAM Optimization Sprint recalibrated
thresholds UP (8/11 -> 20/28 GB) to kill alert fatigue -- but that fix
landed in `tools/ram_guard.py` + `context_monitor`, while the dominant
LIVE hook (`ram-watchdog.js`) kept firing at 1.5 GB, i.e. on essentially
every session-end. Meanwhile `hooks/ram-guard-stop.js` (the wrapper that
exposes ram_guard's richer gaming-mode + snapshot-before-OOM advisory)
is NOT in the Stop-chain and NOT in settings.json -- orphan.

**Fix:** raise `ram-watchdog.js` `RSS_THRESHOLD_MB` to 20480 (20 GB warn
level) so the two stop double-firing on healthy sessions; document that
context_monitor (WorkingSet64, 20/28 GB) is the AUTHORITATIVE trip and
ram-watchdog is a coarse tasklist-private-WS backstop (different metric,
summed across procs -- not a precise mirror). Keep `ram-guard-stop.js`
dormant + header-deprecated; do NOT register it alongside ram-watchdog
or the advisory double-fires again.

**Recognizer:** a recalibration commit that edits a library/module but
not the hook that actually fires on the event = the fix never ships.
Always trace from the registered hook (settings.json / CHAIN_MAP)
BACKWARD to the constant, not forward from the module.

### UKDL TRAP T-RESTART-INTENT-ORPHAN-001 -- cpc_os/restart.py Validates an Intent Nobody Submits

**Level:** UKDL Trap (orphan module; intent-only-by-design).
**Sealed:** 2026-06-22 (restart-kclear recursive audit PF-5).

**Trap:** `modules/cpc_os/restart.py::restart_intent` is a §208.2
acceptance-contract validator (cwd/session/dedup invariants) with NO
live caller -- the shipped /restart path bypasses it entirely. Its own
docstring already declares it intent-only and explicitly refuses to
write `restart_pending.json` (to avoid a second writer destabilising the
marker). It is exercised only by tests + dataset docs.

**Resolution:** documented inert-by-design (not a regression). Available
to wire as a future pre-flight gate inside restart-claude.ps1 (a python
call) IF the Owner wants the §208.2 invariants enforced before the
CONIN$ inject. Until then, leaving it uncalled is correct.

### UKDL TRAP T-KCLEAR-RAM-SEMANTICS-001 -- /kclear Checkpoints, /clear Frees RAM

**Level:** UKDL Trap (expectation gap; honest-gate doctrine).
**Sealed:** 2026-06-22 (restart-kclear recursive audit PF-6).

**Trap:** the mental model "/kclear frees RAM" is FALSE.
`~/.claude/commands/kclear.md` -> `tools/session_checkpoint.py record`
writes a handoff + insights + lesson atomically and then SUGGESTS the
native `/clear`. It does NOT kill claude.exe and does NOT shrink the V8
heap. RAM is reclaimed by the subsequent native `/clear` (context
reset), not by /kclear. Likewise `work_state` is saved by the AUTO-RESET
path (auto_reset_orchestrator via context-watchdog), NOT by manual
/kclear.

**Honest gate (Reality Contract):** a `V-KCLEAR-RAM-DROPS` gate that
asserts /kclear reclaims RAM would be theater. The defensible gate
asserts (a) checkpoint integrity -- handoff + insights written
atomically; (b) the /clear suggestion is emitted; (c) RAM-free is
attributed to native /clear in the docs. Empirical RAM-delta belongs to
a native-/clear measurement, not to /kclear.

**Recognizer:** before writing a `V-X-DOES-Y` gate, confirm X actually
performs Y. If the doc/command only *recommends* the action that does Y,
the gate must test the recommendation + the real effect's true owner.

### UKDL TRAP T-PERSISTENT-SESSIONS-TASKS-CONFLICT-001 -- Two Reload Restorers Double Every Pane

**Level:** UKDL Trap (redundant mechanism; UX duplication).
**Sealed:** 2026-06-22 (no-duplicate-panes execution).

**Trap:** `terminal.integrated.enablePersistentSessions: true` +
`task.allowAutomaticTasks: "on"` + `.vscode/tasks.json` restore tasks with
`runOptions.runOn: "folderOpen"` = duplication GUARANTEED on Reload Window.
Persistent sessions reconnects the live terminals AND the `folderOpen` tasks
spawn fresh `kclaude.bat --resume <sid>` terminals on top -> 2x terminals per
session. The Owner sees two panes per repo. It is NOT a reload-kills-terminals
bug (reload is non-destructive by default); it is two restorers running at once.

**Why one dumb lever can't fix both reload and cold start:** `folderOpen` fires
identically on reload (terminals alive) and cold start (terminals gone), so the
task layer can satisfy reload-clean OR cold-restore, never both. Satisfying both
needs a GUARDED restorer (check whether a terminal already exists for the cwd
before launching) -- see T-TASK-NO-GUARD-001.

**Fix:** `task.allowAutomaticTasks: "off"` in Cursor User settings -- persistent
sessions becomes the sole reload restorer (exact N, zero dup); cold-start restore
goes manual via the PP Sessions panel / `pane_map.md`. One global, reversible
setting; mutates no repo's tasks.json (multi-pane hazard avoided).

**Recognizer:** two mechanisms both claiming to restore the same resource on the
same trigger = duplication. Pick one primary; demote the other to a guarded
fallback or disable it.

### UKDL TRAP T-TASK-NO-GUARD-001 -- A Restore Task With No Liveness Check Always Launches

**Level:** UKDL Trap (idempotence; fail-open discipline).
**Sealed:** 2026-06-22 (no-duplicate-panes execution).

**Trap:** a `claude --resume` launcher (tasks.json `folderOpen` task, autoresume
wrapper, extension restorer) that does NOT first check whether a terminal/session
is already live for that cwd will launch unconditionally -- duplicating any pane
the persistent pty host already restored. The dumb `folderOpen` task is the
canonical instance.

**Fix:** any auto-restorer must diff the desired resumable set (`pane_map.json`,
transcript-on-disk) against the live terminals (by cwd) and launch `--resume`
ONLY where no terminal exists. The guard is fail-open: if the liveness probe
errors, launch anyway -- a duplicate pane is recoverable, a lost pane is not.

**Recognizer:** an auto-launch path whose first action is the launch (no "does it
already exist?" probe) = a duplicator under any retry/reload.

### UKDL TRAP T-CMD-FLASH-EXTERNAL-001 -- cmd.exe Flash Sources Live Outside the PP Repo

**Level:** UKDL Trap (audit-scope blindness).
**Sealed:** 2026-06-23 (cmd-flash remaining-sources execution).

**Trap:** F0 (b144eba) made `audit_spawn_windows.py` PASS 42/42 on PP-repo hooks,
but flashes persisted because the audit's scope was the REPO only. Real flash
sources also live in: (1) `~/.claude/settings.json` hook *commands* -- a
`powershell.exe`/`cmd.exe` launcher without `-WindowStyle Hidden` flashes (the
SessionEnd orphan-reaper, settings.json:342, was exactly this); (2) live-only
hooks in `~/.claude/hooks/` that have NO canonical copy in the repo (see
T-LIVE-ONLY-HOOK-FLASH-001); (3) Claude Code's OWN spawning of hook processes /
Bash / PowerShell tool calls + plugin-internal MCP children -- NOT PP-controllable.

**Fix:** extend the audit -- `--settings` gates settings.json launchers,
`--live` scans the global hook dir. Owner-global fixes (allow-listed
`Edit(~/.claude/hooks/**)`, backup settings.json first): reaper +WindowStyle
Hidden; `bug-hunter-learning.js` (PostToolUse/Bash, fired every Bash) +
`zero-issue-gate.js` (live mirror) +windowsHide. Note honestly what stays:
per-prompt flashes that survive are almost certainly CC-native (FUENTE 4),
outside PP control -- verified by the Owner's empirical 3-prompt test.

**Recognizer:** a green repo-scoped gate + a symptom that persists = the gate's
SCOPE is wrong, not the code. Widen to every path the symptom can originate from
(config, mirror, third-party, host) before concluding "fixed".

### UKDL TRAP T-LIVE-ONLY-HOOK-FLASH-001 -- Global Hooks With No Canonical Copy Are Invisible to a Repo Gate

**Level:** UKDL Trap (split-brain; orphan-direction inverse).
**Sealed:** 2026-06-23 (cmd-flash remaining-sources execution).

**Trap:** the split-brain doctrine usually means canonical (repo) drifts from
live (`~/.claude/hooks/`). The INVERSE also exists: live hooks with NO canonical
counterpart at all (`bug-hunter-learning.js`, `baseline-translator.js`,
`dna-flywheel.js`, `kobiiclaw-autoresearch.js`, `lazarus-{heartbeat,snapshot}.js`,
`quality-skill-gate.js`, `prd-keyword-sentinel.js`, `session-init.js`). A
repo-scoped audit is STRUCTURALLY blind to them. Many fire: the live
`hook-dispatcher.js` runs them via CHAIN_MAP (spawned children) or an in-process
require() bundle. The dispatcher spawns children with `windowsHide:true`, but a
child's OWN `execSync('git ...')` without `windowsHide` can still flash as a
GRANDCHILD (a hidden, console-less parent makes the grandchild allocate a new
console).

**Fix:** audit `--live` enumerates them; fix = add `windowsHide:true` to each
firing hook's execSync/spawn options. Because mass-editing the global hook dir
while sibling panes are active is the multi-pane hazard
([[feedback_edit_modified_since_read_is_live_concurrent_pane]]), batch the
remaining firing hooks behind one Owner approval rather than editing N global
files unilaterally mid-session.

**Recognizer:** `--live` advisory shows a hook absent from the repo glob = a
live-only hook; cross-check the dispatcher CHAIN_MAP / in-process list to learn
if it fires before deciding it is dead.

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

### UKDL TRAP T-PERF-VERIFY-SPP-PARALLEL-001 -- Naive ThreadPoolExecutor on verify_spp regresses wall time

**Level:** UKDL Trap (process-architecture, fixable but non-trivial).
**Sealed:** 2026-06-01 BL-BENCH-ROADMAP S1.1 attempt.

**Trap:** wrapping the `verify_spp.py` row runner in
`ThreadPoolExecutor(max_workers=6)` should -- on paper -- collapse
21 sequential rows into max(row_time). Empirically on this Windows
host it produced the OPPOSITE: a clean serial run measured 155 s
(audit commit 61d7807); the same machine with the parallel patch
measured **>300 s** (bench_all cap hit). 1.94x REGRESSION.

**Root cause hypotheses (ordered by likelihood):**

1. **Shared subprocess resource contention.** Multiple rows spawn
   `python` / `node` test harnesses that read the same files
   (`~/.claude/settings.json`, vault/state, vault/benchmarks). Under
   6-way parallel load the kernel file cache thrashes and per-row
   wall time GROWS rather than shrinks.
2. **Windows process-creation amplification.** Spawning 6
   subprocess.run calls within milliseconds of each other on
   Windows is materially heavier than POSIX fork+exec; the OS
   process-creation lock + AV scan trigger (T-WIN-AV-001) combine.
3. **Per-row timeout amplification.** When ANY row hits its own
   timeout (the 4 STRICT FAIL rows -- mirror-parity, drift-report,
   paths+secrets, hooks-registration -- each hit a 15-30 s cap),
   the parallel runner still waits for the slowest cap rather than
   short-circuiting.
4. **L3 row contention.** The `l3-engine` row has a 360 s budget
   and spawns Node + heavy file I/O. Under parallel load it may
   grow further or block on shared resources used by another row.

**Recognizer:** wall time on `python tools/verify_spp.py` exceeds
the prior serial baseline by 50 % or more after a
ThreadPoolExecutor / multiprocessing patch -- AND no individual row
shows a faster `elapsed` line than its serial counterpart.

**Fix (immediate):** rollback the patch. The serial path is the
default; the proven 155 s wall time is the target floor under the
current row set.

**Fix (architectural -- future work, NOT recommended for one shot):**

- Identify the slowest 2 rows empirically and run THOSE serially at
  the end; pool the remaining ~19 short rows.
- Cap PROBE_MAX_WORKERS at 2 (matches the bash-bridge-doctrine
  recommendation for mutating-or-spawning Windows tool calls).
- Add per-row barrier / fence so AV cold-scan is not multiplied.

**Decision rule:** do NOT attempt verify_spp parallelization again
without first writing a per-row timing profile under controlled
load, and only attempt with PROBE_MAX_WORKERS <= 2. The 90 %
reduction theoretical was overoptimistic; realistic upper bound on
this Windows + this AV + this row mix is ~30 % under tightly
controlled parallel mode.

**Cross-ref:**

- `vault/benchmarks/audit_verify_spp_2026-06-01T12-47-42Z.json`
  (sealed serial baseline 155.3 s).
- `vault/benchmarks/ledger.json` `S0_baseline` entry
  (post-attempt-1 measurement showing >300 s timeout).
- `feedback_parallel_read_partial_transport_fail.md` (the harness
  pipe pressure that capped my workers=6 attempt).

---

### UKDL TRAP T-TOOL-SENTINEL-RECOVERY-001 -- "[Tool result missing due to internal error]" recovery is forensic, not retry

**Level:** UKDL Trap (transversal, every repo, every host).
**Sealed:** 2026-06-01 BL-BENCH-ROADMAP iteration after Owner
re-reported "me pasa en todos mis repos" cross-project.

**Trap:** a tool call returns `[Tool result missing due to internal
error]` (the universal-drop sentinel). The naive instinct is to
retry the same call. On a long session that often results in:

- the underlying work DID land (Write / Edit / Bash / PowerShell
  side-effects already occurred), and a naive retry double-applies
  the operation; OR
- the underlying work did NOT land, and a naive retry hits the same
  multiplex-frame-budget condition and drops again, producing a
  same-shape failure twice in a row (Anti-Antipattern Rule 12
  violation).

Worst case: the dropped tool call combines with a concurrent
`<task-notification>` and the agent yields a turn with NO assistant
text. The Owner sees a frozen screen and only ESC recovers. This
is the canonical "dead screen" hang the Owner re-reports
cross-repo.

**Root cause (transversal, not fixable from inside the agent):**

The Claude Code harness multiplexes tool-result frames over a
single bidirectional channel. At high context length AND under
PreToolUse hook fanout (7-15 hooks per Edit/Bash, 3 per Read),
the frame budget pressure can drop the LAST frame in a wide
parallel fan-out OR a solo frame on a hooks-decorated tool call.
The MSYS2 bridge that backs `Bash` on Windows compounds this -- it
is a known-fragile transport (see `feedback_bash_bridge_*`).

**Recognizer:** the literal string
`[Tool result missing due to internal error]` in a tool result
block. ALWAYS verify state directly before any further action.

**Forensic recovery (mandatory, not optional):**

1. **DO NOT retry the same tool call.** Re-issuing the exact same
   shape almost always reproduces the failure on the same multiplex
   frame OR double-applies a side-effect.
2. **Verify state directly.** For `Edit` / `Write`: `Read` the
   target file to see if the change landed. For `Bash` /
   `PowerShell`: check the side-effect (file created? commit
   landed? service started?) via a DIFFERENT tool (Glob, Read,
   git rev-parse, etc).
3. **If state shows the work landed:** acknowledge and continue;
   the sentinel was a frame drop AFTER the work, not before.
4. **If state shows the work did NOT land:** re-issue the operation
   via a DIFFERENT tool family. Edit -> Write (whole-file rewrite).
   Bash -> PowerShell (different transport). Multi-file batch ->
   single-file at a time.
5. **If a `<task-notification>` arrived in the same turn:** the
   "(sentinel + notification) = dead screen" rule kicks in. The
   turn MUST end with assistant text. Always name the dropped
   frame, name the verification done, name the next concrete
   action.

**Transversal mitigations the agent CAN apply (already in CLAUDE.md
Background Process Hygiene + bash-bridge-doctrine-v2):**

- Cap parallel reads at 4 on Windows.
- Same-file Edits always sequential.
- Producer-consumer pairs always sequential (mutation batch ->
  consumption batch).
- Agent / background-spawn tool calls always SOLO in their batch.
- For long mutations: prefer `Write` (whole-file) over chained
  `Edit` calls when the file is small enough -- Write produces
  ONE tool-result frame; chained Edits produce N frames each at
  risk of drop.
- Use PowerShell instead of Bash for `git` / `python` / `node` /
  `mix` on Windows.

**Transversal mitigations the agent CANNOT apply (out of scope --
require harness or transport layer change):**

- Make the multiplex frame budget unbounded.
- Replace the MSYS2 Bash bridge with a native Win32 sh.
- Disable PreToolUse hook fanout to reduce frame pressure.
- Force AV exclusion on `C:\Users\User\.claude\`.

These are Owner-side OR Anthropic-side concerns. The PP cannot
ship a fix for the harness itself.

**Anti-Waiting closure (sealed reinforcement, 2026-06-01):**

NEVER end a turn with a passive "Waiting..." / "Standing by..." /
"The harness will notify me when..." sentence. This combines with
the sentinel + task-notification frame interaction to produce the
exact dead-screen hang the Owner reports across all repos. The
turn MUST end with either:

- a concrete artifact landed this turn (commit hash, file path
  written, gate passed), OR
- a concrete question requiring Owner action (a question mark, a
  decision needed), OR
- a concrete next-action sentence ("Running X next." -- not "I'll
  run X when..."). Mandatory.

This is Anti-Waiting Rule G of CLAUDE.md, restated for emphasis
because the canonical hang reproduced this session.

**Cross-ref:**

- `~/.claude/CLAUDE.md` § Anti-Waiting doctrine (rules A-G).
- `memory/feedback_bash_bridge_transversal_hang.md` (the bash
  bridge cousin failure mode).
- `memory/feedback_parallel_read_partial_transport_fail.md`
  (the same-shape sentinel in parallel-read fanouts).
- `memory/feedback_opaque_tool_internal_error.md` (prior wording
  of the recovery rule).
- This session's specific reproduction: SOLO Edit on
  `tools/verify_spp.py` after a 100+ tool-call session, sentinel
  fired, `git checkout HEAD -- <file>` confirmed the Edit had not
  landed (state verification > retry).

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

- **UKDL-OSA-2026-06-01T14:41:08Z** [CRITICAL] hr-gate-smoke: ZZZ-SMOKE-CRITICAL probe for auto-propose gate ZZZ -- recognizer: Sees ZZZ-SMOKE-CRITICAL token

### UKDL TRAP T-ORPHAN-MODULE-001 -- A module that imports but nobody calls

**Level:** UKDL Trap
**Sealed:** 2026-06-02, BL-INTEGRATION-WIRING

**Trap:** Build a complete PP module with passing unit V-gates but
never connect it to an activation surface (hook, signal, decorator,
slash command, agent). The module exists in the repo and imports
cleanly, so the build *feels* done -- but it never executes in
production. The dataset-build cycle (2026-06-01) shipped seven modules
this way; an audit the next day found FIVE of them ORPHAN: importable,
zero references in settings.json / agents/ / signals/ / the JIT loader.

**Recognizer (how to detect an orphan at audit time):**
- `grep -r <module_name> ~/.claude/settings.json hooks/ modules/pp_agents/signals/ tools/jit_skill_loader.py` returns nothing, AND
- no slash command in `commands/` imports it, AND
- no agent in `~/.claude/agents/` references it.
If all three are empty, the module is ORPHAN regardless of how many
unit tests pass.

**Fix:** In the SAME build cycle (or the immediately following one),
classify the module's activation cost and wire it via the mechanism
matched to that cost (the SCS C27 table). Then prove activation -- not
just import -- with a consolidated gate
(`tools/verify_integration_wiring.py`, 9/9 this cycle). The empirical
difference is: "module importable" (necessary) vs "module invoked on a
real event" (the actual done condition).

**Why it persists:** unit V-gates test the module in isolation; they
pass whether or not anything calls it. Only an *activation* gate --
one that fires the hook / signal / decorator and observes the module's
effect -- closes the loop. Build the activation gate, not just the
unit gate.

**Cross-ref:** SCS C27 (Integration-Wiring-by-default),
`feedback_automation_mechanism_by_measurement` (mechanism chosen by
measured latency, never tool name).

- **UKDL-OSA-2026-06-03T17:32:43Z** [HIGH] claude-power-pack: State-snapshot writer shipped without the restore reader -- system half-built -- recognizer: A snapshot/checkpoint/state file exists but no script READS it to act -> system incomplete. Grep for the reader before declaring a recovery feature done.

- **UKDL-CPCOS-AUTORUN-PREMISE-2026-06-06** [HIGH] claude-power-pack: The restore task's premise ("restore script emits `cd <cwd> && claude` WITHOUT --resume") was DISPROVEN by source -- R1-R4 were already shipped+tested (snapshot.json non-null session_id per pane, restore_panes.ps1 PRINTS `claude --resume <id>` [exact]/[repo-latest], KobiiSports Resort already in snapshot, restore-panes.md complete; gate 15/15). Verified before building; did NOT blind-rebuild a working system. Only the genuine gap -- auto-vs-manual resume -- was new work. Recognizer: when a feature request matches a recent BL-* memory, READ the live source + RUN the existing done-gate BEFORE coding; the premise may already be false. Cross-ref `feedback_plan_code_is_hypothesis_verify_source`, `feedback_audit_disproves_owner_premise`.

- **UKDL-CPCOS-AUTORUN-2026-06-06** [MEDIUM] claude-power-pack: Restore "auto-resume on Cursor open" closes the manual-paste step with a per-repo `.vscode/tasks.json` whose tasks carry `runOptions.runOn: folderOpen` + `presentation.panel: dedicated`, one task per DISTINCT pane resume (deduped like restore_panes.ps1). Generator `modules/cpc_os/vscode_autorun.py` is MERGE-not-clobber (keeps the Owner's own tasks, replaces only `CPC-Restore:`-labelled), backup-first (`tasks.json.cpc-bak`, also the safety net when an existing tasks.json is JSONC the strict parser cannot read), opt-in via `restore_panes.ps1 -AutoRun` (default stays manual-paste -- no destructive-by-default). Point-in-time: session ids rotate per session -> regenerate each restore. First run needs Cursor's one-time "Allow Automatic Tasks" trust click per repo. Gate test_vscode_autorun.py 10/10 (parse/dedup/merge/backup/idempotent/JSONC-safe/from-snapshot/dry-run) + snapshot 15/15.

- **UKDL-CPCOS-AUTOWRITER-2026-06-06** [HIGH] claude-power-pack: restore_panes WITHOUT a periodic Task Scheduler writer = protection only if the Owner REMEMBERS to run -AutoRun. For an UNSEEN crash (3am reboot) the `.vscode/tasks.json` must already be on disk BEFORE the crash. `tools/snapshot_auto_writer.ps1` (Task Scheduler `pp-snapshot-writer`, 15-min indefinite repeat, RunLevel Limited / no-admin) each cycle refreshes session_snapshot.json from the registry + writes tasks.json per repo. LITERAL-CORRECTION (honor intent): the task said "run restore_panes.ps1 -AutoRun" but that ALSO opens Cursor windows -- a 15-min background job opening windows is wrong; the writer composes the vscode_autorun generator DIRECTLY (write-only, no windows). MECHANISM-VERIFY: `python -m pkg.module` raised a runpy double-import RuntimeWarning -> switched to `python -c "from ...snapshot import generate_snapshot; generate_snapshot()"`; an ABSENT `<Repetition><Duration>` reads as "Deshabilitado / indefinite" in schtasks (StopAtDurationEnd=true is inert without a Duration) -> verified empirically rather than blind-adding RepetitionDuration (the anti-thrash gate forced the verify, which PROVED the edit unnecessary -- gate-as-feature). Idempotent-skip added to the generator so unchanged repos do not churn every cycle. SCS C33 addendum: a periodic auto-writer is MANDATORY -- without an active `pp-snapshot-writer` the restore system is INCOMPLETE (protection lags to the last manual -AutoRun). Process rule: before long nocturnal / Minecraft sessions, `snapshot_auto_writer.ps1 -Action status` must report `State: Ready`. Done-gate: State Ready + tasks.json in EVERY snapshot repo pre-crash (ALL REPOS COVERED: True) + autorun 10/10. Distinct from the daily `\ClaudePP-SessionSnapshot` (projects-zip disaster recovery, NOT pane restore).

- **UKDL-TRAP-T-RAM-GAMING-001 + PR-GAMING-001 (2026-06-06)** [HIGH] claude-power-pack: javaw.exe (Minecraft JVM) consumes 4-8 GB; with Claude Code in a long session a 32 GB host exhausts BEFORE the normal 20/28 GB ram_guard advisory fires. FIX (Gaming Mode in tools/ram_guard.py): `minecraft_active()` detects javaw -> `resolve_thresholds(True)` lowers DEFAULTS to 8/12 GB (explicit PP_RAM_WARN_GB/PP_RAM_CRIT_GB env still wins, gaming or not); at warn/crit the gaming path saves work_state FIRST (fail-open -- a failed save never blocks the advisory), refreshes session_snapshot.json (ensure_snapshot, M3), THEN emits `build_gaming_advisory` carrying task + commit + EXACT `claude --resume <sid>` (sid resolved from the cwd's latest transcript via snapshot.resolve_last_session when the Stop hook does not pass one). Non-gaming path byte-identical (done-gate 5: only an additive `gaming_mode:false` JSON key). ASCII `[GAMING MODE]` marker, NOT an emoji (cp1252 Windows-console print safety). The existing `ram-guard-stop.js` Stop hook surfaces `verdict.advisory` unchanged -> ZERO hook edit (emission path already wired). **PR-GAMING-001 (Process Rule):** before a long session with Minecraft active, verify `pp-snapshot-writer` Task Scheduler is running -- gaming_mode guards the RAM but the snapshot writer guarantees restore even if the crash is INSTANT, before any advisory. **SCS C34 addendum:** gaming mode (javaw active) -> thresholds 8/12 GB; work_state saved BEFORE the advisory; session_snapshot.json refreshed at each critical advisory. Gate: test_ram_optimization.py gaming surface 6/6 (thresholds / env-override / detect / fire-earlier / advisory + the original evaluate); empirical: real-cwd advisory carried `claude --resume 4b080ceb...` + live-registry work_state, M3 snapshot mtime advanced at the advisory. NOTE: the pre-existing A1 `V-RAM-PP-OVERHEAD` live gate (node+python 455 MB > 300 MB this long session) is orthogonal -- the diff provably does not touch bench_ram_footprint.

### UKDL TRAP T-HOOK-MIRROR-001 -- Edited the canonical, forgot the live mirror

**Level:** UKDL Trap
**Sealed:** 2026-06-04, hook-hub fold final sprint

**Trap:** `hook-dispatcher.js` exists TWICE: the git-tracked canonical
at `skills/claude-power-pack/hooks/hook-dispatcher.js` (what commits and
tests touch) AND the LIVE mirror at `~/.claude/hooks/hook-dispatcher.js`
(what settings.json actually invokes at runtime). They are SEPARATE files
(no symlink). Editing + committing the canonical changes NOTHING at runtime
until the canonical is COPIED to the live path. A whole session's dispatcher
fix can pass every unit test and parity check against the canonical while the
running hook is the stale version. `verify_global_mirrors.py` PAIRS enforces
LF-normalized SHA parity between the two; a [DRIFT] there means the runtime
is stale.

**Recognizer:** A hook script registered in settings.json by an absolute
`~/.claude/hooks/<x>.js` path, while the repo tracks `hooks/<x>.js`. The
runtime path is the loose one; the repo path is canonical. `migrate_hub_fold.py`
and `measure_hook_event.py` both operate on the LIVE side -- so AFTER
measurements only reflect changes that were mirrored.

**Fix:** every dispatcher (or any PAIRS-listed hook) change is a 4-step
cycle, not 1: edit canonical -> commit -> `Copy-Item canonical live -Force`
-> `verify_global_mirrors.py` shows [OK]. New gate `verify_hook_dispatcher.py`
V-HOOK-DISP-MIRROR asserts it.

**Cross-ref:** `feedback_mirror_sync_direction_and_hooks_dir_deny`,
`feedback_write_without_read_incomplete_system` (built but not live).

### UKDL TRAP T-HOOK-ORPHAN-CHAIN-001 -- A CHAIN_MAP key no --event names

**Level:** UKDL Trap
**Sealed:** 2026-06-04, hook-hub fold final sprint

**Trap:** A `CHAIN_MAP['Foo-chain']` array exists in the dispatcher source,
so the fold *looks* built -- but settings.json invokes
`--event=Foo-default` (which routes to `EVENT_MAP`, never the chain). The
chain is dead code: no `--event` arg names it. Empirically UPS and
PostToolUse both shipped this way -- the chains existed, were never wired,
and (UPS) were INCOMPLETE (missing `power-pack-reminder` +
`baseline-translator`, which lived in the `-default` EVENT_MAP bundle).
`migrate_hub_fold.py` correctly REFUSES to remove the standalone strays in
this state (removing them would drop hooks entirely): guard #2 reachability
prints "ORPHAN; removing strays would drop them. Wire the chain first."

**Recognizer:** before adding chains, assert the literal `--event=X` value
in settings.json equals the `CHAIN_MAP` key. `parse_chain_map` presence is
NOT reachability.

**Fix:** wire settings `--event=Foo-chain` AND make the chain a COMPLETE
superset of (old `-default` bundle + standalone strays). When the bundle has
fast in-process Node hooks, use the COMPANION path (a `-chain` event also
runs its `-default` EVENT_MAP bundle in-process) instead of converting them
to child cold-starts -- empirical: 2 in-process UPS hooks = 62ms vs ~250ms
per child spawn. Folding parallel top-level spawns into one sequential
dispatcher trades wall time for spawn count: worth it for Bash (MSYS2
fork-storm-prone), marginal for node/python events -- measure before folding.

### UKDL TRAP T-HOOK-ANTI-THRASH-001 -- Plan dispatcher edits at session start

**Level:** UKDL Trap
**Sealed:** 2026-06-04, hook-hub fold final sprint

**Trap:** `hook-dispatcher.js` is gated by an anti-thrash edit budget
(~2 edits/session, fungible: Write+Edit+Edit=3). Discovering a needed 3rd
dispatcher edit AT THE END of a session = silently blocked. The Edit tool's
non-adjacent-region constraint compounds this: N change-regions need N Edits
unless grouped into one contiguous block.

**Fix:** enumerate ALL dispatcher change-regions at PLAN time, group into
<=2 contiguous edits, and spend them on the highest-value changes first
(here: HSO routing fix #1, companion-bundle #2). If a 3rd is needed, defer
to the next session rather than thrash.

**Cross-ref:** SCS C38 (Hook-Dispatcher-by-default: ~1 settings entry per
folded event; new logic goes in dispatcher CHAIN_MAP/EVENT_MAP/companion,
not new settings entries; mergeOutputs always routes additionalContext to
hookSpecificOutput for UPS/PostToolUse/PostToolBatch, never stranded).

### SCS C38 ADDENDUM -- SessionStart + PreToolUse fold COMPLETED (2026-06-07)

**Sealed:** 2026-06-07, commit 8f2214c. The two events DEFERRED at the
2026-06-04 final sprint are now folded.

- **SessionStart 11 -> 8:** ran the existing tested `migrate_sessionstart_fold.py
  --apply` (backup-first) to remove the 3 strays already spawned detached by
  `session_start_hub.js` (mark-live-session, zero-command-bootstrap,
  first-time-project). stdout-consumed (token-shield, learning-sentinel,
  restart-target-consumer) + load-bearing recovery (lazarus-*,
  terminal-slot-recorder) stay standalone.
- **PreToolUse 11 -> 8:** folded windows-bash-bridge-guard -> Bash-chain and
  uqf_pre_edit_gate + claude_md_firewall -> Edit-chain (2 dispatcher edits =
  full anti-thrash budget). NEW `migrate_pretooluse_fold.py` adds the
  MATCHER-COMPAT guard (stray matcher must be SUBSET of chain matcher) so the
  broad-matcher Bash|PowerShell strays (session-file-guard, auto-test-gate) are
  correctly KEPT -- folding them into the Bash-only chain would drop PowerShell.
- **Enforcement:** verify_hook_dispatcher FOLDED_MAX_ENTRIES now gates
  SessionStart<=8 and PreToolUse<=8 (was advisory) -> a re-added stray fails the
  gate. NEW verify_pretooluse_security.py proves the folded chains still block
  (secret firewall + bash-bridge-guard) -- 3/3.

**Trap T-HOOK-FOLD-SELFTHRASH-001:** once a fold makes the Edit-chain LIVE,
your OWN iterative edits to a file go through it -- anti-thrash exit-2 blocks
the 3rd edit/Write in a window. Pivot (Rule 12) = PowerShell file-write
(Bash-matcher, bypasses Edit-chain), never a same-shape retry.

**Trap T-PS-DANGEROUS-LITERAL-001:** a dangerous literal (`rm -rf /`, even `\n`)
inside a PowerShell here-string -- as DATA being string-matched -- trips the
sandbox "Remove-Item on system path" guard. So does `Remove-Item` near any
quoted path. Fix: never put the literal in the command (concat / regex-anchor
around it); never pre-delete temp helpers (leave them in $env:TEMP).

**Finding:** the PreToolUse Bash-chain does NOT block `rm -rf /` -- cascade /
HR-CASCADE-002 is Hard-Rule/agent-layer, NOT a PreToolUse hook here. Test the
gate the change actually touches, not an assumed one.

### SCS C43 -- PP-Governance-Global-by-default (2026-06-08, BL-GOV-PROP-001)

PP governance systems (SDD-OS tiers, PRD/spec requirement, Setup-OS scan) fire
in ANY repo via `proactive_dispatcher`, not just security. No per-repo config.
**Silence = approval for Tier 0-1; Tier >= 2 without a spec = automatic
advisory.** Implementation:

- The cross-repo rail ALREADY existed (FASE -1 correction): `jit_skill_loader.py`
  (UserPromptSubmit hook, runs in any cwd) -> `_pp_proactive_inject` ->
  `dispatch_to_additional_context(ctx_in)` with the real `prompt`+`cwd`. The gap
  was only the missing signals; the wiring was done.
- `signals/sdd_tier.py` composes `spec_gate.classify_tier` + `check_spec_gate`:
  advisory only if Tier >= 2 AND no spec; silent for Tier 0-1. It TOOK the spec
  slot in the dispatch plan (tier-aware; supersedes the binary spec_compliance,
  whose UNIT tests stay -- only the dispatch line + the one dispatch-integration
  assertion swapped to pp-sdd-tier).
- `signals/setup_scan.py` composes `setup_os/registry.has_profile(cwd)`:
  un-profiled repo -> `/scan-repo` advisory (24h throttle); silent once scanned;
  returns None on empty cwd (no repo context -> no nag -- this also preserved the
  clean-context invariant in the proactive/spec suites).
- `setup_os/registry.py` central store at `vault/setup_os/profiles/<slug>_<hash>`
  in the PP repo (keyed by resolved path; external repos never polluted).
  `scanner.py --save` persists; bootstraps PP_ROOT onto sys.path so it runs from
  ANY cwd.
- Throttle: sdd_tier 5m, setup_scan 1440m (no-spam invariant; dispatcher caps 3).

Lesson (compose-not-rebuild): every primitive existed and was cwd-aware
(`classify_tier`, `check_spec_gate`, `scanner.scan`); the prompt's premise that
"the mechanism isn't wired cross-repo" was disproved in FASE -1 -- verify the
live rail before planning a rebuild. Gates: test_governance_propagation 7/7 x3
hermetic; proactive 16/16; spec_department 13/13; sdd_os 10/10; setup_os 8/8;
integration_wiring 9/9 (fixed a stale pre-existing assertion in the same pass).

### T-RESTORE-STALE-SID-001 -- current session restores as a fresh "History restored" pane instead of `--resume <sid>`

**Trap:** the CPC-OS restore baked the WRONG resume command for the CURRENT
session into `.vscode/tasks.json`, so on Cursor reopen the pane you were
actually in opened a brand-new session (banner "History restored") instead of
resuming the exact conversation. The other panes (older sessions) resumed fine
-- only the live one failed, which is the one that matters most.

**Real mechanism (empirically diagnosed 2026-06-09, NOT the hypothesised
"stale sid from a previous session"):** a transcript-creation RACE.
`session_start_hub.js` Hook 8 regenerates the snapshot the instant a pane opens
and `snapshot._resume_for` decided `exact` vs `missing` by
`_transcript_path(cwd, sid).is_file()`. But Claude Code creates the session's
own `~/.claude/projects/<enc-cwd>/<sid>.jsonl` **~1-2 minutes AFTER**
SessionStart (measured: snapshot written 14:53:44Z, transcript born 14:55:29Z).
So the current session's sid ALWAYS failed `is_file()` at capture time ->
`resume_kind=missing` -> `vscode_autorun` wrote a generic `kclaude.bat` (no
`--resume`) task -> fresh session on reopen.

**Avoidance / fix (BL-CPCOS-RESTORE-003):** trust the LIVE session's sid by
IDENTITY, not by file-existence-at-an-unlucky-moment. The hub passes its own
`PP_PANE_SID` as `live_sid` to `generate_snapshot(live_sid=...)`; `_resume_for`
treats `sid in live_sids` as `exact` even before the transcript flushes -- the
process is running, so the transcript provably WILL exist by restore time.
Non-live sids keep the `is_file()` guard, so genuinely-abandoned sids still
resolve `missing` (preserves BL-CPCOS-RESTORE-002 no-substitution +
BL-LAZ-STALE-001 transcript guard). The 15-min `snapshot_auto_writer` and the
next SessionStart self-heal any sid that never produces a transcript.

**Recognizer:** a resume manifest / autorun artifact decides "resume vs fresh"
by a file the SAME event is racing to create. If the artifact is generated at
SessionStart but the file it checks is written later by the host, the
just-started entity always loses the race. Resolve such artifacts by identity
of the live process, or regenerate them after the file is guaranteed present
(Stop hook / periodic writer) -- never bake a point-in-time existence check of
a not-yet-written file into a persisted restore command.

### T-RESTORE-EMPTY-SHELL-002 -- reviving panes shows CO-08 + "History restored" on some tabs (CO-08 is INNOCENT)

**Symptom (2026-07-03):** close a repo window with the X, reopen it -> some panes
resume the exact conversation (the native "Resuming the full session..." prompt)
but OTHERS open fresh with "History restored" + `PP CO-08: N hot session(s) on
this repo (soft cap 2) -- opening a new one anyway`. Read as "CO-08 vetoed my
resume and lost the session."

**Disproven premise -- CO-08 does NOT interfere with resume.** The resume-vs-new
distinction already exists at BOTH layers: `scheduler.decide()`
(`co_08_parallel_cap.py`) returns `proceed` for `is_new=False`, and `kclaude.ps1`
gates the CO-08 warning behind `$newSession`; an explicit `--resume` sets
`$explicitResume -> $newSession=false`, making the warning UNREACHABLE on any
resume. On a bare launch CO-08 is advisory-only -- it prints yellow text and
proceeds new, never blocks or force-resumes (T-KCLAUDE-LAUNCH-CONTEXT-001). The
CO-08 line is a downstream WITNESS of a bare launch, not its cause. (Cosmetic:
`kclaude.ps1` labels the GLOBAL hot_count "on this repo".)

**Real mechanism (empirically diagnosed from disk):** the fresh tabs were EMPTY
SHELLS. Of 9 same-repo panes, 4 had real transcripts (resolved `exact` ->
`kclaude --resume <sid>` -> resume fine) and 5 had session ids that NEVER
produced a `<sid>.jsonl` (verified absent on disk, 0 bytes -- opened but never
used, or the BL-CPCOS-RESTORE-003 race uncovered for the panes NOT carrying
`PP_PANE_SID`). Those resolved `missing` in `snapshot._resume_for` and
`vscode_autorun.build_cpc_tasks` PADded them (BL-CPCOS-RESTORE-004 count-parity)
into bare `kclaude.bat` folderOpen tasks (`args: []`) -> new session +
"History restored" + CO-08 on every reopen.

**Fix (BL-CPCOS-RESTORE-005, Owner decision "no recrear empty shells"):**
`build_cpc_tasks` emits a task ONLY for panes whose resume resolves to an
explicit `--resume <sid>` (empty shells never recreated), and NEVER pads to the
live tab count with bare tasks. `target_count` keeps only its TRUNCATE role
(more resolved sessions than tabs = tabs since closed). Supersedes the
RESTORE-004 padding. An unused shell is not worth resurrecting as an empty Claude
tab. Evidence: this repo's live `.vscode/tasks.json` regenerated 8 -> 4 tasks (4
exact, 0 bare); test_vscode_autorun 14/14, test_topology_reconcile 12/12,
cognitive_os_build 68/68 (CO-08 intact).

**Recognizer:** a scary advisory ("opening a new one anyway") on a restore path
is often a WITNESS, not the culprit. Before "fixing" the gate that prints it,
trace what actually issued the launch it is describing -- here the launch was
correct-by-design (bare = new) and the real defect was UPSTREAM (recreating
sessions that never existed).

**Gates:** `tools/test_cpc_snapshot.py` 17/17 (new `V-RESUME-LIVE-SID`, hermetic
x2); `tools/test_vscode_autorun.py` 10/10. Verified live: post-fix
`claude-power-pack/.vscode/tasks.json` carries `--resume f78deb41...` for the
current pane (was a no-arg "new" task pre-fix). SCS C33 lineage (writer ->
reader -> ACT): this closes the RESOLVE leg -- the reader read a field the
producer had not yet populated for the live session.

---

### T-TCO-TRACKING-GAP-001 -- the dedicated token logger measures injection, not real usage

**TRIGGER:** auditing token/TCO health; about to trust `tis.py` (or any
UserPromptSubmit-piggyback logger) as the record of real session spend.

**TRAP:** TIS writes `vault/token_logs/YYYY-MM-DD.jsonl` continuously and looks
like the cost ledger -- but its rows carry `model="claude-code-hook"`,
`call_label="jit-context-injected"`, and `cache_*_tokens` always 0. Those
`input_tokens`/`output_tokens` are the size of the JIT context being INJECTED,
not the model turn's real usage. The real per-turn `input/output/cache_read/
cache_creation` (billions of cache reads) live ONLY in Claude Code's own
transcripts `~/.claude/projects/<enc-cwd>/<sid>.jsonl` under `message.usage`.

**ACCIÓN:** for real token TCO, read the transcripts
(`tools/token_ground_truth.py::analyze` or `token_autopsy.py`). Treat a
hook-cadence logger as an injection-overhead signal, never as session spend.
`budget_monitor.py` is a THIRD thing (programmatic metered-credit bucket,
post-2026-06-15) -- it cannot "match" transcript burn because it tracks a
different bucket; `unconfigured`/`stale-pricing` are honest for a flat-rate Max
Owner with no programmatic workloads.

**ORIGEN:** FASE -1 TCO audit 2026-06-23 -- 532/545 transcripts carry usage;
TIS daily logs were injection sizes; budget.json absent + pricing 35d stale.
Closed by `tools/token_ground_truth.py` (the missing aggregated real tracker).

### T-CACHE-RATIO-HEALTHY-001 -- measure before optimizing cache

**TRIGGER:** about to "optimize the cache ratio" or split sessions for token
pressure on assumption, without measuring the real ratio first.

**TRAP:** the plan assumed cache might be < 30-50% (variable-prompt churn). Real
measurement: 96.4% today / 96.6% lifetime across 532 transcripts, and ZERO
sessions above 100k average fresh input/turn. The prompt cache absorbs ~96% of
all input-side tokens; average FRESH input/turn is 8-375 tokens even on 12k-turn
sessions. The `T-CACHE-RATIO-LOW-001` optimization does not apply when the ratio
is already healthy -- optimizing it is a no-op chasing a number that is fine.

**ACCIÓN:** compute the real ratio
(`cache_read / (cache_read + input + cache_creation)`) from transcripts FIRST;
only act if it is genuinely below ~50%. Whole-session size pressure is gated
separately by `context_monitor` (16/24 MB jsonl, 6000/12000 turns), not by the
cache ratio. ORIGEN: same 2026-06-23 audit.

---

### T-WRAPPER-W5-SOURCE-001 -- cost gate reads transcripts, never budget_monitor/TIS

**TRIGGER:** building/extending the kclaude W5 cost gate (or any "how much have
I spent today" feature) and about to read budget_monitor or TIS for the number.

**TRAP:** budget_monitor.py tracks the PROGRAMMATIC metered-credit bucket
(Agent SDK / `claude -p`, post-2026-06-15) and is inert for a flat-rate Max
Owner; TIS logs JIT-INJECTION size (cache fields always 0), not real turns.
Either as the W5 source shows a gate on data unrelated to the Owner's actual
session usage. The ONLY valid source is the transcripts via
`token_ground_truth.today_output_tokens` / `analyze` (SCS C53,
T-TCO-TRACKING-GAP-001).

**ACCIÓN:** W5 burn = `token_ground_truth.today_output_tokens(now=)` (mtime-
filtered fast path; over-estimates by including earlier turns of multi-day
files -- documented, never under-counts). Best-effort within its 0.5s timeout;
if it cannot compute in time -> SILENT (no fake 0). ORIGEN: wrapper W5
2026-06-23 (SCS C48).

### T-WRAPPER-TIMEOUT-001 -- per-feature timeouts must run CONCURRENTLY

**TRIGGER:** composing N pre-launch features each with its own timeout under a
total overhead budget.

**TRAP:** running them sequentially makes the worst-case overhead the SUM of the
timeouts. kclaude's W1+W4+W5+W2 timeouts (1.0+0.5+0.5+1.0) sum to 3.0s -- over
the <2s launch budget -- if run one-after-another. The spec's per-feature
timeouts and the total budget are only mutually satisfiable if the features run
concurrently.

**ACCIÓN:** submit all features to a thread pool, collect each with its own
`result(timeout=...)`; wall-time becomes the LONGEST single timeout (~1s), not
the sum. `prelaunch.py` does this; `ex.shutdown(wait=False)` + `os._exit(0)` so
a hung feature thread never blocks process teardown. Measured overhead ~1.6s.
ORIGEN: wrapper W6 2026-06-23.

### T-WRAPPER-RESTART-ABSORB-001 -- a launcher wrapper must preserve the loop it replaces

**TRIGGER:** replacing an existing `kclaude`/launcher that the Owner already
uses, with a richer wrapper.

**TRAP:** the old kclaude.bat was a /restart LOOP (relaunch `claude --resume
<sid>` when a flag drops). A naive new wrapper that launches claude once and
exits silently breaks /restart's in-terminal relaunch -- a regression the
done-gate would not catch because the wrapper "works" on first launch.

**ACCIÓN:** read the artifact you are superseding (SCS C28); absorb its loop.
kclaude.ps1 runs pre-launch intelligence ONCE, then enters the same flag-driven
relaunch loop; the old .bat is backed up `.superseded`, never deleted. ORIGEN:
wrapper W7 2026-06-23.

### HR-SESSION-RESILIENCE-001 -- no recovery is complete without a G4 verdict

**TRIGGER:** declaring a session/crash recovery "complete", "restored" or "done".

**ACCIÓN:** STOP. A recovery is complete ONLY when the G4 Recovery Acceptance
Framework returns `RECOVERED` (`modules/session_resilience/acceptance.acceptance_gate`).
`PARTIAL`/`FAILED` hold the claim and enumerate the missing dimensions; the
acceptance gate fails safe (holds) on `UNKNOWN`. G4 is the arbiter -- without its
verdict nothing is done. ORIGEN: Session Resilience OS build, SCS C56, 2026-06-27.

### T-KCLAUDE-STARTUP-BLANK-001 -- a slow advisory scan must never sit on the launch path

**TRIGGER:** a launcher runs pre-launch modules synchronously before spawning
the child, and one module scans a large corpus.

**TRAP:** kclaude's W5 cost_gate scans the whole ~/.claude/projects transcript
corpus (24h + 7d windows via `token_ground_truth.window_output`) = 17-27s. On
the blocking path the terminal is blank for that whole time; the 1s per-feature
timeout both silently DROPS the advisory AND, under GIL / cold cache, fails to
clip -> the 15s blank the Owner saw. The launch-critical work (resume decision +
CO-08 gate) is ~30ms; the slow scan is a pure advisory that never changes the
launch args.

**ACCIÓN:** split prelaunch into `--mode fast` (launch-critical only: W2 resume
+ W4 coordinate + CO-08 gate + CO-00 advisory) and `--mode advisories` (W1 turn
+ W5 cost + parallel_burn), the latter run DETACHED, writing
`~/.claude/cache/kclaude_advisories.json` that the NEXT launch prints instantly.
claude launches on the fast bundle; advisories are one-launch-stale, never
blocking. Measured time-to-launch 333ms (<3s) vs 15s. ORIGEN: kclaude startup
fix 2026-07-01.

### T-W4-DIALOG-SINGLE-SESSION-001 -- no confirmation prompt for the single-session base case

**TRIGGER:** a coordinator offers to resume an existing session before launch.

**TRAP:** kclaude's W4 fired a blocking `Read-Host` whenever ANY active session
existed -- including the common single-session case -- so every launch stalled
on "Resumir? [S/n]" before claude started. `coordinate()` already distinguishes
`source=active` (one) vs `multiple`; the orchestrator ignored the distinction.

**ACCIÓN:** a SINGLE active session (source=active) -> SILENT auto-resume, zero
dialog. Only `source=multiple` shows a numbered list, and even then a 3s timed
read defaults to the most recent. Zero active -> new session, silent. A
`-n/--new` escape hatch preserves "start fresh on an active repo"; an explicit
`--resume/--continue` is honored verbatim. ORIGEN: kclaude startup fix
2026-07-01.

### HR-RESTART-VIA-KCLAUDE-001 -- /restart always relaunches via kclaude, never bare claude

**TRIGGER:** /restart resolves how to relaunch the session after the graceful
/exit.

**ACCIÓN:** relaunch through the kclaude wrapper so the Cognitive OS (CO-00 /
CO-08) is active after every restart. `kclaude.ps1`'s restart loop re-runs the
fast CO gates before relaunch; `restart-claude.ps1`'s clipboard fallback targets
the live `bin/kclaude.ps1` (then the repo copy, then bare claude -- fail-open,
never breaks /restart). SPLIT-BRAIN NOTE: the Cursor kClaude profile runs
`~/.claude/bin/kclaude.ps1`, a MIRROR of `tools/kclaude.ps1` -- edits to the repo
copy are INERT until copied to bin. ORIGEN: kclaude restart fix 2026-07-01.

**SCS C48 addendum v2 (2026-07-01):** kclaude startup < 3s (fast/advisories
split; time-to-launch 333ms measured). Single active session auto-resumes
silently. /restart always via kclaude (CO active post-restart, fail-open to bare
claude). **SCS C63 addendum:** the W6 launcher's LIVE copy is `bin/kclaude.ps1`
(byte mirror of `tools/kclaude.ps1`); prelaunch.py is read live from the skills
path (no mirror). Keep the launcher mirror in sync on every kclaude.ps1 edit.

**SCS C79 addendum (2026-07-06):** the rule now covers the RESUME surface, not
just /restart. Every resume command the pane_map ecosystem generates uses
`kclaude --resume`, never bare `claude --resume`. Source of truth =
`tools/build_pane_map.ps1` (the `resumeCmd` field written into `pane_map.json`);
the PP Sessions extension (Resume button, copy-to-clipboard, cold-start
auto-launch) reads that field, and its fallbacks (`extension/src/restore_guard.js`,
`extension/src/extension.js`) also synthesize `kclaude`. A resume via bare
`claude` bypasses the whole wrapper -- CO-00 (60% ceiling), CO-08 (parallel cap),
W1-W5 -- leaving the Cognitive OS INERT in that session until the Owner closes and
reopens with kclaude. ORIGEN: pane_map/PP-Sessions resume audit 2026-07-06.
TIER-2 PENDING (documented, not done this seal): the cpc_os snapshot recovery
chain (`modules/cpc_os/snapshot.py:166` and its consumers `recovery.py`,
`auto_reset_orchestrator.py`, `vscode_autorun.py`, `ram_guard.py`),
`modules/session-continuity/restore.ps1`, `session_resilience/resume_identity.py`,
and `tools/lazarus_revive_all.py` still emit bare `claude --resume`; a scoped
follow-up sweep (a distinct subsystem with its own tests) is recommended.

### T-CURSOR-PROFILE-ORDER-001 -- Cursor sorts terminal profiles alphabetically, not by array order

**TRIGGER:** adding a Cursor terminal profile that must appear at a specific
position in the "+" menu.

**TRAP:** the menu does NOT honor `terminal.integrated.profiles.windows` array
order. Cursor's `_sortProfileQuickPickItems` pins the DEFAULT profile first, then
sorts every other profile by `localeCompare(name)`. So a profile keyed "kClaude"
lands AFTER "Claude" (k > C). Array position is irrelevant.

**ACCIÓN:** key the profile " kClaude" (single LEADING SPACE):
`" kClaude".localeCompare("Claude") === -1`, so it collates immediately after the
pinned default ("Last session") and before "Claude" -> menu = Last session /
kClaude / Claude. The space renders as a ~1px indent (label reads "kClaude").
Terminal-profile edits need a Cursor WINDOW RELOAD to appear -- a profile present
in settings.json but absent from the running "+" menu is almost always an
un-reloaded window, not a missing profile. ORIGEN: kClaude Cursor profile
2026-07-01 (BUG 4 premise disproved: the profile was already present + correctly
sorted; the gap was an un-reloaded window).

### T-LAST-SESSION-SMART-WRAPPER-001 -- route "Last session" through the smart W6 wrapper for CO

**TRIGGER:** wiring a Cursor "Last session" / autoresume profile so the Cognitive
OS (CO-00/CO-08) is active in the revived terminal.

**TRAP:** the "Last session" profile runs `lazarus-shell-autoresume.bat`, which
resolves the session then launched the OLD `kclaude.bat` (bare `claude` in a
restart loop, NO pre-launch intelligence) -- so CO was inactive from "Last
session" even though the kClaude profile has it.

**ACCIÓN:** in lazarus-shell-autoresume.bat, the resume launch AND the doskey
fallback prefer `bin\kclaude.cmd` (-> bin\kclaude.ps1, the smart W6 wrapper),
falling back to kclaude.bat then bare claude. Preserves lazarus crash-recovery /
termkey resolution while adding CO; the smart wrapper honors the explicit
`--resume <sid>` (skips its own auto-resume). ORIGEN: kClaude Cursor profile
2026-07-01 (BUG 5). lazarus is a GLOBAL ~/.claude/hooks file (not in the repo);
the "Last session (PS)" .ps1 variant is a separate follow-up.

**SCS C49 addendum v2 (2026-07-01):** kClaude is the preferred Cursor terminal
profile (menu: Last session / kClaude / Claude; icon `sparkle` + color
`ansiMagenta` identical to Claude); it launches the smart bin/kclaude.ps1 (CO
active). "Last session" now also routes through the smart wrapper via
lazarus-shell-autoresume.bat. Profile changes require a Cursor window reload.

### T-KCLAUDE-LAUNCH-CONTEXT-001 -- a terminal-profile launch opens a NEW session, never auto-resume

**TRIGGER:** a launcher wrapper is used in BOTH a terminal-profile context (a new
pane from the "+" menu) and a resume context (/restart, explicit --resume).

**TRAP:** auto-resume tuned for /restart (fec5c3a F2: single active session ->
silent resume) is WRONG for the terminal button. Clicking kClaude landed the
Owner in the PRIOR session instead of a fresh one (BUG A); and because resuming
loads the whole transcript, it also blew the <3s startup budget (BUG B -- SAME
root cause). Worse, the CO-08 rung-3 block (previously bypassed because F2
resumed first) would, once F2 is removed, PROMPT "resume instead?" -- re-
introducing the same landing-in-a-session.

**ACCIÓN:** distinguish contexts by the explicit --resume/--continue ARG, not by
whether a resumable session exists. A bare launch (no explicit resume) -> ALWAYS
a NEW session (parity with the native Claude button). Auto-resume ONLY on an
explicit --resume (Owner, the "Last session" lazarus route, the /restart
clipboard) or the restart loop. CO-08 becomes ADVISORY on a bare launch (warns,
proceeds new; never blocks / force-resumes) -- "gates active, but never
auto-resume". A new session loads no transcript, so startup returns to
wrapper-overhead only (~333ms). Runtime proof: tools/test_kclaude_launch.ps1
stubs `claude` and asserts bare->new, explicit->resume. ORIGEN: kClaude
new-session fix 2026-07-01 (BUG A + BUG B).

**SCS C48 addendum v3 (2026-07-01):** kclaude bare launch -> NEW session; kclaude
--resume <sid> -> explicit resume; /restart -> auto-resume (loop). CO-08 advisory
on a bare launch (no block). bin/kclaude.ps1 re-mirrored from tools/kclaude.ps1.
Startup < 3s (new session = no transcript load, the BUG B root cause).

### PR-SNAPSHOT-BEFORE-RISK-001 -- snapshot + validate before a risky operation

**TRIGGER:** about to hit an OOM threshold, run an update, or force-kill a process.

**ACCIÓN:** call `integration.on_ram_threshold` (or `on_session_start`) FIRST: G3
records a snapshot, G4 validates it reconstructs+scores clean, G5 logs it. Both
entry points are FAIL-OPEN -- if any step fails the operation still proceeds; the
guard never blocks real work. ORIGEN: Session Resilience OS build, SCS C56.

### T-UI-STATE-API-LIMITS-001 -- do not force a UI API that does not exist

**TRIGGER:** capturing/restoring editor scroll, focus or tab order.

**TRAP:** scroll/focus/tab-order live in the editor host; Python cannot touch
them and scroll restore is host-APPROXIMATE (`revealRange`). Forcing a
non-existent API is the trap.

**ACCIÓN:** capture/apply is extension-JS (`G1_EXTENSION_CAPTURE_SPEC.md`). G4 is
capability-aware (`ui_state.g4_host_capabilities`): a property the host cannot
restore is excluded from equivalence and logged by G5 -- never silently failed,
never silently dropped. ORIGEN: Session Resilience OS build, SCS C56.

### T-DEPENDENCY-GRAPH-INVERSION-001 -- read the code before trusting a prompt's graph

**TRIGGER:** a plan/prompt asserts a dependency graph between systems.

**TRAP:** the build prompt's graph (`G4 independent, G3->G4, G1->G2/G3`) was
INVERTED. The datasets+source show data flows `G1 -> {G2, G3} -> G4 -> G5`
(G2/G3 consume G1; G4 consumes G3; G5 consumes G4).

**ACCIÓN:** verify dependencies against the datasets and real source before
implementing; correct the literal, honor the intent. ORIGEN: Session Resilience
OS build, SCS C56, 2026-06-27.

### PROCESS RULE PR-MODE-SELECTION-001 -- EXECUTION by default, ULTRA-PLAN only for genuine architecture

**Level:** Process Rule (mandatory protocol, cross-project, recoverable -- NOT a
data/deploy-class Hard Rule).

**TRIGGER:** before choosing the MODE of a structured prompt (EXECUTION MODE
vs ULTRA-PLAN MODE).

**RULE:**
- **EXECUTION MODE** when: the work has a clear path, extends existing systems,
  needs no new architectural decision. This is the DEFAULT.
- **ULTRA-PLAN MODE** only when: there is a genuine architectural decision with
  multiple valid options, or a brand-new system is being designed from scratch.
- NEVER use ULTRA-PLAN as the default for incremental features. Its FASE -1
  (extensive read) + Q&A + multi-sprint pass costs ~3-5x the output of an
  equivalent EXECUTION MODE prompt.

**EVIDENCE:** Weekly-Burn-RCA 2026-06-30 -- 49.2M output tokens in 48h, 1.81x
the June daily average (13.5M/day), driven by large structured prompts
(EXECUTION/ULTRA-PLAN, ~80k-230k output each) fired in consecutive tandas ~40min
apart. Measured cost: one EXECUTION MODE cycle ~= 194k output tokens.

**ORIGEN:** vault/plans/weekly-limit-burn-rca-2026-06-30.md. Enforced advisory:
modules/wrapper/cost_gate.py weekly_burn() (fires at >=1.5x the June rate).

### UKDL TRAP T-PARALLEL-PANES-BURN-001 -- same-repo parallel panes multiply burn without progress

**Level:** UKDL Trap (cost / workflow edge case).

**TRIGGER:** opening a 2nd (or Nth) pane on the SAME repo and firing large
structured prompts in parallel.

**TRAP:** 2+ panes of the same repo each launching EXECUTION/ULTRA-PLAN prompts
in a short window multiplies OUTPUT without multiplying real progress -- each
pane rebuilds similar context and regenerates overlapping work. In the 48h
forensic, TUA-X 74c7668b + 8cce8060 + InfinityOps f1acb1ec ran in parallel
06-28 15:00-21:00, pushing hourly output to 2.5-2.9M/h (above single-session
ceilings). The W4 coordinator warned of a 2nd pane but only to offer RESUME; it
never flagged the burn risk.

**ACCIÓN:** prefer one pane per feature, sequential, with /kclear between large
features. The detector modules/wrapper/repo_coordinator.py parallel_burn()
(wired into prelaunch _w4) now surfaces this pattern as a fail-open advisory.

**ORIGEN:** Weekly-Burn-RCA 2026-06-30, SCS C59.

### UKDL TRAP T-KICKBACKS-BOOT-CANCELED-001 -- boot-canary false positive skips the patch and hides the earnings bar

**Level:** UKDL Trap (third-party extension race; PP-mitigable, not PP-fixable).

**TRIGGER:** Cursor shows *"Kickbacks: prior activation didn't complete cleanly --
skipping automatic patch this run. Click the status bar to manually re-enable…"*,
or the green `Kickbacks $X today` earnings status-bar item disappears intermittently.

**TRAP:** Kickbacks (`dist/extension.js` bootCanary) writes `~/.vibe-ads/boot.canary`
at activation start and self-deletes it 5s later via an `.unref()`'d `setTimeout`
(`SETTLE_MS=5000`). A Cursor reload / activation-cancel within those 5s (logged
`activate.fatal {"msg":"Canceled","stack":"Canceled: Canceled"}`) drops the unref'd
timer, so the canary survives. The next activation within 90s (`CANARY_STALE_MS`)
reads the stale canary as a crash -> `suspendServing()` -> `servingVerdict()="freeze"`
-> `canPatch()=false` (PATCH SKIPPED + warning toast) AND the earnings `StatusBarItem`
blanks. Both reported symptoms (patch-activation-failed + status-bar-hidden) are the
SAME false positive. Trigger = rapid Cursor reloads / ungraceful shutdown / a
Kickbacks self-update (it auto-updated 2026-06-27, build 06-13 -> 06-27).

**ACCIÓN / mitigation (PP side only -- Kickbacks code NEVER touched):** INV-CANARY in
`tools/kickbacks_guard.ps1` (scheduled task `PP-KickbacksGuard`, every 2 min) reaps a
`boot.canary` older than 15s (past the 5s settle, so never a live activation) so the
next reload patches clean. Recovery when it already fired: click the status bar
(`kickbacks.debugMenu`) or Command Palette -> `Kickbacks: Restore Claude Code`
(`kickbacks.restore`); last resort delete the stale canary + Reload Window. Full
runbook: `~/.claude/state/kickbacks_recovery.md`.

**Honest limit:** the PP cannot pre-empt the FIRST hit in the seconds right after a
rapid reload (race lives inside Kickbacks' 5s window) nor force its own status-bar item
to show -- only the suspend trigger is removable. Guard shortens recurrence to <=2 min.

**ORIGEN:** Kickbacks dual-bug EXECUTION 2026-06-30, SCS C60. Cross-ref
`PR-STATUSLINE-GUARD-ALWAYS-001`.

### PROCESS RULE PR-STATUSLINE-GUARD-ALWAYS-001 -- the statusline/Kickbacks guard runs always, not reactively

**Level:** Process Rule (cross-session, recoverable).

**TRIGGER:** relying on a Kickbacks/statusline self-heal to keep the ad + context bar +
patch alive.

**RULE:** the guard MUST run continuously and idempotently, NOT only when a problem is
detected. Kickbacks can auto-update or re-capture the chain / leave a stale canary at
ANY time and break the chain or skip the patch with no warning. A SessionStart-only
hook heals only at the next session start; the correct mechanism is the 2-min scheduled
task (`PP-KickbacksGuard`, at logon + every 2 min) -- it strictly dominates SessionStart
and caps any broken-state window at ~2 min regardless of what Claude is doing. Each
invariant (INV-CHAIN/SETTINGS/AUTH/CANARY) is fail-open: any error -> exit 0, never
breaks a working setup.

**ORIGEN:** Kickbacks dual-bug EXECUTION 2026-06-30, SCS C60.

### UKDL TRAP T-KICKBACKS-GUARD-GLOBAL-001 -- the guard is system-global by design, not per-repo

**Level:** UKDL Trap (scope clarification; no code change).

**TRIGGER:** wondering whether the Kickbacks/statusline guard only protects the
window where the PP repo is open, or all Cursor windows.

**FACT:** it protects ALL Cursor windows simultaneously, by design, because (1)
Kickbacks keeps a SINGLE per-user `~/.vibe-ads/` for every window (`boot.canary`,
`cli-ad.json`, `cli-prev-statusline.json` are per-user, not per-workspace), so
INV-CANARY/CHAIN/SETTINGS/AUTH operating on those paths heal every window at once;
and (2) `PP-KickbacksGuard` is a USER-level scheduled task (at-logon + 2-min) running
`powershell -File "…\tools\kickbacks_guard.ps1"` as the user -- NOT bound to any Cursor
process/workspace; it fires whatever (or nothing) is open. Verified
`schtasks /query /tn PP-KickbacksGuard /v` -> Estado=Listo, trigger=logon+interval.

**Honest coupling:** the script FILE lives in the PP repo dir, so the task needs that
path on disk -- but NOT the repo open in Cursor. Moving/deleting the repo -> task
no-ops (fail-open), never misfires.

**ORIGEN:** Kickbacks global-scope + context-% compat EXECUTION 2026-06-30, SCS C60 addendum.

### UKDL TRAP T-STATUSLINE-CHAIN-ISOLATED-001 -- context-% HUD failure cannot hide the Kickbacks ad (hypothesis disproven)

**Level:** UKDL Trap (verified property; no fix needed).

**TRIGGER:** suspecting the context-% statusline and the Kickbacks ad conflict, so a
context-% change/absence hides the whole line including the ad.

**FINDING (disproven with code + empirical evidence):** the line is ONE invocation
(`settings.json statusLine` = `node vibe-ads-statusline.mjs`) that prints the ad FIRST
via synchronous `writeSync(1,…)`, THEN spawns the PP HUD (`gsd-statusline.js`) as an
isolated child (5s hard timeout, never-throws) and stacks its output below. The HUD
guards `context_window.remaining_percentage` with optional chaining + `if (remaining
!= null)` -> missing/null context simply OMITS the % segment (model+dir still print),
never crashes. Even a HUD that throws can only drop the HUD line; the ad is already on
the pipe. Empirical (real chain, 4 payloads): ad present in ALL 4 -- normal (ad+46%),
no `context_window` (ad, no %), `context_window:null` (ad, no %), garbage stdin that
makes the HUD `JSON.parse` THROW (ad, no %).

**ACCIÓN:** none -- both layers are independently fail-open; no defect to fix
(constraint: don't invent a fix when the hypothesis isn't confirmed). The green
`$X today` earnings bar is a separate Cursor `StatusBarItem`, not in this terminal
chain; its hiding is the boot-canary `suspendServing()` path already fixed in `b9148de`
(T-KICKBACKS-BOOT-CANCELED-001).

**ORIGEN:** Kickbacks context-% compat EXECUTION 2026-06-30, SCS C60 addendum.

### PR-RESEARCH-OFFLOAD-VPS-001 -- Offload screen-interrupting research/scraping to the VPS

**TRIGGER:** A scheduled task or Stop/SessionStart hook that runs research/scraping
and interrupts the Owner's local session (a window flash OR a hook systemMessage).

**ACCIÓN:** Evaluate it for offload to the VPS. Criterion: it needs NO local
Cursor/session state and can run autonomously. If so -> run it on the VPS (cron +
isolated venv), silence the local interruption, and PULL results into SessionStart
(detached, TTL-gated, additionalContext -- never a blocking message). The local
machine is for the Owner's interactive work, not background polling.

**ORIGEN:** AutoResearch was an orphan -- a Stop hook printed "[KobiiClaw AutoResearch
v2] trigger saved" on every session exit while the engine (nightcrawler.py) was never
actually scheduled. Migrated to KobiiClaw VPS 2026-06-30 (SCS C64).

### T-DEDICATED-ACCOUNTS-001 -- Social automation uses dedicated accounts, never the Owner's

**TRIGGER:** Wiring Twitter/Reddit/Instagram/etc. into an automation (cookies/creds).

**ACCIÓN:** Use a SECONDARY dedicated account, never the Owner's personal account
(ban risk from non-human-detected behavior). Store cookies VPS-only at perms 600,
never in the repo. The agent cannot create these accounts -- the Owner provides them.

**ORIGEN:** Agent-Reach expansion 2026-06-30; deferred Twitter/Reddit to credential-free
channels (Jina web reader + yt-dlp) until dedicated-account cookies are provided.

### T-AGENT-REACH-AGENT-FACING-001 -- Agent-Reach CLI is agent-facing, not a fetch API

**TRIGGER:** Planning to "use the Agent-Reach CLIs" from a headless script/cron.

**ACCIÓN:** Don't. Agent-Reach's CLI is `setup/doctor/configure/transcribe/format/
skill` -- it installs+blesses tools and registers an agent skill; there is NO
`agent-reach fetch <url>` / per-channel command. For a headless pipeline call the
underlying credential-free PRIMITIVES it sets up: Jina Reader (`GET https://r.jina.ai/<url>`)
and `yt-dlp`. Verify the real surface (`--help`) before coding against an assumed one.

**ORIGEN:** Block C 2026-06-30 -- the plan assumed "AutoResearch usa los CLIs de
Agent-Reach"; `pip install agent-reach` 404s on PyPI (install is the GitHub zip), and
the CLI exposes no fetch command. Integration is via Jina + yt-dlp. SCS C64.

## Cursor Terminal Profile -- kClaude -- 2026-07-01

| Ref | File | Why it matters |
|---|---|---|

## Kickbacks session-churn + vsix-blocked -- 2026-07-03

### UKDL TRAP T-KICKBACKS-SESSION-CHURN-001 -- reloads/restart inside the 5s settle window burn bar-minutes with no impressions

**TRIGGER:** Kickbacks earnings look low while the ad + earnings bar are otherwise healthy.

**ACCION:** Frequent Cursor reloads and /restart that land inside Kickbacks' 5s
activation-settle window cancel the activation (logged `activate.fatal Canceled`). Each
cancel = statusline minutes without a counted impression. Impressions accrue ONLY while
an active Claude Code statusline renders the ad. To maximize Kickbacks revenue keep LONG,
STABLE sessions; avoid unnecessary reloads during active work.

**ORIGEN:** Impression-gap forensic 2026-07-03 (`vault/audits/kickbacks_impression_gap_2026-07-03.md`).
Canary-freeze hypothesis DISCARDED: at the 12:08-local (10:08Z) cutoff the CLI was idle
(no activate/injection); the ad pipeline reached `hasAd:true`+`authHealthy:ok` after it;
`boot.canary` absent; guard clean. Cause external to PP. Cross-ref SCS C60.

### UKDL TRAP T-KICKBACKS-VSIX-BLOCKED-001 -- stuck selfupdate can strand Kickbacks on an old version

**TRIGGER:** `selfupdate.failed {reason:"vsix-url-blocked"}` recurring in `~/.vibe-ads/debug.log`.

**ACCION:** Not an immediate earning bug, but a chronic block strands the extension on an
old build (accumulating incompatibilities). `tools/kickbacks_guard.ps1` INV-VSIX now
advises (WARN, throttled 1x/day, fail-open) when the most-recent `consecutiveFails` > 10.
Advisory only -- never blocks. Owner action: reinstall the extension manually from kickbacks.ai.

**ORIGEN:** Same forensic. Observed stuck on 0.3.177 (target 0.3.178) since >=30-jun,
`consecutiveFails` climbing. Monitor added 2026-07-03. Cross-ref SCS C60 addendum (2026-07-03).

### UKDL TRAP T-KICKBACKS-RECURRING-GAP-ACTIVITY-001 -- same-day "recurring gaps" are work-rhythm breaks, not a periodic system fault

**TRIGGER:** Kickbacks ledger shows two+ gaps the same day at a suspiciously regular interval
(e.g. ~5h apart); tempting to hunt a periodic timer / 5h TTL / cron.

**ACCION:** Test the periodic hypothesis against REAL logs before believing it. Checklist that
DISCARDED it 2026-07-03: (1) no auth failure at gap-start -- the first gap (10:08Z) had ZERO;
auth throws are `transient:true` and recover immediately. (2) No scheduled task at ~5h cadence
touches Kickbacks (only `PP-KickbacksGuard` @2min; the 3-6h tasks are benign Windows built-ins:
CEIP, OneSettings, Storage Tiers, WER). (3) Tokens rotate hourly, not 5h. (4) selfupdate/vsix
fails all day, unaligned to gaps. (5) `killed:true` only appears transiently (23:00Z / now),
never at a gap. Gaps = tail of a work burst -> break; impressions RESUME when work resumes
(142 -> 154 across the "gap"). Churn does NOT multiply impressions (server-side per-interval
dedup) -> rapid reload/restart can SUPPRESS earnings. n=2 at 5h30m = human rhythm, not a period.

**ORIGEN:** PM forensic 2026-07-03 (`vault/audits/kickbacks_recurring_gap_2026-07-03.md`).
Reinforces `T-KICKBACKS-SESSION-CHURN-001`. Cross-ref SCS C60 addendum v3.
| T-CURSOR-PROFILE-ORDER-001 | `vault/plans/kclaude-terminal-profile-2026-07-01.md` | kClaude terminal profile added to Cursor `+` menu. Premise-corrected: the `Claude` profile launches the OLD `~/.claude/kclaude.bat` (simple restart wrapper), NOT claude.exe; `kClaude` launches the SMART `~/.claude/bin/kclaude.ps1` (W6 pre-launch intelligence: W1 context / W4 coordinator / W5 cost / W2 auto-resume / W3 naming) via `bin/kclaude.cmd`. Icon/color cloned byte-identical from `Claude` (sparkle / terminal.ansiMagenta). Ordering (proven from Cursor source, NOT insertion order): `_sortProfileQuickPickItems` pins the default then `localeCompare`-sorts the rest alphabetically. So the profile key is `" kClaude"` (leading ASCII space) because `" kClaude".localeCompare("Claude")<0` -> collates first among non-defaults -> menu = Last session (Default) / kClaude / Claude. "Last session" stays `defaultProfile.windows` (unchanged). Insertion order is irrelevant; verified by replaying Cursor's own sort on the live file. Backup: `settings.json.bak.20260701T130248Z`. Arg passthrough + launch chain empirically proven. |

## Conversation Quality Audit -- behavioral inefficiency patterns -- 2026-07-03

Source: `tools/conversation_quality_audit.py` over 646 sessions. Costs are real
`message.usage.output_tokens` of the offending turns. Report:
`vault/plans/conversation-quality-report-2026-07-03.md`. Cross-ref SCS C69.

### UKDL TRAP T-AGENT-SELF-CORRECTION-001 -- agent corrects itself in consecutive turns

**TRIGGER:** Two consecutive assistant turns (no Owner between) where the second
opens with a correction cue (`I made an error`, `corrijo`, `where I was wrong`).

**ACCION:** The first turn shipped an unverified claim; the redo is pure waste.
Gate DONE/assert turns behind observed evidence (superpowers:verification-before-completion).
Measured cost: **370,081 tokens across 71 occurrences** (the corpus's single
largest behavioral cost).

**ORIGEN:** Conversation Quality Audit 2026-07-03. Highest-frequency pattern.

### UKDL TRAP T-OWNER-REPEAT-INSTRUCTION-001 -- Owner re-sends an unresolved instruction/blocker

**TRIGGER:** Two similar Owner messages (>0.7 keyword overlap) with the agent's
between-turn(s) containing NO tool_use (prose-only acknowledgement, no action).

**ACCION:** On any imperative, the NEXT turn must contain the executing tool_use
or an explicit blocker -- never prose-only "sure, I will". Measured cost:
**74,530 tokens across 19 occurrences** (concentrated in error-retry sessions
where the Owner re-pastes the same unresolved blocker). Harness `<local-command>`
wrappers are excluded (not Owner instructions).

**ORIGEN:** Conversation Quality Audit 2026-07-03.

### UKDL TRAP T-PLAN-EXECUTION-DIVERGENCE-001 -- executed files diverge from the approved plan (LOW confidence)

**TRIGGER:** Agent posts a plan listing >=2 file paths, Owner gives a short
approval, next execution turn writes files overlapping the plan <40%.

**ACCION:** Bind execution to the approved plan's file list (HR-ONESHOT-002
fidelity lock); on >40% divergence, pause and re-confirm. Measured cost:
**249,170 tokens across 44 occurrences** -- but this is an **UPPER BOUND**:
"planned" = every path in the plan block, INCLUDING read-context files, so each
hit needs manual review, not auto-fix. LOW-confidence detector by design.

**ORIGEN:** Conversation Quality Audit 2026-07-03.

### UKDL TRAP T-REPEATED-QUESTION-001 -- agent re-asks a question already answered in-session

**TRIGGER:** An assistant interrogative clause (cue-bearing, ends in `?`) whose
keyword set overlaps >0.7 with an EARLIER assistant question that the Owner
already answered.

**ACCION:** Consult the Findings Bus (PM-03) -- `RedundancyTax.reason_or_reuse`
-- before asking; a question resolved earlier in the same session must not
recur. Measured cost: **90,349 tokens across 33 occurrences**. Turns that merely
contain a `?` without an interrogative cue are excluded (FP-hardened).

**ORIGEN:** Conversation Quality Audit 2026-07-03.

### UKDL NOTE T-DUPLICATE-REALITY-SCAN-001 -- NOT FOUND (freq 0)

Cross-session duplicate Reality Scans (same repo, <7 days, >0.6 overlap) were
**not found with significant frequency (0 occurrences)** -- no fix proposed.
Interpretation: scans differ enough per task, and/or PM-01 Repo Brain already
suppresses redundant scanning. Re-check if the corpus behavior shifts.


## Cognitive Cost Leak Taxonomy -- non-token leak families -- 2026-07-03

Source: `vault/plans/cognitive-leak-taxonomy-2026-07-03.md` (SCS C70). The token
audits (C68 volume / C69 behavior) are blind to the OS + coordination axes; these
are the leaks they cannot see, with real data measured this sprint.

### UKDL TRAP T-SCHEDULED-TASK-LEAK-001 -- PP scheduled tasks that fail/idle-fire

**TRIGGER:** A Windows scheduled task fires and (a) exits nonzero every run,
(b) goes STALE vs its own cadence, or (c) fires every few minutes unconditionally
whether or not a session is active.

**COST:** Real, measured 2026-07-03: of 13 PP tasks, **5 FAILING** (Miner-V2,
Normalize-Paths, Sovereign-Miner, Vault-Summarize, SessionSnapshot) + **5
HIGH_FREQ** (q2-5min: Hibernation, KobiiNetworkHealthDaemonV2, WSTrim,
KickbacksGuard, Playwright-Watchdog). No token cost; CPU + host-RAM + scheduler
churn (37 node procs / 231 MB co-resident; reaper culling continuously).

**FIX:** `tools/scheduled_task_health.py` -- pure `classify_task` (hermetic) +
live `scan_live` (schtasks). Verdicts FAILING/STALE/HIGH_FREQ/OK, each with a
NON-destructive recommendation. NEVER auto-disables (verify-before-destructive:
a `--check` task exits nonzero BY CONVENTION -- blanket disable would be wrong).
One clean script-side repair shipped: `vault_summarize.py` now finds the repo's
errors.md via a script-relative PP-root fallback (was exit-2 daily from any cwd).

**ORIGEN:** Cognitive Leak Taxonomy FASE -1. The entire OS axis was unmeasured.

### UKDL TRAP T-VERIFY-BEFORE-EMIT-001 -- prevent the self-correction redo (C69 P1)

**TRIGGER:** A draft emission asserts completion ("done", "fixed", "tests pass",
"listo") but the turn's evidence stream carries NO verification signal
(PASS/FAIL, exit code, N/N gate).

**COST:** C69 P1 = 71 self-corrections, **370,081 output tokens** -- the corpus's
single largest behavioral leak. Each is a turn shipping an unverified claim that
the next turn redoes.

**FIX:** `modules/wrapper/verify_before_emit.py` -- pre-emission advisory (the
complement of HR-OUTPUT-002, which fires post-hoc). Fires only on
claim-without-evidence; silent when evidence is in the draft OR the stream, on
negation, or on no-claim. Fail-open. Wiring is Owner-side (HR-001, documented).

**ORIGEN:** Cognitive Leak Taxonomy FASE 2 (quick win C).

### UKDL TRAP T-PM03-INERT-001 -- P5 persists because the Findings Bus is never populated

**TRIGGER:** Measuring why C69 P5 (repeated in-session question, 33 cases / 90k
tok) is not being prevented despite PM-03 (Findings Bus + RedundancyTax) being
fully BUILT.

**FINDING (measured 2026-07-03):** the PM-03 bus state dir
`~/.claude/state/parallel_mesh/` **does not exist -> 0 findings ever published
across all repos.** PM-03 is built but its SessionStart-digest + Stop-publish
wiring (Owner-side, HR-001) was never installed. The dedup mechanism is inert.

**FIX (Owner-side):** P5's fix is to WIRE PM-03, NOT to build a new gate --
install the SessionStart `--digest` inject + Stop `publish_session_findings`
call. Re-measured on every audit run via `conversation_quality_audit.pm03_health()`
(the "measure before build" that saved building the wrong thing).

**ORIGEN:** Cognitive Leak Taxonomy FASE 2 (measurement B).

### UKDL NOTE T-XPANE-FIRSTLOAD-LEAK-001 -- cross-pane first-load multiplier

Peak hours run **17-26 concurrent panes** (A5); each cache-CREATES its own ~57k
first-load prefix (Anthropic cache is per-conversation, not shared cross-pane),
so ~26 x 57k = ~1.48M near-identical cache-create tokens co-resident at peak.
This MULTIPLIES the value of the already-drafted first-load trim (Proposal A/B,
propose-only per HR-001) by the concurrency factor. No new build; surfaced for
the Owner-side trim install.

**UPDATE (2026-07-03, SCS C73):** T-PM03-INERT-001 is RESOLVED. The C70 sprint
wired PM-03's consume side (`session_start_hub.js` Hook 13) and seeded the bus;
Scope A published a 4th real finding in an active session and proved the digest
round-trips. The bus dir + file now exist and are non-empty. Consume is live;
Stop-auto-publish stays agent-driven (CLI) per hub_wiring_instructions.

### T-INERT-ARCHITECTURE-TAX-001 -- the biggest reasoning-tax is built-but-inert, not missing

**TRIGGER:** A prompt proposes building NEW cognitive systems/datasets on a mature
stack (CO/PM/GK/G already sealed) to "reduce reasoning".

**FINDING (2026-07-03):** on a mature stack the dominant reasoning-tax is
architecture that is **already built but inert or unverified**, not architecture
that is missing. Scope A found PM-03 consume + GK-12 dispatcher already LIVE
(GK-12 0-drift, advisory reaching the model in-session) and the CO-08 scope-gate
already built+tested (26/26) -- only the `prelaunch.py::_gate` wrapper routing and
the declare-intent HABIT remained. Building more would have duplicated C70.

**FIX (doctrine, SCS C73 Activate-Before-Build):** verify liveness of the existing
systems with REAL data BEFORE proposing new ones. Read the live hook/module, run
the round-trip, observe the advisory in-context. Activate-and-prove precedes
design-and-build. `tools/test_scope_a_activation.py` is the regression gate.

**ORIGEN:** Cognitive Kernel Reality Scan -> Scope A execution.

### T-SCS-COLLISION-GATE-FP-001 -- a history line documenting "C69->C71" is not a live collision

**TRIGGER:** The `V-SCS-NO-COLLISION` gate (`test_cognitive_leak_taxonomy.py`)
FAILs with `graphify_c69=True` after the C69->C71 reassignment was completed.

**FINDING:** the gate's `any("SCS C69" in text)` fired on
`graphify_live_scs_c72.md:23` -- the sentence *"SCS C69->C71 collision fix"*, which
DOCUMENTS the fix, the opposite of a live re-seal. A blunt substring test cannot
tell a history note from an active claim (same class as C69's own P5 FP).

**FIX:** a file "still seals C69" only if a line names C69 WITHOUT naming C71 (a
reassignment/history line names both). FP-hardened -> 9/9. Pre-existing at HEAD,
fixed via RCA rather than waved as "not mine" (no classified FAILs at done-gate).

**ORIGEN:** Scope A baseline run surfaced the pre-existing FAIL.

### T-CLAUDE-MD-SIZE-001 -- CLAUDE.md is at its operative floor; trimming cannot shrink it further

**TRIGGER:** The `claude_md_firewall` / `trim_claude_md.py --check` WARNs that
`~/.claude/CLAUDE.md` is >= the 39750 margin (approaching the 40000 hard limit),
and a request asks to trim it below some target.

**FINDING (measured 2026-07-04):** the global CLAUDE.md is ~all OPERATIVE always-on
safety doctrine (Bash-Bridge, Parallel-Subagent caps, Anti-Waiting, HR/PR/T). The
safe provenance-only trim (`trim_claude_md.py`) removes just the dated-parenthetical
+ deep-link provenance: at 39967 chars it cut **57 chars -> 39910** and no more. The
operative floor is ~39,658 (BL-CLAUDEMD-ROUTER, 2026-06-04). **A target below ~39,900
is UNREACHABLE without deleting operative safety rules** -- which is forbidden. A
"<38000" done-gate is therefore impossible by trimming; it is an audit-disproves-
premise case (verify, honor intent = clear the 40k warning, correct the literal,
report loudly -- never blind-execute or fake the number).

**FIX:** (1) run `--dry-run`, apply the safe provenance trim (small, reversible,
HR/PR/T intact); (2) if more headroom is genuinely needed, the ONLY honest lever is
an Owner decision to relocate a specific OPERATIVE-but-non-safety block to a
JIT-loaded surface -- NEVER the Bash-Bridge / Parallel-Subagent / Anti-Waiting sets
(they must stay always-on). Do not claim a sub-floor size as achieved.

**ORIGEN:** the CLAUDE.md-trim + CO-12-wiring EXECUTION sprint (2026-07-04): the
<38000 target was below the operative floor; only 57 provenance chars were trimmable.

### HR-STALLED-SESSION-ADVISORY-001 -- a stalled/unbounded session is ADVISORY only; NEVER auto-kill

**TRIGGER:** The Process Hibernation governor (`modules/cognitive_os/process_governor.py`
`loop_advisory`) detects a pane with no new output for >30min while the session has run
>1h total (STALLED), or a session active >2h without a `/compact` reset (UNBOUNDED).

**ACCIÓN:** STOP at "surface a visible advisory to the Owner" -- the stalled/unbounded
signal NEVER changes the hibernate/keep verdict and NEVER kills a process. A long-running
pane may be doing real continuous work; only the Owner decides to `/kclear` or close it.
Fail-open ABSOLUTE: if session age is unmeasurable, emit NOTHING (silence, never a false
positive). The advisory is orthogonal to `decide()` -- proven by `V-GOVERNOR-ACTIVE-NOT-
HIBERNATED`. Formal sealing into the generator-owned `vault/hard_rules/HARD_RULES.md`
(digest-keyed, regenerates the inline mirror) is an Owner-side `tools/bug_to_hardrule.py`
step; this UKDL entry is the hand-maintained doctrine home.

**EXCEPCIÓN:** none -- there is no phrase that authorizes auto-killing a pane on a
stall/unbounded signal. Killing a live session is only ever the hibernation path
(idle>15min + not-hot + wakeable + anchored), which is a DIFFERENT gate.

**ORIGEN:** a session hung ~10h with no detection caused the Kickbacks suspension
(2026-07-04). Loop-boundedness was added to the governor as the safety net -- but as a
VISIBILITY signal, never an autonomous kill (a wrongly-killed active session is worse
than a missed advisory). Sibling of CO-12 corpus-level loop-boundedness telemetry.

### T-UNBOUNDED-SESSION-001 -- sessions >2h without /compact accrue context; the NOTE is informational

**TRIGGER:** A pane's session wall-clock age (first-turn-to-now, read from the transcript
head by `process_governor.session_start_age_min`) exceeds 2h with no `/compact`/`/kclear`
reset (a reset starts a fresh transcript, so the age is bounded by the last reset).

**FINDING (2026-07-04):** an unbounded session is NOT proof of a hang -- it may be real,
continuous work. The governor emits it as an `unbounded` NOTE (informational), distinct
from the stronger `stalled` WARN (which additionally requires >30min of no output). The
NOTE is safe to ignore when the work is genuinely ongoing; its value is making the "am I
in a 10h runaway?" question answerable at a glance instead of never.

**FIX:** treat the NOTE as a prompt to consider `/compact` (context economy) -- not a
mandate. Only the compound signal (unbounded age AND >30min idle) escalates to the stalled
WARN. Both are advisory (see [[HR-STALLED-SESSION-ADVISORY-001]]); neither kills.

**ORIGEN:** Process Hibernation Sprint 2 loop-boundedness (post-Kickbacks). Sealed under
`[[scs_c75_process_hibernation]]`; corpus-level sibling in `co_12_telemetry.loop_boundedness`.

### PR-VERIFY-HANDOFF-PREMISES-001 -- verify a handoff's factual premises with tools before acting

**TRIGGER:** A new sprint/prompt supplies premises about prior state -- "task registered in
DRY", "SCS C73 addendum", "module at path X", "X is already wired" -- written by a prior
pane/session and not re-verified this session.

**FINDING (empirical, 2026-07-03..04):** handoff premises are frequently STALE or WRONG when
multiple panes work in parallel or across compactions. Four real misses in three sprints:
(1) "PP-Hibernation task registered in DRY, pending LIVE" -> `schtasks /query` proved it was
NEVER registered; (2) "SCS C73 addendum" -> C73 is Activate-Before-Build; the work belonged
in a new C75; (3) module path `modules/session_resilience/hibernation/` -> real path is
`modules/cognitive_os/`; (4) "PM-03 inert / needs wiring" -> the CONSUME side was already
wired (Hook 13, C73); only the PUBLISH side was the gap. Each was caught by a real tool
probe, not assumed.

**FIX:** before acting on any handoff premise, verify with a real tool -- `schtasks`,
`& git log`, `Glob`/`Read`, `ls`, `pm03_health()` -- that the described state actually holds.
On a disproven premise: honor the INTENT, correct the LITERAL, report loudly
(audit-disproves-premise). NEVER blind-execute a premise into an irreversible action.
Companion of HR-PREMISE-001 (verify APIs) and the no-classified-FAILs law. Cross-ref
[[T-UNBOUNDED-SESSION-001]].

**ORIGEN:** the C75 Process-Hibernation build + this housekeeping/PM-03 sprint -- both opened
by verifying (not trusting) the handoff, which is exactly why the false premises were caught.

### T-INERT-ARCHITECTURE-TAX-002 -- a system's LOGIC can be built + tested yet never reach the live path

**TRIGGER:** A prompt asks to "build/recalibrate" behavior X, but a Reality Scan shows X's
pure logic already exists + is unit-green -- the real gap is that the LIVE entry point never
calls it.

**FINDING (empirical, 2026-07-04):** two systems in one week were "built but inert at the
call site", not unbuilt: (1) PM-03 -- consume side wired (Hook 13), publish side had no Stop
hook; (2) CO-08 -- `scheduler.decide(declared=…)` scope-gate built + tested (C65/C66), but the
live launch gate `modules/wrapper/prelaunch._gate` called the blunt `scheduler.admit()` and
never passed `declared`, so the intent-gate was unreachable at launch. Unit-green hides this:
the tests exercise the logic directly, never the live entry point. This is the **inert
architecture tax** -- building the smart layer earns zero savings until the live caller is
rewired to use it.

**FIX:** when a Reality Scan finds the logic present, do NOT rebuild it -- trace the LIVE
entry point (hook, `prelaunch`, wrapper, scheduler `admit`) and wire IT to the built logic,
fail-open, with a test that drives the ENTRY POINT (not just the pure core). If the final
hop is a live `~/.claude/` hook or the wrapper, ship the PP-internal wiring + document the
Owner-side activation (HR-001). Companion of [[PR-VERIFY-HANDOFF-PREMISES-001]] (verify the
premise) -- this one says: once verified-as-built, wire the caller, don't duplicate the layer.

**ORIGEN:** CO-08 intent-gate live-path wiring (`prelaunch._gate` -> PM-02), sealed
`[[scs_c76_co08_intent_gate]]`; PM-03 publish wiring the day before (`[[scs_c75_process_hibernation]]` sprint).

### T-SCOPE-GATE-OPT-IN-ANTIPATTERN-001 -- a gate that needs a manual per-launch action is inert in production

**TRIGGER:** A gate/feature is wired to a switch the Owner must flip by hand EVERY launch
(export an env var, pass a flag, run a CLI first) -- and the plan treats "it works when you
set the var" as done.

**FINDING (empirical, 2026-07-05):** the CO-08 scope-gate (`[[scs_c76_co08_intent_gate]]`)
was reachable at the live path but only *activated* when the Owner exported `PP_PANE_SCOPE`
by hand each launch. A per-launch manual step is not remembered -> the gate is effectively
inert, the same net outcome as [[T-INERT-ARCHITECTURE-TAX-002]] but one layer out (the caller
IS wired; the *activation* isn't). Distinct trap because the fix is different: not "wire the
caller" but "automate the activation IN the wrapper". The paired sprint premise -- "kclaude
derives the scope from a `pane_map` given the cwd" -- was itself disproven at PASO -1 (no
`pane_map`; scope is per-pane INTENT, one repo -> many panes -> many distinct scopes, so it is
NOT a function of cwd; a cold pane has no sid) -- a 5th instance for [[PR-VERIFY-HANDOFF-PREMISES-001]].

**FIX:** automate the activation where the pane is actually born -- the launcher/wrapper.
Two honest auto-paths only: (1) a first-class flag for the case only the Owner can supply
(a cold pane's intended scope), `kclaude --scope "a,b"`; (2) RECALL of what the pane itself
already declared, keyed by the real `(cwd, sid)`, on resume/restart/rehydrate so a
declaration made once persists. Never fabricate a derivation the architecture can't support
(cwd->scope). Keep the failsafe (no declaration -> blunt cap) and fail-open at every hop.

**ORIGEN:** kclaude scope auto-export (`tools/kclaude.ps1` `--scope` + `prelaunch --sid`
recall of `pm_02_intent.resolve_launch_scope`), sealed `[[scs_c77_co08_scope_autoexport]]`.

### PR-AGENT-FILES-IN-REPO-001 -- an agent file's canonical copy lives in the repo; the ~/.claude copy is a live mirror

**TRIGGER:** Creating or editing a Claude sub-agent (`~/.claude/agents/*.md`), a slash command,
or any agent-owned global config that Claude loads from `~/.claude/` but that has no
version-controlled home.

**FINDING (2026-07-05):** the file Claude actually dispatches lives in `~/.claude/agents/`, but
that directory is outside any repo -- an edit there is untracked, un-reviewable, and lost on a
machine reset. The durable source of truth must be the repo (`vault/agents/`), with the
`~/.claude/agents/` copy treated as a deployed mirror. Same shape as the canonical-vs-live hook
dispatcher drift (`[[T-HOOK-DISPATCHER-DRIFT-001]]`): two copies, the repo one authoritative, the
live one what the runtime uses. Agent files also **cold-load** -- a new/edited `~/.claude/agents/*.md`
is not dispatchable until a `/restart` (unlike hot-loaded commands).

**FIX:** write the canonical agent file to `vault/agents/` (committed), then `Copy-Item` it to
`~/.claude/agents/` (Owner-authorized; the dir is writable). Keep both in sync on every change --
the repo copy is reviewed + version-controlled, the live copy is deployed. Document the `/restart`
cold-load requirement. NEVER edit only the `~/.claude/` copy: an untracked agent is a mirror-drift
waiting to be overwritten. Companion of HR-001 (ship the PP-internal half, document the Owner-side
step) and the mirror-sync-direction doctrine.

**ORIGEN:** GK-11 Librarian agent files (`graphify-librarian` / `graphify-route-governor` /
`graphify-writeback`) shipped canonical-in-`vault/agents/` + copied live, sealed as the SCS C72
addendum (`[[graphify_live_scs_c72]]`).

### PR-CDIO-REVIEW-GATE-001 -- a visual output is not "done" until it clears the CDIO review gate

**TRIGGER:** About to declare a visual surface (UI, landing, dashboard, component, onboarding
flow, rendered marketing copy) "done" / "ready" / "shipped".

**RULE:** The surface must pass a CDIO review first. Run the `cdio-reviewer` agent (or the
deterministic `modules.cdio.scorer.score_review` over the recorded verdicts). The done-gate is
**Design Quality Score >= 80 AND zero critical issues** (verdict APPROVE). A score below 80, or
any critical issue at any score (accessibility-floor failure, broken/dead-end state, buried or
absent primary action, fabricated trust signal, dark pattern), is **REVISE** or **BLOCK** — and a
REVISE/BLOCK surface is not done. This gate is part of the PP completion standard for visual
output, not an optional polish step. Zero Findings Is Valid — a surface that clears every
threshold gets a clean 100/APPROVE and never has a defect manufactured to justify the review.

**ORIGEN:** CDIO build, sealed SCS C78 (`[[scs_c78_cdio_active]]`). The score is computed by
`modules/cdio/scorer.py` verbatim from CDIO-05 §4, so the gate is a reproducible measurement, not
a reviewer's opinion. Companion of `[[T-DESIGN-OPINION-VS-CRITERIA-001]]`.

### T-DESIGN-OPINION-VS-CRITERIA-001 -- CDIO gives criteria, never opinions

**TRAP:** Emitting a design judgment as an adjective ("this looks better", "the CTA doesn't pop",
"feels cheap"). Such a statement is not actionable, not reproducible, and not falsifiable — two
reviewers disagree and neither can prove the other wrong.

**RULE:** Every CDIO finding names a **measurable criterion** and the **observed value** that
meets or fails it. "The CTA contrast is 3.2:1, below the 4.5:1 WCAG AA floor" is valid; "the CTA
looks weak" is not. A finding a reviewer cannot state as (criterion + observed value + threshold +
severity + fix) is an impression, and CDIO does not record impressions — the deterministic scorer
drops any verdict with no observed value. This applies to praise too: "the spacing is nice" is
invalid; "all spacing resolves to the 8px base unit" is valid. Taste-level judgment that no
threshold captures (brand character, emotional tone) is handed to the human design authority, not
faked as a measurement.

**ORIGEN:** CDIO build, sealed SCS C78 (`[[scs_c78_cdio_active]]`). This is the reality contract
of CDIO-00 applied to every emission; it is what lets the rest of the PP trust a CDIO verdict the
way it trusts a test result. Companion of `[[PR-CDIO-REVIEW-GATE-001]]`.

### T-AUTORESEARCH-PANE-MAP-ALREADY-COVERED-001 -- research/SERP subagents are already filtered

**TRAP:** Re-opening the "AutoResearch/KobiiClaw subagent sessions leak into the pane_map as if
they were Owner work" gap and adding a filter for it. The gap is already closed. Acting on the
premise without reproducing it first would ship a no-op "fix" for a non-existent bug — a Reality
Contract violation (work manufactured to justify the invocation).

**RULE:** Before filtering "AutoResearch" out of `tools/build_pane_map.ps1`, reproduce the leak
first. It will not reproduce. The `$SUB_PREFIXES` array (lines ~60-66) already excludes every
research/SERP subagent transcript via `isSub`, matched against the transcript's FIRST user message:
`'contents from a SERP search'`, `'generate a list of SERP'`, `'generate a list of search queries'`,
`'expert and insightful researcher'`, `'messages below were generated by the user while running
local commands'`. Empirically verified 2026-07-06: a live run produced 52 panes / 0 research
sessions; three SERP subagent transcripts aged 0.1h (fresh, inside the 24h window) were excluded by
`isSub=True`, NOT by aging out. Owner sessions that merely mention KobiiClaw/AutoResearch in-body
(e.g. `MODO: ULTRA PLAN`) are correctly kept, because the match is on the first user message only.

Two adjacent premises are also false and must not be acted on: (1) **KobiiClaw generates no
prompts** — `modules/daemon/kobiiclaw.sh` is a tmux/SSH wrapper that opens an interactive `claude`
on the VPS (204.168.166.63); those transcripts live on the VPS filesystem and never enter the local
`~/.claude/projects` pane_map. (2) **AutoResearch spawns no claude sessions and emits no inline-code
prompts** — `modules/autoresearch/cross_signal_bus.py` writes a Markdown digest to a file,
`nightcrawler.py` runs python pipeline scripts via `sys.executable` (never `claude`), and the only
code-fence reference (`vision_scorer.py:122`) STRIPS fences from a model response (input parsing,
not generation). If a genuinely new AutoResearch first-message header is ever observed leaking, add
that literal to `$SUB_PREFIXES` — but only with a disk transcript as evidence.

**ORIGEN:** 2026-07-06 EXECUTION-MODE prompt asserted the leak + an inline-code cleanup for KobiiClaw
prompts. Audit disproved both premises before any edit (`[[feedback_audit_disproves_owner_premise]]`,
`HR-PREMISE-001`). Owner elected to seal this note instead of a no-op commit. The filter this
premise asked for already exists (added in a prior session; see build_pane_map docstring line 19-20
and footer line 251 "research/SERP agent prompts are excluded"). SCS C78 addendum v5.

---

## T-TERMINAL-NAME-FROM-PROFILE-001 — restored terminal shows the profile name, not the pane label

**TRIGGER:** A restored/reconnected Cursor terminal shows the terminal-profile or shell name
("claude", "cmd", "pwsh") as its tab name instead of the pane's distinguishing label.

**LESSON:** Terminals opened from a Cursor terminal profile (or reconnected by persistent-sessions)
inherit the PROFILE name, not the pane label. Three levers, in order of reliability:
(a) **task-fired terminals** → set the `folderOpen` task **label** to the topic; VS Code names a
task's terminal after its task label — no settings change, documented behavior (chosen: `vscode_autorun.py`
`_term_label` = `"<repo> - <topic>"[:40] + " " + sid8`, with the "is-ours" sentinel in the task `detail`
field so merge stays idempotent while the label is free to be the topic);
(b) **extension-created terminals** → pass `name` to `createTerminal` — authoritative and immutable by
shell OSC (`extension.js::termName`);
(c) **OSC rename** `\x1b]0;<label>\x07` reaches profile terminals but, under the default
`terminal.integrated.tabs.title` (`${process}`), surfaces only as the tab *description* — needs
`${sequence}` in that setting AND is host-limited (verify visually, cannot confirm headless).

**TRAPS:** `vscode.Terminal.name` is READ-ONLY — an already-open terminal cannot be renamed via the API
(only at `createTerminal` time). Keep the 8-hex session id IN the visible label — `tab_order.js::sidPrefixOf`
joins the tab back to a pane_map record by the first 8-hex run; dropping it degrades tab-order fidelity
(fail-open to lastActivity). `claude.exe`/`cmd` may stamp its own console title over a task label — verify
on a real tab before assuming any rename wins.

**ORIGEN:** 2026-07-06 EXECUTION-MODE prompt. Feasibility (PASO -1) established the dominant restore path
is auto-tasks (`task.allowAutomaticTasks:"on"`) and `pane_map.json` already carries `topic`. Shipped C+B
(Owner-approved): `AUTORUN_PASS=17/17` incl. V-TERMINAL-NAMED-FROM-PANE-MAP + V-FALLBACK-TO-REPO.
SCS C78 addendum v4 ([[scs_restore_all_panes_c78_addendum_v4]]).

---

## PR-TRANSCRIPT-RENAME-SAFETY-001 -- Retroactive session rename is APPEND-ONLY, never whole-file-immutable

**RULE.** Before any retroactive rename of existing sessions:

1. Establish the naming mechanism EMPIRICALLY, not by assumption. Verified 2026-07-06:
   the /resume picker renders the LATEST
   `{"type":"custom-title","customTitle":"<name>","sessionId":"<uuid>"}` record inside
   `<proj>/<uuid>.jsonl`. There is NO separate metadata file -- the name lives INLINE in
   the transcript, append-only. Ctrl+R and `hooks/mark-live-session.js` both set the name
   the same way: by appending one custom-title line. (A prompt CONTEXT block asserting a
   "separate metadata.json" was FALSE; PASO -1 forensics disproved it.)

2. The "sha256 of the .jsonl identical before/after" gate is IMPOSSIBLE and wrong -- an
   append changes the whole-file hash, and Ctrl+R itself would fail it. The correct
   invariant is PREFIX-BYTE-IDENTITY: `sha256(original_bytes[0:N])` unchanged, the file
   grows by exactly one valid record, the appended tail decodes to the expected object.
   Verify per file; on any mismatch, truncate back to N (revert).

3. Encoding must match the harness byte-for-byte: UTF-8 no-BOM, LF terminator, no-space
   JSON separators, key order type/customTitle/sessionId. Binary append (no text-mode
   CRLF translation, no BOM).

4. Name source = the session's own ai-title (clean, Claude-generated). NOT the pane_map
   topic (raw first prompt) and NOT a first-prompt fallback (leaks sub-agent boilerplate).
   Rename only sessions whose effective custom-title is empty or a bare hex UUID (the
   mark-live fallback that shadows the real name). Never overwrite a real Ctrl+R name.

5. Exclude sub-sessions (SUB_PREFIXES, the same set as `build_pane_map.ps1`) and MISLOCATED
   copies -- a transcript whose recorded cwd does not munge to its physical project dir is
   a resumed-from-elsewhere fork; renaming it only pollutes the wrong picker.

6. DRY-RUN always before --apply. Apply in WAVES per project dir (a wave failure stops
   before the next). Protect the running session via --skip-sid.

7. If ANY doubt about the mechanism: do not rename. Ugly names beat a corrupted transcript.

**TOOLS.** `tools/rename_sessions.py` (--dry-run/--apply, --all, per-file verify+revert);
`tools/test_rename_sessions.py` (V-gates, RENAME_PASS=9/9 on a real transcript temp copy).

**EVIDENCE (2026-07-06).** All-repos apply: 574 scanned, 164 renamed OK / 0 failed across
23 project dirs; 351 sub-sessions + 47 mislocated copies + 10 no-ai-title excluded. 9/9
safety V-gates PASS. Live sessions compose with the live-marker hook (baseTitle re-stamped
with the voltage prefix). ORIGEN: escalated EXECUTION-MODE prompt whose CONTEXT falsely
asserted a separate metadata.json; the tool was already built on the real inline-append
mechanism, so the corrected premise changed the documentation, not the code.

### PR-TRANSCRIPT-RENAME-SAFETY-001 ADDENDUM -- forward/live automation (mark-live self-heals hash -> ai-title)

**RULE.** `rename_sessions.py` is the RETROACTIVE authority (a one-shot bulk sweep). The
FORWARD path -- a brand-new session getting a readable name automatically, without re-running
the sweep -- lives in `hooks/mark-live-session.js` (the per-Stop custom-title writer). Its
base title MUST come from `hooks/session-title-lib.js::deriveReadableTitle`, which returns the
session's own CLEAN ai-title (truncated 50 + "…", byte-consistent with rename_sessions.py's
`make_title`), NEVER the raw first prompt. Behaviour: on each Stop, if the current base is
empty/hash/UUID it is re-derived; once the ai-title lands, `⚡ <hash>` self-heals to
`⚡ <ai-title>` (idempotent thereafter). A real Ctrl+R name (non-hash) is never overwritten.
Because mark-live only ever touches the OWN live session, no sub-session / mislocated-copy
exclusion is needed on this path (that is a BULK concern rename_sessions.py owns).

**ROOT CAUSE this closed.** `mark-live-session.js` was the ONLY per-Stop custom-title writer
and its old `fallbackTitle()` wrote `sessionId.slice(0,8)` (the hash) as the base -- so every
new session showed a hash in /resume until the retroactive sweep was re-run. Fixed by routing
the base through the ai-title lib + a hash->ai-title self-heal.

**TOOLS.** `hooks/session-title-lib.js` (ai-title source, `lastCustomTitle`, `isHashTitle`);
`tools/test_session_naming.js` (SESSION_NAMING_PASS=6/6: ai-title-source, no-boilerplate,
truncate, hash-fallback, self-heal, respect-Ctrl+R). Forward path only; retroactive V-gates
stay in `tools/test_rename_sessions.py`.

### UKDL TRAP T-VERIFY-EXISTING-TOOLING-BEFORE-BUILD-001 -- PASO -1 greps for a solution that already exists, not just the files the prompt names

**Level:** UKDL Trap (governance; process rule, no runtime code).

**TRIGGER:** A prompt frames an objective as "feature X is missing / not working" and names a
specific file to inspect (here: W3 `session_namer.py`). About to build the fix.

**ACCIÓN:** PASO -1 MUST also grep the repo for tooling that already SOLVES the objective
(`tools/*<verb>*`, matching UKDL/SCS entries), not only read the file the prompt names. A
prompt's premise about what exists can be stale -- the real solution may have shipped hours
earlier under a different name.

**ORIGEN:** 2026-07-06. A prompt said "W3 no produce nombres en /resume"; PASO -1 read W3 +
mark-live and (correctly) found the hash root cause -- but did NOT search for existing rename
tooling. `tools/rename_sessions.py` (sealed the SAME day, `PR-TRANSCRIPT-RENAME-SAFETY-001`)
already implemented the retroactive fix. The duplicate `retro_session_titles.js` was built AND
its `--apply` polluted ~360 sub-session/mislocated transcripts with raw-first-prompt titles
(violating the sealed rule's ai-title-source + exclusion clauses) before the collision was
caught. Fully reverted (append-only truncate-revert, prefix-byte-identity); authority
re-asserted (`rename_sessions.py --all --apply` -> to-rename 0, 0 failed). Only the genuinely-
new forward/live automation was kept. Cost: a wasted build + a corpus round-trip that a
one-line grep at PASO -1 would have prevented.

### UKDL TRAP T-KICKBACKS-UI-DEATH-NO-DISK-SIGNAL-001 -- empty statusbar with every disk signal GREEN is a live extension-host UI death, not a canary/guard fault

**Level:** UKDL Trap (governance; diagnosis rule, no runtime code changed).

**TRIGGER:** Owner reports "Kickbacks statusbar vacía + 'Kickbacks: Sign in' no responde" and
the reflex is to blame the boot.canary / PP-KickbacksGuard.

**ACCIÓN:** Read the disk signals FIRST, and know that ALL of them can be GREEN while the UI is
dead. In the 2026-07-06 incident: boot.canary ABSENT (not the cause); PP-KickbacksGuard Ready +
running clean every 2 min (healed=[] warns=[]); `kickbacks_auth_state.json` state=OK; cli-ad.json
0.3 min fresh (background ad-refresh alive) -> guard's signed-out proxy correctly GREEN. The
empty statusbar + dead command is the extension's UI layer (statusbar item + command handler
registered in `activate()`) never coming up in the CURRENT window, while the background service
survives. The debug.log even logged a clean last boot (`session.state hasAd:true`) -- so there
is NO trailing disk marker of the freeze. **The ONLY fix is an Owner UI action:** Ctrl+Shift+P ->
"Developer: Reload Window" (re-runs activate() clean); if it persists -> "Kickbacks: Restore
Claude Code", or disable/enable the extension. The agent CANNOT press Reload for the Owner.

**DO-NOT:** do NOT ship a guard "UI-freeze detector" for this. The current real debug.log tail is
clean (hasAd:true AFTER the last `activate.fatal Canceled`), so any log-tail signal would say
"not frozen" on the very state the Owner reports as frozen -- a detector that misses the real
positive is false confidence (Reality Contract / HR-OUTPUT-002). This failure mode has no
reliable disk footprint; INV-CANARY/INV-AUTH cannot see it BY CONSTRUCTION. Documenting the
limitation is the correct seal, not a fragile detector.

**ORIGEN:** 2026-07-06 escalated EXECUTION-MODE prompt assumed a stale canary was blocking boot.
Diagnosis disproved the premise (canary absent, guard healthy, ads fresh). 67 activate.fatal
/boot.cycle lines in debug.log; a cascade of `activate.fatal {"msg":"Canceled"}` at 13:11 UTC
(4 activates in 16 s = extension-host thrash) is the likely origin of a wedged host, but the
last boot (13:26 UTC) logged clean -- confirming the freeze is a live-render state only the
Owner sees. Kickbacks token lives in Cursor SecretStorage (DPAPI) and survives reload; re-auth
is Owner-only. REMOTE_DELTA unaffected (docs-only seal).

### UKDL TRAP T-KICKBACKS-GAP-PATTERN-001 -- periodic billing gaps with the extension 100% healthy locally = window-focus-gated billing, not a local fault

**Level:** UKDL Trap + guard invariant (INV-FOCUS / INV-AUTHSTREAK shipped in kickbacks_guard.ps1).

**TRIGGER:** Kickbacks stops registering impressions periodically during "active" sessions
(pattern: 2026-07-03 gaps ~12:08 & 17:32; 2026-07-06 gap 15:45+), extension VISUALLY active,
and the reflex is to hunt a local fault (canary / auth / vsix / killed).

**ACCIÓN:** Know that EVERY locally-observable signal can be GREEN during a real billing gap.
2026-07-06 forensic (gap 13:43-14:13Z): auth.refresh 6/6 ok, vsix consecutiveFails=3 (backup
URL works), session.state signedIn:true killed:false hasAd:true throughout, canary absent. The
ad renderer `vibe-ads-statusline.mjs` is a PURE renderer -- ZERO network / ZERO impression
report -- so impression accounting lives entirely in the CLOSED extension + backend, which
bills ONLY while the Cursor window is FOREGROUND (dashboard label "100% billed while focused").
The gap is focus-gated suppression behaving AS DESIGNED, invisible because PP had no focus
telemetry -- which is exactly why the prior forensics (all local, all green) never found it.
The debug.log records NO focus / impression / billing / serving events at all; confirm the
cause on the dashboard's own "Window focus" section (red bars in the gap = confirmed).

**CAUSES (all Host-limited -> notifiable, none PP-preventable):** (a) window focus lost while
Cursor runs [primary, evidence-backed]; (b) auth.refresh failure streak dropping the session;
(c) vsix-url-blocked degrading the extension (already covered by INV-VSIX >10). PP CANNOT force
focus, re-auth, or fix the backend -- the honest fix is DETECT + visible advisory before the
gap widens, turning an invisible problem into a visible one.

**FIX SHIPPED.** `tools/kickbacks_guard.ps1` (SCS C28: read-before-modify satisfied) gained:
INV-FOCUS (Win32 GetForegroundWindow; advisory + flag when Cursor unfocused >= 5 min while
running; fail-open to SILENCE on indeterminate foreground so it can NEVER false-alarm; anchor
is a known-focused sample so the first unfocused sample can't fire; throttled 30 min; clears
the flag on regain) and INV-AUTHSTREAK (trailing auth.refresh ok:false streak >= 5 -> warn;
dormant when last outcome is ok). Both advisory-only (HR-STALLED-SESSION-ADVISORY-001), never
auto-act. Guard runs LogonType=InteractiveToken so foreground is queryable. Verified 4/4:
plain=billing-eligible+no flag; -SimulateUnfocused=toast+flag written; plain=regained+flag
cleared; -SimulateAuthStreak=warn. ORIGEN: 2026-07-06 EXECUTION-MODE "esto no deberia pasar
nunca mas"; prior forensic stopped at local-green and never checked focus.

### T-KICKBACKS-GAP-PATTERN-001 ADDENDUM v2 -- focus DISPROVEN; render-staleness is the true gate

**CORRECTION (loud, per no-classified-FAILs + premise-disproved doctrine).** v1 above named
window focus the "primary, evidence-backed" cause. The Owner then checked the dashboard's
Window-focus section: **100% green, zero red bars -- the gap happened WITH Cursor focused.**
Focus is therefore NEITHER the cause of this gap NOR a sufficient explanation. INV-FOCUS stays
as a secondary net (focus loss is one way renders can stop) but is NOT authoritative.

**TRUE ROOT CAUSE (elimination, not hypothesis).** During the gap the extension had
`hasAd:true` the WHOLE time, so billing is NOT timer-based-while-serving; and focus was green,
so it is NOT focus-gated. Everything local was green. The only remaining gate is the ad
actually RENDERING/DISPLAYING. The CLI ad is drawn by the statusline, which Claude Code
re-invokes ONLY on activity (a turn running / spinner ticking). Idle panes -- even focused --
stop rendering -> the ad stops displaying -> impressions pause. **Proof:** gsd-statusline.js
rewrites `%TEMP%/claude-ctx-<sid>.json` on every render; the newest such mtime across live
sessions went SPARSE at exactly 15:45 (renders/min: ~11 at 15:42, then 1 every 10-16 min),
the SAME instant the dashboard Activity Ledger's last row landed. Render activity == billing
activity. The gaps are CC-idle windows (Owner not actively running Claude turns), orthogonal
to focus.

**FIX SHIPPED (KickbacksGuard v5).** INV-RENDER: newest UUID-named `claude-ctx-*.json` bridge
mtime; when >= RenderStaleMinutes (10) old while Cursor runs, advisory + flag "sin render del
statusline en X min -> Kickbacks no acumula impresiones ... ejecuta un prompt para reanudar".
It is the AUTHORITATIVE earning-health signal (focus/auth/vsix are secondary). **HARD ETHICAL
LINE:** PP MUST NEVER auto-invoke the statusline to fake a render -- that is manufacturing ad
impressions for an advertiser = fraud. The only honest lever is VISIBILITY so the Owner chooses
to resume. Verified 3/3 (fresh->no flag; -SimulateRenderStale->toast+flag; fresh->cleared).
ORIGEN: 2026-07-06 follow-up; the render bridge (a PP context-monitor artifact) turned out to
be the exact per-render impression proxy the closed extension never exposed.

### T-KICKBACKS-GAP-PATTERN-001 ADDENDUM v3 -- render-staleness DISPROVEN; the bridge is NOT an ad-render proxy; INV-RENDER RETRACTED

**CORRECTION (loud).** v2 claimed the `%TEMP%/claude-ctx-<sid>.json` bridge is a faithful
per-render/impression proxy and shipped INV-RENDER on it. That was WRONG. The Owner was
ACTIVELY prompting Claude 15:45-16:27, so renders were continuous -- yet the bridge mtimes were
sparse (10-16 min gaps). That is impossible if the bridge tracked renders. It does not.

**WHY the bridge is not a render proxy (live probe, deterministic).** The bridge is written by
`gsd-statusline.js` (the PP HUD chained BELOW the ad), ONLY inside `if (remaining != null)`.
Probe: pipe a CC statusline payload WITH `context_window.remaining_percentage` -> ad prints AND
bridge written; pipe the SAME payload WITHOUT it -> the ad STILL prints (impression happens) but
NO bridge is written. So any render whose payload lacks context (common: early session, many
refresh types) displays the ad but leaves no bridge. Confirmed in the wild: active session
029d13b9 (InfinityOps) ran with ZERO bridges ever. Bridge-staleness is a MEASUREMENT ARTIFACT
of the `remaining!=null` gate, not an ad-render gap -> a detector on it FALSE-ALARMS during
active use. INV-RENDER retracted to an inert note (2026-07-06); params kept but unused.

**What is actually known now.** Config is global + uniform (every pane's statusLine is the ad
-> gsd; no project/local override, verified). The ad (`vibe-ads-statusline.mjs` top branch)
writes NOTHING when it renders, so there is currently NO reliable LOCAL proxy for an ad
impression. During the gap the ad was almost certainly rendering (active panes, fresh cache,
ad prints even on null-ctx). Therefore the impression gap is NOT a CLI-render gap -- it lies in
the CLOSED extension's impression accounting/reporting, which PP cannot observe. Focus,
render-staleness, auth, vsix, canary are ALL disproven for this gap.

**Only valid path forward (Owner-gated, not yet shipped).** An UNGATED per-invocation append
log (rotated, never-throw) at the TOP of `gsd-statusline.js` records ts+sid on EVERY render
regardless of context -> ground-truth per-pane render cadence. If the next gap shows gsd firing
continuously (ad rendering) while the dashboard shows no impressions, the fault is proven
extension-side and PP genuinely cannot fix it (only surface it). HARD LINE unchanged: never
auto-render to fake impressions (fraud). LESSON (meta): two detectors (INV-FOCUS, INV-RENDER)
were shipped on proxies that did not hold; per anti-antipattern Rule 12, STOP building detectors
on unvalidated proxies -- instrument for ground truth first, then detect.

### T-KICKBACKS-GAP-PATTERN-001 ADDENDUM v4 -- ROOT CAUSE CONFIRMED: extension event-loop suspension; instruments A+B shipped

**CONFIRMED (two independent timelines, Owner-supplied).** The impression ledger resumed at
**16:15**; the Kickbacks debug.log woke from a dead silence at **16:11:52 local**
(`auth.refresh ok`). It went silent at **15:43:24** vs the ledger's last row at **15:45**.
So: impression gap 15:45->16:15 (30 min) ~= extension event-loop silence 15:43->16:11:52
(28 min), both edges aligned (~3 min wake->refresh->first-counted-render lag on resume).

**ROOT CAUSE.** The Kickbacks extension-host background loop was SUSPENDED / timer-throttled for
~28 min while Cursor was focused and the Owner was actively prompting Claude. During suspension
ALL of its periodic work halted -- `auth.refresh`, `session.state`, ad-cache refresh, and
impression accounting -- so no impressions billed despite continuous CC statusline renders and
green window focus. Not focus, not render (the ad kept rendering), not auth/vsix/canary: the
extension's own clock stopped. Most likely OS/Electron timer or power throttling of the ext-host
process (independent of top-level window focus). Host-level, NOT PP-fixable -- but now capturable.

**INSTRUMENTS SHIPPED (both, pure data capture, no alarm).**
- **A (guard, repo-tracked):** INV-TELEMETRY appends every 2 min to
  `~/.claude/state/kickbacks_earning_timeline.log`: adAge (cli-ad.json freshness), dbgAge
  (debug.log mtime age == extension-quiet proxy), renderAge (claude-lastrender.json), fg,
  cursor. Rotated 2000 lines, fail-open. Verified: logged `adAge=0 dbgAge=21.8 renderAge=0
  fg=Cursor cursor=1` -- and dbgAge=21.8 min at capture time was itself a live quiet window.
- **B (gsd-statusline.js, LIVE-ONLY -- NOT repo-tracked):** an UNGATED marker at the top of the
  render path writes `%TEMP%/claude-lastrender.json {ts,session}` on EVERY render (fixes the
  null-context blind spot that made the old bridge a false proxy). Verified: updates on BOTH
  with-context and null-context renders (old bridge updated only the former). Durability note:
  `~/.claude/hooks/gsd-statusline.js` is a global hook outside the power-pack repo, so this edit
  is not version-controlled; if ~/.claude/hooks is ever reset, re-apply this line after the
  `const remaining = ...` line (best-effort, never throws):
  `try { fs.writeFileSync(path.join(os.tmpdir(),'claude-lastrender.json'), JSON.stringify({ts:Math.floor(Date.now()/1000),session})); } catch (e) { /* best-effort marker */ }`

**PROMOTION PATH (deferred until validated).** Once the timeline captures a full gap, a detector
can fire on `dbgAge >= <validated-threshold> while cursor=1` (extension-quiet == not earning) --
a signal tied to the CONFIRMED mechanism, unlike the two retracted proxy-detectors. Thresholds
from real data, not a guess. HARD LINE unchanged: never auto-render to fake impressions (fraud).

### T-KICKBACKS-GAP-PATTERN-001 ADDENDUM v5 -- candidate FIX applied: --disable-background-timer-throttling on Cursor launch

**HYPOTHESIS FIX (Owner-approved, host-side, pending telemetry validation).** If the ~28-min
event-loop suspensions are Chromium renderer/timer throttling of the ext-host, disabling that
throttle should PREVENT them (not just surface them). Applied `--disable-background-timer-throttling`
to Cursor's launch shortcuts (Cursor.exe took no flags before). `argv.json` was NOT usable --
the VS Code-family runtime-args file only honours a fixed allowlist that excludes this switch;
the shortcut Arguments are the reliable carrier.

**WHAT CHANGED (reversible).** Three shortcuts, all pointing at
`%LOCALAPPDATA%\Programs\cursor\Cursor.exe`, Args set from empty to the flag:
Start Menu `Programs\Cursor.lnk`, `Programs\Cursor\Cursor.lnk`, and the Taskbar pin
`...\Quick Launch\User Pinned\TaskBar\Cursor.lnk`. Each backed up once to `<lnk>.bak-preflag`.
REVERT: `tools/cursor_apply_perf_flags.ps1 -Revert` (or restore the .bak-preflag copies).

**TOOL (repo).** `tools/cursor_apply_perf_flags.ps1` -- idempotent apply/-Revert of the flag(s)
across all discovered Cursor shortcuts, backup-once, ASCII-clean, PSParser-0. Re-run AFTER a
Cursor auto-update (updates can recreate Start Menu shortcuts and drop the flag).

**TAKES EFFECT ON FULL RESTART ONLY.** A single-instance re-launch onto a running Cursor just
focuses it without the flag. Owner must quit ALL Cursor windows then relaunch. Verify live:
`Get-CimInstance Win32_Process -Filter "Name='Cursor.exe'" | ? { $_.CommandLine -notmatch '--type=' } | Select CommandLine`
should show the flag on the main process.

**VALIDATION LOOP.** Instrument A (`kickbacks_earning_timeline.log`) is the judge: after the
restart, if `dbgAge` stops spiking while `cursor=1` (no more extension-quiet windows) and the
dashboard shows no new gaps, the fix is proven on this machine. If gaps persist, escalate to the
sibling switches `--disable-renderer-backgrounding` + `--disable-backgrounding-occluded-windows`
(pass all three via `-Flags`). Change ONE variable, measure, iterate -- do not stack blindly.

---

### PR-PANE-MAP-LIVE-ONLY-001 (2026-07-06, SCS C80)

The PP Sessions panel and post-crash restore use only the panel-facing pane map
(OPEN-NOW + ACTIVE + RECENT tiers); the history exists but is separated
(`pane_map_archive.*`, `pane_map_history/`). **"54 panes in a repo" is a filtering
/ framing bug, not reality** -- the builder lists every transcript touched within
the collection window, so the total conflates open tabs with recent closed
conversations. The map now leads with the OPEN-NOW count and demotes stale-content
panes (real last turn older than the RECENT boundary, dragged in by a batch
mtime-touch) to ARCHIVE. Tier = INTERNAL-timestamp age, never file mtime
(cross-ref `T-PANE-MAP-FALSE-LIVE-MTIME-001`); the 12-min OPEN-NOW floor is proven
and must not be relaxed. Versioning snapshots on topology change + >=15min gate,
7-day retention; the Workspace Session Registry (`workspace_sessions.jsonl`)
records which repos held OPEN-NOW panes at each snapshot instant.
Artifacts: `tools/build_pane_map.ps1`, `tools/pane_map_snapshot.py`,
`tools/test_pane_map_snapshot.py`.

---

### PR-TEST-AUDIT-BEFORE-FEATURE-001 (2026-07-08, SCS C81)

Before any NEW feature in a repo, verify there is no active F1 (logica critica sin
test) on the surface the feature touches. If there is, write the minimum test for the
critical functionality FIRST, then build the feature. Rationale from the Global Testing
Audit: a healthy aggregate test count is NOT evidence for any specific surface --
KobiiCraft has 268 JUnit files and 1,596 passing assertions yet `EconomyService` (money
transfer, the most abusable surface) has ZERO test references. Grep the specific surface
you are about to modify; never infer its coverage from the repo total. Cross-ref the F1-F8
taxonomy (`vault/knowledge_base/testing/testing_failure_taxonomy.md`) and the V-gates x3
hermetic standard (`testing_universal_standards.md`).

### T-MINECRAFT-TESTING-CONCENTRATION-001 (2026-07-08, SCS C81)

**Rewritten from the disproved `T-MINECRAFT-TESTING-BLIND-SPOT-001` premise.** The plan
asserted Minecraft plugins run "sin ningun test" -- disk evidence disproves it: KobiiCraft
has 268 JUnit files under `src/test/java` and `mvn -o test` on JDK 21 runs 1,596 + 10
green assertions. The real finding is CONCENTRATION, not absence: 232 of 268 test files
(87%) live in ONE plugin (KobiMapEngine), MockBukkit is wired in 1 of 90 poms, and the
operator-risk surfaces (economy in kobicore, rewards in KobiiLuckyArena, permissions) sit
nearly untested -- the inverse of where the tests are. MockBukkit permits headless,
hermetic plugin testing without a live server (proven: 1,596 green offline); the harness
works, it is simply concentrated in one non-gameplay-critical plugin. Toolchain contract:
the prebuilt test classes are Java 21 (class file 65); JDK 17 fails with
"compiled by a more recent version" -- pin `JAVA_HOME` = JDK 21. Fix: wire MockBukkit into
kobicore, write `EconomyServiceTest` (transfer allow / deny-insufficient / boundary /
concurrency). ORIGEN: Global Testing Audit 2026-07-08; the plan's original wording was
empirically false and would have sealed an invented falencia
(cross-ref feedback `no-classified-fails-at-done-gate`, `plan-code-is-hypothesis`).

## PR-FABLE-DELTA-ONLY-001 — Spend frontier tokens only on the delta (2026-07-09)

**TIPO:** Process Rule (sealed with the Fable Advantage Distillation Suite, SCS C82).

**REGLA (verbatim, inheritable):** When a frontier model is available, spend its tokens
only on what the existing PP systems cannot already produce. If the PP can produce the
result — by CO-03 routing, CO-05 asset reuse, GK navigation, a deterministic rung, or a
prior distilled protocol — the frontier model is **not invoked**. Every frontier
interaction that *does* occur **must deposit a classified delta before the session closes**
(NEW / STRONGER / DUP / DISCARD against the CO-05 baseline). A session that spent a frontier
token and closed with no classified deposit has leaked a moat's worth of capital as a log
line.

**POR QUÉ (cost asymmetry):** a wrongly-*declined* call costs one bounded retry; a
wrongly-*admitted* at-floor call costs the recurring frontier bill for that entire class
every time it is asked again without a distilled replacement — an unbounded, silent,
compounding error. Symmetrically, a missed deposit costs every future session that would
have started from the higher floor. Weight the gates toward declining on admission and
forcing on deposit.

**CÓMO SE APLICA:** FD-01 is the classifier of this decision (delta vs at-floor); FD-05
converts the frequently-admitted classes into CO-03 routing rules + CO-05 assets so the
next ask is served cheaper; FD-04 proves a distilled capability actually survives the
downgrade (else it stays `frontier-only`, an honest hypothesis, not a claimed advantage).
Success metric = **CO-12 model-demotion / Opus-avoided count + cognitive-compression
ratio**, reused, never re-invented. No dependence-reduction claim without a
`(metric, source, value)` triple (CO-12 Telemetry-Before-Claims).

**ORIGEN:** Fable Advantage Distillation Reinforcement Suite (FD-00…FD-07), sealed
**SCS C82** 2026-07-09. Root law of FD-00; the routing rule FD-01/FD-05 feed into CO-03.
Cross-ref: `fable_distillation_scs_c82.md`, `fable_distillation/FD_INDEX.md`,
`fable_distillation/fd_00_fable_advantage_doctrine_and_session_protocol.md`.

---

## T-FRONTIER-SESSION-DETECTION-001 -- FD-07 flywheel fires only on frontier sessions

**TRIGGER:** the FD-07 close-boundary flywheel (Stop-chain child
`modules/fable_distillation/fd_07_flywheel.py`) deciding whether to turn the distillation
loop at a session's close.

**REGLA:** the flywheel turns ONLY when `PP_FRONTIER_SESSION=1` is exported. `kclaude.ps1`
sets it unconditionally because kclaude launches the host default model, which is Opus (a
frontier model) on this host -- so a kclaude session IS a frontier session by construction.
A bare `claude` launch never sets it, so the Stop hook runs normally WITHOUT the flywheel (a
silent no-op). The launched claude and every hook child it spawns inherit the env var.

**POR QUE:** the flywheel is only worth its close-verification + writeback cost on a session
that actually spent frontier tokens; running it on every Sonnet/Haiku session would pay the
loop overhead with no delta to compound (FD-07 II.6 token-ROI priced over the class).

**FAIL-OPEN:** unset env -> no loop turn, session closes normally; malformed Stop JSON ->
cwd falls back to `os.getcwd()`; any flywheel error -> swallowed, `main()` ALWAYS exits 0.
The flywheel never blocks session close (mirrors the GK-08 session_writeback contract).

**HONEST (CO-10):** live only after the canonical dispatcher + kclaude are Copy-Item'd to
their live mirrors (`~/.claude/hooks/hook-dispatcher.js`, `~/.claude/kclaude.ps1`,
`~/.claude/bin/kclaude.ps1`) -- the Owner-side registration step (T-HOOK-DISPATCHER-DRIFT-001).
A v2 refinement gates on the actual launch model rather than assuming kclaude == frontier.

**ORIGEN:** FD EXECUTION-mode activation (H2), SCS C82 addendum 2026-07-09.
Cross-ref: `fable_distillation_scs_c82.md`, `fd_07_fable_learning_flywheel.md`,
`plans/fd-hooks-activation-2026-07-09.md`.

---

## PR-FRONTIER-AS-RD-001 -- a frontier session is an R&D operation, not a query

**TRIGGER:** about to launch or plan a session with a frontier model (Opus/Fable) for
discovery, architecture, critique, or synthesis work.

**REGLA:** treat every frontier token as R&D capital, not operational cost. Compile the
session first (`modules/frontier_intelligence/session_compiler.py` -> the 9-component
SESSION_ZERO plan: minimal context <2000 tok, ROI-ranked questions, 5-category budget,
stopping criteria, writeback + distillation + transfer plan), and close it with a
writeback (the FD-07 flywheel). A session without a compiled plan and without a
writeback is capital spent with no asset kept.

**POR QUE:** the durable advantage is not the answer (commodity) but the permanent asset
the session deposits that lowers the need for future frontier tokens. The Token IRR
(`modules/frontier_intelligence/token_irr.py`) measures the return numerically:
immediate_roi, reuse_multiplier, compound_roi, payback, and the Frontier Dependence
Index -- fed to CO-12, never a parallel accountant (FD-07 Invariant 1). No ROI claim
without its `(metric, source, value)` triple.

**COMO SE APLICA:** FIOS is the EXECUTION layer over the FD KNOWLEDGE: FD-00 defines what
a distillation is; FIOS compiles/prices/evolves. session_compiler ranks questions via the
FD-00 admission gate and the FD-07 deposits floor; token_irr reads the deposits ledger +
CO-12 fd_metrics; nothing forks the dependence metric.

**FAIL-OPEN:** every FIOS engine swallows its own errors and returns a benign result --
a planning/metric/evolution tool must never block the session it serves.

**ORIGEN:** FIOS execution-first build, SCS C84, 2026-07-10. Reality scan of 17 candidate
systems -> 3 NEW (code) / 7 thin-extend / 5 covered by FD/CO/PM/GK.
Cross-ref: `frontier_intelligence_os/FIOS_INDEX.md`, `modules/frontier_intelligence/`.

---

## T-FIOS-EVOLUTION-LOCK-001 -- the Dataset Evolution Engine proposes, never applies

**TRIGGER:** the FIOS Dataset Evolution Engine
(`modules/frontier_intelligence/evolution_engine.py`) detecting a mutation candidate
(compress / split / merge / reinforce / deprecate / abstract / specialize) in a
knowledge_base dataset.

**REGLA:** the engine writes a proposal to
`frontier_intelligence_os/pending_mutations.md` and STOPS. It never edits, splits, merges,
or deletes a dataset. Every mutation to a sealed dataset requires explicit Owner promotion
by hand. Unapproved proposals accumulate in the pending file for periodic review.

**POR QUE:** a sealed dataset is a curated, cross-referenced artifact; an automatic
mutation could silently corrupt a family's invariants or drop load-bearing content. This
mirrors the cdio-standards-librarian and graphify agents (propose-with-evidence,
never-auto-apply) and the HR-SECRET-003 recommend-and-wait discipline.

**FAIL-OPEN:** a missing/unreadable kb dir -> zero proposals (never a raise); a failed
proposal-file write -> None, the scan result is still returned. The engine is read-only
over the datasets it scans.

**ORIGEN:** FIOS execution-first build, SCS C84, 2026-07-10. The one genuinely-new FIOS
responsibility (whole-KB dataset evolution; FD-06 mutates assets, GK-07 the graph, the
cdio-librarian only CDIO -- none did whole-KB).
Cross-ref: `frontier_intelligence_os/FIOS_INDEX.md`, `evolution_engine.py`.

## T-FIOS-FRONTIER-SESSION-DETECT-001 -- PP_FRONTIER_SESSION is the FIOS activation signal

**TRIGGER:** wiring any FIOS engine (session_compiler preflight, token_irr Stop) to a
live surface, or reasoning about when FIOS should fire.

**REGLA:** `PP_FRONTIER_SESSION=1` is the single signal that a session is frontier
(R&D-worth). `tools/kclaude.ps1` exports it UNCONDITIONALLY (kclaude launches Opus, a
frontier model, by construction; a bare `claude` launch never sets it). So:
- The **token_irr Stop entry** gates on it alone -- exactly like `fd_07_flywheel.py`.
- The **session_compiler preflight** gates on it AND an Owner-declared objective (env
  `PP_SESSION_OBJECTIVE` or repo `.pp_frontier.json`). The extra gate is mandatory: since
  kclaude sets the flag on every launch, firing the compiler on the flag alone would write
  a near-empty SESSION_ZERO per launch = the bloat `evolution_engine` exists to flag
  (PR-FABLE-DELTA-ONLY-001). Verify the flag is already exported before inventing new
  detection infrastructure.

**POR QUE:** a single, already-exported activation signal avoids a parallel detector; the
objective sub-gate keeps the "compile a plan" surface from degrading into per-launch spam
(profundidad sobre cantidad).

**FAIL-OPEN:** flag unset / python missing / compile error -> the launch and the Stop both
proceed with zero FIOS output. FIOS never blocks the session it serves.

**ORIGEN:** FIOS live-path wiring, SCS C84 addendum, 2026-07-10. Mirror of the FD-07 cadence
gate (`_is_frontier_session`). Cross-ref: `FIOS_INDEX.md`, `tools/kclaude.ps1`,
`hooks/hook-dispatcher.js`, `T-HOOK-DISPATCHER-DRIFT-001`.

## PR-DUPLICATE-TO-ADVANTAGE-001 -- ninguna duplicidad termina en rechazo (2026-07-10)

**TRIGGER:** detecting that a proposed system, dataset, module, or capability overlaps
something the ecosystem already owns (a duplicate / near-duplicate architecture proposal).

**REGLA:** a detected duplicate is NEVER a bare rejection. It is a search signal. Every
detection activates the D2A Engine (`modules/duplicate_to_advantage/d2a_engine.py`):
detect (3-axis coverage) -> map the capability gap around the parent (14 dimensions) ->
generate vertical + horizontal reinforcement candidates -> score the portfolio on 16
dimensions by expected-compound-value / (complexity + maintenance + debt) -> emit a
minimal BUILD CONTRACT under the 10-rule anti-inflation gate. The duplication is the
coordinate of the frontier of the non-redundant capability space, not a dead end.

**POR QUE:** every sealed family (CO 9->2, PM, GK 40->13, FD 26->8, FIOS 17->3+doctrine)
executed this procedure by hand under STOP-#1 pressure. Making it repeatable, deterministic,
and zero-token stops the ecosystem from either accreting near-duplicates (skipped scan) or
rejecting the adjacent capability the duplicate points at.

**FAIL-OPEN:** empty / pathological proposal -> a DEFER verdict, never a raise, never a
wrong block. The governor of builds must never itself block a build by failing. Propose-
never-build: the engine renders a verdict; only the Owner promotes a BUILD CONTRACT.

**ORIGEN:** D2A Engine, SCS C85, 2026-07-10. Reality Scan found 0/6 proposed components
pure-NEW; the honest build (D2A applied to itself) is 1 doctrine + 1 engine, not 6 datasets.
Cross-ref: `duplicate_to_advantage/D2A_INDEX.md`, `d2a_engine.py`,
`[[T-D2A-ANTIINFLATION-VIOLATION-001]]`, `[[PR-FABLE-DELTA-ONLY-001]]`.

## T-D2A-ANTIINFLATION-VIOLATION-001 -- a dataset where a Part would suffice is a violation

**TRIGGER:** the D2A Build Governor (or any agent following D2A doctrine) about to
recommend a full new dataset / module / family for a reinforcement capability.

**REGLA:** every new dataset must first BEAT four cheaper alternatives, in order: a new
UKDL rule, a new dataset Part, a new eval, and not-building-at-all. The artifact ladder
(`ukdl_rule < eval < dataset_part < benchmark < interface < tool < gate < protocol <
dataset`) is climbed from the bottom; a full dataset is reachable only for a genuinely-new,
low-coverage, low-reuse candidate that has cleared every lighter rung. Recommending a
dataset while parent coverage >= 40% is a contract violation. More files is never success.

**POR QUE:** the most expensive mistake in a mature ecosystem is building a whole family
when a Part, rule, or eval carries the entire delta -- the exact bloat GK-00 (one system,
no parallels), SCS C41, and PR-FABLE-DELTA-ONLY-001 forbid. A governor that exempts its own
family is theatre; D2A ran itself through the pipeline and shipped 1 doctrine + 1 engine.

**FAIL-OPEN:** the anti-inflation ledger is advisory metadata on the BUILD CONTRACT; a
failing rule surfaces which and why, it never crashes the verdict. The Owner rules.

**ORIGEN:** D2A Engine, SCS C85, 2026-07-10. Companion of `[[PR-DUPLICATE-TO-ADVANTAGE-001]]`
and the FIOS execution-first precedent (17 systems -> 3 engines + 1 doctrine, zero prose
datasets). Cross-ref: `d2a_00_duplicate_to_advantage_doctrine.md` Part III.

## T-D2A-GATE-KEYWORD-SCOPE-001 -- the D2A gate intercepts CREATION only

**TRIGGER:** the D2A advisory gate (`hooks/d2a_gate.js`, UserPromptSubmit) evaluating an
Owner prompt, or any change to its keyword sets.

**REGLA:** the gate fires ONLY on a proposal to CREATE a new system / dataset / module.
Detection is CONJUNCTIVE: (a creation verb) AND (an architecture-level noun) AND NOT (a
verb acting on something that already exists). It NEVER intercepts use, query, extension,
wiring, activation, testing, refactor, rename, or modification of an existing system.
**A false positive is strictly worse than a false negative** -- an advisory on a prompt
that was never a creation proposal trains the Owner to ignore the gate, which destroys the
only value it has. When in doubt, stay silent.

**POR QUE:** the gate's authority is entirely borrowed from its precision. It never blocks,
so its only lever is the Owner's attention; spending that attention on a false positive is
the one unrecoverable failure. Under-firing costs a missed nudge; over-firing costs the
gate itself.

**FAIL-OPEN:** engine missing / python broken / timeout / non-JSON stdin / unparseable
verdict -> empty stdout, exit 0. The gate NEVER exits 2, NEVER denies, NEVER blocks
(level-2 on the CO-10 ladder, mirroring `graph_first_gate.js` / GK-12). A silent gate is
always preferable to a gate that stops the Owner's work.

**SURFACE NOTE (empirical):** it is a **UserPromptSubmit** hook, not PreToolUse. A
PreToolUse hook receives `{tool_name, tool_input}` and never sees the Owner's prompt text,
so "advise before Claude starts building, based on the Owner's own words" is not
implementable there. Precedent: `prd-keyword-sentinel.js`. Do not "fix" this by moving it.

**ORIGEN:** D2A gate wiring, SCS C85 addendum, 2026-07-10. Companion of
`[[PR-DUPLICATE-TO-ADVANTAGE-001]]`. Cross-ref: `hooks/d2a_gate.js`,
`hooks/hook-dispatcher.js` (UserPromptSubmit-chain), `[[T-HOOK-DISPATCHER-DRIFT-001]]`.

---

### PROCESS RULE PR-LIVENESS-CHECK-BEFORE-SHIP-001

**TRIGGER:** Declaring a wired component "done"/"shipped" (a hook entry, a Stop-chain
producer, a scheduled task, an extension surface).

**ACCIÓN:** The ecosystem verifies at CONSTRUCTION time (V-gates, hermetic x3) and is
blind POST-SHIP: a V-gate proves code works WHEN INVOKED, nothing proves anything
invokes it. `built != wired` is therefore a recurring CLASS (dispatcher drift, the
PM-03 producer-without-consumer bus, orphan modules/fields, the FD then FIOS Copy-Item
last-miles). No new wired component is complete without a row in the D1 Liveness Ledger
(`modules/liveness/liveness_ledger.py` `default_registry()`) declaring its surface +
a deterministic evidence probe (hash-drift / co12-signal-recency / pm-bus / file-mtime).
Ship + silence surfaces as WIRED-BUT-SILENT within a day; the loop is *ship -> is it
alive?*, closed by the ledger, not rediscovered sessions later.

**ORIGEN:** Strategic-gaps audit D1, SCS C87, 2026-07-10. The activation gap had bitten
>=8 sealed lessons as one shape before it was made a monitored invariant. Cross-ref:
`modules/liveness/liveness_ledger.py`, `vault/audits/liveness_report.md`,
`[[T-HOOK-DISPATCHER-DRIFT-001]]`, `[[T-OWNER-QUEUE-INVISIBLE-001]]`.

---

### UKDL TRAP T-OWNER-QUEUE-INVISIBLE-001

**TRIGGER:** The agent ships the PP-internal half of a change and DOCUMENTS an
Owner-side residual (HR-001 Copy-Item, a scheduled-task registration, a settings.json
hook entry) somewhere -- a vault/plans doc, a memory file, a session-end emission.

**SÍNTOMA:** Those residuals were tracked nowhere as a SET, so built->live latency was
unbounded and invisible: the PM-03 consumer wiring sat pending 6+ days with nobody
watching. A documented-but-unqueued residual is a silent gap.

**ACCIÓN:** Every Owner-side residual goes into the durable `vault/OWNER_QUEUE.md` at
SHIP TIME (same commit), each item copy-paste-ready. The D4 activation layer
(`modules/owner_queue`) ingests its `[PENDING]` sections into a materialized view the
SessionStart hub surfaces past a 24h grace, and auto-clears a row when its component
goes LIVE (D1 composition). One human surface (the vault doc), one dynamic layer
(the engine) -- never a second competing queue.

**ORIGEN:** Strategic-gaps audit D4, SCS C87, 2026-07-10. Reconciled with a
parallel-pane `vault/OWNER_QUEUE.md` (commit 1fedb79) instead of shipping a duplicate.
Cross-ref: `modules/owner_queue/owner_queue.py`, `hooks/session_start_hub.js` (Hook 14),
`[[PR-LIVENESS-CHECK-BEFORE-SHIP-001]]`.

---

### SCS C87 -- Strategic-Gaps-Closed (post-ship blindness -> monitored invariants)

Five deterministic, model-free systems from the 2026-07-10 frontier strategic-gap
audit (`vault/plans/strategic-gap-audit-2026-07-10.md`). Root theme: strong at
construction-time verification, blind at post-ship liveness + value. Each closes one
instance of *ship -> is it alive? -> is it earning?*:

- **D1 Liveness Ledger** (`modules/liveness/`): post-ship blindness closed. Registry +
  daily probe -> LIVE / WIRED-BUT-SILENT / DRIFTED / ORPHANED. First run flagged the
  PM-03 bus WIRED-BUT-SILENT (the class made visible).
- **D4 OWNER_QUEUE** (`modules/owner_queue/`): HR-001 residuals visible at SessionStart,
  auto-cleared by D1. Two layers, one human surface (the durable vault doc).
- **D5 session_active guard + miner repair** (`tools/session_active.py`): idle-fire
  waste cut; gate only session-scoped tasks (reapers/monitors intentionally exempt);
  both miners' pythonw headless-stdout exit-1 fixed (0 FAILING, verified on the real
  scheduled tasks).
- **D2 Federated FD ledger** (`modules/fable_distillation/federated_ledger.py`): premise
  corrected (the ledger was ALREADY per-repo); shipped the missing cross-repo aggregate
  + PR-/HR- lesson propagation (17 rules -> TUA-X + KobiiCraft) + FDI-0 Stop advisory.
- **D3 Recall-ROI** (`modules/recall_roi/`): KB eviction evidence-based. Reads the
  existing JIT usage log (no fork) -> kb_injection_count=1240 live through CO-12 +
  RETIREMENT_CANDIDATES.md.

Gates: `tools/test_strategic_gaps.py` 21/21 hermetic x3. Commits 9b725a2 (D1),
24782cd (D4), a52a102 (D5), 5655cc0 (D2), 56d8814 (D3).

---

## PR-HARVEST-BEFORE-FRONTIER-001 -- never launch a frontier session with an empty question portfolio (2026-07-10)

**TRIGGER:** compiling a SESSION_ZERO (FIOS session_compiler preflight or CLI) for a
frontier session whose declaration has an objective but zero `candidate_questions`.

**REGLA:** an empty portfolio is filled BEFORE launch by the deterministic
question_harvester (`modules/frontier_intelligence/question_harvester.py`): it mines
candidates from state the stack already records -- FD-07 unproven deposits (-> FD-04
downgrade-test questions), OWNER_QUEUE residuals (-> retire-the-class questions),
CO-12 instrument-pending fd metrics (-> instrumentation questions), UKDL traps with no
covering PR/HR id (-> hardening questions), vault honest-residual markers (-> closure
questions). Then the pipeline is harvest -> FD-00 admission rank -> candidate-vs-candidate
dedup (Jaccard, drop LOGGED) -> depends_on deferral -> SESSION_ZERO. Every question
carries `source_ref` + `expected_asset` + a `fingerprint` the session tags its PM-03
findings with, so each FD-07 deposit records the `question_ref` that paid for it
(per-question ROI, read through CO-12 -- no parallel metric). Kill-switch:
`PP_SESSION_NO_HARVEST=1`.

**POR QUE:** Session #1 (SESSION_ZERO_2026-07-10T162015Z) launched with 0 candidates --
the compiler ranked an empty set and the session improvised its questions, so nothing
linked deposits back to intent and the ranking/dedup machinery ran idle. The harvester
never invents: it only converts already-recorded gaps into questions, and the FD-00 gate
remains the sole admission arbiter (a harvested question the floor covers is DECLINE'd
there, correctly -- most harvested questions routing ROUTE_CHEAPER is the system working,
not failing: that work belongs below frontier).

**FAIL-OPEN:** any harvester source error -> that source contributes nothing; harvest()
never raises; preflight without a declaration stays silent (no per-launch bloat,
T-FIOS-FRONTIER-SESSION-DETECT-001 unchanged).

**ORIGEN:** Frontier Session #2 preparation build, 2026-07-10. Production Reality Gate:
the live harvest on claude-power-pack produced 16 candidates from all 5 sources vs
Session #1's 0, with a dedup drop logged and all 7 unproven deposits on the FD-04 agenda
(SESSION_ZERO_2026-07-10T200936Z). Gates: `tools/test_frontier_intelligence_os.py`
31/31 hermetic x3. Cross-ref: `[[PR-FRONTIER-AS-RD-001]]`, `[[PR-FABLE-DELTA-ONLY-001]]`,
`fable_distillation/fd_02_high_leverage_question_compiler.md` (the doctrine this executes).

## T-UFIEL-IS-COMPOSITION-001 -- a "Universal Frontier Intelligence Economics Layer" is FD+FIOS+D2A, already built

**TRIGGER:** a prompt (any phrasing: frontier economics layer, reasoning-capital OS,
cognitive-capital budget, universal model arbitrage, frontier constitution, reasoning
portfolio optimizer) proposing a NEW permanent layer that governs how frontier reasoning
is consumed, distilled, reused, and retired.

**REGLA:** do not build the layer -- it exists as a composition, verified 2026-07-10 for
the third consecutive ask of this shape: escalation ladder / zero-repeat = FD-00 gate
consulting CO-03 route() + CO-05 assets + the deposits floor; reasoning compression +
writeback = FD-07 flywheel (Stop-chain); conversation compiler = session_compiler
(9-component SESSION_ZERO + question_harvester intake); session economics / cognitive
IRR = token_irr + CO-12 fd_metrics (single accountant); duplicate arbitration = D2A
engine + gate; constitution = PR-FABLE-DELTA-ONLY-001 + PR-FRONTIER-AS-RD-001; evolution
/ retirement proposals = evolution_engine (Owner-gated). The honest response to the next
such prompt is a Reality Scan overlap report + thin extensions of the named modules
(EXECUTION MODE), never a parallel layer, registry, accountant, or router.

**POR QUE:** the FIOS (SCS C84: 17 systems -> 3 engines) and D2A (SCS C85: 6 datasets ->
1 doctrine + 1 engine) precedents each burned a full Reality Scan to reach the same
verdict. Sealing the composition as negative knowledge makes the fourth ask resolve in
one lookup instead of a fourth scan (PR-DUPLICATE-TO-ADVANTAGE-001: the duplicate points
at its parents).

**ORIGEN:** Frontier Session #2 / UFIEL ROI analysis, 2026-07-10. Verdict: ~90% covered;
genuine deltas shipped as extensions (question_harvester, portfolio dedup + depends_on +
bilingual axes + FD-04 portability agenda in session_compiler, Deposit.question_ref in
fd_07_flywheel). Cross-ref: `[[PR-HARVEST-BEFORE-FRONTIER-001]]`,
`[[PR-DUPLICATE-TO-ADVANTAGE-001]]`, `[[PR-FRONTIER-AS-RD-001]]`, `FIOS_INDEX.md`,
`D2A_INDEX.md`.

## PR-PROOF-OR-HYPOTHESIS-001 -- a deposit without an FD-04 proof is hypothesis, not capital

**TRIGGER:** declaring a frontier session (or its writeback) complete, or citing a
deposited delta as established knowledge, while its fingerprint has no PROVEN record in
the FD-04 proofs ledger.

**REGLA:** the frontier-session done-gate includes the prover: (1) every deterministic-
checkable deposit gets `fd_04_prover.prove()` with real probes before the session's
value is claimed; (2) mid/small-model deposits get an evidence-backed `attest()` from
the substrate that re-derived them, or stay explicitly hypothesis; (3) session close
runs `--recheck` -- a regressed probe names knowledge that silently rotted and reopens
its deposit. CO-12 `fd_portability_proven` is the only number that may be cited (single
accountant); the estimate field on the deposit row never counts.

**POR QUE:** Session #1 closed with 7/7 deposits carrying `portability_proven: False`
and the ecosystem had NO code path that could ever flip one -- every claimed delta was
structurally condemned to remain a hypothesis while being cited as capital. The prover
turns each proof into a stored, re-runnable probe set, so proving portability, generating
the evaluation, replaying it, and regression-detecting it are one artifact.

**FAIL-OPEN:** consumers of the proofs ledger (`proven_fingerprints`) degrade to the
pre-FD-04 behavior on any error; proving itself is fail-CLOSED (an error is never PROVEN).

**ORIGEN:** Frontier architecture optimization, 2026-07-11. Reality Gate: 3 real
Session-#1 deposits proven with live probes (CO-12 0->3), portability agenda 7->4,
recheck 3/3 green. Cross-ref: `[[T-PRODUCERLESS-FIELD-001]]`,
`[[PR-HARVEST-BEFORE-FRONTIER-001]]`, `modules/fable_distillation/fd_04_prover.py`.

## T-PRODUCERLESS-FIELD-001 -- a field with consumers but no producer is a dead loop

**TRIGGER:** designing or reviewing any schema field / ledger column / state flag that
downstream code branches on (`if x.get("field")`), before shipping.

**REGLA:** grep the PRODUCER before shipping (or trusting) the consumers: some code path
must be able to write every value the consumers branch on. A field initialized to a
constant at write time with N readers and zero writers of the other value is dead
infrastructure -- the branch will never fire, and every metric derived from it is
structurally frozen at its initial value. The fix is never "more consumers": build the
producer or delete the field.

**POR QUE:** `portability_proven` shipped with three consumers (compiler agenda,
harvester skip, CO-12 count) and a writer that hard-codes `False` -- the FD loop's core
yield metric could never move, and "0 proven" was indistinguishable from "prover ran,
nothing proved". Second in-repo instance of the pattern (first: a recovery-path field
whose producer never ran); two instances = trap, not incident.

**FAIL-OPEN:** n/a (design-time rule); at runtime a consumer that cannot resolve the
producer's output degrades to its pre-field behavior, never crashes.

**ORIGEN:** FD-04 Reality Scan, 2026-07-11 -- grep showed `portability_proven` written
always-False at fd_07_flywheel deposit time, read at session_compiler / question_harvester
/ co_12_telemetry, flippable by nothing. Producer shipped as fd_04_prover.
Cross-ref: `[[PR-PROOF-OR-HYPOTHESIS-001]]`.

## PR-ACIS-FALSIFIABILITY-001 -- no claim becomes infrastructure without a falsifier

**TRIGGER:** about to promote any ACIS claim (a candidate law, a theorem record, a deposited
delta) past hypothesis -- i.e. treat it as an operational rule (E4) or higher.

**REGLA:** a claim may occupy only the epistemic level its on-disk evidence licenses, and the
PRODUCER of a claim may never certify its own level. E0-E3 is the most a single model (Fable
included) may author. E4+ requires an artifact authored by a DIFFERENT actor: an Owner-promoted
UKDL rule (E4/E5) or a sealed Hard Rule (E6). Every claim carries an explicit falsifier -- a
concrete, observable refutation condition the pipeline can actually measure; a claim with no
falsifier is not a weak claim, it is not a theorem, and is dropped at authoring time. Evidence
must be independent of the model that proposed the claim (a probe re-run, or a different
substrate re-deriving it), and a claim with no production-impact chain may be kept as research
but never declared E4+.

**POR QUE:** the epistemic ladder E0-E7 names the sealed promotion chain (deposit E2 -> FD-04
prove/attest E3 -> Owner UKDL rule E4 -> Hard Rule E6). Without the falsifier gate, a confident
deposit reads as a law; without the different-actor rule, a model ratifies its own output and
calls it validation (the CWOPS degenerate-feedback trap at the level of epistemics).

**FAIL-OPEN:** `epistemic_level()` fails CLOSED on promotion (an unreadable artifact degrades a
claim's level DOWNWARD, never up -- an error must never inflate a claim) and fail-open on reads
(garbage fingerprint -> E0). Enforced by `V-NO-AUTOPROMOTION` + `V-THEOREM-SCHEMA-COMPLETE`.

**ORIGEN:** ACIS Generation Zero, 2026-07-11. Live proof: 8 deposits resolve to 5xE3 + 3xE2,
zero E4+ (no sealed rule cites a deposit ref) -- the No-Autopromotion Invariant working, not a
bug. Extends `[[PR-PROOF-OR-HYPOTHESIS-001]]` (a deposit without an FD-04 proof is hypothesis);
this rule generalizes it to every level of the ladder. Cross-ref: `[[T-ACIS-MODEL-CONSENSUS-001]]`,
`[[T-ACIS-GOODHART-001]]`, `ACIS_INDEX.md`.

## T-ACIS-MODEL-CONSENSUS-001 -- same-model consensus is not independent evidence

**TRIGGER:** about to treat agreement among agents of the SAME model (a Fable critic ratifying a
Fable claim; a swarm of one model's instances voting) as validation that promotes a claim past E3.

**REGLA:** consensus among instances of one model is not independent evidence -- they share the
weights that produced the claim, so their agreement is correlated, not confirmatory. A claim's
E3->E4+ promotion requires a DIFFERENT actor: the Owner (who authors the rule) or a different
model that re-derives the capability, and even a different model is only weak independence until
production evidence confirms it. A destruction attempt an author runs on its own claim strengthens
the hypothesis but never validates it.

**POR QUE:** ACIS-01's candidate laws were authored AND stress-tested by Fable; if that self-test
counted as validation, every ACIS law would self-promote to operational on the strength of its own
author's approval -- the exact failure the No-Autopromotion Invariant exists to stop.

**FAIL-OPEN:** design-time epistemics rule; the mechanical half is the `epistemic_level()` E3 cap,
which never reads a model's self-assessment as a referent -- only on-disk artifacts by other actors.

**ORIGEN:** ACIS Generation Zero, 2026-07-11. This rule is itself listed in the Generation One
agenda as a claim to be attacked (is a different model genuinely independent, or is model diversity
illusory?) -- the rule ACIS proposes threatens itself, which is the discipline working. Cross-ref:
`[[PR-ACIS-FALSIFIABILITY-001]]`.

## T-ACIS-GOODHART-001 -- every ACIS metric is a proxy; the master check is the CO-12 ratio

**TRIGGER:** about to optimize, report, or gate on any ACIS/PCCR metric (Cognitive IRR, Frontier
Dependence Index, Portability Score, Compression Loss, Reuse Horizon, Production Impact Confidence,
Infrastructure Delta, Theory Maturity).

**REGLA:** each ACIS metric is a proxy anchored to an EXISTING accountant (token_irr, CO-12
dependence metric, fd_portability_proven, FD-04 DEGRADED, recall_roi, D1 liveness, FD-07 deposit
precision, the derived E-level counts) -- never a new number. The master ground-truth check remains
the CO-12 cognitive-compression ratio; if it does not move, the proxies are theater regardless of
their values. Do NOT re-derive an anti-Goodhart mechanism for ACIS: the doctrine is already sealed
(FD-00 III.1 metric-decoupling + deposit-count Goodharting; FD-07 names the CO-12 ratio the master
signal). This trap is a genealogy pointer, not a new system -- re-deriving it would be the exact
duplication D2A forbids (`DO_NOT_BUILD`).

**POR QUE:** Theory Maturity climbing (deposits moving E2->E3) looks like progress, but a stack can
lift every claim to E3 with cheap probes while the dependence curve stays flat -- the volume-theater
failure FD already catalogs, now reachable through an ACIS proxy.

**FAIL-OPEN:** advisory epistemics rule; the derived metrics carry no gate that can fire on the proxy
alone -- the CO-12 ratio remains the single accountant.

**ORIGEN:** ACIS Generation Zero, 2026-07-11. PCCR-to-existing-accountant map in `ACIS_INDEX.md`;
anti-Goodhart genealogy in `[[fd_00_fable_advantage_doctrine_and_session_protocol]]` III.1.
Cross-ref: `[[PR-ACIS-FALSIFIABILITY-001]]`.

### UKDL TRAP T-AKOS-KNOWLEDGE-DEAD-001 -- a store that only GENERATES a brief, with no active consumption path, never composes

**REGLA:** a knowledge store needs four steps to compose: generate + inject + harvest + measure.
With only generate, the artifact sits on disk unread. AKOS generated 89 domain-tagged units into
`<repo>/knowledge/AKOS_KNOWLEDGE_BRIEF.md` across ~15 repos, but no hook, module, or command read any
of them into an active session -- the gap was CONSUMPTION, not generation. Fix (2026-07-11): a shared
parser (`modules/akos_knowledge`) feeding two live consumers -- JIT session injection
(`_akos_knowledge_inject`, domain-matched, throttled 1/session, CO-12-measured) and the FIOS
question harvester (`_from_akos`). Consume-existing-only; brief-exists AND repo-mapped policy.

**POR QUE:** an unconsumed artifact reads as "done" (the file exists, the units were matched) while
delivering zero value to any session -- the write-without-read pattern (`[[feedback_write_without_read_incomplete_system.md]]`)
applied to a knowledge store rather than a recovery path.

**FAIL-OPEN:** absolute at every seam -- unmapped repo, missing brief, or parse error yields silence,
never a blocked prompt or a raised harvest.

**ORIGEN:** AKOS Knowledge Brief integration, 2026-07-11. Two plan premises corrected during PASO -1:
the `/knowledge` command's engine path was stale (TUAX_UGC_SYSTEM gone; real engine under the AKOS/
repo), and briefs already existed widely on disk. Cross-ref: `[[feedback_write_without_read_incomplete_system.md]]`,
`[[feedback_orphan_module_wiring.md]]`.

---

## DRK Live Wiring + Proactive Mode (sealed 2026-07-11)

### UKDL TRAP T-DRK-PROACTIVE-NOISE-001 -- a proactive scanner that emits too much is worse than absent

**REGLA:** a scanner that produces more suggestions than the Owner will read becomes noise and is
ignored -- at which point it is WORSE than having none, because the stack believes that surface is
covered. Three rules hold the line, enforced in code, not intention: (1) every suggestion cites a
REAL path or ledger row (`ProactiveSuggestion.is_publishable()` filters at the egress, so a sloppy
detector cannot leak an ungrounded finding); (2) `high` urgency is EARNED -- a kernel-computed blast
magnitude at or above the threshold, or a DRIFTED gate the stack believes is enforcing and which
provably is not deployed -- never a heuristic; (3) a volume cap is REPORTED as a row, never applied
silently. A detector that cannot cite evidence emits nothing.

**POR QUE:** the value of a proactive system is entirely in its precision. One ignorable false
positive per day trains the Owner to skip the report, and the true positive that follows dies with
it. Silence is a valid scan; noise is not.

**FAIL-OPEN:** per-detector. One that raises is skipped and the scan continues; the scanner never
blocks a workflow and never gates a commit.

**ORIGEN:** DRK proactive scanner, 2026-07-11. A first implementation ran the D1-liveness and
D3-recall-ROI detectors against ANY target repo -- but those read PP-global ledgers, so scanning a
foreign repo reported the pack's own silent systems as findings ABOUT that repo (an empty directory
produced 7 suggestions). Evidence that does not belong to the thing being scanned is fabrication,
not detection. Fixed by scoping PP-global detectors to the pack itself; gated by
`V-DRK-SCANNER-RUNS` (empty repo -> 0) and `V-DRK-SCANNER-EVIDENCE`.

### UKDL TRAP T-DRK-PRECEDENT-LENGTH-BIAS-001 -- a length-sensitive advisory provider mapped to a hard verdict rejects every big decision

**REGLA:** before mapping a provider's output onto a hard verdict, measure the DISTRIBUTION of that
output over real inputs. `arch_check`'s relevance score rises monotonically with input length
(body-token matches score per-token up to a cap, entity hits score higher), and 86% of its index
(459/531 sources) is veto-class. So a naive adapter that (a) fed it a concatenated
statement+problem+rationale blob and (b) read `on_veto` as "any veto-class source in the top 3"
converted "this is a big decision" into "this collides with a Hard Rule" -- and REJECTED it. The same
decision scored 1.50 as a 28-word statement and 4.05 as a 78-word blob, climbing toward the 4.5
COLLISION floor purely by growing. Feed a provider the input shape its thresholds were calibrated on
(here: the STATEMENT, a prompt-sized intent), and mirror its OWN escalation condition rather than
inventing a looser one.

**POR QUE:** this is the always-reject bias of `[[T-DECISION-AUTHORITY-CAPTURE-001]]` arriving through
the back door -- not from a doctrine that likes saying no, but from an adapter whose signal correlates
with verbosity. A decision authority that rejects every substantial decision is not strict; it is
broken, and it will be routed around within a week. An ADVISORY provider ("this is advisory, the agent
decides what to weigh") must not be able to unilaterally veto.

**FAIL-OPEN:** an unavailable provider contributes NO input (None), never a CLEAR. Absence of a
precedent signal is not evidence of no precedent.

**ORIGEN:** DRK live wiring, 2026-07-11. Found by submitting the wiring decision ITSELF to the kernel:
it returned REJECT on `precedent-collision-on-veto`. The collision was an artifact of text length, not
a precedent. After the fix the same decision returns APPROVE-WITH-CONDITIONS with the precedent cited
as a WARNING -- surfaced, not vetoing. Regression gate: `V-DRK-NO-LENGTH-BIAS`. Cross-ref:
`[[PR-DECISION-AUTHORITY-LIMITS-001]]` (block-narrow, recommend-wide), `[[feedback_plan_code_is_hypothesis_verify_source.md]]`.

---

## Decision Review Kernel (DRK) — Decision Axis (sealed 2026-07-11)

The executable Decision axis of the PP: authenticate a decision (record, reversibility, blast radius,
precedent, evidence-burden) before action, and judge its reasoning — not just its outcome — after.
DEEPENs the shallow SDD-OS Parte V (Decision OS) enumeration into an operating discipline and ships
the runtime Parte V never had. Doctrine: `vault/knowledge_base/decision_review/` (DRK-00…07) +
`vault/knowledge_base/sdd_os/sdd_os_06_*` (accountability). Code: `modules/decision_review/`. Gate:
`tools/test_decision_review.py` (11/11 hermetic ×3). Sealed via Reality Scan → STOP #1 → Owner
override to fuller corpus (`vault/plans/decision-intelligence-2026-07-11.md`).

### PROCESS RULE PR-DECISION-AUTHORITY-LIMITS-001 — the authority is block-narrow, recommend-wide

**Level:** Process Rule (governance, constitutional).
**Sealed:** 2026-07-11.

**Rule:** The PP's decision authority has a limited scope. It **may block** — refuse autonomous
action, holding a decision for the Owner — **only when the impact is irreversible (Tipo C) AND the
evidence is insufficient (below ACIS E3).** In every other case it **only recommends**. The Owner may
always annul a verdict with a **registered override** (appended to the Decision Record, never a silent
reversal; the disagreement is kept and later judged on reasoning). The discipline evaluates its own
errors with the same rigor it applies to other systems — its overrides and high-confidence errors
enter the same calibration population (SDD-OS Parte VI) it uses to judge others.

**Mechanism:** `modules/decision_review/decision_kernel.py` fires the block-gate iff
`tier == L4 ∧ reversibility == C ∧ max_evidence_level < E3`; asserted by `V-DRK-BLOCK-GATE`
(blocks under the twin-condition, never otherwise). Constitution: `drk_07_governance_evolution_authority.md`.

**Cross-ref:** `drk_00_foundations_canonical_objects.md` (verdict ontology, review-tier routing),
`drk_07_governance_evolution_authority.md` (override protocol, anti-capture), `sdd_os_06_*`
(self-error calibration), `modules/one_shot/escalation.py` + `modules/owner_queue` (escalation transport).

### UKDL TRAP T-DECISION-AUTHORITY-CAPTURE-001 — the three biases of a decision authority

**Level:** UKDL Trap (governance, self-capture).
**Sealed:** 2026-07-11.

**Trap:** A decision authority **that never rejects anything is theater**; **one that always rejects
is a block**; **one that always recommends platform/consolidation has a bias toward complexity.**
Each is a distinct failure and each is invisible to the authority that has it — the never-rejecter
feels helpful, the always-rejecter feels safe, the always-platformer feels principled.

**Recognizer:** the three biases are **calibration drifts in the population of Decision Records**, not
opinions: approval rate ≈ 1.0 (never-reject), reject+block rate ≥ 0.5 (always-reject), consolidate
rate ≥ 0.5 with keep-local ≈ 0 (always-platform). Detected by `modules/decision_review/accountability.py::calibrate`
above a population threshold (telemetry-before-claims; below it, `insufficient_data`), and each has a
dedicated scenario in `V-DRK-3-BIAS`.

**Rule:** Calibrating against all three biases is part of the discipline's **done criteria** — a
decision authority is not complete until it can be shown *not* to be any of the three. A healthy
verdict distribution matches the population of decisions actually seen, never a target distribution.

**Cross-ref:** `drk_07_governance_evolution_authority.md` §II.4 (the three biases + correctives),
`sdd_os_06_decision_accountability_attribution.md` (calibration), `tools/test_decision_review.py`
(`V-DRK-3-BIAS`). Sister of `PR-DECISION-AUTHORITY-LIMITS-001`.
