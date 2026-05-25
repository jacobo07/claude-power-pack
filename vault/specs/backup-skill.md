# Backup / Snapshot Skill -- Authoritative Spec

Status: **Sealed 2026-05-25**
Closes: state-preservation gap discovered in Deploy Axis PASO 0 grounding (2026-05-24).
Sister axis to Deploy. Precondition for the future Rollback Axis.

---

## 1. Purpose

Preserve state BEFORE a deploy. A deploy that succeeds against a corrupted plugin update destroys user-generated worlds, transaction state, and database rows. The Deploy Axis verifies the future ("did the new bytes serve?"); the Backup Axis verifies the past ("can we get back to where we were?"). Together they bracket the deploy event.

The skill is a 3-mode runner (rsync-dir / docker-volume-tar / pg-dump), a restore-test verifier, a retention policy enforcer, and a receipt writer. It is NOT a backup orchestrator -- it does not schedule cron jobs, it does not push to off-site storage automatically, and it does not encrypt. Those are deliberate out-of-scope choices documented in §15.

## 2. Reality Contract

A snapshot that has not been restore-tested is a `.tar.gz`, not a backup. The dispatcher refuses to write a `vault/backups/<ts>_<project>.md` receipt unless `verify_restore.py` has executed against the snapshot AND emitted a structural-check verdict (PASS or FAIL). A snapshot with sha256 manifest mismatch or restore-test failure yields verdict `backup-warn` (exit 3); the receipt states the failure in plain text. No silent masking.

## 3. Architecture

```
modules/backup/
  __init__.py
  backup.py              # dispatcher (entry point)
  runners/
    __init__.py
    rsync_dir.py         # mode: rsync-dir   (tar+gzip+ssh pipe)
    docker_volume_tar.py # mode: docker-volume-tar
    pg_dump.py           # mode: pg-dump
  verify_restore.py      # restore-test: extract to tmpdir + structural_check
  retention.py           # keep-last-N + drop-older-than + sha256 manifest
  test_v_block.py        # 12+ V-tests
commands/backup.md       # /backup slash command
vault/backup/            # per-project configs (JSON, no credentials)
vault/backups/           # per-run receipts (closed loop)
```

The dispatcher is the single public entry. It accepts STDIN JSON, runs schema-validate → disk-full guard → runner → verify_restore → retention → receipt. Runners are pure I/O; they do not decide verdicts.

## 4. The 3 backup modes

| Mode | Mechanism | Real-world target |
|---|---|---|
| `rsync-dir` | `ssh <alias> 'tar --create -C <remote_root> <paths...> \| gzip -1'` piped to a local file; no agent required on remote | KobiiCraft world + plugin data dirs |
| `docker-volume-tar` | `ssh <alias> 'docker run --rm -v <volume>:/data alpine tar -czf - /data'` piped local | TUA-X `postgres_data` + `rabbitmq_data` |
| `pg-dump` | `ssh <alias> 'docker exec <container> pg_dump -Fc -U <user> <db>'` piped local; restore via `pg_restore` | TUA-X postgres (logical), InfinityOps when applicable |

Each runner emits the snapshot bytes to a local destination (`local_destination`), records the byte count + sha256, and returns a `RunnerResult` dict. The dispatcher does not orchestrate networking beyond what SSH provides.

## 5. STDIN / STDOUT contract

Input (STDIN JSON):

```json
{
  "project_root": "C:/path/to/project",
  "project": "kobiicraft",
  "dry_run": false,
  "config_override": "vault/backup/kobiicraft.json"
}
```

Output (STDOUT JSON):

```json
{
  "verdict": "pass|fail|ceiling|backup-warn|skip|dry-run",
  "exit_code": 0|2|3|4,
  "mode": "rsync-dir|docker-volume-tar|pg-dump",
  "snapshot_path": "backups/kobiicraft/2026-05-25-HHMMSS.tar.gz",
  "snapshot_size_bytes": 12345678,
  "snapshot_sha256": "abcd...",
  "duration_ms": 12345,
  "restore_test": { "ok": true|false, "checks_passed": 2, "checks_total": 2, "evidence": "..." },
  "retention_applied": { "kept": 10, "dropped": 2, "dropped_files": [...] },
  "receipt_path": "vault/backups/2026-05-25-HHMMSS_kobiicraft.md",
  "summary": "human-readable one-liner",
  "previous_backups": ["..."]
}
```

## 6. Verdict shapes and exit codes

| Verdict | Exit | When |
|---|---|---|
| `pass` | 0 | snapshot + sha256 manifest + restore-test all OK |
| `dry-run` | 0 | `--dry-run`; no mutation; prints plan |
| `skip` | 0 | `CLAUDEPP_BACKUP_DISABLED=1` |
| `fail` | 2 | schema invalid / build fail / scp fail / pg_dump non-zero |
| `backup-warn` | 3 | snapshot bytes written BUT restore-test FAILED or sha256 mismatch -- receipt states this explicitly |
| `ceiling` | 4 | SSH key missing / disk-full / target unreachable / mode=none |

## 7. Config schema (vault/backup/<project>.json)

```json
{
  "project": "kobiicraft",
  "mode": "rsync-dir",
  "ssh_alias": "gex44",
  "ssh_key": "~/.ssh/kobicraft_gex44",
  "remote_paths": ["/srv/kobiicraft/main/world", "/srv/kobiicraft/main/plugins"],
  "local_destination": "backups/kobiicraft/",
  "retention": {"keep_last_n": 10, "drop_older_than_days": 30, "min_keep": 3},
  "restore_test": {
    "extract_method": "tar-gz",
    "sample_files": ["world/level.dat"],
    "structural_check": "nbt-magic"
  },
  "manifest": true,
  "notes": "..."
}
```

Forbidden keys (validator REJECTS with exit 2 before any runner action):

- Any key whose name contains (case-insensitive) `password`, `secret`, `token`, `api_key`, `apikey`, `passphrase`.

Forbidden modes: `n8n`, `zapier`, `make.com`, `pipedream`.

Authentication is delegated entirely to `~/.ssh/config` (host aliases + key files). The Owner manages credentials outside the backup config.

## 8. Restore-test contract

`verify_restore.py` is invoked AFTER the snapshot is written, BEFORE retention is applied, BEFORE the receipt is written. It:

1. Computes sha256 of the snapshot file; compares against the runner-reported sha256.
2. Extracts the snapshot into a `tempfile.TemporaryDirectory()`.
3. Verifies each `sample_files` path exists in the extracted tree.
4. Applies the declared `structural_check` (e.g. `nbt-magic`, `pg-dump-header`, `json-parse`, `not-empty`).
5. Returns `{ok, checks_passed, checks_total, evidence}`.

If `ok=False`, the dispatcher emits verdict `backup-warn` exit 3 AND the receipt explicitly says "snapshot written, restore-test FAILED". Retention IS NOT applied on backup-warn (the failed snapshot stays on disk for Owner inspection).

Supported `structural_check` values:

| Check | Mechanism |
|---|---|
| `nbt-magic` | First 4 bytes of `world/level.dat` decompressed = NBT gzip magic |
| `pg-dump-header` | First 5 bytes of pg_dump output = `PGDMP` (custom format) |
| `json-parse` | All `.json` sample files parse without error |
| `not-empty` | Each sample file has size > 0 |

## 9. Disk-full guard

Before invoking the runner, the dispatcher checks:

- `df --output=avail <local_destination>` returns at least `2× expected_snapshot_size`.
- `expected_snapshot_size` is taken from the config's optional `expected_size_bytes` field (Owner-provided estimate). If absent, the guard checks for a minimum of **1 GiB free** as a conservative floor.

Disk-full → CEILING exit 4. The receipt is NOT written (the dispatcher refuses to start work that cannot complete).

## 10. NO credentials in vault/backup/

Same hard invariant as Deploy. Schema validator rejects any key containing the forbidden tokens BEFORE the runner executes. For `pg-dump`, the database password must live in `~/.pgpass` on the host invoking the `pg_dump` command (i.e., the VPS itself, via ssh). The skill never sees the password.

## 11. NO push to off-site by default

Each runner writes to `local_destination` (a directory under the PP repo's `backups/` -- gitignored). The skill does NOT automatically push to S3, rclone, or any off-site target. Off-site push is a backlog item documented in §15.

Rationale: the most catastrophic failure mode of an automated backup is a misconfigured push that silently fails or pushes corrupted bytes. Local-first writes are auditable; off-site is an explicit Owner action.

## 12. Recursion guard

`CLAUDEPP_BACKUP_RUNNING=1` is set ONLY when the dispatcher spawns nested sub-shell commands (level-2+). It is NEVER set on the level-1 entry from the slash command or hook piggyback. Lesson L2 sealed in code-review + deploy cycles.

## 13. Mirror-Sync-Direction

Apex section is written to PP source first:

```
claude-power-pack/knowledge_vault/core/apex-completion-standard.md
```

Then byte-mirrored to the live loose copy via Python `read_bytes` / `write_bytes`. SHA-256 must match. Direction is one-way only: PP → loose.

## 14. Opt-out env vars

| Env var | Effect |
|---|---|
| `CLAUDEPP_BACKUP_DISABLED=1` | Disables the skill (verdict `skip`, exit 0) |
| `CLAUDEPP_BACKUP_SKIP_RESTORE_TEST=1` | Skips the restore-test step. **Not recommended.** When set, the receipt explicitly records this and the verdict can never be `pass` (the highest reachable is `backup-warn` because restore-test was skipped). |

## 15. Out of scope (explicit)

- Off-site push (S3, rclone, scp-to-cold-storage). Backlog.
- Encrypted snapshots (gpg). Backlog.
- Cron / scheduler. Owner schedules manually.
- Backup of Pterodactyl panel files. Out of scope for the 3 productive projects.
- Restore command (`/restore`). Belongs to the future Rollback Axis (P1.2 of the 2026-05-24 roadmap).

## 16. DONE gate

- [ ] All V-tests in `test_v_block.py` PASS with documented evidence.
- [ ] `verify_spp.py` exits 0 (7/7 STRICT); pre-existing FAILs documented in session_lessons.md if any.
- [ ] `verify_full_install.py` exits 0.
- [ ] Apex section sealed; PP source + live mirror sha256 match.
- [ ] UKDL-BK-01..05 rows + UKDL-BK-REP-01.
- [ ] session_lessons.md L1..LN rows from this cycle.
- [ ] V-DEEP dry-run receipt at `vault/backups/<ts>_kobiicraft_dryrun.md`.
- [ ] `git push origin main` REMOTE_DELTA = 0.
- [ ] Deploy integration: `vault/deploy/*.json` supports `pre_deploy_backup` field; `modules/deployment/deploy.py` invokes backup as pre-gate; V-BACKUP-FIRST test PASS.
