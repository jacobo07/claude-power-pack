# NOTICE: absorbed source

| | |
|---|---|
| **Upstream** | [realiti4/claude-swap](https://github.com/realiti4/claude-swap) |
| **Author** | Onur Cetinkol |
| **License** | MIT (full text in `LICENSE`) |
| **Docs read at commit** | `ee79e705cf6e1ad3f70621b88b80983a99bb2001` (2026-11-19, main, version 1.2.0b1) |
| **Installed pin** | `claude-swap==1.1.0` from PyPI (latest stable on 2026-11-20), via `uv tool install` |
| **Absorbed** | 2026-11-20 |

## What was taken

- `LICENSE`: verbatim.
- `references/architecture.md`, `references/auto-switch.md`, `references/json-output.md`:
  verbatim from `docs/` at the commit above.
- `references/AGENTS.upstream.md`: verbatim `AGENTS.md`.

## What was not taken, and why

- **No source code is vendored.** Upstream is about 1.7 MB of source plus about 4 MB of tests.
  The tool is installed at a pinned version, so the Power Pack carries no fork to keep in sync.
- `menubar.py` and `docs/menubar.md`: macOS only, and this host is Windows.

## What is ours

- `SKILL.md`: when to route to the tool, the risk table, the host rules (session mode instead of a
  global switch under live panes, the first-run `EOFError`, opt-in auto-switch) and the UKDL lessons.
- `tools/test_claude_swap.py`: the done-gate.

## Observed on this host (2026-11-20, cswap 1.1.0, Windows 11, Python 3.12)

- `cswap status` with an empty store: exit 0, `(not managed)`.
- `cswap list` with an empty store, no TTY: `EOFError` at `switcher._first_run_setup` (input prompt).
- `cswap add`: exit 0, Account 1 registered. After that, `cswap list` exits 0 and reports the 7d and
  Fable windows plus 18 CLI sessions and 7 Cursor IDE windows running.

## Updating the pin

Change `PINNED_VERSION` in `tools/test_claude_swap.py` and the version in `SKILL.md` together, then
run `uv tool install claude-swap==<new> --force` and re-run the gate.
