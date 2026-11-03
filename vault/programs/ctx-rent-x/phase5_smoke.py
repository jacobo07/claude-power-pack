"""ctx-rent-x Phase 5 live smoke: Safe-to-Forget in REAL interactive main panes (ConPTY, `claude --model haiku`).

usage: python phase5_smoke.py <cwd> <out.json> <seq> [claude]      e.g. ... C:/repo phase5-safe-to-forget.json FNFNFN
Arm F = CCR_MAIN_PROJECT unset (today: shadow projection); arm N = CCR_MAIN_PROJECT=1 (enforce, judged by safeToForget).
Each run asks the pane to run phase5_fixture.py with its own 3-char key and to report the code printed on the ONE buried
verdict line, so a correct answer proves the proof line reached the model. Per run: correctness, calls, processed tokens
(transcript usage), the CCR start receipt and this session's `project` / projected-`fault` receipts.
Spec: vault/specs/ccr-safe-to-forget-main.md. Harness rules from GPF S4: no plan mode, /exit only after end_turn.
"""
import hashlib, json, os, re, sys, threading, time, uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOME = Path(os.environ["USERPROFILE"])
PROJ = HOME / ".claude" / "projects"
REC = HOME / ".claude" / "ccr" / "state" / "receipts"
FIXTURE = HERE / "phase5_fixture.py"
TURN_TIMEOUT_S = 300
BOOT_WAIT_S = 25
PROMPT = ("Run exactly this one command with the PowerShell tool, with no pipe, filter or redirection added: "
          "& \"{python}\" \"{fixture}\" {key}   It prints a log. Then reply with exactly one final line: CODE <the value of code= on "
          "the line that contains verdict=>")


def code_for(key):
    return hashlib.sha256(("phase5:" + key).encode()).hexdigest()[:6].upper()


def rows(f):
    for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            yield json.loads(line)
        except ValueError:
            continue


def final_text(f):
    last = None
    for o in rows(f):
        if o.get("type") == "assistant":
            last = o
    if not last:
        return None
    m = last.get("message") or {}
    if m.get("stop_reason") != "end_turn" or any(isinstance(c, dict) and c.get("type") == "tool_use" for c in m.get("content") or []):
        return None
    return " ".join(c.get("text", "") for c in m.get("content") or [] if isinstance(c, dict) and c.get("type") == "text").strip()


def usage(f):
    seen, calls, proc = set(), 0, 0
    for o in rows(f):
        m = o.get("message") or {}
        if o.get("type") == "assistant" and m.get("usage") and m.get("id") not in seen:
            seen.add(m.get("id")); calls += 1
            u = m["usage"]
            proc += sum(int(u.get(k, 0)) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
    return calls, proc


def receipts(sid):
    out = {"start": None, "project": [], "faults": 0}
    for f in REC.glob(f"*/{sid}.jsonl"):
        for o in rows(f):
            if o.get("ev") == "start":
                out["start"] = {k: o.get(k) for k in ("releaseId", "compatible", "interactive", "canary", "unit")}
            elif o.get("ev") == "project":
                out["project"].append({k: o.get(k) for k in ("tool", "agent", "bytes", "out", "applied", "forget", "durable", "mainProject")})
            elif o.get("ev") == "fault" and o.get("kind") == "projected":
                out["faults"] += 1
    return out


def run(arm, key, cwd, claude):
    from winpty import PtyProcess
    sid = str(uuid.uuid4())
    env = dict(os.environ)
    env.pop("CCR_MAIN_PROJECT", None)
    if arm == "N":
        env["CCR_MAIN_PROJECT"] = "1"
    p = PtyProcess.spawn([claude, "--model", "haiku", "--session-id", sid, "--permission-mode", "auto",
                          "--disallowedTools", "Write", "Edit", "NotebookEdit"], cwd=cwd, env=env, dimensions=(50, 200))

    def reader():
        while p.isalive():
            try:
                p.read(4096)
            except Exception:  # noqa: BLE001 -- a closed pty raises; the loop only drains output
                time.sleep(0.2)
    threading.Thread(target=reader, daemon=True).start()

    def wait(secs):
        end = time.time() + secs
        while time.time() < end and p.isalive():
            time.sleep(0.25)
    wait(BOOT_WAIT_S)
    p.write(PROMPT.format(python=sys.executable, fixture=str(FIXTURE), key=key)); time.sleep(1); p.write("\r")
    f, final, deadline = None, None, time.time() + TURN_TIMEOUT_S
    while time.time() < deadline:
        wait(5)
        c = list(PROJ.glob(f"*/{sid}.jsonl"))
        if c:
            f = c[0]
            final = final_text(f)
            if final is not None:
                break
    if final is not None:
        wait(8); p.write("/exit"); time.sleep(0.5); p.write("\r"); wait(15)
    if p.isalive():
        p.terminate(force=True)
    wait(3)
    r = {"session": sid, "arm": arm, "key": key, "finished": final is not None}
    if f:
        r["calls"], r["processed"] = usage(f)
    lines = [l for l in (final or "").splitlines() if l.strip()]
    r["final"] = (lines[-1] if lines else "")[:160]
    m = re.search(r"CODE\s+`?([0-9A-Fa-f]{6})`?", r["final"])
    r["correct"] = bool(m and m.group(1).upper() == code_for(key))
    r["receipts"] = receipts(sid)
    return r


def main():
    cwd, out, seq = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
    claude = sys.argv[4] if len(sys.argv) > 4 else "claude"
    res = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {
        "contract": "ctx-rent-x-phase5-v1", "spec": "vault/specs/ccr-safe-to-forget-main.md",
        "plane": os.environ.get("COMPUTERNAME"), "cwd": cwd, "runs": []}
    base = len(res["runs"])
    for i, arm in enumerate(seq):
        key = "k%02d" % (base + i)
        r = run(arm, key, cwd, claude)
        res["runs"].append(r)
        out.write_text(json.dumps(res, indent=1), encoding="utf-8")
        pr = r["receipts"]["project"]
        print(key, arm, r.get("finished"), r.get("correct"), r.get("calls"), r.get("processed"),
              [(x.get("applied"), (x.get("forget") or {}).get("reason")) for x in pr], r["receipts"]["faults"],
              (r["receipts"]["start"] or {}).get("releaseId"), r["final"][:60], flush=True)
    arms = {a: [x for x in res["runs"] if x["arm"] == a and x.get("finished")] for a in "FN"}
    res["summary"] = {a: {"n": len(v), "correct": sum(1 for x in v if x["correct"]),
                          "processed": [x.get("processed") for x in v]} for a, v in arms.items()}
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res["summary"]), flush=True)


if __name__ == "__main__":
    main()
