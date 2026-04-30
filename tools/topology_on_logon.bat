@echo off
REM topology_on_logon.bat -- post-repair / post-reboot hook that opens the
REM five Cursor windows in canonical taskbar order per
REM vault/topology/lazarus_layout_<DATE>.json.
REM
REM Wired in two ways:
REM   1. Manually one-shot:  topology_on_logon.bat
REM   2. Via Windows Task Scheduler /SC ONLOGON (created by REPAIR_WINDOWS_v2.bat
REM      lazarus-shell-autoresume.bat invocation, OR by:
REM         schtasks /Create /TN "TopologyResume" /TR "topology_on_logon.bat" \
REM           /SC ONLOGON /RL HIGHEST /F
REM
REM Safety: relies on topology_apply.py's --i-have-no-open-windows fence.
REM If Cursor processes are already running (e.g. user opened them manually
REM before this script fires), the python tool refuses with exit 4 and the
REM .bat exits cleanly without clobbering.
REM
REM Owner override: pass --force-search-roots to fall back to heuristic
REM resolution if explicit resolved_path entries are missing in the layout.

setlocal
set "REPO=%USERPROFILE%\.claude\skills\claude-power-pack"
set "LAYOUT=%REPO%\vault\topology\lazarus_layout_2026-04-29.json"
set "LOG=%USERPROFILE%\Desktop\.topology_resume_LOG"
set "PYTHONIOENCODING=utf-8"

> "%LOG%" echo [%DATE% %TIME%] topology_on_logon start
>> "%LOG%" echo Layout: %LAYOUT%

if not exist "%LAYOUT%" (
  >> "%LOG%" echo FATAL: layout file missing
  exit /b 2
)

python "%REPO%\tools\topology_apply.py" "%LAYOUT%" --i-have-no-open-windows >> "%LOG%" 2>&1
set "RC=%ERRORLEVEL%"
>> "%LOG%" echo [%TIME%] topology_apply.py exit=%RC%

if "%RC%"=="0" (
  >> "%LOG%" echo SUCCESS: 5/5 Cursor windows launched in canonical order
  exit /b 0
)
if "%RC%"=="4" (
  >> "%LOG%" echo SKIPPED: open Cursor processes detected, refused to clobber
  exit /b 0
)
>> "%LOG%" echo FAIL: rc=%RC% — see log tail above
exit /b %RC%
