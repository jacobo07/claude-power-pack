@echo off
REM Claude Power Pack - Manual RAM Override for Daemon (Part P)
REM
REM Usage:
REM   claude-daemon-set-ram [MB]       Force specific heap size
REM   claude-daemon-set-ram --reset    Back to auto-detect

set "CONFIG_DIR=%USERPROFILE%\.claude\daemon"
set "CONFIG_FILE=%CONFIG_DIR%\config"

if "%~1"=="--reset" goto :do_reset
if "%~1"=="" goto :show_usage
goto :do_set

:do_reset
if exist "%CONFIG_FILE%" del "%CONFIG_FILE%"
echo [OK] RAM override removed. Will use auto-detection.
exit /b 0

:show_usage
echo Usage: claude-daemon-set-ram [MB]
echo        claude-daemon-set-ram --reset
echo.
echo Examples:
echo   claude-daemon-set-ram 4096     Force 4GB heap
echo   claude-daemon-set-ram 8192     Force 8GB heap
echo   claude-daemon-set-ram --reset  Back to auto-detect
exit /b 1

:do_set
if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"
echo MAX_OLD_SPACE_SIZE=%~1> "%CONFIG_FILE%"
echo [OK] Node.js heap override set to %~1MB. Effective on next claude-daemon launch.
exit /b 0
