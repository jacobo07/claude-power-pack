"""Deterministic per-session autopsy of raw Claude Code transcripts (read-only)."""
import json, sys, os, collections

UK = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
A3B = "c:\\users\\user\\apps\\pp-ce-a3b"


def rows(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                yield json.loads(line)
            except Exception:
                continue


def autopsy(path):
    seen, calls, tools, cwds = set(), [], collections.Counter(), []
    first_a3b = None
    denials = []
    last_cwd = None
    for r in rows(path):
        cwd = r.get("cwd")
        if cwd and cwd != last_cwd:
            cwds.append((r.get("timestamp", "")[:19], cwd))
            last_cwd = cwd
            if first_a3b is None and cwd.lower().startswith(A3B):
                first_a3b = r.get("timestamp", "")[:19]
        m = r.get("message") or {}
        if r.get("type") == "user" and isinstance(m.get("content"), list):
            for b in m["content"]:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    txt = json.dumps(b.get("content"))[:400]
                    if "GOAL BUDGET" in txt or "SESSION BUDGET" in txt:
                        denials.append((r.get("timestamp", "")[:19], txt[:220]))
        if not isinstance(m, dict) or not m.get("usage") or m.get("model") == "<synthetic>":
            continue
        for b in m.get("content") or []:
            if isinstance(b, dict) and b.get("type") == "tool_use":
                name = b.get("name")
                inp = b.get("input") or {}
                if name in ("Bash", "PowerShell"):
                    name += ":" + (str(inp.get("command", "")).split() or ["?"])[0][:30]
                tools[name] += 1
        mid = m.get("id") or r.get("uuid")
        if mid in seen:
            continue
        seen.add(mid)
        u = m["usage"]
        ctx = sum(int(u.get(k) or 0) for k in UK[:3])
        calls.append(dict(ts=r.get("timestamp", "")[:19], model=m.get("model"), ctx=ctx,
                          out=int(u.get("output_tokens") or 0),
                          cr=int(u.get("cache_read_input_tokens") or 0),
                          cw=int(u.get("cache_creation_input_tokens") or 0),
                          a3b=bool(last_cwd and last_cwd.lower().startswith(A3B))))
    return calls, tools, cwds, first_a3b, denials


def main():
    for p in sys.argv[1:]:
        calls, tools, cwds, first_a3b, denials = autopsy(p)
        tot = sum(c["ctx"] + c["out"] for c in calls)
        bound = sum(c["ctx"] + c["out"] for c in calls if c["a3b"])
        print("=" * 100)
        print(os.path.basename(p))
        print(f"calls={len(calls)} processed={tot:,} processed_while_cwd_in_a3b={bound:,}")
        print("models:", dict(collections.Counter(c["model"] for c in calls)))
        print("cache_read=%s cache_write=%s output=%s" % (
            f"{sum(c['cr'] for c in calls):,}", f"{sum(c['cw'] for c in calls):,}", f"{sum(c['out'] for c in calls):,}"))
        if calls:
            print("context first/mid/max/last:", calls[0]["ctx"], calls[len(calls) // 2]["ctx"],
                  max(c["ctx"] for c in calls), calls[-1]["ctx"])
            print("first/last call:", calls[0]["ts"], calls[-1]["ts"])
        print("cwd transitions:", cwds[:8])
        print("first cwd in a3b:", first_a3b)
        print("tools:", tools.most_common(14))
        print("budget denials:", len(denials))
        for d in denials[:6]:
            print("   ", d)
        # spend by hour bucket
        b = collections.OrderedDict()
        for c in calls:
            k = c["ts"][:13]
            b[k] = b.get(k, 0) + c["ctx"] + c["out"]
        print("by hour:", {k: f"{v:,}" for k, v in b.items()})


if __name__ == "__main__":
    main()
