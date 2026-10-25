#!/usr/bin/env python
"""V-RECALL-SRC-* gates: default_sources() discovers vault/lessons and vault/hard_rules.

Hermetic: PP_ROOT and HOME are pointed at a temp dir with planted files, so the gate
measures discovery, not whatever the live repo happens to hold.

Run: python tools/test_recall_sources.py
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from modules.gsd_x import recall  # noqa: E402

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def main() -> int:
    d = Path(tempfile.mkdtemp(prefix="test_recall_sources_"))
    old = (recall.PP_ROOT, recall.HOME, os.environ.get("CPP_RECALL_SEO_CORPUS"))
    try:
        pp = d / "pp"
        (pp / "vault" / "lessons").mkdir(parents=True)
        (pp / "vault" / "hard_rules").mkdir(parents=True)
        (pp / "vault" / "plans").mkdir(parents=True)
        (pp / "vault" / "lessons" / "one.md").write_text("# One\n\nlesson one\n", encoding="utf-8")
        (pp / "vault" / "lessons" / "two.md").write_text("# Two\n\nlesson two\n", encoding="utf-8")
        (pp / "vault" / "lessons" / "note.txt").write_text("not markdown", encoding="utf-8")
        (pp / "vault" / "hard_rules" / "HARD_RULES.md").write_text("### HR-X\nTRIGGER: t\n", encoding="utf-8")
        (pp / "vault" / "plans" / "p.md").write_text("# Plan\n", encoding="utf-8")
        recall.PP_ROOT = pp
        recall.HOME = d / "home"
        os.environ["CPP_RECALL_SEO_CORPUS"] = str(d / "no-seo")

        src = recall.default_sources()
        by_kind: dict = {}
        for p, kind, scope in src:
            by_kind.setdefault(kind, []).append((Path(p), scope))

        check("V-RECALL-SRC-CONTROL-PLAN", [p.name for p, _ in by_kind.get("plan", [])] == ["p.md"],
              f"kinds={sorted(by_kind)}")
        lessons = sorted(p.name for p, _ in by_kind.get("lesson", []))
        check("V-RECALL-SRC-LESSONS", lessons == ["one.md", "two.md"], f"lessons={lessons}")
        check("V-RECALL-SRC-LESSON-SCOPE", all(s == "global" for _, s in by_kind.get("lesson", []))
              and bool(by_kind.get("lesson")), "scope=global")
        hr = [p for p, _ in by_kind.get("hard-rules-pp", [])]
        check("V-RECALL-SRC-HARD-RULES", [p.name for p in hr] == ["HARD_RULES.md"]
              and hr[0].parent.name == "hard_rules", f"hard-rules-pp={[str(p) for p in hr]}")
    finally:
        recall.PP_ROOT, recall.HOME = old[0], old[1]
        if old[2] is None:
            os.environ.pop("CPP_RECALL_SEO_CORPUS", None)
        else:
            os.environ["CPP_RECALL_SEO_CORPUS"] = old[2]
        shutil.rmtree(d, ignore_errors=True)

    print(f"RECALL_SRC_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
