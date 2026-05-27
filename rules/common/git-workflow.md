# Git Workflow

## Commit format

Conventional Commits with PP-tag prefixes:

```
<type>(<scope>): <description>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`,
`ci`, `style`.

Examples:

```
feat(uqf): scaffold modules/uqf + Principle base class
fix(paths): normalize 4 tmpdir path leaks in TCO evidence
docs(standards): SCS v5 C13 + apex axis v5 TCO + L13-L15
test(tco): 8/8 V-* gates TCO suite
```

## Commit body

Keep under ~10 lines unless the change deserves more. Lead with the
"why", not the "what" (the diff already shows what changed).

Footer (mandatory for AI-generated commits):

```
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

## Pre-commit checklist

- [ ] `pytest tests/` passes
- [ ] Relevant V-* gates pass
- [ ] `verify_spp.py` STRICT PASS (or 2 doc-only failures documented)
- [ ] No completion-pending anchors in new code -- finish the slice
      or do not scaffold it (Reality Contract / Jobs-Woz gatekeeper).
      This applies to every variant of incomplete-slice anchor the
      gatekeeper recognises.
- [ ] No leaked absolute paths
- [ ] Heredocs avoid the PowerShell argv-reparser bug
      (use `-F file` instead)

## Push hygiene

- Push to your branch first (`feat/...`), not directly to `main`
  unless you are on an approved fast-path
- `git fetch origin` BEFORE making decisions about what to push
- Refuse to push when `git rev-list --count origin/main ^HEAD` > 0
  (you are behind; pull first)
- After push, verify `REMOTE_DELTA = 0  0`

## Anti-overlap (shared repos)

- Never `git add -A` -- always stage specific files
- Scope commits to the cycle's named files
- If you accidentally stage something out-of-scope:
  `git reset HEAD <path>` and continue
- If you accidentally COMMIT something out-of-scope:
  `git reset HEAD~1 <path>; git commit --amend --no-edit`

## On Windows: heredoc trap (PP-specific)

The PowerShell argv reparser interprets quote characters inside an
`@'...'@` heredoc differently than expected when passed via `-m`,
causing `pathspec did not match` errors.

Use `git commit -F file.txt` instead. The PP wrapper
`tools/git_commit_safe.ps1` (Invoke-GitCommitSafe) automates this.

---

*Portions adapted from ECC (github.com/affaan-m/ecc) under MIT License
(c) 2026 Affaan Mustafa.*
