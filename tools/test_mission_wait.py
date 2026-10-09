#!/usr/bin/env python3
"""V-WAIT-* gates for the dependency-wait engine (tools/mission_wait.py, goal caa-wake).

Real mission_wait + real gsd_x GoalLog + a throwaway `git init` repo + a temp wait dir. The world probes
(goal status, live missions, free RAM, executor) are injected; nothing touches the live state dir.
Each gate is driven from both poles. Prints WAIT_PASS=n/m, exits 0 only when all pass.

    python tools/test_mission_wait.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import mission_wait as mw                            # noqa: E402

GIT = mw.find_git()
_N = [0]


def git(repo: Path, *args: str) -> str:
    r = subprocess.run([GIT, "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
                        *args], cwd=str(repo), capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError("git %s: %s" % (" ".join(args), r.stderr))
    return r.stdout.strip()


def make_repo(tmp: Path) -> Path:
    _N[0] += 1
    repo = tmp / ("repo%d" % _N[0])
    repo.mkdir()
    git(repo, "init", "-q")
    (repo / "seed.txt").write_text("seed", encoding="utf-8")
    git(repo, "add", "seed.txt")
    git(repo, "commit", "-q", "-m", "seed")
    return repo


def commit_file(repo: Path, name: str, body: str = "x") -> None:
    (repo / name).write_text(body, encoding="utf-8")
    git(repo, "add", name)
    git(repo, "commit", "-q", "-m", "add " + name)


def leaf(repo: Path, path: str, **kw) -> dict:
    return {"kind": "git_object", "repo": str(repo), "ref": "HEAD", "path": path, **kw}


def rec(wid: str, pred: dict, nxt: dict | None = None, inv: dict | None = None, waits_on=None) -> dict:
    return {"wait_id": wid, "dependency_type": "git_object", "predicate": pred, "source": "test",
            "next": nxt or {"action": "arm", "cwd": str(ROOT), "command": "go", "lease_tokens": 100},
            "invalidators": inv or {}, "owner_program": "test", "goal": "g-test",
            "created_at": "2026-10-08T00:00:00+00:00", "waits_on": waits_on or []}


class World:
    def __init__(self, tmp: Path, remaining: int = 10_000_000, name: str = "wd"):
        _N[0] += 1
        self.wd = tmp / ("%s%d" % (name, _N[0]))
        self.remaining = remaining
        self.launched: list = []

    def ctx(self, **kw) -> mw.Ctx:
        def execute(nxt):
            self.launched.append(nxt)
            return {"ok": True, "rc": 0, "tail": ""}
        return mw.Ctx(wd=self.wd, goal_status=lambda g: {"ok": True, "remaining": self.remaining},
                      live_missions=lambda cwd: [], free_ram=lambda: 16.0, executor=execute, **kw)

    def declare(self, r: dict) -> dict:
        return mw.declare(r, self.ctx())

    def state(self, wid: str) -> str:
        return mw.derive(mw.open_log(wid, self.wd).read())

    def run(self, **kw) -> dict:
        return {w["wait_id"]: w for w in mw.evaluate_waits(self.ctx(**kw))["waits"]}


def main() -> int:
    os.environ.pop("CPP_MISSION_WAIT", None)
    passes: list[str] = []
    fails: list[str] = []

    def check(g, cond, ev, why=""):
        (passes if cond else fails).append(g)
        print("  %s %s: %s" % ("PASS" if cond else "FAIL", g, ev if cond else why))

    tmp = Path(tempfile.mkdtemp(prefix="mission_wait_"))

    # 1 pre-satisfied dependency wakes on the first pass; absent one does not
    repo = make_repo(tmp)
    commit_file(repo, "receipt.txt")
    w = World(tmp)
    w.declare(rec("w-pre", leaf(repo, "receipt.txt")))
    w.declare(rec("w-pre-neg", leaf(repo, "absent.txt")))
    out = w.run()
    check("V-WAIT-PRESAT", out["w-pre"]["outcome"] == "COGNITIVE" and w.state("w-pre") == "CONSUMED"
          and out["w-pre-neg"]["outcome"] == "WAITING" and w.state("w-pre-neg") == "WAITING"
          and len(w.launched) == 1,
          "true dependency woke on pass 1 (1 launch); absent one stayed WAITING",
          "out=%s launched=%d" % ({k: v["outcome"] for k, v in out.items()}, len(w.launched)))

    # 2 offline gap: declared false, becomes true while no evaluator runs, later pass wakes
    repo = make_repo(tmp)
    w = World(tmp)
    w.declare(rec("w-off", leaf(repo, "later.txt")))
    before = w.run()["w-off"]["outcome"]
    commit_file(repo, "later.txt")
    after = w.run()["w-off"]["outcome"]
    check("V-WAIT-OFFLINE", before == "WAITING" and after == "COGNITIVE" and len(w.launched) == 1,
          "false -> WAITING; became true offline -> next pass woke it",
          "before=%s after=%s launched=%d" % (before, after, len(w.launched)))

    # 3 duplicate pass -> one claim
    repo = make_repo(tmp)
    commit_file(repo, "d.txt")
    w = World(tmp)
    w.declare(rec("w-dup", leaf(repo, "d.txt")))
    first = w.run()["w-dup"]["outcome"]
    second = w.run()["w-dup"]["outcome"]
    claims = [e for e in mw.open_log("w-dup", w.wd).read() if e.type == "claimed"]
    check("V-WAIT-DUP", first == "COGNITIVE" and second == "SKIP_CONSUMED" and len(claims) == 1
          and len(w.launched) == 1, "pass 1 launched; pass 2 SKIP_CONSUMED; 1 claim, 1 launch",
          "first=%s second=%s claims=%d launched=%d" % (first, second, len(claims), len(w.launched)))

    # 4 two concurrent evaluators -> one claim (CAS); a separate wait still gets its own claim
    repo = make_repo(tmp)
    commit_file(repo, "c.txt")
    w = World(tmp)
    w.declare(rec("w-con", leaf(repo, "c.txt")))
    bar = threading.Barrier(2, timeout=20)
    results: list = []

    def racer():
        c = w.ctx(between=lambda point, wid: bar.wait() if point == "satisfy" else None)
        results.append(mw.evaluate_waits(c))

    ts = [threading.Thread(target=racer) for _ in range(2)]
    [t.start() for t in ts]
    [t.join(60) for t in ts]
    claims = [e for e in mw.open_log("w-con", w.wd).read() if e.type == "claimed"]
    outs = sorted(x["outcome"] for r in results for x in r["waits"])
    w.declare(rec("w-con2", leaf(repo, "c.txt")))
    w.run()
    check("V-WAIT-CONCURRENT", len(results) == 2 and len(claims) == 1 and outs.count("DUPLICATE") == 1
          and len(w.launched) == 2, "2 racers: 1 claim, 1 DUPLICATE; second wait claimed on its own",
          "outs=%s claims=%d launched=%d" % (outs, len(claims), len(w.launched)))

    # 5 invalidator true -> STALE, no launch; false -> launches
    repo = make_repo(tmp)
    commit_file(repo, "dep.txt")
    commit_file(repo, "kill.txt")
    w = World(tmp)
    w.declare(rec("w-inv", leaf(repo, "dep.txt"), inv={"any_of": [leaf(repo, "kill.txt")]}))
    w.declare(rec("w-inv-ok", leaf(repo, "dep.txt"), inv={"any_of": [leaf(repo, "nokill.txt")]}))
    out = w.run()
    check("V-WAIT-INVALIDATOR", out["w-inv"]["outcome"] == "STALE" and w.state("w-inv") == "STALE"
          and out["w-inv-ok"]["outcome"] == "COGNITIVE" and len(w.launched) == 1,
          "true invalidator -> STALE with no launch; false invalidator launched",
          "out=%s launched=%d" % ({k: v["outcome"] for k, v in out.items()}, len(w.launched)))

    # 6 goal exhausted -> DENIED with model_calls 0; funded -> launches
    repo = make_repo(tmp)
    commit_file(repo, "g.txt")
    w = World(tmp, remaining=0)
    w.declare(rec("w-ex", leaf(repo, "g.txt")))
    o = w.run()["w-ex"]
    w2 = World(tmp, remaining=10_000_000)
    w2.declare(rec("w-fund", leaf(repo, "g.txt")))
    o2 = w2.run()["w-fund"]
    check("V-WAIT-EXHAUSTED", o["outcome"] == "DENIED" and o["model_calls"] == 0 and w.state("w-ex") == "DENIED"
          and not w.launched and o2["outcome"] == "COGNITIVE" and len(w2.launched) == 1,
          "remaining 0 -> DENIED, model_calls 0, no launch; funded goal launched",
          "o=%s o2=%s" % (o.get("outcome"), o2.get("outcome")))

    # 7 no-work -> NO_WORK (consumed, nothing launched); arm -> launches
    repo = make_repo(tmp)
    commit_file(repo, "n.txt")
    w = World(tmp)
    w.declare(rec("w-nw", leaf(repo, "n.txt"), nxt={"action": "none"}))
    w.declare(rec("w-nw-arm", leaf(repo, "n.txt")))
    out = w.run()
    check("V-WAIT-NOWORK", out["w-nw"]["outcome"] == "NO_WORK" and w.state("w-nw") == "CONSUMED"
          and out["w-nw-arm"]["outcome"] == "COGNITIVE" and len(w.launched) == 1,
          "action none -> NO_WORK, nothing launched; action arm launched once",
          "out=%s launched=%d" % ({k: v["outcome"] for k, v in out.items()}, len(w.launched)))

    # 8 unreadable -> REFUSED, state unchanged; readable sibling unaffected
    repo = make_repo(tmp)
    commit_file(repo, "r.txt")
    w = World(tmp)
    w.declare(rec("w-ok", leaf(repo, "r.txt")))
    w.declare(rec("w-unk", leaf(tmp / "no-such-repo", "r.txt")))
    (w.wd / "w-bad.json").write_text("{not json", encoding="utf-8")
    out = w.run()
    check("V-WAIT-REFUSED", out["w-bad"]["outcome"] == "REFUSED" and out["w-unk"]["outcome"] == "REFUSED"
          and w.state("w-unk") == "WAITING" and out["w-ok"]["outcome"] == "COGNITIVE" and len(w.launched) == 1,
          "corrupt record and missing repo -> REFUSED, state WAITING (UNKNOWN != SATISFIED); sibling launched",
          "out=%s" % {k: v["outcome"] for k, v in out.items()})

    # 9 cycle -> DENIED on every member naming the cycle; acyclic not denied
    repo = make_repo(tmp)
    commit_file(repo, "y.txt")
    w = World(tmp)
    w.declare(rec("w-a", leaf(repo, "y.txt"), waits_on=["w-b"]))
    w.declare(rec("w-b", leaf(repo, "y.txt"), waits_on=["w-a"]))
    w.declare(rec("w-c", leaf(repo, "y.txt"), waits_on=["w-a"]))
    out = w.run()
    named = all("w-a" in " ".join(out[i].get("reasons", [])) for i in ("w-a", "w-b"))
    check("V-WAIT-CYCLE", out["w-a"]["outcome"] == "DENIED" and out["w-b"]["outcome"] == "DENIED" and named
          and out["w-c"]["outcome"] == "COGNITIVE" and len(w.launched) == 1,
          "a<->b both DENIED naming the cycle; c (waits on a, not on a cycle) not denied",
          "out=%s" % {k: (v["outcome"], v.get("reasons")) for k, v in out.items()})

    # 10 kill switch
    repo = make_repo(tmp)
    commit_file(repo, "k.txt")
    w = World(tmp)
    w.declare(rec("w-kill", leaf(repo, "k.txt")))
    snap = {p.name: p.read_bytes() for p in (w.wd / "log").rglob("*") if p.is_file()}
    os.environ["CPP_MISSION_WAIT"] = "off"
    try:
        off = mw.evaluate_waits(w.ctx())
        off_decl = mw.declare(rec("w-kill2", leaf(repo, "k.txt")), w.ctx())
    finally:
        os.environ.pop("CPP_MISSION_WAIT", None)
    snap2 = {p.name: p.read_bytes() for p in (w.wd / "log").rglob("*") if p.is_file()}
    on = w.run()["w-kill"]["outcome"]
    check("V-WAIT-KILL", off["outcome"] == "DISABLED" and off_decl["outcome"] == "DISABLED" and snap == snap2
          and not w.launched[:0] and on == "COGNITIVE" and len(w.launched) == 1
          and not (w.wd / "w-kill2.json").exists(),
          "CPP_MISSION_WAIT=off -> DISABLED, records untouched; switch removed -> launched",
          "off=%s decl=%s on=%s" % (off["outcome"], off_decl["outcome"], on))

    # 11 work-tree-only file does not satisfy; committed does
    repo = make_repo(tmp)
    (repo / "wt.txt").write_text("uncommitted", encoding="utf-8")
    w = World(tmp)
    w.declare(rec("w-wt", leaf(repo, "wt.txt")))
    o1 = w.run()["w-wt"]["outcome"]
    git(repo, "add", "wt.txt")
    git(repo, "commit", "-q", "-m", "wt")
    o2 = w.run()["w-wt"]["outcome"]
    check("V-WAIT-WORKTREE", o1 == "WAITING" and o2 == "COGNITIVE" and len(w.launched) == 1,
          "file only in the work tree -> WAITING; once committed -> woke",
          "o1=%s o2=%s" % (o1, o2))

    # ARGV: unknown argument refused, no gate, no flag; no-arg control still writes the flag
    flag = tmp / "argv_flag.json"
    marker = tmp / "gate_ran.txt"
    env = {**os.environ, "PP_WAKE_FLAG": str(flag), "PP_WAKE_GATE_CMD": json.dumps(
        [sys.executable, "-c", "import sys,pathlib; pathlib.Path(r'%s').write_text('ran'); sys.exit(1)" % marker])}
    py = [sys.executable, str(HERE / "wake_check.py")]
    bad = subprocess.run(py + ["--help"], env=env, capture_output=True, text=True, timeout=60)
    ran_after_bad, flag_after_bad = marker.exists(), flag.exists()
    ctl = subprocess.run(py, env=env, capture_output=True, text=True, timeout=60)
    check("V-WAIT-ARGV", bad.returncode == 2 and not ran_after_bad and not flag_after_bad
          and ctl.returncode == 0 and marker.exists() and flag.exists(),
          "--help exit 2, gate not run, no flag; no-arg control ran the gate and wrote the flag",
          "rc=%s ran=%s flag=%s ctl_rc=%s ctl_flag=%s" % (bad.returncode, ran_after_bad, flag_after_bad,
                                                         ctl.returncode, flag.exists()))

    # CONTENT: git_object contains
    repo = make_repo(tmp)
    commit_file(repo, "doc.txt", "alpha BETA gamma")
    w = World(tmp)
    w.declare(rec("w-has", leaf(repo, "doc.txt", contains="BETA")))
    w.declare(rec("w-lacks", leaf(repo, "doc.txt", contains="ZETA")))
    out = w.run()
    c = w.ctx()
    v_unk, ev_unk = mw.eval_pred(leaf(repo, "doc.txt", contains="BETA"),
                                 _BrokenCat(c))
    check("V-WAIT-CONTENT", out["w-has"]["outcome"] == "COGNITIVE" and out["w-lacks"]["outcome"] == "WAITING"
          and w.state("w-lacks") == "WAITING" and v_unk is None,
          "blob containing the string satisfied (positive control); blob without it did not; unreadable blob UNKNOWN",
          "out=%s unk=%s" % ({k: v["outcome"] for k, v in out.items()}, v_unk))

    # ZEROMODEL (ported from gen2 V-CE-T1-WAIT-ZERO-HOT / IDEMPOTENT): a woken pass makes no model call and
    # a second pass changes no durable byte
    repo = make_repo(tmp)
    commit_file(repo, "z.txt")
    w = World(tmp)
    w.declare(rec("w-zero", leaf(repo, "z.txt")))
    z1 = w.run()["w-zero"]
    s1 = {p.name: p.read_bytes() for p in (w.wd / "log").rglob("*") if p.is_file()}
    z2 = w.run()["w-zero"]
    s2 = {p.name: p.read_bytes() for p in (w.wd / "log").rglob("*") if p.is_file()}
    check("V-WAIT-ZEROMODEL", z1["outcome"] == "COGNITIVE" and z1["model_calls"] == 0 and z1["model_tokens"] == 0
          and z2["outcome"] == "SKIP_CONSUMED" and s1 == s2 and len(w.launched) == 1,
          "woken pass: model_calls 0, model_tokens 0; second pass SKIP_CONSUMED with the log byte-identical",
          "z1=%s calls=%s z2=%s same=%s" % (z1["outcome"], z1.get("model_calls"), z2["outcome"], s1 == s2))

    n, m = len(passes), len(passes) + len(fails)
    print("WAIT_PASS=%d/%d" % (n, m))
    if fails:
        print("FAILED: " + ", ".join(fails))
    return 0 if not fails and n == 14 else 1


class _BrokenCat:
    """A ctx whose `git cat-file -p` fails: the blob exists (-e, rev-parse ok) but its body cannot be read."""

    def __init__(self, inner: mw.Ctx):
        self._i = inner
        self.git = inner.git

    def run(self, argv, cwd=None):
        if argv[1:3] == ["cat-file", "-p"]:
            return subprocess.CompletedProcess(argv, 128, "", "boom")
        return self._i.run(argv, cwd=cwd)


if __name__ == "__main__":
    sys.exit(main())
