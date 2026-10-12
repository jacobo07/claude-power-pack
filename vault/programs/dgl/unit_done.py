"""dgl bootstrap: give chain-armed packet missions a done-check (until W3/W5 lands it in the chain driver).

    python unit_done.py check <receipt.md>            exit 0 = receipt says Status: DONE, 1 = not (yet), 2 = unreadable
    python unit_done.py attach <mission_id> <receipt.md>   store done_check on the mission record (CAS transition)

Why: gsd_mission.supervise asks GSD whether a stopped worker's work remains. pp-dgl has no GSD phases, so it answers
NO_PHASES and the mission stays BLOCKED for ever, holding the root (W1b, 2026-10-10). A record with `done_check` is
completed from its own receipt first (gsd_mission.py:3265-3279). Zero model. Kill switch: just do not attach.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

PY = r"C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe"
LIVE = Path.home() / ".claude" / "skills" / "claude-power-pack" / "tools"


def receipt_done(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return 1
    m = re.search(r"^\s*Status:\s*\**\s*([A-Z_]+)", text, re.M)
    if not m:
        return 2
    return 0 if m.group(1) == "DONE" else 1


def attach(mid: str, receipt: str) -> int:
    sys.path.insert(0, str(LIVE))
    import gsd_mission as gm  # noqa: E402
    rec = gm.load(mid) if hasattr(gm, "load") else None
    if rec is None:
        import json
        rec = json.loads((gm.lr.state_dir() / f"gsd-mission-{mid}.json").read_text(encoding="utf-8-sig"))
    argv = [PY, str(Path(__file__).resolve()), "check", str(Path(receipt).resolve())]
    if rec.get("done_check") == argv:
        print(f"done_check already set on {mid}")
        return 0
    gm.transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"], event="done_check_attached",
                  done_check=argv)
    print(f"done_check attached to {mid} ({rec['state']}): {receipt}")
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["check"] and len(a) == 2:
        sys.exit(receipt_done(Path(a[1])))
    if a[:1] == ["attach"] and len(a) == 3:
        sys.exit(attach(a[1], a[2]))
    print(__doc__)
    sys.exit(2)
