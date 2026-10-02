"""How often listing attachments (skills, agents, deferred tools, instructions) are injected per
main transcript over 7 d, initial vs later, and the measured ctx jump at each injection.
Read-only, zero model quota. Jump = ctx(next call) - ctx(previous call) in the same segment."""
import json, os, sqlite3, statistics as st, sys
from collections import Counter, defaultdict

sys.path.insert(0, r"C:\Users\User\.claude\skills\claude-power-pack\tools")
p = os.path.expanduser("~/.claude/state/usage_index/index.sqlite")
c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
END = c.execute("select max(ts) from calls").fetchone()[0]
files = [r[0] for r in c.execute("select file from calls where is_sub=0 and ts>? group by file having count(*)>=2", (END - 7 * 86400,))]
TYPES = {"skill_listing", "agent_listing_delta", "deferred_tools_delta", "instructions", "mcp_instructions_delta"}
per_file = defaultdict(Counter); initial = Counter(); later = Counter(); chars = defaultdict(list)
jumps = defaultdict(list)          # later injections only: ctx jump when this is the only listing in the interval
for f in files:
    seen = set(); last_ctx = None; pend = []; ncalls = 0
    for line in open(f, encoding="utf-8"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        t = d.get("type")
        if t == "system" and d.get("subtype") == "compact_boundary":
            last_ctx = None; pend = []
        elif t == "attachment":
            a = d.get("attachment") or {}
            ty = a.get("type")
            if ty in TYPES:
                per_file[f][ty] += 1
                first = a.get("isInitial") or ncalls == 0
                (initial if first else later)[ty] += 1
                chars[ty].append(len(json.dumps(a, ensure_ascii=False)))
                if not first:
                    pend.append(ty)
        elif t == "assistant":
            m = d.get("message") or {}
            if m.get("id") in seen:
                continue
            seen.add(m.get("id")); ncalls += 1
            u = m.get("usage") or {}
            ctx = (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
            if last_ctx is not None and len(pend) == 1:
                jumps[pend[0]].append(ctx - last_ctx)
            last_ctx = ctx; pend = []
print(f"main transcripts={len(files)}")
for ty in sorted(TYPES):
    n = [per_file[f][ty] for f in files]
    js = jumps[ty]
    print(f"{ty:24} injections={sum(n):>5} initial={initial[ty]:>5} later={later[ty]:>5} "
          f"per-transcript max={max(n)} median chars={int(st.median(chars[ty])) if chars[ty] else 0:,} "
          f"| later-injection ctx jump n={len(js)} median={int(st.median(js)) if js else 'NA'} p90={sorted(js)[int(len(js)*.9)] if js else 'NA'}")
