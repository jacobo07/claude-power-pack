"""V-gate: output_contract_stop.js reads the transcript, not the payload.

Regression origin (2026-07-20 PP audit): the hook scanned JSON.stringify(payload)
for slop markers. The Stop payload carries transcript_path -- a path, never the
turn's prose -- so the scan matched nothing the harness ever sends. Wired as-is
it would have been a permanently-silent gate.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "hooks", "output_contract_stop.js")
NODE = r"C:\Program Files\nodejs\node.exe"

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate}: {diagnostic}")


def _assistant(text: str) -> str:
    return json.dumps({
        "type": "assistant",
        "message": {"role": "assistant", "content": [{"type": "text", "text": text}]},
    })


def _user(text: str) -> str:
    return json.dumps({
        "type": "user",
        "message": {"role": "user", "content": [{"type": "text", "text": text}]},
    })


def _run(transcript_lines: list[str] | None) -> dict:
    """Invoke the hook with a realistic Stop payload; return parsed stdout."""
    path = ""
    tmp = None
    if transcript_lines is not None:
        fd, tmp = tempfile.mkstemp(suffix=".jsonl")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write("\n".join(transcript_lines))
        path = tmp
    payload = json.dumps({
        "session_id": "test",
        "transcript_path": path,
        "cwd": os.getcwd(),
        "stop_hook_active": False,
        "hook_event_name": "Stop",
    })
    try:
        proc = subprocess.run([NODE, HOOK], input=payload, capture_output=True,
                              text=True, timeout=30)
        return json.loads(proc.stdout or "{}")
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)


def _fired(out: dict) -> bool:
    return "additionalContext" in out.get("hookSpecificOutput", {})


def main() -> int:
    # The marker is assembled at runtime so this test file does not itself
    # carry the literal token (PP slop-doctrine: a detector's fixtures must
    # not trip the detector).
    marker = bytes.fromhex("706c616365686f6c646572").decode()

    # V-OUTPUT-CONTRACT-FIRES: marker in the last assistant turn -> advisory.
    out = _run([_user("do the thing"), _assistant(f"I left a {marker} here.")])
    if _fired(out):
        _ok("V-OUTPUT-CONTRACT-FIRES", "advisory emitted from transcript text")
    else:
        _fail("V-OUTPUT-CONTRACT-FIRES", f"expected advisory, got {out}")

    # V-OUTPUT-CONTRACT-CLEAN: no marker -> silent. Guards against a gate
    # that fires on everything, which is as useless as one that never fires.
    out = _run([_user("do the thing"), _assistant("All wired and verified.")])
    if not _fired(out) and out.get("continue") is True:
        _ok("V-OUTPUT-CONTRACT-CLEAN", "silent on clean turn")
    else:
        _fail("V-OUTPUT-CONTRACT-CLEAN", f"expected silence, got {out}")

    # V-OUTPUT-CONTRACT-SCOPE: a marker in a PRIOR turn (before the user
    # message that opened this one) must not be attributed to this turn.
    out = _run([_assistant(f"old {marker}"), _user("next"), _assistant("clean now")])
    if not _fired(out):
        _ok("V-OUTPUT-CONTRACT-SCOPE", "prior-turn marker not attributed")
    else:
        _fail("V-OUTPUT-CONTRACT-SCOPE", "leaked a marker from a previous turn")

    # V-OUTPUT-CONTRACT-FAILOPEN: unreadable transcript -> continue, no throw.
    out = _run(None)
    if out.get("continue") is True and not _fired(out):
        _ok("V-OUTPUT-CONTRACT-FAILOPEN", "fail-open on missing transcript")
    else:
        _fail("V-OUTPUT-CONTRACT-FAILOPEN", f"expected fail-open, got {out}")

    # V-OUTPUT-CONTRACT-NEVER-BLOCKS: Stop must always succeed.
    out = _run([_user("x"), _assistant(f"{marker} {marker}")])
    if out.get("continue") is True:
        _ok("V-OUTPUT-CONTRACT-NEVER-BLOCKS", "continue:true even when firing")
    else:
        _fail("V-OUTPUT-CONTRACT-NEVER-BLOCKS", f"blocked Stop: {out}")

    total = _passes + _fails
    print(f"OUTPUT_CONTRACT_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
