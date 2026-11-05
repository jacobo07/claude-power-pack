"""ICC W0 A1: single-variable request-plane floor probes. claude -p --model haiku, n=3/arm, pinned session ids.
Reads call-1 usage (input+cache_creation+cache_read) from each transcript. Plane: REQUEST (API usage), not transcript chars.
usage: python floor_probe.py <out.json>"""
import json, os, subprocess, sys, uuid, glob, statistics
from pathlib import Path
HOME = Path(os.environ["USERPROFILE"]); PROJ = HOME/".claude"/"projects"
scratch = Path(os.environ.get("CLAUDE_JOB_DIR", ".")) / "tmp"; scratch.mkdir(parents=True, exist_ok=True)
empty = scratch/"empty-mcp.json"; empty.write_text('{"mcpServers":{}}')
ARMS = {"control": ({}, []), "ccr_off": ({"CCR_MAIN_CANARY": "0"}, []),
        "no_mcp": ({}, ["--strict-mcp-config", "--mcp-config=" + str(empty)])}


def call1(sid):
    for f in glob.glob(str(PROJ/"*"/f"{sid}.jsonl")):
        for line in open(f, encoding="utf-8", errors="replace"):
            try:
                o = json.loads(line)
            except ValueError:
                continue
            u = (o.get("message") or {}).get("usage")
            if o.get("type") == "assistant" and u:
                return sum(int(u.get(k, 0)) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
    return None


out = {"plane": "request (API usage call-1, input+cache_creation+cache_read)", "cwd": os.getcwd(), "arms": {}}
for arm, (env, extra) in ARMS.items():
    vals = []
    for i in range(3):
        sid = str(uuid.uuid4())
        r = subprocess.run(["claude", "-p", "--model", "haiku", "--session-id", sid, "Reply with the single word OK.", *extra],
                           env={**os.environ, **env}, capture_output=True, text=True, timeout=240, shell=True)
        vals.append({"sid": sid, "rc": r.returncode, "call1": call1(sid)})
        print(arm, i, vals[-1], flush=True)
    ok = [v["call1"] for v in vals if v["call1"]]
    out["arms"][arm] = {"runs": vals, "median": statistics.median(ok) if ok else None}
c = out["arms"]["control"]["median"]
if c:
    for a in ("ccr_off", "no_mcp"):
        m = out["arms"][a]["median"]
        out["arms"][a]["delta_vs_control"] = (m - c) if m else None
Path(sys.argv[1]).write_text(json.dumps(out, indent=2))

