# bench.ps1 — Locale-safe benchmark helper (BL-0026 / MC-SYS-54).
#
# Wraps Measure-Command and emits durations as raw integer milliseconds,
# bypassing PowerShell's locale-aware formatting which mis-prints es-ES
# thousands separators (the bug caught in Phase III: my "7.447ms" was
# actually 7,447ms = 7.4 seconds, see BL-0022).
#
# Usage:
#   .\tools\bench.ps1 -Label "advisor cold" -Cmd "node" -CmdArgs @("path\to\hook.js") -StdIn '{"tool_name":"Bash",...}'
#   .\tools\bench.ps1 -Label "selftest" -Cmd "python" -CmdArgs @("path\to\atomic_write.py","--self-test")
#
# Output (one line):
#   <Label>\t<integer ms>
#
# Or with -Json:
#   {"label":"...","ms":1234,"exit":0}

param(
  [Parameter(Mandatory=$true)][string]$Label,
  [Parameter(Mandatory=$true)][string]$Cmd,
  [string[]]$CmdArgs = @(),
  [string]$StdIn = $null,
  [int]$Repeat = 1,
  [switch]$Json,
  [switch]$ClearTempFlags
)

if ($ClearTempFlags) {
  Get-ChildItem "$env:TEMP\claude-*flag*","$env:TEMP\claude-skills-suggested-*","$env:TEMP\claude-ramwd-*","$env:TEMP\claude-ctxwd-*" -ErrorAction SilentlyContinue | Remove-Item -ErrorAction SilentlyContinue
}

$samples = @()
$exit = 0
for ($i = 0; $i -lt $Repeat; $i++) {
  $m = Measure-Command {
    if ($null -ne $StdIn -and $StdIn.Length -gt 0) {
      # PowerShell pipe injects a UTF-8/UTF-16 BOM. We avoid it by writing the
      # input to a UTF-8-no-BOM temp file and redirecting via the native
      # Windows cmd.exe (NOT msys2's cmd which lives in PATH on devkitPro
      # systems and breaks pipeline redirection).
      $tmp = [System.IO.Path]::GetTempFileName()
      $utf8 = New-Object System.Text.UTF8Encoding $false
      [System.IO.File]::WriteAllText($tmp, $StdIn, $utf8)
      try {
        $cmdExe = Join-Path $env:WINDIR 'System32\cmd.exe'
        $argStr = ($CmdArgs | ForEach-Object { '"' + ($_ -replace '"', '\"') + '"' }) -join ' '
        & $cmdExe /c "`"$Cmd`" $argStr < `"$tmp`"" | Out-Null
      } finally {
        Remove-Item $tmp -ErrorAction SilentlyContinue
      }
    } else {
      & $Cmd $CmdArgs | Out-Null
    }
    $script:exit = $LASTEXITCODE
  }
  $samples += [int]$m.TotalMilliseconds
}

# Use InvariantCulture for any further formatting; raw int output here is
# unambiguous (no thousands separator, no decimal point).
$ms = if ($Repeat -eq 1) { $samples[0] } else { [int](($samples | Measure-Object -Average).Average) }
$min = ($samples | Measure-Object -Minimum).Minimum
$max = ($samples | Measure-Object -Maximum).Maximum

if ($Json) {
  $obj = @{ label = $Label; ms = $ms; exit = $exit; samples = $samples; min = [int]$min; max = [int]$max }
  $obj | ConvertTo-Json -Compress
} else {
  if ($Repeat -gt 1) {
    "{0}`t{1} ms (avg of {2}, min={3}, max={4})" -f $Label, $ms, $Repeat, $min, $max
  } else {
    "{0}`t{1} ms" -f $Label, $ms
  }
}
