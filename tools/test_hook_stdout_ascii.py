#!/usr/bin/env python3
"""V-HSA-*: Python hooks whose stdout Claude Code consumes must survive the live plane's stdout encoding.

Incident (2026-11-22, ~/.claude/state/design_route/errors.jsonl x2): design_donegate_stop.py wrote its block with
json.dumps(ensure_ascii=False) to a cp1252 stdout. A reason naming a non-cp1252 character raised UnicodeEncodeError
AFTER decide() had counted the block, so every later Stop logged "already blocked" and the page shipped with the gate
never shown (session ad5e5284: 7 silent Stops). test_design_route.py could not see it: its env() forces
PYTHONIOENCODING=utf-8, which the live hook-dispatcher.js never sets -- a test plane that is not the production plane.

This suite runs the real entrypoints with PYTHONIOENCODING=cp1252 (the dispatcher's effective encoding here) and a
payload whose output must contain non-cp1252 text. Both poles: the hook must emit parseable JSON carrying the text,
and errors.jsonl must stay empty.
Run: python tools/test_hook_stdout_ascii.py   (exit 0 = all pass)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STOP = ROOT / "tools" / "design_donegate_stop.py"
PROMPT = ROOT / "tools" / "design_route_prompt.py"
FAMILY = ROOT / "tools" / "family_donegate_stop.py"
_TMP = tempfile.mkdtemp(prefix="v-hsa-")
STATE = os.path.join(_TMP, "state")
NON_CP1252 = "菜单"  # CJK: not representable in cp1252 (the incident's pages were en-zh guides)
RESULTS: list = []


def ok(name: str, cond: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(cond)))
    print("  %s %-36s %s" % ("PASS" if cond else "FAIL", name, "" if cond else str(detail)[:400]))


def run(script: Path, payload: dict) -> subprocess.CompletedProcess:
    env = dict(os.environ, CPP_DESIGN_STATE_DIR=STATE, PYTHONIOENCODING="cp1252")
    env.pop("PYTHONUTF8", None)
    return subprocess.run([sys.executable, str(script)], input=json.dumps(payload).encode("utf-8"),
                          capture_output=True, env=env, timeout=120)


def errors() -> list:
    p = Path(STATE, "errors.jsonl")
    return p.read_text(encoding="utf-8").splitlines() if p.exists() else []


def test_stop() -> None:
    d = tempfile.mkdtemp(dir=_TMP)
    page = os.path.join(d, "guide-%s.html" % NON_CP1252)
    Path(page).write_text("<!doctype html><html lang=\"zh\"><head><meta charset=\"utf-8\"><title>t</title></head>"
                          "<body><h1>%s</h1></body></html>" % NON_CP1252, encoding="utf-8")
    t = os.path.join(d, "t.jsonl")
    rows = [{"type": "user", "message": {"role": "user", "content": "haz la landing"}},
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Write", "input": {"file_path": page, "content": "x"}}]}},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "Listo."}]}}]
    Path(t).write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    before = len(errors())
    r = run(STOP, {"session_id": "hsa-stop", "cwd": d, "transcript_path": t})
    try:
        out = json.loads(r.stdout.decode("ascii")) if r.stdout.strip() else None
    except (ValueError, UnicodeDecodeError) as exc:
        out = {"_parse": str(exc)}
    ok("V-HSA-STOP-EMITS-BLOCK", isinstance(out, dict) and out.get("decision") == "block"
       and NON_CP1252 in out.get("reason", ""), (r.stdout[-300:], r.stderr[-300:]))
    ok("V-HSA-STOP-NO-ERROR-ROW", len(errors()) == before, errors()[before:])
    ok("V-HSA-STOP-STDOUT-ASCII", all(b < 128 for b in r.stdout), r.stdout[:120])


def test_prompt() -> None:
    before = len(errors())
    r = run(PROMPT, {"session_id": "hsa-prompt", "prompt": "hazme una landing page %s" % NON_CP1252})
    try:
        out = json.loads(r.stdout.decode("ascii")) if r.stdout.strip() else None
    except (ValueError, UnicodeDecodeError) as exc:
        out = {"_parse": str(exc)}
    ctx = ((out or {}).get("hookSpecificOutput") or {}).get("additionalContext", "")
    ok("V-HSA-PROMPT-EMITS-ROUTE", "Design route" in ctx, (r.stdout[-300:], r.stderr[-300:]))
    ok("V-HSA-PROMPT-NO-ERROR-ROW", len(errors()) == before, errors()[before:])


def test_source_pins() -> None:
    # The three hooks emit ASCII JSON; a revert to ensure_ascii=False on the stdout line reopens the incident.
    for f in (STOP, PROMPT, FAMILY):
        bad = [ln for ln in f.read_text(encoding="utf-8").splitlines()
               if "sys.stdout.write(json.dumps(" in ln and "ensure_ascii=False" in ln]
        ok("V-HSA-PIN-%s" % f.stem.upper(), not bad, bad)


def main() -> int:
    test_stop()
    test_prompt()
    test_source_pins()
    failed = [n for n, c in RESULTS if not c]
    print("V-HSA: %d passed, %d failed" % (len(RESULTS) - len(failed), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
