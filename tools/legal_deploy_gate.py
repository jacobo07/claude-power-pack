#!/usr/bin/env python3
"""CDIO-10 at publish time (spec vault/specs/cdio-10-publish-gate.md).

stdin: the PreToolUse payload {tool_input: {command}, cwd, session_id}. stdout: {"deny": bool, "reason": str}.
Called by hooks/legal_deploy_gate.js only after its prefilter saw a production web publish. Fail-open: any error
prints {"deny": false} and is ledgered. Kill switch: CPP_LEGAL_DEPLOY_GATE=off.

Declaration (`.cpp-legal.json`, nearest one walking up from the site root):
  {"jurisdiction": "us|eu|es", "saas": false, "b2b": false}
  {"exempt": "<why this publish needs no legal pages, >= 15 chars>"}
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

DECL = ".cpp-legal.json"
MIN_EXEMPT = 15
_CWD_ARG = re.compile(r"--cwd[= ]\s*(\"[^\"]+\"|'[^']+'|\S+)")
_LEAD_CD = re.compile(r"^\s*(?:cd|Set-Location|sl)\s+(\"[^\"]+\"|'[^']+'|\S+)\s*(?:&&|;)", re.I)


def state_dir() -> Path:
    d = Path(os.environ.get("CPP_LEGAL_DEPLOY_STATE_DIR") or Path.home() / ".claude" / "state" / "legal_deploy")
    d.mkdir(parents=True, exist_ok=True)
    return d


def ledger(row: dict) -> None:
    with open(state_dir() / "ledger.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(row, ts=time.time()), ensure_ascii=False) + "\n")


def _unquote(s: str) -> str:
    return s[1:-1] if len(s) > 1 and s[0] == s[-1] and s[0] in "\"'" else s


def site_root(command: str, cwd: str) -> str:
    m = _CWD_ARG.search(command) or _LEAD_CD.search(command)
    root = _unquote(m.group(1)) if m else ""
    if root and not os.path.isabs(root):
        root = os.path.join(cwd, root)
    return os.path.abspath(root or cwd)


def find_decl(root: str) -> str | None:
    d = os.path.abspath(root)
    while True:
        p = os.path.join(d, DECL)
        if os.path.isfile(p):
            return p
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def decide(payload: dict) -> dict:
    command = str((payload.get("tool_input") or {}).get("command") or "")
    cwd = str(payload.get("cwd") or os.getcwd())
    root = site_root(command, cwd)
    row = {"sid": payload.get("session_id"), "root": root, "command": command[:200]}
    decl_path = find_decl(root)
    if not decl_path:
        ledger(dict(row, decision="deny", why="undeclared"))
        return {"deny": True, "reason": (
            "CDIO-10 publish gate: this publishes a website from %s, and no %s declares its legal jurisdiction. "
            "Write %s with {\"jurisdiction\": \"es\"|\"eu\"|\"us\", \"saas\": false, \"b2b\": false} (from the Owner's "
            "facts, never guessed), or, when this publish genuinely needs no legal pages, {\"exempt\": \"<reason>\"}. "
            "Then run the deploy again." % (root, DECL, os.path.join(root, DECL)))}
    try:
        decl = json.loads(Path(decl_path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        ledger(dict(row, decision="deny", why="unreadable", decl=decl_path))
        return {"deny": True, "reason": "CDIO-10 publish gate: %s is not valid JSON (%s); fix it and deploy again."
                % (decl_path, exc)}
    exempt = str(decl.get("exempt") or "").strip()
    if "exempt" in decl:
        if len(exempt) < MIN_EXEMPT:
            ledger(dict(row, decision="deny", why="short exemption", decl=decl_path))
            return {"deny": True, "reason": "CDIO-10 publish gate: the exemption in %s needs a real reason (>= %d "
                    "characters), not %r." % (decl_path, MIN_EXEMPT, exempt)}
        ledger(dict(row, decision="allow", why="exempt", exempt=exempt, decl=decl_path))
        return {"deny": False, "reason": ""}
    from modules.cdio import legal_surface as ls
    jur = str(decl.get("jurisdiction") or "")
    if jur not in ls.JURISDICTIONS:
        ledger(dict(row, decision="deny", why="bad jurisdiction", decl=decl_path))
        return {"deny": True, "reason": "CDIO-10 publish gate: %s has jurisdiction %r; it must be one of %s."
                % (decl_path, jur, list(ls.JURISDICTIONS))}
    rep = ls.check(root, jur, saas=bool(decl.get("saas")), b2b=bool(decl.get("b2b")))
    fails = [v for v in rep["verdicts"] if v["status"] == "fail" and v["severity"] == "critical"]
    if not fails:
        ledger(dict(row, decision="allow", jurisdiction=jur, pages=rep["pages"]))
        return {"deny": False, "reason": ""}
    ledger(dict(row, decision="deny", why="legal floor", jurisdiction=jur,
                fails=[[v["criterion"], v["observed"]] for v in fails]))
    lines = ["CDIO-10 publish gate (%s): this site is not publishable yet (%s)." % (jur, root)]
    for v in fails[:10]:
        lines.append("  - %s: %s%s" % (v["criterion"], v["observed"],
                                       " -> " + v["recommendation"] if v.get("recommendation") else ""))
    lines.append("Fill every page from facts the Owner supplied, never invented ones. If they are missing, ask the "
                 "Owner; do not publish.")
    return {"deny": True, "reason": "\n".join(lines)}


def main() -> int:
    if os.environ.get("CPP_LEGAL_DEPLOY_GATE", "").strip().lower() in ("off", "0", "false"):
        print(json.dumps({"deny": False, "reason": ""}))
        return 0
    try:
        raw = sys.stdin.read().lstrip("﻿")
        payload = json.loads(raw) if raw.strip() else {}
        out = decide(payload if isinstance(payload, dict) else {})
    except Exception as exc:  # noqa: BLE001 -- fail-open, never silently
        try:
            ledger({"decision": "error", "error": "%s: %s" % (type(exc).__name__, exc)})
        except Exception:  # noqa: BLE001
            pass
        out = {"deny": False, "reason": ""}
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
