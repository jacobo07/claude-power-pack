---
description: PP Backup Skill -- snapshot state before deploy, restore-tested. Reality contract: a snapshot without a restore-test verdict is not a backup.
argument-hint: "[--project NAME] [--dry-run] [--config PATH]"
---

# /backup -- PP Backup / Snapshot Axis

State-preservation precondition for the Deploy Axis. Closes the gap
identified in Deploy PASO 0: deploys verify the future (healthcheck
post-deploy) but do not preserve the past (snapshot pre-deploy).
Sister to /deploy. Precondition for the future Rollback Axis.

Spec: `vault/specs/backup-skill.md`.

## Surface

```
/backup [--project NAME] [--dry-run] [--config PATH]
```

Flags:

- `--project NAME` -- override project name (default: cwd basename)
- `--dry-run` -- detector + runner planner only; no mutation; no receipt
- `--config PATH` -- override `vault/backup/<project>.json`

## Protocol (8 steps)

When the Owner invokes `/backup ...`, follow this protocol exactly:

1. **Load config.** Invoke `python modules/backup/backup.py` with
   STDIN JSON `{"project_root": <cwd>, "project": <name>, "dry_run":
   <bool>, "config_override": <path?>}`. The dispatcher resolves the
   config at `vault/backup/<project>.json`.

2. **Schema validate.** Reject any key whose name contains
   `password` / `secret` / `token` / `api_key` / `apikey` /
   `passphrase` (case-insensitive). Reject forbidden modes (n8n,
   zapier, make.com, pipedream). Exit 2 BEFORE any runner action.

3. **Disk-full guard.** `shutil.disk_usage` on the
   `local_destination` directory; require at least `2 ×
   expected_size_bytes` or 1 GiB floor. CEILING exit 4 if
   insufficient.

4. **Dispatch runner.**
   - `rsync-dir` -> `runners/rsync_dir.py` (tar+gzip+ssh pipe)
   - `docker-volume-tar` -> `runners/docker_volume_tar.py`
     (ephemeral alpine container snapshot)
   - `pg-dump` -> `runners/pg_dump.py` (logical Postgres backup)

5. **Restore-test.** Only if runner verdict is `pass`, invoke
   `verify_restore.py` with the snapshot path + `restore_test`
   spec. Supported `structural_check` values: `nbt-magic`,
   `pg-dump-header`, `json-parse`, `not-empty`. Failure -> verdict
   `backup-warn` exit 3.

6. **Apply retention.** Only on restore-test PASS, invoke
   `retention.py` to enforce `keep_last_n` + `drop_older_than_days`
   + `min_keep`. Writes sha256 manifest at
   `<local_destination>/manifest.json`.

7. **Write receipt.** Only AFTER restore-test (PASS or FAIL), the
   dispatcher writes `vault/backups/<UTC-ts>_<project>.md` with 4
   sections (Runner / Receipt / Restore-test / Retention).

8. **Echo verdict.** Show the Owner the verdict (one of: `pass`,
   `dry-run`, `skip`, `ceiling`, `backup-warn`, `fail`), the mode,
   duration, snapshot size + sha256, and the receipt path.

## Exit code table

| Code | Verdict | Meaning |
|---|---|---|
| 0 | pass | snapshot + sha256 + restore-test OK |
| 0 | dry-run | no mutation; planner output only |
| 0 | skip | `CLAUDEPP_BACKUP_DISABLED=1` |
| 2 | fail | schema invalid / build fail / scp fail |
| 3 | backup-warn | snapshot written but restore-test FAILED; receipt states this |
| 4 | ceiling | SSH key missing / disk-full / config missing |

## Hard invariants

- A snapshot without restore-test verdict is NOT a backup. The
  receipt is the proof; absence of receipt = absence of backup.
- NO credentials in `vault/backup/*.json`. For pg-dump, the
  database password lives in `~/.pgpass` on the remote.
- NO off-site auto-push. Snapshots land in `local_destination`
  (gitignored) only. Off-site is an explicit Owner step.
- `CLAUDEPP_BACKUP_RUNNING=1` recursion guard is level-2+ only
  (lesson L2 sealed in code-review + deploy cycles).
- Retention manifest sha256 verified on every retention pass.

## Examples

```bash
# Dry-run kobiicraft (mode: rsync-dir on gex44 world dirs)
/backup --project kobiicraft --dry-run

# Real backup of tua-x postgres
/backup --project tua-x

# Inspect previous backups
ls vault/backups/ | grep kobiicraft
```

## Integration with /deploy

`vault/deploy/<project>.json` supports an optional `pre_deploy_backup:
true` field. When set, `/deploy` invokes `/backup` as a pre-gate; backup
verdict != pass aborts the deploy with CEILING. The backup verdict is
folded into the deploy receipt under a new "Pre-deploy backup" section.

This is the **safe-deploy contract**: a deploy is only safe if a
restore-tested snapshot exists from immediately before it.

## Cross-references

- Spec: `vault/specs/backup-skill.md`
- Plan: `vault/plans/backup-skill-2026-05-24.md`
- Apex section: `knowledge_vault/core/apex-completion-standard.md`
  "Backup Axis (sealed 2026-05-25)"
- UKDL: `vault/knowledge_base/ukdl-universal.md` UKDL-BK-01..05
- Sister skill: `commands/deploy.md`
