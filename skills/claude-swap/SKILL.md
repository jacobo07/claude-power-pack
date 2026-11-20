---
name: claude-swap
description: Use when the Owner wants to use, add, switch, inspect or run in parallel more than one Claude Code account, check an account's 5h/7d/per-model usage or reset time, or asks about cswap / claude-swap. Covers the pinned install, the read-only commands, the safe way to run two accounts on a host with many live panes (session mode, never a global switch under them), the first-run prompt that crashes non-interactive shells, and the refresh-token rules that make a careless switch destroy a login. Triggers: cswap, claude-swap, switch account, otra cuenta, cambiar de cuenta, multi-account, usage limit, rate limit, 7d usage, weekly limit, which account.
---

# claude-swap (absorbed, MIT)

Upstream: `realiti4/claude-swap` (MIT, Onur Cetinkol). Attribution and pins: `NOTICE.md`.
Installed as a tool, NOT vendored: `uv tool install claude-swap==1.1.0` -> `~/.local/bin/cswap.exe`.
Done-gate for this absorption: `python tools/test_claude_swap.py` (from the PP repo root).

## What it does

It keeps one backup per Claude Code login in a numbered slot: the credential, plus the
`oauthAccount` block of `~/.claude.json`. A switch writes one slot to where Claude Code reads its
login. The usage dashboard, auto-switch and session mode are all built on top of that.
Backup root on Windows: `~/.claude-swap-backup/`. The credentials live in files under `credentials/`.

## Commands by risk

| Risk | Commands |
|---|---|
| Read-only | `cswap status [--json]`, `cswap list [--json]`, `cswap watch`, `cswap config`, `cswap threshold`, `cswap priority` |
| Writes the backup store only | `cswap add [--slot N] [--alias X]`, `alias`, `disable/enable`, `threshold N pct`, `priority N tier`, `export` |
| Changes the live login of EVERY pane | `cswap switch [N]`, `cswap auto`, `cswap import` (then `switch --force`) |
| Destroys data | `cswap remove N`, `cswap unclaimed --purge ID`, `cswap purge` |

The last two rows count as destructive-state actions: load `destructive-state-authorization`
and get the Owner's yes for the specific command each time.

## Rules on this host

1. **Never run a global `cswap switch` under live panes.** On Windows the credential is a file, and
   Claude Code re-reads it when it changes. Every running pane moves to the new account on its next
   message. On 2026-11-20 `cswap list` counted 18 CLI sessions in 8 directories, plus 7 Cursor IDE
   windows. For parallel work use **session mode**: `cswap run N` (or `cswap run N -- --resume`).
   It sets `CLAUDE_CONFIG_DIR` to a per-account profile, so only that terminal changes account.
   `cswap map N <dir>` binds a repo to an account.
2. **Never `/logout` before `cswap add`.** Claude Code may revoke the refresh token of the account
   being left. Log in with the other account (`/login`), then run `cswap add`.
3. **The first run in a non-interactive shell crashes.** With an empty store, `cswap list` asks
   `Add current account ... [Y/n]`. That reads stdin, and from the agent's PowerShell it dies with
   `EOFError` (observed with 1.1.0, 2026-11-20). Run `cswap add` explicitly first. `cswap status`
   does not prompt.
4. **Never print a credential.** Use `cswap list --token-status`, which summarises state and does
   not dump tokens.
5. **Auto-switch is opt-in, by the Owner.** `cswap auto` rotates subscriptions to stay under rate
   limits. Rotating several accounts specifically to get around usage limits may conflict with
   Anthropic's terms. Do not start it, cron it, or recommend it unprompted. If the Owner asks, use
   `--dry-run` first.
6. **Third-party env vars win.** If `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN` or
   `ANTHROPIC_BASE_URL` is set, it stays in effect after a switch.

## Lessons recorded in UKDL (they hold beyond this tool)

These are the codebase-wide rules from upstream `references/architecture.md`, generalised:

- **A refresh token is single-use.** Once a refresh is posted, its successor must be persisted
  or stashed, whatever else fails. Serialize refreshes per credential through ONE gate that
  re-reads the freshest copy before posting.
- **A live credential goes into a slot only when it is known to belong there.** Writing account
  B's token into A's slot destroys A's only refresh token.
- **Take locks in a fixed order, the foreign tool's own locks included, and make no network call
  under them.** The identity lookup a switch needs is fetched before the locks are taken.
- **Persist only readings.** A label such as "token expired" is derived on every pass and never
  written.

UKDL ids: `PR-SINGLE-USE-REFRESH-SUCCESSOR-001`, `PR-CREDENTIAL-SLOT-OWNERSHIP-001`,
`PR-FOREIGN-LOCK-ORDER-NO-NETWORK-001`.

## References (verbatim upstream, commit pinned in NOTICE.md)

- `references/architecture.md`: module map, the switch, refresh and usage flows, rules.
- `references/auto-switch.md`: exact auto-switch rules (margins, landing, cadence).
- `references/json-output.md`: the `--json` contract (additive only).
- `references/AGENTS.upstream.md`: upstream's rules for agents working on its code.

Note: the references come from upstream `main` (1.2.0b1), and the installed pin is 1.1.0 (the
latest stable on PyPI on 2026-11-20). Before relying on a flag, check it against `cswap <cmd> --help`.
