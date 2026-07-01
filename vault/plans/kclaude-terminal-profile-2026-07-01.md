# kClaude Cursor Terminal Profile — 2026-07-01

Status: **Shipped (settings.json edited + validated)** · Owner visual gate pending
Mode: EXECUTION

## Objective

Add a `kClaude` terminal profile to Cursor's `+` menu that launches the **smart**
W6 wrapper (`~/.claude/bin/kclaude.ps1`) with the same icon/color as the existing
`Claude` profile, positioned between "Last session (Default)" and "Claude".

## Premise corrections (audit-disproves-premise)

Two assumptions in the source prompt were disproved by reading the real state
before editing:

1. **"The `Claude` profile launches `claude.exe` directly."** — FALSE. It launches
   `${env:USERPROFILE}\.claude\kclaude.bat` (line 98 of settings.json): the OLD,
   simple restart wrapper (`claude %*` + /restart flag loop). It does NOT run the
   pre-launch intelligence.
2. **The smart wrapper `~/.claude/bin/kclaude.ps1`** (W6 orchestrator: W1 context
   pressure, W4 same-repo coordinator, W5 cost gate, W2 auto-resume, W3 background
   session naming, plus the /restart loop that supersedes kclaude.bat) was **not
   wired into any terminal profile.** Reachable only via `~/.claude/bin/kclaude.cmd`.

Owner INTENT honored: the new `kClaude` profile is the one that launches the smart
`kclaude.ps1` orchestrator. The literal `claude.exe` premise was corrected.

3. **"SCS C49 defines a Cursor Startup Protocol doc — add an addendum."** — There is
   no SCS ledger FILE in the repo; "SCS C49" appears only in session `.jsonl`
   transcripts. Intent recorded here + in UKDL instead of inventing a file.

## What shipped

`%APPDATA%\Cursor\User\settings.json` — new first key under
`terminal.integrated.profiles.windows`:

- `path`: Sysnative/System32 `cmd.exe` (identical host to `Claude`)
- `args`: `/K`, `${env:USERPROFILE}\.claude\bin\kclaude.cmd`,
  `--exclude-dynamic-system-prompt-sections`, `--no-chrome`
- `env`: `FORCE_COLOR=1`, `NODE_NO_WARNINGS=1`, `CLAUDE_CODE_DISABLE_TELEMETRY=1`
- `icon`: `sparkle` · `color`: `terminal.ansiMagenta` — byte-identical to `Claude`,
  so the menu glyph/color is visually the same (no "raro" white icon).

`terminal.integrated.defaultProfile.windows` UNCHANGED (`Last session`).
Backup written to `settings.json.bak.20260701T130248Z` before editing.

## Launch chain (proven)

`cmd /K` → `bin\kclaude.cmd` → `powershell -File bin\kclaude.ps1 <args>` → `claude`.
- Arg passthrough verified: `--exclude-dynamic-system-prompt-sections --no-chrome`
  bind cleanly to the `[ValueFromRemainingArguments] $ClaudeArgs` param (empirical
  throwaway-script test: COUNT=2, both flags present).
- Chain executes + returns verified: `kclaude.cmd -h` printed the wrapper help
  (proves cmd→powershell→ps1→param-binding all resolve).
- Overhead: `kclaude.ps1` runs W1+W4+W5+W2 in ONE python process
  (`modules/wrapper/prelaunch.py`) with per-feature timeouts, header-documented
  budget `< 2s`, fail-open absolute.

## Done-gate

- [x] `kClaude` profile added, JSONC still valid (comment-tolerant parse PASS)
- [x] icon=`sparkle` color=`terminal.ansiMagenta` (identical to `Claude`)
- [x] `defaultProfile.windows` still `Last session` (default not broken)
- [x] launch chain cmd→cmd→ps1→claude proven; args bind; <2s budget by design
- [x] settings.json backup taken before edit
- [ ] **Owner visual gate** (cannot be self-verified — no Cursor UI access):
      open the terminal `+` dropdown, confirm `kClaude` shows with the sparkle/
      magenta glyph and launches the smart wrapper.

## Menu-ordering note (honest)

`kClaude` is placed as the FIRST key in the profiles object, before `Claude`.
"Last session (Default)" is pinned to the top of the `+` menu because it is the
`defaultProfile`. The remaining profiles are rendered by Cursor/VS Code from the
config object; observed behavior on this host (pre-existing order matched JSON
key order) is consistent with **insertion-order rendering**, which yields
`Last session / kClaude / Claude`.

If the live menu instead sorts **alphabetically**, `kClaude` (k) sorts AFTER
`Claude` (c) → `Last session / Claude / … / kClaude`. Remedy if so: rename the
key to something that sorts first (e.g. `Claude (k)`), or accept the position —
the button is fully functional either way. This is the single Owner-verifiable
gate.
