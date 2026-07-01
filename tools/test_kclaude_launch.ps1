# test_kclaude_launch.ps1 -- behavioral V-gates for the kclaude launch context.
#
# T-KCLAUDE-LAUNCH-CONTEXT-001: a bare terminal-profile launch opens a NEW
# session (no --resume); an explicit --resume is honored; the /restart loop
# still resumes; CO-08 is advisory (never blocks/force-resumes on a bare launch).
#
# Hermetic: stubs `claude` on a temp PATH front so the real CLI never runs and
# the wrapper's final `& claude @launch` is captured. Runs kclaude in pp-root,
# which HAS resumable sessions (where the pre-fix code auto-resumed).

$ErrorActionPreference = 'Continue'
$repo   = Join-Path $env:USERPROFILE ".claude\skills\claude-power-pack\tools\kclaude.ps1"
$ppRoot = Join-Path $env:USERPROFILE ".claude\skills\claude-power-pack"
$pass = 0; $fail = 0
function Ok($g,$e){ $script:pass++; Write-Host "  [OK]   $g : $e" }
function Fail($g,$e){ $script:fail++; Write-Host "  [FAIL] $g : $e" }

$stub = Join-Path $env:TEMP "kclaude_stub_$PID"
New-Item -ItemType Directory -Path $stub -Force | Out-Null
$argfile = Join-Path $stub "args.txt"
$stubBody = "@echo off`r`n> `"%KCLAUDE_TEST_ARGS%`" echo ARGS:%*`r`nexit 0`r`n"
[System.IO.File]::WriteAllText((Join-Path $stub "claude.cmd"), $stubBody, [System.Text.ASCIIEncoding]::new())

function Run-Kclaude([string[]]$kargs) {
  Remove-Item $argfile -ErrorAction SilentlyContinue
  Push-Location $ppRoot
  try { & powershell (@('-NoProfile','-ExecutionPolicy','Bypass','-File',$repo) + $kargs) *> $null }
  finally { Pop-Location }
  if (Test-Path $argfile) { (Get-Content $argfile -Raw).Trim() } else { "<claude-not-invoked>" }
}

$orig = $env:PATH
try {
  $env:KCLAUDE_TEST_ARGS = $argfile
  $env:PATH = "$stub;$orig"

  $bare = Run-Kclaude @()
  if ($bare -notmatch 'resume') { Ok "V-NEW-SESSION-ON-LAUNCH" "bare -> claude [$bare]" }
  else { Fail "V-NEW-SESSION-ON-LAUNCH" "bare launched resume: [$bare]" }

  $res = Run-Kclaude @('--resume','fake-sid-abc')
  if ($res -match 'resume.*fake-sid-abc') { Ok "V-RESUME-ON-EXPLICIT" "[$res]" }
  else { Fail "V-RESUME-ON-EXPLICIT" "explicit resume not honored: [$res]" }
}
finally {
  $env:PATH = $orig
  Remove-Item Env:\KCLAUDE_TEST_ARGS -ErrorAction SilentlyContinue
  Remove-Item $stub -Recurse -Force -ErrorAction SilentlyContinue
}

# Static contract checks on the wrapper source.
$body = Get-Content $repo -Raw
if ($body -match "@\('--resume', \`$sid\)") { Ok "V-RESTART-LOOP-RESUMES" "restart loop resumes the SID" }
else { Fail "V-RESTART-LOOP-RESUMES" "restart loop resume missing" }
if (($body -notmatch 'Read-Host') -and ($body -notmatch 'exit 9')) { Ok "V-CO08-ADVISORY-NO-BLOCK" "no Read-Host/exit-9 in gate path" }
else { Fail "V-CO08-ADVISORY-NO-BLOCK" "CO-08 still blocks (Read-Host/exit 9 present)" }

Write-Host ""
Write-Host ("KCLAUDE_LAUNCH=$pass/$($pass+$fail)  threshold=4/4")
if ($fail -eq 0) { exit 0 } else { exit 1 }
