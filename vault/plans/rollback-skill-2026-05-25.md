# Rollback Skill -- Plan (2026-05-25)

Materializes the proposal accepted by the Owner this date. Mirrors the structure of `vault/plans/backup-skill-2026-05-24.md`. Closes the deploy lifecycle by adding the third executable node: **Backup -> Deploy -> Rollback**.

---

## P1 -- Spec

`vault/specs/rollback-skill.md` (16 sections). Authoritative contract. Sealed first so subsequent phases have a fixed reference.

## P2 -- Plan file (this document)

Single page, scannable. Goal-backward from the DONE gate of the spec.

## P3 -- `modules/rollback/source_selector.py`

Public function: `select_source(project_root: Path, project: str, target: str | None) -> dict`.

Returns one of:
- `{ok: True, path, sha256, size_bytes, mtime}` -- success
- `{ok: False, reason: "manifest_absent"|"manifest_empty"|"target_not_found"|"target_unverified", evidence: "..."}` -- caller maps to CEILING

Reads `<project_root>/backups/<project>/manifest.json`. This file is written by `modules/backup/retention.py:apply_retention` and contains one entry per verified snapshot with `path`, `sha256`, `size_bytes`, `mtime`. A snapshot on disk without a manifest entry is treated as absent.

## P4 -- `modules/rollback/runners/restore_rsync_dir.py`

Public function: `run_restore_rsync_dir(config: dict, snapshot_path: str, dry_run: bool) -> dict`.

Mechanism: open the local `.tar.gz` for read; pipe it into `ssh -i <key> <alias> 'tar -xzf - -C /'`. The remote tar processes the archive in-place at root (snapshots were taken with `tar --create -P` against absolute paths, so the archive members are absolute and recreate exactly where the backup captured them).

If `config.post_restore_cmd` is set, run `ssh -i <key> <alias> '<post_restore_cmd>'` after the tar extraction. Capture stderr from both.

Returns `{ok, verdict, summary, receipt}`. Verdicts: `pass`, `fail`, `ceiling`, `dry-run`.

## P5 -- `modules/rollback/runners/restore_pg_dump.py`

Public function: `run_restore_pg_dump(config: dict, snapshot_path: str, dry_run: bool) -> dict`.

Mechanism: open local `.dump` for read; pipe into `ssh -i <key> <alias> 'docker exec -i <container> pg_restore -c -U <user> -d <db>'`. The `-c` flag drops + recreates objects before reload -- this is the correct semantics for a rollback (the current state is what we are replacing).

Captures stderr. `pg_restore` exits non-zero on warnings too; the runner classifies exit 0 as `pass`, exit 1 with stderr matching only WARNING lines as `pass` with a `warnings_only=true` flag, anything else as `fail`.

## P6 -- `modules/rollback/runners/restore_docker_volume.py`

Public function: `run_restore_docker_volume(config: dict, snapshot_path: str, dry_run: bool) -> dict`.

Mechanism: open local `.tar.gz` for read; pipe into `ssh -i <key> <alias> 'docker run --rm -i -v <vol>:/data alpine sh -c "cd /data && tar -xzf -"'`.

Symmetric inverse of `runners/docker_volume_tar.py`. The volume contents are wiped (the alpine container's tar overwrites; if archive contents are a complete tree, the result is the snapshot's state).

## P7 -- `modules/rollback/rollback.py` (dispatcher)

Entry function: `rollback(stdin_payload: dict) -> dict`. CLI entry: `main()` -> `int` (exit code).

Pipeline:
1. Honor `CLAUDEPP_ROLLBACK_DISABLED=1` -> `skip` exit 0.
2. Load `vault/rollback/<project>.json` (or `config_override`). Missing -> CEILING exit 4.
3. `validate_config` (reuses `FORBIDDEN_KEY_TOKENS` + `FORBIDDEN_MODES` from backup). Schema invalid -> `fail` exit 2.
4. `source_selector.select_source(...)`. On `ok=False` -> CEILING exit 4 with the selector's reason.
5. If `rescue_current=true`, take a rescue snapshot to `vault/rescues/<ts>_<project>.tar.gz`. If the rescue itself fails -> CEILING exit 4 (refuse to apply restore without a recoverable state).
6. Dispatch runner based on `config.mode`. Runner crash/non-zero -> `fail` exit 2.
7. Healthcheck via `from healthcheck import check_tcp, check_http, check_curl_grep` (deployment module). On `ok=False` -> `rollback-warn` exit 3 (the bytes were restored, the live process did not come back; receipt states this).
8. If `include_code_rollback=true` AND `project=infinityops`: print §77 citation, invoke `gh workflow run deploy-vps.yml --ref <prev_sha>`. `prev_sha` from `vault/deploys/*_infinityops.md` latest receipt header. Record `code_rollback_invoked` + `code_rollback_ref` in output.
9. Write receipt to `vault/rollbacks/<ts>_<project>.md`.
10. STDIN BOM strip (PowerShell pipe defensive): `if raw.startswith("﻿"): raw = raw[1:]`.

`dry_run=True` short-circuits after step 4 (source selected, but no rescue, no runner, no healthcheck, no code-rollback, no receipt) and returns the plan as text.

## P8 -- `modules/rollback/test_v_block.py`

15 V-tests, all required PASS pre-seal:

| ID | Subject |
|---|---|
| `V-LIST-VERIFIED` | source_selector returns highest-mtime entry from a fixture manifest |
| `V-LIST-EMPTY` | manifest absent -> CEILING reason `manifest_absent` |
| `V-DRYRUN-RSYNC` | dispatcher dry-run on rsync-dir config -> verdict `dry-run`, plan in receipt, zero mutations |
| `V-DRYRUN-PGDUMP` | dispatcher dry-run on pg-dump config -> verdict `dry-run`, pg_restore plan visible |
| `V-CONFIG-INVALID` | config with forbidden-class key -> schema reject before runner |
| `V-CEILING-SSH-KEY` | ssh_key file absent -> CEILING exit 4 with explicit path message |
| `V-TARGET-NOT-FOUND` | `target_snapshot` is a name not on disk -> CEILING |
| `V-TARGET-UNVERIFIED` | `target_snapshot` exists on disk but is absent from manifest -> CEILING reason `target_unverified` |
| `V-RESCUE-CREATES` | `rescue_current=true` writes `vault/rescues/<ts>_<project>.tar.gz` BEFORE runner dispatch |
| `V-HEALTHCHECK-PASS` | mocked healthcheck returns ok -> verdict `pass`, receipt includes HC OK |
| `V-HEALTHCHECK-FAIL` | mocked healthcheck returns fail -> verdict `rollback-warn`, exit 3, receipt states failure |
| `V-NO-AUTO` | grep deploy.py for `rollback(` invocations -> zero call sites |
| `V-DOCTRINE-CITE-ROLLBACK` | infinityops + `include_code_rollback=true` dry-run -> §77 cite line in output |
| `V-CLOSED-LOOP` | output includes `previous_rollbacks` list, populated from `vault/rollbacks/*.md` glob |
| `V-TIMING` | dispatcher p95 dry-run wall-time < 500 ms |

## P9 -- `commands/rollback.md`

Eight-step Owner-facing protocol. `/rollback --project X` is the canonical invocation. `--list` prints verified snapshots. `--target <name>` selects a specific snapshot. `--rescue` opts in to pre-restore rescue. `--include-code-rollback` opts in to §77 gh-workflow re-trigger (infinityops only).

## P10 -- 3 configs in `vault/rollback/`

- `kobiicraft.json`: rsync-dir, gex44, post_restore_cmd `sudo systemctl restart kobiicraft@main`, tcp healthcheck on 5.9.23.174:25565.
- `tua-x.json`: pg-dump, vps204, pg_container tuax-postgres, http healthcheck on https://cw.infinityops.ai/.
- `infinityops.json`: pg-dump, vps204, pg_container infinityops-postgres, curl-grep healthcheck on infinityops.ai with grep token `br.jula`.

## P11 -- V-DEEP empirical receipt

Execute `python modules/rollback/rollback.py` with kobiicraft dry-run JSON over STDIN. Capture verdict, source selector output (expected CEILING `manifest_absent` because no backup has run yet), produce `vault/rollbacks/2026-05-25-HHMMSS_kobiicraft_dryrun.md` documenting the empirical state.

The V-DEEP value here is precisely that the CEILING fires correctly with the exact helpful message -- the spec's §2 invariant is exercised against a real empty state, not mocked.

## P12 -- Deploy Axis integration

In `modules/deployment/deploy.py`, on `verdict in {fail, deploy-warn}`, append to the summary string AND the receipt body:

```
To roll back: /rollback --project <X>   (NOT auto-invoked; Owner decides)
```

Add `V-ROLLBACK-SUGGEST` to deployment V-block: verifies the suggestion string is present in the receipt for fail-class verdicts. Add `V-NO-AUTO` rollback-side test (grep deploy.py for `rollback(` call) -- enforces §10.

## P13 -- Apex section + mirror

Append `## Rollback Axis (sealed 2026-05-25)` block to `knowledge_vault/core/apex-completion-standard.md` (PP source). Byte-mirror to live loose copy via Python `read_bytes` / `write_bytes`. Verify sha256 match.

## P14 -- UKDL + lessons

Append `UKDL-RB-01..05` + `UKDL-RB-REP-01` to `vault/knowledge_base/ukdl-universal.md`. Append Rollback cycle lessons `L1..Ln` to `vault/knowledge_base/session_lessons.md` (any error encountered during this cycle becomes a lesson row, per the standing iteration contract).

## P15 -- normalize_paths ALLOWLIST + verify_spp

Add to `tools/normalize_paths.py` ALLOWLIST: `vault/specs/rollback-skill.md`, `vault/plans/rollback-skill-2026-05-25.md`, `vault/rollback/*.json`, `vault/rollbacks/*.md`, `modules/rollback/test_v_block.py`, `commands/rollback.md`, `vault/rescues/` (directory pattern; receipts only, never the actual rescue bytes).

Run `python tools/verify_spp.py`. Target: exit 0, 7/7 STRICT PASS. Pre-existing FAILs (mirror-parity hook-dispatcher.js drift) documented as such in session_lessons.md with override authorization, mirroring the Backup Axis P16 row.

## P16 -- commit + push

Two commits:
1. `feat(rollback): Rollback Axis sealed -- deploy lifecycle complete` (all rollback files + spec + plan + configs + deploy integration changes).
2. `fix(allowlist): Rollback Axis paths + override authorization` (normalize_paths.py ALLOWLIST entries + session_lessons.md override row).

`git push origin main`. Confirm REMOTE_DELTA = 0.

## Done-gate (matches spec §16)

- All 15 V-tests PASS with documented evidence.
- `verify_spp.py` exit 0 (7/7 STRICT) or documented override.
- `verify_full_install.py` exit 0.
- Apex sealed + mirror sha256 match.
- UKDL + lessons present.
- V-DEEP receipt present.
- Deploy integration verified (V-ROLLBACK-SUGGEST + V-NO-AUTO PASS).
- `git push` succeeds, REMOTE_DELTA = 0.
