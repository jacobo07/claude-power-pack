"""ctx-rent-x L6: CCR_MAIN_CANARY=1 vs unset on a REAL bounded Work Unit in a real interactive pane (ConPTY).
Contract P3-main-canary-v1. Usage: p6_quality.py <cwd> <out.json> <claude.exe> <arms e.g. SE> <tag>
Metrics per run (main + subagent transcripts): calls, processed, cache-weighted (in 1, cw 1.25, cr 0.1, out 5),
tool uses, page faults (page tool / ToolSearch for it), rereads (same Read path twice), repairs (tool errors), correct."""
import json, os, re, sys, time
from pathlib import Path
from winpty import PtyProcess

sys.path.insert(0, str(Path(__file__).parent))
import p3_canary as pc  # noqa: E402

CWD = Path(sys.argv[1]); OUT = Path(sys.argv[2]); CLAUDE = sys.argv[3]; ARMS = sys.argv[4]; TAG = sys.argv[5]
PROMPT = ("Use the subagent type best suited for read-only codebase search to find which file in this repo defines "
          "DEFAULT_MODES, and what the default mode of `main` is there. Run the subagent in the foreground (not in the background) and wait for its result. Reply with exactly one final line: <repo-relative path> <mode>")
OK_PATH = "mods/cpp-cognitive-runtime/hooks/policy.ts"


def lines(f):
    for l in f.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            yield json.loads(l)
        except Exception:
            pass


def done(f):
    last = None
    for o in lines(f):
        if o.get("type") == "assistant":
            last = o
    if not last:
        return False
    m = last.get("message") or {}
    if m.get("stop_reason") != "end_turn" or any(c.get("type") == "tool_use" for c in m.get("content") or [] if isinstance(c, dict)):
        return False
    txt = " ".join(c.get("text", "") for c in m.get("content") or [] if isinstance(c, dict) and c.get("type") == "text").strip()
    last = [l for l in txt.splitlines() if l.strip()][-1:] or [""]
    return re.search(r"\S+\.\w+\s+`?(shadow|enforce|off)`?\s*$", last[0].strip()) is not None


def metrics(f):
    files = [f] + sorted((f.parent / f.stem / "subagents").glob("*.jsonl")) if (f.parent / f.stem / "subagents").is_dir() else [f]
    seen = set(); calls = proc = 0; w = 0.0; tools = []; reads = []; errors = 0; final = ""
    for i, x in enumerate(files):
        for o in lines(x):
            if o.get("type") == "assistant":
                m = o.get("message") or {}
                mid = m.get("id"); u = m.get("usage")
                if u and mid not in seen:
                    seen.add(mid); calls += 1
                    a, cw, cr, out = (int(u.get(k, 0)) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"))
                    proc += a + cw + cr; w += a + 1.25 * cw + 0.1 * cr + 5 * out
                for c in m.get("content") or []:
                    if isinstance(c, dict) and c.get("type") == "tool_use":
                        inp = c.get("input") or {}
                        tools.append(c.get("name") + (":" + str(inp.get("subagent_type")) if c.get("name") in ("Agent", "Task") else ""))
                        if c.get("name") == "Read":
                            reads.append(inp.get("file_path"))
                        if "page" in (c.get("name") or "") or ("page" in json.dumps(inp) and c.get("name") == "ToolSearch"):
                            tools.append("PAGE_FAULT")
                    if i == 0 and isinstance(c, dict) and c.get("type") == "text":
                        final = c.get("text") or final
            if o.get("type") == "user":
                for c in (o.get("message") or {}).get("content") or []:
                    if isinstance(c, dict) and c.get("type") == "tool_result" and c.get("is_error"):
                        errors += 1
    last = [l for l in final.strip().splitlines() if l.strip()][-1:] or [""]
    norm = last[0].replace("\\", "/").strip("` ")
    correct = OK_PATH in norm and re.search(r"\bshadow\b", norm) is not None
    return {"calls": calls, "processed": proc, "weighted": round(w), "tools": tools, "page_faults": tools.count("PAGE_FAULT"),
            "rereads": len(reads) - len(set(reads)), "repairs": errors, "final": last[0][:160], "correct": correct}


def run(arm):
    env = dict(os.environ); env.pop("CCR_MAIN_CANARY", None)
    if arm == "E":
        env["CCR_MAIN_CANARY"] = "1"
    t0 = time.time() - 1
    p = PtyProcess.spawn([CLAUDE, "--model", "haiku"], cwd=str(CWD), env=env, dimensions=(50, 200))
    def pump(secs):
        end = time.time() + secs
        while time.time() < end and p.isalive():
            try:
                p.read(4096)
            except Exception:
                time.sleep(0.2)
    pump(25); p.write(PROMPT); time.sleep(1); p.write("\r")
    f = None; deadline = time.time() + 240
    while time.time() < deadline:
        pump(5)
        c = [x for x in pc.new_transcripts(t0) if (pc.cwd_of(x) or "").lower() == str(CWD).lower()]
        if c:
            f = max(c, key=lambda x: x.stat().st_mtime)
            if done(f):
                break
    pump(8); p.write("/exit"); time.sleep(0.5); p.write("\r"); pump(15)
    if p.isalive():
        p.terminate(force=True)
    sid = f.stem if f else None
    r = {"arm": arm, "session": sid, "receipt": pc.start_receipt(sid) if sid else None, "finished": bool(f and done(f))}
    if f:
        r.update(metrics(f))
    exp = "enforce" if arm == "E" else "off"
    r["receipt_matches_arm"] = (r["receipt"] or {}).get("canary") == exp
    return r


def main():
    res = json.loads(OUT.read_text()) if OUT.exists() else {"contract": "P3-main-canary-v1", "prompt": PROMPT, "runs": []}
    for i, a in enumerate(ARMS):
        r = run(a); r["seq"] = f"{TAG}{i}"; res["runs"].append(r)
        OUT.write_text(json.dumps(res, indent=1))
        print(r["seq"], a, r.get("calls"), r.get("processed"), r.get("weighted"), r.get("page_faults"), r.get("correct"),
              (r.get("receipt") or {}).get("canary"), r.get("finished"), r.get("final"), flush=True)


if __name__ == "__main__":
    main()
