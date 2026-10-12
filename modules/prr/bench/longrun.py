"""longrun.py -- PRR long-lived session memory curve on Linux (GEX44 plane).

Drives ONE real claude process through N user turns over stream-json stdin against
stub_api.py, sampling the process tree's memory at checkpoints. Modes:
  plain    : one process for all turns (baseline curve)
  compact  : one process, `/compact` every --every turns (does compaction return RAM?)
  recycle  : end the process every --every turns and continue with --resume <sid>
             (physical epoch recycling under one logical session)

Memory per sample (from /proc): VmRSS, RssAnon (closest to Windows private bytes while
nothing is swapped), RssFile, VmSwap, VmHWM, summed over the claude process tree.

Output: JSON lines to --out, one per checkpoint, plus a final {"fit": ...} line with the
least-squares slope of RssAnon (MB per 100 turns) after --warmup turns.
stdlib only; Python 3.8+.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

FIELDS = ("VmRSS", "RssAnon", "RssFile", "VmSwap", "VmHWM")


def proc_mem(pid: int) -> dict:
    out = {k: 0 for k in FIELDS}
    try:
        with open(f"/proc/{pid}/status") as fh:
            for line in fh:
                k, _, v = line.partition(":")
                if k in out:
                    out[k] = int(v.split()[0]) // 1024
    except (FileNotFoundError, ProcessLookupError):
        return {}
    return out


def tree(pid: int) -> list:
    pids, stack = [], [pid]
    while stack:
        p = stack.pop()
        pids.append(p)
        try:
            with open(f"/proc/{p}/task/{p}/children") as fh:
                stack.extend(int(x) for x in fh.read().split())
        except (FileNotFoundError, ProcessLookupError):
            continue
    return pids


def sample(root: int) -> dict:
    main = proc_mem(root)
    total = {k: 0 for k in FIELDS}
    pids = tree(root)
    for p in pids:
        m = proc_mem(p)
        for k in FIELDS:
            total[k] += m.get(k, 0)
    return {"main": main, "tree": total, "tree_n": len(pids)}


def fit(points: list) -> dict:
    n = len(points)
    if n < 3:
        return {"n": n, "slope_mb_per_100_turns": None}
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx if sxx else 0.0
    resid = [y - (my + slope * (x - mx)) for x, y in zip(xs, ys)]
    return {"n": n, "slope_mb_per_100_turns": round(slope * 100, 2),
            "mean_mb": round(my, 1), "max_abs_resid_mb": round(max(abs(r) for r in resid), 1)}


class Session:
    def __init__(self, args, resume: str | None):
        cmd = [args.claude, "-p", "--input-format", "stream-json", "--output-format", "stream-json",
               "--verbose", "--model", args.model, "--allowedTools", "Bash"]
        if resume:
            cmd += ["--resume", resume]
        env = dict(os.environ,
                   ANTHROPIC_BASE_URL=f"http://127.0.0.1:{args.port}",
                   ANTHROPIC_API_KEY="sk-ant-prr-stub-not-a-key",
                   CLAUDE_CONFIG_DIR=args.config_dir,
                   CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1",
                   DISABLE_AUTOUPDATER="1")
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=open(args.out + ".stderr", "a"), env=env,
                                  cwd=args.workdir, text=True, bufsize=1)
        self.sid = resume

    def turn(self, text: str, timeout: float) -> dict:
        msg = {"type": "user", "message": {"role": "user", "content": text}}
        self.p.stdin.write(json.dumps(msg) + "\n")
        self.p.stdin.flush()
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError(f"claude exited rc={self.p.poll()}")
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if ev.get("session_id"):
                self.sid = ev["session_id"]
            if ev.get("type") == "result":
                return ev
        raise TimeoutError(f"no result within {timeout}s")

    def end(self):
        try:
            self.p.stdin.close()
            self.p.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.p.terminate()
            self.p.wait(timeout=10)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--claude", default=os.path.expanduser("~/.local/bin/claude"))
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--model", default="claude-haiku-4-5")
    ap.add_argument("--turns", type=int, default=100)
    ap.add_argument("--checkpoints", default="1,10,25,50,100,150,200,250,300,400,500")
    ap.add_argument("--mode", choices=["plain", "compact", "recycle"], default="plain")
    ap.add_argument("--every", type=int, default=50)
    ap.add_argument("--warmup", type=int, default=25)
    ap.add_argument("--config-dir", required=True)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout", type=float, default=120)
    args = ap.parse_args(argv)
    os.makedirs(args.config_dir, exist_ok=True)
    os.makedirs(args.workdir, exist_ok=True)
    cps = {int(x) for x in args.checkpoints.split(",") if x}
    sess = Session(args, None)
    epoch, pts = 1, []
    t0 = time.time()
    with open(args.out, "a") as out:
        for k in range(1, args.turns + 1):
            t1 = time.time()
            sess.turn(f"turn {k}", args.timeout)
            lat = round(time.time() - t1, 3)
            if k in cps or k == args.turns:
                time.sleep(1.0)
                s = sample(sess.p.pid)
                rec = {"mode": args.mode, "turn": k, "epoch": epoch, "pid": sess.p.pid, "sid": sess.sid,
                       "turn_latency_s": lat, "elapsed_s": round(time.time() - t0, 1), **s}
                out.write(json.dumps(rec) + "\n")
                out.flush()
                if k >= args.warmup:
                    pts.append((k, s["main"].get("RssAnon", 0)))
                print(json.dumps({"turn": k, "epoch": epoch, "RssAnon": s["main"].get("RssAnon"),
                                  "VmRSS": s["main"].get("VmRSS"), "tree_n": s["tree_n"]}), flush=True)
            if args.every and k % args.every == 0 and k < args.turns:
                if args.mode == "compact":
                    sess.turn("/compact", args.timeout)
                elif args.mode == "recycle":
                    sid = sess.sid
                    sess.end()
                    r0 = time.time()
                    sess = Session(args, sid)
                    sess.turn("resume check", args.timeout)
                    epoch += 1
                    out.write(json.dumps({"mode": "recycle", "event": "epoch", "epoch": epoch, "sid_in": sid,
                                          "sid_out": sess.sid, "resume_s": round(time.time() - r0, 3),
                                          **sample(sess.p.pid)}) + "\n")
        out.write(json.dumps({"fit": fit(pts), "mode": args.mode, "turns": args.turns, "epochs": epoch}) + "\n")
    sess.end()
    print(json.dumps({"fit": fit(pts), "epochs": epoch}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
