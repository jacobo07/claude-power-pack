#!/usr/bin/env python3
"""V-ROLL-DISP-*: every sealed capsule gets exactly one disposition, joined per capsule, not counted per day.

Origin 2026-10-23: a status read counted 19 seals, 14 certifications and 2 failures for one DAY and reported
"3 unexplained". Joined per capsule, all 19 were certified (some on another day, 3 after a failed exam).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rollover as ro  # noqa: E402

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def row(ts, event, sid, **kw):
    return {"ts": ts, "event": event, "session_id": sid, **kw}


def main() -> int:
    # Arrange: the 2026-10-22 shape -- certified the next day, a failed exam before a certification,
    # a seal nobody claimed, a claim without a verdict, a re-seal that supersedes an unclaimed capsule.
    rows = [
        row("2026-10-22T10:00:00+00:00", "capsule_sealed", "a"),
        row("2026-10-23T01:00:00+00:00", "successor_claimed", "a", claimant="x"),
        row("2026-10-23T01:05:00+00:00", "resume_certified", "a", claimant="x", wrong=[]),
        row("2026-10-22T11:00:00+00:00", "capsule_sealed", "b"),
        row("2026-10-22T11:10:00+00:00", "successor_claimed", "b", claimant="y"),
        row("2026-10-22T11:11:00+00:00", "resume_failed", "b", claimant="y", wrong=["next"]),
        row("2026-10-22T11:20:00+00:00", "resume_certified", "b", claimant="y", wrong=[]),
        row("2026-10-22T12:00:00+00:00", "capsule_sealed", "c"),
        row("2026-10-22T13:00:00+00:00", "capsule_sealed", "d"),
        row("2026-10-22T13:10:00+00:00", "successor_claimed", "d", claimant="z"),
        row("2026-10-22T14:00:00+00:00", "capsule_sealed", "e"),
        row("2026-10-22T15:00:00+00:00", "capsule_sealed", "e"),
        row("2026-10-22T16:00:00+00:00", "capsule_sealed", "f"),
        row("2026-10-22T16:10:00+00:00", "resume_failed", "f", claimant="w", wrong=[{"key": "head"}]),
    ]
    # Act
    out = ro.dispositions(rows, since="2026-10-22")
    by = {(c["session_id"], c["sealed_at"]): c for c in out["capsules"]}
    # Assert
    check("V-ROLL-DISP-ONE-PER-CAPSULE", len(out["capsules"]) == 7 and all(c["disposition"] for c in out["capsules"]),
          str(out["counts"]))
    check("V-ROLL-DISP-CROSS-DAY-CERTIFIED", by[("a", "2026-10-22T10:00:00+00:00")]["disposition"] == "RESUMED_CERTIFIED")
    b = by[("b", "2026-10-22T11:00:00+00:00")]
    check("V-ROLL-DISP-FAILED-THEN-CERTIFIED", b["disposition"] == "RESUMED_CERTIFIED" and b["failed_exams"] == 1
          and b["failure_classes"] == ["EXAM_NEXT_MISMATCH"], str(b))
    check("V-ROLL-DISP-PENDING", by[("c", "2026-10-22T12:00:00+00:00")]["disposition"] == "PENDING")
    check("V-ROLL-DISP-CLAIMED-NO-VERDICT", by[("d", "2026-10-22T13:00:00+00:00")]["disposition"] == "CLAIMED_NO_VERDICT")
    check("V-ROLL-DISP-SUPERSEDED", by[("e", "2026-10-22T14:00:00+00:00")]["disposition"] == "SUPERSEDED"
          and by[("e", "2026-10-22T15:00:00+00:00")]["disposition"] == "PENDING")
    f = by[("f", "2026-10-22T16:00:00+00:00")]
    check("V-ROLL-DISP-FAILED-TYPED", f["disposition"] == "RESUME_FAILED_TYPED"
          and f["failure_classes"] == ["EXAM_HEAD_MISMATCH"], str(f))
    check("V-ROLL-DISP-UNRECONCILED-COUNT", out["unreconciled"] == 3, str(out["unreconciled"]))  # c, d, e-second
    check("V-ROLL-DISP-SINCE-FILTER", ro.dispositions(rows, since="2026-10-23")["capsules"] == [])
    print(f"ROLL_DISP_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
