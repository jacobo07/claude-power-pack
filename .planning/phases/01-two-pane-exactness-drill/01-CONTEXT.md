# Phase 1: Two-pane exactness drill - Context

**Gathered:** 2026-09-19
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

Prove the exactness claim the transport was rebuilt for: with two live sessions
in two panes, a continuation armed for session A is submitted into A's own
terminal and never into B's, and a request whose owner does not answer is
refused rather than typed into whatever window has focus.

Done: both panes' transcripts read; A carries the resume line, B carries none;
one deliberately unowned request is ledgered `refused` with its reason.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — discuss phase was skipped per user setting. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions.

Known constraints that bound those choices, measured in this session rather than assumed:

- This host has no Orca runtime (`%APPDATA%\orca\orca-runtime.json` absent,
  `ORCA_PANE_KEY` empty), so the route under test is `terminal-inbox`, not
  `orca-exact`. The Orca leg stays unproven and must not be claimed.
- The PP Sessions extension (`kobii.pp-sessions-0.4.0`) is live in this Cursor
  window and answers inbox requests: an owned-but-expired request was refused
  with `reason: expired`, and a control request carrying foreign ancestors was
  ignored. That pair is the shape the drill must reproduce across two panes.
- Ownership is decided by `extension/src/terminal_inbox.js::decide`: exactly one
  of the window's terminals must have a shell `processId` in the request's
  ancestor chain, the `~/.claude/sessions/<pid>.json` identity must agree on
  session id, pid and `procStart`, and status must be exactly `idle`.

</decisions>

<code_context>
## Existing Code Insights

Codebase context will be gathered during plan-phase research. The subjects are
`extension/src/terminal_inbox.js`, `hooks/auto-compact-sendkeys-daemon.ps1`
(`Request-Inbox` / `Poll-Inbox` / `Refuse-NoExact`), `tools/continuation_transport.py`,
and `modules/zero-crash/hooks/context-watchdog.py::_route_for` / `_dispatch_continuation`.

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond the ROADMAP description. The drill must produce
evidence from the two panes' own transcripts, not from the daemon's log alone —
a log line saying a thing was sent is not the pane having received it.

</specifics>

<deferred>
## Deferred Ideas

The `orca-exact` leg (GSDX-C08) stays deferred while no Orca runtime exists on
this host.

</deferred>
