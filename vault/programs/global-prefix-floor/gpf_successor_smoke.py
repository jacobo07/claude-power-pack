"""GPF-L1 / ctx-rent-x Phase 4: real interactive successor smoke + fresh-start cost (laptop plane).

predecessor pane (pinned --session-id, isolated empty CPP_ROLLOVER_STATE_DIR) -> one turn -> `rollover.py seal` into that dir
-> `/clear` -> `/kresume` in the SAME pane -> successor transcript + CCR receipts (ev successor / ev frontier.basis).
Panes run `--permission-mode plan` so a rehydrating successor cannot mutate the repo.

usage: python gpf_successor_smoke.py <out.json> <label>      (appends one run per invocation)
Measured per successor: frontier.basis, successor marker/mode, call-1 (bootstrap), calls and processed for the /kresume
turn, rereads (same Read path twice) and page faults, seconds from /kresume to turn end, goal named in the final text.
"""
import json, os, subprocess, sys, tempfile, threading, time, uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HOME = Path(os.environ["USERPROFILE"])
PROJ = HOME / ".claude" / "projects"
REC = HOME / ".claude" / "ccr" / "state" / "receipts"
OUT, LABEL = Path(sys.argv[1]), sys.argv[2]
GOAL = "GPF successor smoke " + LABEL
TURN_S = 360
sys.path.insert(0, str(HERE.parent / "ctx-rent-x"))


def jl(f):
    for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            yield json.loads(line)
        except Exception:
            continue


def turn_done(f):
    last = None
    for o in jl(f):
        if o.get("type") == "assistant":
            last = o
    m = (last or {}).get("message") or {}
    return m.get("stop_reason") == "end_turn" and not any(
        isinstance(c, dict) and c.get("type") == "tool_use" for c in m.get("content") or [])


def first_prompt(f):
    """The /kresume command line, else "". The first user row after /clear is a local-command caveat, so scan them all."""
    for o in jl(f):
        if o.get("type") == "user":
            c = (o.get("message") or {}).get("content")
            c = c if isinstance(c, str) else json.dumps(c)[:400]
            if "<command-name>/kresume" in c:
                return c
    return ""


def metrics(f):
    seen = set(); calls = proc = 0; call1 = None; reads = []; faults = 0; final = ""
    files = [f] + sorted((f.parent / f.stem / "subagents").glob("*.jsonl")) if (f.parent / f.stem / "subagents").is_dir() else [f]
    for i, x in enumerate(files):
        for o in jl(x):
            if o.get("type") != "assistant":
                continue
            m = o.get("message") or {}
            u = m.get("usage")
            if u and m.get("id") not in seen:
                seen.add(m.get("id")); calls += 1
                t = sum(int(u.get(k, 0)) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
                proc += t
                if i == 0 and call1 is None:
                    call1 = t
            for c in m.get("content") or []:
                if not isinstance(c, dict):
                    continue
                if c.get("type") == "tool_use":
                    inp = c.get("input") or {}
                    if c.get("name") == "Read":
                        reads.append(inp.get("file_path"))
                    if "page" in (c.get("name") or ""):
                        faults += 1
                if i == 0 and c.get("type") == "text":
                    final = c.get("text") or final
    return {"call1": call1, "calls": calls, "processed": proc, "reads": len(reads),
            "rereads": len(reads) - len(set(reads)), "page_faults": faults, "final": final[-300:]}


def receipts(sid):
    out = []
    for f in REC.glob(f"*/{sid}.jsonl"):
        for o in jl(f):
            if o.get("ev") in ("start", "successor", "frontier", "arm"):
                out.append({k: o.get(k) for k in ("ev", "releaseId", "canary", "marker", "mode", "frontier", "bytes")})
    return out


def main():
    from winpty import PtyProcess
    state = Path(tempfile.mkdtemp(prefix="gpf-rollover-", dir=os.environ.get("TEMP")))
    env = dict(os.environ); env["CPP_ROLLOVER_STATE_DIR"] = str(state)
    # GPF_MAIN_CANARY=0 -> CCR_MAIN_CANARY=0 (opt-out). With the main canary on (default since L8) register.ts:124 keeps the
    # successor mode off, so resolveFrontier never runs: this arm is the discriminating test for that.
    if os.environ.get("GPF_MAIN_CANARY") is not None:
        env["CCR_MAIN_CANARY"] = os.environ["GPF_MAIN_CANARY"]
    s1 = str(uuid.uuid4())
    # After /clear the CCR plugin keeps writing receipts under the PREDECESSOR's sid (observed S1), so read both.
    _rc = globals()["receipts"]
    receipts = lambda sid: _rc(s1) + ([] if sid == s1 else _rc(sid))  # noqa: E731
    run = {"label": LABEL, "state_dir": str(state), "predecessor": s1, "goal": GOAL}
    p = PtyProcess.spawn(["claude", "--model", "haiku", "--session-id", s1, "--permission-mode", "plan"],
                         cwd=str(ROOT), env=env, dimensions=(50, 200))
    def reader():
        while p.isalive():
            try:
                p.read(4096)
            except Exception:
                time.sleep(0.2)
    threading.Thread(target=reader, daemon=True).start()
    def wait(secs, until=None):
        end = time.time() + secs
        while time.time() < end and p.isalive():
            if until and until():
                return True
            time.sleep(1)
        return False
    def say(text):
        p.write(text); time.sleep(1); p.write("\r")
    try:
        wait(25)
        say("reply OK")
        f1 = lambda: next(iter(PROJ.glob(f"*/{s1}.jsonl")), None)
        wait(150, lambda: f1() is not None and turn_done(f1()))
        run["predecessor_metrics"] = metrics(f1()) if f1() else None
        seal = subprocess.run([sys.executable, str(ROOT / "tools" / "rollover.py"), "seal", "--session", s1, "--cwd", str(ROOT),
                               "--transcript", str(f1()), "--goal", GOAL, "--next", "name the resumed goal in one line"],
                              env=env, capture_output=True, text=True, timeout=180)
        run["seal"] = {"rc": seal.returncode, "out": seal.stdout[-600:], "err": seal.stderr[-300:]}
        run["state_files"] = sorted(str(x.relative_to(state)) for x in state.rglob("*") if x.is_file())
        say("/clear")
        wait(12)
        t_k = time.time()
        say("/kresume")
        def succ():
            for x in PROJ.glob("*/*.jsonl"):
                try:
                    if x.stat().st_ctime >= t_k - 15 and x.stem != s1 and "kresume" in first_prompt(x):
                        return x
                except OSError:
                    continue
            return None
        wait(TURN_S, lambda: succ() is not None and turn_done(succ()))
        f2 = succ()
        run["seconds_to_turn_end"] = round(time.time() - t_k)
        if f2:
            run["successor"] = f2.stem
            run["successor_first_prompt"] = first_prompt(f2)[:200]
            run["successor_metrics"] = metrics(f2)
            run["goal_named"] = GOAL.lower() in (run["successor_metrics"]["final"] or "").lower()
            wait(8)
            run["receipts"] = receipts(f2.stem)
            run["frontier_basis"] = next((r["frontier"].get("basis") for r in run["receipts"]
                                          if r["ev"] == "frontier" and r.get("frontier")), None)
        say("/exit"); wait(15)
    finally:
        try:
            if p.isalive():
                p.terminate(force=True)
        except OSError as exc:  # pane already exiting (WinError 5, observed S2): keep the run record, name the cause
            run["terminate_error"] = f"{type(exc).__name__}: {exc}"[:160]
    res = json.loads(OUT.read_text()) if OUT.exists() else {"contract": "GPF-L1-successor-v1", "plane": os.environ.get("COMPUTERNAME"), "runs": []}
    res["runs"].append(run)
    OUT.write_text(json.dumps(res, indent=1))
    sm = run.get("successor_metrics") or {}
    print(LABEL, "basis", run.get("frontier_basis"), "goal_named", run.get("goal_named"), "call1", sm.get("call1"),
          "calls", sm.get("calls"), "processed", sm.get("processed"), "rereads", sm.get("rereads"),
          "secs", run.get("seconds_to_turn_end"), "seal_rc", run["seal"]["rc"], "state", run.get("state_files"), flush=True)


if __name__ == "__main__":
    main()
