---
name: secret-scan
description: Full-repository secret sweep (BL-SECRET-001). Walks the current project and runs the Secret Firewall detector over every text file, reporting file + line + pattern name for any leaked credential (API keys, JWTs, connection strings, private keys). Values are always REDACTED -- the raw secret is never printed or logged. Exit 0 = clean, exit 1 = hits found. Pairs with secret_rotation_advisor for remediation (HR-SECRET-007 rotate-first).
---

# /secret-scan -- full-repo credential sweep

## What it does

Scans the current repository for leaked secrets before they reach a
commit or a log. Composes the Secret Firewall detector
(`modules/secret_firewall/detector.py`) -- the same 9-pattern engine the
PreToolUse firewall uses -- so a clean `/secret-scan` and a clean
firewall agree by construction.

Values are **redacted** in all output: you get `pattern_name`, line
number, and severity, never the raw credential.

## Usage

```
PP="$HOME/.claude/skills/claude-power-pack"
python "$PP/tools/secret_scan_repo.py" --path .              # scan cwd
python "$PP/tools/secret_scan_repo.py" --severity CRITICAL   # CRITICAL only
python "$PP/tools/secret_scan_repo.py" --report              # per-hit detail
```

On Windows, run via PowerShell with the absolute python path:

```
$py = 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'
& $py "$env:USERPROFILE\.claude\skills\claude-power-pack\tools\secret_scan_repo.py" --path .
```

## Programmatic equivalent

```python
from tools.secret_scan_repo import scan_repo

results = scan_repo(".", min_severity="CRITICAL")
for rel_path, hits in results:
    for h in hits:
        print(rel_path, h.line_no, h.pattern_name)   # value never exposed
```

## What it finds

API keys (Anthropic / OpenAI / GitHub PAT / AWS), private keys,
database connection strings, JWTs, bearer tokens, and generic
`secret=`/`password=` assignments.

## If it finds something

Do **not** scrub-then-ignore. Per HR-SECRET-007: rotate the credential
at the provider FIRST, revoke the leaked one, then optionally rewrite
history. Run `python tools/secret_rotation_advisor.py` for the
remediation plan.
