#!/usr/bin/env python3
"""F5 factory lane (PP vault/specs/ascension-reconstruction-factory.md, Owner ruling 2026-11-20, pane 5a77ca0e).

Deterministic, 0 tokens. Per configured lane, per tick:
  PREPARE  scratch clone reset to the lane HEAD; base report built once per lane HEAD; perfn + carve every run
  GATE     scratch build: every binary OK; report lost == 0 vs base AND vs the MATCH snapshot; gained > 0; commit scratch
  APPLY    under the autopilot's cron.lock, only in a window (autopilot status != RUNNING), lane HEAD == base, lane clean:
           ff, lane build, binaries OK, lost == 0 vs snapshot (else reset the lane to base), snapshot + ledger + NOTICE
Standing authorization (brief.md, 2026-11-20): applications of this kind need no Owner turn; anything else does.

usage: lane.py tick [--lane NAME] [--prepare-only] | lane.py selftest
"""
import argparse, fcntl, json, os, shutil, subprocess, sys, time

F = "/home/kobii/agora/factory"
H = "/home/kobii/agora/ascension-autopilot"
READY = os.path.expanduser("~/.claude/state/factory-lane.ready")
CFG = F + "/lanes_factory.json"
STATE = F + "/lane_state.json"
GIT_ID = ["-c", "user.name=kobii-gex44-mission", "-c", "user.email=mission@gex44.local"]
PATHS = ["src", "configure.py", "config"]


def ts():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def log(msg):
    print(f"{ts()} {msg}", flush=True)


def sh(cmd, cwd=None, out=None, timeout=3600):
    """-> (rc, tail). Output goes to the file `out` when given (full log kept for a NOTICE)."""
    try:
        if out:
            with open(out, "w") as w:
                rc = subprocess.run(cmd, cwd=cwd, stdout=w, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                    timeout=timeout).returncode
            txt = open(out, errors="replace").read()
        else:
            p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=timeout)
            rc, txt = p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, f"timeout {timeout}s: {cmd}"
    return rc, txt[-4000:]


def git(repo, *a):
    rc, t = sh(["git", "-C", repo, *a])
    return rc, t.strip()


def head(repo):
    return git(repo, "rev-parse", "HEAD")[1]


def tracked_dirty(repo):
    rc, t = git(repo, "diff", "--name-only", "HEAD")
    return {l for l in t.splitlines() if l.strip()} if rc == 0 else None


def at100(path):
    r = json.load(open(path))
    return {f"{u.get('name')}::{f.get('name')}" for u in r.get("units") or [] if isinstance(u, dict)
            for f in u.get("functions") or [] if isinstance(f, dict) and f.get("fuzzy_match_percent") == 100}


def verdict(base, after, snap):
    """The gate's arithmetic, kept pure so selftest drives it from both poles."""
    lost_b, lost_s, gained = sorted(base - after), sorted(snap - after), sorted(after - base)
    if lost_b or lost_s:
        return False, f"lost {len(lost_b)} vs base, {len(lost_s)} vs snapshot: {(lost_b + lost_s)[:5]}", gained
    if not gained:
        return False, "nothing gained", gained
    return True, f"gained {len(gained)}, lost 0", gained


def build(repo, ln, tag):
    """configure + ninja + report in repo; tracked files the build dirtied are restored (D5). -> (ok, why, report)."""
    before = tracked_dirty(repo)
    if before is None:  # review F2: unknown dirt -> the restore below could discard a pre-existing edit; refuse
        return False, "git diff failed before the build: cannot tell what the build dirties", None
    try:
        rc, t = sh(["nice", "-n", "10", "python3", "configure.py"], cwd=repo, out=f"{repo}/.fl_{tag}_configure.log")
        if rc != 0:
            return False, f"configure rc={rc}: {t[-300:]}", None
        rc, t = sh(["nice", "-n", "10", "ninja", "-j", "12"], cwd=repo, out=f"{repo}/.fl_{tag}_ninja.log", timeout=3600)
        if rc != 0:
            return False, f"ninja rc={rc}: {t[-300:]}", None
        for b in ln["binaries"]:
            if f"{b}: OK" not in t:
                return False, f"binary not OK: {b}", None
        rc, t = sh(["nice", "-n", "10", "ninja", ln["report"]], cwd=repo, out=f"{repo}/.fl_{tag}_report.log")
        if rc != 0:
            return False, f"report rc={rc}: {t[-300:]}", None
        return True, "ok", os.path.join(repo, ln["report"])
    finally:
        after = tracked_dirty(repo)
        for f in sorted((after or set()) - (before or set())):
            git(repo, "checkout", "--", f)


def notice(lane, msg):
    with open(H + "/owner_queue.md", "a") as w:
        w.write(f"- [{ts()}] {lane}: NOTICE (no action needed) factory lane F5 (standing authorization 2026-11-20): {msg}\n")


def ledger(row):
    with open(H + "/ledger.jsonl", "a") as w:
        w.write(json.dumps({"ts": time.time(), "tokens": 0, **row}) + "\n")


def autopilot_status(lane):
    s = json.load(open(H + "/state.json"))
    return (s.get("lanes", s).get(lane) or {}).get("status")


def runs_sig(ln):
    sig = []
    for r in ln["runs"]:
        p = os.path.join(F, r["run"], "sweep.jsonl")
        st = os.stat(p)
        sig.append([r["run"], r["producer"], st.st_size, int(st.st_mtime)])
    return sig


def prepare(ln, st):
    """-> pending dict, or None (nothing to do / refused; reason logged)."""
    L, S, name = ln["repo"], ln["scratch"], ln["lane"]
    base, sig = head(L), runs_sig(ln)
    pend = st.get("pending")
    if pend and pend["base"] == base and pend["sig"] == sig and head(S) == pend["commit"]:
        return pend
    if st.get("done") == [base, sig]:
        log(f"{name}: runs already applied at {base[:7]}, nothing to do")
        return None
    if st.get("failed") == [base, sig]:
        log(f"{name}: gate failed before at this lane HEAD and run set; waiting for a change")
        return None
    if not os.path.isdir(S):
        rc, t = sh(["git", "clone", "-q", "--shared", "--no-checkout", L, S])
        if rc != 0:
            log(f"{name}: clone failed {t}")
            return None
    git(S, "fetch", "-q", L, "HEAD")
    git(S, "checkout", "-q", "--detach", base)
    git(S, "reset", "-q", "--hard", base)
    git(S, "clean", "-fdq", "--", *PATHS)
    for d in ln.get("links", []):  # orig/<GAME>/*, build/compilers, build/tools from the lane (never copied)
        src, dst = os.path.join(L, d), os.path.join(S, d)
        if os.path.isdir(src) and d.startswith("orig/"):
            os.makedirs(dst, exist_ok=True)
            for e in os.listdir(src):
                if not os.path.lexists(os.path.join(dst, e)):
                    os.symlink(os.path.join(src, e), os.path.join(dst, e))
        elif not os.path.lexists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            os.symlink(src, dst)
    bp = os.path.join(F, "lane_base", f"{name}-{base[:12]}.json")
    if not os.path.exists(bp):
        ok, why, rp = build(S, ln, "base")
        if not ok:
            log(f"{name}: BASE build failed at {base[:7]}: {why}")
            st["failed"] = [base, sig]
            notice(name, f"base build failed at {base[:7]} ({why}); scratch {S}")
            return None
        os.makedirs(os.path.dirname(bp), exist_ok=True)
        shutil.copy(rp, bp)
    carved = 0
    for r in ln["runs"]:
        pf = os.path.join(F, "perfn", name, r["run"].replace("/", "_"))
        shutil.rmtree(pf, ignore_errors=True)
        rc, t = sh(["python3", F + "/perfn.py", os.path.join(F, r["run"]), pf])
        if rc != 0:
            log(f"{name}: perfn failed {t[-300:]}")
            return None
        rc, t = sh(["python3", F + "/carve.py", "--run", pf, "--repo", S, "--game", ln["game"], "--compiler", r["compiler"],
                    "--producer", r["producer"], "--lib", r["lib"]])
        if rc != 0:  # review note: a producer failure is told once, then waits for a change like a gate failure
            log(f"{name}: carve failed {t[-300:]}")
            st["failed"] = [base, sig]
            notice(name, f"carve of {r['run']} failed at {base[:7]}: {t[-200:]}")
            return None
        carved += json.loads(t.strip().splitlines()[-1]).get("carved", 0)
    if carved == 0:
        log(f"{name}: 0 functions to carve at {base[:7]}")
        st["done"] = [base, sig]
        return None
    ok, why, rp = build(S, ln, "full")
    snap = set(json.load(open(f"{H}/match/{name}.json")))
    if ok:
        ok, why, gained = verdict(at100(bp), at100(rp), snap)
    if not ok:
        log(f"{name}: GATE REFUSED ({carved} carved): {why}")
        st["failed"] = [base, sig]
        notice(name, f"gate refused {carved} carved functions at {base[:7]}: {why}; scratch {S} kept for inspection")
        return None
    adds = [p for p in PATHS if p != "config"] + [p for p in (f"config/{ln['game']}/splits.txt",
                                                            f"config/{ln['game']}/module/splits.txt") if os.path.exists(os.path.join(S, p))]
    git(S, "add", "-A", "--", *adds)
    rc, t = sh(["git", "-C", S, *GIT_ID, "commit", "-q", "-m",
                f"factory F5: carve {carved} deterministic matches into per-function units ({why}, binaries OK)\n\n"
                "Source: /home/kobii/agora/factory/lane.py (PP vault/specs/ascension-reconstruction-factory.md F5).\n"
                "Owner standing authorization 2026-11-20 (laptop pane 5a77ca0e): 0-token deterministic applications."])
    if rc != 0:
        log(f"{name}: scratch commit failed {t}")
        return None
    pend = {"base": base, "commit": head(S), "sig": sig, "carved": carved, "gained": len(gained), "at": ts()}
    st["pending"] = pend
    log(f"{name}: GATED {pend['commit'][:7]} on {base[:7]}: carved {carved}, gained {len(gained)}")
    return pend


def lock_cron(timeout=900):
    fd = open(H + "/cron.lock", "w")
    end = time.time() + timeout
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd
        except BlockingIOError:
            if time.time() > end:
                fd.close()
                return None
            time.sleep(5)


def apply(ln, st, pend):
    L, S, name = ln["repo"], ln["scratch"], ln["lane"]
    status = autopilot_status(name)
    if status == "RUNNING":
        log(f"{name}: gated {pend['commit'][:7]} waits for a window (autopilot RUNNING)")
        return
    fd = lock_cron()
    if fd is None:
        log(f"{name}: cron.lock busy, retry next tick")
        return
    try:
        status = autopilot_status(name)
        if status == "RUNNING":
            log(f"{name}: lane went RUNNING before the lock; waiting")
            return
        if head(L) != pend["base"]:
            log(f"{name}: lane moved ({head(L)[:7]} != {pend['base'][:7]}); re-prepare next tick")
            st.pop("pending", None)
            return
        d = tracked_dirty(L)
        if d is None or d:  # review F2: a failed git diff is not "clean"
            log(f"{name}: lane tracked-dirty or unreadable {sorted(d or [])[:3]}; waiting")
            return
        git(L, "fetch", "-q", S, pend["commit"])
        rc, t = git(L, "merge", "-q", "--ff-only", pend["commit"])
        if rc != 0:
            log(f"{name}: ff failed {t}")
            return
        snapf = f"{H}/match/{name}.json"
        try:  # review F1: anything raising between the ff and the verdict must not leave the lane on an unverified commit
            ok, why, rp = build(L, ln, "lane")
            old = set(json.load(open(snapf)))
            cur = at100(rp) if ok else set()
        except BaseException as e:
            git(L, "reset", "-q", "--hard", pend["base"])
            st["failed"] = [pend["base"], pend["sig"]]
            st.pop("pending", None)
            notice(name, f"apply raised {type(e).__name__}: {e}; lane reset to {pend['base'][:7]}")
            raise
        lost = sorted(old - cur)
        if not ok or lost:
            git(L, "reset", "-q", "--hard", pend["base"])
            msg = why if not ok else f"lost {len(lost)} vs snapshot: {lost[:5]}"
            log(f"{name}: APPLY REFUSED, lane reset to {pend['base'][:7]}: {msg}")
            st["failed"] = [pend["base"], pend["sig"]]
            st.pop("pending", None)
            notice(name, f"apply refused and lane reset to {pend['base'][:7]}: {msg}")
            return
        bak = f"{snapf}.bak-factory-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
        shutil.copy(snapf, bak)
        with open(snapf + ".tmp", "w") as w:
            json.dump(sorted(cur), w)
        os.replace(snapf + ".tmp", snapf)
        new = len(cur - old)
        ledger({"lane": name, "kind": "factory_match", "new": new, "total": len(cur), "base": pend["base"],
                "commit": pend["commit"], "note": "factory lane F5 (standing authorization 2026-11-20); not a generation's MATCH"})
        notice(name, f"applied {pend['commit'][:7]} in a {status} window: +{new} at 100% (snapshot {len(old)} -> {len(cur)}, "
                     f"0 lost, binaries OK); backup {os.path.basename(bak)}; rollback = git reset --hard {pend['base'][:7]}")
        log(f"{name}: APPLIED {pend['commit'][:7]}: snapshot {len(old)} -> {len(cur)}")
        st["done"] = [head(L), pend["sig"]]
        st.pop("pending", None)
    finally:
        fd.close()


def selftest():
    """The gate arithmetic from both poles; exit 1 on any surprise."""
    ok = True
    def chk(name, got, want):
        nonlocal ok
        print(("PASS " if got == want else "FAIL ") + name)
        ok &= got == want
    chk("gain, nothing lost -> accept", verdict({"a"}, {"a", "b"}, {"a"})[0], True)
    chk("lost vs base -> refuse", verdict({"a", "c"}, {"a", "b"}, {"a"})[0], False)
    chk("lost vs snapshot only -> refuse", verdict({"a"}, {"a", "b"}, {"a", "z"})[0], False)
    chk("no gain -> refuse", verdict({"a"}, {"a"}, {"a"})[0], False)
    sys.exit(0 if ok else 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["tick", "selftest"])
    ap.add_argument("--lane")
    ap.add_argument("--prepare-only", action="store_true")
    a = ap.parse_args()
    if a.cmd == "selftest":
        selftest()
    if not os.path.exists(READY):
        log("kill switch absent (~/.claude/state/factory-lane.ready): no-op")
        return
    lanes = json.load(open(CFG))
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    for ln in lanes:
        if a.lane and ln["lane"] != a.lane:
            continue
        st = state.setdefault(ln["lane"], {})
        try:
            pend = prepare(ln, st)
            if pend and not a.prepare_only:
                apply(ln, st, pend)
        except Exception as e:  # noqa: BLE001 -- one lane's failure must not stop the others; logged with its reason
            log(f"{ln['lane']}: ERROR {type(e).__name__}: {e}")
        finally:
            with open(STATE + ".tmp", "w") as w:
                json.dump(state, w, indent=1)
            os.replace(STATE + ".tmp", STATE)


if __name__ == "__main__":
    main()
