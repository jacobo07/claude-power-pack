"""Dangerous command registry -- BL-DATASET-BUILD M11.

Pattern set of shell / SQL / git / network commands that warrant
Cascade C4 block. Patterns are checked against a single command
string via is_dangerous / reasons.
"""
from __future__ import annotations

import re

# Each entry: (compiled pattern, short human-readable reason).
DANGEROUS_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^\s*rm\s+-r?f+\s+/", re.IGNORECASE),
     "rm -rf on absolute path"),
    (re.compile(r"\bRemove-Item\b.*\b-Recurse\b.*\b-Force\b",
                re.IGNORECASE),
     "Remove-Item -Recurse -Force"),
    (re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE),
     "destructive SQL DROP"),
    (re.compile(r"\bTRUNCATE\s+TABLE\b", re.IGNORECASE),
     "destructive SQL TRUNCATE"),
    (re.compile(r"\bgit\s+push\s+.*--force(?!-with-lease)",
                re.IGNORECASE),
     "git push --force without --force-with-lease"),
    (re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE),
     "git reset --hard"),
    (re.compile(r"\bgit\s+clean\s+-[a-z]*fdx?", re.IGNORECASE),
     "git clean -fdx"),
    (re.compile(r":\(\)\s*\{[^}]*&\s*\}\s*;"),
     "fork bomb"),
    (re.compile(r"\bchmod\s+-R\s+777\b"),
     "chmod -R 777"),
    (re.compile(
        r"\b(curl|wget|iwr|Invoke-WebRequest)\b[^|\n]*\|\s*"
        r"(bash|sh|zsh|powershell|pwsh)\b"
    ),
     "pipe-to-shell from network"),
    (re.compile(r"\beval\s*\(", re.IGNORECASE),
     "eval() of dynamic content"),
]


# Commands that are not destructive but are RELIABLY WRONG on this host.
# Each one is documented in CLAUDE.md or the vault and each one has still
# been re-issued by an agent that had read the documentation -- which makes
# them a knowledge-execution failure, not a knowledge gap. Prose has to be
# recalled at the moment of writing a command; a pattern does not.
#
# Advisory, never a block: the command may be exactly what the author
# wants, and a correctness note that blocks would be indistinguishable from
# the destructive registry above.
CORRECTNESS_TRAPS: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"\b(?:Set-Content|Out-File|Add-Content)\b[^|\n]*"
                r"-Encoding\s+utf8\b(?!NoBOM)", re.IGNORECASE),
     "PowerShell 5.1 writes a UTF-8 BOM with -Encoding utf8",
     "[System.IO.File]::WriteAllText($p, $s, "
     "(New-Object System.Text.UTF8Encoding($false)))"),

    (re.compile(r"@['\"][\s\S]*?['\"]@\s*\|\s*[&\s]*\S*\bssh\b",
                re.IGNORECASE),
     "a here-string piped to ssh prepends a BOM to the remote stdin, so the "
     "remote shell loses the first command",
     "write the script to a temp file UTF-8-no-BOM with LF endings and run "
     "cmd /c \"ssh ... bash -s < $tmp\""),

    (re.compile(r"(?<![\w./\\-])git\s+(?:status|commit|log|push|add|diff|"
                r"checkout|rev-parse|fetch)\b"),
     "bare `git` is not on this host's non-interactive PowerShell PATH, so "
     "it silently falls back to Bash and can hang the MSYS2 bridge",
     "& 'C:\\Program Files\\Git\\cmd\\git.exe' <args>"),

    (re.compile(r"\bgit\s+commit\b[^\n]*-m\s*(['\"])[\s\S]*?\n"),
     "a multi-line `git commit -m` is re-parsed by the shell and breaks the "
     "pathspec (HR-003)",
     "write the body to a file and use `git commit -F <file>`"),

    # Observed 2026-08-26 in this session: `python x.py | Select-Object
    # -First 5` reported CHECK_EXIT=-1 for a script that exited 0.
    (re.compile(r"&?\s*\S*\b(?:python|pytest|node|npm|git)\S*\b[^|\n]*\|\s*"
                r"Select-Object\s+-First\b", re.IGNORECASE),
     "Select-Object -First stops the pipeline, killing the native process "
     "early and making $LASTEXITCODE meaningless",
     "redirect to a file, read it, and measure the exit code separately"),

    # Recurrence four, 2026-09-02. Documented in CLAUDE.md, sealed in the
    # vault, and re-issued four times in the session that was auditing why
    # known traps recur. PowerShell 5.1 wraps each stderr line from a
    # NATIVE executable in an ErrorRecord, so the call reports
    # NativeCommandError and $? goes False even when the exe returned 0 --
    # output that reads as a failure for a command that succeeded.
    #
    # Deliberately narrow. `2>&1` is ordinary and correct in Bash, and this
    # registry is checked against Bash commands too, so the pattern
    # requires a PowerShell native-exe invocation: the call operator with a
    # variable or quoted .exe, or a bare .exe token. Precision over recall
    # is the right trade on a surface this busy -- a correctness note that
    # fires on every shell redirect is a note that gets ignored.
    (re.compile(r"""(?:&\s*(?:\$\w+|['"][^'"]*\.exe['"])"""
                r"""|\b[\w.-]+\.exe\b)[^|\n]*?2>&1"""),
     "PowerShell wraps a native executable's stderr in an ErrorRecord, so "
     "2>&1 reports NativeCommandError and sets $? False on a command that "
     "exited 0",
     "drop the redirect -- stderr is already captured; if you must have it, "
     "send it to a file and read that"),
]


def trap_warnings(command: str) -> list[dict]:
    """Non-blocking correctness notes for `command`. Empty -> nothing known.

    Separate from `reasons()` on purpose: these describe a command that
    will probably do the wrong thing, not one that will destroy something,
    and collapsing the two severities would erode the block's meaning.
    """
    if not command:
        return []
    return [{"trap": what, "fix": fix}
            for pat, what, fix in CORRECTNESS_TRAPS if pat.search(command)]


def is_dangerous(command: str) -> bool:
    """Return True iff `command` matches any DANGEROUS_PATTERNS entry."""
    if not command:
        return False
    return any(pat.search(command) for pat, _ in DANGEROUS_PATTERNS)


def reasons(command: str) -> list[str]:
    """Return the list of reasons that match. Empty -> safe."""
    if not command:
        return []
    return [reason for pat, reason in DANGEROUS_PATTERNS
            if pat.search(command)]
