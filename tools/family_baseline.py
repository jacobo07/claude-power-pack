"""CLI over modules.tower.baselines -- build B0, show, review.

    python tools/family_baseline.py build-b0 <family> <candidates.jsonl>
    python tools/family_baseline.py show <family>
    python tools/family_baseline.py review <family>
    python tools/family_baseline.py verify <family>
    python tools/family_baseline.py revert <family> <id> --reason R --authority A

review lists the entries still `auto` and then verifies the chain. verify
reports every unrecorded weakening between consecutive generations and every
generation whose parent changed after it was written (modules/tower/ratchet).
revert writes B<n+1> with the entry reverted and the change on the record; it
refuses an empty reason or authority, and an id that is not active.

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


def review(family: str) -> int:
    """Entries still `auto` in the newest generation, plus the chain verdict.

    The docstring promised this command since S2; it did not exist until the
    ratchet did, because a review with no way to verify the chain it reviews
    would only be a listing."""
    g = bl.latest(family)
    if not g:
        print("%s: no generation" % family)
        return 0
    auto = [e for e in g["entries"] if e.get("status") == "auto"]
    print("%s B%d: %d auto-promoted entr%s awaiting review"
          % (family, g["generation"], len(auto), "y" if len(auto) == 1 else "ies"))
    for e in auto:
        print("  [auto] %s  %s" % (e["id"], e["requirement"]))
    return verify(family)


def verify(family: str) -> int:
    from modules.tower import ratchet as rt
    rep = rt.verify_chain(family)
    for r in rep.regressions:
        print("  REGRESSION B%d %s %s (no reason+authority on record)"
              % (r["generation"], r["id"], r["kind"]))
    for n in rep.tampered:
        print("  TAMPERED B%d: its parent's bytes changed after it was written" % n)
    print("%s chain: %s (generations %s)" % (family, "OK" if rep.ok else "REGRESSED",
                                              rep.generations))
    return 0 if rep.ok else 1


def revert_cmd(family: str, entry_id: str, reason: str, authority: str) -> int:
    from modules.tower import ratchet as rt
    try:
        path = rt.revert(family, entry_id, reason=reason, authority=authority)
    except rt.RatchetRefusal as exc:
        print("REFUSED: %s" % exc)
        return 2
    print("reverted %s -> %s" % (entry_id, path))
    return 0


def _opt(argv: list, name: str) -> str:
    return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) \
        else ""


def main(argv: list) -> int:
    if len(argv) >= 3 and argv[0] == "build-b0":
        return build_b0(argv[1], argv[2])
    if len(argv) >= 2 and argv[0] == "show":
        return show(argv[1])
    if len(argv) >= 2 and argv[0] == "review":
        return review(argv[1])
    if len(argv) >= 2 and argv[0] == "verify":
        return verify(argv[1])
    if len(argv) >= 3 and argv[0] == "revert":
        return revert_cmd(argv[1], argv[2], _opt(argv, "--reason"), _opt(argv, "--authority"))
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
