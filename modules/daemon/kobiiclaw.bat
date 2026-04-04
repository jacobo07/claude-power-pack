@echo off
REM KobiiClaw 2.0 — Persistent Claude Code on VPS via tmux (Windows)
REM
REM Usage:
REM   kobiiclaw [session-name] [workspace-path]
REM   kobiiclaw                                    (default session + workspace)
REM   kobiiclaw attach                             (reattach to existing session)
REM   kobiiclaw list                               (show active sessions)
REM
REM Part of Claude Power Pack — Infrastructure Resiliency Protocol.

set VPS_HOST=204.168.166.63
set VPS_USER=kobicraft
set SSH_KEY=%USERPROFILE%\.ssh\kobicraft_vps
set SESSION=%1
if "%SESSION%"=="" set SESSION=kobiiclaw
set WORKSPACE=%2
if "%WORKSPACE%"=="" set WORKSPACE=/home/kobicraft/workspace

if "%SESSION%"=="attach" (
    echo [KobiiClaw] Reattaching to existing tmux session...
    ssh -t -i "%SSH_KEY%" %VPS_USER%@%VPS_HOST% "tmux attach || tmux list-sessions"
    goto :eof
)

if "%SESSION%"=="list" (
    ssh -i "%SSH_KEY%" %VPS_USER%@%VPS_HOST% "tmux list-sessions 2>/dev/null || echo No tmux sessions running"
    goto :eof
)

echo [KobiiClaw 2.0] Connecting to VPS %VPS_HOST% as %VPS_USER%...
echo [KobiiClaw 2.0] tmux session: %SESSION% ^| workspace: %WORKSPACE%
echo [KobiiClaw 2.0] If disconnected, run: kobiiclaw attach
echo.

ssh -t -i "%SSH_KEY%" %VPS_USER%@%VPS_HOST% "tmux new-session -A -s '%SESSION%' -c '%WORKSPACE%' 'claude-daemon || claude || bash'"
