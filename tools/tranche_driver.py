"""tranche_driver: zero-model step driver (TOK-18 context-runtime-2, S6).

One headless `claude -p` worker per packet, then deterministic receipt checks: receipt exists, every hash on
its `COMMITS:` line is reachable from HEAD (at least one), each named test exits 0, worker spend <= step cap.
Refuses a step whose cap exceeds --step-max, or that would push the tranche past --cap minus --reserve (stops).
Spend enforcement is the existing guard: each worker is declared via `mission_spend.py session-declare`.
"""
import argparse, contextlib, io, json, re, shlex, shutil, subprocess, sys, time, uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SPEND_SRC = REPO / "vault/programs/cognitive-economy/gen2/evidence/stage0/self_spend.py"
GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
PER_CALL = 110_000


def spend(sid):
    """Processed tokens for a session via stage0/self_spend.py (read, sid swapped in memory, never edited)."""
    buf = io.StringIO()
    src = re.sub(r'sid="[^"]*"', f'sid="{sid}"', SPEND_SRC.read_text(encoding="utf-8"), count=1)
    with contextlib.redirect_stdout(buf):
        exec(src, {})  # noqa: S102 -- the program's own meter, executed unmodified except the sid
    m = re.search(r"processed ([\d,]+)", buf.getvalue())
    return int(m.group(1).replace(",", "")) if m else None


def run(argv, timeout=None, stdin=None):
    try:
        return subprocess.run(argv, cwd=REPO, input=stdin, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout).returncode
    except (OSError, subprocess.TimeoutExpired):
        return None


def check(p, sid, spend_fn=spend, run_fn=run):
    rc = REPO / p["receipt"]
    c = {"receipt": rc.is_file()}
    text = rc.read_text(encoding="utf-8", errors="replace") if c["receipt"] else ""
    hs = [h for ln in text.splitlines() if ln.strip().upper().startswith("COMMITS:")
          for h in re.findall(r"\b[0-9a-f]{7,40}\b", ln)]
    c["commits"] = bool(hs) and all(run_fn([GIT, "-C", str(REPO), "merge-base", "--is-ancestor", h, "HEAD"]) == 0
                                    for h in hs)
    c["tests"] = all(run_fn([sys.executable, *shlex.split(t)], 1800) == 0 for t in p.get("tests", []))
    s = spend_fn(sid)
    c["spend"] = s is not None and s <= p["cap"]
    return c, s


def calls_for(sid, stop, feas_fn=None):
    """Largest call count session-declare will admit under `stop`, priced at the guard's own measured per-call
    context (not a fixed 110k). 0 = nothing fits; None = cost unknown (the declare will refuse)."""
    if feas_fn is None:
        sys.path.insert(0, str(REPO / "tools"))
        import mission_spend as ms
        feas_fn, g, r = ms.feasibility, ms.DEFAULT_GROWTH_PER_CALL, ms.DEFAULT_RESERVE_CALLS
    else:
        g, r = 2_100, 2
    f = feas_fn(sid, stop, 1)
    if f.get("per_call") is None:
        return None
    n = 0
    while (f["spent"] + (n + 1 + r) * f["per_call"] + g * (n + 1 + r) * (n + 2 + r) // 2) <= stop:
        n += 1
    return n


def drive(packets, res, coordinator, cap, reserve, step_max, spend_fn=spend, run_fn=run, launch_fn=None, log=print,
          calls_fn=calls_for):
    claude = shutil.which("claude") or "claude"
    launch_fn = launch_fn or (lambda argv, prompt: run(argv, 3600, prompt))
    for p in packets:
        total = (spend_fn(coordinator) or 0) + sum(s.get("spend") or 0 for s in res["steps"].values())
        if p["cap"] > step_max or total + p["cap"] > cap - reserve:
            res["steps"][p["step"]] = {"verdict": "REFUSED_OVER_CAP", "total_before": total, "cap": p["cap"]}
            log(f"{p['step']} REFUSED_OVER_CAP total_before={total:,} step_cap={p['cap']:,} limit={cap - reserve:,}")
            break
        sid = str(uuid.uuid4())
        calls = calls_fn(sid, p["cap"])
        if calls == 0:
            res["steps"][p["step"]] = {"verdict": "REFUSED_INFEASIBLE", "sid": sid, "cap": p["cap"]}
            log(f"{p['step']} REFUSED_INFEASIBLE sid={sid} cap={p['cap']:,}: not one call fits at the measured floor")
            break
        calls = calls or max(1, p["cap"] // PER_CALL)
        d = run_fn([sys.executable, "tools/mission_spend.py", "session-declare", "--session", sid, "--target",
                    str(int(p["cap"] * .8)), "--warn", str(int(p["cap"] * .9)), "--stop", str(p["cap"]),
                    "--calls-estimate", str(calls)])
        if d != 0:
            res["steps"][p["step"]] = {"verdict": "ADMISSION_REFUSED", "sid": sid, "declare_rc": d}
            log(f"{p['step']} ADMISSION_REFUSED sid={sid} declare_rc={d}")
            break
        prompt = (REPO / p["prompt"]).read_text(encoding="utf-8") + (
            f"\n\nYOUR SESSION ID: {sid}. CAP {p['cap']:,} processed tokens = {calls} calls at this repo's measured per-call floor. "
            f"Write the receipt {p['receipt']} with a `COMMITS: <hash ...>` line before your last call.\n")
        t0 = time.time()
        lrc = launch_fn([claude, "-p", "--session-id", sid, "--output-format", "json",
                         "--permission-mode", "acceptEdits", "--allowedTools", "Read Write Edit Grep Glob PowerShell"],
                        prompt)
        c, s = check(p, sid, spend_fn, run_fn)
        v = "PASS" if all(c.values()) else "FAIL"
        res["steps"][p["step"]] = {"verdict": v, "sid": sid, "launch_rc": lrc, "checks": c, "spend": s,
                                   "cap": p["cap"], "receipt": p["receipt"], "secs": round(time.time() - t0)}
        log(f"{p['step']} {v} sid={sid} launch_rc={lrc} checks={c} spend={s} cap={p['cap']:,}")
    res["coordinator_spend"] = spend_fn(coordinator)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(prog="tranche_driver")
    ap.add_argument("--packets", required=True)
    ap.add_argument("--results", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--coordinator", required=True)
    ap.add_argument("--cap", type=int, default=4_500_000)
    ap.add_argument("--reserve", type=int, default=0)
    ap.add_argument("--step-max", type=int, default=1_200_000)
    a = ap.parse_args(argv)
    out, led = REPO / a.results, REPO / a.ledger
    res = json.loads(out.read_text(encoding="utf-8")) if out.is_file() else {"steps": {}}

    def log(msg):
        with led.open("a", encoding="utf-8") as f:
            f.write(f"- driver {time.strftime('%Y-%m-%dT%H:%M:%S')} {msg}\n")
        print(msg)
    drive(json.loads((REPO / a.packets).read_text(encoding="utf-8")), res, a.coordinator, a.cap, a.reserve,
          a.step_max, log=log)
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    return 0 if all(s.get("verdict") == "PASS" for s in res["steps"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
