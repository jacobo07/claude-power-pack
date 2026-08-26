#!/usr/bin/env python3
"""EED -- what a body of work did to the cost of understanding this repo.

`cognitive_load.measure()` reports, per module, the files you must open and
the upstream public names you must understand to use it. It reports a
LEVEL. Entropy is a DIRECTION, and a level cannot tell you whether a piece
of work made the estate cheaper or more expensive to hold in your head.

This measures the delta between two refs: modules added, owners added,
context cost moved, and entry points left undeclared. A mission that adds
capability while raising the cost of understanding everything else has not
obviously won, and the only way to know is to measure both ends.

    python tools/eed_delta.py --from 9e69d11 --to HEAD

Deliberately not a gate. Complexity is sometimes the right purchase; the
requirement is that it be VISIBLE and argued, not that it be zero.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PP))

from modules.cognitive_load.load import measure  # noqa: E402


def _git() -> str:
    found = shutil.which("git")
    if found:
        return found
    for c in (r"C:\Program Files\Git\cmd\git.exe",
              r"C:\Program Files (x86)\Git\cmd\git.exe"):
        if Path(c).is_file():
            return c
    return "git"


def _measure_at(ref: str) -> dict:
    """context_cost by module at `ref`, via a throwaway worktree."""
    tmp = Path(tempfile.mkdtemp(prefix="eed_"))
    wt = tmp / "t"
    git = _git()
    try:
        r = subprocess.run([git, "-C", str(PP), "worktree", "add", "--detach",
                            str(wt), ref],
                           capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or "").strip()[:200])
        rows = measure(wt)
        return {row["unit"]: row for row in rows}
    finally:
        subprocess.run([git, "-C", str(PP), "worktree", "remove", "--force",
                        str(wt)], capture_output=True, text=True, timeout=120)
        shutil.rmtree(tmp, ignore_errors=True)


def report(before: dict, after: dict, from_ref: str, to_ref: str) -> str:
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    cost_b = sum(r["context_cost"] for r in before.values())
    cost_a = sum(r["context_cost"] for r in after.values())

    moved = []
    for unit in sorted(set(before) & set(after)):
        d = after[unit]["context_cost"] - before[unit]["context_cost"]
        if d:
            moved.append((d, unit))
    moved.sort(reverse=True)

    undeclared_new = [u for u in added if not after[u]["declares_entry_point"]]

    L = [f"EED delta  {from_ref} -> {to_ref}",
         "=" * 62,
         f"  owners      {len(before):3d} -> {len(after):3d}   "
         f"({len(added):+d} added, {len(removed)} removed)",
         f"  context cost {cost_b:6d} -> {cost_a:6d}   "
         f"({cost_a - cost_b:+d}, {_pct(cost_b, cost_a)})"]
    if added:
        L.append(f"  new owners: {', '.join(added)}")
    if removed:
        L.append(f"  retired:    {', '.join(removed)}")
    if undeclared_new:
        L.append(f"  NEW OWNERS WITH NO DECLARED ENTRY POINT: "
                 f"{', '.join(undeclared_new)}")
        L.append("    (a new unit nobody can find the start of is entropy "
                 "even when its code is good)")
    if moved:
        L.append("  existing units whose cost moved:")
        for d, unit in moved[:10]:
            L.append(f"    {d:+5d}  {unit}")
    if not added and not moved:
        L.append("  no structural change to the cost of understanding.")
    L.append("=" * 62)
    L.append("  A rise is not automatically a failure; an UNARGUED rise is.")
    return "\n".join(L)


def _pct(before: int, after: int) -> str:
    if not before:
        return "n/a"
    return f"{(after - before) / before * 100:+.1f}%"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="from_ref", required=True)
    ap.add_argument("--to", dest="to_ref", default="HEAD")
    args = ap.parse_args()
    try:
        before = _measure_at(args.from_ref)
        after = _measure_at(args.to_ref)
    except Exception as exc:  # noqa: BLE001
        print(f"EED delta unavailable: {exc}")
        return 2
    print(report(before, after, args.from_ref, args.to_ref))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
