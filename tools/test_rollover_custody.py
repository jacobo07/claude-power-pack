#!/usr/bin/env python
"""V-CUSTODY-* gates: safe-to-forget refuses when the session's OWN written paths are uncommitted in
another repo (plan ccp-s16 §16.1 S1). Hermetic: two throwaway git repos and a non-repo dir.

Measured 2026-10-03: session a4849588 sealed SAFE_TO_FORGET in an Orca-X worktree while its edit to
the Power Pack's tools/rollover.py was uncommitted; it sat orphaned for 3 days."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rollover as ro  # noqa: E402

PASS = FAIL = 0


def ok(gate, cond, ev=""):
    global PASS, FAIL
    PASS += bool(cond)
    FAIL += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def repo(d: Path) -> Path:
    d.mkdir(parents=True)
    for args in (("init", "-q"), ("config", "user.email", "t@t"), ("config", "user.name", "t"),
                 ("commit", "-q", "--allow-empty", "-m", "root")):
        assert ro._git(d, *args)[0], args
    return d


def custody_missing(fo: dict) -> list[str]:
    comp = ro.completeness({"repo": {"state": "OK", "head": "h", "branch": "b", "dirty": []}, "foreign": fo})
    return [m for m in comp["missing"] if m.startswith("custody")]


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="custody-"))
    home, other, loose = repo(tmp / "home"), repo(tmp / "other"), tmp / "loose"
    loose.mkdir()
    mine, peer, at_home = other / "mine.py", other / "peer.py", home / "a.py"
    for p in (mine, peer, at_home, loose / "note.txt"):
        p.write_text("x\n", encoding="utf-8")
    writes = [str(mine), str(at_home), str(loose / "note.txt")]

    fo = ro.foreign_custody(writes, str(home))
    dirty = [r["dirty"] for r in fo.get("repos", [])]
    ok("V-CUSTODY-OWN-FOREIGN-WRITE-FOUND", fo.get("state") == "OK" and dirty == [["mine.py"]], str(fo))
    ok("V-CUSTODY-PEER-DIRT-NOT-JUDGED", all("peer.py" not in d for d in dirty), str(dirty))
    ok("V-CUSTODY-HOME-REPO-NOT-JUDGED", all(r["root"] != str(home) for r in fo.get("repos", [])), str(fo))
    ok("V-CUSTODY-NON-REPO-COUNTED", fo.get("unchecked_non_repo") == 1, str(fo))
    miss = custody_missing(fo)
    ok("V-CUSTODY-REFUSES", len(miss) == 1 and "mine.py" in miss[0], str(miss))

    assert ro._git(other, "add", "mine.py")[0] and ro._git(other, "commit", "-q", "-m", "mine")[0]
    clean = ro.foreign_custody(writes, str(home))
    ok("V-CUSTODY-COMMITTED-PASSES", clean.get("repos") == [] and not custody_missing(clean), str(clean))

    ok("V-CUSTODY-UNKNOWN-REFUSES", custody_missing(ro._unknown("git status failed")) != [])
    legacy = ro.completeness({"repo": {"state": "OK", "head": "h", "branch": "b", "dirty": []}})
    ok("V-CUSTODY-LEGACY-CAPSULE-NOT-JUDGED", not [m for m in legacy["missing"] if m.startswith("custody")])
    print(f"CUSTODY_PASS={PASS}/{PASS + FAIL}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
