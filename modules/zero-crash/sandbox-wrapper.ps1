# Zero-Crash Sandbox Wrapper — Windows PowerShell
#
# Usage:
#   zero-crash-sandbox.ps1 <command> [args...]
#
# What it does:
#   1. Starts process with no window (detached from terminal)
#   2. Redirects stdout+stderr to timestamped log file
#   3. Captures PID for later cleanup
#   4. Returns immediately (non-blocking)
#
# Part of Claude Power Pack — Zero-Crash Environment module.

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Command,

    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

# Configuration
$LogDir = if ($env:ZERO_CRASH_LOG_DIR) { $env:ZERO_CRASH_LOG_DIR } else { Join-Path $env:TEMP "zero-crash" }
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$Timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$CommandName = Split-Path -Leaf $Command
$LogFile = Join-Path $LogDir "${Timestamp}-${CommandName}.log"
$PidFile = Join-Path $LogDir "active_pids.txt"

# Build argument string
$ArgString = if ($Arguments) { $Arguments -join " " } else { "" }

Write-Host "[Zero-Crash] Sandboxing: $Command $ArgString"
Write-Host "[Zero-Crash] Log: $LogFile"

# Launch sandboxed process (no window, redirected output)
$ProcessInfo = New-Object System.Diagnostics.ProcessStartInfo
$ProcessInfo.FileName = $Command
$ProcessInfo.Arguments = $ArgString
$ProcessInfo.UseShellExecute = $false
$ProcessInfo.CreateNoWindow = $true
$ProcessInfo.RedirectStandardOutput = $true
$ProcessInfo.RedirectStandardError = $true
$ProcessInfo.RedirectStandardInput = $true

try {
    $Process = [System.Diagnostics.Process]::Start($ProcessInfo)

    # Redirect output to log file asynchronously
    $Process.StandardInput.Close()

    # Start async reads to prevent buffer deadlock
    $stdoutTask = $Process.StandardOutput.ReadToEndAsync()
    $stderrTask = $Process.StandardError.ReadToEndAsync()

    # Write PID immediately (don't wait for process to finish)
    $PID = $Process.Id
    Add-Content -Path $PidFile -Value $PID

    # Fire-and-forget: write output to log when available
    # Use a background job to collect output without blocking
    Start-Job -ScriptBlock {
        param($proc, $logFile, $stdoutT, $stderrT)
        $stdout = $stdoutT.Result
        $stderr = $stderrT.Result
        $content = "=== STDOUT ===`n$stdout`n=== STDERR ===`n$stderr"
        Set-Content -Path $logFile -Value $content -Encoding UTF8
    } -ArgumentList $Process, $LogFile, $stdoutTask, $stderrTask | Out-Null

    Write-Host "[Zero-Crash] SANDBOXED: PID=$PID"
    Write-Host "[Zero-Crash] Monitor: Get-Content -Wait $LogFile"
    Write-Host "[Zero-Crash] Kill: Stop-Process -Id $PID"

} catch {
    Write-Host "[Zero-Crash] ERROR: Failed to start process: $_" -ForegroundColor Red
    exit 1
}
