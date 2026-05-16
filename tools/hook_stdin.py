#!/usr/bin/env python3
"""hook_stdin.py - synthetic hook-payload serializer.

Permanently kills the echo/printf escape-mangling class: shell-quoting
`{"cwd":"C:\\Users\\..."}` through bash collapses the `\\` escapes, the
hook's `JSON.parse` silently fails, `data` falls back to `{}`, and the
hook returns a bare `{"continue":true}` that LOOKS like a logic failure
but is actually corrupted stdin (forensic lesson, 2026-05-16).

The fix is to never hand-craft hook stdin in a shell string. Use a real
JSON serializer:

  CLI:
    python tools/hook_stdin.py SessionStart cwd="C:\\path" session_id=abc
    python tools/hook_stdin.py Stop --out payload.json
    # then:  node some-hook.js < payload.json

  Importable:
    from hook_stdin import make_payload
    p = make_payload("SessionStart", cwd=r"C:\\path", session_id="abc")

Every value is passed verbatim into json.dumps (which correctly escapes
backslashes, quotes, and control chars). stdout is written as bytes with
an explicit trailing LF and ensure_ascii=True so a downstream Node
JSON.parse never chokes on a BOM, a CRLF translation, or a raw backslash.
"""
from __future__ import annotations
import argparse
import json
import sys

# Hook events that take a stdin JSON payload (Claude Code contract).
KNOWN_EVENTS = {
    "PreToolUse", "PostToolUse", "PostToolUseFailure", "Notification",
    "Stop", "PreCompact", "PostCompact", "UserPromptSubmit",
    "SessionStart", "SessionEnd", "PermissionRequest",
}


def make_payload(event: str, **kw) -> dict:
    """Build a hook stdin payload dict.

    `event` populates BOTH `hook_event_name` and the legacy `event`
    alias (some hooks read one or the other). Extra kwargs are merged
    verbatim; `tool_input` may be passed as a dict and is kept nested.
    """
    if not event:
        raise ValueError("event is required")
    payload: dict = {"hook_event_name": event, "event": event}
    for k, v in kw.items():
        if v is None:
            continue
        payload[k] = v
    return payload


def _coerce(raw: str):
    """key=value parsing: try JSON first (so tool_input={...} or
    nums/bools work), else treat as a literal string. split('=', 1)
    so Windows paths with '=' never lose data (audit G7)."""
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return raw


def _parse_kv(args: list[str]) -> dict:
    out: dict = {}
    for a in args:
        if "=" not in a:
            raise SystemExit(
                f"hook_stdin: positional arg must be key=value: {a!r}")
        k, v = a.split("=", 1)  # maxsplit=1 — path backslashes/'=' safe
        out[k.strip()] = _coerce(v)
    return out


def _emit(payload: dict, out_path: str | None) -> int:
    # ensure_ascii=True: no non-ASCII bytes hit the pipe; Node JSON.parse
    # is byte-safe. Explicit '\n' terminator, NO BOM.
    blob = json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n"
    data = blob.encode("ascii")
    if out_path:
        with open(out_path, "wb") as fh:  # binary: no CRLF translation
            fh.write(data)
        sys.stderr.write(f"hook_stdin: wrote {len(data)} bytes -> "
                         f"{out_path}\n")
    else:
        # Bypass text-mode stdout entirely (Windows CRLF + encoding trap).
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Serialize a synthetic hook stdin payload as JSON.")
    ap.add_argument("event", help="hook event name (e.g. SessionStart)")
    ap.add_argument("kv", nargs="*",
                    help="key=value pairs (values JSON-coerced; "
                         "split on first '=' so paths are safe)")
    ap.add_argument("--out", default=None,
                    help="write JSON to this file (binary, no CRLF) "
                         "instead of stdout")
    ap.add_argument("--strict-event", action="store_true",
                    help="reject unknown event names")
    a = ap.parse_args()
    if a.strict_event and a.event not in KNOWN_EVENTS:
        sys.stderr.write(
            f"hook_stdin: unknown event {a.event!r} "
            f"(known: {sorted(KNOWN_EVENTS)})\n")
        return 2
    payload = make_payload(a.event, **_parse_kv(a.kv))
    return _emit(payload, a.out)


if __name__ == "__main__":
    raise SystemExit(main())
