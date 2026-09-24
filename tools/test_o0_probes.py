"""V-O0-* -- every O0 probe mode can return every answer (20_O0 §6).

A probe that can only return one verdict carries no information when it returns
it. Each mode is driven on synthetic repos to MET, NOT_MET and NOT_APPLICABLE,
using the REAL probes from vault/tower/o0/probes.json (not copies), so a probe
edit is exercised here the moment it lands.

Run: python tools/test_o0_probes.py     (exit 0 = all gates pass)
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import o0_measure as om  # noqa: E402

_PASS = 0
_FAIL = 0


def _check(gate, cond, evidence, diagnostic):
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print("  PASS %-40s %s" % (gate, evidence))
    else:
        _FAIL += 1
        print("  FAIL %-40s %s" % (gate, diagnostic))


def _repo(root, name, files):
    base = os.path.join(root, name)
    for rel, text in files.items():
        p = os.path.join(base, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    return base


def main() -> int:
    spec, _ = om.load_probes()
    P = {p["entry"]: p for p in spec["probes"]}
    tmp = tempfile.mkdtemp(prefix="o0_gate_")
    try:
        print("V-O0 gates")
        v = lambda repo, eid: om.evaluate(repo, P[eid])["verdict"]   # noqa: E731

        # every_applicable_file
        gui = "kobiicraft_mode-gui-click-handler-standards"
        ok = _repo(tmp, "gui_ok", {"A.java": "void on(InventoryClickEvent e){ e.setCancelled(true); }"})
        bad = _repo(tmp, "gui_bad", {"A.java": "void on(InventoryClickEvent e){ }",
                                     "B.java": "void on(InventoryClickEvent e){ e.setCancelled(true); }"})
        none = _repo(tmp, "gui_none", {"A.java": "class A {}"})
        _check("V-O0-EVERY-FILE-POLES",
               (v(ok, gui), v(bad, gui), v(none, gui)) == (om.MET, om.NOT_MET, om.NA),
               "MET / NOT_MET (one of two handlers) / NOT_APPLICABLE",
               "got %s" % [v(ok, gui), v(bad, gui), v(none, gui)])

        # no_file, with the float literal traps
        fl = "wii_homebrew-float-literals-need-f-suffix"
        f_ok = _repo(tmp, "f_ok", {"a.c": 'float x = 1.0f; const char* v = "1.0"; /* v1.2.3 */\n'
                                          'int y = 3;\n'})
        f_bad = _repo(tmp, "f_bad", {"a.c": "float x = 1.0;\n"})
        f_none = _repo(tmp, "f_none", {"readme.md": "no c here"})
        _check("V-O0-NO-FILE-FLOAT-POLES",
               (v(f_ok, fl), v(f_bad, fl), v(f_none, fl)) == (om.MET, om.NOT_MET, om.NA),
               "1.0f / \"1.0\" / 1.2.3 pass, bare 1.0 fails, no C -> NA",
               "got %s" % [v(f_ok, fl), v(f_bad, fl), v(f_none, fl)])
        px = "wii_homebrew-no-posix-headers"
        _check("V-O0-NO-FILE-POSIX",
               v(_repo(tmp, "px_bad", {"a.c": "#include <unistd.h>\n"}), px) == om.NOT_MET
               and v(_repo(tmp, "px_ok", {"a.c": "#include <gccore.h>\n"}), px) == om.MET,
               "<unistd.h> fails, <gccore.h> passes", "posix probe cannot discriminate")

        # any_file with applies_if; the fix may live in ANOTHER file
        rm = "web_surface-experience-floors-not-arbitrable"
        anim_ok = _repo(tmp, "anim_ok", {"a.css": ".x{transition: all .2s}",
                                         "g.css": "@media (prefers-reduced-motion: reduce){*{transition:none}}"})
        anim_bad = _repo(tmp, "anim_bad", {"a.css": ".x{transition: all .2s}"})
        anim_none = _repo(tmp, "anim_none", {"a.css": ".x{color:red}"})
        _check("V-O0-ANY-FILE-POLES",
               (v(anim_ok, rm), v(anim_bad, rm), v(anim_none, rm)) == (om.MET, om.NOT_MET, om.NA),
               "global reduced-motion MET / missing NOT_MET / no animation NA",
               "got %s" % [v(anim_ok, rm), v(anim_bad, rm), v(anim_none, rm)])

        # truncation is UNJUDGED, never a verdict about the repo
        saved = om.MAX_ENTRIES
        om.MAX_ENTRIES = 1
        try:
            trunc = v(_repo(tmp, "trunc", {"a.txt": "", "b.txt": "", "c.java": "InventoryClickEvent"}), gui)
        finally:
            om.MAX_ENTRIES = saved
        _check("V-O0-TRUNCATED-IS-UNJUDGED", trunc in (om.UNJUDGED,),
               "a cut walk judges nothing", "got %s" % trunc)

        # coverage: the probe set covers B0 exactly once
        _check("V-O0-COVERS-B0-ONCE", om.coverage_check(spec) == [],
               "60 entries, each probed or classed once", "gaps: %s" % om.coverage_check(spec))

        print()
        print("O0_PROBES_PASS=%d/%d  threshold=%d/%d"
              % (_PASS, _PASS + _FAIL, _PASS + _FAIL, _PASS + _FAIL))
        return 0 if _FAIL == 0 else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
