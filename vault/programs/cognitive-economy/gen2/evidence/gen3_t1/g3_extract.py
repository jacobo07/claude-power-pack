"""Gen3 T1 extractor (zero-model). Reads main-session transcripts (not subagents) and writes a per-session cache.
usage: python g3_extract.py OUT.json [since_iso]
Per session: calls [(ts, ctx, out)], events (attachments, with call index), per-interval growth features."""
import glob, json, os, sys, datetime as dt

BASE = os.path.expanduser(r"~\.claude\projects")
OUT = sys.argv[1]
SINCE = dt.datetime.fromisoformat((sys.argv[2] if len(sys.argv) > 2 else "2026-10-02T00:00:00+00:00"))


def tlen(c):
    if c is None: return 0
    if isinstance(c, str): return len(c)
    if isinstance(c, list):
        return sum(tlen(x) for x in c)
    if isinstance(c, dict):
        if "text" in c and isinstance(c["text"], str): return len(c["text"])
        if "content" in c: return tlen(c["content"])
        return 0
    return 0


def ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


sessions = []
for pdir in sorted(glob.glob(os.path.join(BASE, "*"))):
    for f in glob.glob(os.path.join(pdir, "*.jsonl")):
        try:
            if dt.datetime.fromtimestamp(os.path.getmtime(f), dt.timezone.utc) < SINCE: continue
        except OSError: continue
        calls, seen, events = [], {}, []
        feat = None  # features accumulating after the latest call
        feats = []   # feats[i] = growth between call i and call i+1
        first_ts = None
        try:
            fh = open(f, encoding="utf-8", errors="replace")
        except OSError: continue
        with fh:
            for line in fh:
                try: o = json.loads(line)
                except ValueError: continue
                typ = o.get("type")
                msg = o.get("message") or {}
                if typ == "assistant" and msg.get("usage"):
                    u = msg["usage"]; k = msg.get("id") or o.get("requestId") or o.get("uuid")
                    out = u.get("output_tokens") or 0
                    if k in seen:
                        i = seen[k]; calls[i][2] = max(calls[i][2], out); continue
                    if not o.get("timestamp"): continue
                    t = ts(o["timestamp"])
                    if first_ts is None: first_ts = t
                    ctx = (u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0)
                    if feat is not None: feats.append(feat)
                    seen[k] = len(calls)
                    calls.append([o["timestamp"], ctx, out])
                    feat = {"tr": 0, "ut": 0, "rend": 0, "rend_hac": 0, "hs_out": 0}
                elif typ == "user":
                    c = msg.get("content")
                    if feat is None: continue
                    if isinstance(c, list):
                        for b in c:
                            if isinstance(b, dict) and b.get("type") == "tool_result": feat["tr"] += tlen(b.get("content"))
                            elif isinstance(b, dict): feat["ut"] += tlen(b)
                    else: feat["ut"] += tlen(c)
                elif typ == "attachment":
                    a = o.get("attachment") or {}
                    at = a.get("type")
                    rl = tlen(o.get("rendered")) if "rendered" in o else None
                    ev = {"i": len(calls), "t": at, "r": rl}
                    if at in ("hook_success", "hook_additional_context", "hook_system_message", "hook_blocking_error", "hook_non_blocking_error", "hook_stopped_continuation"):
                        ev["hn"] = a.get("hookName"); ev["he"] = a.get("hookEvent"); ev["cmd"] = (a.get("command") or "")[:120]
                        so = a.get("stdout")
                        ev["so"] = len(so) if isinstance(so, str) else 0
                        ev["se"] = len(a.get("stderr") or "")
                        ev["ec"] = a.get("exitCode")
                        ev["cl"] = tlen(a.get("content"))
                        ev["head"] = (so[:140] if isinstance(so, str) and so else (json.dumps(a.get("content"))[:140]))
                    if at == "instructions":
                        ev["files"] = sum(tlen(x.get("content")) for x in a.get("files", []))
                    events.append(ev)
                    if feat is not None and rl is not None:
                        feat["rend"] += rl
                        if at == "hook_additional_context": feat["rend_hac"] += rl
                    if feat is not None and at == "hook_success": feat["hs_out"] += ev["so"]
            if feat is not None: feats.append(feat)
        if not calls or first_ts < SINCE: continue
        sessions.append({"proj": os.path.basename(pdir), "sid": os.path.basename(f)[:8], "calls": calls, "events": events, "feats": feats})
json.dump(sessions, open(OUT, "w"))
print("sessions", len(sessions), "calls", sum(len(s["calls"]) for s in sessions))
