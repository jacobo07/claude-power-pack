# Rollback receipt -- kobiicraft (V-DEEP self-test, dry-run; empirical CEILING)

- Timestamp (UTC): 2026-05-25-155500
- Duration: 0 ms (CEILING short-circuit at source selector; no runner, no healthcheck)
- Verdict: ceiling (exit 4)
- Mode: rsync-dir (config loaded; selector ran before runner)
- SSH alias: gex44 (resolved from vault/rollback/kobiicraft.json)

## 1. Invocation

```
echo '{"project_root":".", "project":"kobiicraft", "dry_run":true}' | python modules/rollback/rollback.py
```

## 2. Empirical STDOUT

```json
{
  "verdict": "ceiling",
  "exit_code": 4,
  "mode": "rsync-dir",
  "duration_ms": 0,
  "summary": "source selector CEILING: manifest_absent -- manifest absent at C:\\Users\\User\\.claude\\skills\\claude-power-pack\\backups\\kobiicraft\\manifest.json. No verified backup exists for 'kobiicraft'. Ensure a /backup --project kobiicraft has run successfully (verdict=pass) before invoking /rollback.",
  "source_selector": {
    "ok": false,
    "reason": "manifest_absent",
    "evidence": "manifest absent at C:\\Users\\User\\.claude\\skills\\claude-power-pack\\backups\\kobiicraft\\manifest.json. No verified backup exists for 'kobiicraft'. Ensure a /backup --project kobiicraft has run successfully (verdict=pass) before invoking /rollback."
  }
}
```

## 3. V-DEEP empirical evidence

This receipt is the artefact of P11 in the Rollback Skill plan
(`vault/plans/rollback-skill-2026-05-25.md`). It captures the following
empirical facts on the real PP repo state as of 2026-05-25:

1. The dispatcher correctly loaded the rollback config from
   `vault/rollback/kobiicraft.json` (PP source). Schema validation
   passed (mode=rsync-dir, no credential-class keys present).

2. The source selector ran and CORRECTLY refused to proceed because
   `backups/kobiicraft/manifest.json` does not exist on disk. The PP
   `backups/` directory is gitignored AND no real `/backup --project
   kobiicraft` has executed yet (only the dry-run V-DEEP receipt from
   the Backup Axis P12 exists, which by design does not write bytes
   or populate a manifest).

3. The CEILING message includes the EXACT remediation instruction the
   Owner needs: `Ensure a /backup --project kobiicraft has run
   successfully (verdict=pass) before invoking /rollback.` -- no
   ambiguity, no cryptic error, no fallback to a stale snapshot.

4. Exit code 4 (`EXIT_CEILING`) emitted, propagating to the shell.

5. The dispatcher did NOT mutate disk: no rescue, no runner
   invocation, no receipt auto-written by the receipt-writer. The
   present file is a manually-curated V-DEEP artefact; the automated
   receipt-writer engages only AFTER the runner has acted.

## 4. Reality contract reaffirmed

- A rollback that cannot identify a verified source IS NOT a rollback.
  The spec sec 2 invariant -- "a snapshot not in the manifest is treated
  as absent" -- is empirically enforced here against a literally absent
  manifest, not a mocked one.

- The CEILING is the correct outcome. A FAIL would imply we tried and
  failed; we did neither -- we identified that the precondition for a
  safe rollback is not met and stopped before doing harm.

- The sister axis path is the fix: once `/backup --project kobiicraft`
  has run successfully (verdict=pass), `backups/kobiicraft/manifest.json`
  will exist with sha256 entries, and this exact same `/rollback
  --project kobiicraft --dry-run` invocation will return verdict
  `dry-run` exit 0 with the planned tar+ssh command in the receipt.

## 5. Snapshot of the dispatcher state on this run

- `CLAUDEPP_ROLLBACK_DISABLED`: not set
- `target_snapshot`: null (would have selected latest verified, but manifest absent)
- `rescue_current`: false
- `include_code_rollback`: false (not infinityops anyway)
- Manifest location probed: `backups/kobiicraft/manifest.json` (relative to project_root)
- Source selector reason: `manifest_absent`

## 6. What this V-DEEP run does NOT verify

This dry-run does NOT verify:
- The runner actually streams bytes to gex44 (would require a verified
  snapshot to source from -- the precondition of this whole spec).
- The TCP healthcheck on 5.9.23.174:25565 actually connects (requires a
  live MC server, the gex44 VPS, which the Owner controls).
- The post_restore_cmd `sudo systemctl restart kobiicraft@main` actually
  cycles the service (requires sudoer + systemd-aware host).

Those are verified empirically once an actual snapshot exists. The V-block
fixture-based tests verify the dispatcher logic at every fork; this
V-DEEP receipt verifies that the dispatcher REFUSES TO ACT when the
real-world precondition is unmet.
