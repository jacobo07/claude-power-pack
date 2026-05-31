<#
.SYNOPSIS
Playwright MCP Stale Process Killer -- PP BL-PLAYWRIGHT-001

.DESCRIPTION
Mata procesos playwright node.exe que llevan idle > N min.
El Claude Code plugin loader los reinicia automaticamente
la proxima vez que se necesiten, con transport limpio.

No intenta "reconectar" el transport roto. Mata limpiamente
y deja que el plugin loader haga su trabajo.

Logs en $env:TEMP\pp-playwright-killer.log

.PARAMETER IdleThresholdMinutes
Minutos de idle antes de matar el proceso (default: 10).

.PARAMETER DryRun
Si se pasa, solo reporta sin matar nada.

.EXAMPLE
.\playwright_stale_killer.ps1
.\playwright_stale_killer.ps1 -IdleThresholdMinutes 5 -DryRun

.NOTES
ASCII-ONLY (BL-2026-05-24 PowerShell 5.1 ANSI codepage trap).
Sealed 2026-05-31 (Option A, Owner-approved arquitectura).
#>
param(
    [int]$IdleThresholdMinutes = 10,
    [switch]$DryRun
)

$LogFile = "$env:TEMP\pp-playwright-killer.log"

function Write-Log($msg, $Level = "INFO") {
    $ts = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
    $line = "$ts [$Level] $msg"
    $line | Out-File -FilePath $LogFile -Append -Encoding ascii
    Write-Host $line
}

function Get-PlaywrightProcesses {
    Get-CimInstance Win32_Process -Filter "Name='node.exe'" -ErrorAction SilentlyContinue |
        Where-Object {
            $_.CommandLine -and
            (
                $_.CommandLine -like "*@playwright/mcp*" -or
                $_.CommandLine -like "*playwright*cli.js*"
            )
        } |
        Select-Object ProcessId, CommandLine,
            @{N="AgeMinutes";E={
                if ($_.CreationDate) {
                    [int]([Math]::Round((New-TimeSpan -Start $_.CreationDate -End (Get-Date)).TotalMinutes))
                } else { 0 }
            }}
}

Write-Log "Playwright Stale Killer started (threshold: ${IdleThresholdMinutes}min, DryRun: $DryRun)"

$procs = Get-PlaywrightProcesses
$count = if ($procs) { @($procs).Count } else { 0 }
Write-Log "Found $count playwright node processes"

if ($count -eq 0) {
    Write-Log "No playwright processes found -- nothing to do"
    exit 0
}

$killed = 0
$skipped = 0

foreach ($p in $procs) {
    Write-Log "PID=$($p.ProcessId) age=$($p.AgeMinutes)min"

    if ($p.AgeMinutes -ge $IdleThresholdMinutes) {
        if ($DryRun) {
            Write-Log "  [DRYRUN] Would kill PID=$($p.ProcessId)" "WARN"
            $killed++
        } else {
            try {
                Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
                Write-Log "  KILLED PID=$($p.ProcessId) (age=$($p.AgeMinutes)min)" "WARN"
                $killed++
            } catch {
                Write-Log "  FAILED to kill PID=$($p.ProcessId): $($_.Exception.Message)" "ERROR"
            }
        }
    } else {
        Write-Log "  SKIPPED PID=$($p.ProcessId) (age=$($p.AgeMinutes)min < threshold)"
        $skipped++
    }
}

Write-Log "Summary: killed=$killed skipped=$skipped DryRun=$DryRun"

if ($killed -gt 0 -and -not $DryRun) {
    Write-Log "Stale processes removed. Claude Code will restart fresh ones on next Playwright use." "INFO"
}

exit 0
