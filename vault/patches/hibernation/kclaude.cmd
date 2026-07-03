@echo off
rem kclaude.cmd -- the smart-wrapper shim (canonical). Runs the PowerShell wrapper
rem kclaude.ps1 (W6) which carries the CO gates + FASE A hibernation park-and-resume
rem + sid beacon. Lives at %USERPROFILE%\.claude\bin\kclaude.cmd; kclaude.ps1 sits
rem beside it (%~dp0kclaude.ps1). This is the single convergence point every other
rem launcher (kclaude.bat, lazarus-shell-autoresume.bat) routes through.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0kclaude.ps1" %*
