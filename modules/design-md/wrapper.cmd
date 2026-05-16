@echo off
REM design-md.cmd — Windows wrapper around @google/design.md, resolves the CLI
REM from the Claude Power Pack repo's local node_modules.
REM
REM Usage: design-md ^<lint^|diff^|export^|spec^> [args...]

setlocal

REM Resolve the Power-Pack repo. When copied to %USERPROFILE%\.claude\bin\
REM the wrapper can no longer derive the skill dir from %~dp0; prefer the
REM canonical path and only fall back to relative resolution from-repo.
if defined CLAUDE_POWER_PACK_DIR (
    if exist "%CLAUDE_POWER_PACK_DIR%\package.json" set "SKILL_DIR=%CLAUDE_POWER_PACK_DIR%"
)
if not defined SKILL_DIR (
    if exist "%USERPROFILE%\.claude\skills\claude-power-pack\package.json" set "SKILL_DIR=%USERPROFILE%\.claude\skills\claude-power-pack"
)
if not defined SKILL_DIR set "SKILL_DIR=%~dp0..\.."

set "ENTRY=%SKILL_DIR%\node_modules\@google\design.md\dist\index.js"

if not exist "%ENTRY%" (
    echo design-md: CLI entry not found at %ENTRY% 1>&2
    echo design-md: run "%SKILL_DIR%\install.ps1" ^(Node 18+ + npm required^) to provision it. 1>&2
    exit /b 127
)

where node >nul 2>nul
if errorlevel 1 (
    echo design-md: 'node' not on PATH - install Node 18+ and retry. 1>&2
    exit /b 127
)

node "%ENTRY%" %*
exit /b %errorlevel%
