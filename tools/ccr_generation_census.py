"""CCR generation census (A2-14): which live Claude processes run a stale CCR release.

Joins the host's live-session listing with each session's newest `start` receipt (tools/ccr_release.session_status) and
reports per process: pid, session, start time, loaded release, current release, stale. The Stale CCR Process Ratio is
STALE / (STALE + CURRENT); DEV and UNKNOWN sessions have nothing to compare, so they are counted but never enter the
ratio, and an empty denominator is null, not 0 (absent is not zero).

Migration policy: a process cannot swap its own release. Only a NEW process loads the current one (`/restart`, or
`claude --resume <id>` from a shell); `/clear` keeps the process and never migrates. impact_class (ACTIVE.json) says
what a stale process loses: none | hook | policy | breaking.

Usage: ccr_generation_census.py [--root ~/.claude/ccr] [--listing ~/.claude/sessions] [--receipts DIR ...]
Read-only. Prints JSON.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ccr_release as cr  # noqa: E402

MIGRATION = "rotation needs a new process (/restart or claude --resume); /clear never migrates"


def census(root: Path, listing: Path, receipt_dirs: list[Path], alive=cr._alive, proc_start=cr._proc_start) -> dict:
    st = cr.session_status(root, listing, [root / "state" / "receipts", *receipt_dirs], alive, proc_start)
    rows = [{"pid": r["pid"], "sid": r["sid"], "startTs": r.get("startTs"), "loaded": r["loaded"], "current": st["active"],
             "state": r["state"], "stale": r["stale"]} for r in st["sessions"]]
    c = st["counts"]
    den = c["STALE"] + c["CURRENT"]
    try:
        impact = json.loads((root / "ACTIVE.json").read_text(encoding="utf-8")).get("impact_class")
    except (OSError, ValueError, AttributeError):
        impact = None  # no ACTIVE.json, or one from before A2: the class is unknown
    return {"active": st["active"], "impact_class": impact, "processes": rows, "counts": c,
            "stale_ratio": round(c["STALE"] / den, 3) if den else None, "migration": MIGRATION}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=cr.DEFAULT_ROOT)
    ap.add_argument("--listing", type=Path, default=Path.home() / ".claude" / "sessions")
    ap.add_argument("--receipts", type=Path, action="append", default=[])
    a = ap.parse_args(argv)
    print(json.dumps(census(a.root, a.listing, a.receipts), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
