"""V-NIGHT-* gates for tools/night_research_runner.py + tools/night_research.cjs (T10 item 34).

Everything runs in a private state dir. The fixture worker and the clock override are refused
by the core unless CPP_NIGHT_RESEARCH_FIXTURE=1, and both refusals are driven here too.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
TMP = Path(tempfile.mkdtemp(prefix="night-"))
os.environ["CPP_NIGHT_RESEARCH_DIR"] = str(TMP)
import night_research_runner as nrr  # noqa: E402

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


def madrid(h: int, day: int = 29) -> int:
    return int(datetime(2026, 9, day, h, 30, tzinfo=ZoneInfo("Europe/Madrid")).timestamp() * 1000)


def main() -> int:
    os.environ.pop("CPP_NIGHT_RESEARCH_FIXTURE", None)
    if nrr.host_ok()[0]:
        # On the VPS the refusal branch is unreachable by design, and `run` there is a REAL pass
        # (red team R1). Say so; never launch a model from a test.
        print("INFO V-NIGHT-HOST-REFUSED not applicable: this IS the permitted host")
    else:
        # `status` never dispatches, so even a broken host check could not start a pass here.
        p = subprocess.run([sys.executable, str(ROOT / "tools" / "night_research_runner.py"), "status"],
                           capture_output=True, text=True, env={**os.environ})
        check("V-NIGHT-HOST-REFUSED", p.returncode == 3 and "REFUSED" in p.stdout and not any(TMP.iterdir()),
              f"{p.stdout.strip()[:110]} (state dir untouched)")

    node, why = nrr.find_node()
    check("V-NIGHT-ENGINE", node is not None, why or node)
    if node is None:
        print(f"NIGHT_PASS={passes}/{passes + fails}")
        return 1

    def core(req, env_fixture):
        env = {**os.environ, **({"CPP_NIGHT_RESEARCH_FIXTURE": "1"} if env_fixture else {})}
        env.pop("CPP_NIGHT_RESEARCH_FIXTURE", None) if not env_fixture else None
        r = subprocess.run([node, str(nrr.CORE)], input=json.dumps(req), capture_output=True, text=True, env=env)
        return json.loads(r.stdout)

    base = {"mode": "run", "stateDir": str(TMP), "timezone": nrr.TIMEZONE, "maxPassesPerNight": nrr.PASSES_PER_NIGHT,
            "timeoutMs": 20000, "theme": nrr.theme()}
    r = core({**base, "fixture": True, "now": madrid(23)}, env_fixture=False)
    check("V-NIGHT-FIXTURE-GUARD", r.get("outcome") == "REFUSED", "the fixture worker needs the test flag")
    r = core({**base, "fixture": False, "now": madrid(23)}, env_fixture=True)
    check("V-NIGHT-CLOCK-GUARD", r.get("outcome") == "REFUSED", "a clock override is fixture-only")

    os.environ["CPP_NIGHT_RESEARCH_FIXTURE"] = "1"
    try:
        day = nrr.call("run", fixture=True, now=madrid(14))
        check("V-NIGHT-DAY-IDLE", day.get("outcome") == "OK" and day["result"].get("dispatched") is False
              and "outside-night-window" in (day["result"].get("reasons") or []),
              f"14:30 Madrid dispatches nothing: {day.get('result', {}).get('reasons')}")

        night = nrr.call("run", fixture=True, now=madrid(23))
        res = night.get("result") or {}
        rep = json.loads(Path(res["report"]).read_text(encoding="utf-8")) if res.get("report") else {}
        check("V-NIGHT-PASS", night.get("outcome") == "OK" and res.get("dispatched") is True and res.get("ok") is True,
              f"23:30 Madrid runs one pass: {res.get('status')}")
        check("V-NIGHT-UNPROMOTED", rep.get("promotion") == "none" and rep.get("reward") == 0
              and rep.get("independentlyValidated") is False
              and all(s.get("validation") == "unverified" for s in rep.get("sources") or [{}]),
              "the report is a candidate: unverified sources, reward 0, no promotion")

        (TMP / "paused.flag").write_text("", encoding="utf-8")
        paused = nrr.call("run", fixture=True, now=madrid(23))
        check("V-NIGHT-PAUSED", paused["result"].get("dispatched") is False and "paused" in paused["result"].get("reasons", []),
              str(paused["result"].get("reasons")))
        (TMP / "paused.flag").unlink()

        # 01:30 and 02:30 on the 30th belong to the SAME night as 23:30 on the 29th.
        second = nrr.call("run", fixture=True, now=madrid(1, day=30))
        check("V-NIGHT-SECOND", second["result"].get("dispatched") is True, "the second pass of the night runs")
        third = nrr.call("run", fixture=True, now=madrid(2, day=30))
        check("V-NIGHT-BUDGET", third["result"].get("dispatched") is False
              and "night-pass-budget-exhausted" in third["result"].get("reasons", []),
              f"pass budget {nrr.PASSES_PER_NIGHT}/night holds: {third['result'].get('reasons')}")
        st = nrr.call("status", fixture=True, now=madrid(23))
        check("V-NIGHT-STATUS-READONLY", st.get("outcome") == "OK" and "status" in st, "status answers without dispatching")
    finally:
        os.environ.pop("CPP_NIGHT_RESEARCH_FIXTURE", None)
    print(f"NIGHT_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
