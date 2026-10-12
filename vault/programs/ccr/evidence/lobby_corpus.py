"""U1 (ccr v3): Lobby corpus from the usage index, read-only. Per-day calls, gross and weighted tokens for the
KobiiCraft-Core-Files project (main + subagent rows), plus the busiest sessions.

Gross = inp + cw + cr + out (the ledger's processed tokens). Weighted = inp + 0.1 cr + 2 cw + 5 out (CE CLOSE
table, plan v3 "Facts"). Rows come from tools/usage_index.py (deduplicated by message id + request id).
Usage: python lobby_corpus.py [--db PATH] [--like PATTERN] [--day YYYY-MM-DD]
"""
import argparse, json, sqlite3
from pathlib import Path

DB = Path.home() / ".claude" / "state" / "usage_index" / "index.sqlite"
W = "(inp + 0.1*cr + 2*cw + 5*out)"
G = "(inp + cw + cr + out)"


def main() -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DB))
    ap.add_argument("--like", default="%KobiiCraft-Core-Files%")
    ap.add_argument("--day", default=None)
    a = ap.parse_args()
    con = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    meta = dict(con.execute("SELECT k, v FROM meta WHERE k IN ('last_refresh','schema_version')").fetchall())
    last_ts = con.execute("SELECT max(ts) FROM calls").fetchone()[0]
    where = "file LIKE ?"
    args = [a.like]
    tot = con.execute(f"SELECT count(*), sum({G}), sum({W}), sum(out), sum(cr), sum(cw), sum(is_sub), "
                      f"count(DISTINCT session) FROM calls WHERE {where}", args).fetchone()
    days = con.execute(f"SELECT date(ts,'unixepoch') d, count(*), sum({G}), sum({W}), count(DISTINCT session) "
                       f"FROM calls WHERE {where} GROUP BY d ORDER BY d", args).fetchall()
    out = {"db": a.db, "meta": meta, "index_last_call": last_ts, "like": a.like,
           "total": {"calls": tot[0], "gross": tot[1], "weighted": round(tot[2] or 0), "out": tot[3], "cr": tot[4],
                     "cw": tot[5], "sub_calls": tot[6], "sessions": tot[7]},
           "per_day": [{"day": d, "calls": c, "gross": g, "weighted": round(w), "sessions": s}
                       for d, c, g, w, s in days]}
    if a.day:
        out["day_sessions"] = [
            {"session": s, "calls": c, "gross": g, "weighted": round(w), "first": f, "last": l, "files": n}
            for s, c, g, w, f, l, n in con.execute(
                f"SELECT session, count(*), sum({G}), sum({W}), datetime(min(ts),'unixepoch'), "
                f"datetime(max(ts),'unixepoch'), count(DISTINCT file) FROM calls WHERE {where} "
                f"AND date(ts,'unixepoch')=? GROUP BY session ORDER BY 3 DESC LIMIT 15", args + [a.day])]
    return out


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
