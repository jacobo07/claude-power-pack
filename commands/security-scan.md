---
name: security-scan
description: Scan the current change for security problems -- semgrep SAST findings on the lines you changed, and known-vulnerable dependencies (OSV) in the project's lockfiles, marked when this change introduced them. Then fix or justify each one. Spec vault/specs/security-scan.md (Gap 4 v1).
---

# /security-scan -- SAST on changed lines + dependency CVEs

## What it does

Runs `tools/security_scan.py` on the current git project:

- **SAST** -- semgrep (`p/default` registry rules, metrics off) on the changed source files.
  Only findings that touch a line changed since `--base` are listed; findings on untouched lines
  are counted as `pre-existing`, not hidden.
- **SCA** -- osv-scanner over every lockfile (`requirements.txt`, `poetry.lock`, `uv.lock`,
  `package-lock.json`, `pnpm-lock.yaml`, `go.mod`, `Cargo.lock`, ...). Each vulnerable package is
  `INTRODUCED` when its lockfile is part of this change, `existing` otherwise.

Both read the project in place and never write to it. Needs network: semgrep fetches its rules
and osv-scanner queries the OSV database.

## Usage

```
/security-scan                 # changes since HEAD (plus untracked files)
/security-scan --base main     # changes since main
```

Run:

```
python ~/.claude/skills/claude-power-pack/tools/security_scan.py --repo . [--base <rev>]
```

## Then

1. Each SAST finding on a changed line: fix it, or state why it is safe here (the input is not
   user-controlled, etc.). Do not suppress a rule to make the list empty.
2. Each `INTRODUCED` vulnerable package: upgrade to a patched version, or state why the vulnerable
   code path is not reachable. `existing` ones are worth reporting to the Owner, not silently
   fixing inside an unrelated change.

## Outcomes

Per scanner: `CLEAN`, `FINDINGS`, or `UNCHECKED` with a reason (missing binary, timeout, network or
rules failure). **UNCHECKED is not clean** -- say it was not checked. Exit 2 only when no scanner
could run or the project changed during the scan.

## Tools

`C:\Users\User\Apps\osv-scanner\osv-scanner.exe` (v2.6.0, checksum-verified official release) and
`C:\Users\User\Apps\semgrep-venv\` (semgrep 1.178.0 in its own venv). Override with `--osv` and
`--semgrep`.
