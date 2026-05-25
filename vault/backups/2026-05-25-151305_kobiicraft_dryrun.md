# Backup receipt -- kobiicraft (V-DEEP self-test, dry-run)

- Timestamp (UTC): 2026-05-25-151305
- Duration: 0 ms (dry-run path is schema-validate + planner only)
- Mode: rsync-dir
- SSH alias: gex44
- Local destination: backups/kobiicraft/

## 1. Runner verdict

- verdict: dry-run
- ok: true
- summary: rsync-dir dry-run for gex44
- snapshot_path (planned): C:\Users\User\.claude\skills\claude-power-pack\backups\kobiicraft\2026-05-25-151251.tar.gz
- snapshot_size_bytes: 0 (dry-run does not write bytes)
- snapshot_sha256: "" (no snapshot to hash)

## 2. Runner receipt (planner output)

```
DRY RUN -- ssh key resolved: C:\Users\User\.ssh\kobicraft_gex44
DRY RUN -- ssh_alias: gex44
DRY RUN -- remote paths: ['/srv/kobiicraft/main/world', '/srv/kobiicraft/main/world_nether', '/srv/kobiicraft/main/world_the_end', '/srv/kobiicraft/main/plugins']
DRY RUN -- would execute: ssh -i C:\Users\User\.ssh\kobicraft_gex44 gex44 'tar --create -P /srv/kobiicraft/main/world /srv/kobiicraft/main/world_nether /srv/kobiicraft/main/world_the_end /srv/kobiicraft/main/plugins | gzip -1'
DRY RUN -- snapshot would land at: backups/kobiicraft/2026-05-25-151251.tar.gz
```

## 3. Restore-test (verify_restore.py) -- planned

```
(dry-run path does not execute restore-test -- it would run only after a
real ssh+tar returned exit 0 with non-zero snapshot bytes)

Configured restore_test:
{
  "extract_method": "tar-gz",
  "sample_files": ["srv/kobiicraft/main/world/level.dat"],
  "structural_check": "nbt-magic"
}

What it would do on a real snapshot:
- tarfile.open(snapshot, "r:*"); extract the level.dat member to tempdir
- gunzip the level.dat bytes (Minecraft world data is always gzipped NBT)
- assert first byte is 0x0a (NBT Compound tag)
- verdict pass if first-byte matches; backup-warn if not
```

## 4. Retention applied -- planned

```
(retention is applied ONLY after restore-test PASS)

Configured retention:
{
  "keep_last_n": 10,
  "drop_older_than_days": 30,
  "min_keep": 3
}

What it would do:
- list backups/kobiicraft/*.tar.gz; sort by mtime desc
- keep_set = (top 10) UNION (anything within 30 days) UNION (always keep 3)
- drop the rest; unlink files; record drop list
- write backups/kobiicraft/manifest.json with sha256 of each retained snapshot
```

## V-DEEP empirical evidence

This receipt is the artefact of P12 in the Backup Skill plan
(`vault/plans/backup-skill-2026-05-24.md`). It captures these facts:

1. The dispatcher correctly loaded the config from
   `vault/backup/kobiicraft.json` (PP source).
2. Schema validation PASSED: no credential-class keys, mode in
   the allowed set (`rsync-dir`), retention + restore_test specs
   both present.
3. The disk-full guard passed (this Windows host has plenty of free
   space; the guard's 1 GiB floor is satisfied).
4. The runner identified the correct ssh key path:
   `C:\Users\User\.ssh\kobicraft_gex44` exists locally (the file
   was confirmed at PASO 0 of Deploy Axis).
5. The planned ssh command preserves the full path list verbatim
   and pipes through `gzip -1` -- low compression for speed (the
   restore-test is what guarantees integrity, not the gzip CRC).
6. The dispatcher did NOT mutate disk: no snapshot file was written
   (dry-run path), no receipt was auto-written by the receipt-writer
   (the present file is a manually-curated V-DEEP artefact).

## Reality contract reaffirmed

- A backup that has not been restore-tested is, by spec §2, NOT a
  backup. This dry-run executes nothing on the live target; no
  claim of preservation is implied by this artefact.
- For a real `/backup --project kobiicraft` invocation, the
  dispatcher will execute ssh+tar, then verify_restore against the
  NBT magic, then apply retention, then write the receipt. Each
  step has its own verdict; the combined verdict is the bottleneck.
- The §11 invariant holds: snapshots land in local `backups/`
  (gitignored). Off-site push is an explicit Owner step, not an
  automatic side-effect of /backup.
