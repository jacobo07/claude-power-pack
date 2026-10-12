"""U1/U2 (ccr v3): a Ralph mission's burn per epoch. Epoch -> worker session comes from the autorun ledger
(`worker_adopted` / `worker_acked` events carry `worker`); spend comes from the usage index by session id, so totals
are the indexer's (deduplicated by message id + request id; subagent rows share the parent session).

Gross = inp + cw + cr + out; weighted = inp + 0.1 cr + 2 cw + 5 out (CE CLOSE table). Read-only.
Usage: python mission_burn.py <mission id> [--ledger PATH] [--db PATH]
"""
import argparse, json, sqlite3
from pathlib import Path

ST = Path.home() / ".claude" / "state"
G = "(inp + cw + cr + out)"
W = "(inp + 0.1*cr + 2*cw + 5*out)"


def main() -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("mission")
    ap.add_argument("--ledger", default=str(ST / "gsd-autorun-ledger.jsonl"))
    ap.add_argument("--db", default=str(ST / "usage_index" / "index.sqlite"))
    a = ap.parse_args()
    workers, events = {}, []
    for line in open(a.ledger, encoding="utf-8"):
        if a.mission not in line:
            continue
        o = json.loads(line)
        if o.get("mission_id") != a.mission:
            continue
        events.append({k: o.get(k) for k in ("ts", "event", "epoch", "state", "reason")})
        if o.get("worker") and o.get("epoch") is not None:
            workers.setdefault(o["worker"], o["epoch"])
    con = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    rows = []
    for sid, ep in sorted(workers.items(), key=lambda kv: kv[1]):
        n, g, w, sub, t0, t1 = con.execute(
            f"SELECT count(*), sum({G}), sum({W}), sum(is_sub), datetime(min(ts),'unixepoch'), "
            f"datetime(max(ts),'unixepoch') FROM calls WHERE session=?", [sid]).fetchone()
        rows.append({"epoch": ep, "session": sid, "calls": n, "sub_calls": sub or 0, "gross": g or 0,
                     "weighted": round(w or 0), "start": t0, "end": t1})
    return {"mission": a.mission, "epochs_with_worker": len(rows),
            "launched": sum(e["event"] == "launched" for e in events),
            "calls": sum(r["calls"] for r in rows), "gross": sum(r["gross"] for r in rows),
            "weighted": sum(r["weighted"] for r in rows),
            "last_events": events[-4:], "rows": rows}


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
