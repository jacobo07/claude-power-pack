"""Read-only autopsy of a dgl goal against its binding records (W4).

Reports where the ledger, the session bindings and the succession journal disagree. It opens no writer: the
spend journal, the workspace journal, the succession journal and the binding files are only read, and a gate
asserts they are byte-identical after a run.

  bound_settled / bound_unsettled   sids bound to the goal that do / do not have a settled mark
  settled_unbound                   sids with a settled mark and no binding record
  holds_no_binding                  sids that still hold reserved budget and have no binding record
  bindings_no_hold                  bound sids that never reserved anything
  unknown_past_ttl                  UNKNOWN_RESERVED rows older than the TTL with no terminal / swept row
  unclaimed_leases                  leases a succession opened and never claimed (CLAIM_LOST residue)
  incomplete_successions            succession ids with step rows and no done row, with their last step

A goal with no programme envelope (a pre-W1 journal) is UNKNOWN: the report does not invent headroom.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from modules.provider_routing.ledger import GoalLedger  # noqa: E402
import goal_succession as gs  # noqa: E402

SPEND = "spend.journal.jsonl"


def _rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_bytes().split(b"\n"):
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    return out


def _bound_sids(root: Path, goal: str) -> set[str]:
    d = root.parent / "goal-binding"
    sids = set()
    if d.is_dir():
        for p in d.glob("*.json"):
            try:
                rec = json.loads(p.read_text(encoding="utf-8-sig"))
            except (OSError, ValueError):
                continue
            if isinstance(rec, dict) and rec.get("goal") == goal:
                sids.add(p.stem)
    return sids


def _fold(root: Path, goal: str) -> dict:
    led = GoalLedger(root / goal, goal)
    with led._lock:                                   # the same read lineage() does; nothing is appended
        return led._gfold(led._read())


def _successions(root: Path, goal: str, now: float, ttl: int) -> dict:
    rows = _rows(root / goal / gs.JOURNAL)
    steps: dict[str, dict] = {}
    done = {r["key"] for r in rows if r["op"] == "done"}
    for r in rows:
        if r["op"] == "step":
            sid_, _, step = r["key"].rpartition(":")
            steps.setdefault(sid_, {})[step] = r
    resolved = {r["key"] for r in rows if r["op"] in ("terminal", "swept")}
    unknown = [{"sid": r["key"], "since": r["at"], "age_s": round(now - r["at"], 3)}
               for r in rows if r["op"] == "unknown" and r["key"] not in resolved and now - r["at"] > ttl]
    unclaimed = [{"succession_id": s, "lease": st["opened"].get("lease")}
                 for s, st in steps.items() if "opened" in st and "claimed" not in st]
    order = ("settled", "closed", "opened", "claimed")
    incomplete = [{"succession_id": s, "last_step": max(st, key=lambda k: order.index(k) if k in order else -1)}
                  for s, st in steps.items() if s not in done]
    return {"unknown_past_ttl": sorted(unknown, key=lambda x: x["sid"]),
            "unclaimed_leases": sorted(unclaimed, key=lambda x: x["succession_id"]),
            "incomplete_successions": sorted(incomplete, key=lambda x: x["succession_id"])}


def autopsy(root, goal: str, *, now: float | None = None, ttl: int = gs.DEFAULT_UNKNOWN_TTL_S) -> dict:
    root, now = Path(root), time.time() if now is None else now
    if not (root / goal / SPEND).exists():
        return {"goal": goal, "state": "UNKNOWN", "reason": f"UNKNOWN: no spend journal for goal {goal!r}"}
    g = _fold(root, goal)
    if g["programme"] is None:
        return {"goal": goal, "state": "UNKNOWN",
                "reason": "UNKNOWN: no programme envelope declared; unknown headroom is not reported as free"}
    bound = _bound_sids(root, goal)
    marks = set(g["marks"])
    held = {r["sid"] for r in g["res"].values() if r["hold"] > 0}
    reserved = {r["sid"] for r in g["res"].values()}
    out = {"goal": goal, "state": "OK", "reason": "", "lease": g["leases"][-1]["id"],
           "bound_settled": sorted(bound & marks), "bound_unsettled": sorted(bound - marks),
           "settled_unbound": sorted(marks - bound), "holds_no_binding": sorted(held - bound),
           "bindings_no_hold": sorted(bound - reserved)}
    out.update(_successions(root, goal, now, ttl))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="goal_autopsy")
    ap.add_argument("--goal", required=True)
    ap.add_argument("--ttl", type=int, default=gs.DEFAULT_UNKNOWN_TTL_S)
    a = ap.parse_args(argv)
    out = autopsy(gs._goal_root(), a.goal, ttl=a.ttl)
    print(json.dumps(out, sort_keys=True))
    return 3 if out["state"] == "UNKNOWN" else 0


if __name__ == "__main__":
    sys.exit(main())
