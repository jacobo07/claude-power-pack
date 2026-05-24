---
description: PP Deploy Skill -- detect mode, invoke canonical pipeline, verify with healthcheck. Reality contract: a deploy without a verified healthcheck is not a deploy.
argument-hint: "[--project NAME] [--env prod|staging] [--dry-run] [--config PATH]"
---

# /deploy -- PP Deploy Axis

Fourth side of the PP Quality Quadrangle (auto-testing + arch-check +
code-review + deploy). Closes the loop: code reaches production only
when a real healthcheck against the live target confirms it is
serving traffic. See `vault/specs/deployment-skill.md` for the
authoritative spec.

## Surface

```
/deploy [--project NAME] [--env prod|staging] [--dry-run] [--config PATH]
```

Flags:

- `--project NAME` -- override project name (default: cwd basename)
- `--env prod|staging` -- environment label for the receipt (default: `prod`)
- `--dry-run` -- run detector + runner planner only; no mutation; no receipt
- `--config PATH` -- override `vault/deploy/<project>.json` location

## Protocol (8 steps)

When the Owner invokes `/deploy ...`, follow this protocol exactly:

1. **Detect.** Run `python modules/deployment/deploy.py` with STDIN
   JSON `{"project_root": <cwd>, "project": <name>, "env": <env>, "dry_run": <bool>}`.
   The dispatcher resolves the deploy mode via `detect_deploy_target`.

2. **Load config.** The dispatcher reads `vault/deploy/<project>.json`
   (or `--config` override). If the file is missing AND mode requires
   it (e.g. healthcheck for non-dry-run), verdict = `fail`.

3. **Validate schema.** For `manual-scp` mode, `validate_config` rejects
   forbidden-key categories (password / secret / token / api_key) AND
   forbidden modes (n8n, zapier, make.com, pipedream). Exit 2 BEFORE any
   runner action.

4. **Dispatch runner.** Based on mode:
   - `gh-workflow` -> `runners/gh_workflow.py` invokes `gh workflow run`
     then `gh run watch --exit-status`. Cites §77 when workflow path
     matches `deploy-vps.yml`.
   - `git-push-to-deploy` -> `runners/git_push.py` pushes to a NON-origin
     remote. Refuses to touch `origin`, `upstream`, `github`, or any URL
     containing `github.com` / `gitlab.com` / `bitbucket.org`.
   - `manual-scp` -> `runners/scp_systemd.py` builds, scps artefacts,
     ssh-restarts the systemd service. CEILING if SSH key missing.

5. **Healthcheck.** Only if runner verdict is `pass`, the dispatcher
   runs `healthcheck.py` with the config's `healthcheck` block. Three
   kinds: `tcp` (socket), `http` (curl), `curl-grep` (§77 content
   verification). All three retry per spec.

6. **Write receipt.** Only AFTER healthcheck, the dispatcher writes
   `vault/deploys/<UTC-ts>_<project>_<env>.md` with 4 sections (Mode /
   Build / Receipt / Healthcheck). Receipt path is included in the
   verdict JSON.

7. **Echo verdict.** Show the Owner the verdict (one of: `pass`,
   `dry-run`, `skip`, `ceiling`, `deploy-warn`, `fail`), the mode,
   duration, healthcheck result, and the receipt path. If
   `doctrine_cite` is non-empty, echo it verbatim.

8. **Cite doctrine.** If mode is `gh-workflow` AND the workflow file is
   `deploy-vps.yml`, output the §77 Deploy Sovereignty citation
   verbatim. The skill INVOKES the canonical pipeline; it does not
   replace it. This citation is mandatory -- it tells the Owner the
   skill respected the existing standard.

## Exit code table

| Code | Verdict | Meaning |
|---|---|---|
| 0 | pass | deploy + healthcheck OK |
| 0 | dry-run | dry-run mode; no mutation |
| 0 | skip | `CLAUDEPP_DEPLOY_DISABLED=1` |
| 2 | fail | build failed / schema invalid / push rejected |
| 3 | deploy-warn | deploy executed, healthcheck FAILED -- target may not be live |
| 4 | ceiling | SSH key missing / mode=none / config missing |

## Hard invariants

- A deploy without a verified healthcheck is NOT a deploy. The receipt
  is the proof; absence of receipt = absence of deploy.
- NO runner pushes to the canonical origin remote. The Owner pushes
  separately.
- NO credentials in `vault/deploy/*.json`. Authentication is
  delegated to `~/.ssh/config` and existing key files.
- `CLAUDEPP_DEPLOY_RUNNING=1` recursion guard is for level-2+ chains
  only. Never set at level-1 (lesson L2 sealed in code-review).
- §77 Deploy Sovereignty citation is mandatory when the runner is
  `gh_workflow.py` and the workflow file matches `deploy-vps.yml`.

## Examples

```bash
# Dry-run the infinityops deploy (mode: gh-workflow)
/deploy --project infinityops --dry-run

# Real deploy to KobiiCraft (mode: manual-scp)
/deploy --project kobiicraft --env prod

# Inspect previous deploys for a project
ls vault/deploys/ | grep infinityops
```

## Cross-references

- Spec: `vault/specs/deployment-skill.md`
- Plan: `vault/plans/deployment-skill-2026-05-24.md`
- Apex section: `knowledge_vault/core/apex-completion-standard.md`
  "Deploy Axis (sealed 2026-05-24)"
- UKDL: `vault/knowledge_base/ukdl-universal.md` UKDL-DP-01..05
- Sister skills: `commands/code-review.md`, `commands/arch-decision.md`,
  the auto-testing gate at `hooks/auto-test-gate.js`.
