---
title: Live-Session Marker — replaces resume-hide-live cloaking
tags: [standard, sessions, resume, power-pack]
tier: standard
status: shipping
supersedes: BL-0013 (resume-hide-live.js .jsonl-rename approach)
sealed: 2026-05-21
---

## What changed

The legacy mechanism (`~/.claude/hooks/resume-hide-live.js`, BL-0013, 2026-05-01)
hid currently-live Claude sessions from the native `/resume` modal by renaming
`<uuid>.jsonl` → `<uuid>.jsonl.live`. The picker filters on `endsWith(".jsonl")`
so live sessions disappeared from the list. Two problems:

1. **Crashed sessions vanish until orphan-cleanup re-runs.** The 3-layer
   discriminator added 2026-05-21 reduced the leak but kept the failure mode:
   any classifier drift means the user loses sessions from the picker entirely.
2. **The user can't see their own context.** Active sessions are invisible by
   design — you can't tell which panes are open without `Get-Process`.

The replacement (`claude-power-pack/hooks/mark-live-session.js`) keeps every
session visible in `/resume` and tags the live ones by appending an `custom-title`
record prefixed with `⚡ ` to the session's `.jsonl`. The native picker renders
the latest `custom-title` verbatim, so the live marker shows up in the modal
without any picker modification.

## Mechanism

- The native `/resume` picker scans `~/.claude/projects/<proj>/<uuid>.jsonl`
  and reads the **latest** `{"type":"custom-title", ...}` record per file.
- `.jsonl` files are append-only by harness convention. Both the harness and
  our hook can append concurrently — each append-mode write is atomic for
  sub-PIPE_BUF payloads on Windows.
- On **Stop** (every assistant turn), the hook checks the current last
  `custom-title`. If it does not start with `⚡ `, the hook appends a new line
  `{"type":"custom-title","customTitle":"⚡ <base-title>","sessionId":"..."}`.
- On **SessionStart** and on every Stop, the hook runs an orphan sweep:
  for every `.jsonl` whose last `custom-title` carries the `⚡ ` prefix AND
  whose session is no longer alive (3-layer gate below), it appends a
  strip-line restoring the base title.

## Liveness discriminator (3-layer gate, fail-open)

Same gate as the patched `resume-hide-live#isOrphanedDead`. Documented at
`vault/lessons/discriminator-on-missing-external-dep.md` (cross-reference).

1. `mtime(<uuid>.jsonl) <= 300 s` → **ALIVE** (recent assistant turn).
2. UUID present in any live `claude.exe` / `node.exe` command line
   (`Get-CimInstance Win32_Process`, ~300 ms scan, cached per hook invocation)
   → **ALIVE** (idle-but-running).
3. `~/.claude/lazarus/<proj>/sessions/<uuid>.json.timestamp <= 300 s`
   → **ALIVE** (recent stop_hook write).
4. else → **DEAD** — append a strip-line restoring the base title.

Fail-open: if the PowerShell scan errors out (missing binary, timeout, perms),
the sweep falls back to mtime + index alone. Bias is toward un-marking rather
than over-marking — a stuck `⚡ ` is never permanent.

## Activation (Owner-run, opt-out by default)

This is the Power Pack default for `/resume` discoverability. Activate once
per host with the consolidator:

```
python ~/.claude/skills/claude-power-pack/tools/settings_merger.py \
  register-mark-live-session
```

Wires SessionStart + Stop in one idempotent call (re-runs are no-ops). Takes
effect on the next `/restart` (per `~/.claude/CLAUDE.md` → "settings.json
session-load" rule).

To preview without writing:

```
python ~/.claude/skills/claude-power-pack/tools/settings_merger.py \
  register-mark-live-session --dry-run
```

The hook script is registered directly at the Power Pack repo path
(`~/.claude/skills/claude-power-pack/hooks/mark-live-session.js`) — no copy to
`~/.claude/hooks/`, matching the RTK pattern (BL-0070). One source of truth,
no split-brain.

## Decommissioning the legacy hook

When `register-mark-live-session` runs, the Owner should also unregister the
legacy `~/.claude/hooks/resume-hide-live.js` from `~/.claude/settings.json`
SessionStart and Stop. The merger does not currently provide an unregister
subcommand — surgical edit:

1. Open `~/.claude/settings.json`.
2. Remove the two matcher blocks whose `command` references
   `resume-hide-live.js` (one in `hooks.SessionStart[]`, one in `hooks.Stop[]`).
3. Restore any leftover `<uuid>.jsonl.live` files: rename back to
   `<uuid>.jsonl` if no collision, else preserve as
   `<uuid>.jsonl.live.recovered-<yyyymmdd-hhmmss>` for manual inspection.
   PowerShell one-liner is in the commit message of the rollout PR.

## Properties

- **Idempotent**: re-marking a live session is a no-op (last `custom-title` already
  has the prefix → skip).
- **Crash-safe**: every IO is wrapped; hook never throws, always `exit(0)`.
- **Concurrency-safe**: append-only writes never collide with the harness's
  held fd. Atomic per-line on Windows for sub-PIPE_BUF payloads.
- **Self-healing**: a stuck `⚡ ` from a crashed session gets stripped on the
  next Stop or SessionStart anywhere on the host (orphan sweep).
- **Resurrection-friendly**: nothing is ever hidden; Lazarus picker, native
  picker, and any future picker all see every session.

## Cross-references

- Hook: `claude-power-pack/hooks/mark-live-session.js`
- Consolidator: `claude-power-pack/tools/settings_merger.py` → `register-mark-live-session`
- Supersedes: `~/.claude/hooks/resume-hide-live.js` + BL-0013
- Lesson (discriminator): `vault/lessons/discriminator-on-missing-external-dep.md`
- Picker contract evidence: `~/.cursor/extensions/anthropic.claude-code-<v>/extension.js`
  (search `endsWith(".jsonl")` and the custom-title rendering path)
