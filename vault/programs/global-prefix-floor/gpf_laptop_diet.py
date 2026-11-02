"""GPF-L2 laptop measurement: original vs diet resident doctrine, in real interactive panes.

Extends ctx-rent-x l5_canary_driver.run (ConPTY, `claude --model haiku`, call-1 from the transcript, CCR start receipt).
Both arms run the live default (CCR_MAIN_CANARY enforce). The only variable is the content of the swapped files.

usage: python gpf_laptop_diet.py <cwd> <out.json> <seq> <label>     e.g. ... CTCT A
Safety: the original files are backed up once per run; before every swap the live file must hash to either the
original or the diet (anything else = another writer -> abort without touching it); `finally` restores the original
and verifies its hash.
"""
import hashlib, json, os, shutil, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOME = Path(os.environ["USERPROFILE"])
CWD, OUT, SEQ, LABEL = sys.argv[1], Path(sys.argv[2]), sys.argv[3], sys.argv[4]

sys.argv = [sys.argv[0], CWD, str(OUT.with_suffix(".l5scratch.json"))]
sys.path.insert(0, str(HERE.parent / "ctx-rent-x"))
import l5_canary_driver as l5  # noqa: E402  (reads sys.argv at import)

DIET = HERE / "diet"
STUB = ("# {name} (moved, GPF diet 2026-11-02)\n"
        "Full rule: `~/.claude/skills/claude-power-pack/rules/{rel}` -- Read it before a code review / test-writing task.\n")
SWAPS = {
    HOME / ".claude" / "CLAUDE.md": (DIET / "global-CLAUDE.laptop.diet.md").read_bytes(),
    HOME / ".claude" / "rules" / "common" / "code-review.md":
        STUB.format(name="Code Review", rel="common/code-review.md").encode(),
    HOME / ".claude" / "rules" / "python" / "testing.md":
        STUB.format(name="Python Testing", rel="python/testing.md").encode(),
}


MODE = os.environ.get("GPF_MODE", "floor")  # floor = call-1 probe; quality = l6 bounded Work Unit
if MODE == "quality":
    _argv = sys.argv
    sys.argv = [_argv[0], CWD, str(OUT), "claude", "X", "X"]
    # l6 imports p3_canary (gone from the tree: it lived in a vanished temp worktree). l5 exposes the same three
    # functions l6 uses (new_transcripts, cwd_of, start_receipt), so alias it rather than recreate the file.
    sys.modules["p3_canary"] = l5
    import l6_quality_driver as l6  # noqa: E402  (reads sys.argv at import; reuse PROMPT/done/metrics)
    sys.argv = _argv


def quality_run():
    """l6 Work Unit with the probe's own session id pinned and a non-blocking reader (l6.run has neither)."""
    import threading, uuid
    from winpty import PtyProcess
    sid = str(uuid.uuid4())
    p = PtyProcess.spawn([l5.CLAUDE, "--model", "haiku", "--session-id", sid], cwd=CWD, env=dict(os.environ),
                         dimensions=(50, 200))
    def reader():
        while p.isalive():
            try:
                p.read(4096)
            except Exception:
                time.sleep(0.2)
    threading.Thread(target=reader, daemon=True).start()
    def wait(secs):
        end = time.time() + secs
        while time.time() < end and p.isalive():
            time.sleep(0.25)
    wait(25); p.write(l6.PROMPT); time.sleep(1); p.write("\r")
    f = None; deadline = time.time() + 300
    while time.time() < deadline:
        wait(5)
        c = list(l5.PROJ.glob(f"*/{sid}.jsonl"))
        if c:
            f = c[0]
            if l6.done(f):
                break
    wait(8); p.write("/exit"); time.sleep(0.5); p.write("\r"); wait(15)
    if p.isalive():
        p.terminate(force=True)
    r = {"session": sid, "finished": bool(f and l6.done(f)), "receipt": l5.start_receipt(sid)}
    if f:
        r.update(l6.metrics(f))
    return r


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    orig = {p: p.read_bytes() for p in SWAPS}
    ts = time.strftime("%Y%m%dT%H%M%S")
    bdir = HOME / ".claude" / "backups" / f"gpf-{ts}"
    for p, b in orig.items():
        dst = bdir / p.relative_to(HOME / ".claude")
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(b)
    res = {"contract": "GPF-L2-laptop-v1", "plane": os.environ.get("COMPUTERNAME"), "cwd": CWD, "backup": str(bdir),
           "orig_sha": {str(p): sha(b) for p, b in orig.items()},
           "diet_sha": {str(p): sha(b) for p, b in SWAPS.items()}, "probes": []}
    if OUT.exists():
        prev = json.loads(OUT.read_text())
        res["probes"] = prev.get("probes", [])

    def put(state):
        for p in SWAPS:
            cur = sha(p.read_bytes())
            if cur not in (sha(orig[p]), sha(SWAPS[p])):
                raise SystemExit(f"ABORT: {p} changed by another writer (sha {cur[:12]})")
            p.write_bytes(orig[p] if state == "C" else SWAPS[p])

    try:
        for i, arm in enumerate(SEQ):
            put(arm)
            if MODE == "quality":
                r = quality_run()
            else:
                r = l5.run("T", session_id=True)  # canary on in both arms; the arm is the file content; own sid pinned
            r["arm"] = arm; r["seq"] = f"{LABEL}{i}"
            res["probes"].append(r)
            OUT.write_text(json.dumps(res, indent=1))
            print(r["seq"], arm, r.get("call1"), r.get("calls"), r.get("processed"), r.get("correct"), r.get("finished"),
                  r.get("page_faults"), r.get("repairs"), (r.get("receipt") or {}).get("canary"), r.get("session"),
                  (r.get("final") or "")[:90], flush=True)
    finally:
        for p in SWAPS:
            p.write_bytes(orig[p])
        ok = all(sha(p.read_bytes()) == sha(orig[p]) for p in SWAPS)
        res["restored_original"] = ok
        print("RESTORED_ORIGINAL", ok, flush=True)
    key = "processed" if MODE == "quality" else "call1"
    c = [x[key] for x in res["probes"] if x["arm"] == "C" and x.get(key)]
    t = [x[key] for x in res["probes"] if x["arm"] == "T" and x.get(key)]
    if c and t:
        res["summary"] = {"metric": key, "control": c, "treatment": t,
                          "control_spread": round((max(c) - min(c)) / max(c), 4),
                          "delta_mean": round(sum(c) / len(c) - sum(t) / len(t)), "n": [len(c), len(t)]}
    if MODE == "quality":
        res["correct"] = {a: sum(1 for x in res["probes"] if x["arm"] == a and x.get("correct")) for a in "CT"}
    OUT.write_text(json.dumps(res, indent=1))
    print(json.dumps(res.get("summary"), indent=1))


if __name__ == "__main__":
    main()
