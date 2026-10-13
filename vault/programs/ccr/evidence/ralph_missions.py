"""U1/U2 (ccr v3): Ralph mission epochs from the usage index. An epoch is a session whose transcript title is
`m-<mission id>-e<N>` (gsd_mission relays). Per epoch: calls, gross, weighted, window; per mission: totals.

Gross = inp + cw + cr + out; weighted = inp + 0.1 cr + 2 cw + 5 out (CE CLOSE table). Read-only on the index.
Usage: python ralph_missions.py [--like %KobiiCraft%] [--mission m-1d270cd85220]
"""
import argparse, json, re, sqlite3
from collections import defaultdict
from pathlib import Path

DB = Path.home() / ".claude" / "state" / "usage_index" / "index.sqlite"
G = "(c.inp + c.cw + c.cr + c.out)"
W = "(c.inp + 0.1*c.cr + 2*c.cw + 5*c.out)"
TITLE = re.compile(r"^(m-[0-9a-f]{12})-e(\d+)$")


def main() -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DB))
    ap.add_argument("--like", default="%KobiiCraft%")
    ap.add_argument("--mission", default=None)
    a = ap.parse_args()
    con = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    # Title lives on the session's main file; subagent rows share the session id, so join through the session.
    titles = {}
    for s, t in con.execute("SELECT c.session, f.title FROM calls c JOIN files f ON f.path=c.file "
                            "WHERE c.file LIKE ? AND f.title IS NOT NULL GROUP BY c.session, f.title", [a.like]):
        m = TITLE.match(t or "")
        if m:
            titles[s] = (m.group(1), int(m.group(2)))
    eps = defaultdict(list)
    for s, n, g, w, sub, t0, t1 in con.execute(
            f"SELECT c.session, count(*), sum({G}), sum({W}), sum(c.is_sub), datetime(min(c.ts),'unixepoch'), "
            f"datetime(max(c.ts),'unixepoch') FROM calls c WHERE c.file LIKE ? GROUP BY c.session", [a.like]):
        if s in titles and (a.mission is None or titles[s][0] == a.mission):
            mid, e = titles[s]
            eps[mid].append({"epoch": e, "session": s, "calls": n, "sub_calls": sub, "gross": g,
                             "weighted": round(w), "start": t0, "end": t1})
    out = {}
    for mid, rows in sorted(eps.items()):
        rows.sort(key=lambda r: r["epoch"])
        out[mid] = {"epochs": len(rows), "calls": sum(r["calls"] for r in rows),
                    "gross": sum(r["gross"] for r in rows), "weighted": sum(r["weighted"] for r in rows),
                    "start": min(r["start"] for r in rows), "end": max(r["end"] for r in rows), "rows": rows}
    return out


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
