<#
  ngen_powershell.ps1 -- give Windows PowerShell 5.1 its native images back.
  T-KCLAUDE-PASTE-WINDOW-001 (2026-09-22). RUN ELEVATED (Administrator).

  WHY. Every Claude pane on this host starts through kclaude.cmd ->
  powershell.exe -File kclaude.ps1 -> claude.exe, and nothing can be pasted
  into a pane until claude.exe is up. Measured 2026-09-22 on this host:
      cmd /c exit                          127 ms
      powershell -NoProfile -Command exit  4183 ms
      + one Management and one Utility cmdlet  7352 ms
  A fresh powershell.exe loads native images (*.ni.dll) for mscorlib, System
  and System.Core -- so the instrument CAN see a native image -- but NOT for
  System.Management.Automation or Microsoft.PowerShell.ConsoleHost, and
  `ngen display System.Management.Automation` answers "The specified assembly
  is not installed". PowerShell's own core is JIT-compiled on EVERY start.
  That is a machine-wide cost: every powershell.exe on the host pays it --
  panes, hooks, scheduled tasks and the agent's own tool calls.

  WHAT. Collects every assembly a fresh `powershell -NoProfile` loads after
  touching the Management and Utility modules (the ones kclaude.ps1 uses),
  and runs `ngen install` on each. Idempotent: an already-native assembly is
  a no-op. Reversible: `ngen uninstall <assembly>`. Writes a before/after
  report to %TEMP%\ngen_powershell_report.txt so the effect is measured, not
  assumed.

  RUN (from any shell):
      Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','C:\Users\User\.claude\skills\claude-power-pack\tools\ngen_powershell.ps1'

  ASCII-only source (PS 5.1 codepage safety).
#>
$ErrorActionPreference = 'Continue'
$report = Join-Path $env:TEMP 'ngen_powershell_report.txt'
$ps = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
$ngen = Join-Path ([Runtime.InteropServices.RuntimeEnvironment]::GetRuntimeDirectory()) 'ngen.exe'
$lines = New-Object System.Collections.Generic.List[string]
function Say([string] $s) { $lines.Add($s); Write-Host $s }

$id = [Security.Principal.WindowsIdentity]::GetCurrent()
$admin = (New-Object Security.Principal.WindowsPrincipal($id)).IsInRole(
  [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) {
  Say 'REFUSED: not elevated. ngen install writes the machine native-image cache; run this as Administrator.'
  [IO.File]::WriteAllLines($report, $lines)
  exit 3
}

# The probe a fresh process runs: touch the two modules kclaude.ps1 uses, then
# report (a) which assemblies are loaded, (b) which of them have a native image.
$probe = @'
[void](Test-Path C:\); [void]('{}' | ConvertFrom-Json)
$mods = (Get-Process -Id $PID).Modules | ForEach-Object { $_.ModuleName }
foreach ($a in [AppDomain]::CurrentDomain.GetAssemblies()) {
  if (-not $a.Location) { continue }
  $n = $a.GetName().Name
  $native = [bool]($mods | Where-Object { $_ -ieq ($n + '.ni.dll') })
  '{0}|{1}|{2}' -f $n, $native, $a.Location
}
'@

function Measure-Start {
  $m = @()
  for ($i = 0; $i -lt 3; $i++) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    & $ps -NoProfile -Command 'exit' | Out-Null
    $sw.Stop(); $m += [int]$sw.ElapsedMilliseconds
  }
  $s = @($m | Sort-Object); return ('median {0} ms ({1})' -f $s[1], ($m -join '/'))
}

function Get-Loaded { & $ps -NoProfile -Command $probe | Where-Object { $_ -match '\|' } }

$before = Get-Loaded
$jit = @($before | Where-Object { $_.Split('|')[1] -eq 'False' })
Say ("BEFORE  startup {0}; assemblies without a native image: {1}" -f (Measure-Start), $jit.Count)
$jit | ForEach-Object { Say ('   JIT ' + $_.Split('|')[0]) }

foreach ($row in $jit) {
  $loc = $row.Split('|')[2]
  $out = & $ngen install $loc /nologo 2>&1 | Out-String
  $ok = $LASTEXITCODE -eq 0
  Say ('   ngen install {0} -> {1}' -f $row.Split('|')[0], $(if ($ok) { 'ok' } else { 'rc=' + $LASTEXITCODE }))
  if (-not $ok) { Say ('      ' + ($out.Trim() -split "`n" | Select-Object -Last 2) -join ' ') }
}

$after = Get-Loaded
$still = @($after | Where-Object { $_.Split('|')[1] -eq 'False' })
Say ("AFTER   startup {0}; assemblies without a native image: {1}" -f (Measure-Start), $still.Count)
$still | ForEach-Object { Say ('   still JIT ' + $_.Split('|')[0]) }
[IO.File]::WriteAllLines($report, $lines)
Say "report: $report"
