"""V-TCHK-* -- a baseline entry's `check` is either runnable or says it is not.

The check field existed in the spec as "machine check (file, glob, regex)" and
every one of the 31 non-empty checks in the four B0s was prose. A ratchet over
prose compares text, and a prose check never runs, so a green could mean
nothing ran at all. These gates pin the grammar's answers and, above all, that
nothing but an evaluated static check can ever report PASS.

Hermetic: a temp repo root and a temp registry.

Run: python tools/test_tower_checks.py     (exit 0 = all gates pass)
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, ".."))
if _PP_ROOT not in sys.path:
    sys.path.insert(0, _PP_ROOT)

from modules.tower import baselines as bl  # noqa: E402
from modules.tower import checks as ck  # noqa: E402

_PASS = 0
_FAIL = 0


def _check(gate, cond, evidence, diagnostic):
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print("  PASS %-38s %s" % (gate, evidence))
    else:
        _FAIL += 1
        print("  FAIL %-38s %s" % (gate, diagnostic))


def _one(check, root, registry=None):
    return ck.evaluate({"id": "e", "check": check}, root, registry)


def main() -> int:
    root = tempfile.mkdtemp(prefix="tchk_")
    try:
        print("V-TCHK gates")
        os.makedirs(os.path.join(root, "src"))
        with open(os.path.join(root, "src", "Plugin.java"), "w", encoding="utf-8") as fh:
            fh.write("getCommand(\"kit\").setExecutor(new KitCommand());\n")
        with open(os.path.join(root, "tests.py"), "w", encoding="utf-8") as fh:
            fh.write("print('ok')\n")
        reg = os.path.join(root, "registry.json")
        with open(reg, "w", encoding="utf-8") as fh:
            json.dump({"verifiers": [{"id": "lobby-npc-gate"}]}, fh)

        # --- static kinds: evaluated here, both poles ----------------------
        r = _one("file:src/Plugin.java", root)
        _check("V-TCHK-FILE-PASS", r.outcome == ck.PASS, "present file -> PASS", r)
        r = _one("file:src/Missing.java", root)
        _check("V-TCHK-FILE-FAIL", r.outcome == ck.FAIL, "absent file -> FAIL", r)
        r = _one("glob:src/*.java", root)
        _check("V-TCHK-GLOB-PASS", r.outcome == ck.PASS, "glob matched -> PASS", r)
        r = _one("glob:src/*.kt", root)
        _check("V-TCHK-GLOB-FAIL", r.outcome == ck.FAIL, "no match -> FAIL", r)
        r = _one("regex:src/Plugin.java::setExecutor\\(", root)
        _check("V-TCHK-REGEX-PASS", r.outcome == ck.PASS, "pattern found -> PASS", r)
        r = _one("regex:src/Plugin.java::registerEvents\\(", root)
        _check("V-TCHK-REGEX-FAIL", r.outcome == ck.FAIL, "pattern absent -> FAIL", r)

        # --- the instrument's own failures are not the subject's -----------
        r = _one("regex:src/Plugin.java::(unclosed", root)
        _check("V-TCHK-REGEX-MALFORMED", r.outcome == ck.MALFORMED,
               "a broken pattern is MALFORMED, never FAIL", r)
        r = _one("regex:src/Missing.java::x", root)
        _check("V-TCHK-REGEX-UNREADABLE", r.outcome == ck.UNREADABLE,
               "an unreadable subject is UNREADABLE, never FAIL", r)
        r = _one("file:../outside.txt", root)
        _check("V-TCHK-PATH-ESCAPE", r.outcome == ck.REFUSED_PATH,
               "a path leaving the repo root is refused", r)
        r = _one("file:C:/Windows/win.ini", root)
        _check("V-TCHK-PATH-ABSOLUTE", r.outcome == ck.REFUSED_PATH,
               "an absolute path is refused", r)

        # --- delegated kinds: resolved, NEVER a PASS ------------------------
        r = _one("registry:lobby-npc-gate", root, reg)
        _check("V-TCHK-REGISTRY-DELEGATED", r.outcome == ck.DELEGATED,
               "a registered verifier is DELEGATED to the repo, not PASS", r)
        r = _one("registry:no-such-gate", root, reg)
        _check("V-TCHK-REGISTRY-MISSING", r.outcome == ck.FAIL,
               "a check naming an unregistered verifier FAILS", r)
        r = _one("registry:lobby-npc-gate", root, os.path.join(root, "absent.json"))
        _check("V-TCHK-REGISTRY-UNREADABLE", r.outcome == ck.UNREADABLE,
               "no readable registry is UNREADABLE, not 'id missing'", r)
        r = _one("registry:lobby-npc-gate", root, None)
        _check("V-TCHK-REGISTRY-NONE", r.outcome == ck.UNREADABLE,
               "no registry supplied is UNREADABLE", r)
        r = _one("test:tests.py", root)
        _check("V-TCHK-TEST-DELEGATED", r.outcome == ck.DELEGATED,
               "an existing test file is DELEGATED, not run and not PASS", r)
        r = _one("test:nope.py", root)
        _check("V-TCHK-TEST-MISSING", r.outcome == ck.FAIL,
               "a check naming a missing test FAILS", r)

        # --- prose and emptiness can never read as a result -----------------
        r = _one("grep for callers of every new public method", root)
        _check("V-TCHK-PROSE", r.outcome == ck.UNRUNNABLE_PROSE,
               "prose is UNRUNNABLE_PROSE", r)
        r = _one("", root)
        _check("V-TCHK-EMPTY", r.outcome == ck.EMPTY, "empty is EMPTY", r)
        r = _one("frobnicate:x", root)
        _check("V-TCHK-UNKNOWN-KIND", r.outcome == ck.UNRUNNABLE_PROSE,
               "an unknown kind is not silently a pass", r)

        # --- the aggregate counts only what was evaluated -------------------
        entries = [{"id": "a", "check": "file:src/Plugin.java"},
                   {"id": "b", "check": "registry:lobby-npc-gate"},
                   {"id": "c", "check": "just words"},
                   {"id": "d", "check": ""}]
        s = ck.summarize(ck.run_checks(entries, root, reg))
        _check("V-TCHK-SUMMARY-HONEST",
               s["PASS"] == 1 and s["DELEGATED"] == 1 and s["UNRUNNABLE_PROSE"] == 1
               and s["EMPTY"] == 1 and s["evaluated"] == 1 and s["population"] == 4,
               "1 PASS of 4, the other three named by kind", s)

        # --- the verifier may not die on an unanticipated entry shape -------
        class Hostile(dict):
            def get(self, *_a, **_k):
                raise RuntimeError("hostile entry")
        results = ck.run_checks([Hostile(id="x"), {"id": "ok", "check": "file:tests.py"}],
                                root, reg)
        outs = [x.outcome for x in results]
        _check("V-TCHK-VERIFIER-ISOLATED", outs == [ck.ERROR, ck.PASS],
               "one hostile entry is ERROR; the next is still judged", outs)

        # --- the REAL population: measured, with a floor --------------------
        real = []
        for fam in ("web_surface", "persistent_state", "kobiicraft_mode", "wii_homebrew"):
            real.extend(bl.active_entries(fam))
        rs = ck.summarize(ck.run_checks(real, root, None))
        print("  real B0 population: %s" % rs)
        _check("V-TCHK-REAL-POPULATION",
               rs["population"] >= 60 and rs["PASS"] == 0
               and rs["UNRUNNABLE_PROSE"] + rs["EMPTY"] == rs["population"],
               "every stored check today is prose or empty; none reads as PASS",
               rs)

        print()
        print("TOWER_CHECKS_PASS=%d/%d  threshold=%d/%d"
              % (_PASS, _PASS + _FAIL, _PASS + _FAIL, _PASS + _FAIL))
        return 0 if _FAIL == 0 else 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
