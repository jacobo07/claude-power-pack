#!/usr/bin/env python
"""context_lifetime.py -- pillars D and E of the cognitive-economy campaign. Zero model calls.

Question: what did crossing a context boundary (interactive /kclear -> /clear -> /kresume, and
mission CONTEXT_ROTATION) actually save in the D-W7 window, after paying the successor's
rehydration, and is any threshold change worth >= 3 % of D-W7 weighted?

Population (discovered, never hand-listed):
  interactive : `successor_claimed` rows of ~/.claude/state/rollover/rollover-ledger.jsonl in
                D-W7 whose claimant is not a drill; pair = (session_id -> claimant). The route
                that asked (economic / self / terminal-inbox / ...) is joined from the
                `rollover_kclear_asked` rows of ~/.claude/state/gsd-autorun-ledger.jsonl.
  mission     : epochs from tools/gsd_epoch.py `epochs()` (imported, never edited) whose
                start_cause is CONTEXT_ROTATION and start falls in D-W7; pair = (previous
                epoch's session -> this epoch's session).

Per pair, from the two main-thread transcripts (distinct message.id, not sidechain, not
<synthetic>), weighting = the frozen D-W7 weighting (input 1, cache_read 0.1, cache_write 2,
output 5):
  ctx_before   : context (input + cache_read + cache_write) of the predecessor's LAST call
  ctx_after    : context of the successor's FIRST call
  rehydration  : weighted cost of the successor's calls from its first call up to and
                 including the call that issues its first Edit/Write/NotebookEdit (all calls
                 if it never edits) -- the displaced work
  carry_saved  : (ctx_before - ctx_after) x 0.1 x successor calls -- the cache-read rent the
                 successor did not pay, IF the predecessor would have carried its context for
                 that long. That counterfactual is unobservable, so this is an UPPER bound.
  net interval : [ -rehydration , carry_saved - rehydration ]

Controls: a positive control (a pair the ledger records must be found, with ctx_before >
ctx_after) and a negative control (a D-W7 session whose transcript never typed /clear or
/kclear and appears in no ledger row must yield no crossing).

    python vault/programs/cognitive-economy/measure/context_lifetime.py [--json OUT]
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "tools"))
STATE = Path.home() / ".claude" / "state"
ROLLOVER_LEDGER = STATE / "rollover" / "rollover-ledger.jsonl"
AUTORUN_LEDGER = STATE / "gsd-autorun-ledger.jsonl"
PROJECTS = Path.home() / ".claude" / "projects"
W_START = datetime(2026, 9, 26, tzinfo=timezone.utc).timestamp()
W_END = datetime(2026, 10, 3, tzinfo=timezone.utc).timestamp()
DW7_WEIGHTED = 3325101725
EDIT_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
KSR_DEAD_UPPER_PCT = 6.34


def ts_of(v) -> float | None:
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).timestamp()
    except (TypeError, ValueError):
        return None


def jsonl(path: Path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            try:
                yield json.loads(ln)
            except json.JSONDecodeError:
                continue


def is_drill(claimant) -> bool:
    s = str(claimant or "")
    return "drill" in s or s.startswith("test")


def transcript_index() -> dict:
    out = {}
    for fp in glob.glob(str(PROJECTS / "*" / "*.jsonl")):
        out.setdefault(Path(fp).stem, fp)
    return out


def calls_of(path: str) -> list[dict]:
    """Main-thread model calls INSIDE D-W7: [{ctx, w, edit}] in order. Calls outside the window
    are dropped so the numerator is drawn from the same calls as the frozen denominator, and a
    session still running after the window cannot move the result."""
    seen, calls = set(), []
    for d in jsonl(Path(path)):
        if d.get("isSidechain") or d.get("type") != "assistant":
            continue
        t = ts_of(d.get("timestamp"))
        if t is None or not (W_START <= t < W_END):
            continue
        m = d.get("message") or {}
        u, mid = m.get("usage"), m.get("id")
        edit = any(isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") in EDIT_TOOLS
                   for b in m.get("content") or [])
        if u and mid and mid not in seen and m.get("model") != "<synthetic>":
            seen.add(mid)
            inp = u.get("input_tokens", 0) or 0
            cr = u.get("cache_read_input_tokens", 0) or 0
            cw = u.get("cache_creation_input_tokens", 0) or 0
            out = u.get("output_tokens", 0) or 0
            calls.append({"ctx": inp + cr + cw, "w": inp + cr * 0.1 + cw * 2 + out * 5, "edit": edit})
        elif edit and calls and mid in seen:
            calls[-1]["edit"] = True      # a later content block of the same message
    return calls


def typed_clear(path: str) -> bool:
    for d in jsonl(Path(path)):
        if d.get("type") != "user":
            continue
        c = (d.get("message") or {}).get("content")
        txt = c if isinstance(c, str) else " ".join(
            b.get("text", "") for b in c or [] if isinstance(b, dict) and b.get("type") == "text")
        if "/clear" in txt or "/kclear" in txt or "<command-name>/clear" in txt:
            return True
    return False


def interactive_pairs() -> list[dict]:
    asks = {}
    for d in jsonl(AUTORUN_LEDGER):
        if d.get("event") == "rollover_kclear_asked":
            t = ts_of(d.get("ts"))
            if t is not None and W_START <= t < W_END:
                asks[d.get("session_id")] = d.get("route")
    pairs, seen = [], set()
    for d in jsonl(ROLLOVER_LEDGER):
        if d.get("event") != "successor_claimed" or is_drill(d.get("claimant")):
            continue
        t = ts_of(d.get("ts"))
        if t is None or not (W_START <= t < W_END):
            continue
        key = (d["session_id"], d["claimant"])
        if key in seen:
            continue                      # a re-claim of the same pair is one crossing
        seen.add(key)
        pairs.append({"kind": "interactive", "pred": d["session_id"], "succ": d["claimant"], "ts": d["ts"],
                      "route": asks.get(d["session_id"], "unrecorded")})
    return pairs


def mission_pairs() -> list[dict]:
    import gsd_epoch as ge
    import gsd_long_run as lr
    import gsd_mission as gm
    events = lr.ledger_events()
    ids = {m["mission_id"] for m in gm.all_missions()} | {
        e["mission_id"] for e in events if e.get("event") == "launch_claimed" and e.get("mission_id")}
    pairs = []
    for mid in sorted(ids):
        eps = ge.epochs(mid, events)
        for i, ep in enumerate(eps):
            t = ts_of(ep.get("start"))
            if ep.get("start_cause") != ge.CONTEXT_ROTATION or t is None or not (W_START <= t < W_END):
                continue
            prev = eps[i - 1] if i else {}
            pairs.append({"kind": "mission", "mission": mid, "pred": prev.get("session"), "succ": ep.get("session"),
                          "ts": ep.get("start"), "route": "rotation"})
    return pairs


def mission_rent_above_floor(tix: dict, rehydrations: list[float]) -> dict:
    """Ceilings for ANY rotation-threshold change (pillar E).

    gross : the cache-read rent every mission worker session started in D-W7 paid above its own
            first-call context. Rotating earlier can remove at most this rent.
    net   : sum over sessions of max(rent_i - R, 0), R = the CHEAPEST rehydration measured on a
            real mission rotation in the window (R_min makes this an upper bound: every extra
            rotation pays at least one rehydration, and real ones cost more).
    raise : rotating LATER can save at most the rehydration the window's rotations paid.
    A threshold change worth >= 3 % of D-W7 needs net or raise >= 3 %."""
    import gsd_epoch as ge
    import gsd_long_run as lr
    import gsd_mission as gm
    events = lr.ledger_events()
    ids = {m["mission_id"] for m in gm.all_missions()} | {
        e["mission_id"] for e in events if e.get("event") == "launch_claimed" and e.get("mission_id")}
    sessions, missing, epochs, unresolved = set(), set(), 0, 0
    for mid in sorted(ids):
        for ep in ge.epochs(mid, events):
            t = ts_of(ep.get("start"))
            if t is None or not (W_START <= t < W_END):
                continue
            epochs += 1
            if tix.get(str(ep.get("session"))):
                sessions.add(str(ep.get("session")))
            else:
                unresolved += 1
                if ep.get("session"):
                    missing.add(str(ep["session"]))
    # An epoch without a transcript is bounded by the usage index (read-only): if it made no
    # indexed call in D-W7 it is outside the denominator as well as the numerator.
    import sqlite3
    db = STATE / "usage_index" / "index.sqlite"
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    miss_calls = miss_w = 0
    for sid in sorted(missing):
        n, w = con.execute("SELECT COUNT(*), COALESCE(SUM(inp + cr*0.1 + cw*2 + out*5), 0) FROM calls "
                           "WHERE session=? AND ts>=? AND ts<?", (sid, W_START, W_END)).fetchone()
        miss_calls, miss_w = miss_calls + n, miss_w + w
    con.close()
    rents = []
    for sid in sorted(sessions):
        cs = calls_of(tix[sid])
        if cs:
            floor = cs[0]["ctx"]
            rents.append(sum(max(c["ctx"] - floor, 0) * 0.1 for c in cs))
    r_min = min(rehydrations) if rehydrations else 0.0
    gross = sum(rents)
    net = sum(max(r - r_min, 0) for r in rents)
    pct = lambda x: round(100 * x / DW7_WEIGHTED, 4)
    return {"epochs_started_in_window": epochs, "unresolved_epochs": unresolved, "sessions": len(rents),
            "rent_above_floor_gross_w": round(gross), "gross_pct_DW7": pct(gross),
            "cheapest_rotation_rehydration_w": round(r_min),
            "sessions_with_rent_above_r_min": sum(1 for r in rents if r > r_min),
            "earlier_rotation_net_ceiling_w": round(net), "earlier_rotation_net_ceiling_pct_DW7": pct(net),
            "later_rotation_ceiling_pct_DW7": pct(sum(rehydrations)),
            "untranscribed_sessions": len(missing), "untranscribed_indexed_calls": miss_calls,
            "untranscribed_weighted_pct_DW7": pct(miss_w)}


def measure(pair: dict, tix: dict) -> dict:
    row = dict(pair)
    pp, sp = tix.get(str(pair.get("pred"))), tix.get(str(pair.get("succ")))
    if not pp or not sp:
        row["status"] = "UNRESOLVED_TRANSCRIPT"
        return row
    pc, sc = calls_of(pp), calls_of(sp)
    if not pc or not sc:
        row["status"] = "NO_CALLS"
        return row
    first_edit = next((i for i, c in enumerate(sc) if c["edit"]), len(sc) - 1)
    rehyd = sum(c["w"] for c in sc[: first_edit + 1])
    drop = pc[-1]["ctx"] - sc[0]["ctx"]
    row.update({"status": "MEASURED", "ctx_before": pc[-1]["ctx"], "ctx_after": sc[0]["ctx"],
                "succ_calls": len(sc), "calls_to_first_edit": first_edit + 1,
                "never_edited": not any(c["edit"] for c in sc),
                "rehydration_w": round(rehyd), "carry_saved_ub_w": round(max(drop, 0) * 0.1 * len(sc))})
    return row


def summarise(rows: list[dict]) -> dict:
    m = [r for r in rows if r.get("status") == "MEASURED"]
    rh = sum(r["rehydration_w"] for r in m)
    ub = sum(r["carry_saved_ub_w"] for r in m)
    pct = lambda x: round(100 * x / DW7_WEIGHTED, 4)
    return {"pairs": len(rows), "measured": len(m),
            "unresolved": sum(1 for r in rows if r.get("status") != "MEASURED"),
            "median_ctx_before": statistics.median(r["ctx_before"] for r in m) if m else None,
            "median_ctx_after": statistics.median(r["ctx_after"] for r in m) if m else None,
            "rehydration_w": round(rh), "rehydration_pct_DW7": pct(rh),
            "carry_saved_ub_w": round(ub), "carry_saved_ub_pct_DW7": pct(ub),
            "net_interval_pct_DW7": [pct(-rh), pct(ub - rh)]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--json", help="write the full result here")
    a = ap.parse_args(argv)
    tix = transcript_index()
    inter = interactive_pairs()
    miss = mission_pairs()
    rows = [measure(p, tix) for p in inter + miss]

    by = {}
    for label, sel in (("interactive_all", lambda r: r["kind"] == "interactive"),
                       ("interactive_economic", lambda r: r["kind"] == "interactive" and r["route"] == "economic"),
                       ("interactive_wall_or_other", lambda r: r["kind"] == "interactive" and r["route"] != "economic"),
                       ("mission_rotation", lambda r: r["kind"] == "mission")):
        by[label] = summarise([r for r in rows if sel(r)])

    # Controls ---------------------------------------------------------------------------
    involved = {str(r.get("pred")) for r in rows} | {str(r.get("succ")) for r in rows}
    pos = next((r for r in rows if r.get("status") == "MEASURED" and r["kind"] == "interactive"), None)
    neg_sid, neg_pairs = None, None
    for sid, fp in sorted(tix.items()):
        if sid in involved or os.path.getmtime(fp) < W_START or os.path.getsize(fp) < 200_000:
            continue
        if not typed_clear(fp):
            neg_sid = sid
            neg_pairs = [p for p in inter + miss if str(p.get("pred")) == sid or str(p.get("succ")) == sid]
            break
    controls = {
        "positive": {"pair": [pos["pred"], pos["succ"]] if pos else None,
                     "found_with_drop": bool(pos and pos["ctx_before"] > pos["ctx_after"])},
        "negative": {"session": neg_sid, "crossings_reported": None if neg_pairs is None else len(neg_pairs),
                     "ok": neg_pairs == []},
    }
    econ_ub = by["interactive_economic"]["carry_saved_ub_pct_DW7"]
    result = {"window": "D-W7 2026-09-26T00:00:00Z..2026-10-03T00:00:00Z", "weighted_denominator": DW7_WEIGHTED,
              "by_population": by, "controls": controls,
              "mission_threshold_ceiling": mission_rent_above_floor(
                  tix, [r["rehydration_w"] for r in rows if r["kind"] == "mission" and r.get("status") == "MEASURED"]),
              "ksr_comparison": {"ksr_dead_carriage_upper_pct": KSR_DEAD_UPPER_PCT,
                                 "economic_trigger_carry_saved_ub_pct": econ_ub,
                                 "all_crossings_carry_saved_ub_pct": round(
                                     by["interactive_all"]["carry_saved_ub_pct_DW7"]
                                     + by["mission_rotation"]["carry_saved_ub_pct_DW7"], 4)},
              "rows": rows}
    blob = json.dumps(result, indent=1, sort_keys=True)
    if a.json:
        Path(a.json).write_text(blob, encoding="utf-8", newline="\n")
    print("result_sha256", hashlib.sha256(blob.encode()).hexdigest())
    for k, v in by.items():
        print(k, json.dumps(v))
    print("controls", json.dumps(controls))
    print("ksr_comparison", json.dumps(result["ksr_comparison"]))
    return 0 if controls["positive"]["found_with_drop"] and controls["negative"]["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
