"""First-call cache read by project directory (main sessions, 7 d), and for sessions whose cwd is
a git repo vs not. Tests the hypothesis that the startup git-status snapshot breaks
cross-session cache reuse in busy repos. Read-only, zero model quota."""
import json, os, sqlite3
from collections import defaultdict

p = os.path.expanduser("~/.claude/state/usage_index/index.sqlite")
c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
END = c.execute("select max(ts) from calls").fetchone()[0]
first = {}
for f, ts, cr, cw in c.execute("select file, ts, cr, cw from calls where is_sub=0 and ts>? order by ts", (END - 7 * 86400,)):
    first.setdefault(f, (ts, cr, cw))


def cwd_of(f):
    try:
        for line in open(f, encoding="utf-8"):
            if '"cwd"' in line:
                d = json.loads(line)
                if d.get("cwd"):
                    return d["cwd"]
    except (OSError, ValueError):
        pass
    return None


by = defaultdict(list); git = defaultdict(list)
for f, (ts, cr, cw) in first.items():
    cwd = cwd_of(f) or "?"
    by[cwd].append(cr)
    g = "git" if cwd != "?" and os.path.isdir(os.path.join(cwd, ".git")) or os.path.isfile(os.path.join(cwd, ".git")) else "no-git"
    git[g].append(cr)
med = lambda v: sorted(v)[len(v) // 2]
print("first-call cache_read by cwd (dirs with >= 8 sessions): n, median, share reading >= 20k")
for d, v in sorted(by.items(), key=lambda x: -len(x[1])):
    if len(v) >= 8:
        print(f"  {len(v):>4}  med={med(v):>7,}  >=20k={sum(x >= 20000 for x in v)/len(v):>5.0%}  {d[-70:]}")
for g, v in git.items():
    print(f"[{g}] n={len(v)} median={med(v):,} share>=20k={sum(x >= 20000 for x in v)/len(v):.0%}")
