"""ctx-rent-x L5: existing v4 A7 main-lean canary (CCR_MAIN_CANARY=1) vs control, REAL interactive panes via ConPTY.
Live release, no new release. Counterbalanced CTCT then TCTC. Measures call-1 (input+cache_creation+cache_read) from the
session transcript and reads the CCR start receipt (canary field) so an arm that did not actually fire is visible."""
import json, os, sys, time
from pathlib import Path
from winpty import PtyProcess

HOME = Path(os.environ["USERPROFILE"])
PROJ = HOME / ".claude" / "projects"
REC = HOME / ".claude" / "ccr" / "state" / "receipts"
CWD = Path(sys.argv[1])
OUT = Path(sys.argv[2])
CLAUDE = sys.argv[3] if len(sys.argv) > 3 else "claude"


def new_transcripts(t0):
    out = []
    for f in PROJ.glob("*/*.jsonl"):
        try:
            if f.stat().st_ctime >= t0:
                out.append(f)
        except OSError:
            pass
    return out


def first_usage(f):
    seen = set()
    for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            o = json.loads(line)
        except Exception:
            continue
        if o.get("type") == "assistant":
            m = o.get("message") or {}
            u = m.get("usage")
            if u and m.get("id") not in seen:
                return int(u.get("input_tokens", 0)) + int(u.get("cache_creation_input_tokens", 0)) + int(u.get("cache_read_input_tokens", 0))
    return None


def cwd_of(f):
    for line in f.read_text(encoding="utf-8", errors="replace").splitlines()[:30]:
        try:
            o = json.loads(line)
        except Exception:
            continue
        if o.get("cwd"):
            return o["cwd"]
    return None


def start_receipt(sid):
    for f in REC.glob(f"*/{sid}.jsonl"):
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                o = json.loads(line)
            except Exception:
                continue
            if o.get("ev") == "start":
                return {k: o.get(k) for k in ("releaseId", "compatible", "interactive", "canary", "policyGen", "version")}
    return None


def run(arm, session_id=None):
    """session_id (GPF 2026-11-02): pin the probe's own transcript by id. Without it the newest same-cwd transcript is
    taken, which measures ANOTHER pane when one is active in the same cwd (observed: 09664f88 in the PP root)."""
    import threading, uuid
    env = dict(os.environ)
    env.pop("CCR_MAIN_CANARY", None)
    if arm == "T":
        env["CCR_MAIN_CANARY"] = "1"
    t0 = time.time() - 1
    argv = [CLAUDE, "--model", "haiku"]
    if session_id is True:
        session_id = str(uuid.uuid4())
    if session_id:
        argv += ["--session-id", session_id]
    p = PtyProcess.spawn(argv, cwd=str(CWD), env=env, dimensions=(50, 200))
    chunks = []
    def reader():  # p.read blocks while the pane is quiet; a thread keeps pump() bounded by its deadline
        while p.isalive():
            try:
                chunks.append(p.read(4096))
            except Exception:
                time.sleep(0.2)
    threading.Thread(target=reader, daemon=True).start()
    def pump(secs):
        end = time.time() + secs
        while time.time() < end and p.isalive():
            time.sleep(0.25)
    pump(25)
    p.write("reply OK")
    time.sleep(1)
    p.write("\r")
    f = None; call1 = None
    deadline = time.time() + 150
    while time.time() < deadline and call1 is None:
        pump(5)
        if session_id:
            cands = [x for x in PROJ.glob(f"*/{session_id}.jsonl")]
        else:
            cands = [x for x in new_transcripts(t0) if (cwd_of(x) or "").lower() == str(CWD).lower()]
        if cands:
            f = max(cands, key=lambda x: x.stat().st_mtime)
            call1 = first_usage(f)
    pump(8)  # let turn.complete flush the receipts
    p.write("/exit"); time.sleep(0.5); p.write("\r")
    pump(15)
    if p.isalive():
        p.terminate(force=True)
    sid = f.stem if f else None
    return {"arm": arm, "call1": call1, "session": sid, "receipt": start_receipt(sid) if sid else None,
            "screen_tail": "".join(chunks)[-400:] if call1 is None else None}


def main():
    res = {"contract": "P3-main-canary (existing v4 A7 CCR_MAIN_CANARY=1, live release)", "cwd": str(CWD), "probes": []}
    seqs = (("A", "CTCT"), ("B", "TCTC"))
    if len(sys.argv) > 4:
        seqs = ((sys.argv[4], sys.argv[5]),)
    for s, seq in seqs:
        for i, a in enumerate(seq):
            r = run(a); r["seq"] = f"{s}{i}"
            res["probes"].append(r)
            OUT.write_text(json.dumps(res, indent=1))
            print(r["seq"], a, r["call1"], (r["receipt"] or {}).get("canary"), r["session"], flush=True)
    c = [p["call1"] for p in res["probes"] if p["arm"] == "C" and p["call1"]]
    t = [p["call1"] for p in res["probes"] if p["arm"] == "T" and p["call1"]]
    if c and t:
        res["summary"] = {"control": c, "treatment": t, "control_spread": round((max(c) - min(c)) / max(c), 4),
                          "delta_mean": round(sum(c) / len(c) - sum(t) / len(t)), "n": [len(c), len(t)]}
    OUT.write_text(json.dumps(res, indent=1))
    print(json.dumps(res.get("summary"), indent=1))


if __name__ == "__main__":
    main()
