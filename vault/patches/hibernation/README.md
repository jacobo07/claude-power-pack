# Hibernation global-wrapper patches (FASE A activation)

These are the `~/.claude/` global files auto-mode cannot write (HR-001), packaged
for one-step install. They converge every launcher on `kclaude.ps1` — the single
wrapper that carries the FASE A hibernation park-and-resume + sid beacon.

## Live launcher distribution (measured 2026-07-03)
`ps1=23` (already covered after the `bin\kclaude.ps1` sync) · `bat=33` (need the
`kclaude.bat` patch below) · `cmd=0` · `other=3` (lazarus-shell / raw).

## Install (run each line; back up first)

```powershell
$cl = "$env:USERPROFILE\.claude"
$src = "$cl\skills\claude-power-pack\vault\patches\hibernation"

# 0. bin\kclaude.ps1 -- already synced in A1 (verify identical):
(Get-FileHash "$cl\skills\claude-power-pack\tools\kclaude.ps1").Hash -eq `
  (Get-FileHash "$cl\bin\kclaude.ps1").Hash    # -> True

# 1. bin\kclaude.cmd -- the shim (usually already present; refresh to canonical):
Copy-Item "$cl\bin\kclaude.cmd" "$cl\bin\kclaude.cmd.bak" -Force -EA SilentlyContinue
Copy-Item "$src\kclaude.cmd"    "$cl\bin\kclaude.cmd" -Force

# 2. kclaude.bat -- CONVERGE the 33 bat panes onto kclaude.ps1:
Copy-Item "$cl\kclaude.bat" "$cl\kclaude.bat.bak" -Force
Copy-Item "$src\kclaude.bat" "$cl\kclaude.bat" -Force
```

New panes launched after this get the sid beacon + wake flag. Existing panes
activate on their next launch (or `/restart`).

## lazarus-shell-autoresume.bat -- NO CHANGE NEEDED

It already resumes through `bin\kclaude.cmd` (its `MC-LAZ-26` block prefers
`%USERPROFILE%\.claude\bin\kclaude.cmd --resume`) and its fresh-launch doskey points
at the same shim. Once `kclaude.bat` delegates to `bin\kclaude.cmd` (step 2), every
lazarus path converges too. No patch shipped for it on purpose (no redundant copy).

## Verify convergence (after install + relaunching a couple panes)

```powershell
# claude.exe parents should now be powershell (kclaude.ps1), not bare cmd:
Get-CimInstance Win32_Process -Filter "Name='claude.exe'" | ForEach-Object {
  (Get-CimInstance Win32_Process -Filter ("ProcessId=" + $_.ParentProcessId)).Name
} | Group-Object | Select-Object Name, Count

# beacons should start appearing for resumed panes:
Get-ChildItem "$env:TEMP\kclaude-pane-*.sid"
```

## Rollback
Each step wrote a `.bak`. To revert: `Copy-Item <file>.bak <file> -Force`.
`bin\kclaude.ps1` backup from A1: `bin\kclaude.ps1.bak-prehibernation-20260703`.
