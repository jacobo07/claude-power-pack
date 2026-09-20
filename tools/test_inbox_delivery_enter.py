#!/usr/bin/env python
"""V-INBOX-* — the inbox delivery must submit, and the live copy must not drift.

Spec: vault/specs/exact-target-continuation.md (delivery), PR-CONT-06.

WHY (Owner observation, 2026-09-20)
-----------------------------------
A delivery whose ack read `status:"sent"` left the prompt holding `/compact`
and its argument line, UNSUBMITTED. The slash-command completion popup eats
the first Enter. One behaviour, two standing failures:

  * a `/compact` reported delivered while no compaction ever happened;
  * a resume that executed without leaving the ordinary user row
    `user_issued_command_since` looks for, so `resume_confirmed` never fired.

The fix sends a second Enter. This gate pins it, and pins the thing that
would silently undo it: `extension/src/extension.js` in this repo is a MIRROR.
The copy Cursor actually executes lives under `.cursor/extensions/`, so a fix
committed here and not mirrored changes nothing at all -- the same drift class
the dispatcher already taught this estate.

STRUCTURAL BY DESIGN. The send path needs the live `vscode` API, so it cannot
be driven in-process here; this asserts the shipped source and the identity of
the two copies. It is therefore NOT evidence that a delivery submits -- only
the next live delivery is, and §9d of the certification says so. A structural
gate that claimed more than it measures would be the defect it is guarding.
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_EXT = ROOT / "extension" / "src" / "extension.js"
LIVE_DIR = Path.home() / ".cursor" / "extensions"

_passes = 0
_fails = 0
_skips = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  OK   {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate}: {diagnostic}")


def _skip(gate: str, why: str) -> None:
    """Could not ask. Never a pass, never a failure of the subject."""
    global _skips
    _skips += 1
    print(f"  SKIP {gate}: {why}")


def live_copy() -> Path | None:
    """The highest-versioned installed pp-sessions extension, or None."""
    if not LIVE_DIR.is_dir():
        return None
    cands = []
    for d in LIVE_DIR.glob("kobii.pp-sessions-*"):
        js = d / "src" / "extension.js"
        if js.is_file():
            m = re.search(r"-(\d+)\.(\d+)\.(\d+)$", d.name)
            key = tuple(int(x) for x in m.groups()) if m else (0, 0, 0)
            cands.append((key, js))
    if not cands:
        return None
    return max(cands)[1]


def send_path(src: str) -> str | None:
    """The bytes between the terminal lookup and the ack — the delivery."""
    start = src.find("const term = terms[d.terminalIndex]")
    if start < 0:
        return None
    end = src.find("writeAck", start)
    return src[start:end] if end > start else None


def main() -> int:
    print("V-INBOX-* — delivery submits, and the executing copy matches the repo")
    src = REPO_EXT.read_text(encoding="utf-8", errors="replace")

    # POSITIVE CONTROL. Without it, every assertion below is satisfied by a
    # file this gate failed to parse.
    body = send_path(src)
    if not body:
        _fail("V-INBOX-CONTROL-PATH-FOUND",
              "could not locate the delivery block in extension.js — every "
              "other gate here would pass vacuously")
        print(f"\nINBOX_PASS={_passes}/{_passes + _fails}  threshold=5/5  "
              "HARNESS-FAILED")
        return 2
    _ok("V-INBOX-CONTROL-PATH-FOUND", f"delivery block located, {len(body)} chars")

    enters = len(re.findall(r'term\.sendText\("\\r", false\)', body))
    if enters >= 2:
        _ok("V-INBOX-TWO-ENTERS",
            f"{enters} carriage returns after the text — the completion popup "
            "eats the first")
    else:
        _fail("V-INBOX-TWO-ENTERS",
              f"only {enters} carriage return(s): the slash-command popup eats "
              "the first, so the line is typed and never submitted, and the "
              "ack still reads 'sent'")

    # Ordering: the text must be typed before any Enter, or the Enter submits
    # an empty prompt and the text lands in the NEXT turn's box.
    i_text = body.find("term.sendText(req.text")
    i_enter = body.find('term.sendText("\\r"')
    if i_text >= 0 and i_enter > i_text:
        _ok("V-INBOX-TEXT-BEFORE-ENTER", "text is typed before the first Enter")
    else:
        _fail("V-INBOX-TEXT-BEFORE-ENTER",
              f"ordering wrong (text@{i_text}, enter@{i_enter})")

    tail = src[src.find("const term = terms[d.terminalIndex]"):]
    if re.search(r'writeAck\([^)]*enters:\s*2', tail, re.S):
        _ok("V-INBOX-ACK-RECORDS-ENTERS",
            "the ack records how many Enters were sent, so a reader can tell "
            "the builds apart without guessing")
    else:
        _fail("V-INBOX-ACK-RECORDS-ENTERS",
              "the ack does not record `enters`; `status:\"sent\"` alone "
              "asserts only that a call returned (PR-CONT-06)")

    live = live_copy()
    if live is None:
        _skip("V-INBOX-LIVE-MATCHES-REPO",
              "no installed pp-sessions extension found — could not ask. This "
              "is NOT a pass: on the Owner's host the installed copy is the "
              "executing authority.")
    else:
        a = hashlib.sha256(REPO_EXT.read_bytes()).hexdigest()[:16].upper()
        b = hashlib.sha256(live.read_bytes()).hexdigest()[:16].upper()
        if a == b:
            _ok("V-INBOX-LIVE-MATCHES-REPO",
                f"repo and {live.parent.parent.name} identical, sha={a}")
        else:
            _fail("V-INBOX-LIVE-MATCHES-REPO",
                  f"DRIFT: repo {a} != installed {b} ({live}). The repo copy is "
                  "a mirror; Cursor executes the installed one, so a fix that "
                  "lands only here changes nothing.")

    total = _passes + _fails
    print(f"\nINBOX_PASS={_passes}/{total}  threshold=5/5  inconclusive={_skips}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
