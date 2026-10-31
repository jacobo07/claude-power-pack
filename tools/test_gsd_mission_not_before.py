"""V-RES-NB-* gates for the `not_before` resource kind (a clock wait that costs no launch and no iteration).

Origin 2026-10-31, mission m-a0dea5075a85: the only remaining units needed the 00:00 UTC quota reset. Each relayed
worker reconciled, found nothing it could run, and exited, so epochs 14-18 each spent an iteration. The mission
reached max_cycles 30 and HALTED before the reset arrived. A typed clock requirement parks the mission under the
existing WAIT_RESOURCE hold instead.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ.setdefault("CPP_MISSION_STATE_DIR", tempfile.mkdtemp(prefix="nb-state-"))

import mission_resources as mres  # noqa: E402

PASS: list[str] = []
FAIL: list[str] = []


def check(gate: str, cond: bool, ev: str = "") -> None:
    (PASS if cond else FAIL).append(gate)
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def _ev(arg, now):
    req = [{"id": "O-1-not_before", "kind": "not_before", "arg": arg, "obligation": "O-1"}]
    return mres.evaluate(req, probes={**mres.PROBES, "not_before": lambda _a: now})


def main() -> int:
    t = 1793491200.0  # 2026-11-01T00:00:00Z
    iso = "2026-11-01T00:00:00+00:00"
    check("V-RES-NB-KIND", "not_before" in mres.KINDS and "not_before" in mres.PROBES, str(mres.KINDS))
    # Arrange/Act/Assert per pole: before, at, after; epoch and ISO spellings agree.
    before = _ev(iso, t - 60)
    check("V-RES-NB-BEFORE-UNMET", not before["admissible"]
          and before["obligations"]["O-1"]["status"] == mres.UNMET, mres.reason(before))
    at = _ev(iso, t)
    check("V-RES-NB-AT-MET", at["admissible"] and at["actionable"] == ["O-1"], str(at["obligations"]))
    after = _ev(str(t), t + 5)
    check("V-RES-NB-EPOCH-MET", after["admissible"], str(after["obligations"]))
    z = _ev("2026-11-01T00:00:00Z", t - 1)
    check("V-RES-NB-Z-SUFFIX-UNMET", z["obligations"]["O-1"]["status"] == mres.UNMET, str(z["obligations"]))
    # A naive ISO time is ambiguous across hosts (laptop CET vs GEX44 UTC): it must be UNKNOWN, never MET.
    naive = _ev("2026-11-01T00:00:00", t + 86400)
    check("V-RES-NB-NAIVE-UNKNOWN", naive["obligations"]["O-1"]["status"] == mres.UNKNOWN and not naive["admissible"],
          str(naive["obligations"]))
    junk = _ev("tomorrow", t + 86400)
    check("V-RES-NB-JUNK-UNKNOWN", junk["obligations"]["O-1"]["status"] == mres.UNKNOWN, str(junk["obligations"]))
    # The waiting detail drifts every second; the evaluation key must not, or every sweep pass rewrites the record.
    check("V-RES-NB-KEY-STABLE", mres.key(_ev(iso, t - 600)) == mres.key(_ev(iso, t - 5)), mres.key(before))
    # The real probe reads the wall clock.
    import time
    real = mres.check_one({"id": "x", "kind": "not_before", "arg": "2000-01-01T00:00:00+00:00", "obligation": "O"})
    check("V-RES-NB-REAL-PROBE", real["status"] == mres.MET and abs(float(real["measured"]) - time.time()) < 60,
          str(real))
    # CLI: `requires --not-before` reaches set_requires (a mission must exist; a missing one is refused, not ignored).
    r = subprocess.run([sys.executable, str(HERE / "gsd_mission.py"), "requires", "--mission", "m-nb-absent",
                        "--obligation", "O-1", "--not-before", iso], capture_output=True, text=True, timeout=120)
    check("V-RES-NB-CLI-PARSED", "unrecognized arguments" not in (r.stderr or "") and r.returncode != 0,
          f"rc={r.returncode} {(r.stderr or r.stdout).strip()[-160:]}")
    print(f"RES_NB_PASS={len(PASS)}/{len(PASS) + len(FAIL)}  threshold={len(PASS) + len(FAIL)}/{len(PASS) + len(FAIL)}")
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
