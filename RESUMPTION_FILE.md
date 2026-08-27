# RESUMPTION — observation surface closure

**Repo** `~/.claude/skills/claude-power-pack` · **branch** `frontier28/session-2026-08-26`
· **worktree** an isolated one; the main checkout is on another pane's branch and must not
be switched.

**Thesis.** An instrument can be accurate and blind. The CEPS producer was registered,
firing, recording and losing nothing while observing about a quarter of its subject,
because the entry carrying its name matched `Bash` on a host whose doctrine routes python,
pytest, git, npm, node, mix and gh through PowerShell.

## State

Sealed: coverage is measured, not assumed (`capture_liveness.py` rule 4 — declared
surfaces vs matched surfaces, declared discovered from the hook's own source). The
migration that would close the gap is written, dry-run clean, and refuses any registration
whose code rejects the surface. The benchmark that timed a refusal now times the record
path against a real-corpus fixture. Two roots that were `$HOME`-hardcoded now derive from
their own location, which ended a test that wrote production and proved it had not.
Dispatcher divergence fails instead of being narrated. An adversarial pass found 14
defects in the above; all fixed.

Coherence anchor: `python tools/capture_liveness.py` exits 1 naming **PowerShell
unobserved** for two producers. That is the gap, still open, visible by design.

## Owner actions — the only things blocking closure

1. `python tools/migrate_capture_surface.py --apply` — widens two registrations
   (`bug-hunter-ceps-bridge.js`, `PreToolUse-Bash-chain`). Backup-first, idempotent,
   reversible. Refused by the auto-mode classifier (HR-001), correctly.
   The second one restores HR-CASCADE-001..005 on PowerShell, where
   `Remove-Item -Recurse -Force` is actually written.
2. Copy `hooks/hook-dispatcher.js` to `~/.claude/hooks/` — `session_delta_stop.js` and
   `closer-guard.js` diverge between the canonical copy and the one that runs.
3. 144 path rewrites plus 18 doctrine/security lines, unchanged from the prior session.

## Next three actions

1. After action 1, re-run `capture_liveness.py`; it must flip to COVERED, and
   `test_correctness_traps.py` must go 8/8 on its own.
2. Then watch the corpus: real traffic through the new surface should broaden the
   subsystem distribution beyond `bash:*`. Until it does, coverage is configured, not
   proven.
3. Re-derive `ceps_record_ms` when the corpus has grown materially — the append is
   O(corpus) and the probe now moves with it, deliberately.

## Start instruction

Read `vault/plans/observation-coverage-2026-08-27.md`, then run
`python tools/capture_liveness.py --window-days 30`. Its output is the current truth.
Do not trust any coverage claim in prose over that command.
