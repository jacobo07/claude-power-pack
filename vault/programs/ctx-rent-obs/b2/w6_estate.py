"""W6 Projected Estate Rent, laptop plane. One measured week of transcripts, streamed line by line.

Per session: calls (unique assistant message.id with usage), call-1 floor (input + cache_read + cache_creation of
the first call), processed input (sum over calls), floor rent = calls x call-1 floor (the floor carried by every call).
Class: mission owner sessions -> 'worker:<kind>'; files under */subagents/ -> 'subagent'; the rest -> 'top-level'.
Usage: w6_estate.py <since_iso_utc> <until_iso_utc> <out.json>
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, r"C:\Users\User\.claude\skills\claude-power-pack\tools")
import gsd_mission as g  # noqa: E402

since, until, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
PROJECTS = Path.home() / ".claude" / "projects"

worker_kind = {}
for m in g.all_missions():
    o = m.get("owner")
    if isinstance(o, dict) and o.get("session_id"):
        worker_kind[o["session_id"]] = o.get("kind") or "full"


def measure(path):
    seen, calls, floor, processed, first_ts = set(), 0, None, 0, None
    with open(path, encoding="utf-8", errors="replace") as f:
        for ln in f:
            if '"usage"' not in ln:
                continue
            try:
                e = json.loads(ln)
            except ValueError:
                continue
            msg = e.get("message") or {}
            u = msg.get("usage")
            mid = msg.get("id")
            if e.get("type") != "assistant" or not u or not mid or mid in seen:
                continue
            t = e.get("timestamp") or ""
            seen.add(mid)
            inp = (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + \
                (u.get("cache_creation_input_tokens") or 0)
            if floor is None:                                  # the session's real call 1, even before the window
                floor, first_ts = inp, t
            if t < since or t >= until:
                continue
            calls += 1
            processed += inp
    return calls, floor or 0, processed, first_ts


t0 = time.time()
lo = time.mktime(time.strptime(since[:10], "%Y-%m-%d")) - 86400
agg, sessions = {}, 0
for p in PROJECTS.rglob("*.jsonl"):
    try:
        if p.stat().st_mtime < lo:
            continue
    except OSError:
        continue
    calls, floor, processed, first_ts = measure(p)
    if not calls:
        continue
    sessions += 1
    if "subagents" in p.parts:
        cls = "subagent"
    elif p.stem in worker_kind:
        cls = f"worker:{worker_kind[p.stem]}"
    else:
        cls = "top-level"
    a = agg.setdefault(cls, {"sessions": 0, "calls": 0, "processed": 0, "floor_rent": 0, "floor_sum": 0})
    a["sessions"] += 1
    a["calls"] += calls
    a["processed"] += processed
    a["floor_rent"] += calls * floor
    a["floor_sum"] += floor
for a in agg.values():
    a["mean_floor"] = round(a["floor_sum"] / a["sessions"])
    a["floor_share"] = round(a["floor_rent"] / a["processed"], 3) if a["processed"] else None
tot = {k: sum(a[k] for a in agg.values()) for k in ("sessions", "calls", "processed", "floor_rent")}
res = {"plane": "laptop", "since": since, "until": until, "classes": agg, "total": tot,
       "elapsed_s": round(time.time() - t0, 1),
       "method": "calls = unique assistant message.id with usage inside the window; floor = call-1 input incl. cache; "
                 "floor_rent = calls x floor"}
out.write_text(json.dumps(res, indent=1), encoding="utf-8")
print(json.dumps({"total": tot, "classes": {k: {x: v[x] for x in ("sessions", "calls", "mean_floor", "floor_rent",
                                                                     "processed", "floor_share")}
                                            for k, v in agg.items()}}, indent=1))
