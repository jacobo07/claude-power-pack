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
