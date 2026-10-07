"""Overshoot decomposition for canary-20261007 from raw transcripts + journal (no ledger code)."""
import datetime as dt
import json
from pathlib import Path

SINCE = "2026-10-07T18:43:02"
D = Path.home() / ".claude" / "projects" / ("C--Users-User-AppData-Local-Temp-claude-C--Users-User--claude-skills-claude-p"
                                             "ower-pack-2a90c34a-17e3-4f9c-b317-e6cc993c4469-scratchpad-canary-work")
J = Path.home() / ".claude" / "state" / "goal-budget" / "canary-20261007" / "spend.journal.jsonl"
UK = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")


def iso(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:23]


jr = [json.loads(l) for l in J.read_text(encoding="utf-8").splitlines() if l.strip()]
# first refused renew per sid = a settle not followed by a reserve for the same sid
refusals = {}
for i, r in enumerate(jr):
    if r["op"] == "settle":
        nxt = jr[i + 1] if i + 1 < len(jr) else None
        if not (nxt and nxt["op"] == "reserve" and nxt["sid"] == r["sid"]):
            refusals.setdefault(r["sid"][:8], []).append((r["seq"], iso(r["ts"]), r["measured"]))
print("ledger refusals per sid:", json.dumps(refusals, indent=1))

for sid in ("79f9c88f-02d7-43b7-8118-26b31529ba0a", "9adc4255-0a45-4a4e-ba32-c7d20f547db2"):
    s8 = sid[:8]
    first_ref = refusals[s8][0][1]
    files = [D / f"{sid}.jsonl"] + sorted((D / sid / "subagents").glob("*.jsonl"))
    seen, reqs, events = set(), [], []
    for f in files:
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if not isinstance(r, dict) or str(r.get("timestamp") or "") < SINCE:
                continue
            ts = r["timestamp"]
            if "SESSION BUDGET TRIPPED" in line:
                events.append((ts, f.name[:10], "closeout-advisory", r.get("type")))
            m = r.get("message") or {}
            if isinstance(m, dict) and isinstance(m.get("content"), list):
                for b in m["content"]:
                    if isinstance(b, dict) and b.get("type") == "tool_result" and "GOAL BUDGET" in json.dumps(b.get("content")) \
                            and "closeout call" not in json.dumps(b.get("content")):
                        events.append((ts, f.name[:10], "DENY tool_result", ""))
            u = m.get("usage") if isinstance(m, dict) else None
            if not u or m.get("model") == "<synthetic>":
                continue
            mid = m.get("id") or r.get("uuid")
            tools = [b.get("name") for b in m.get("content") or [] if isinstance(b, dict) and b.get("type") == "tool_use"]
            if mid in seen:
                if tools and reqs and reqs[-1][3] == mid:
                    reqs[-1][2].extend(tools)
                continue
            seen.add(mid)
            reqs.append([ts, sum(int(u.get(k) or 0) for k in UK), tools, mid, f.name[:10]])
    reqs.sort()
    after = [q for q in reqs if q[0] > first_ref]
    print(f"\n== {s8}: first ledger refusal {first_ref}; requests after it: {len(after)}, tokens {sum(q[1] for q in after):,}")
    for q in after:
        print(f"  {q[0]}  {q[1]:>8,}  {q[4]}  tools={q[2]}")
    print("  events:")
    for e in sorted(events):
        print("   ", e)
