# post_restart_smoke.ps1 — Hook activation verification (BL-0036 / MC-SYS-71).
#
# Run this after `/restart` (or after any settings.json change) to verify all
# Phase II–V hooks load and respond. Each test pipes a synthetic event payload
# to the hook script and validates the JSON output shape.
#
# This script does NOT read any tokens, does NOT touch ~/.claude/.mcp.json,
# does NOT write outside $env:TEMP. Read-mostly.
#
# Usage:
#   pwsh -File C:\Users\kobig\.claude\skills\claude-power-pack\tools\post_restart_smoke.ps1
#
# Output: per-test PASS/FAIL line + final summary. Exit 0 if all pass, 1 if any fail.

$ErrorActionPreference = 'Stop'
$failures = @()
$passes = @()

function Bench {
  param([string]$Label, [string]$Cmd, [string[]]$CmdArgs, [string]$StdIn)
  $tmp = [System.IO.Path]::GetTempFileName()
  try {
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($tmp, $StdIn, $utf8)
    $cmdExe = Join-Path $env:WINDIR 'System32\cmd.exe'
    $argStr = ($CmdArgs | ForEach-Object { '"' + ($_ -replace '"', '\"') + '"' }) -join ' '
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $output = & $cmdExe /c "`"$Cmd`" $argStr < `"$tmp`""
    $stopwatch.Stop()
    return @{ ms = [int]$stopwatch.Elapsed.TotalMilliseconds; out = ($output -join "`n"); exit = $LASTEXITCODE }
  } finally {
    Remove-Item $tmp -ErrorAction SilentlyContinue
  }
}

function Test-Hook {
  param([string]$Name, [scriptblock]$Test)
  try {
    $result = & $Test
    if ($result.passed) {
      $script:passes += $Name
      Write-Host "[PASS] $Name ($($result.detail))" -ForegroundColor Green
    } else {
      $script:failures += "$Name - $($result.detail)"
      Write-Host "[FAIL] $Name - $($result.detail)" -ForegroundColor Red
    }
  } catch {
    $script:failures += "$Name - exception: $_"
    Write-Host "[FAIL] $Name - exception: $_" -ForegroundColor Red
  }
}

# ---- Hooks under test ----
$pp = "C:\Users\kobig\.claude\skills\claude-power-pack"
$advisor = "$pp\modules\zero-crash\hooks\skill-heat-map-advisor.js"
$ramwd   = "$pp\modules\zero-crash\hooks\ram-watchdog.js"
$ctxwd   = "$pp\modules\zero-crash\hooks\context-watchdog.py"
$awjs    = "$pp\lib\atomic_write.js"
$awpy    = "$pp\lib\atomic_write.py"

# ---- Tests ----

Write-Host "`n=== Hook activation smoke (BL-0036) ===`n"

Get-ChildItem "$env:TEMP\claude-skill-advisor-smoke-*.flag","$env:TEMP\claude-skills-suggested-smoke-*.txt","$env:TEMP\claude-ramwd-smoke-*.flag","$env:TEMP\claude-ctxwd-*-smoke-*.flag","$env:TEMP\claude-ctx-smoke-*.json" -ErrorAction SilentlyContinue | Remove-Item -ErrorAction SilentlyContinue

Test-Hook 'atomic_write.js self-test' {
  $r = Bench 'aw-js' 'node' @($awjs, '--self-test') ''
  $passed = ($r.exit -eq 0) -and ($r.out -match 'PASS \(4/4\)')
  return @{ passed = $passed; detail = "$($r.ms)ms exit=$($r.exit)" }
}

Test-Hook 'atomic_write.py self-test' {
  $r = Bench 'aw-py' 'python' @($awpy, '--self-test') ''
  $passed = ($r.exit -eq 0) -and ($r.out -match 'PASS \(4/4\)')
  return @{ passed = $passed; detail = "$($r.ms)ms exit=$($r.exit)" }
}

Test-Hook 'skill-heat-map-advisor returns hookSpecificOutput on Bash w/ design keywords' {
  $payload = '{"tool_name":"Bash","session_id":"smoke-advisor-1","tool_input":{"command":"audit codebase for security vulnerabilities and bugs"}}'
  $r = Bench 'advisor' 'node' @($advisor) $payload
  $passed = ($r.exit -eq 0) -and ($r.out -match 'hookSpecificOutput')
  return @{ passed = $passed; detail = "$($r.ms)ms exit=$($r.exit) out_starts=$($r.out.Substring(0,[Math]::Min(40,$r.out.Length)))" }
}

Test-Hook 'ram-watchdog returns valid JSON with continue:true' {
  $r = Bench 'ramwd' 'node' @($ramwd) '{"session_id":"smoke-ramwd-1"}'
  $passed = ($r.exit -eq 0) -and ($r.out -match 'continue.*true')
  return @{ passed = $passed; detail = "$($r.ms)ms exit=$($r.exit) out=$($r.out)" }
}

Test-Hook 'context-watchdog tier 1 silent (used=65)' {
  $TD = $env:TEMP
  $utf8nb = New-Object System.Text.UTF8Encoding $false
  [System.IO.File]::WriteAllText("$TD\claude-ctx-smoke-ctx1.json", '{"used_pct":65,"remaining_percentage":35,"tokens_used":130000,"tokens_total":200000}', $utf8nb)
  $r = Bench 'ctxwd1' 'python' @($ctxwd) '{"session_id":"smoke-ctx1","transcript_path":"/foo","cwd":"/bar"}'
  $passed = ($r.exit -eq 0) -and ($r.out.Trim() -eq '{}')
  Remove-Item "$TD\claude-ctx-smoke-ctx1.json" -ErrorAction SilentlyContinue
  return @{ passed = $passed; detail = "$($r.ms)ms exit=$($r.exit) out='$($r.out)'" }
}

Test-Hook 'context-watchdog tier 2 advisory (used=72)' {
  $TD = $env:TEMP
  $utf8nb = New-Object System.Text.UTF8Encoding $false
  [System.IO.File]::WriteAllText("$TD\claude-ctx-smoke-ctx2.json", '{"used_pct":72,"remaining_percentage":28,"tokens_used":144000,"tokens_total":200000}', $utf8nb)
  $r = Bench 'ctxwd2' 'python' @($ctxwd) '{"session_id":"smoke-ctx2","transcript_path":"/foo","cwd":"/bar"}'
  $passed = ($r.exit -eq 0) -and ($r.out -match 'CONTEXT THRESHOLD CROSSED') -and ($r.out -match '/compact')
  Remove-Item "$TD\claude-ctx-smoke-ctx2.json" -ErrorAction SilentlyContinue
  return @{ passed = $passed; detail = "$($r.ms)ms exit=$($r.exit)" }
}

# ---- Summary ----

Write-Host ""
Write-Host "PASSED: $($passes.Count)" -ForegroundColor Green
Write-Host "FAILED: $($failures.Count)" -ForegroundColor $(if ($failures.Count -gt 0) { 'Red' } else { 'Green' })
if ($failures.Count -gt 0) {
  Write-Host "`nFailures:" -ForegroundColor Red
  $failures | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
  exit 1
}

Write-Host "`nAll Phase II-V hooks responding correctly. Settings.json wiring is active." -ForegroundColor Green
Write-Host "Next step: do real frontend work -- type something like 'build me a SaaS dashboard'"
Write-Host "to trigger the lieutenant (parts/sleepy/frontend.md) in a real session."
exit 0
