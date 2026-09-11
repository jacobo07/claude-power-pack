# git_commit_safe.ps1 -- transversal wrapper around `git commit -F`.
#
# Sealed 2026-05-26 after the L8 argv-reparser cascade. PowerShell's
# native-command splitter re-tokenizes a heredoc commit message on
# inner double-quotes, breaking `-m`. This wrapper bypasses argv
# entirely: write the body to a temp file (literal bytes), invoke
# `git commit -F <file>`, delete on success.
#
# Use this in EVERY repo on this Windows host instead of inline -m
# commits with multi-line bodies.
#
# SCOPE (added 2026-09-11). -PathSpec names the files this commit may take.
# Without it git commits the whole index, so on a host with two panes on one
# checkout this wrapper handed a concurrent writer's staged files to whoever
# committed first. The pathspec rule was already doctrine in three places and
# the sanctioned wrapper could not express it -- documented prevention with an
# owner that was structurally unable to obey. Pathspec is FILE granularity;
# when two writers are inside one FILE, escalate to tools/foreign_hunk_guard.py,
# which stages at hunk granularity against a pre-edit baseline.
#
# Usage:
#   . tools/git_commit_safe.ps1
#   Invoke-GitCommitSafe -RepoRoot . -Body $body -PathSpec 'a.py','b.py' [-Amend]
#
# Or pipeline:
#   $body | tools/git_commit_safe.ps1 -RepoRoot .

# $Body is NOT Mandatory at script scope, and that is deliberate. A mandatory
# script parameter is bound when the file is DOT-SOURCED, so the documented
# first usage below -- `. tools/git_commit_safe.ps1` -- failed with
# MissingMandatoryParameter and could never expose the function. The wrapper
# sealed 2026-05-26 for use in every repo on this host had a header whose
# opening line did not work, which is the likeliest reason nothing in the
# estate ever called it. The function keeps its own Mandatory $Body, so a real
# commit still cannot be issued without a message.
[CmdletBinding()]
param(
    [Parameter(ValueFromPipeline=$true)]
    [string]$Body,

    [Parameter()]
    [string]$RepoRoot = (Get-Location).Path,

    [Parameter()]
    [switch]$Amend,

    [Parameter()]
    [string[]]$PathSpec = @(),

    [Parameter()]
    [switch]$AllowUnscoped,

    [Parameter()]
    [string]$GitExe = 'C:\Program Files\Git\cmd\git.exe'
)

function Invoke-GitCommitSafe {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)] [string]$Body,
        [string]$RepoRoot = (Get-Location).Path,
        [switch]$Amend,
        [string[]]$PathSpec = @(),
        [switch]$AllowUnscoped,
        [string]$GitExe = 'C:\Program Files\Git\cmd\git.exe'
    )

    if (-not (Test-Path $GitExe)) {
        Write-Error "git.exe not found at $GitExe -- adjust -GitExe or install Git for Windows."
        return 1
    }

    # A commit with no pathspec takes whatever is in the index, including
    # another pane's staged files, under this message. The doctrine has
    # required named files since the Hermes collision; this wrapper could not
    # express one until now, so every caller told to use it was structurally
    # unable to comply. Absent -PathSpec the commit still proceeds -- an amend
    # or a deliberate whole-index commit is legitimate -- but it says so, and
    # it reports what it is about to take so the operator can see a foreign
    # file before it lands rather than in the insertion count afterwards.
    if ($PathSpec.Count -eq 0 -and -not $Amend -and -not $AllowUnscoped) {
        $staged = & $GitExe -C $RepoRoot diff --cached --name-only
        $n = @($staged).Count
        Write-Warning ("UNSCOPED COMMIT: no -PathSpec given, so this takes all $n staged path(s): " +
                       (@($staged) -join ', '))
        Write-Warning "Pass -PathSpec <paths> to scope it, or -AllowUnscoped to silence this."
    }

    # Write body to a temp file as raw UTF-8 (no BOM). PowerShell's
    # Out-File / Set-Content default to UTF-16-LE BOM; we explicitly
    # emit UTF-8 LF so git reads it cleanly.
    $tempFile = [System.IO.Path]::Combine($RepoRoot, ".commit_msg_safe_$([System.Guid]::NewGuid().ToString('N').Substring(0,8)).txt")
    try {
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($tempFile, $Body, $utf8NoBom)

        $gitArgs = @('-C', $RepoRoot, 'commit', '-F', $tempFile)
        if ($Amend) { $gitArgs += '--amend' }
        if ($PathSpec.Count -gt 0) { $gitArgs += '--'; $gitArgs += $PathSpec }

        & $GitExe @gitArgs
        $rc = $LASTEXITCODE
        if ($rc -ne 0) {
            Write-Warning "git commit returned exit code $rc -- inspect output above."
        }
        return $rc
    }
    finally {
        if (Test-Path $tempFile) { Remove-Item $tempFile -Force }
    }
}

# When dot-sourced, the function is exposed. When executed directly
# with -Body, run the commit.
if ($MyInvocation.InvocationName -ne '.' -and $Body) {
    exit (Invoke-GitCommitSafe -Body $Body -RepoRoot $RepoRoot `
                               -Amend:$Amend -PathSpec $PathSpec `
                               -AllowUnscoped:$AllowUnscoped -GitExe $GitExe)
}
