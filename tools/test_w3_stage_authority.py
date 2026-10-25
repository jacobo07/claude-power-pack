#!/usr/bin/env python
"""V-W3B-* gates: stage tag over mission authority (gsd_mission.set_authority).

Hermetic like tools/test_gsd_mission.py: state dir redirected before import, owner turn
found through the `finder=` seam, spend through `spent_fn=`.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="gsd-w3b-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_RESOURCE_ADMISSION"] = "off"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None

NOW = 1_800_000_000.0
M = 1_000_000
SID = "11111111-aaaa-bbbb-cccc-222222222222"
passes = total = 0


def check(gate, cond, ev=""):
    global passes, total
    total += 1
    passes += bool(cond)
    print(("PASS " if cond else "FAIL ") + gate, ev)


def transcript() -> Path:
    p = Path(TMP) / f"{SID}.jsonl"
    rows = [{"type": "user", "timestamp": f"2026-10-25T10:0{i}:00.000Z", "uuid": f"u-{i}",
             "message": {"role": "user", "content": f"owner act {i}"}} for i in range(1, 5)]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return p


TP = transcript()
finder = lambda sid: TP  # noqa: E731
spend = lambda rec: 5 * M  # noqa: E731
turn = lambda i: f"{SID}:2026-10-25T10:0{i}:00"  # noqa: E731
kw = dict(finder=finder, spent_fn=spend, now=NOW)


def fresh(mid):
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    gm.set_authority(mid, 50 * M, owner_turn=turn(1), stage="s1", reason="open s1", **kw)
    return mid


def raises(fn):
    try:
        fn()
    except gm.MissionError as exc:
        return str(exc)
    return None


def main(set_authority=None) -> int:
    sa = set_authority or gm.set_authority

    mid = fresh("m-w3b-a")
    before = gm.load(mid)
    err = raises(lambda: sa(mid, 60 * M, stage="s2", reason="no turn", **kw))
    check("V-W3B-OPEN-NEEDS-OWNER", err is not None and "s2 opens after s1" in err and gm.load(mid) == before, err)
    if set_authority is not None:
        return 0

    rec = sa(mid, 60 * M, owner_turn=turn(2), stage="s2", reason="open s2", **kw)
    last = rec["authority_receipts"][-1]
    check("V-W3B-OPEN-WITH-OWNER", last["stage"] == "s2" and last["stage_opened"] is True
          and rec["authority_tokens"] == 60 * M, last)

    mid = fresh("m-w3b-b")
    rec = gm.set_authority(mid, 70 * M, reason="resize", stage="s1", **kw)
    last = rec["authority_receipts"][-1]
    rec2 = gm.set_authority(mid, 80 * M, reason="resize, no stage", **kw)
    last2 = rec2["authority_receipts"][-1]
    check("V-W3B-RESIZE-SAME-STAGE", rec["authority_tokens"] == 70 * M and last["stage"] == "s1"
          and last["stage_opened"] is False and rec2["authority_tokens"] == 80 * M and last2["stage"] == "s1"
          and last2["stage_opened"] is False, f"{last['stage']} {last2['stage']}")

    mid = fresh("m-w3b-c")
    gm.set_authority(mid, 60 * M, owner_turn=turn(3), stage="s2", **kw)
    n = len(gm.load(mid)["authority_receipts"])
    noop = gm.set_authority(mid, 60 * M, owner_turn=turn(3), stage="s2", **kw)
    err = raises(lambda: gm.set_authority(mid, 60 * M, owner_turn=turn(3), stage="s3", **kw))
    check("V-W3B-REPLAY-OTHER-STAGE", err is not None and len(noop["authority_receipts"]) == n
          and len(gm.load(mid)["authority_receipts"]) == n, err)

    mid = fresh("m-w3b-d")
    low = dict(kw, spent_fn=lambda rec: 40 * M)
    err = raises(lambda: gm.set_authority(mid, 30 * M, owner_turn=turn(4), stage="s1", **low))
    rec = gm.set_authority(mid, 30 * M, owner_turn=turn(4), stage="s1", recognize_overrun=True, **low)
    last = rec["authority_receipts"][-1]
    check("V-W3B-OVERRUN-RECORDED", err is not None and last["stage"] == "s1"
          and last["recognize_overrun"] is True and rec["authority_tokens"] == 30 * M, err)

    # mutant: a set_authority that skips the stage rule must be caught by the OPEN-NEEDS-OWNER check
    def mutant(mission_id, *a, stage=None, **k):
        return gm.set_authority(mission_id, *a, stage=None, **k)

    mid = fresh("m-w3b-e")
    before = gm.load(mid)
    err = raises(lambda: mutant(mid, 60 * M, stage="s2", **kw))
    caught = not (err is not None and "s2 opens after s1" in err and gm.load(mid) == before)
    check("V-W3B-MUTATION-RED", caught, "mutant slipped past the stage rule" if caught else err)

    print(f"W3B_PASS={passes}/{total}")
    return 0 if passes == total else 1


if __name__ == "__main__":
    sys.exit(main())
