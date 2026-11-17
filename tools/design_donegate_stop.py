#!/usr/bin/env python3
"""Stop: a session that wrote visual files is not done until Taste, the routed skills and a recorded cdio-reviewer
APPROVE of the current bytes all hold (spec vault/specs/design-surface-router.md).

Contract shared with tools/family_donegate_stop.py: judges only a session that wrote a visual file inside its cwd;
blocks at most once per (session, problem set) and never when stop_hook_active; `NO APLICA: design-<check>: <reason>`
in the final message waives that check; every judgement is a row in donegate.jsonl.
Fail-open: any error prints nothing (ledgered). Kill switch: CPP_DESIGN_DONEGATE=off.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

FIX = {
    "design-taste": "fix the page (python -m modules.cdio.taste <page> lists each hit)",
    "design-skills": "load them with the Skill tool and apply them to the files",
    "design-review": "dispatch the cdio-reviewer agent on the rendered surface; it renders and records with "
                     "tools/design_review_record.py, and only an APPROVE of these exact bytes counts",
}


def decide(payload: dict) -> dict | None:
    from modules.cdio import design_route as dr
    sid = str(payload.get("session_id") or payload.get("sessionId") or "")
    cwd = str(payload.get("cwd") or "")
    if not sid or not cwd or not os.path.isdir(cwd):
        return None
    routes = dr.load_routes()
    transcript = str(payload.get("transcript_path") or "")
    st = dr.scan_transcript(transcript, dr.load_session(sid))
    dr.save_session(sid, st)
    res = dr.judge(st, cwd, routes, na=dr.not_applicable(dr.last_assistant_text(transcript)))
    if not res["files"]:
        return None
    row = {"sid": sid, "cwd": cwd, "kinds": res["kinds"], "files": len(res["files"]),
           "problems": [[p["check"], os.path.basename(p["file"])] for p in res["problems"]], "waived": res["waived"]}
    if not res["problems"]:
        dr.append_row("donegate.jsonl", dict(row, decision="pass"))
        return None
    key = hashlib.sha256(json.dumps(sorted([p["check"], p["file"], p.get("sha", ""), p["detail"]]
                                           for p in res["problems"])).encode()).hexdigest()[:16]
    blocked = st.setdefault("blocked", [])
    if payload.get("stop_hook_active") or key in blocked:
        dr.append_row("donegate.jsonl", dict(row, decision="not_blocked", key=key,
                                             why="stop_hook_active" if payload.get("stop_hook_active") else "already blocked once"))
        return None
    blocked.append(key)
    dr.save_session(sid, st)
    dr.append_row("donegate.jsonl", dict(row, decision="block", key=key))
    lines = ["Design done-gate (kind %s): visual work in %s is not done yet." % ("+".join(res["kinds"]), cwd)]
    for check in dr.CHECKS:
        hits = [p for p in res["problems"] if p["check"] == check]
        if hits:
            lines.append("%s -> %s:" % (check, FIX[check]))
            lines += ["  - %s%s" % (os.path.basename(p["file"]) + ": " if p["file"] else "", p["detail"]) for p in hits[:12]]
    lines.append("A check that genuinely does not apply: `NO APLICA: <check>: <reason>` in the final message.")
    return {"decision": "block", "reason": "\n".join(lines)}


def main() -> int:
    if os.environ.get("CPP_DESIGN_DONEGATE", "").strip().lower() in ("off", "0", "false"):
        return 0
    try:
        raw = sys.stdin.read().lstrip("﻿")
        payload = json.loads(raw) if raw.strip() else {}
        out = decide(payload if isinstance(payload, dict) else {})
        if out:
            sys.stdout.write(json.dumps(out, ensure_ascii=False))
    except Exception as exc:  # noqa: BLE001 -- fail-open, never silently
        try:
            from modules.cdio import design_route as dr
            dr.append_row("errors.jsonl", {"hook": "stop", "error": "%s: %s" % (type(exc).__name__, exc)})
        except Exception:  # noqa: BLE001
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
