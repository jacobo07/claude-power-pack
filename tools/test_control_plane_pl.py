"""V-CPP-* gates for tools/control_plane_pl.py."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tools.control_plane_pl as cp  # noqa: E402

FAILS: list[str] = []
N = 0


def check(name, ok, ev=""):
    global N
    N += 1
    if not ok:
        FAILS.append(name)
    print(f"  {'PASS' if ok else 'FAIL'}  {name}  {ev}")


def main() -> int:
    canary = [{"goal": "cp50-c2", "coordinator_tokens": 37_527_020, "worker_tokens": 8_606_329}]
    inc = cp.detect(canary)
    check("V-CPP-CANARY-37.5M", len(inc) == 1 and inc[0]["verdict"] == cp.INCIDENT, str(inc))
    r = cp.detect([{"goal": "3b4f4757", "coordinator_tokens": 4_943_171, "worker_tokens": 0, "cap": 1_500_000}])
    check("V-CPP-CANARY-3b4f4757", len(r) == 1 and r[0]["over_cap"] == 3_443_171, str(r))
    check("V-CPP-WITHIN-CAP", cp.detect([{"goal": "g", "coordinator_tokens": 1_000_000, "worker_tokens": 10}]) == [])
    check("V-CPP-NO-RATIO-GATE", cp.detect([{"goal": "g", "coordinator_tokens": 900, "worker_tokens": 1}]) == [])
    check("V-CPP-UNMEASURABLE", cp.detect([{"goal": "g", "coordinator_tokens": "x"}])[0]["verdict"] == "UNMEASURABLE")
    p = cp.pnl(canary)[0]
    check("V-CPP-PNL", p["total"] == 46_133_349 and 0.81 < p["control_share"] < 0.82, str(p))
    rows = [{"mission_id": "m-aaa1"}, {"mission_id": "m-bbb2"}]
    check("V-CPP-STATUS-FILTER", cp.filter_mission(rows, "m-bbb") == [rows[1]] and cp.filter_mission(rows, None) == rows)
    with tempfile.TemporaryDirectory() as t:
        (Path(t) / "X-receipt.md").write_text("# X receipt\nStatus: DONE\n", encoding="utf-8")
        st = cp.collect_state({"goal": "cp50-c2", "cap": 14_000_000, "used": 8_606_329,
                               "coordinator_tokens": 37_527_020, "worker_tokens": 8_606_329,
                               "missions": [{"id": "m-1", "state": "DONE"}], "next": ["tick"]}, Path(t))
        txt = cp.render_resumption(st)
        check("V-CPP-RESUME", "remaining 5,393,671" in txt and "X-receipt.md: DONE" in txt and cp.INCIDENT in txt)
        check("V-CPP-RESUME-DETERMINISTIC", txt == cp.render_resumption(st))
    print(f"CPP_PASS={N - len(FAILS)}/{N}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
