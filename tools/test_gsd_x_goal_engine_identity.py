#!/usr/bin/env python3
"""V-gates for the engine identity that pins the sweep's autonomy record.

Why this exists: the autonomy record was pinned to repository HEAD. In the shared
tree HEAD moves every 7.6 minutes (median, 79 commits / 48 h, measured
2026-10-02), almost always for files the engine never imports, so a scheduled
sweep would refuse as "stale" on nearly every run. The record now names the
digest of the code that would actually run -- the engine's discovered import
closure -- so an unrelated commit keeps it valid and an engine change voids it.

    python tools/test_gsd_x_goal_engine_identity.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import engine_identity as ei  # noqa: E402
from modules.gsd_x.goal import git_state as gs        # noqa: E402
from modules.gsd_x.goal import sweep as sw            # noqa: E402


def _fixture() -> Path:
    """A miniature PP tree: an engine package, a lazy dependency, an unrelated file."""
    d = Path(tempfile.mkdtemp(prefix="gsdx_engine_id_"))
    goal = d / "modules" / "gsd_x" / "goal"
    goal.mkdir(parents=True)
    # No modules/__init__.py: the real tree's top level is a namespace package.
    (d / "modules" / "gsd_x" / "__init__.py").write_text("", encoding="utf-8")
    (goal / "__init__.py").write_text("", encoding="utf-8")
    (goal / "sweep.py").write_text("from . import log\n", encoding="utf-8")
    (goal / "log.py").write_text(
        "def f():\n    from modules.dep.core import x\n    return x\n", encoding="utf-8")
    dep = d / "modules" / "dep"
    dep.mkdir()
    (dep / "__init__.py").write_text("", encoding="utf-8")
    (dep / "core.py").write_text("x = 1\n", encoding="utf-8")
    tools = d / "tools"
    tools.mkdir()
    (tools / "gsd_x_goal.py").write_text("RUN = 'tools/helper_script.py'\n", encoding="utf-8")
    (tools / "helper_script.py").write_text("print('h')\n", encoding="utf-8")
    for suite in sw.REQUIRED_SUITES:
        (tools / suite).write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
    (d / "unrelated.py").write_text("y = 2\n", encoding="utf-8")
    return d


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def check(g, cond, ev, why):
        (passes if cond else fails).append(g)
        print(f"  {'PASS' if cond else 'FAIL'} {g}: {ev if cond else why}")

    # Arrange: the real tree.
    real = ei.engine_closure(ROOT)
    must = ["modules/gsd_x/goal/sweep.py", "modules/gsd_x/goal/log.py",
            "modules/repo_identity/identity.py", "modules/secret_firewall/detector.py",
            "modules/gsd_x/mission/closure.py", "tools/gsd_x_goal.py",
            # named only by a literal passed to providers/long_run.py:_tools_import
            "tools/gsd_long_run.py", "tools/gsd_mission.py",
            *[f"tools/{s}" for s in sw.REQUIRED_SUITES]]
    missing = [m for m in must if m not in real]
    check("V-ENGINE-CLOSURE-DISCOVERS-LAZY-IMPORTS", not missing,
          f"{len(real)} files, incl. function-level imports (repo_identity, secret_firewall)",
          f"closure misses {missing}")
    check("V-ENGINE-CLOSURE-EXCLUDES-UNRELATED",
          not any(p.startswith(("modules/usage", "tools/usage_index")) for p in real),
          "an unrelated module (usage_index) is outside the closure",
          "the closure swallowed unrelated code; it would go stale on every commit")
    a, b = ei.engine_identity(ROOT), ei.engine_identity(ROOT)
    check("V-ENGINE-ID-DETERMINISTIC", a.startswith("engine:") and a == b,
          f"two reads agree ({a[:20]}...)", f"{a!r} != {b!r}")

    # Act/Assert on the fixture: what moves the identity and what does not.
    fx = _fixture()
    base = ei.engine_identity(fx)
    check("V-ENGINE-ID-FIXTURE-NONEMPTY", base.startswith("engine:"),
          "fixture identity computed", f"got {base!r}")
    (fx / "unrelated.py").write_text("y = 3\n", encoding="utf-8")
    check("V-ENGINE-ID-IGNORES-UNRELATED-CHANGE", ei.engine_identity(fx) == base,
          "changing a file outside the closure keeps the identity",
          "an unrelated change moved the identity")
    p = fx / "modules" / "gsd_x" / "goal" / "log.py"
    # write_text already emits CRLF on Windows: flip the file to the OTHER ending.
    raw = p.read_bytes()
    lf = raw.replace(b"\r\n", b"\n")
    p.write_bytes(lf if raw != lf else lf.replace(b"\n", b"\r\n"))
    check("V-ENGINE-ID-EOL-FLIPPED", p.read_bytes() != raw,
          "precondition: the file's line endings really changed", "the flip did nothing")
    check("V-ENGINE-ID-EOL-NEUTRAL", ei.engine_identity(fx) == base,
          "a CRLF checkout of the same code has the same identity (finding B1)",
          "line endings changed the identity")
    (fx / "modules" / "dep" / "core.py").write_text("x = 2\n", encoding="utf-8")
    lazy = ei.engine_identity(fx)
    check("V-ENGINE-ID-TRACKS-LAZY-DEP", lazy != base,
          "a change in a function-level import moves the identity",
          "a lazily imported dependency changed and the identity did not")
    (fx / "tools" / "helper_script.py").write_text("print('i')\n", encoding="utf-8")
    check("V-ENGINE-ID-TRACKS-SCRIPT-LITERAL", ei.engine_identity(fx) != lazy,
          "a script the engine names by path is part of the identity",
          "a .py path literal was not followed")
    (fx / "tools" / sw.REQUIRED_SUITES[0]).unlink()
    check("V-ENGINE-ID-UNKNOWN-WITHOUT-SEEDS", ei.engine_identity(fx) == "",
          "a missing required suite is UNKNOWN, never a partial identity",
          "an incomplete engine produced an identity")

    # The verdict, on the real tree, with a record whose HEAD is deliberately wrong.
    goals = Path(tempfile.mkdtemp(prefix="gsdx_engine_goals_")) / "goals"
    goals.mkdir(parents=True)
    os.environ["GSDX_GOALS_ROOT"] = str(goals)
    rec = sw.record_path()
    rec.parent.mkdir(parents=True, exist_ok=True)
    green = {s: {"ok": True} for s in sw.REQUIRED_SUITES}

    rec.write_text(json.dumps({"head": "0" * 40, "engine": a, "green": True,
                               "suites": green}), encoding="utf-8")
    ok, why = sw.autonomy_verdict(ROOT)
    check("V-ENGINE-VERDICT-SURVIVES-UNRELATED-COMMIT", ok,
          f"same engine, other HEAD -> allowed ({why})", f"refused: {why}")

    rec.write_text(json.dumps({"head": gs.head(ROOT), "engine": "engine:" + "f" * 64,
                               "green": True, "suites": green}), encoding="utf-8")
    ok, why = sw.autonomy_verdict(ROOT)
    check("V-ENGINE-VERDICT-REFUSES-OTHER-ENGINE",
          not ok and "re-run `record-gates`" in why,
          "same HEAD, other engine -> refused: the engine identity wins", f"allowed: {why}")

    rec.write_text(json.dumps({"head": "0" * 40, "engine": a, "green": False,
                               "suites": green}), encoding="utf-8")
    ok, why = sw.autonomy_verdict(ROOT)
    check("V-ENGINE-VERDICT-RED-STILL-REFUSED", not ok and "not green" in why,
          "a matching engine does not license a red record", f"allowed: {why}")

    rec.write_text(json.dumps({"head": "0" * 40, "green": True, "suites": green}),
                   encoding="utf-8")
    ok, why = sw.autonomy_verdict(ROOT)
    check("V-ENGINE-VERDICT-LEGACY-RECORD-USES-HEAD", not ok and "re-run" in why,
          "a record without an engine digest keeps the HEAD rule (stale here)",
          f"allowed: {why}")

    print(f"\nGSDX_ENGINE_ID_PASS={len(passes)}/{len(passes) + len(fails)}  "
          f"threshold={len(passes) + len(fails)}/{len(passes) + len(fails)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
