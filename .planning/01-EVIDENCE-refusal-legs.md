# Phase 1 evidence — the refusal legs, driven live (2026-09-19)

Session `37cfb187`. Real extension, real window, real inbox protocol
(`~/.claude/state/terminal-inbox/<sid>.req.json` → `<sid>.ack.json`). Nothing
here is simulated and nothing here was typed.

## Why these two legs could run without an operator

`terminal_inbox.js::decide` resolves ownership by **pid ancestry** — one of this
window's terminals must have a shell `processId` in the request's ancestor chain
— and every refusal is returned *before* the `term.sendText` branch, which is
reachable only through `action: "send"` (`extension.js:100-107`). So a request
built to be refused cannot produce a keystroke, whatever else is wrong with it.
That is what made it safe to drive against the Owner's own live pane.

The probe's ancestor chain, measured from one process-table snapshot:

```
57412 python.exe → 48380 powershell.exe → 53752 cmd.exe → 2640 claude.exe
      → 60832 powershell.exe → 19368 cmd.exe → 60280 Cursor.exe → 61988 Cursor.exe
```

The terminal this window owns is in that chain, so leg A is genuinely *this
window's* request, not a stranger's.

## Leg A — an owned request, answered and refused

`claude_pid` names a pid with no `~/.claude/sessions/<pid>.json`, so the
extension reads `session = null` and `decide()` returns `session-unreadable`.

```
waited_s  0.28
ack       {"status": "refused", "reason": "session-unreadable",
           "window_cwd": "c:\\Users\\User\\.claude\\skills\\claude-power-pack"}
request   claimed and removed by the extension
```

The answering window is this one, by its own `window_cwd`. **HR-CONT-03 holds on
real bytes: no exact target, no keystroke** — and the refusal carries `decide()`'s
own reason rather than a generic failure.

## Leg B — an unowned request: ignored, not typed

`ancestors` is a single pid present in no process table, so `ownedTerminals()` is
empty in every window.

```
waited_s  15.04
ack       none
request   still present, untouched by any window (then removed by the drill)
```

Leg B's silence means something **only because leg A was answered in 0.28 s in
the same run** — an extension that was not polling at all produces leg B's result
exactly. That pairing is the whole evidentiary value.

## The negative control, checked where a keystroke would have landed

Leg A's ownership resolved to a terminal in **the Owner's own working pane**. Had
the identity guard been wrong, the probe line would have been typed there and
submitted. Searching this session's transcript for the probe string:

```
typed user rows carrying it        0
positive control ("gsd_long_run")  801 occurrences — the search is not blind
```

## An instrument failure of mine, in the same measurement

The first version of that control counted **any** `type: "user"` row carrying the
probe string and reported `user_hits=1` → FAIL. A tool result is recorded as a
`type: "user"` row, so my own script's stdout — which prints the probe string —
came back as a user row and read exactly like a keystroke. I nearly reported that
the guard had typed into the Owner's live session.

The fix is to classify the row rather than count it: a typed prompt carries a
plain string or `text` blocks; a tool result carries `tool_result` blocks and a
`toolUseResult` field. Both matches were tool results; typed rows = 0.

> A transcript row that records *my own observation of a thing* and a row that
> records *the thing* are the same `type` here. An instrument that reads the type
> and not the shape cannot tell an echo from an event.

## What is still not proven

The **positive** leg — a request that resolves to an owning window and is really
typed into the subject's terminal, with a second pane shown to receive nothing —
needs a live subject session in a terminal an extension owns, and the drill
cannot create one (`two_pane_drill.py`, module docstring). At the time of this
run the host had **766 MB free of 32 GB (2.4 %)** across 29 `claude` and 30
`Cursor` processes, which is below the run's own 1500 MB floor, so opening a
second window to manufacture a subject was refused on those grounds rather than
attempted. `arm` / `fire` / `observe` remain UNEXERCISED.
