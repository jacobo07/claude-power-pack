# Power Pack — 5-minute Global Install

This is the first thing a brand-new user runs. It installs the
Claude Power Pack into `~/.claude/` so every project on this host
inherits its agents, commands, doctrine, and verifiers. Total wall
clock: ~5 minutes on a warm host, longer for first-time Python /
Node setup.

> **You are here:** you cloned the repo, you have not yet run any
> installer, and `~/.claude/agents/oneshot-architect-auditor.md`
> does **not** exist on your machine. If both `agents/` and
> `commands/` already match the repo, you do not need this guide —
> jump to `docs/INSTALL.md` for the Programmatic Budget Layer
> (RTK + JIT) activation, which is a separate, opt-in step.

## Prerequisites

| Tool         | Version | Why it is required                       |
|--------------|---------|------------------------------------------|
| `python`     | ≥ 3.10  | All Power-Pack tooling (`tools/*.py`).   |
| `node`       | ≥ 20    | Hooks and L3 engine (`modules/*/*.js`).  |
| `claude.exe` | current | The harness itself.                      |
| `git`        | any     | Cloning + `git -C` integrity checks.     |

On Windows the global installer auto-detects `python.exe` via PATH
(or honors `$env:CLAUDE_PY_EXE`). On POSIX it tries `python3` then
`python`. If neither resolves, the wrapper exits `5` with a clear
message — no silent degraded mode.

## The five steps

```powershell
# 1. Clone the repo (anywhere — the global installer reads from THIS path).
git clone https://github.com/<you>/claude-power-pack.git
cd claude-power-pack

# 2. Dry-run first. ALWAYS. This previews every action without writing.
.\install-global.ps1 -DryRun        # Windows
./install-global.sh --dry-run       # POSIX

# 3. Real install. Idempotent (SHA-skip); safe to re-run.
.\install-global.ps1                # Windows
./install-global.sh                 # POSIX

# 4. Restart Claude Code so the newly-deployed agents + hooks
#    cold-load. Agents do NOT hot-reload; this step is mandatory.
/restart

# 5. Verify. Exit 0 = S++ baseline reached.
python tools\verify_spp.py
```

The installer prints two checklists at the end — a **permissions
checklist** (settings rules the harness's auto-mode classifier
refuses to write programmatically; you paste them yourself once) and
a **hooks checklist** (the few `~/.claude/hooks/<file>.js` writes
that classifier policy reserves for hand-copy). Follow both. After
you do, re-run step 5; the row count of `OK` will rise.

## Per-project vs per-user: which installer do I want?

| Question                                              | `install.{ps1,sh}` (per-project)        | `install-global.{ps1,sh}` (per-user)    |
|-------------------------------------------------------|------------------------------------------|------------------------------------------|
| **What does it touch?**                               | `<project>/CLAUDE.md`, `<project>/.claude/`. Never `~/.claude/`. | `~/.claude/agents/`, `~/.claude/commands/`. Never the project tree. |
| **When do I run it?**                                 | Once per repository, after you `cd` into it. | Once per host (or whenever you pull a new Power-Pack revision). |
| **Does it need `/restart`?**                          | No — per-project files load on next prompt. | Yes — agents + hooks cold-load only at session start. |
| **Idempotent?**                                       | Re-running overwrites the project doctrine block (warning printed first). | SHA-skip; identical files report `unchanged`. |
| **Backups?**                                          | Single `.claude.bak` rotation.            | `~/.claude/.pp-backups/<iso>/`, retention 5 (audit gap 11). |
| **Permissions?**                                      | Adds project-scoped allow-rules.          | **Never** writes permissions. Prints the rules you paste. |
| **Hooks?**                                            | No hooks (per-project skill files only).  | **Never** writes hooks. Prints a copy-checklist (Lesson 1 / Mirror-Sync-Direction doctrine, 2026-05-19). |
| **Verifier?**                                         | None — project tooling decides.           | `tools/verify_spp.py` covers all 7 rows. |

Rule of thumb: **install-global first, install (per-project) second.**
A per-project install before the global one boots into a host that
has no Power Pack agents and no verifiers, so half its doctrine
references dangle.

## Restoring from a backup

The global installer writes every overwritten file as
`~/.claude/.pp-backups/<iso>/<relpath>` before writing the new
copy. The five most-recent runs are retained; older ones are
pruned in-place at install time.

```powershell
# List available backup sets, newest first.
ls $env:USERPROFILE\.claude\.pp-backups | Sort-Object Name -Descending

# Restore a specific file from a specific run.
Copy-Item `
  $env:USERPROFILE\.claude\.pp-backups\2026-05-19T12-03-44Z\agents\oneshot-architect-auditor.md `
  $env:USERPROFILE\.claude\agents\oneshot-architect-auditor.md
```

POSIX is symmetrical with `ls` / `cp`. There is no `pp-restore` CLI;
the directory layout is the contract, and a shell one-liner is the
intended UX.

## Troubleshooting (top-3)

1. **`install-global.ps1: cannot find python.exe`** — install
   Python 3.10+ from python.org (NOT the Microsoft Store stub) or
   set `$env:CLAUDE_PY_EXE` to the absolute path of the interpreter.
   The wrapper does not silently fall back.
2. **`verify_spp.py` reports `paths+secrets` FAIL with N hits** —
   you are looking at the verifier doing its job. The hits are
   real path-leaks or VPS-IP residues in PP-internal docs; they do
   not block your global install, but they are tracked follow-ups
   in `docs/REMAINING_WORK.md`. Re-run with `--row mirror-parity`
   to confirm the install-side gates are green independently.
3. **Agents do not appear after install** — you skipped `/restart`,
   or you ran `/restart` in a window that landed on a different
   session (a known harness limitation; see `MEMORY.md` →
   "Agent files cold-load like hooks"). Close every Claude window,
   start a fresh one, and re-run `python tools/verify_spp.py`.

## What "S++" means here

`tools/verify_spp.py` exit 0 = every strict row green:

- `mirror-parity` — every PP-tracked `~/.claude/` file matches its
  repo canonical (LF-normalised SHA-256).
- `drift-report` — no PP↔loose pair is in `loose-ahead` or
  `pp-ahead` state.
- `paths+secrets` — no hardcoded user-paths or VPS secrets in code.
- `rtk-fusion` — the RTK output-compression hook is wired and
  measuring ≥60 % on the canonical `git log --stat -50` probe.
- `intent-lock` — the concurrent-pane mutex passes its self-test.
- `l3-engine` — the L3 compound-learnings detached subagent passes
  its harness probe.
- `programmatic-budget` (advisory) — Owner-side; surfaces only if
  the budget config + telemetry are already populated.

If any strict row is red, the umbrella exits 1 and points you at
the specific row. Re-run individual rows with
`python tools/verify_spp.py --row <name>`.

---

Sealed 2026-05-19 (BL-0069 / Apex Onboarding Standard, doctrine).
Snowball lessons referenced: Lesson 1 (chunked-edit-on-internal-error),
Lesson 2 (installer prints rather than writes capability grants).
