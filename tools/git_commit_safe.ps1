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
# Usage:
#   . tools/git_commit_safe.ps1
#   Invoke-GitCommitSafe -RepoRoot . -Body $body [-Amend]
#
# Or pipeline:
#   $body | tools/git_commit_safe.ps1 -RepoRoot .

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, ValueFromPipeline=$true)]
    [string]$Body,

    [Parameter()]
    [string]$RepoRoot = (Get-Location).Path,

    [Parameter()]
    [switch]$Amend,

    [Parameter()]
    [string]$GitExe = 'C:\Program Files\Git\cmd\git.exe'
)

function Invoke-GitCommitSafe {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)] [string]$Body,
        [string]$RepoRoot = (Get-Location).Path,
        [switch]$Amend,
        [string]$GitExe = 'C:\Program Files\Git\cmd\git.exe'
    )

    if (-not (Test-Path $GitExe)) {
        Write-Error "git.exe not found at $GitExe -- adjust -GitExe or install Git for Windows."
        return 1
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
                               -Amend:$Amend -GitExe $GitExe)
}
