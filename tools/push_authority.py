"""push_authority.py -- one owner for "may this session push?" (Resource Residency W0, 2026-11-21).

Incident: mission m-e78bdb938339's worker pushed its branch to the PUBLIC origin at 2026-11-20 23:53:24 by calling git
through a PowerShell variable (`& $g push ...`); ovo-push-gate only matched the literal word pair and no layer knew
that a mission worker has no push authority. Invariant enforced here:

    a session that is (or was) a mission worker may push only if that mission holds an explicit push grant.

Identity: Claude Code exports CLAUDE_CODE_SESSION_ID to every shell command (inherited by git and its hooks) and puts
`session_id` in every PreToolUse payload. A session is a mission worker when its id appears in a mission record
(`gsd-mission-<id>.json`: owner / pending / previous_owner / continuations ...). Grants live in their own file
(`push-authority.json`), never inside the mission record, so the supervisor's writes cannot race them away.

Consumers: `.git/hooks/pre-push` (every shell and invocation shape) and `modules/zero-crash/hooks/ovo-push-gate.js`
(PreToolUse, all repos). Exit codes of `check`: 0 allow, 3 deny.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time

SID_ENV = "CLAUDE_CODE_SESSION_ID"


def state_dir() -> str:
    return os.environ.get("GSD_LONG_RUN_STATE_DIR") or os.path.join(os.path.expanduser("~"), ".claude", "state")


def grants_path() -> str:
    return os.path.join(state_dir(), "push-authority.json")


def _load_grants() -> dict:
    try:
        with open(grants_path(), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def scan(session_id: str) -> tuple[list[str], list[str]]:
    """(mission ids whose record names this session anywhere -- every worker field, every epoch;
    records that could not be read). Same semantics as pushAuthority() in ovo-push-gate.js."""
    out, unreadable = [], []
    for p in glob.glob(os.path.join(state_dir(), "gsd-mission-m-*.json")):
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError as e:
            unreadable.append(f"{os.path.basename(p)}:{e.errno}")
            continue
        if session_id in text:
            out.append(os.path.basename(p)[len("gsd-mission-"):-len(".json")])
    return sorted(out), unreadable


def missions_of(session_id: str) -> list[str]:
    return scan(session_id)[0]


def decide(session_id: str | None) -> dict:
    sid = (session_id or "").strip()
    if len(sid) < 8:
        return {"allow": True, "reason": "no Claude session id: not a mission worker", "missions": []}
    missions, unreadable = scan(sid)
    if not missions and unreadable:          # an unreadable record could be this worker's: UNKNOWN refuses
        return {"allow": False, "missions": [],
                "reason": f"push authority UNKNOWN (unreadable mission records: {', '.join(unreadable[:3])}); refusing"}
    if not missions:
        return {"allow": True, "reason": "session is not a mission worker", "missions": []}
    if os.path.exists(grants_path()):
        try:
            with open(grants_path(), encoding="utf-8") as f:
                json.load(f)
        except (OSError, ValueError) as e:     # parity with the gate: a corrupt grants file is UNKNOWN, refuse
            return {"allow": False, "missions": missions,
                    "reason": f"push authority UNKNOWN (grants file unreadable: {e}); refusing"}
    grants = _load_grants()
    granted = [m for m in missions if grants.get(m)]
    if granted:
        return {"allow": True, "reason": f"push granted to {granted[0]}: {grants[granted[0]].get('reason', '')}",
                "missions": missions}
    return {"allow": False, "missions": missions,
            "reason": (f"session {sid[:8]} is a worker of {', '.join(missions)} and no push authority was granted. "
                       "Commit only; the Owner grants a push with "
                       "`python tools/push_authority.py grant --mission <id> --reason \"...\"` from an attended pane.")}


def _write_grants(g: dict) -> None:
    os.makedirs(state_dir(), exist_ok=True)
    tmp = grants_path() + f".tmp-{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(g, f, indent=1)
    os.replace(tmp, grants_path())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="mission push authority")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("--session", default=None)
    g = sub.add_parser("grant"); g.add_argument("--mission", required=True); g.add_argument("--reason", required=True)
    r = sub.add_parser("revoke"); r.add_argument("--mission", required=True)
    sub.add_parser("list")
    a = ap.parse_args(argv)
    if a.cmd == "check":
        d = decide(a.session if a.session is not None else os.environ.get(SID_ENV))
        print(json.dumps(d))
        return 0 if d["allow"] else 3
    if a.cmd in ("grant", "revoke"):
        own = os.environ.get(SID_ENV, "")
        if own and missions_of(own):          # a worker must not grant itself (or any mission) a push
            print(json.dumps({"refused": "grant/revoke from a mission worker session"})); return 3
        grants = _load_grants()
        if a.cmd == "grant":
            grants[a.mission] = {"reason": a.reason, "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        else:
            grants.pop(a.mission, None)
        _write_grants(grants)
        print(json.dumps({a.cmd: a.mission})); return 0
    print(json.dumps(_load_grants(), indent=1)); return 0


if __name__ == "__main__":
    sys.exit(main())
