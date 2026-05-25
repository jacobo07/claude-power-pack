---
description: PP Rollback Axis -- restore a verified snapshot when a deploy goes wrong. Reality contract: a restore without a passing healthcheck is not a recovery.
argument-hint: "[--project NAME] [--dry-run] [--target NAME] [--list] [--rescue] [--include-code-rollback]"
---

# /rollback -- PP Rollback Axis

Third executable node of the deploy lifecycle. Backup (safe) -> Deploy
(deliver) -> Rollback (recover). Makes every deploy recoverable. Without
this node, a failed deploy is in practice irreversible: the Owner faces
~15 minutes of manual restoration under outage pressure.

Spec: `vault/specs/rollback-skill.md`.

## Surface

```
/rollback [--project NAME] [--dry-run] [--target NAME] [--list] [--rescue] [--include-code-rollback]
```

Flags:

- `--project NAME` -- override project name (default: cwd basename)
- `--dry-run` -- source-select + planner only; no mutation
- `--target NAME` -- specific verified snapshot file name (e.g. `2026-05-25-151305.tar.gz`); default = latest verified
- `--list` -- print the top-5 verified snapshots for the project and exit
- `--rescue` -- take a pre-rollback snapshot of the CURRENT state into `vault/rescues/<project>/` BEFORE restoring (opt-in safety net)
- `--include-code-rollback` -- only meaningful for `infinityops`: after data restore, re-triggers the canonical `gh workflow run deploy-vps.yml --ref <prev_sha>` per sec 77

## Protocol (8 steps)

When the Owner invokes `/rollback ...`, follow this protocol exactly:

1. **Load config.** Invoke `python modules/rollback/rollback.py` with STDIN JSON `{"project_root": <cwd>, "project": <name>, "dry_run": <bool>, "target_snapshot": <name|null>, "rescue_current": <bool>, "include_code_rollback": <bool>, "config_override": <path?>}`. The dispatcher resolves the config at `vault/rollback/<project>.json`.

2. **Schema validate.** Reject any key whose name falls into the credential-class token category (case-insensitive). Reject forbidden modes (n8n, zapier, make.com, pipedream). Exit 2 BEFORE any runner action.

3. **Source select.** `source_selector.select_source` reads `backups/<project>/manifest.json` (the artefact written by the Backup Axis's retention pass). A snapshot on disk without a manifest entry is treated as if it does not exist -- the Rollback Axis cannot trust a snapshot that the Backup Axis itself did not certify. CEILING exit 4 if the manifest is absent, empty, or the requested target is not in it.

4. **Rescue snapshot (opt-in).** If `--rescue`, the dispatcher reads `vault/backup/<project>.json` and re-invokes the matching backup runner against `vault/rescues/<project>/<ts>.tar.gz`. If the rescue cannot complete -> CEILING (refuse to apply restore without a recoverable current state).

5. **Dispatch inverse runner.**
   - `rsync-dir` -> `runners/restore_rsync_dir.py` (local tar.gz piped into `ssh + tar -xzf -` at remote root)
   - `pg-dump` -> `runners/restore_pg_dump.py` (local .dump piped into `ssh + docker exec -i + pg_restore -c`)
   - `docker-volume-tar` -> `runners/restore_docker_volume.py` (local tar.gz piped into `ssh + docker run + tar -xzf -` against the named volume)

6. **Healthcheck (mandatory).** Reuses `modules/deployment/healthcheck.py` (`check_tcp` / `check_http` / `check_curl_grep` via `run_healthcheck`). A restore that succeeded technically but whose healthcheck FAILED yields `rollback-warn` (exit 3) -- the bytes are in a known state corresponding to a previously verified backup, but the live process did not come back. The Owner investigates.

7. **Code rollback (sec 77, infinityops only).** If `--include-code-rollback` AND `project=infinityops`: extract `prev_sha` from the latest `vault/deploys/*_infinityops.md` HEAD line, print the sec 77 citation, invoke `gh workflow run deploy-vps.yml --ref <prev_sha>`. This INVOKES the canonical CD pipeline; it does not reimplement it. The cite is non-negotiable.

8. **Write receipt.** Only AFTER the healthcheck verdict is recorded, the dispatcher writes `vault/rollbacks/<UTC-ts>_<project>.md` with 6 sections (Source / Rescue / Runner / Receipt / Healthcheck / Code-rollback).

## Exit code table

| Code | Verdict | Meaning |
|---|---|---|
| 0 | pass | restore + healthcheck OK |
| 0 | dry-run | no mutation; planner output only |
| 0 | skip | `CLAUDEPP_ROLLBACK_DISABLED=1` |
| 2 | fail | schema invalid / runner crash / restore non-zero |
| 3 | rollback-warn | restore OK but healthcheck FAILED; receipt states this; rescue (if requested) recoverable |
| 4 | ceiling | SSH key missing / manifest absent or empty / target not in manifest / config missing |

## Hard invariants

- A rollback without a passing healthcheck is NOT a rollback. The receipt is the proof; absence of receipt = absence of recovery.
- A snapshot not in the manifest is treated as absent. Period.
- NO credentials in `vault/rollback/*.json`. Schema validator rejects credential-class key tokens before any runner action.
- NO automatic rollback. `/deploy` only suggests `/rollback`; it never invokes it. V-NO-AUTO grep-asserts this in deploy.py.
- `CLAUDEPP_ROLLBACK_RUNNING=1` recursion guard is level-2+ only (lesson L2 sealed in code-review + deploy + backup cycles).
- sec 77 Deploy Sovereignty extends to rollback: InfinityOps code rollback INVOKES the canonical CD pipeline on a previous ref; it never reimplements `deploy_from_git.sh`.

## Examples

```bash
# List verified snapshots for kobiicraft
/rollback --project kobiicraft --list

# Dry-run rollback to the latest verified snapshot
/rollback --project kobiicraft --dry-run

# Real rollback with rescue safety net
/rollback --project kobiicraft --rescue

# Roll back to a specific snapshot
/rollback --project tua-x --target 2026-05-25-093000.dump

# Full recovery for InfinityOps: data restore + canonical CD re-trigger
/rollback --project infinityops --include-code-rollback --rescue
```

## When `/deploy` fails

The Deploy Axis dispatcher prints, on `verdict in {fail, deploy-warn}`:

```
To roll back: /rollback --project <X>   (NOT auto-invoked; Owner decides)
```

Owner runs the suggested command. There is no TTY prompt; there is no auto-fire. The Owner always decides on destructive operations.

## Cross-references

- Spec: `vault/specs/rollback-skill.md`
- Plan: `vault/plans/rollback-skill-2026-05-25.md`
- Apex section: `knowledge_vault/core/apex-completion-standard.md` "Rollback Axis (sealed 2026-05-25)"
- UKDL: `vault/knowledge_base/ukdl-universal.md` UKDL-RB-01..05
- Sister skills: `commands/deploy.md`, `commands/backup.md`
