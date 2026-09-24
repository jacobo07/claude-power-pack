"""V-FAMB-* -- the family classifier against its PREDECLARED subjects.

Subjects: vault/audits/ucr_cif/18_FAMILY_MISSION_PREDECLARATION.md (commit
247ffc0), fixed before modules/tower/families.py existed. Every row there is a
gate here, verbatim; nothing is added to make the classifier look good.

Repo subjects are REAL repos. A missing one is INVALID (exit 3), never a
negative: a subject the sweep cannot visit passes by absence, not by judgement.

Run: python tools/test_family_baselines.py     (exit 0 = all gates pass)
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, ".."))
if _PP_ROOT not in sys.path:
    sys.path.insert(0, _PP_ROOT)

from modules.tower import families as fm  # noqa: E402

_PASS = 0
_FAIL = 0
CP = r"C:\Users\User\Desktop\Cursor Projects"

PROMPTS = {
    "web_surface": ("hazme una landing para un restaurante con reservas online",
                    "arregla el crash del escritor de level.dat en la Wii"),
    "kobiicraft_mode": ("crea una nueva modalidad de KobiiCraft tipo skywars con arenas y kits",
                        "hazme una landing para un restaurante con reservas online"),
    "persistent_state": ("añade una tabla de suscripciones con su migración al backend de InfinityOps",
                         "cambia el color del botón del hero"),
    "wii_homebrew": ("porta el menú de CavEX a la Wii con libogc y GX",
                     "crea una nueva modalidad de KobiiCraft tipo skywars con arenas y kits"),
}
REPOS = {
    "web_surface": (CP + r"\CostaLuz Lawyers", CP + r"\Wii Projects\CavEX"),
    "kobiicraft_mode": (CP + r"\Minecraft Projects\KobiiCraft Workspace\KobiiCraft Core Files",
                        CP + r"\CostaLuz Lawyers"),
    "persistent_state": (CP + r"\InfinityOps", CP + r"\Wii Projects\ABSW2-Wii"),
    "wii_homebrew": (CP + r"\Wii Projects\CavEX", CP + r"\InfinityOps"),
}


def _check(gate: str, cond: bool, evidence: str, diagnostic: str) -> None:
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print("  PASS %-40s %s" % (gate, evidence))
    else:
        _FAIL += 1
        print("  FAIL %-40s %s" % (gate, diagnostic))


def main() -> int:
    fams = fm.load_families()
    ids = sorted(f.id for f in fams)
    print("V-FAMB gates -- families loaded: %s" % ids)
    if ids != sorted(PROMPTS):
        print("  INVALID: registry %s != predeclared %s" % (ids, sorted(PROMPTS)))
        return 3

    for fid, (inside, outside) in PROMPTS.items():
        got_in = dict(fm.classify_prompt(inside, fams))
        got_out = dict(fm.classify_prompt(outside, fams))
        _check("V-FAMB-PROMPT-IN-%s" % fid, fid in got_in,
               "hits=%s" % got_in.get(fid), "%r did not classify" % inside)
        _check("V-FAMB-PROMPT-OUT-%s" % fid, fid not in got_out,
               "stays out", "%r over-matched: %s" % (outside, got_out.get(fid)))

    none = fm.classify_prompt("qué hora es", fams)
    _check("V-FAMB-POSITIVE-CONTROL", none == [],
           "'que hora es' -> no family", "false activation: %s" % none)

    hard = dict(fm.classify_prompt(
        "haz una landing para anunciar la nueva modalidad de KobiiCraft", fams))
    _check("V-FAMB-HARD-CASE", "web_surface" in hard and "kobiicraft_mode" not in hard,
           "web yes, kobiicraft mode no", "got %s" % sorted(hard))

    # MECHANISM cases -- not predeclared subjects, and labelled so. Each one
    # isolates a single piece so a mutation of that piece cannot hide behind
    # another trigger (the predeclared persistent_state prompt also matches on
    # 'tabla' and 'backend', so it cannot see the accent fold at all).
    only_accent = dict(fm.classify_prompt("crea la migración", fams))
    _check("V-FAMB-MECH-ACCENT-FOLD", "persistent_state" in only_accent,
           "'migración' matches trigger 'migracion'",
           "accent folding lost: %s" % only_accent)
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(8):
            open(os.path.join(tmp, "f%d.txt" % i), "w").close()
        saved = fm._MAX_ENTRIES
        fm._MAX_ENTRIES = 3
        try:
            rep = fm.repo_family_report(tmp, [f for f in fams if f.id == "wii_homebrew"])
        finally:
            fm._MAX_ENTRIES = saved
    _check("V-FAMB-MECH-TRUNCATED-IS-UNJUDGED",
           rep["unjudged"] == ["wii_homebrew"] and rep["in"] == {},
           "a cut walk reports UNJUDGED, not OUT",
           "truncation read as a verdict: %s" % rep)

    missing = [p for pair in REPOS.values() for p in pair if not os.path.isdir(p)]
    if missing:
        print("  INVALID: repo subjects missing on disk: %s" % missing)
        return 3
    cache: dict = {}
    for fid, (inside, outside) in REPOS.items():
        for p in (inside, outside):
            if p not in cache:
                cache[p] = fm.repo_families(p, fams)
        _check("V-FAMB-REPO-IN-%s" % fid, fid in cache[inside],
               "%s via %s" % (os.path.basename(inside), cache[inside].get(fid)),
               "%s not in %s" % (os.path.basename(inside), fid))
        _check("V-FAMB-REPO-OUT-%s" % fid, fid not in cache[outside],
               "%s stays out" % os.path.basename(outside),
               "%s over-matched via %s" % (os.path.basename(outside),
                                           cache[outside].get(fid)))

    print()
    print("FAMILY_BASELINES_PASS=%d/%d  threshold=%d/%d"
          % (_PASS, _PASS + _FAIL, _PASS + _FAIL, _PASS + _FAIL))
    return 0 if _FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
