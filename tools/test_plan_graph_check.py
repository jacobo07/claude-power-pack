"""V-PGRAPH-*: tools/plan_graph_check.py -- GSD phase plans judged by the vendored plan graph.

Every verdict is driven from a synthetic phase built here (never a real project's plans), and each
refusal has a green control beside it: a checker that refused everything would pass every refusal.
    python tools/test_plan_graph_check.py
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import plan_graph_check as pg  # noqa: E402

passes = fails = 0


def check(gate: str, cond: bool, ev: object = "") -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {ev}")


def plan(d: Path, pid: str, wave=None, deps=(), files=None, done=False, extra: str = "") -> None:
    fm = [f"phase: {d.name}", f"plan: {pid.split('-')[1]}", "type: execute"]
    if wave is not None:
        fm.append(f"wave: {wave}")
    fm.append(f"depends_on: [{', '.join(repr(x) for x in deps)}]")
    if files is not None:
        fm.append("files_modified: []" if not files else "files_modified:\n" + "\n".join(f"  - {f}  # note" for f in files))
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{pid}-PLAN.md").write_text("---\n" + "\n".join(fm) + extra + "\n---\n\n<objective>x</objective>\n",
                                      encoding="utf-8")
    if done:
        (d / f"{pid}-SUMMARY.md").write_text("# done\n", encoding="utf-8")


def judge(d: Path, root: Path) -> dict:
    return pg.check_phase(d, root)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="pgraph_t_"))
    try:
        root = tmp / "proj"
        (root / ".planning" / "phases").mkdir(parents=True)
        ph = root / ".planning" / "phases"

        print("green control, then one refusal per rule")
        d = ph / "05-ok"
        plan(d, "05-01", 1, files=["src/a.py"])
        plan(d, "05-02", 1, files=["src/b.py"])
        plan(d, "05-03", 2, deps=["05-01", "05-02"], files=["src/a.py", "src/b.py"])
        r = judge(d, root)
        check("V-PGRAPH-GREEN", r["verdict"] == pg.OK and not r["refused"] and not r["unjudged"], r)

        d = ph / "06-overlap"
        plan(d, "06-01", 1, files=["src/a.py"])
        plan(d, "06-02", 1, files=["src/a.py", "src/c.py"])
        r = judge(d, root)
        check("V-PGRAPH-SAME-WAVE-OVERLAP", r["verdict"] == pg.REFUSED
              and any("wave 1" in x and "06-02" in x for x in r["refused"]), r["refused"])

        d = ph / "07-dir-overlap"
        plan(d, "07-01", 1, files=["src"])
        plan(d, "07-02", 1, files=["src/deep/x.py"])
        r = judge(d, root)
        check("V-PGRAPH-DIRECTORY-OVERLAP", r["verdict"] == pg.REFUSED, r["refused"])

        # A real batch reviewer (2026-09-28) claimed `./src/a.py` vs `src/a.py` would MISS an overlap,
        # having seen only _owns(). The vendored overlap normalizes; `..` spellings are refused outright.
        d = ph / "07b-dot-segment"
        plan(d, "07b-01", 1, files=["./src/a.py"])
        plan(d, "07b-02", 1, files=["src/a.py"])
        r = judge(d, root)
        check("V-PGRAPH-DOT-SEGMENT-SAME-KEY", r["verdict"] == pg.REFUSED, r["refused"])
        d = ph / "07c-parent-segment"
        plan(d, "07c-01", 1, files=["src/../src/a.py"])
        plan(d, "07c-02", 1, files=["src/b.py"])
        r = judge(d, root)
        check("V-PGRAPH-PARENT-SEGMENT-NEVER-OK", r["verdict"] != pg.OK, r["refused"] or r["unjudged"])

        d = ph / "08-cross-wave"
        plan(d, "08-01", 1, files=["src/a.py"])
        plan(d, "08-02", 2, deps=["08-01"], files=["src/a.py"])
        r = judge(d, root)
        check("V-PGRAPH-SAME-FILE-DIFFERENT-WAVES-OK", r["verdict"] == pg.OK, r)

        d = ph / "09-wave-order"
        plan(d, "09-01", 1, files=["a"])
        plan(d, "09-02", 1, deps=["09-01"], files=["b"])
        r = judge(d, root)
        check("V-PGRAPH-WAVE-ORDER", r["verdict"] == pg.REFUSED and any("wave order" in x for x in r["refused"]),
              r["refused"])

        d = ph / "10-cycle"
        plan(d, "10-01", 1, deps=["10-02"], files=["a"])
        plan(d, "10-02", 2, deps=["10-01"], files=["b"])
        r = judge(d, root)
        check("V-PGRAPH-CYCLE", r["verdict"] == pg.REFUSED and any("cycle" in x for x in r["refused"]), r["refused"])

        d = ph / "11-unknown-dep"
        plan(d, "11-01", 1, files=["a"])
        plan(d, "11-02", 2, deps=["11-09"], files=["b"])
        r = judge(d, root)
        check("V-PGRAPH-UNKNOWN-SAME-PHASE-DEP", r["verdict"] == pg.REFUSED
              and any("unknown dependency 11-09" in x for x in r["refused"]), r["refused"])

        print("absence: undeclared is not declared-empty")
        d = ph / "12-undeclared"
        plan(d, "12-01", 1, files=["a"])
        plan(d, "12-02", 1, files=None)
        r = judge(d, root)
        check("V-PGRAPH-UNDECLARED-UNJUDGED", r["verdict"] == pg.UNJUDGED
              and any("never declared" in x for x in r["unjudged"]), r["unjudged"])
        d = ph / "13-declared-empty"
        plan(d, "13-01", 1, files=["a"])
        plan(d, "13-02", 1, files=[])
        r = judge(d, root)
        check("V-PGRAPH-DECLARED-EMPTY-JUDGED", r["verdict"] == pg.OK, r)
        d = ph / "14-no-wave"
        plan(d, "14-01", None, files=["a"])
        plan(d, "14-02", 1, files=["b"])
        r = judge(d, root)
        check("V-PGRAPH-NO-WAVE-UNJUDGED", r["verdict"] == pg.UNJUDGED, r["unjudged"])
        d = ph / "15-alone"
        plan(d, "15-01", None, deps=["phase-01"], files=None)
        r = judge(d, root)
        check("V-PGRAPH-LONE-PLAN-NEEDS-NO-WAVE", r["verdict"] == pg.OK, r)
        d = ph / "16-garbled"
        d.mkdir()
        (d / "16-01-PLAN.md").write_text("---\nwave: [unclosed\n---\n", encoding="utf-8")
        plan(d, "16-02", 1, files=["b"])
        r = judge(d, root)
        check("V-PGRAPH-UNREADABLE-UNJUDGED", r["verdict"] == pg.UNJUDGED
              and any("16-01" in x for x in r["unjudged"]), r["unjudged"])

        print("what counts as satisfied")
        d = ph / "17-done-sibling"
        plan(d, "17-01", 1, files=["a"], done=True)
        plan(d, "17-02", 1, files=["a"])
        plan(d, "17-03", 1, files=["z"])
        r = judge(d, root)
        check("V-PGRAPH-DONE-PLAN-EXCLUDED", r["verdict"] == pg.OK and r["pending"] == ["17-02", "17-03"], r)
        audit = pg.check_phase(d, root, include_done=True)
        check("V-PGRAPH-AUDIT-INCLUDES-DONE", audit["verdict"] == pg.REFUSED, audit["refused"])
        d = ph / "18-cross-phase"
        plan(d, "18-01", 1, deps=["05-03"], files=["a"])
        plan(d, "18-02", 1, files=["b"])
        r = judge(d, root)
        check("V-PGRAPH-CROSS-PHASE-DEP-SATISFIED", r["verdict"] == pg.OK, r)
        d = ph / "19-none-pending"
        plan(d, "19-01", 1, files=["a"], done=True)
        check("V-PGRAPH-NOTHING-PENDING", judge(d, root)["verdict"] is None, "no verdict for a finished phase")

        print("worktree absolute paths key under their own git root")
        wt = tmp / "wt"
        (wt / ".git").mkdir(parents=True)
        d = ph / "20-worktree"
        plan(d, "20-01", 1, files=[(wt / "src" / "a.py").as_posix()])
        plan(d, "20-02", 1, files=["src/a.py"])
        r = judge(d, root)
        check("V-PGRAPH-WORKTREE-PATH-COLLIDES", r["verdict"] == pg.REFUSED, r["refused"] or r["unjudged"])
        d = ph / "21-outside"
        plan(d, "21-01", 1, files=["C:/no-git-anywhere-xyz/a.py" if os.name == "nt" else "/no-git-anywhere-xyz/a.py"])
        plan(d, "21-02", 1, files=["b"])
        r = judge(d, root)
        check("V-PGRAPH-NO-GIT-ROOT-UNJUDGED", r["verdict"] == pg.UNJUDGED, r["unjudged"])

        print("a bridge that cannot answer is never OK")
        saved = os.environ.get("CPP_NODE_EXE")
        os.environ["CPP_NODE_EXE"] = str(tmp / "no-node.exe")
        try:
            r = judge(ph / "06-overlap", root)
            r_ok = judge(ph / "05-ok", root)
        finally:
            if saved is None:
                os.environ.pop("CPP_NODE_EXE", None)
            else:
                os.environ["CPP_NODE_EXE"] = saved
        check("V-PGRAPH-BRIDGE-DOWN-UNJUDGED", r["verdict"] == pg.UNJUDGED and r_ok["verdict"] == pg.UNJUDGED,
              (r["unjudged"][:1], r_ok["unjudged"][:1]))

        print("card and CLI")
        res = [judge(ph / "05-ok", root), judge(ph / "06-overlap", root)]
        card = pg.card_lines(res)
        check("V-PGRAPH-CARD-NAMES-REFUSAL", "REFUSED 06-overlap" in card and "one at a time" in card, card)
        check("V-PGRAPH-CARD-GREEN-ONE-LINE", pg.card_lines(res[:1]).startswith("PLAN GRAPH: 3 pending")
              and "\n" not in pg.card_lines(res[:1]), pg.card_lines(res[:1]))
        check("V-PGRAPH-CARD-EMPTY-WHEN-NOTHING", pg.card_lines([]) == "", "")
        check("V-PGRAPH-CLI-EXIT-REFUSED", pg.main([str(ph / "06-overlap")]) == 3, "exit 3")
        check("V-PGRAPH-CLI-EXIT-OK", pg.main([str(ph / "05-ok")]) == 0, "exit 0")
        check("V-PGRAPH-CLI-EXIT-NOTHING", pg.main([str(ph / "19-none-pending")]) == 4, "exit 4")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    total = passes + fails
    print(f"PGRAPH_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
