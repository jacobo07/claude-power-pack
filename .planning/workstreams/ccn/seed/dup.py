"""Cross-session duplicate tool work, last N hours. Deterministic, read-only.
A duplicate = same normalized tool key in >=2 distinct main sessions within WINDOW_S of each other."""
import json, os, sys, time, glob, collections, re
H = float(sys.argv[1]) if len(sys.argv) > 1 else 48
WINDOW_S = 1800
root = os.path.expanduser("~/.claude/projects")
cut = time.time() - H * 3600
ev = []          # (key, sid, ts, result_bytes, tool)
sessions = set()
for f in glob.glob(os.path.join(root, "*", "*.jsonl")):
    if os.path.getmtime(f) < cut:
        continue
    sid = os.path.basename(f)[:-6]
    pend = {}
    try:
        fh = open(f, encoding="utf-8", errors="replace")
    except OSError:
        continue
    for line in fh:
        try:
            r = json.loads(line)
        except ValueError:
            continue
        ts = r.get("timestamp")
        if not ts:
            continue
        try:
            t = time.mktime(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S"))
        except ValueError:
            continue
        if t < cut:
            continue
        c = (r.get("message") or {}).get("content")
        if not isinstance(c, list):
            continue
        for b in c:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                n, i = b.get("name"), b.get("input") or {}
                if n == "Read":
                    k = "Read:" + str(i.get("file_path", "")).lower().replace("\\", "/") + f":{i.get('offset')}:{i.get('limit')}"
                elif n == "Grep":
                    k = "Grep:" + str(i.get("pattern")) + "|" + str(i.get("path", "")).lower()
                elif n == "Glob":
                    k = "Glob:" + str(i.get("pattern")) + "|" + str(i.get("path", "")).lower()
                elif n in ("PowerShell", "Bash"):
                    cmd = " ".join(str(i.get("command", "")).split())
                    if not re.search(r"test_|pytest|git (log|status|diff)|status|census|gsd_mission", cmd):
                        continue
                    k = n + ":" + cmd[:300]
                elif n in ("Agent", "Task"):
                    k = "Agent:" + str(i.get("subagent_type")) + "|" + str(i.get("description"))
                else:
                    continue
                pend[b.get("id")] = (k, t, n)
            elif b.get("type") == "tool_result" and b.get("tool_use_id") in pend:
                k, t0, n = pend.pop(b["tool_use_id"])
                rc = b.get("content")
                size = len(json.dumps(rc)) if rc is not None else 0
                ev.append((k, sid, t0, size, n))
                sessions.add(sid)
by = collections.defaultdict(list)
for e in ev:
    by[e[0]].append(e)
dup_calls = dup_bytes = 0
per_tool = collections.Counter(); per_tool_b = collections.Counter(); top = []
for k, L in by.items():
    L.sort(key=lambda e: e[2])
    first_seen = {}
    for e in L:
        # duplicate if another session ran the same key within WINDOW_S before
        prior = [p for p in L if p[1] != e[1] and 0 <= e[2] - p[2] <= WINDOW_S]
        if prior:
            dup_calls += 1; dup_bytes += e[3]; per_tool[e[4]] += 1; per_tool_b[e[4]] += e[3]
    s = {e[1] for e in L}
    if len(s) >= 2:
        top.append((sum(e[3] for e in L), len(L), len(s), k[:110]))
tot_b = sum(e[3] for e in ev)
print(f"window_h={H} sessions_with_tools={len(sessions)} tool_events={len(ev)} result_bytes={tot_b}")
print(f"cross-session duplicates (<= {WINDOW_S}s): calls={dup_calls} ({dup_calls/max(1,len(ev)):.1%}) bytes={dup_bytes} ({dup_bytes/max(1,tot_b):.1%})")
for n in per_tool:
    print(f"  {n}: {per_tool[n]} calls, {per_tool_b[n]} bytes")
top.sort(reverse=True)
for x in top[:12]:
    print("  top", x)
