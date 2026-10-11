"""python -m modules.autonomy_gate classify "<question>" [--authorized a,b] [--record --source X]
python -m modules.autonomy_gate obligations add|close|list|compile --session <sid> [...]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .gate import OWNER, classify, record


def _obligations(argv) -> int:
    from modules.gsd_x.goal import session_scope as ss
    from modules.gsd_x.goal.log import GoalLogError, repo_id
    from .obligations import classify_obligation
    ap = argparse.ArgumentParser(prog="modules.autonomy_gate obligations")
    ap.add_argument("op", choices=["add", "close", "list", "compile"])
    ap.add_argument("--session", required=True)
    ap.add_argument("--repo-dir", default=".")
    ap.add_argument("--text")
    ap.add_argument("--source", default="agent")
    ap.add_argument("--severity", default="RED")
    ap.add_argument("--next-action")
    ap.add_argument("--id")
    ap.add_argument("--verdict")
    ap.add_argument("--open", action="store_true")
    a = ap.parse_args(argv)
    try:
        repo = repo_id(Path(a.repo_dir).resolve())
        if a.op == "add":
            if not a.text:
                raise ss.SessionScopeError("add needs --text")
            nxt = a.next_action or a.text
            v = classify_obligation({"severity": a.severity, "next_action": nxt, "actionability": "NOW"})
            act = {"NOW": "NOW", "INFO": "INFO", "HUMAN_PREF": "HUMAN_PREF", "RESOURCE": "RESOURCE"}.get(
                v["category"], "APPROVAL")
            oid = ss.add(repo, a.session, text=a.text, source=a.source, severity=a.severity,
                         actionability=act, owner_class=v["owner"], next_action=nxt)
            print(json.dumps({"id": oid, "actionability": act, "owner_class": v["owner"]}))
        elif a.op == "close":
            if not (a.id and a.verdict):
                raise ss.SessionScopeError("close needs --id and --verdict '<gate>: <result>'")
            ss.close(repo, a.session, a.id, a.verdict)
            print(json.dumps({"id": a.id, "state": "closed"}))
        elif a.op == "list":
            rows = ss.list_obligations(repo, a.session)
            print(json.dumps([r for r in rows if r["state"] == "open"] if a.open else rows,
                             ensure_ascii=False))
        else:
            from modules.daif.turn_obligations import compile_turn
            text = a.text if a.text is not None else sys.stdin.read()
            obs = compile_turn(text)
            for o in obs:
                ss.add(repo, a.session, text=o["text"], source=o["source"], severity=o["severity"],
                       actionability=o["actionability"], owner_class=o["owner_class"],
                       next_action=o["next_action"])
            print(json.dumps(obs, ensure_ascii=False))
        return 0
    except (GoalLogError, ss.SessionScopeError) as exc:
        print(f"obligations: {exc}", file=sys.stderr)
        return 2


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "obligations":
        return _obligations(argv[1:])
    ap = argparse.ArgumentParser(prog="modules.autonomy_gate")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("classify")
    c.add_argument("question")
    c.add_argument("--authorized", default="")
    c.add_argument("--record", action="store_true")
    c.add_argument("--source", default="cli")
    c.add_argument("--session")
    c.add_argument("--chosen")
    a = ap.parse_args(argv)
    v = classify(a.question, authorized=[x for x in a.authorized.split(",") if x])
    if a.record:
        v["recorded"] = record(v, a.question, source=a.source, session=a.session, chosen=a.chosen)
    print(json.dumps(v, ensure_ascii=False))
    return 10 if v["owner"] == OWNER else 0


if __name__ == "__main__":
    sys.exit(main())
