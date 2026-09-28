"""python -m modules.autonomy_gate classify "<question>" [--authorized a,b] [--record --source X]"""
from __future__ import annotations

import argparse
import json
import sys

from .gate import OWNER, classify, record


def main(argv=None) -> int:
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
