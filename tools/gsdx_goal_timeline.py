#!/usr/bin/env python3
"""Sweep -> judge timeline instrument for GSD X goals (gsdx-pcc phase 1, R01).

Reads a goal's hash-chained event log and reports when each epoch dispatched, ran,
ended and returned its receipt, what each receipt cost and observed, and how long the
judge's gate replay took. A live goal store is only ever COPIED, never opened for write.

    python tools/gsdx_goal_timeline.py recorded --store DIR --repo ID --goal ID --out FILE.json

Exit codes: 0 timeline written; 2 refused (missing goal dir, broken chain) with no file.
A metric that cannot be computed is null in the JSON and prints UNKNOWN, never 0.

Analogs: the chain is read with GoalLog.read() (modules/gsd_x/goal/log.py:152-178),
the event types are imported from the goal package, the PASS/FAIL conventions of the
companion suite follow tools/test_gsd_x_goal_gate_provider.py.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal.contract import DECLARED  # noqa: E402
from modules.gsd_x.goal.epoch import DISPATCHING, ENDED, RECEIPT, RUNNING  # noqa: E402
from modules.gsd_x.goal.judge import JUDGED  # noqa: E402
from modules.gsd_x.goal.log import GoalLog, GoalLogError  # noqa: E402

_EPOCH_FIELD = {DISPATCHING: "dispatching_s", RUNNING: "running_s", ENDED: "ended_s", RECEIPT: "receipt_s"}


def _ts(ev) -> datetime:
    return datetime.fromisoformat(ev.ts)


def _rel(ev, t0) -> float:
    return round((_ts(ev) - t0).total_seconds(), 3)


def timeline(events) -> dict:
    """Pure: relative times, per-epoch phases, receipt cost/observed and judge replay.

    Emits only seq/type/relative times/epoch ids/cost seconds/verdicts/observed/gate
    seconds -- no handles, identities, briefs or intent text."""
    if not events:
        return {"events": [], "epochs": {}, "first_dispatch_s": None, "judged": [],
                "judge_replay_s": None, "declared_to_last_judged_s": None}
    first = next((e for e in events if e.type == DECLARED), events[0])
    t0 = _ts(first)
    rows, epochs, judged = [], {}, []
    first_dispatch = None
    for ev in events:
        t = _rel(ev, t0)
        eid = ev.data.get("epoch_id")
        rows.append({"seq": ev.seq, "type": ev.type, "t_s": t, **({"epoch_id": eid} if eid else {})})
        if ev.type in _EPOCH_FIELD and eid:
            ep = epochs.setdefault(eid, {"provider": None, "dispatching_s": None, "running_s": None,
                                         "ended_s": None, "receipt_s": None, "outcome": None,
                                         "cost_seconds": None, "observed": []})
            ep[_EPOCH_FIELD[ev.type]] = t
            if ev.type == DISPATCHING:
                ep["provider"] = ev.data.get("provider")
                if first_dispatch is None:
                    first_dispatch = t
            elif ev.type == ENDED:
                ep["outcome"] = ev.data.get("outcome")
            elif ev.type == RECEIPT:
                rec = ev.data.get("receipt") or {}
                secs = (rec.get("cost") or {}).get("seconds")
                ep["cost_seconds"] = secs if isinstance(secs, (int, float)) else None
                ep["observed"] = [v.get("observed") for v in rec.get("verdicts") or [] if isinstance(v, dict)]
        elif ev.type == JUDGED:
            gates = ev.data.get("gates") or []
            gsecs = [g.get("seconds") if isinstance(g, dict) else None for g in gates]
            numeric = bool(gsecs) and all(isinstance(s, (int, float)) and not isinstance(s, bool) for s in gsecs)
            judged.append({"seq": ev.seq, "t_s": t, "verdict": ev.data.get("verdict"),
                           "gate_count": len(gates), "gate_seconds": gsecs,
                           "replay_s": round(sum(gsecs), 1) if numeric else None})
    return {"events": rows, "epochs": epochs, "first_dispatch_s": first_dispatch, "judged": judged,
            "judge_replay_s": judged[-1]["replay_s"] if judged else None,
            "declared_to_last_judged_s": judged[-1]["t_s"] if judged else None}


def _fmt(v) -> str:
    return "UNKNOWN" if v is None else str(v)


def print_timeline(tl: dict) -> None:
    for r in tl["events"]:
        print(f"  {r['t_s']:>10.3f}s  #{r['seq']:<4} {r['type']:<20} {r.get('epoch_id', '')}")
    print(f"first dispatch        : {_fmt(tl['first_dispatch_s'])} s")
    for eid, ep in tl["epochs"].items():
        print(f"epoch {eid}: ended {_fmt(ep['ended_s'])} s outcome {_fmt(ep['outcome'])} "
              f"cost {_fmt(ep['cost_seconds'])} s observed {ep['observed']}")
    last = tl["judged"][-1] if tl["judged"] else {}
    print(f"judged gate count     : {_fmt(last.get('gate_count'))}")
    print(f"judged verdict        : {_fmt(last.get('verdict'))}")
    print(f"judge replay          : {_fmt(tl['judge_replay_s'])} s")
    print(f"declared -> judged    : {_fmt(tl['declared_to_last_judged_s'])} s")


def cmd_recorded(a) -> int:
    src = Path(a.store) / a.repo / a.goal
    if not src.is_dir():
        print(f"REFUSED: no goal directory {src} (absence is not an empty timeline)")
        return 2
    base = Path(tempfile.mkdtemp(prefix="gsdx_tl_copy_"))
    shutil.copytree(src, base / a.repo / a.goal)
    try:
        events = GoalLog(a.repo, a.goal, base=base).read()
    except GoalLogError as exc:
        print(f"REFUSED: {exc}")
        return 2
    tl = timeline(events)
    doc = {"source": "recorded", "store": str(a.store), "repo": a.repo, "goal": a.goal,
           "copied_to": str(base / a.repo / a.goal),
           "read_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "timeline": tl}
    Path(a.out).write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    print_timeline(tl)
    print(f"written: {a.out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("recorded")
    r.add_argument("--store", required=True)
    r.add_argument("--repo", required=True)
    r.add_argument("--goal", required=True)
    r.add_argument("--out", required=True)
    return p


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    return {"recorded": cmd_recorded}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
