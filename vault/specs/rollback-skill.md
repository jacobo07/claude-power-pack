# Rollback Skill -- Authoritative Spec

Status: **Sealed 2026-05-25**
Closes: state-recovery gap discovered in Backup Axis grounding (2026-05-25) -- backups exist but no in-band path to apply them under deploy failure pressure.
Downstream of Backup. Completes the deploy lifecycle chain: **Backup (safe) -> Deploy (deliver) -> Rollback (recover)**.

---

## 1. Purpose

Make every deploy recoverable. The Deploy Axis verifies the future ("did the new bytes serve?"); the Backup Axis verifies the past ("can we get back to where we were?"); the Rollback Axis EXERCISES that past under pressure ("get us back, now"). Without this third node, every deploy is in practice irreversible -- the Owner faces 15-minute manual restoration under outage pressure when seconds count.

The skill is a 3-mode inverse runner (`restore_rsync_dir` / `restore_pg_dump` / `restore_docker_volume`), a manifest-based source selector, a healthcheck verifier (reuses `modules/deployment/healthcheck.py`), and a receipt writer. It is NOT an automatic safety net -- it never fires without an explicit Owner command (or explicit Owner-supplied JSON STDIN), and the Deploy Axis only SUGGESTS the command on failure; it does not invoke it.

## 2. Reality Contract

A rollback that has not been health-checked against the live target is a `subprocess.run` that returned 0, not a recovery. The dispatcher refuses to write a `vault/rollbacks/<ts>_<project>.md` receipt unless the post-restore healthcheck (TCP / HTTP / curl-grep, depending on project) has executed AND emitted a verdict (PASS or FAIL). A restore that succeeded technically but whose healthcheck FAILED yields verdict `rollback-warn` (exit 3); the receipt states the failure in plain text. No silent masking.

A snapshot that does not appear in `backups/<project>/manifest.json` was either never written or never passed `verify_restore`. The source selector REFUSES to use such snapshots even if they exist on disk -- a `.tar.gz` without a manifest entry is exactly the case the Backup Axis already classified as `backup-warn`, and rolling forward from one would propagate corrupted state into production.

## 3. Architecture

```
modules/rollback/
  __init__.py
  rollback.py                   # dispatcher (entry point)
  source_selector.py            # reads backups/<project>/manifest.json
  runners/
    __init__.py
    restore_rsync_dir.py        # mode: rsync-dir (inverse of backup runner)
    restore_pg_dump.py          # mode: pg-dump
    restore_docker_volume.py    # mode: docker-volume-tar
  test_v_block.py               # 15 V-tests
commands/rollback.md            # /rollback slash command
vault/rollback/                 # per-project configs (JSON, no credentials)
vault/rollbacks/                # per-run receipts (closed loop)
vault/rescues/                  # opt-in pre-rollback rescue snapshots
```

The dispatcher is the single public entry. It accepts STDIN JSON, runs schema-validate -> source select (manifest) -> optional rescue -> runner -> healthcheck -> receipt. Runners are pure I/O; they do not decide verdicts. Healthcheck logic is imported from `modules/deployment/healthcheck.py` -- single source of truth, no duplication.

## 4. The 3 inverse runners

| Mode | Mechanism | Real-world target |
|---|---|---|
| `rsync-dir` | local `cat <ts>.tar.gz | ssh <alias> 'tar -xzf - -C /'` then optional `ssh <alias> '<post_restore_cmd>'` (e.g. `sudo systemctl restart kobiicraft@main`) | KobiiCraft world + plugin restore |
| `pg-dump` | `cat <ts>.dump | ssh <alias> 'docker exec -i <container> pg_restore -c -U <user> -d <db>'` -- the `-c` flag drops + recreates objects before reload | TUA-X postgres, InfinityOps postgres |
| `docker-volume-tar` | `cat <ts>.tar.gz | ssh <alias> 'docker run --rm -i -v <vol>:/data alpine sh -c "cd /data && tar -xzf -"'` | TUA-X named volumes (e.g. rabbitmq_data) when applicable |

Each runner streams the local snapshot bytes back to the remote via the same SSH pipe used to take the snapshot, runs the optional post-restore command, and returns a `RunnerResult` dict. The dispatcher then invokes the project's healthcheck to verify the live target accepts traffic.

## 5. STDIN / STDOUT contract

Input (STDIN JSON):

```json
{
  "project_root": "C:/path/to/project",
  "project": "kobiicraft",
  "dry_run": false,
  "target_snapshot": null,
  "rescue_current": false,
  "include_code_rollback": false,
  "config_override": "vault/rollback/kobiicraft.json"
}
```

Field semantics:

- `target_snapshot`: file name relative to `backups/<project>/`, e.g. `"2026-05-25-151305.tar.gz"`. `null` means "latest verified" (highest mtime entry in manifest.json with `verify_restore=PASS`).
- `rescue_current`: when `true`, the dispatcher takes a snapshot of the CURRENT remote state to `vault/rescues/<ts>_<project>.tar.gz` BEFORE applying the restore. Default `false` (Hawkins lens: no destructive-by-default behaviour beyond what the Owner asked for).
- `include_code_rollback`: only meaningful for `project=infinityops`. When `true`, after data restore the dispatcher invokes `gh workflow run deploy-vps.yml --ref <prev_sha>` to re-trigger the canonical §77 CD pipeline on the previous deployed commit. `prev_sha` is read from `previous_deploys` in the latest deploy receipt. Default `false`.

Output (STDOUT JSON):

```json
{
  "verdict": "pass|fail|ceiling|rollback-warn|skip|dry-run",
  "exit_code": 0|2|3|4,
  "mode": "rsync-dir|pg-dump|docker-volume-tar",
  "source_snapshot": "backups/kobiicraft/2026-05-25-151305.tar.gz",
  "source_sha256": "abcd...",
  "source_verified": true,
  "rescue_path": null,
  "code_rollback_invoked": false,
  "code_rollback_ref": null,
  "healthcheck_result": { "ok": true, "kind": "tcp", "attempts": 1, "evidence": "..." },
  "duration_ms": 12345,
  "receipt_path": "vault/rollbacks/2026-05-25-HHMMSS_kobiicraft.md",
  "summary": "human-readable one-liner",
  "previous_rollbacks": ["..."]
}
```

## 6. Verdict shapes and exit codes

| Verdict | Exit | When |
|---|---|---|
| `pass` | 0 | runner OK + healthcheck OK + receipt written |
| `dry-run` | 0 | `dry_run: true`; no mutation; prints plan |
| `skip` | 0 | `CLAUDEPP_ROLLBACK_DISABLED=1` |
| `fail` | 2 | schema invalid / runner crash / restore command non-zero |
| `rollback-warn` | 3 | runner OK BUT healthcheck FAILED -- receipt states this explicitly; rescue (if requested) was written and IS recoverable |
| `ceiling` | 4 | SSH key missing / target_snapshot not in manifest / manifest absent (no verified backup exists) / config invalid |

## 7. Config schema (vault/rollback/<project>.json)

```json
{
  "project": "kobiicraft",
  "mode": "rsync-dir",
  "ssh_alias": "gex44",
  "ssh_key": "~/.ssh/kobicraft_gex44",
  "backup_source_dir": "backups/kobiicraft/",
  "post_restore_cmd": "sudo systemctl restart kobiicraft@main",
  "healthcheck": {
    "kind": "tcp",
    "target": "5.9.23.174",
    "port": 25565,
    "retries": 12,
    "delay_sec": 10
  },
  "notes": "..."
}
```

For `pg-dump` mode, additional keys: `pg_container`, `pg_user`, `pg_database` (mirrors the backup config; the inverse runner needs them to reach the same database).

Forbidden keys (validator REJECTS with exit 2 before any runner action):

- Any key whose name contains (case-insensitive) `password`, `secret`, `token`, `api_key`, `apikey`, `passphrase`.

Forbidden modes: `n8n`, `zapier`, `make.com`, `pipedream`.

Authentication is delegated entirely to `~/.ssh/config` (host aliases + key files). The Owner manages credentials outside the rollback config.

## 8. Source selector contract

`source_selector.py` is invoked AFTER schema validation, BEFORE any runner action. It:

1. Resolves `backups/<project>/manifest.json` from `project_root`.
2. If the manifest is absent: returns CEILING with message `"No verified backup exists for <project>. Ensure a /backup --project <project> has run successfully (verdict=pass) before invoking /rollback."`.
3. If the manifest is present: parses the entries, sorts by `mtime` descending.
4. If `target_snapshot` is `null`: returns the highest-mtime entry.
5. If `target_snapshot` is given: returns that specific entry if present in manifest, else CEILING with `"Target snapshot <name> not found in manifest. Use /rollback --list to see verified snapshots."`.
6. The returned entry always carries `path`, `sha256`, `size_bytes`, `mtime`.

A snapshot on disk that is NOT in the manifest is treated as if it does not exist. This is the load-bearing invariant of §2.

## 9. Healthcheck post-rollback

The dispatcher imports `check_tcp`, `check_http`, `check_curl_grep` from `modules/deployment/healthcheck.py`. The `healthcheck` block in the rollback config has the same shape as the deploy config: `{kind, target/url/port/grep_pattern, retries, delay_sec}`. The dispatcher dispatches on `kind` and propagates the result into the receipt.

A rollback whose healthcheck returns `ok=False` yields `rollback-warn` (exit 3), NOT `fail`. The distinction matters: the bytes were restored (so the disk is in a known state corresponding to a previously verified backup), but the live process did not come back online. The Owner investigates whether to retry, escalate, or take the rescue snapshot off disk and apply it manually.

## 10. NO automatic rollback

The Deploy Axis dispatcher (`modules/deployment/deploy.py`) does NOT call `modules/rollback/rollback.py` directly under any verdict. On `verdict in {fail, deploy-warn}`, the deploy receipt and the deploy STDOUT summary include a single suggested line:

```
To roll back: /rollback --project <X>   (NOT auto-invoked; Owner decides)
```

V-NO-AUTO grep-asserts that `modules/deployment/deploy.py` contains zero call sites that invoke `rollback.py` (the only allowed mention is the literal suggestion string above). Rationale: autonomous mode has no TTY, an interactive prompt would corrupt the JSON STDIN/STDOUT contract, and Hawkins lens places "the Owner always decides on destructive operations" above the convenience of one fewer keypress.

## 11. §77 Deploy Sovereignty extension to rollback

For `project=infinityops` with `include_code_rollback=true`, the dispatcher does NOT reimplement `deploy_from_git.sh`. It invokes `gh workflow run deploy-vps.yml --ref <prev_sha>` and prints the §77 citation line to STDOUT before invocation:

```
§77 Deploy Sovereignty: code rollback for infinityops invokes the
canonical deploy-vps.yml workflow on ref <prev_sha>. This skill
INVOKES that pipeline; it does not replace it.
```

`prev_sha` is read from the most recent entry in `vault/deploys/*_infinityops.md` (the deploy receipt format includes the deployed git sha in its header). If no such receipt exists, CEILING with explicit message.

V-DOCTRINE-CITE-ROLLBACK asserts this print on every infinityops-with-code-rollback invocation. The cite is non-negotiable -- same invariant as Deploy Axis V-DOCTRINE-CITE for gh_workflow.py.

## 12. Recursion guard

`CLAUDEPP_ROLLBACK_RUNNING=1` is set ONLY when the dispatcher spawns nested sub-shell commands (level-2+). It is NEVER set on the level-1 entry from the slash command or external invocation. Lesson L2 sealed in code-review + deploy + backup cycles, now repeated for rollback to keep the rule symmetrical across all four executable axes.

## 13. Mirror-Sync-Direction

Apex section is written to PP source first:

```
claude-power-pack/knowledge_vault/core/apex-completion-standard.md
```

Then byte-mirrored to the live loose copy via Python `read_bytes` / `write_bytes`. SHA-256 must match. Direction is one-way only: PP -> loose.

## 14. Opt-out env vars

| Env var | Effect |
|---|---|
| `CLAUDEPP_ROLLBACK_DISABLED=1` | Disables the skill (verdict `skip`, exit 0) |

Unlike Backup, there is no `SKIP_HEALTHCHECK` opt-out. A rollback without a post-healthcheck verdict is by definition not a rollback per §2 -- there is no path to verdict `pass` that bypasses it.

## 15. Out of scope (explicit)

- Automatic rollback on deploy failure. By design (§10).
- Code rollback for projects other than InfinityOps. TUA-X code rollback is `git push vps204 +<prev_sha>:main` and is Owner-driven (the post-receive hook handles the rest). KobiiCraft code rollback IS data rollback (the .jar lives inside the backup tar.gz alongside the world data).
- Cross-project rollback (e.g. "roll back kobiicraft AND tua-x atomically"). Each project rolls back independently.
- Time-travel rollback to an arbitrary point not captured by an existing snapshot. Backups are discrete; rollback targets are discrete.
- Restore-test of the snapshot at rollback time. The Backup Axis already restore-tested it; we trust the manifest. Re-testing on every rollback doubles the wall-clock cost of recovery for no integrity gain.

## 16. DONE gate

- [ ] All V-tests in `test_v_block.py` PASS with documented evidence.
- [ ] `verify_spp.py` exits 0 (7/7 STRICT); pre-existing FAILs documented in session_lessons.md if any.
- [ ] `verify_full_install.py` exits 0.
- [ ] Apex section sealed; PP source + live mirror sha256 match.
- [ ] UKDL-RB-01..05 rows + UKDL-RB-REP-01.
- [ ] session_lessons.md L1..LN rows from this cycle.
- [ ] V-DEEP dry-run receipt at `vault/rollbacks/<ts>_kobiicraft_dryrun.md`.
- [ ] `git push origin main` REMOTE_DELTA = 0.
- [ ] Deploy integration: `modules/deployment/deploy.py` prints rollback-suggestion on fail|deploy-warn; V-ROLLBACK-SUGGEST and V-NO-AUTO tests PASS.
