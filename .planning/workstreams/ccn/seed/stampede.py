"""First-call cache economics per main session (7 d): does a cold start that another session launched
just before it (<=5 min) write less (shared prefix) or the same (stampede)? Deterministic, read-only."""
import json, os, glob, time, statistics as st
root = os.path.expanduser("~/.claude/projects")
cut = time.time() - 7 * 86400
rows = []
for f in glob.glob(os.path.join(root, "*", "*.jsonl")):
    if os.path.getmtime(f) < cut:
        continue
    try:
        fh = open(f, encoding="utf-8", errors="replace")
    except OSError:
        continue
    for line in fh:
        try:
            r = json.loads(line)
        except ValueError:
            continue
        m = r.get("message") or {}
        u = m.get("usage")
        if r.get("type") != "assistant" or not u or not r.get("timestamp"):
            continue
        t = time.mktime(time.strptime(r["timestamp"][:19], "%Y-%m-%dT%H:%M:%S"))
        if t >= cut:
            rows.append((t, u.get("cache_creation_input_tokens", 0) or 0, u.get("cache_read_input_tokens", 0) or 0, m.get("model", "")))
        break
rows.sort()
conc, iso = [], []
for i, (t, w, rd, mdl) in enumerate(rows):
    near = any(0 < t - rows[j][0] <= 300 for j in range(max(0, i - 30), i))
    (conc if near else iso).append((w, rd))
def s(L, k):
    v = [x[k] for x in L]
    return f"n={len(v)} median={st.median(v) if v else 0:.0f} mean={st.mean(v) if v else 0:.0f}"
print("first call, launched <=5 min after another session:")
print("  cache_write", s(conc, 0), "| cache_read", s(conc, 1))
print("first call, isolated start:")
print("  cache_write", s(iso, 0), "| cache_read", s(iso, 1))
tot_w = sum(x[0] for x in conc + iso); tot_r = sum(x[1] for x in conc + iso)
print(f"all first calls: write={tot_w} read={tot_r} read_share={tot_r/max(1,tot_w+tot_r):.1%}")
