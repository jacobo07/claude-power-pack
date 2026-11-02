"""CR-29 / CR-15: a REAL /kclear -> /clear -> /kresume on a real goal, in a throwaway project (laptop plane).

Why a throwaway project: /kclear writes the project's memory (MEMORY.md "Session Handoff" line, project_session_handoff.md,
session_lessons.md). In the PP repo those are shared by every pane, so the probe runs in a temp git repo under %TEMP% (trusted
parent), with its own memory dir, repoKey and goal file, and an isolated CPP_ROLLOVER_STATE_DIR.

Goal file: RESUMPTION_FILE.md whose first Next item is "Create done.txt containing exactly <TOKEN>". The predecessor only reads
it, then runs /kclear. The successor gets /kresume and nothing else. Fresh-agent recovery = it creates done.txt with TOKEN, with
no transcript of the predecessor. Measured: capsule verdict, frontier.basis, seconds and tokens from /kresume to done.txt.

usage: python gpf_cr29_kclear.py <out.json> <label>
"""
import json, os, subprocess, sys, tempfile, threading, time, uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT, LABEL = Path(sys.argv[1]), sys.argv[2]
sys.argv = [sys.argv[0], str(OUT.with_suffix(".unused.json")), LABEL]
sys.path.insert(0, str(HERE))
import gpf_successor_smoke as sm  # noqa: E402  (jl, turn_done, first_prompt, metrics, receipts, PROJ)

TOKEN = f"RESUMED-{LABEL}-{uuid.uuid4().hex[:6]}"
TURN_S, KCLEAR_S, RESUME_S = 180, 300, 600


def git(cwd, *a):
    return subprocess.run(["C:/Program Files/Git/cmd/git.exe", "-c", "user.name=gpf-probe", "-c", "user.email=probe@local", *a],
                          cwd=cwd, capture_output=True, text=True, timeout=60)


FIXED = Path(os.environ["TEMP"]) / "gpf-cr29-probe"   # trusted ONCE by the Owner (HR-001: the agent may not write trust)
MARKER = ".gpf-cr29-probe"


def probe_root():
    """A fresh mkdtemp root always shows the trust dialog (K2/K3 screen evidence) and the auto-mode classifier refuses an
    agent write of hasTrustDialogAccepted (HR-001). So: if the Owner-trusted FIXED root exists AND carries MARKER, reset
    its contents (marker-gated: never wipe a directory this probe did not create) and reuse it; else fall back to mkdtemp,
    which will abort safely at the dialog."""
    import shutil, stat
    if not (FIXED / MARKER).is_file():
        return Path(tempfile.mkdtemp(prefix="gpf-cr29-", dir=os.environ["TEMP"])), False
    def _rw(fn, path, _exc):  # .git objects are read-only on Windows
        os.chmod(path, stat.S_IWRITE); fn(path)
    for x in FIXED.iterdir():
        if x.name == MARKER:
            continue
        shutil.rmtree(x, onerror=_rw) if x.is_dir() else x.unlink()
    return FIXED, True


def main():
    from winpty import PtyProcess
    root, fixed = probe_root()
    mem = Path.home() / ".claude" / "projects" / str(root).replace(":", "-").replace("\\", "-").replace("/", "-") / "memory"
    mem_pre = sorted(x.name for x in mem.iterdir()) if mem.is_dir() else []  # a reused root can carry a prior run's handoff
    (root / "RESUMPTION_FILE.md").write_text(
        "# RESUMPTION_FILE -- GPF CR-29 probe\n\n"
        "Goal: prove a fresh successor resumes from the compiled capsule alone.\n\n"
        "## Next\n"
        f"1. Create done.txt in the project root containing exactly {TOKEN}\n"
        "2. Reply with one line: the goal and the token you wrote.\n", encoding="utf-8")
    git(root, "init", "-q"); git(root, "add", "-A"); git(root, "commit", "-q", "-m", "probe goal")
    state = Path(tempfile.mkdtemp(prefix="gpf-rollover-", dir=os.environ["TEMP"]))
    env = dict(os.environ); env["CPP_ROLLOVER_STATE_DIR"] = str(state)
    s1 = str(uuid.uuid4())
    run = {"label": LABEL, "root": str(root), "fixed_root": fixed, "memory_preexisting": mem_pre, "state_dir": str(state),
           "predecessor": s1, "token": TOKEN}
    argv = ["claude", "--model", "haiku", "--session-id", s1, "--permission-mode", "auto",
            "--disallowedTools", "Edit", "NotebookEdit"]
    p = PtyProcess.spawn(argv, cwd=str(root), env=env, dimensions=(50, 200))
    screen = []
    def reader():
        while p.isalive():
            try:
                screen.append(p.read(4096))
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
    f1 = lambda: next(iter(sm.PROJ.glob(f"*/{s1}.jsonl")), None)
    def assistant_after(f, t):  # an end_turn row newer than t (a turn of THIS prompt, not the previous one)
        for o in sm.jl(f):
            m = o.get("message") or {}
            if o.get("type") == "assistant" and m.get("stop_reason") == "end_turn" and o.get("timestamp", "") >= t:
                return True
        return False
    iso = lambda: time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    try:
        wait(25)
        if "trust" in "".join(screen)[-3000:].lower():
            import re
            plain = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07", "", "".join(screen))
            run["aborted"] = "trust dialog shown; not typing into it"
            run["screen_tail"] = " ".join(plain.split())[-1200:]  # evidence: was it really the dialog?
            raw = "".join(screen)
            i = raw.lower().rfind("trust")
            run["screen_raw_len"] = len(raw)
            run["screen_raw_at_trust"] = repr(raw[max(0, i - 400):i + 400])
            return finish(run, p)
        t = iso(); say("Read RESUMPTION_FILE.md and reply with its goal in one line. Do not do the work yet.")
        run["turn1_done"] = wait(TURN_S, lambda: f1() is not None and assistant_after(f1(), t))
        t = iso(); say("/kclear")
        run["kclear_done"] = wait(KCLEAR_S, lambda: f1() is not None and assistant_after(f1(), t))
        tail = (sm.metrics(f1())["final"] if f1() else "")
        run["kclear_tail"] = tail[-400:]
        run["capsule_verdict"] = next((v for v in ("SAFE_TO_FORGET", "REFUSED", "UNKNOWN") if v in tail), None)
        run["state_files"] = sorted(str(x.relative_to(state)) for x in state.rglob("*") if x.is_file())
        if not run["kclear_done"]:
            run["aborted"] = "kclear turn did not complete; not typing into it"
            return finish(run, p)
        say("/clear"); wait(12)
        t_k = time.time(); say("/kresume")
        done_txt = root / "done.txt"
        ok = lambda: done_txt.is_file() and done_txt.read_text(encoding="utf-8", errors="replace").strip() == TOKEN
        run["first_correct_action"] = wait(RESUME_S, ok)
        run["seconds_to_first_correct_action"] = round(time.time() - t_k) if run["first_correct_action"] else None
        def succ():
            for x in sm.PROJ.glob("*/*.jsonl"):
                try:
                    if x.stat().st_ctime >= t_k - 15 and x.stem != s1 and sm.first_prompt(x):
                        return x
                except OSError:
                    continue
            return None
        run["successor_turn_done"] = wait(120, lambda: succ() is not None and sm.turn_done(succ()))
        f2 = succ()
        if f2:
            run["successor"] = f2.stem
            run["successor_metrics"] = sm.metrics(f2)
            run["token_named"] = TOKEN in (run["successor_metrics"]["final"] or "")
        if run["successor_turn_done"]:
            say("/exit"); wait(15)
        if f2:
            rec = sm.receipts(s1) + sm.receipts(f2.stem)
            run["frontier"] = [r.get("frontier") for r in rec if r["ev"] == "frontier"]
            run["successor_decision"] = [r for r in rec if r["ev"] == "successor" and r.get("marker")]
        run["done_txt"] = done_txt.read_text(encoding="utf-8", errors="replace")[:80] if done_txt.is_file() else None
    finally:
        try:
            if p.isalive():
                p.terminate(force=True)
        except OSError as exc:
            run["terminate_error"] = f"{type(exc).__name__}: {exc}"[:160]
    return finish(run, None)


def finish(run, p):
    if p is not None:
        try:
            if p.isalive():
                p.terminate(force=True)
        except OSError as exc:
            run["terminate_error"] = f"{type(exc).__name__}: {exc}"[:160]
    res = json.loads(OUT.read_text()) if OUT.exists() else {"contract": "GPF-CR29-kclear-v1", "plane": os.environ.get("COMPUTERNAME"), "runs": []}
    res["runs"].append(run)
    OUT.write_text(json.dumps(res, indent=1))
    m = run.get("successor_metrics") or {}
    print(LABEL, "verdict", run.get("capsule_verdict"), "frontier", [f.get("basis") for f in run.get("frontier") or [] if f],
          "correct", run.get("first_correct_action"), "secs", run.get("seconds_to_first_correct_action"),
          "call1", m.get("call1"), "calls", m.get("calls"), "processed", m.get("processed"), "rereads", m.get("rereads"),
          "aborted", run.get("aborted"), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
