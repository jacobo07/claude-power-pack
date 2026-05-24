# Deployment Skill — Authoritative Spec

Status: **Sealed 2026-05-24**
Closes: PP Quality Quadrangle (auto-testing + arch-check + code-review + **deploy**).

---

## 1. Purpose

Verified delivery to production. Not a pipeline generator. The skill **detects** the deploy modality of the target project, **invokes** the canonical pipeline if one exists, and **verifies** the deploy with a real healthcheck. A deploy without a verified healthcheck is, by contract, **not** a deploy.

The skill closes the fourth axis of the PP Quality Quadrangle. Auto-testing answers "does the code do what it should". Arch-check answers "is the decision consistent with the vault". Code-review answers "is the code well-written, secure, maintainable". Deploy answers "did the code actually reach production AND is it serving traffic". Without this axis, all prior signals stop at the merge.

## 2. Reality Contract

- A deploy is **not** considered complete until a real healthcheck against the live target returns OK.
- The skill **never** writes a `vault/deploys/<ts>_<project>_<env>.md` report before the healthcheck finishes. No report = the deploy did not happen.
- Slop tokens, scaffold markers, and bracket templates with literal angle-marks are forbidden in delivered files. Detected and refactored inline.
- CEILING is the **correct** behaviour when preconditions are missing. CEILING is not failure — it is honest stop with a documented exit code (4) and an actionable message.

## 3. Architecture

```
modules/deployment/
  deploy.py              # entry point + dispatcher
  detectors.py           # detect_deploy_target() — 4 modes
  runners/
    __init__.py
    gh_workflow.py       # mode: gh-workflow
    git_push.py          # mode: git-push-to-deploy
    scp_systemd.py       # mode: manual-scp
  healthcheck.py         # tcp / http / curl-grep helpers
  test_v_block.py        # 12 V-tests
commands/deploy.md       # /deploy slash command
vault/deploy/            # per-project configs (JSON, no secrets)
vault/deploys/           # per-run reports (closed loop)
```

The dispatcher (`deploy.py`) is the single public entry. It accepts STDIN JSON, runs the detector, hands off to the correct runner, executes the healthcheck, and emits a JSON verdict to stdout. Runners are pure I/O modules — they do not decide the verdict; they execute.

## 4. The 4 deploy modes

| Mode | Signal | Action | Real-world case |
|---|---|---|---|
| `gh-workflow` | `.github/workflows/deploy*.yml` exists with workflow_dispatch or push trigger to main | Invokes `gh workflow run <yml> --ref main` then `gh run watch --exit-status`; cites §77 if the workflow path matches `deploy-vps.yml` | InfinityOps |
| `git-push-to-deploy` | Either `deploy/post-receive` is present in the working tree OR a git remote is configured as `<user>@<host>:/path/repo.git` (non-origin) | Executes `git push <remote> main`, captures stderr (server post-receive output), reports HEAD short SHA | TUA-X |
| `manual-scp` | A build manifest (`pom.xml` / `build.gradle` / `mix.exs` / `package.json`) is present AND `vault/deploy/<project>.json` exists with `mode: scp-systemd` | Reads config, runs build, scps artefacts to the host (via SSH alias), invokes the post-deploy command (typically `sudo systemctl restart <service>`) | KobiiCraft |
| `none` | No signal of any of the above | CEILING (exit 4); documented stop; does **not** generate a template, does **not** guess | New / unconfigured projects |

The detector evaluates modes in the order listed and returns the **first** match. This deterministic ordering means InfinityOps (which has all three signals — workflows + post-receive history + Maven submodules) deterministically picks gh-workflow, honoring §77.

## 5. STDIN / STDOUT contract

Input — STDIN JSON:

```json
{
  "project_root": "C:/path/to/project",
  "env": "prod|staging",
  "dry_run": true|false,
  "config_override": "vault/deploy/<name>.json"   // optional, default = detector picks
}
```

Output — STDOUT JSON:

```json
{
  "verdict": "pass|fail|ceiling|deploy-warn|skip|dry-run",
  "exit_code": 0|2|3|4,
  "mode": "gh-workflow|git-push-to-deploy|manual-scp|none",
  "head_sha": "abcd1234",
  "duration_ms": 12345,
  "healthcheck": { "kind": "...", "ok": true|false, "attempts": 3, "evidence": "..." },
  "receipt_path": "vault/deploys/2026-05-24-HHMMSS_<project>_<env>.md",
  "summary": "human-readable one-liner",
  "doctrine_cite": "§77 Deploy Sovereignty (when applicable)"
}
```

## 6. Verdict shapes and exit codes

| Verdict | Exit | When |
|---|---|---|
| `pass` | 0 | Deploy executed + healthcheck OK |
| `dry-run` | 0 | `--dry-run` flag; nothing mutates; prints the plan |
| `skip` | 0 | Healthcheck target unreachable from local network (e.g., V-KOBIICRAFT without gex44) |
| `fail` | 2 | Build failed, schema invalid, push rejected, or other deterministic deploy-level failure |
| `deploy-warn` | 3 | Deploy executed but healthcheck failed. Report **states this explicitly**. Does **not** mask as success. |
| `ceiling` | 4 | SSH key missing, mode=none, config missing, or other precondition gap. Honest stop. |

Exit codes are stable. The slash-command (`/deploy`) reads the JSON verdict, not the exit code, for routing — but the exit code is the contract for shell consumers.

## 7. Healthcheck kinds

Defined in `vault/deploy/<project>.json` under the `healthcheck` key. Three kinds:

```json
{
  "kind": "tcp",
  "target": "5.9.23.174",
  "port": 25565,
  "retries": 6,
  "delay_sec": 10
}
```

```json
{
  "kind": "http",
  "url": "https://example.com/health",
  "retries": 6,
  "delay_sec": 10,
  "expect_status": 200
}
```

```json
{
  "kind": "curl-grep",
  "url": "https://infinityops.ai/",
  "grep_pattern": "br.jula",
  "retries": 24,
  "delay_sec": 15
}
```

`curl-grep` is the §77 style — verifies the production page literally contains an expected string. HTTP 200 is insufficient because a stale build still returns 200. Content verification is the real receipt.

## 8. Config schema (vault/deploy/<project>.json)

```json
{
  "project": "kobiicraft|tua-x|infinityops|...",
  "mode": "gh-workflow|git-push-to-deploy|scp-systemd",
  "ssh_alias": "gex44|vps204|...",
  "ssh_key": "~/.ssh/<key-name>",
  "instance": "<systemd-instance-name>",
  "build_cmd": "mvn -DskipTests package",
  "artefact_glob": "KobiCraftServer/plugins/*/target/*.jar",
  "remote_path": "/srv/kobiicraft/<instance>/plugins/",
  "post_deploy_cmd": "sudo systemctl restart kobiicraft@<instance>",
  "workflow_file": ".github/workflows/deploy-vps.yml",
  "remote": "vps204:/repo.git",
  "healthcheck": { ... }
}
```

Forbidden keys (validator REJECTS with exit 2 before any runner executes):

- `password`
- `secret`
- `token`
- `api_key`
- Any key whose name contains `password` / `secret` / `token` / `api_key` (case-insensitive)

The skill **never** reads or writes credentials. Authentication is delegated entirely to `~/.ssh/config` (host aliases) and existing key files. The skill resolves `ssh_key` via `os.path.expanduser` and verifies existence; if missing → CEILING.

## 9. §77 Deploy Sovereignty

InfinityOps owns the canonical CD pattern: self-hosted GitHub Actions runner on the VPS, forced-command SSH key pinned to a server-side deploy script, dedicated key per CD pipeline, concurrency group, path-filtered triggers, and a 24×15s post-deploy content healthcheck against the live URL.

This skill **invokes** that pipeline. It does not reimplement it. When `gh_workflow.py` detects `.github/workflows/deploy-vps.yml`, it prints:

> §77 Deploy Sovereignty — InfinityOps uses the canonical CD pipeline at `.github/workflows/deploy-vps.yml`. This skill INVOKES; it does not replace.

The doctrine cite is also included in the JSON verdict under `doctrine_cite`.

## 10. NO auto-push to origin

Hard invariant. **No runner** in this skill ever executes `git push origin <branch>` or any equivalent push to the canonical GitHub origin. The runners are allowed to:

- Run `git push <remote> main` only when `<remote>` is a **non-origin** deploy remote (e.g. `vps204:/repo.git`)
- Execute `gh workflow run` (this is a GitHub API call, not a push)
- Execute `scp` and `ssh` against a configured host alias

V-NO-AUTO-PUSH (test) greps the runner sources for any `git push origin` substring; expected hit count = 0.

The Owner pushes to origin separately. Deploy is downstream of origin/main, not a side-effect of it.

## 11. Recursion guard

`CLAUDEPP_DEPLOY_RUNNING=1` is set **only** when the deploy dispatcher spawns sub-shell commands (level-2+). It is **never** set on the level-1 entry from the slash command or hook piggyback. This was the L2 lesson sealed in the code-review skill cycle — setting the guard at level-1 short-circuits the very call that should detect the deploy.

## 12. Mirror-Sync-Direction

Apex section is written to PP source first:

```
claude-power-pack/knowledge_vault/core/apex-completion-standard.md
```

Then byte-mirrored to the live loose copy via Python `read_bytes` / `write_bytes` (NEVER `cat >>`, NEVER bash heredoc — both have BOM-clobber failure modes):

```
~/.claude/knowledge_vault/core/apex-completion-standard.md
```

SHA-256 must match. `verify_global_mirrors.py` validates this on every verify_spp run with `SEALING_REF = main`.

Direction is **one-way only**: PP → loose. Never loose → PP.

## 13. Opt-out env vars

| Env var | Effect |
|---|---|
| `CLAUDEPP_DEPLOY_DISABLED=1` | Disables the deploy skill entirely (skips the dispatcher with verdict `skip` and exit 0). Useful in CI environments where deploys must be triggered exclusively from the canonical pipeline, not piggybacked. |

## 14. Closed loop

Every non-skip, non-dry-run run appends a report to `vault/deploys/<ts>_<project>_<env>.md`. The report has 4 sections:

1. **Mode detected** — which of the 4 modes the detector picked, plus the signal evidence.
2. **Build summary** — command run, exit code, artefact count or build output last 10 lines.
3. **Receipt** — deploy command output, last 15 lines. For gh-workflow: the run URL. For git-push: the post-receive lines. For scp-systemd: the scp progress + systemctl status output.
4. **Healthcheck** — kind, target, attempts, success/failure, evidence.

Future runs surface prior reports in the dispatcher output under `previous_deploys` so the skill carries memory between sessions. Mechanical — no LLM.

## 15. DONE gate

A deploy axis change is considered DONE only when **all** of the following are green:

- [ ] All 12 V-tests in `test_v_block.py` PASS with documented evidence.
- [ ] `verify_spp.py` exits 0 (7/7 STRICT) — pre-existing FAILs documented in session_lessons.md.
- [ ] `verify_full_install.py` exits 0.
- [ ] Apex section sealed; PP source and live mirror sha256 match.
- [ ] UKDL rows appended (UKDL-DP-01..05).
- [ ] session_lessons.md rows appended (L1..LN with empirical findings).
- [ ] `git push origin main` succeeded with `REMOTE_DELTA=0` both directions.
- [ ] `vault/deploys/<ts>_self-test_dryrun.md` exists (V-DEEP receipt).

A deploy axis change is NOT done when:

- A V-test is skipped without justification.
- The Apex sha256 does not match.
- `verify_spp` has a NEW FAIL caused by this change (pre-existing is documented and overridable; new is a stop).
- The dispatcher silently masked a healthcheck failure as success.
