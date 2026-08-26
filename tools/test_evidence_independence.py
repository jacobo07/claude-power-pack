#!/usr/bin/env python3
"""V-EIAA-* -- evidence independence in the global knowledge graph.

`origins` recorded WHERE a claim was found, and the query surface printed
the distinct repos as `repos_represented` -- read, and used, as a
cross-repo proof. Repetition is not independence. A claim copied into four
repos has one ancestor and four addresses, so counting addresses inflated
confidence in exactly the cases where the evidence was weakest.

Both hermetic gates (designed echo sets, so the rule is asserted rather
than the store's current contents) and a live measurement that tracks
reality without pinning it.
"""
from __future__ import annotations

import sys
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PP))

from modules.graphify import global_store as gs  # noqa: E402

EXPECTED_GATES = 7
_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate}: {diag}")


def _entry(files, alts=None):
    return {
        "node_id": "x", "origins": [
            {"repo_id": f"repo{i}", "repo_path": f"/r{i}", "file": f}
            for i, f in enumerate(files)
        ],
        **({"alt_summaries": alts} if alts else {}),
    }


def main() -> int:
    print("V-EIAA -- evidence independence (ancestry, not address count)")

    # Identical content across origins is one text, copied.
    e = _entry(["vault/kb/ukdl.md", "docs/ukdl.md", "a/b/other-name.md"])
    a = gs.ancestry(e)
    if a["independent_roots"] == 1 and "identical_content" in a["echoes"]:
        _ok("V-EIAA-IDENTICAL-CONTENT-IS-ONE-ROOT",
            f"3 origins, 3 distinct filenames, no alternates -> "
            f"{a['independent_roots']} root")
    else:
        _fail("V-EIAA-IDENTICAL-CONTENT-IS-ONE-ROOT", f"got {a}")

    # Same filename in several repos is a copy even when content drifted.
    e = _entry(["vault/kb/ukdl.md", "CW/vault/kb/ukdl.md", "x/ukdl.md"],
               alts=["a drifted summary"])
    a = gs.ancestry(e)
    if a["independent_roots"] == 1 and "identical_filename" in a["echoes"]:
        _ok("V-EIAA-IDENTICAL-FILENAME-IS-ONE-ROOT",
            f"3 origins of one filename, content drifted -> "
            f"{a['independent_roots']} root")
    else:
        _fail("V-EIAA-IDENTICAL-FILENAME-IS-ONE-ROOT", f"got {a}")

    # BOOKEND. Genuinely distinct expressions must NOT be discounted, or the
    # discount is indistinguishable from always answering 1.
    e = _entry(["a/alpha.md", "b/beta.md", "c/gamma.md"],
               alts=["second phrasing", "third phrasing"])
    a = gs.ancestry(e)
    if a["independent_roots"] == 3 and not a["echoes"]:
        _ok("V-EIAA-BOOKEND-INDEPENDENT-SURVIVES",
            "3 distinct filenames with differing content -> 3 roots, no echo")
    else:
        _fail("V-EIAA-BOOKEND-INDEPENDENT-SURVIVES", f"got {a}")

    # BOOKEND. A single origin is one root and is never flagged as an echo.
    a = gs.ancestry(_entry(["only/one.md"]))
    if a == {"origins": 1, "independent_roots": 1, "echoes": []}:
        _ok("V-EIAA-BOOKEND-SINGLE-ORIGIN", "1 origin -> 1 root, no echo")
    else:
        _fail("V-EIAA-BOOKEND-SINGLE-ORIGIN", f"got {a}")

    # Reading must never prune. The lineage stays exactly as recorded.
    e = _entry(["p/one.md", "p/one.md"])
    before = [dict(o) for o in e["origins"]]
    gs.ancestry(e)
    if e["origins"] == before:
        _ok("V-EIAA-NEVER-DESTROYS-LINEAGE",
            "origins identical after ancestry(); the discount is a read")
    else:
        _fail("V-EIAA-NEVER-DESTROYS-LINEAGE", "ancestry() mutated origins")

    # The number has to reach the surface that made the claim.
    res = gs.query_global(cross_repo_only=True)
    if not res:
        _fail("V-EIAA-QUERY-EXPOSES-ROOTS",
              "global layer is empty, so the query surface could not be "
              "exercised -- an environment condition to investigate")
    elif all("independent_roots" in r and "echoes" in r for r in res):
        _ok("V-EIAA-QUERY-EXPOSES-ROOTS",
            f"all {len(res)} global results carry independent_roots + echoes")
    else:
        _fail("V-EIAA-QUERY-EXPOSES-ROOTS",
              "a global result lacks independent_roots/echoes")

    # LIVE. Reports the real discount; tracks reality rather than pinning a
    # number that a future re-index would falsify.
    multi = [r for r in res if r.get("origins") and len(r["origins"]) > 1]
    addresses = sum(len(r["origins"]) for r in multi)
    roots = sum(r.get("independent_roots", 1) for r in multi)
    if not multi:
        _ok("V-EIAA-LIVE-DISCOUNT-OBSERVED",
            "no multi-origin node in the live store; nothing to discount")
    elif roots < addresses:
        _ok("V-EIAA-LIVE-DISCOUNT-OBSERVED",
            f"{len(multi)} multi-origin nodes: {addresses} addresses "
            f"discounted to {roots} independent roots")
    else:
        _fail("V-EIAA-LIVE-DISCOUNT-OBSERVED",
              f"{len(multi)} multi-origin nodes but no discount applied "
              f"({addresses} addresses, {roots} roots)")

    total = _passes + _fails
    print(f"EIAA_PASS={_passes}/{total}  "
          f"threshold={EXPECTED_GATES}/{EXPECTED_GATES}")
    if total != EXPECTED_GATES:
        print(f"FAIL: {total} gates executed, {EXPECTED_GATES} declared")
        return 1
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
