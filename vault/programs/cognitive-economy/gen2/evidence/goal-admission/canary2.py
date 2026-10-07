"""Live tiny-cap canary #2 for goal budget admission, after the closeout fix (19240f98).

Usage: python canary2.py <pp_repo> <canary_dir> <goal> <cap> [workers=2] [max_turns=30]

Differences from canary #1 (CANARY.md): worker stderr goes to its own file (a merged `SessionEnd hook
... failed` line broke the session-id parse and the driver reported 0 tokens / 0 denies), and the
measurement is the diag.py decomposition: raw transcripts + the goal journal, no ledger code.
"""
import datetime as dt
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

pp, cdir, goal, cap = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], int(sys.argv[4])
workers = int(sys.argv[5]) if len(sys.argv) > 5 else 2
max_turns = int(sys.argv[6]) if len(sys.argv) > 6 else 30
py = sys.executable
UK = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")

cdir.mkdir(parents=True, exist_ok=True)
for i in range(3):
    (cdir / f"note{i}.txt").write_text(f"canary note {i}\n" * 200, encoding="utf-8")
decl = subprocess.run([py, str(pp / "tools" / "mission_spend.py"), "goal-declare", "--goal", goal, "--cap", str(cap),
                       "--source", "canary #2 2026-10-07 (Owner 'y' to rerun after 19240f98)", "--root", str(cdir),
                       "--host", socket.gethostname(), "--lease-calls", "2"], capture_output=True, text=True)
print("declare:", decl.stdout.strip()[:300], decl.stderr.strip()[:200], flush=True)
dout = json.loads(decl.stdout.strip().splitlines()[-1])
if not dout.get("ok"):
    sys.exit(f"declare refused: {dout.get('reason')}")
since = dout["binding"]["since"]

PROMPT = ("You are a budget canary. Repeat this loop: Read note0.txt, note1.txt and note2.txt in this "
          "directory; on your third loop, launch ONE Agent (general-purpose) told to Read all three notes "
          "twice and report their line counts. Keep looping. The moment ANY tool call is denied with a "
          "message containing 'GOAL BUDGET', reply with exactly 'CANARY STOPPED: <the denial reason>' and "
          "make no further tool calls.")
env = dict(os.environ, CPP_GOAL=goal)
env.pop("CPP_SESSION_BUDGET", None)
t0 = time.time()
procs = []
for i in range(workers):
    out = open(cdir / f"worker{i}.json", "w", encoding="utf-8")
    err = open(cdir / f"worker{i}.stderr.txt", "w", encoding="utf-8")
    procs.append((subprocess.Popen([shutil.which("claude"), "-p", PROMPT, "--output-format", "json",
                                    "--max-turns", str(max_turns), "--model", "sonnet",
                                    "--allowedTools", "Read,Glob,Agent"],
                                   cwd=str(cdir), env=env, stdout=out, stderr=err), out, err))
for p, out, err in procs:
    try:
        p.wait(timeout=500)
    except subprocess.TimeoutExpired:
        p.kill()
    out.close()
    err.close()
wall = round(time.time() - t0)


def iso(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:23]


sids = []
for i in range(workers):
    raw = (cdir / f"worker{i}.json").read_text(encoding="utf-8", errors="replace").strip()
    try:
        sids.append(json.loads(raw)["session_id"])
    except (ValueError, KeyError) as e:
        sys.exit(f"worker{i}: no session_id in stdout ({e}); stdout head: {raw[:200]!r}")

state = Path(os.environ.get("GSD_LONG_RUN_STATE_DIR") or Path.home() / ".claude" / "state")
jr = [json.loads(l) for l in (state / "goal-budget" / goal / "spend.journal.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
refusals = {}
for i, r in enumerate(jr):
    if r["op"] == "settle":
        nxt = jr[i + 1] if i + 1 < len(jr) else None
        # A refusal is a settle with no LEASE after it; since a3aaa515 it is followed by a `final` hold.
        # Canary #3 first ran without the `kind` test and reported no refusals at all (check3.py).
        if not (nxt and nxt["op"] == "reserve" and nxt["sid"] == r["sid"] and nxt.get("kind") != "final"):
            refusals.setdefault(r["sid"], []).append({"seq": r["seq"], "at": iso(r["ts"]), "measured": r["measured"]})

pdir = Path.home() / ".claude" / "projects"
receipt = {"goal": goal, "cap": cap, "since": since, "wall_s": wall, "workers": []}
grand = 0
for sid in sids:
    main = next(pdir.glob(f"*/{sid}.jsonl"))
    files = [main] + sorted((main.parent / sid / "subagents").glob("*.jsonl"))
    seen, reqs, denies, advisories = set(), [], [], []
    for f in files:
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if not isinstance(r, dict) or str(r.get("timestamp") or "") < since:
                continue
            if "closeout call" in line:
                advisories.append(r["timestamp"])
            m = r.get("message") or {}
            if isinstance(m, dict) and isinstance(m.get("content"), list):
                for b in m["content"]:
                    c = json.dumps(b.get("content")) if isinstance(b, dict) else ""
                    if isinstance(b, dict) and b.get("type") == "tool_result" and "GOAL BUDGET" in c and "closeout call" not in c:
                        denies.append(r["timestamp"])
            u = m.get("usage") if isinstance(m, dict) else None
            if not u or m.get("model") == "<synthetic>":
                continue
            mid = m.get("id") or r.get("uuid")
            if mid in seen:
                continue
            seen.add(mid)
            tools = [b.get("name") for b in m.get("content") or [] if isinstance(b, dict) and b.get("type") == "tool_use"]
            reqs.append({"at": r["timestamp"], "tokens": sum(int(u.get(k) or 0) for k in UK), "tools": tools,
                         "file": f.name[:12]})
    reqs.sort(key=lambda q: q["at"])
    total = sum(q["tokens"] for q in reqs)
    grand += total
    first_ref = (refusals.get(sid) or [{}])[0].get("at")
    after = [q for q in reqs if first_ref and q["at"] > first_ref]
    receipt["workers"].append({
        "sid": sid, "files": len(files), "requests": len(reqs), "tokens": total,
        "ledger_refusals": refusals.get(sid, []), "first_deny_tool_result": min(denies, default=None),
        "closeout_advisories": len(advisories), "requests_after_first_refusal": after,
        "tokens_after_first_refusal": sum(q["tokens"] for q in after)})
receipt["independent_total"] = grand
receipt["overshoot"] = grand - cap
receipt["first_refusal_used"] = None
if refusals:
    first = min((v[0] for v in refusals.values()), key=lambda x: x["seq"])
    marks = {}
    for r in jr:
        if r["op"] == "settle" and r["seq"] <= first["seq"]:
            marks[r["sid"]] = max(marks.get(r["sid"], 0), r["measured"])
    receipt["first_refusal_used"] = {"seq": first["seq"], "at": first["at"], "settled_sum": sum(marks.values())}
(Path(__file__).parent / f"receipt_{goal}.json").write_text(json.dumps(receipt, indent=1), encoding="utf-8")
print(json.dumps(receipt, indent=1))
