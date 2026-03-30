@echo off
setlocal enabledelayedexpansion

REM Claude Power Pack - Dynamic Daemon and Crash Recovery (Part P)
REM Hardware-aware Node.js memory tuning + automatic crash recovery loop.
REM
REM Usage:
REM   claude-daemon [claude args...]

set "CONFIG_FILE=%USERPROFILE%\.claude\daemon\config"
set "MIN_RAM=2048"
set "MAX_RAM=8192"
set "MAX_RETRIES=5"
set "RETRIES=0"

REM 1. RAM Detection via WMIC
for /f "skip=1" %%A in ('wmic computersystem get TotalPhysicalMemory 2^>nul') do (
    set "RAM_BYTES=%%A"
    goto :got_ram
)
:got_ram
REM Convert bytes to MB via PowerShell one-liner
for /f %%M in ('powershell -NoProfile -Command "[math]::Floor(%RAM_BYTES% / 1048576)"') do set "TOTAL_RAM=%%M"

if not defined TOTAL_RAM set "TOTAL_RAM=8192"

REM 2. Calculate 25%% with clamp
set /a "NODE_MEM=TOTAL_RAM / 4"
if !NODE_MEM! LSS %MIN_RAM% set "NODE_MEM=%MIN_RAM%"
if !NODE_MEM! GTR %MAX_RAM% set "NODE_MEM=%MAX_RAM%"

REM 3. Load user override from config file
if not exist "%CONFIG_FILE%" goto :no_override
for /f "tokens=2 delims==" %%V in ('findstr /B "MAX_OLD_SPACE_SIZE=" "%CONFIG_FILE%" 2^>nul') do (
    set "NODE_MEM=%%V"
    echo [daemon] Using manual override: !NODE_MEM!MB
    goto :set_env
)
:no_override
echo [daemon] System RAM: %TOTAL_RAM%MB -- Node.js heap: %NODE_MEM%MB (25%%)

:set_env
set "NODE_OPTIONS=--max-old-space-size=%NODE_MEM%"

REM 4. Immortality Loop
:loop
claude %*
set "EXIT_CODE=!ERRORLEVEL!"

if "!EXIT_CODE!"=="0" exit /b 0
REM Ctrl+C on Windows typically gives 3221225786 (STATUS_CONTROL_C_EXIT)
if "!EXIT_CODE!"=="3221225786" exit /b 1

set /a "RETRIES+=1"
if !RETRIES! GEQ %MAX_RETRIES% goto :max_retries

echo.
echo [WARNING] Claude Code crashed (exit code: !EXIT_CODE!). Recovering... (attempt !RETRIES!/%MAX_RETRIES%)
echo           Restarting in 2 seconds...
timeout /t 2 /nobreak >nul
goto :loop

:max_retries
echo.
echo [STOP] Claude Code crashed %MAX_RETRIES% times consecutively. Stopping.
echo        Check logs or adjust memory: claude-daemon-set-ram [MB]
exit /b 1
