---
name: powershell-git-path-gap
description: The 2026-05-21 'use PowerShell for git on Windows' rule degrades to 'command not found' on hosts where Git is not on PowerShell's default PATH. Without the absolute path, the agent silently falls back to Bash and re-triggers the MSYS2 bridge hang. Absolute path must be in the rule itself.
metadata:
  type: feedback
related:
  - hook-fanout-systemic-cost.md
  - parallel-batch-large-output-cascade.md
---

## What

The Windows Bash Bridge Reliability rule sealed in `~/.claude/CLAUDE.md` on 2026-05-21 says: "default to the PowerShell tool for git / mix / gh / node / npm". The rule's intent is to bypass the Git-Bash/MSYS2 transport that produces `[Tool result missing due to internal error]`.

**Gap discovered the next session (also 2026-05-21):** on this Windows 11 host, `git` is NOT on PowerShell's PATH. The PATH contains `C:\Program Files\GitHub CLI` and the WinGet `gh` shim, but Git's `cmd` directory (`C:\Program Files\Git\cmd`) is missing. A bare `git status` from PowerShell errors with `git : El término 'git' no se reconoce como nombre de un cmdlet`. Empirically reproduced PASO 0 of this session.

Why this matters: the agent reads the CLAUDE.md rule, runs `git status` in PowerShell, gets the error, and falls back to Bash — re-triggering the exact MSYS2 hang the rule was sealed to prevent. The rule was self-defeating without the absolute path.

## Why

PowerShell does not inherit Git's PATH the way `cmd.exe` does on Windows. Git's installer registers the cmd path in the *user* PATH, but PowerShell sessions spawned by the Claude Code harness in `-NonInteractive` mode (this tool's mode) often inherit a stripped PATH. PowerShell-native cmdlets work; native exes need either PATH registration or absolute invocation.

The same issue likely affects `mix` (Elixir), `gh` (GitHub CLI — though this one IS on PATH here), and any other dev tool installed under `Program Files` whose PATH entry was registered for `cmd.exe` only.

## Rule

When the global Windows Bash Bridge rule says "default to PowerShell for X", verify X is reachable from PowerShell's `-NonInteractive` PATH BEFORE relying on it. Two acceptable fixes per tool:

1. **Inline absolute path in PowerShell command** — e.g. `& 'C:\Program Files\Git\cmd\git.exe' status`. Works without modifying user state.
2. **Idempotent PATH augmentation in `$PROFILE`** — append `$env:PATH += ';C:\Program Files\Git\cmd'` IF the dir exists AND not already on PATH. Survives across sessions, but modifies user shell config.

The PP-canonical answer is (1) inline absolute path. The CLAUDE.md amendment names the verified Git path so the agent doesn't have to re-discover it every session.

## How to apply

- **When invoking git from PowerShell**: always use `& 'C:\Program Files\Git\cmd\git.exe' <args>` (or `$g = 'C:\Program Files\Git\cmd\git.exe'; & $g <args>` for multi-call scripts).
- **When the absolute path is wrong on a different host**: probe `Get-Command git -ErrorAction SilentlyContinue` first; fall back to `Test-Path` on the three standard install locations (Program Files, Program Files (x86), LOCALAPPDATA Programs).
- **NEVER** retry git via Bash after a PowerShell `command not found` — that re-triggers the hang. Fall through to absolute-path PowerShell.
- **NEVER** silently modify `$PROFILE` without telling the Owner — the inline-path fix is reversible by definition; the $PROFILE fix is durable shell-config mutation.

## Reach boundary

Applies to Windows hosts where PowerShell's `-NonInteractive` PATH lacks Git. Reach: every Power Pack session on Windows. Does NOT apply to Linux/VPS sessions (where `git` is always on the system PATH). Does NOT remove the need for the parent rule (PowerShell preferred over Bash) — it completes it.

## Why fix it instead of working around it

Working around (each session re-discovering the path with `Get-Command`) costs ~50 ms and one extra tool call per session start, AND if the discovery happens DURING a parallel batch the discovery probe itself can fall victim to the hook-fanout pipe pressure. Naming the absolute path in CLAUDE.md eliminates the probe step entirely on this host. Cross-host portability is preserved by keeping the `Test-Path` probe pattern as the documented fallback for OTHER hosts.

## Verification

```powershell
$g = 'C:\Program Files\Git\cmd\git.exe'
Test-Path $g    # → True on this host
& $g --version  # → git version 2.x
```

Sealed: 2026-05-21. Lineage: sister to [[hook-fanout-systemic-cost]] (proximate cause = MSYS2 bridge) and [[parallel-batch-large-output-cascade]] (transversal hang family).
