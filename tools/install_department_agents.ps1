# install_department_agents.ps1 -- PP Spec-Driven Department installer.
#
# HR-001: the agent cannot write ~/.claude/agents/ in auto-mode, and new
# agent files cold-load (they do not become dispatchable until /restart).
# This installer is the Owner-side registration step: it copies the three
# department agents staged in vault/agents/ into ~/.claude/agents/ so they
# become dispatchable subagent types after a /restart.
#
# Usage:   powershell -ExecutionPolicy Bypass -File tools\install_department_agents.ps1
# ASCII-only (PS 5.1 codepage safety; no em-dashes, no accented chars).

$ErrorActionPreference = 'Stop'

$agents = @(
    'pp-spec-guardian',
    'pp-premise-guardian',
    'pp-error-analyst'
)

$src = Join-Path $PSScriptRoot '..\vault\agents'
$dst = Join-Path $HOME '.claude\agents'

if (-not (Test-Path $dst)) {
    New-Item -ItemType Directory -Force -Path $dst | Out-Null
}

$installed = 0
foreach ($a in $agents) {
    $from = Join-Path $src "$a.md"
    $to   = Join-Path $dst "$a.md"
    if (-not (Test-Path $from)) {
        Write-Host "SKIP (missing source): $a"
        continue
    }
    Copy-Item $from $to -Force
    Write-Host "Installed: $a -> $to"
    $installed++
}

Write-Host ""
Write-Host "Installed $installed/$($agents.Count) department agents."
Write-Host "Run /restart for Claude Code to cold-load them as dispatchable subagents."
