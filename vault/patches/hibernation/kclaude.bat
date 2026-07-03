@echo off
rem kclaude.bat -- CONVERGED to the smart PowerShell wrapper (FASE A hibernation).
rem
rem Was: an independent cmd restart-loop that launched `claude %*` directly, so
rem its panes had NO hibernation park (claude.exe's parent was cmd.exe, not the
rem kclaude.ps1 powershell that arms/reads the wake flag).
rem
rem Now: a thin delegator to bin\kclaude.cmd -> kclaude.ps1, which owns BOTH the
rem /restart-flag loop AND the hibernation park-and-resume + sid beacon. This
rem makes every kclaude.bat-launched pane wakeable, converging all launchers on
rem the single park implementation (SCS C67).
rem
rem Install: copy over %USERPROFILE%\.claude\kclaude.bat (see README.md).
call "%USERPROFILE%\.claude\bin\kclaude.cmd" %*
