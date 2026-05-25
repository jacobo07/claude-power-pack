# Backup / Snapshot Skill -- ULTRA Plan (2026-05-24, executed 2026-05-25)

Sister to Deploy Axis (sealed 2026-05-24). Closes the state-preservation gap
identified in Deploy PASO 0. Precondition for the future Rollback Axis.

Spec: `vault/specs/backup-skill.md` (16 sections).
Apex section target: "Backup Axis (sealed 2026-05-25) -- safe-deploy precondition".

---

## PASO 0 grounding (executed 2026-05-24, cited verbatim)

Honest tabla por proyecto (decisional inputs for the scope):

| Project | JAR/release backup today | State-of-runtime backup today | Cron / scheduled | Restore-tested |
|---|---|---|---|---|
| KobiiCraft | `vps-bootstrap/scripts/deploy/safe-deploy.sh` -- backup JAR via SFTP to `$BACKUP_DIR/$SERVER/` before scp + auto-rollback on test fail | **NO**. World `/srv/kobiicraft/<i>/world/`, `world_nether/`, `world_the_end/`, `plugins/*/data/`, player files NEVER backed up | NO known cron in repo | rollback restores JAR only, not state |
| TUA-X | NO (docker compose recreates images) | **NO**. `postgres_data` + `rabbitmq_data` volumes persist on filesystem only; no `pg_dump`, no volume tar, no snapshot policy | NO | NO |
| InfinityOps | `git checkout -f main` (ascend.sh) -- code rollback is `git reset --hard` | **NO**. Postgres/RabbitMQ assumed persistent; `ascend.sh:509` cites "PG/Rabbit unreachable" as diagnostic, not as backupable precondition | NO | NO |

**Lectura clave:** the 3 projects share the same exact gap. Opposite case to Deploy
Axis (where InfinityOps already had the §77 canonical pipeline). Here NONE has the
real path -- Backup Axis is a pure generator in all 3 modes, not a detector/invoker.

KobiiCraft has a partial seed (JAR backup via safe-deploy.sh) that the module CAN
invoke as a sibling step; the other 2 start from zero.

---

## Sequencing graph

```
P1 spec  ---+
P2 plan ----+--> P3 rsync_dir ---+
                P4 docker_volume_tar -+
                P5 pg_dump ----------+
                P6 verify_restore ---+
                P7 retention --------+
                                     v
                              P8 backup.py (dispatcher)
                                     v
                              P9 V-block
                                     v
                              P10 /backup command
                                     v
                              P11 3 configs
                                     v
                              P12 V-DEEP dry-run
                                     v
                              P13 Deploy integration (--backup-first)
                                     v
                              P14 Apex + mirror
                                     v
                              P15 UKDL + lessons
                                     v
                              P16 verify_spp + push
```

---

## Pasos detallados

### P1 -- Spec (DONE)
Output: `vault/specs/backup-skill.md` (16 sections).
Done-gate: 3 modes documented; restore-test contract; Jobs/Woz PASS; cites §11 (no off-site) + §10 (no credentials).

### P2 -- Plan (this file, in progress)
Done-gate: cites PASO 0; sequencing graph; per-paso done-gates.

### P3 -- rsync_dir.py
Function: `run_rsync_dir(config, dry_run) -> dict`.
Logic: `ssh -i <key> <alias> 'tar --create -C <root> <paths...> | gzip -1' > <local_dest>/<ts>.tar.gz`.
Done-gate: dry-run prints planned command; CEILING on missing key; receipt includes byte count + sha256.

### P4 -- docker_volume_tar.py
Function: `run_docker_volume_tar(config, dry_run) -> dict`.
Logic: `ssh -i <key> <alias> 'docker run --rm -v <volume>:/data alpine tar -czf - /data' > <local_dest>/<ts>.tar.gz`.
Done-gate: dry-run; CEILING if docker not available remote; receipt includes volume name + sha256.

### P5 -- pg_dump.py
Function: `run_pg_dump(config, dry_run) -> dict`.
Logic: `ssh -i <key> <alias> 'docker exec <pg_container> pg_dump -Fc -U <user> <db>' > <local_dest>/<ts>.dump`.
Done-gate: dry-run; schema rejects db password in JSON (lives in `~/.pgpass` on VPS); receipt includes db name + sha256.

### P6 -- verify_restore.py
Function: `verify_restore(snapshot_path, restore_test_spec) -> dict`.
Logic: extract to tempdir; check each sample file exists; apply structural_check.
Supported checks: `nbt-magic`, `pg-dump-header`, `json-parse`, `not-empty`.
Done-gate: V-RESTORE-TEST + V-RESTORE-FAIL PASS with mock snapshots.

### P7 -- retention.py
Function: `apply_retention(local_destination, retention_spec) -> dict`.
Logic: list snapshots; sort by mtime; apply `keep_last_n` + `drop_older_than_days`; respect `min_keep`.
Manifest: write `<local_destination>/manifest.json` with sha256 of each retained snapshot.
Done-gate: V-RETENTION-APPLY PASS (12 fixtures -> 10 kept + 2 dropped, manifest updated).

### P8 -- backup.py (dispatcher)
Function: `main()` -- reads STDIN, validates schema, runs disk-full guard, dispatches runner, runs verify_restore, applies retention, writes receipt.
STDIN/STDOUT contract per spec §5.
Recursion-guard env var NOT set at level-1.
Done-gate: STDIN BOM strip (lesson L2 sealed); verdict shapes complete.

### P9 -- test_v_block.py
12 V-tests + V-TIMING. Each mocks external commands (ssh/docker/pg_dump) via subprocess monkeypatch where needed.
Done-gate: 12+/12+ PASS; p95 timing < 500 ms on dry-run hot path.

### P10 -- commands/backup.md
Surface: `/backup [--project NAME] [--dry-run] [--config PATH]`.
Done-gate: 8-step protocol documented; cites spec §8 restore-test contract.

### P11 -- 3 configs
Outputs:
- `vault/backup/kobiicraft.json` (mode: rsync-dir, restore_test: nbt-magic)
- `vault/backup/tua-x.json` (mode: pg-dump, restore_test: pg-dump-header)
- `vault/backup/infinityops.json` (mode: pg-dump, restore_test: pg-dump-header)
Done-gate: 3 valid JSON, no forbidden keys, retention defined, restore_test defined.

### P12 -- V-DEEP dry-run
Output: `vault/backups/2026-05-25-<HHMMSS>_kobiicraft_dryrun.md`.
Execution: `--dry-run` over `kobiicraft.json`. Receipt section says "DRY RUN -- would invoke...".
Done-gate: receipt exists; 4 sections; planned command + restore_test plan shown.

### P13 -- Deploy integration
Modify `vault/deploy/<project>.json` schema to support optional `pre_deploy_backup: true`.
Modify `modules/deployment/deploy.py` to invoke `modules/backup/backup.py` BEFORE the runner when `pre_deploy_backup=true`. Backup verdict != pass -> deploy CEILING.
Add V-BACKUP-FIRST to `modules/deployment/test_v_block.py`: with pre_deploy_backup=true and a mock backup-fail, the deploy short-circuits.
Done-gate: integration test PASS; deploy receipts now show `pre_deploy_backup` field; no regression on existing deploy V-block.

### P14 -- Apex section + mirror
Section: "Backup Axis (sealed 2026-05-25) -- safe-deploy precondition".
Method: Python `read_bytes`/`write_bytes` for PP + live mirror (sister to deploy seal pattern).
Done-gate: sha256(PP) == sha256(live mirror).

### P15 -- UKDL + lessons
Outputs:
- `vault/knowledge_base/ukdl-universal.md` -- UKDL-BK-01..05 + UKDL-BK-REP-01.
- `vault/knowledge_base/session_lessons.md` -- L1..LN findings.
Done-gate: rows appended via Python read_bytes/write_bytes.

### P16 -- verify_spp + push
Steps:
1. `python tools/verify_spp.py` -- expect 7/7 STRICT or documented preexisting FAILs.
2. `python tools/verify_full_install.py` -- exit 0.
3. Selective git add (Backup Axis files only).
4. `git commit -m "feat(backup): Backup Axis sealed -- safe-deploy precondition"`.
5. `git push origin main`.
6. REMOTE_DELTA = 0.

---

## Hard constraints (verifiable)

| Constraint | Verifier |
|---|---|
| NO credentials in vault/backup/ | schema validator + V-CONFIG-INVALID |
| Restore-test obligatory | V-RESTORE-TEST + V-RESTORE-FAIL; dispatcher writes receipt only after verify_restore |
| Disk-full guard | V-DISK-FULL CEILING exit 4 |
| sha256 manifest | retention.py writes manifest.json on every retention pass |
| NO off-site auto-push | runners write to local_destination only; off-site is backlog |
| Reality Contract | receipt written ONLY after verify_restore |
| n8n forbidden | schema validator |
| Recursion guard level-2+ only | `grep -E 'env\["CLAUDEPP_BACKUP_RUNNING"\] = "1"' modules/backup/backup.py` -> 0 hits |
| Mirror-Sync-Direction | sha256 PP == sha256 live mirror; `read_bytes`/`write_bytes` only |
| Slop-token gate | this skill carries zero literal markers from the forbidden set in delivered runtime files (paráfrasis pattern sealed in deploy L3) |

---

## Status log (populated during execution)

| Paso | Status | Evidence |
|---|---|---|
| P1 | done | `vault/specs/backup-skill.md` (16 sections, Jobs/Woz PASS) |
| P2 | in progress | this file |
| P3..P16 | pending |  |

(updated by the executor as each paso completes -- empirical evidence inline)
