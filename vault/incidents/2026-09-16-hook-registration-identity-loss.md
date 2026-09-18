# Incident: hook registration identity loss (2026-09-16 20:02 → 2026-09-18 13:55)

**Class:** HOOK REGISTRATION IDENTITY LOSS → SILENT GLOBAL CAPABILITY BYPASS.
Every Power Pack dispatcher chain became unreachable from real sessions while the
dispatcher, the hook sources and every test suite stayed healthy. Nothing was
broken except the one field that routes an event to its chain.

## Timeline (local time, CEST; UTC in parentheses)

| when | what | instrument |
|---|---|---|
| 09-16 19:42:43 | last known good `settings.json` bytes (kept as `settings.json.bak-20260916-200232`) | backup mtime + semantic diff |
| 09-16 20:00:32 | writer stages `%TEMP%\settings.fixed.json`; `Copy-Item` later carries this mtime onto the live file, which is why earlier forensics dated the break to 20:00:32 | backup `bak-20260916-200509` mtime |
| **09-16 20:02:24–36 (18:02:24Z)** | **first bad write: session `2174d82b` applies the file on "hazlo tu por mi"** | the writer's own transcript |
| 09-16 20:01:08 (18:01:08Z) | last real-session Stop-chain row before the break | `logs/context-watchdog.log` |
| 09-16 20:05 / 20:06 | same session re-reads with PS 5.1 ANSI and rewrites twice (async flags) → mojibake layers 2 and 3 | backups 200509, 200610 |
| 09-16 → 09-18 | ~150 watchdog rows, **all synthetic** (`gsdac-*`, `gsdlr-*`, `budget-probe`); zero real-session Stop rows | session-id census |
| 09-18 12:44:39 | this pane launches; `kclaude` → `fix_conhost_hook_leak.py` strips Orca conhost wrappers (argv-safe, benign) | backup `bak-20260918-124439` |
| 09-18 13:39:17 | Orca X.exe launch rewrites the file (Node writer, no hook semantics changed) — a live concurrent writer during the repair | CreationTime + semantic diff |
| **09-18 13:55:50** | **repair applied** (8 argv tails restored, 15 mojibake strings reversed), backup `settings.json.bak-20260918-135550-pre-incident-repair` (sha `3066fe63…`) → live sha `49402dc0…` | repair script, compare-and-swap |
| 09-18 13:56:38 | first GSD X tier judgement after repair, from a session started **before** it | `state/gsd-x-heartbeat.json` |
| 09-18 13:59:22 (11:59:22Z) | first real-session Stop-chain row after repair | watchdog log |
| 09-18 ~14:30 | fresh `claude -p` session routes a real Bash event through `--event=PreToolUse-Bash-chain` and is denied by the bridge guard | canary |

## Root cause

The writer was an agent, not a tool. Session `2174d82b` was fixing a real problem —
14 `$(for n in …)` bash shims that spawned Git Bash on every hook call — by converting
48 shell-string hooks to exec form (`command` + `args`). Its PowerShell regex captured
only the quoted `.js` path, so **everything after the path was dropped**:

- the six dispatcher identities `--event=PreToolUse-Bash-chain | PreToolUse-Edit-chain |
  PreToolUse-Read-chain | PostToolUse-default | Stop-chain | UserPromptSubmit-chain`;
- `research-domain-guard.js --event=pre` / `--event=post`.

Its verification checked "parses, event counts match, Orca refs = 0" — every one true.
**No check compared argv before and after.** The same script read the file with
`Get-Content -Raw` (ANSI on PS 5.1) and wrote `ConvertTo-Json`, adding a mojibake layer
to `autoMode` text on every pass.

The earliest causal divergence is not the regex; it is that **settings.json had no
semantic contract**. Any writer — agent script, Orca installer, CPP's own
`fix_conhost` — could change what a hook receives and still pass every check.

## Why it was invisible for 42 hours

1. **Success-shaped silence.** `hook-dispatcher.js` answered a registration with no
   `--event=` with `{}` / exit 0 — "every hook passed" to the host.
2. **The monitors were hooks.** closer-guard, the context watchdog and the GSD X tier
   hook are all dispatcher chains; they went dark with the substrate they watch.
3. **Synthetic traffic in production logs.** Test drivers wrote ~150 rows into the
   production watchdog log during the dark window, so the log looked alive.
4. **Every suite tested components, none the live registry.** Manual dispatcher runs
   with `--event=` succeeded; the host never sent one.

The handoff's hypothesis that old sessions kept hooks via a start-time snapshot and
concealed the break is **contradicted**: on this Claude Code build running sessions
pick up hook edits live (see GSDX-I03 / I10). All sessions went dark together, and all
came back together.

## Repair and controls

| control | where | evidence |
|---|---|---|
| settings repaired, unrelated state preserved | `~/.claude/settings.json` (not in git) | dry run then CAS apply; readback equal; 0 unrelated diffs |
| no-event is CONFIG_INVALID, never `{}` | `hooks/hook-dispatcher.js` (commit `9b536df`, live mirror SHA `C08558B1…`) | mutant restoring `{}` fails exactly 2 clauses |
| registry gate (static + runtime) | `tools/test_hook_registration_integrity.py` | 15/15; red on the real pre-repair file |
| launch-time detection outside the substrate, detect-only | `bin/kclaude.ps1` ↔ `tools/kclaude.ps1` (commit `e58b6af`) | green live, red + INVALID receipt on fixture |
| producer argv contract + CAS | `tools/fix_conhost_hook_leak.py`, `tools/test_settings_writer_argv.py` | 5/5; both mutants caught |
| replay isolation | `tools/test_hook_replay_isolation.py` (commit `5dfbda4`) | 1/1 with scanner positive control |
| umbrella rows | `tools/verify_spp.py` (commit `098f564`) | 3 rows green |

## Production reality grades

| grade | status |
|---|---|
| SETTINGS_REPAIRED | yes |
| STATIC_REGISTRATION_VERIFIED | yes |
| DISPATCHER_SIX_EVENT_VERIFIED | yes (as-written argv, synthetic payloads) |
| SECURITY_GATE_BEHAVIOR_VERIFIED | yes — fake-key Write denied (direct + no-event recovery path); git-via-Bash denied |
| FRESH_SESSION_VERIFIED | yes — Bash chain via host path; Edit-chain denial in a fresh session **not** shown (model refused first) |
| ACTIVE_SESSIONS_RESTARTED | not required — live pickup measured |
| RECURRENCE_PROTECTED | detect at launch + per event; **not** prevented against an arbitrary writer |

## Security exposure

CONFIRMED POLICY BYPASS for the window. NO EVIDENCE OF SECRET EXPOSURE through
Write/Edit/MultiEdit/NotebookEdit inputs (4,273 calls, one credential-shaped match — a
header-only refusal fixture in a TUA-X test). **Not assessed:** writes performed via
Bash/PowerShell, and reads the secret read-guard would have blocked.

## Open debt

- Writers outside CPP (ad-hoc agent scripts, Orca X installer) are still not bound to
  the argv contract; only detection covers them.
- Synthetic drivers (`gsdac-*`, `gsdlr-*`, `budget-probe`) still write the production
  watchdog log; their files were dirty under another live pane and were not touched.
- Orca's `claude-hook.cmd` exits without draining stdin when its env vars are unset
  (the stdin-hang shape) — belongs in the Orca X repo.
- Headless `-p` sessions add no GSD X tier judgement; unexplained.
- Long-horizon mission health does not yet consume these signals (GSDX-I08).

## Do not re-litigate without new evidence

- The writer is session `2174d82b`'s ad-hoc exec-form script, not `fix_conhost` nor `settings_merger`.
- Exec form is correct and stays; only the argv tails were wrong.
- Hooks reload live in running sessions on this build.
- Repair is detect-only at launch by decision (GSDX-I05); do not add auto-restore.
