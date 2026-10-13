"""U1 (ccr v3): tag KobiiCraft sessions by what their tool calls touched, then price them from the usage index.

"Lobby" in plan v3 means LuckyArena's lobby (Owner, 2026-10-12), not SkyParty's. A transcript cannot say which lobby
it worked on except through what it touched, so each session is tagged by counting tool_use inputs (paths and
commands) that mention luckyarena, lobby and skyparty. A session is LUCKYARENA_LOBBY when its inputs name both
luckyarena and lobby, and luckyarena outweighs skyparty. Sessions are joined to usage_index call rows by session id
(subagent rows carry the parent session id), so totals are the indexer's, not re-parsed here.
Usage: python lobby_sessions.py <out.json> [--dirs-like KobiiCraft]
"""
import json, re, sqlite3, sys
from collections import defaultdict
from pathlib import Path

PROJ = Path.home() / ".claude" / "projects"
DB = Path.home() / ".claude" / "state" / "usage_index" / "index.sqlite"
PAT = {k: re.compile(p, re.I) for k, p in
       {"lucky": r"lucky[-_ ]?arena", "lobby": r"lobby", "sky": r"sky[-_ ]?party"}.items()}
W = "(inp + 0.1*cr + 2*cw + 5*out)"
G = "(inp + cw + cr + out)"


def scan(dirs_like: str) -> dict:
    tags = defaultdict(lambda: {"lucky": 0, "lobby": 0, "sky": 0, "both": 0, "uses": 0, "files": 0})
    for d in PROJ.iterdir():
        if not d.is_dir() or dirs_like.lower() not in d.name.lower():
            continue
        for f in d.rglob("*.jsonl"):
            sid = None
            t = None
            for line in open(f, encoding="utf-8", errors="replace"):
                if '"tool_use"' not in line:
                    if sid is None and '"sessionId"' in line:
                        try:
                            sid = json.loads(line).get("sessionId")
                        except ValueError:
                            pass
                    continue
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                sid = sid or o.get("sessionId")
                t = tags[sid]
                for b in (o.get("message") or {}).get("content") or []:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        s = json.dumps(b.get("input") or {})
                        t["uses"] += 1
                        hit = {k: bool(p.search(s)) for k, p in PAT.items()}
                        for k, v in hit.items():
                            t[k] += v
                        t["both"] += hit["lucky"] and hit["lobby"]
            if sid is not None:
                tags[sid]["files"] += 1
    return tags


def cls(t: dict) -> str:
    if t["lucky"] and t["lobby"] and t["lucky"] > t["sky"]:
        return "LUCKYARENA_LOBBY"
    if t["sky"] and t["lobby"] and t["sky"] >= t["lucky"]:
        return "SKYPARTY_LOBBY"
    if t["lobby"]:
        return "LOBBY_OTHER"
    if t["lucky"]:
        return "LUCKYARENA_NO_LOBBY"
    return "OTHER"


def main(out: str, dirs_like: str) -> dict:
    tags = scan(dirs_like)
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    rows = {s: (c, g, w, d0, d1) for s, c, g, w, d0, d1 in con.execute(
        f"SELECT session, count(*), sum({G}), sum({W}), date(min(ts),'unixepoch'), date(max(ts),'unixepoch') "
        f"FROM calls WHERE file LIKE ? GROUP BY session", [f"%{dirs_like}%"])}
    sessions, agg = [], defaultdict(lambda: {"sessions": 0, "calls": 0, "gross": 0, "weighted": 0})
    for sid, t in tags.items():
        c, g, w, d0, d1 = rows.get(sid, (0, 0, 0, None, None))
        k = cls(t)
        sessions.append({"session": sid, "class": k, "calls": c, "gross": g or 0, "weighted": round(w or 0),
                         "first": d0, "last": d1, **t})
        a = agg[k]
        a["sessions"] += 1
        a["calls"] += c
        a["gross"] += g or 0
        a["weighted"] += round(w or 0)
    unjoined = sorted(set(rows) - set(tags))
    res = {"dirs_like": dirs_like, "classes": agg,
           "index_sessions_without_transcript_tag": len(unjoined),
           "index_calls_without_transcript_tag": sum(rows[s][0] for s in unjoined),
           "sessions": sorted(sessions, key=lambda r: -r["gross"])}
    Path(out).write_text(json.dumps(res, indent=1), encoding="utf-8")
    return {k: v for k, v in res.items() if k != "sessions"}


if __name__ == "__main__":
    like = sys.argv[sys.argv.index("--dirs-like") + 1] if "--dirs-like" in sys.argv else "KobiiCraft"
    print(json.dumps(main(sys.argv[1], like), indent=1))
