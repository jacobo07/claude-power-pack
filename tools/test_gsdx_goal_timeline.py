#!/usr/bin/env python3
"""V-TL-* gates for tools/gsdx_goal_timeline.py -- every detector driven from both poles.

    python tools/test_gsdx_goal_timeline.py

Hermetic: HOME/USERPROFILE point at a temp dir for this process and every child; every
goal store is a temp dir built here with the real event_digest/GENESIS chain rules.
Summary line: GSDX_GOAL_TIMELINE_PASS=n/m  threshold=n/m.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "gsdx_goal_timeline.py"
TMP = Path(tempfile.mkdtemp(prefix="gsdx_tl_test_"))
HOME = TMP / "home"
HOME.mkdir()
os.environ.update(HOME=str(HOME), USERPROFILE=str(HOME), PYTHONIOENCODING="utf-8")
sys.path.insert(0, str(ROOT))
from modules.gsd_x.goal.log import GENESIS, event_digest  # noqa: E402

REPO = "ab" * 20
GOAL = "g-tl"
T0 = datetime(2026, 10, 7, 12, 0, 0, tzinfo=timezone.utc)

passes = 0
fails = 0


def check(gate: str, ok: bool, detail) -> None:
    global passes, fails
    if ok:
        passes += 1
        print(f"  PASS {gate}: {detail}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {detail}")


def tool(*args):
    r = subprocess.run([sys.executable, str(TOOL), *map(str, args)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=dict(os.environ), timeout=600)
    return r.returncode, r.stdout + r.stderr


def chain(specs: list[tuple[float, str, dict]]) -> list[dict]:
    out, prev = [], GENESIS
    for seq, (dt, type_, data) in enumerate(specs, start=1):
        ev = {"seq": seq, "type": type_, "ts": (T0 + timedelta(seconds=dt)).isoformat(),
              "actor": "test", "data": data, "prev_digest": prev}
        ev["digest"] = event_digest(ev)
        prev = ev["digest"]
        out.append(ev)
    return out


def store(name: str, events: list[dict]) -> Path:
    s = TMP / name
    d = s / REPO / GOAL
    d.mkdir(parents=True)
    for ev in events:
        (d / f"{ev['seq']:06d}.json").write_text(json.dumps(ev, indent=2), encoding="utf-8")
    return s


def specs(judged: bool = True, gate_seconds=(0.5, 0.3)) -> list:
    s = [(0.0, "goal.declared", {"goal_id": GOAL}),
         (1.5, "epoch.dispatching", {"epoch_id": "ep-1", "provider": "gate"}),
         (1.6, "epoch.running", {"epoch_id": "ep-1", "handle": {}}),
         (3.0, "epoch.ended", {"epoch_id": "ep-1", "outcome": "succeeded", "detail": ""}),
         (3.1, "epoch.receipt", {"epoch_id": "ep-1", "receipt_id": "r1",
                                 "receipt": {"epoch_id": "ep-1", "cost": {"seconds": 1.4},
                                             "verdicts": [{"observed": "2 passed"}]}})]
    if judged:
        gates = [({"verdict": "PASS"} | ({} if g is None else {"seconds": g})) for g in gate_seconds]
        s.append((5.0, "goal.judged", {"verdict": "PASS", "gates": gates}))
    return s


def recorded(st: Path, out: Path, goal: str = GOAL):
    return tool("recorded", "--store", st, "--repo", REPO, "--goal", goal, "--out", out)


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def main() -> int:
    if not TOOL.is_file():
        print(f"  FAIL V-TL-TOOL-EXISTS: {TOOL} is missing")
        print("\nGSDX_GOAL_TIMELINE_PASS=0/8  threshold=8/8")
        return 1

    st = store("full", chain(specs()))
    out = TMP / "full.json"
    src_sha = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (st / REPO / GOAL).iterdir()}
    rc, txt = recorded(st, out)
    tl = load(out).get("timeline", {})
    ep = (tl.get("epochs") or {}).get("ep-1", {})
    jd = (tl.get("judged") or [{}])[-1]
    check("V-TL-DELTAS",
          rc == 0 and tl.get("first_dispatch_s") == 1.5 and ep.get("ended_s") == 3.0
          and ep.get("cost_seconds") == 1.4 and ep.get("observed") == ["2 passed"]
          and jd.get("t_s") == 5.0 and tl.get("judge_replay_s") == 0.8,
          f"rc={rc} first={tl.get('first_dispatch_s')} ep={ep} judged={jd} replay={tl.get('judge_replay_s')}")

    copied = load(out).get("copied_to", "")
    now_sha = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (st / REPO / GOAL).iterdir()}
    check("V-TL-READS-A-COPY",
          rc == 0 and now_sha == src_sha and copied and not Path(copied).resolve().is_relative_to(st.resolve()),
          f"source_unchanged={now_sha == src_sha} copied_to={copied}")

    st = store("nojudge", chain(specs(judged=False)))
    out = TMP / "nojudge.json"
    rc, txt = recorded(st, out)
    tl = load(out).get("timeline", {})
    check("V-TL-JUDGE-ABSENT-UNKNOWN",
          rc == 0 and "judge_replay_s" in tl and tl["judge_replay_s"] is None and "UNKNOWN" in txt,
          f"rc={rc} replay={tl.get('judge_replay_s', 'missing')} unknown_printed={'UNKNOWN' in txt}")

    st = store("partial", chain(specs(gate_seconds=(0.5, None))))
    out = TMP / "partial.json"
    rc, txt = recorded(st, out)
    tl = load(out).get("timeline", {})
    check("V-TL-JUDGE-PARTIAL-UNKNOWN",
          rc == 0 and "judge_replay_s" in tl and tl["judge_replay_s"] is None,
          f"rc={rc} replay={tl.get('judge_replay_s', 'missing')}")

    evs = chain(specs())
    evs[2]["data"]["handle"] = {"tampered": True}  # edited after its digest
    st = store("corrupt", evs)
    out = TMP / "corrupt.json"
    rc, txt = recorded(st, out)
    check("V-TL-CORRUPT-REFUSED",
          rc == 2 and txt.lstrip().startswith("REFUSED") and not out.exists(),
          f"rc={rc} out_exists={out.exists()} {txt.strip()[:120]}")

    st = store("missing", chain(specs()))
    out = TMP / "missing.json"
    rc, txt = recorded(st, out, goal="g-absent")
    check("V-TL-MISSING-REFUSED", rc == 2 and not out.exists(),
          f"rc={rc} out_exists={out.exists()} {txt.strip()[:120]}")

    total = passes + fails
    print(f"\nGSDX_GOAL_TIMELINE_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
