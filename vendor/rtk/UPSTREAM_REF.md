# RTK Upstream Reference

**Project:** RTK — "Rust Token Killer" — high-performance CLI proxy that filters and
summarizes system command output before it reaches the LLM context.

| Field | Value |
|-------|-------|
| Upstream repo | https://github.com/rtk-ai/rtk |
| License | MIT (author: Patrick Szymkowiak) |
| Binary version installed | `rtk 0.40.0` |
| Release tag | `v0.40.0` |
| Windows asset | `rtk-x86_64-pc-windows-msvc.zip` |
| Asset URL | https://github.com/rtk-ai/rtk/releases/download/v0.40.0/rtk-x86_64-pc-windows-msvc.zip |
| Asset SHA256 | `7fc90190f76f55dc170898d0ac755e89f405fc2d1d89f717ad8600640ab0f1ed` |
| Verified against | `checksums.txt` at the same release tag (exact match) |
| Installed to | `~/.claude/bin/rtk.exe` (8,754,176 bytes) |
| Local source archive | `~/Downloads/rtk-develop.zip` (v0.34.3, `develop` branch) — used only for agent `.md` extraction + provenance, never compiled |
| Identity guard | `rtk.exe --version` → `rtk 0.40.0`; subcommand surface (`git`/`grep`/`diff`/`log`/`gain`) confirms rtk-ai, not the `reachingforthejack/rtk` "Rust Type Kit" name collision |

## Integration model

RTK is a per-command output rewriter, not an agent orchestrator. Its upstream
Claude Code hook (`hooks/claude/rtk-rewrite.sh`) is a thin delegator: it reads the
PreToolUse stdin JSON, extracts `.tool_input.command`, runs `rtk rewrite <cmd>`,
and maps the binary exit code to a `hookSpecificOutput` decision:

| Exit | Meaning | Hook behaviour |
|------|---------|----------------|
| 0 | Rewrite found, no permission rule matched | rewrite + auto-allow |
| 1 | No RTK equivalent | pass through unchanged |
| 2 | Deny rule matched | pass through (native deny handles it) |
| 3 | Ask rule matched | rewrite, let Claude Code prompt |

The Power Pack port (`~/.claude/hooks/rtk-rewrite.js`) reimplements this contract
in Node to drop the `jq` + `bash` dependencies on Windows, and resolves the binary
by absolute path (`$RTK_BIN` or `~/.claude/bin/rtk.exe`) because `~/.claude/bin`
is not on `PATH`.

## Refresh procedure

1. Check latest tag: `curl -s https://api.github.com/repos/rtk-ai/rtk/releases/latest`
2. Download `rtk-x86_64-pc-windows-msvc.zip` + `checksums.txt` for that tag.
3. Verify SHA256 against the windows-msvc line in `checksums.txt`.
4. Extract `rtk.exe` → `~/.claude/bin/rtk.exe`; assert `rtk --version`.
5. Update the table above.
