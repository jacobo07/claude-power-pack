"""CLI over modules.tower.baselines -- build B0, show, review.

    python tools/family_baseline.py build-b0 <family> <candidates.jsonl>
    python tools/family_baseline.py show <family>

build-b0 re-reads every candidate's cited line (baselines.verify_origin) and
writes B0 from the VERIFIED ones only. WEAK, LINE_MISSING, FILE_MISSING and
MALFORMED are listed by name and left out: an entry whose citation does not
support it is not evidence, and B0 is the one generation nothing precedes.

  exit 0  generation written (or shown)
  exit 1  nothing verified -- no generation written
  exit 2  usage / family already has a B0
"""
from __future__ import annotations

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, ".."))
if _PP_ROOT not in sys.path:
    sys.path.insert(0, _PP_ROOT)

from modules.tower import baselines as bl  # noqa: E402


def build_b0(family: str, src: str) -> int:
    if bl.generations(family):
        print("REFUSED: %s already has generations %s; B0 is written once"
              % (family, bl.generations(family)))
        return 2
    kept, dropped, seen = [], [], set()
    with open(src, "r", encoding="utf-8-sig") as fh:
        for n, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except ValueError:
                dropped.append(("line %d" % n, bl.MALFORMED))
                continue
            # window=0: the cited line itself must carry the vocabulary. A +-3
            # window admitted an entry about motion FLOORS against a line about
            # DECLARING after CLAUDE.md shifted under the citation.
            verdict = bl.verify_origin(e, window=0)
            if verdict != bl.VERIFIED:
                dropped.append((e.get("id", "line %d" % n), verdict))
                continue
            if e["id"] in seen:
                dropped.append((e["id"], "DUPLICATE_ID"))
                continue
            seen.add(e["id"])
            with open(e["origin"]["file"], "r", encoding="utf-8",
                      errors="replace") as src:
                cited = src.read().splitlines()[int(e["origin"]["line"]) - 1]
            e["origin"]["quote"] = " ".join(cited.split())   # drift now detectable
            e["status"] = "reviewed"      # B0 = Owner-sealed governance, cited
            e.setdefault("check", "")
            kept.append(e)
    for ident, why in dropped:
        print("  dropped %-40s %s" % (ident, why))
    if not kept:
        print("NOTHING VERIFIED -- no B0 written for %s" % family)
        return 1
    path = bl.write_generation(family, kept,
                               "B0 from Owner-sealed governance; every entry's "
                               "cited line re-read and verified")
    print("B0 %s: %d entries written, %d dropped -> %s"
          % (family, len(kept), len(dropped), path))
    return 0


def show(family: str) -> int:
    g = bl.latest(family)
    if not g:
        print("%s: no generation" % family)
        return 0
    print("%s B%d (%d entries)" % (family, g["generation"], len(g["entries"])))
    for e in g["entries"]:
        print("  [%s/%s] %s" % (e.get("class"), e.get("status"), e["requirement"]))
    return 0


def main(argv: list) -> int:
    if len(argv) >= 3 and argv[0] == "build-b0":
        return build_b0(argv[1], argv[2])
    if len(argv) >= 2 and argv[0] == "show":
        return show(argv[1])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
