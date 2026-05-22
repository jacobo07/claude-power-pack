# Session Safety Contract

<!-- CANONICAL SOURCE — Power Pack repo (vault/contracts/). Deployed to
~/.claude/SESSION_SAFETY_CONTRACT.md by install-global.ps1 +
tools/install_global_core.py session-safety manifest. Edit here, re-run
install-global; never edit the deployed copy directly. -->

**Sealed 2026-05-21, revised 2026-05-22 (BL-SESSION-SAFETY-001) — UNIVERSAL LAW**

Triggered by the `4a600525` near-loss incident (2026-05-21) where an overconfident heuristic in `_oneshot_solitary_empty_shell_cleanup.js` classified a session-orchestrator `.jsonl` as an "empty shell" and archived it into `_empty_shells/`, despite the parent having a sibling `4a600525/subagents/` directory holding 1.69 MB of week-long KB-distillation work. The Owner's explicit directive: *"NO PERMITIR EN NINGUNO DE LOS CASOS DEL UNIVERSO"*.

---

## §1 — Sacred Invariant

**No `.jsonl` file inside `~/.claude/projects/` is ever destroyed, moved, renamed, or truncated by automation. Period.**

The only exceptions are the four sanctioned flows in §3. Any other path requires explicit Owner ratification, surfaced via `AskUserQuestion` with the destructive operation quoted verbatim.

This invariant overrides:
- "It looked empty"
- "It was idle"
- "It looked like a stub"
- "It seemed redundant"
- "The hook reported it as stale"
- Any heuristic, no matter how well-intentioned

A session is the user's conversation. Once on disk, only the user removes it.

---

## §2 — The Triple Defense

Three independent layers protect the invariant. **All three must fail simultaneously** for a session to be lost involuntarily.

### Layer 1 — Triple-Gated Cleanup (Author-Side)

`~/.claude/hooks/_oneshot_solitary_empty_shell_cleanup.js` (and any future cleanup script) MUST satisfy:

- **GATE 1 — Subagent isolation**: refuse to touch any `.jsonl` whose UUID has a sibling directory `<uuid>/` containing any file (subagents, tool-results, etc.). Such a sibling means the `.jsonl` is an orchestrator parent — its smallness is structural, not emptiness.
- **GATE 2 — Strict no-content**: zero user AND zero assistant entries (`type=user`/`type=assistant` or `message.role=user`/`message.role=assistant`).
- **GATE 3 — Zero-turn meta-attestation**: no `type=system, subtype=turn_duration` entry with `messageCount > 0`; no `type=system, subtype=away_summary` entry.

If ANY gate fails to confirm "empty shell" → skip. Always backup to `<proj>/_preserved/<uuid>.preserved-<ts>.jsonl` before moving. Move (never delete) to `<proj>/_empty_shells/<uuid>.jsonl`.

### Layer 2 — PreToolUse Guard (Runtime-Side)

`~/.claude/hooks/session-file-guard.js` runs on every Bash + PowerShell tool call. If the command contains:

- a destructive verb (`rm`, `del`, `erase`, `Remove-Item`, `Move-Item`, `Rename-Item`, `mv`, `ren`, `Clear-Content`, `Out-File`), OR
- a truncating redirect (`>` to a `.jsonl` path),

AND the target is inside `~/.claude/projects/**/*.jsonl`, AND the command does not contain a sanctioned-flow marker (§3), → `decision: block`, exit 2, with a verbose explanation.

Fail-OPEN by design: if the guard crashes or can't parse the command, it lets through AND logs to `~/.claude/state/session-guard-fail-open.log` for later audit. A buggy guard MUST NOT brick the agent — the snapshot backup (Layer 3) is the real bottom.

### Layer 3 — Daily Snapshot (Last-Resort)

Full snapshot of `~/.claude/projects/` to `~/.claude/backups/projects-snapshot-YYYY-MM-DD_HHmmss.zip`. Retention: 14 days rolling. Idempotent: re-run on same day overwrites.

Initial snapshot from the 4a600525 incident: `~/.claude/backups/projects-snapshot-2026-05-21_220036.zip` (385 MB, 4899 files, 71% compression).

**Implementation (2026-05-22, Paso 3.1+3.2 of session-safety-global plan):**

- **Canonical script**: `claude-power-pack/tools/session-snapshot.py` — pure Python (cross-platform-portable), `--dry-run` mode, 14-day rolling retention, same-day idempotent overwrite, file-in-use skip-and-continue. Empirically verified: 5305 files / 1462.6 MiB uncompressed → 380.9 MiB zip in ~57 s.
- **Schedule (Windows)**: `install-global.ps1` auto-registers a Windows Scheduled Task named `ClaudePP-SessionSnapshot` running daily at 03:00. Idempotent (`schtasks /F` overwrites if present). Manual run any time via `schtasks /run /tn "ClaudePP-SessionSnapshot"`.
- **Opt-out**: set environment variable `CLAUDEPP_SNAPSHOT_DISABLE=1` in the user/system scope. The script exits 0 with a single "DISABLED" line; the installer skips the task registration. Both layers honor the same env var for symmetry.
- **Rotation**: oldest snapshots beyond 14 are deleted on each run. Same-day re-runs OVERWRITE today's existing zip (not rotated) so the "today" zip is always current.
- **Manual one-off** (no schedule needed, run anywhere):
  ```
  python ~/.claude/skills/claude-power-pack/tools/session-snapshot.py
  ```
- **Status check**: `schtasks /query /tn "ClaudePP-SessionSnapshot" /fo LIST` shows next run + status.

**Cross-platform note**: the Python script is portable, but the Scheduled Task registration is currently Windows-only. POSIX hosts should add a cron entry manually (e.g. `0 3 * * * /usr/bin/python3 ~/.claude/skills/claude-power-pack/tools/session-snapshot.py`); a future installer pass will auto-detect crontab on macOS/Linux.

---

## §3 — Sanctioned Flows (the Guard's Allowlist)

The PreToolUse guard recognizes these markers in any command path and lets them through:

| Marker | Purpose |
|--------|---------|
| `_empty_shells/` | Archive flow — triple-gated, reversible (file is moved not deleted) |
| `_preserved/` | Backup flow — always-backup before any destructive op |
| `.jsonl.live` | **LEGACY** cloak rename `.jsonl ↔ .jsonl.live` from the retired `resume-hide-live.js`. No active hook produces new `.jsonl.live` files as of 2026-05-21 — the current `mark-live-session.js` (registered SessionStart + Stop) is append-only and never renames. Existing `.jsonl.live` files on disk are forensic-only; `lazarus-stub-recover.js` (BL-2026-05-21) may promote them back to canonical on a future SessionStart |
| `.jsonl.live.recovered-*` | Forensic backup of a legacy `.jsonl.live` that the 2026-05-21 marker rollout preserved when a same-UUID `.jsonl` already existed (collision case). Read-only — only the Owner ratifies removal |
| `.recovered-*` | Generic prefix for recovered-flow targets (broader than `.jsonl.live.recovered-*`) |
| `.shell.*` | Pair-recovery backup naming (orphanCleanup promotes `.live` over a stub `.jsonl` after the stub was renamed to `.shell.<ts>`) |
| `.bak.stub-*` | Pair-recovery alternate backup naming |
| `.stub-corrupt-*` | `lazarus-stub-recover.js` (BL-2026-05-21) forensic backup — when the vaccine detects a hook-stub-only canonical and promotes a sibling with real turns, the prior canonical is renamed `<uuid>.jsonl.stub-corrupt-<ts>` (never deleted) |
| `.stub-collision-*` | Shadow-stub naming (liveCloakSweep hides a stub-collision file from the picker) |
| `.bak-*` | Generic timestamped backup naming (legacy + ad-hoc backups) |
| `.preserved-*` | Preserved-flow target naming |
| `_archived/` | Archived dir (older sessions) |
| `_audit_cache/` | Audit cache dir (safe area) |

Any new flow MUST add its marker to the guard's `ALLOWLIST_MARKERS` array AND to this table. No marker = blocked.

**Discoverability is a sister-responsibility, NOT covered by §1's durability invariant.** A `.jsonl` that survives on disk but is invisible to `/resume` is loss-equivalent for the user — but the contract does NOT enforce that surface. Discoverability is enforced by:

- `~/.claude/hooks/lazarus-stub-recover.js` (BL-2026-05-21) — SessionStart hook that detects hook-stub-only canonicals and promotes sibling `.jsonl.live` / `.recovered-*` files with real turns
- `~/.claude/skills/claude-power-pack/hooks/mark-live-session.js` — SessionStart + Stop hook that visibly tags live sessions in `/resume` with `⚡ ` so the Owner can see (rather than hide) which panes are open
- `~/.claude/knowledge_vault/core/persistence-indestructible.md` — Lazarus resumption doctrine: every clean exit AND every crash is resumable via FIFO + 24h-window fallback

§8 below makes the discoverability promise explicit.

---

## §4 — Procedure on Suspected Loss

If a session appears missing from `/resume`:

1. **Don't panic** — Layer 3 has it.
2. Check `~/.claude/projects/<proj>/_empty_shells/<uuid>.jsonl` first.
3. Check `~/.claude/projects/<proj>/_preserved/` — there's a `<uuid>.preserved-<date>.jsonl` if the cleanup script touched it.
4. Check the sibling subagent dir `~/.claude/projects/<proj>/<uuid>/subagents/*.jsonl` — if the orchestrator parent was lost, the children may carry the conversation.
5. Restore from snapshot:
   ```powershell
   $snap = Get-ChildItem "$env:USERPROFILE\.claude\backups\projects-snapshot-*.zip" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
   Expand-Archive $snap.FullName -DestinationPath "$env:USERPROFILE\.claude\backups\_restore-staging" -Force
   # Then copy the specific .jsonl back into ~/.claude/projects/<proj>/
   ```
6. If even Layer 3 doesn't have it (e.g., session was created and lost on the same day, before that day's snapshot ran), check `~/.claude/state/session-guard-fail-open.log` for the time-window — that log records every fail-open + every block.

---

## §5 — Past Violations (Indexed Vaccines)

| Date | UUID | Cause | Vaccine |
|------|------|-------|---------|
| 2026-05-21 | `4a600525-7ade-4e52-a04b-a5b59714c472` | `isEmptyShell` heuristic only checked `type=user`/`type=assistant`; orchestrator parents with 0 turns in `.jsonl` but 1.7 MB in `<uuid>/subagents/` were classified as shells | §2 Layer 1 GATES 1+3 + §2 Layer 2 PreToolUse guard + §2 Layer 3 daily snapshot |

When a violation occurs, append a row here. Don't blame the heuristic — *write the vaccine*.

---

## §6 — Owner Override

The Owner can override §1 by issuing the exact phrase **"borra esta sesión <UUID>"** or **"delete session <UUID>"**. The agent then:

1. Reads back the UUID + its CWD + its size + its first user message verbatim.
2. Asks via `AskUserQuestion` for explicit confirmation.
3. Only after the Owner confirms, copies to `_preserved/` with `manual-delete-` prefix, then deletes.

No keyword-shortcut. No silent comply. Even an Owner-triggered delete leaves a `_preserved/` copy by contract.

---

## §7 — Out of Scope

This contract does NOT govern:
- Files outside `~/.claude/projects/`
- `.jsonl` files inside `_empty_shells/` or `_preserved/` (those are already archive zones — secondary archival/cleanup is fine there with normal heuristics)
- Files in `~/.claude/lazarus/`, `~/.claude/state/`, `~/.claude/skills/` (separate concerns)
- The user's own manual `rm` from a terminal outside the agent (the agent cannot enforce policies on the human at the keyboard)

---

## §8 — Discoverability Guarantee (added 2026-05-22)

**A `.jsonl` that survives on disk but cannot be reached via `/resume` is loss-equivalent for the user.** Durability without discoverability is a partial promise; the user has not lost their conversation in a forensic sense, but they have lost it in a functional sense. This contract covers both.

The §1 Sacred Invariant guarantees durability. §8 names the actors that guarantee discoverability — without §8, durability alone is insufficient:

| Failure mode | Symptom | Responsible actor |
|---|---|---|
| Canonical `.jsonl` populated only with hook-stubs; real turns in sibling `.jsonl.live` | `/resume` returns "No conversation found" or shows a session with no turns | `~/.claude/hooks/lazarus-stub-recover.js` (BL-2026-05-21) — SessionStart hook, promotes sibling with real turns to canonical, renames stub to `.stub-corrupt-<ts>` |
| Live session visually indistinguishable from idle/dead in `/resume` picker | Owner cannot tell which panes are currently open; risk of accidental double-resume | `~/.claude/skills/claude-power-pack/hooks/mark-live-session.js` — appends `⚡ <title>` `custom-title` record on every Stop; orphan-sweeps dead `⚡` markers |
| Crashed session has no FIFO entry after Cursor relaunch | Manual `/lazarus` required even though crash should auto-resume | `lazarus-resolve-fallback.ps1` (per `knowledge_vault/core/persistence-indestructible.md`) — 24h `clean_exit`/`revived` window fallback when FIFO empty |
| Heartbeat stale during long idle → snapshot missed | Recovery succeeds but with outdated context | `lazarus-heartbeat.js` wired on PreToolUse + UserPromptSubmit + SessionStart + Stop; 90 s live-window for fast crash detection |

**Discoverability done-gate**: zero "No conversation found with session ID …" across the four loss vectors of §4 + the §8 failure modes above. The clean-install crash matrix in `vault/plans/session-safety-global-2026-05-22.md` is the canonical empirical test.

**Why §8 is sister to §1, not a sub-section of it**: §1 prohibits automation from destroying the file; §8 obligates automation to keep the file findable. Different verbs, different actors, different failure modes. Both are required for "never lose a session involuntarily".

---

**Authority**: this contract is canonical for any agent operating in this environment. Pinned reference from `~/.claude/CLAUDE.md` (the pin itself is enforced by `claude-power-pack/install-global.ps1` post-2026-05-22 — see plan `vault/plans/session-safety-global-2026-05-22.md`). Conflicts with anything else → this contract wins on session-file-touching matters.
