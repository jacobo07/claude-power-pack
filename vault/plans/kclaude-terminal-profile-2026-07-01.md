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

`%APPDATA%\Cursor\User\settings.json` — new profile keyed `" kClaude"` (leading
space, see ordering section below) under `terminal.integrated.profiles.windows`:

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

## Menu-ordering — SOLVED (proven from Cursor source, not guessed)

Cursor does NOT render terminal profiles in config/insertion order. Its
`_sortProfileQuickPickItems` (extracted from
`resources/app/out/vs/workbench/workbench.desktop.main.js`) is:

```js
n.sort((t,i)=> i.profileName===e ? 1 : t.profileName===e ? -1
             : t.profileName.localeCompare(i.profileName))
```

i.e. the **default** profile (`e` = "Last session") is force-pinned first, and
**every other profile is sorted alphabetically** by name via `localeCompare`.
Insertion order is irrelevant. So a key named `kClaude` sorts AFTER `Claude`
(c < k) — the wrong slot.

**Fix:** the profile key is `" kClaude"` (single **leading space**).
`" kClaude".localeCompare("Claude") < 0` (verified in Node, same ICU collation as
Cursor's Electron), so it collates before `Claude` — and before every other
non-default profile — landing it as the first item under the pinned default.
The leading space renders as a ~1px indent, essentially invisible; the label
reads "kClaude". Not a homoglyph/zero-width trick — a plain ASCII space.

Simulated resulting menu (Cursor's own sort algorithm replayed on the live file):
`Last session (Default) / kClaude / Claude / Claude (VPS) / …`. Matches the
requested position exactly.
