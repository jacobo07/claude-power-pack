# PP Hooks Setup -- One-Time Owner Registration

The Power Pack ships seven proactive agents at `~/.claude/agents/`
and a global UserPromptSubmit hook (`jit_skill_loader`) that fires
them on every prompt. Five additional hooks (PreToolUse, PostToolUse,
SessionStart, Stop) cannot be self-registered by Claude Code in
auto-mode because the classifier blocks writes to
`~/.claude/settings.json`. This is by design -- a malicious agent
should not be able to wire its own hooks.

The Owner runs the registration script **once**, from a terminal,
to enable the full PP proactive surface.

## Prerequisites

- Active Claude Code install with `~/.claude/settings.json` present.
- This Power Pack repo cloned at
  `~/.claude/skills/claude-power-pack`.
- Python 3.12+ available on PATH (or run with the absolute path on
  Windows: `C:\Users\User\AppData\Local\Programs\Python\Python312\
  python.exe`).
- Node.js (any LTS) available on PATH.

## Step 1 -- preview

```bash
cd ~/.claude/skills/claude-power-pack
python tools/register_global_hooks.py --dry-run
```

The script prints the five hook entries it would add, with the
real absolute paths, and exits without touching `settings.json`.

## Step 2 -- close every active Claude Code session

Hooks load once at session start. Re-running an existing session
will not pick up the new wiring; close all of them first.

## Step 3 -- commit the registration

```bash
python tools/register_global_hooks.py
```

The script:
1. Copies `~/.claude/settings.json` to
   `~/.claude/settings.pre-pp-hooks-<ts>.bak` (timestamped).
2. Appends only the missing entries (idempotent -- re-runs after a
   partial registration only add what is absent).
3. Writes the new `settings.json` atomically.
4. Prints the registered markers and the backup path.

If the script reports `[FAIL] Hook files missing on disk`, run it
again from the PP repo root and verify `hooks/` contains the four
`.js` files.

## Step 4 -- relaunch Claude Code, then verify

```bash
python tools/check_hook_status.py
```

Expected output: every hook marked `[OK]`, `jit_skill_loader` active,
all seven PP agents present, and (after the next session) the
"LAST ADVISORIES FIRED" section populated.

## What each hook does

| Trigger | Hook | Agent surface |
|---|---|---|
| You write a `.py` file (Write/Edit/MultiEdit) | `uqf_pre_edit_gate.js` | `pp-code-reviewer` + `pp-uqf-auditor` advisory when anti-patterns are detected in the new content. |
| You run a deploy command (`vercel deploy`, `kubectl apply`, `mix release`, `gh release create`, ...) | `osa_deploy_detector.js` | `omni-singularity` advisory recommending `/osa --audit`. |
| Bash output contains an error / traceback | `bug-hunter-ceps-bridge.js` | `pp-ceps-analyst` captures the snippet to CEPS and advises a recurrence query. |
| New Claude Code session starts | `tco_compact_gate.py --session-start-check` | `pp-tco-advisor` warns when context proxy is at >= 70%. |
| Claude finishes an assistant turn | `jobs_woz_gate.js` | Jobs/Woz judge flags slop-token signals in the output (advisory only). |
| Every prompt you send | `jit_skill_loader` (already active) | Full proactive dispatcher: `pp-tco`, `pp-monitor`, `pp-ceps`, `pp-code-reviewer`, `pp-uqf-auditor`, `pp-never-again` evaluators -- silence when no signal, capped at 3 advisories per turn. |

## Idempotency + safety

- The registration script uses unique marker strings
  (`uqf_pre_edit_gate`, `osa_deploy_detector`, etc.) to detect
  prior registrations. Running it twice leaves `settings.json`
  unchanged on the second run.
- Every commit is preceded by an automatic backup at
  `~/.claude/settings.pre-pp-hooks-<ts>.bak`.
- All hooks are **advisory-only**. They emit
  `additionalContext` blocks via `hookSpecificOutput`. None of
  them deny tool calls or block Stop / SessionStart.
- Each hook is **fail-open**: a Python subprocess error, a
  malformed JSON payload, or a missing module is swallowed and the
  hook exits 0 with no output.

## Rollback

Restore the backup if anything misbehaves:

```bash
cp ~/.claude/settings.pre-pp-hooks-<ts>.bak ~/.claude/settings.json
```

Then close + reopen Claude Code. The previous wiring is restored
exactly. The proactive agents under `jit_skill_loader` are
unaffected by this rollback (they are wired into UserPromptSubmit
by a separate, already-registered entry).

## Observability

- `vault/pp_agents/throttle/<agent>_<scope>.json` -- last_fire
  timestamp, last_advisory text, cumulative fire_count per
  (agent, scope) pair.
- `vault/ceps/events.jsonl` -- CEPS events captured by
  `bug-hunter-ceps-bridge.js`.
- `~/.claude/logs/jit-skill-loader.log` -- decisions made by the
  global UserPromptSubmit dispatcher.

## Quick reference

```bash
# Preview (no changes)
python tools/register_global_hooks.py --dry-run

# Commit
python tools/register_global_hooks.py

# Status snapshot
python tools/check_hook_status.py

# Restore prior settings.json
cp ~/.claude/settings.pre-pp-hooks-<ts>.bak ~/.claude/settings.json
```
